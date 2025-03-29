import os
from agent.llm.llm import LLM
from agent.prompt.thinking_agent_prompt import SYSTEM_PROMPT, NEXT_STEP_PROMPT
from agent.react_agent import ReActAgent
from base.schema import ToolChoice

# think:
# 询问模型调用工具拆解任务
# 模型返回 plan_create 调用，入参为子任务列表
# act：
# plan_create 创建任务，返回 plan ，写入memory
# think:
#
# 模型返回 plan_create 调用，入参为子任务列表
# act：
# plan_create 创建任务，返回 plan ，写入memory


class ThinkingAgent(ReActAgent):
    def __init__(self):
        super().__init__()
        self.name = "ThinkingAgent"
        self.description = "A Smart AI Agent that can do everything."
        self.system_prompt = SYSTEM_PROMPT
        self.next_step_prompt = NEXT_STEP_PROMPT
        self.llm = LLM("deepseek-chat", os.getenv("DK_API_KEY"), "https://api.deepseek.com")
        self.tools= []
        self.tool_mcp_clients = {}
        self.tool_choices = ToolChoice.AUTO
        self.step_tool_calls = []
        self.sub_agents = []


    async def act(self) -> str:
        pass

    async def think(self) -> bool:
        pass