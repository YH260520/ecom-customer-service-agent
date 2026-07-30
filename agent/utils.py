from agent.state import *
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langgraph.types import interrupt


def format_profile(profile: UserProfile) -> str:
    """把结构化画像渲染成一段自然语言文本,方便直接拼进 System Prompt"""
    parts = []
    if profile.id:
        parts.append(f"身份:{profile.identity}")
    if profile.preferences:
        parts.append(f"偏好:{', '.join(profile.preferences)}")
    if profile.emotional_tendency:
        parts.append(f"情绪倾向:{profile.emotional_tendency}")
    if profile.interested_products:
        parts.append(f"关注商品:{', '.join(profile.interested_products)}")
    if profile.summary:
        parts.append(f"综合摘要:{profile.summary}")
    return " | ".join(parts) if parts else ""


def create_tools_node_with_hitl(tools: list):
    """
    工厂函数：为不同的 Graph 生成各自的工具节点，共用同一套 HITL 检查逻辑。

    Args:
        tools: 该 Graph 使用的工具列表
    """
    tool_executor = ToolNode(tools)
    sensitive_set = {"exec_refund"}

    async def tools_node_with_hitl(state: GraphState):
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        sensitive_calls = [tc for tc in tool_calls if tc["name"] in sensitive_set]

        if sensitive_calls:
            human_decision = interrupt({
                "type": "tool_approval",
                "message": "检测到敏感工具调用，请人工确认是否继续执行。",
                "sensitive_calls": [
                    {"tool_name": tc["name"], "args": tc["args"], "id": tc["id"]}
                    for tc in sensitive_calls
                ],
            })

            if not human_decision.get("approved", False):
                return {"messages": [
                    ToolMessage(
                        content=f"工具 {tc['name']} 的调用已被人工拒绝："
                                f"{human_decision.get('reason', '无具体原因')}",
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    )
                    for tc in tool_calls
                ]}

        return await tool_executor.ainvoke(state)

    return tools_node_with_hitl