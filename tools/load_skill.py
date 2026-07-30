from langchain_core.tools import tool
from agent.skills import ALL_SKILLS

def _load_skill(skill_name: str) -> str:
    """
    当判断某个技能（如退款流程）与当前用户请求相关时，调用此工具加载该技能的完整操作指南。
    参数 skill_name 必须是系统提示词中列出的技能名称之一。

    Args:
        skill_name: 技能名

    Returns:
        success: 加载技能是否成功
        message: 如果加载成功，包含技能的完整操作指南；如果加载失败，描述失败原因
    """
    skill = ALL_SKILLS.get(skill_name)
    if not skill:
        return {
            "success": False,
            "message": f"未找到名为 '{skill_name}' 的技能，可用技能有: {list(ALL_SKILLS.keys())}"
        }
    return {
        "success": True,
        "message": skill["content"]
    }

@tool
def load_skill(skill_name: str) -> str:
    """
    当判断某个技能（如退款流程）与当前用户请求相关时，调用此工具加载该技能的完整操作指南。
    参数 skill_name 必须是系统提示词中列出的技能名称之一。

    Args:
        skill_name: 技能名

    Returns:
        str: 技能的完整操作指南
    """
    return _load_skill(skill_name)