import json

from agent.llm.llm import LLM
from agent.prompt.system_prompt import SYSTEM_PROMPT, NEXT_STEP_PROMPT
from agent.react_agent import ReActAgent
from base.logger import logger
from base.schema import Message, ToolCall, ToolChoice, TOOL_CHOICE_TYPE, AgentState
from my_mcp.client.mcp_client import McpClient
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)
class ThinkingAgent(ReActAgent):
    def __init__(self):
        super().__init__()
        self.name = "ThinkingAgent"
        self.description = "A Smart AI Agent that can do everything."
        self.system_prompt = SYSTEM_PROMPT
        self.next_step_prompt = NEXT_STEP_PROMPT
        self.llm = LLM("deepseek-chat", "sk-0b5b9ed3f61b487d8308151dd9ab9ef4", "https://api.deepseek.com")
        self.tools= []
        self.tool_mcp_clients = {}
        self.tool_choices = ToolChoice.AUTO
        self.step_tool_calls = []

    async def init_tool(self):
        self.init_system_tool()

        for tool_box_name in ["filesystem"]:
            mcp_client = McpClient(tool_box_name)
            await mcp_client.connect_to_server()
            tools = mcp_client.list_tools()
            for tool in tools:
                self.tools.append(McpClient.convert_tool_format(tool))
                self.tool_mcp_clients[tool.name] = mcp_client

    def init_system_tool(self):
        system_tool_finish = {
            'type': 'function',
            'function': {
                'name': "system_tool_finish",
                'description': "Use this tool to signal that you've finished addressing the user's request",
                'parameters': None
            }
        }
        self.tools.append(system_tool_finish)


    async def think(self) -> bool:
        if self.next_step_prompt:
            user_msg = Message.user_message(self.next_step_prompt)
            self.memory.messages += [user_msg]
        try:
            response = await self.llm.ask_tool(
                system_messages=[Message.system_message(self.system_prompt)],
                user_messages=self.memory.messages,
                tools=self.tools
            )
        except Exception as e:
            logger.exception("Exception while asking tool", e)
            raise RuntimeError("call llm exception")

        self.step_tool_calls = response.tool_calls

        logger.info(f"{self.name}'s thoughts: {response.content}")
        logger.info(
            f"selected {len(response.tool_calls) if response.tool_calls else 0} tools to use"
        )
        if response.tool_calls:
            logger.info(
                f"Tools being prepared: {[call.function.name for call in response.tool_calls]}"
            )

        assistant_msg = (
            Message.from_tool_calls(
                content=response.content, tool_calls=self.step_tool_calls
            )
            if self.step_tool_calls
            else Message.assistant_message(response.content)
        )
        self.memory.add_message(assistant_msg)

        if self.tool_choices == ToolChoice.REQUIRED and not self.step_tool_calls:
            raise RuntimeError("required use tool but no tool calls")

        # For 'auto' mode, continue with content if no commands but content exists
        if self.tool_choices == ToolChoice.AUTO and not self.step_tool_calls:
            return bool(response.content)

        return bool(self.step_tool_calls)


    async def act(self) -> str:
        if not self.step_tool_calls:
            return self.memory.messages[-1].content or "No content or commands to execute"
        results = []
        for tool_call in self.step_tool_calls:
            result = await self.execute_tool(tool_call)
            logger.info(
                f"🎯 Tool '{tool_call.function.name}' completed its mission! Result: {result}"
            )

            # Add tool response to memory
            tool_msg = Message.tool_message(
                content=result, tool_call_id=tool_call.id, name=tool_call.function.name
            )
            self.memory.add_message(tool_msg)
            results.append(result)

        return "\n\n".join(results)

    async def execute_tool(self, tool_call: ChatCompletionMessageToolCall) -> str:
        """Execute a single tool call with robust error handling"""
        if not tool_call or not tool_call.function or not tool_call.function.name:
            return "Error: Invalid command format"

        if tool_call.function.name == "system_tool_finish":
            logger.info("ThinkingAgent has already completed user request")
            self.state = AgentState.FINISHED

        name = tool_call.function.name
        if name not in self.tool_mcp_clients.keys():
            return f"Error: Unknown tool '{name}'"

        try:

            client = self.tool_mcp_clients[name]
            result = await client.call_tool(tool_call)

            # Format result for display
            observation = (
                f"Observed output of tool `{name}` executed:\n{str(result.content)}"
                if result
                else f"`{name}` completed with no output"
            )

            # Handle special tools like `finish`
            # await self._handle_special_tool(name=name, result=result)

            return observation
        except json.JSONDecodeError:
            error_msg = f"Error parsing arguments for {name}: Invalid JSON format"
            logger.error(
                f"Oops! The arguments for '{name}' don't make sense - invalid JSON, arguments:{tool_call.function.arguments}"
            )
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Tool '{name}' encountered a problem: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"


if __name__ == "__main__":
    agent = ThinkingAgent()
    agent.run()