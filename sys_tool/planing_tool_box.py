from typing import Any, Optional

from base.base_tool import BaseTool
from base.schema import ToolChoice, ToolCall


class SystemPlanCreateTool(BaseTool):
    name: str = "system_plan_create"
    description: str = "system tool, create plan"
    parameters: Optional[dict] = {

    }

    async def execute(self, **kwargs) -> Any:
        pass


class PlaningToolBox:
    def __init__(self):
        self.sub_agents = []



