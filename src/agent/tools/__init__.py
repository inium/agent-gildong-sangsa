from langchain_core.tools import StructuredTool
from agent.tools.common.introduction_tool import IntroductionTool
from agent.tools.common.current_time_tool import CurrentTimeTool
from agent.tools.mall.cs_tool import CsTool
from agent.tools.hr.rules_of_employment_tool import RulesOfEmploymentTool
from agent.tools.hr.travel_of_employment_tool import TravelOfEmploymentTool
from agent.tools.hr.welfare_of_employment_tool import WelfareOfEmploymentTool

__all__ = [
    "IntroductionTool",
    "CurrentTimeTool",
    "CsTool",
    "RulesOfEmploymentTool",
    "TravelOfEmploymentTool",
    "WelfareOfEmploymentTool",
]


def all_tools() -> list[StructuredTool]:
    tools = [
        CurrentTimeTool().as_tool(),
        RulesOfEmploymentTool().as_tool(),
        TravelOfEmploymentTool().as_tool(),
        WelfareOfEmploymentTool().as_tool(),
        CsTool().as_tool(),
    ]
    tools.append(IntroductionTool(tools).as_tool())

    return tools
