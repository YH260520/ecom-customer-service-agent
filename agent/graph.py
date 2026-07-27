from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import START, StateGraph, END
from agent.node import *
from tools.tool_manager import TOOL_MGR

# 构建子智能体
# 售前客服
presale_agent_graph = StateGraph(GraphState)
presale_agent_graph.add_node("presale_assistant", presale_assistant)
presale_agent_graph.add_node("presale_tools", create_tools_node_with_hitl(TOOL_MGR.get_filted_tools("presale")))
presale_agent_graph.add_edge(START, "presale_assistant")
presale_agent_graph.add_conditional_edges("presale_assistant", check_resolution_status,
                                            {"resolved": END, "unresolved": "presale_tools"})
presale_agent_graph.add_edge("presale_tools", "presale_assistant")

# 售后客服
aftersale_agent_graph = StateGraph(GraphState)
aftersale_agent_graph.add_node("aftersale_assistant", aftersale_assistant)
aftersale_agent_graph.add_node("aftersale_tools", create_tools_node_with_hitl(TOOL_MGR.get_filted_tools("aftersale")))
aftersale_agent_graph.add_edge(START, "aftersale_assistant")
aftersale_agent_graph.add_conditional_edges("aftersale_assistant", check_resolution_status,
                                            {"resolved": END, "unresolved": "aftersale_tools"})
aftersale_agent_graph.add_edge("aftersale_tools", "aftersale_assistant")

# 投诉处理客服
complaint_agent_graph = StateGraph(GraphState)
complaint_agent_graph.add_node("complaint_assistant", complaint_assistant)
complaint_agent_graph.add_node("complaint_tools", create_tools_node_with_hitl(TOOL_MGR.get_filted_tools("complaint")))
complaint_agent_graph.add_edge(START, "complaint_assistant")
complaint_agent_graph.add_conditional_edges("complaint_assistant", check_resolution_status,
                                            {"resolved": END, "unresolved": "complaint_tools"})
complaint_agent_graph.add_edge("complaint_tools", "complaint_assistant")

# 通用客服
general_agent_graph = StateGraph(GraphState)
general_agent_graph.add_node("general_assistant", general_assistant)
general_agent_graph.add_node("general_tools", create_tools_node_with_hitl(TOOL_MGR.get_filted_tools("general")))
general_agent_graph.add_edge(START, "general_assistant")
general_agent_graph.add_conditional_edges("general_assistant", check_resolution_status,
                                            {"resolved": END, "unresolved": "general_tools"})
general_agent_graph.add_edge("general_tools", "general_assistant")

# 构建主智能体图
main_graph = StateGraph(GraphState)
# 添加节点
main_graph.add_node("load_memory", load_memory)
main_graph.add_node("summarizer", summarizer)
main_graph.add_node("router", router)
main_graph.add_node("presale", presale_agent_graph.compile())
main_graph.add_node("aftersale", aftersale_agent_graph.compile())
main_graph.add_node("complaint", complaint_agent_graph.compile())
main_graph.add_node("general", general_agent_graph.compile())

# 定义边
main_graph.add_edge(START, "load_memory")
main_graph.add_edge("load_memory", "summarizer")
main_graph.add_edge("summarizer", "router")
main_graph.add_conditional_edges("router",
                                 lambda state: state["customer_intent"].intent,  # 直接返回分类结果字符串
                                 {
                                     "presale": "presale",
                                     "aftersale": "aftersale",
                                     "complaint": "complaint",
                                     "general": "general"
                                 })
main_graph.add_edge("presale", END)
main_graph.add_edge("aftersale", END)
main_graph.add_edge("complaint", END)
main_graph.add_edge("general", END)
