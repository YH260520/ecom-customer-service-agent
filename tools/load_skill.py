from langchain_core.tools import tool
from agent.skills import ALL_SKILLS

@tool
def load_skill(skill_name: str) -> str:
    """
    当判断某个技能（如退款流程）与当前用户请求相关时，调用此工具加载该技能的完整操作指南。
    参数 skill_name 必须是系统提示词中列出的技能名称之一。
    """
    skill = ALL_SKILLS.get(skill_name)
    if not skill:
        return f"未找到名为 '{skill_name}' 的技能，可用技能有: {list(ALL_SKILLS.keys())}"
    return skill["content"]