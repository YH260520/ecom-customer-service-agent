from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from qdrant_client import QdrantClient
from dashscope import TextEmbedding

from agent.skills import build_skill_prompt, filter_skills_by_agent, ALL_SKILLS
from mcp_client.client import MCPClientManager
from tools.tool_manager import TOOL_MGR
from prompt import *
from agent.state import *
from agent.utils import *


import os

MAX_MESSAGE_LENGTH = 10
KEEP_RECENT_LENGTH = 3

# 定义节点
async def load_memory(
    state: GraphState,
    config: RunnableConfig,
    *,
    store: BaseStore,   # LangGraph 会根据类型注解自动注入编译时传入的 store 实例
) -> dict:
    user_id = config["configurable"]["user_id"]
    namespace = ("memory", str(user_id))

    existing_memory = await store.aget(namespace, "profile")

    if not existing_memory:
        return {"user_memory": ""}   # 新用户,没有历史画像

    profile = UserProfile(**existing_memory.value)
    return {"user_memory": format_profile(profile)}

def summarizer(state: GraphState):
    # 如果对话长度小于最大限制，跳过摘要步骤
    messages = state["messages"]
    if len(messages) < MAX_MESSAGE_LENGTH:
        return {}

    # 获取历史摘要
    summary = state.get("summary", "")
    # 拆分：需要压缩的历史 vs 需要保留的最近消息
    to_summarize = messages[:-KEEP_RECENT_LENGTH]  # 前面要压缩的部分
    to_keep = messages[-KEEP_RECENT_LENGTH:]  # 最近2条，原样保留

    # 把待压缩的历史消息拼成文本，交给 LLM 生成摘要
    history_message = ""
    if summary:
        history_message += "此前摘要：{summary}"
    for m in to_summarize:
        if m.type == "human":
            history_message += f"\n用户：{m.content}"
        elif m.type == "ai":
            history_message += f"\n客服：{m.content}"
        elif m.type == "tool":
            history_message += f"\n工具结果：{m.content}"

    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )
    summary_prompt = [
        SystemMessage(SUMMARY_PROMPT),
        HumanMessage(history_message)
    ]
    summary_result = llm.invoke(summary_prompt)

    # 用 RemoveMessage 删除被压缩的原始消息
    remove_messages = [RemoveMessage(id=m.id) for m in to_summarize]

    # 更新摘要同时移除多余的历史消息
    return {
        "summary": summary_result.content, "messages": remove_messages
    }

def router(state: GraphState):
    # 使用级联系统进行路由识别
    # 第一层：密集向量余弦相似度，相似度>0.9进入下一层
    dense_embedding_model = "qwen3.7-text-embedding"
    embedding_dim = 1024
    collection_name = "router_template"
    client = QdrantClient(url=os.getenv("QDRANT_CLOUD_CLUSTER_URL"),
                          api_key=os.getenv("QDRANT_CLOUD_CLUSTER_API_KEY"),
                          cloud_inference=True)
    query_embedding_result = TextEmbedding.call(api_key=os.getenv("DASHSCOPE_API_KEY"),
                                                model=dense_embedding_model,
                                                input=state["messages"][-1].content,
                                                distance=embedding_dim)
    dense_query_vector = query_embedding_result.output["embeddings"][0]["embedding"]
    search_result = client.query_points(
        collection_name=collection_name,
        query=dense_query_vector,
        limit=1
    )
    if search_result.points[0].score > 0.85:
        return {"customer_intent": search_result.payload["intent"]}

    # 创建LLM实例
    llm = ChatOpenAI(
        model="qwen-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).with_structured_output(IntentClassification)

    # 拼接提示词：客服角色+（历史对话摘要）+近期对话
    system_message = ROUTER_PROMPT
    summary = state.get("summary", "")
    if summary:
        system_message += f"""

            ## 对话摘要
            以下是此前对话的摘要：{state['summary']}"""

    messages = [SystemMessage(system_message), *state["messages"]]
    llm_output = llm.invoke(messages)
    return {"customer_intent": llm_output}

async def presale_assistant(state: GraphState):
    # 创建LLM实例并绑定工具
    presale_tools = TOOL_MGR.get_filted_tools("presale")
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(presale_tools)

    # 拼接提示词：客服角色+技能+（长期记忆）+（历史对话摘要）+近期对话
    system_message = PRESALE_PROMPT + build_skill_prompt(filter_skills_by_agent(ALL_SKILLS, "presale"))
    user_memory = state.get("user_memory", "")
    if user_memory:
        system_message += f"""
        
        ## 历史画像
        该客户历史画像如下：
            {user_memory}
        请结合以上客户信息调整你的语气和回复策略"""

    summary = state.get("summary", "")
    if summary:
        system_message += f"""
        
        ## 对话摘要
        以下是此前对话的摘要：{state['summary']}"""

    messages = [SystemMessage(system_message), *state["messages"]]
    llm_output = llm.invoke(messages)
    return {"messages": llm_output}

async def aftersale_assistant(state: GraphState):
    # 创建LLM实例并绑定工具
    aftersale_tools = TOOL_MGR.get_filted_tools("aftersale")
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(aftersale_tools)

    # 拼接提示词：客服角色+技能+（长期记忆）+（历史对话摘要）+近期对话
    system_message = AFTERSALE_PROMPT + build_skill_prompt(filter_skills_by_agent(ALL_SKILLS, "aftersale"))
    user_memory = state.get("user_memory", "")
    if user_memory:
        system_message += f"""

            ## 历史画像
            该客户历史画像如下：
                {user_memory}
            请结合以上客户信息调整你的语气和回复策略"""

    summary = state.get("summary", "")
    if summary:
        system_message += f"""

            ## 对话摘要
            以下是此前对话的摘要：{state['summary']}"""

    messages = [SystemMessage(system_message), *state["messages"]]

    llm_output = llm.invoke(messages)
    return {"messages": llm_output}

async def complaint_assistant(state: GraphState):
    # 创建LLM实例并绑定工具
    complaint_tools = TOOL_MGR.get_filted_tools("complaint")
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(complaint_tools)

    # 拼接提示词：客服角色+技能+（长期记忆）+（历史对话摘要）+近期对话
    system_message = COMPLAINT_PROMPT + build_skill_prompt(filter_skills_by_agent(ALL_SKILLS, "complaint"))
    user_memory = state.get("user_memory", "")
    if user_memory:
        system_message += f"""

            ## 历史画像
            该客户历史画像如下：
                {user_memory}
            请结合以上客户信息调整你的语气和回复策略"""

    summary = state.get("summary", "")
    if summary:
        system_message += f"""

            ## 对话摘要
            以下是此前对话的摘要：{state['summary']}"""

    messages = [SystemMessage(system_message), *state["messages"]]

    llm_output = llm.invoke(messages)
    return {"messages": llm_output}

async def general_assistant(state: GraphState):
    # 创建LLM实例并绑定工具
    general_tools = TOOL_MGR.get_filted_tools("general")
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(general_tools)

    # 拼接提示词：客服角色+（长期记忆）+（历史对话摘要）+近期对话
    system_message = GENERAL_PROMPT
    user_memory = state.get("user_memory", "")
    if user_memory:
        system_message += f"""

            ## 历史画像
            该客户历史画像如下：
                {user_memory}
            请结合以上客户信息调整你的语气和回复策略"""

    summary = state.get("summary", "")
    if summary:
        system_message += f"""

            ## 对话摘要
            以下是此前对话的摘要：{state['summary']}"""

    messages = [SystemMessage(system_message), *state["messages"]]

    llm_output = llm.invoke(messages)
    return {"messages": llm_output}

def check_resolution_status(state: GraphState) -> Literal["resolved", "unresolved"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "unresolved"
    return "resolved"