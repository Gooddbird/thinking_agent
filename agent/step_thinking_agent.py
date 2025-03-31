import os
import mimetypes


from mcp.types import CallToolResult, TextContent, ImageContent
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)

from agent.llm.llm import LLM
from agent.prompt.step_prompt import SYSTEM_PROMPT
from agent.react_agent import ReActAgent
from agent.thinking_agent import ThinkingAgent
from base.logger import logger
from base.schema import Message, ToolChoice, AgentState
from mcp_tool.client.mcp_client import McpClient
from utils.image import ImageUtil
from utils.aliyun_oss import AliYunOSSUtil
from string import Template

from utils.time_util import TimeUtil


class StepThinkingAgent(ReActAgent):

    def __init__(self):
        super().__init__()
        self.name = "StepThinkingAgent"
        self.description = "A Smart AI Agent that can do everything."
        self.llm = LLM("deepseek-chat", os.getenv("DK_API_KEY"), "https://api.deepseek.com")
        self.tools= []
        self.tool_mcp_clients = {}
        self.tool_mcp_client_list = []
        self.tool_choices = ToolChoice.AUTO
        self.step_tool_calls = []
        self.sys_prompt = ""


    def init(self) -> bool:
        self.create_work_root()
        self.build_system_prompt()
        return True

    def build_system_prompt(self):
        template = Template(SYSTEM_PROMPT)
        self.sys_prompt = template.substitute(
            request=self.request,
            work_root_dir=self.work_root_dir
        )

    def create_work_root(self):
        dir_name = TimeUtil.get_now_time_14_str()
        self.work_root_dir = f"E:\\ai_workspace\\thinking_agent\\start\\{dir_name}"
        os.makedirs(self.work_root_dir, exist_ok=True)
        logger.info(f"Already create Work root dir: {self.work_root_dir}")

    async def cleanup(self):
        for mcp_client in self.tool_mcp_client_list:
            await mcp_client.cleanup()

    async def init_tool(self):
        self.init_system_tool()

        for tool_box_name in ["filesystem", "playwright"]:
            mcp_client = McpClient(tool_box_name)
            await mcp_client.connect_to_server()
            self.tool_mcp_client_list.append(mcp_client)
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
        try:
            response = await self.llm.ask_tool(
                system_messages=[Message.system_message(self.sys_prompt)],
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
                f"Tool '{tool_call.function.name}' completed its mission! Result:"
            )
            logger.info(result)

            observation = (
                f"Observed output of tool `{tool_call.function.name}` executed:\n{str(result.content)}"
                if result
                else f"`{tool_call.function.name}` completed with no output"
            )
            # Add tool response to memory
            tool_msg = Message.tool_message(
                content=observation, tool_call_id=tool_call.id, name=tool_call.function.name
            )
            self.memory.add_message(tool_msg)
            results.append(observation)

        return "\n\n".join(results)

    @staticmethod
    def build_error_call_tool_result(msg: str, is_error) -> CallToolResult:
        result = CallToolResult(content = [TextContent(type="text", text=msg)], isError=is_error)
        return result


    async def execute_tool(self, tool_call: ChatCompletionMessageToolCall) -> CallToolResult:
        """Execute a single tool call with robust error handling"""
        if not tool_call or not tool_call.function or not tool_call.function.name:
            return self.build_error_call_tool_result("Error: Invalid command format", True)

        if tool_call.function.name == "system_tool_finish":
            logger.info("ThinkingAgent has already completed user request")
            self.state = AgentState.FINISHED
            return self.build_error_call_tool_result("system tool finish", False)

        name = tool_call.function.name
        if name not in self.tool_mcp_clients.keys():
            return self.build_error_call_tool_result("can't find tool '{name}'", True)

        try:
            client = self.tool_mcp_clients[name]
            call_result = await client.call_tool(tool_call)
            if call_result and call_result.content:
                for content in call_result.content:
                    if isinstance(content, ImageContent):
                        now = TimeUtil.get_now_time_14_str()
                        extension = mimetypes.guess_extension(content.mimeType)
                        file_path = f"{self.work_root_dir}\\{name}_{now}{extension}"
                        ImageUtil.save_base64_image(content.data, file_path)
                        content.data = f"image url: {AliYunOSSUtil.upload_file(file_path)}, local_path: {file_path}"
                        logger.info(content.data)
            return call_result
        except Exception as e:
            error_msg = f"Tool '{name}' encountered a problem: {str(e)}"
            logger.error(error_msg)
            return self.build_error_call_tool_result(f"Error: {error_msg}", True)


if __name__ == "__main__":
    agent = ThinkingAgent()
    agent.run()