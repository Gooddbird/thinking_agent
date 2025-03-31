import asyncio
import sys
import json
from contextlib import AsyncExitStack
from enum import Enum
from typing import Optional, List

import mcp.client.stdio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)

from base.logger import logger
from config.config import g_mcp_server_config

UVX_PATH = "C:\\Users\\Administrator\\.local\\bin\\uvx.exe"
NPX_PATH = "E:\\Node\\npx.cmd"

sys.path.append(" E:\\ai_workspace\\thinking_agent")

class McpServerType(str, Enum):
    PYTHON_MCP_SERVER = "python_mcp_server"
    TS_MCP_SERVER = "ts_mcp_server"


class McpClient:
    def __init__(self, name: str):
        self.name = name
        self.write = None
        self.stdio = None
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.config = g_mcp_server_config[name]
        self.tools = []

    @staticmethod
    def convert_tool_format(tool: MCPTool):
        converted_tool = {
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.inputSchema
            }
        }
        return converted_tool

    def convert_tool_list_format(self):
        result = []
        for tool in self.tools:
            result.append(self.convert_tool_format(tool))
        return result

    def list_tools(self) -> List[MCPTool]:
        return self.tools

    async def connect_to_server(self):
        if self.config is None:
            raise RuntimeError("mcp server config is null")

        if self.config.get("command") != "uvx" and self.config.get("command") != "npx":
            raise RuntimeError("mcp server config is invalid")

        command = UVX_PATH if self.config.get("commend") == "uvx" else NPX_PATH
        default_env = mcp.client.stdio.get_default_environment()
        input_env = {}
        if self.config.get("env") is not None:
            input_env = self.config.get("env")
        env =  {**default_env, **input_env}
        server_params = StdioServerParameters(
            command=command,
            args=self.config.get("args", []),
            env=env,
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # 列出可用工具
        response = await self.session.list_tools()
        self.tools = response.tools
        for tool in self.tools:
            tool.name = self.name + "--" + tool.name
            logger.info(f"tool name: {tool.name}")

    async def call_tool(self, tool_call: ChatCompletionMessageToolCall):
        real_tool_name = tool_call.function.name.split("--")[1]
        return await self.session.call_tool(real_tool_name, json.loads(tool_call.function.arguments))

    async def cleanup(self):
        """清理资源"""
        await self.exit_stack.aclose()


async def test_jetbrains():
    client = McpClient("jetbrains")
    try:
        await client.connect_to_server()
    finally:
        await client.cleanup()


async def main():
    await test_jetbrains()
    # client = McpClient("playwright")
    # try:
    #     await client.connect_to_server()
    #     result = await client.session.call_tool('browser_navigate', {"url": "https://www.baidu.com"})
    #
    #     screenshot = await client.session.call_tool('browser_screenshot', {})
    #     logger.info(screenshot)
    #
    #     # snap = await client.session.call_tool('browser_click', {"ref": "s1e13", "element": "link"})
    #     # logger.info(snap)
    #     #
    #     # snap = await client.session.call_tool('browser_go_forward', {})
    #     # logger.info(snap)
    #     #
    #     wait = await client.session.call_tool('browser_wait', {"time": 10})
    #
    # finally:
    #     await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
