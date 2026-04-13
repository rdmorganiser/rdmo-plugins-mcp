import json
import logging

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from rdmo_chatbot.chatbot.adapter import LangChainAdapter, config, messages_to_dicts, store


logger = logging.getLogger(__name__)


class MCPLangChainAdapter(LangChainAdapter):
    def __init__(self, *args):
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("system", "{tool_instruction}"),
                ("system", "{context}"),
                MessagesPlaceholder(variable_name="history"),
            ]
        )

    async def on_user_message(self, message):
        user = cl.user_session.get("user")
        project = await self.call_copilot("getProject")
        project = project if isinstance(project, dict) else {}
        project_id = project.get("id")
        history = store.get_history(user.identifier, project_id)
        conversation = [*history, HumanMessage(content=message.content)]

        inputs = {
            "system_prompt": config.SYSTEM_PROMPT.format(user=user.display_name),
            "tool_instruction": self._build_tool_instruction(),
            "context": json.dumps(project),
            "history": conversation,
        }

        async with self._mcp_session() as session:
            tools = await self._get_bound_tools(session)
            tool_choice = "any" if self._should_force_tool_use(message.content, tools) else "auto"
            logger.info(
                "MCP adapter preparing request: tool_choice=%s tools=%s user=%s project_id=%s message=%r",
                tool_choice,
                [tool["function"]["name"] for tool in tools],
                user.identifier,
                project_id,
                message.content,
            )
            chain = self.prompt | self.llm.bind_tools(tools, tool_choice=tool_choice)
            response = await self._run_agent_loop(chain, session, inputs, user.identifier)

        response_message = await cl.Message(content=response.content).send()
        response_message.actions = [
            cl.Action(name="on_transfer", icon="file-output", payload={"content": response_message.content}),
            cl.Action(name="on_contact", icon="mail", payload={"history": messages_to_dicts(history)}),
        ]
        await response_message.update()

        store.set_history(
            user.identifier,
            project_id,
            [
                *history,
                HumanMessage(content=message.content),
                AIMessage(content=response_message.content),
            ],
        )

        return response_message

    async def _run_agent_loop(self, chain, session, inputs, user_identifier):
        max_steps = getattr(config, "MCP_MAX_STEPS", 8)
        response = await chain.ainvoke(inputs)
        logger.info(
            "MCP adapter initial model response: content=%r tool_calls=%s invalid_tool_calls=%s",
            response.content,
            response.tool_calls,
            getattr(response, "invalid_tool_calls", None),
        )

        for step in range(max_steps):
            if not response.tool_calls:
                logger.info("MCP adapter finished without tool call at step=%s", step)
                return response

            tool_messages = []
            for tool_call in response.tool_calls:
                tool_args = {
                    **tool_call.get("args", {}),
                    "username": tool_call.get("args", {}).get("username") or user_identifier,
                }
                logger.info(
                    "MCP adapter executing tool call: step=%s name=%s args=%s id=%s",
                    step,
                    tool_call["name"],
                    tool_args,
                    tool_call["id"],
                )
                result = await session.call_tool(
                    tool_call["name"],
                    arguments=tool_args,
                )
                logger.info(
                    "MCP adapter tool result: step=%s name=%s is_error=%s structured=%s content=%s",
                    step,
                    tool_call["name"],
                    result.isError,
                    result.structuredContent,
                    result.content,
                )
                tool_messages.append(
                    ToolMessage(
                        content=self._serialise_tool_result(result),
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"],
                    )
                )

            inputs = {
                **inputs,
                "history": [*inputs["history"], response, *tool_messages],
            }
            response = await chain.ainvoke(inputs)
            logger.info(
                "MCP adapter follow-up model response: step=%s content=%r tool_calls=%s invalid_tool_calls=%s",
                step,
                response.content,
                response.tool_calls,
                getattr(response, "invalid_tool_calls", None),
            )

        logger.warning("MCP adapter reached max_steps=%s without terminal response", max_steps)
        return response

    async def _get_bound_tools(self, session):
        tool_result = await session.list_tools()
        logger.info(
            "MCP adapter discovered MCP tools: %s",
            [tool.name for tool in tool_result.tools],
        )
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": self._tool_parameters(tool.inputSchema),
                },
            }
            for tool in tool_result.tools
        ]

    def _mcp_session(self):
        transport = getattr(config, "MCP_SERVER_TRANSPORT", "sse")
        url = getattr(config, "MCP_SERVER_URL", "http://127.0.0.1:8090/sse")

        if transport == "streamable-http":
            return _MCPStreamableHTTPSession(url)
        if transport != "sse":
            raise ValueError(f"Unsupported MCP transport for chatbot adapter: {transport}")
        return _MCPSSESession(url)

    def _serialise_tool_result(self, result):
        if result.structuredContent is not None:
            return json.dumps(result.structuredContent)

        parts = []
        for item in result.content:
            text = getattr(item, "text", None)
            if text:
                parts.append(text)

        if parts:
            return "\n".join(parts)

        return json.dumps({"is_error": result.isError})

    def _build_tool_instruction(self):
        return (
            "You can call MCP tools to perform actions in RDMO. "
            "When the user asks you to create, add, update, change, or modify data in RDMO, "
            "prefer using the available tools instead of saying that you cannot act. "
            "The authenticated RDMO user is injected by the system, so do not ask for or invent usernames. "
            "Only answer without tools if the user is clearly asking for explanation, planning, or advice. "
            "If required tool parameters are missing, ask a short follow-up question."
        )

    def _should_force_tool_use(self, content, tools):
        lowered = content.lower()
        action_markers = [
            "create project",
            "new project",
            "create a new project",
            "add member",
            "add user",
            "invite user",
            "update answer",
            "change answer",
            "change repository",
            "modify",
            "create",
            "add",
            "update",
            "change",
        ]
        if any(marker in lowered for marker in action_markers):
            return True

        return any(tool["function"]["name"].lower() in lowered for tool in tools)

    def _tool_parameters(self, schema):
        copied = json.loads(json.dumps(schema))
        properties = copied.get("properties", {})
        properties.pop("username", None)

        required = copied.get("required")
        if isinstance(required, list):
            copied["required"] = [item for item in required if item != "username"]

        return copied


class _MCPSSESession:
    def __init__(self, url):
        self.url = url
        self._stream_context = None
        self._session = None

    async def __aenter__(self):
        logger.info("Opening MCP SSE session to %s", self.url)
        self._stream_context = sse_client(self.url)
        read_stream, write_stream = await self._stream_context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        logger.info("MCP SSE session initialized for %s", self.url)
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        if self._session is not None:
            await self._session.__aexit__(exc_type, exc, tb)
        if self._stream_context is not None:
            await self._stream_context.__aexit__(exc_type, exc, tb)


class _MCPStreamableHTTPSession:
    def __init__(self, url):
        self.url = url
        self._stream_context = None
        self._session = None

    async def __aenter__(self):
        logger.info("Opening MCP streamable-http session to %s", self.url)
        self._stream_context = streamable_http_client(self.url)
        read_stream, write_stream, _ = await self._stream_context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        logger.info("MCP streamable-http session initialized for %s", self.url)
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        if self._session is not None:
            await self._session.__aexit__(exc_type, exc, tb)
        if self._stream_context is not None:
            await self._stream_context.__aexit__(exc_type, exc, tb)


class OpenAIMCPLangChainAdapter(MCPLangChainAdapter):
    @property
    def llm(self):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(**config.LLM_ARGS)


class OllamaMCPLangChainAdapter(MCPLangChainAdapter):
    @property
    def llm(self):
        from langchain_ollama import ChatOllama

        return ChatOllama(**config.LLM_ARGS)
