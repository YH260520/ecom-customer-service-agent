from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from agent.skills import SKILL_INDEX_PROMPT
from prompt import *
from agent.state import *
from tools import *

import os

MAX_MESSAGE_LENGTH = 10
KEEP_RECENT_LENGTH = 3



# 定义节点
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
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(PRESALE_TOOLS)

    # 拼接提示词：客服角色+技能+（长期记忆）+（历史对话摘要）+近期对话
    system_message = PRESALE_PROMPT + SKILL_INDEX_PROMPT
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
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(AFTERSALE_TOOLS)

    # 拼接提示词：客服角色+技能+（长期记忆）+（历史对话摘要）+近期对话
    system_message = AFTERSALE_PROMPT + SKILL_INDEX_PROMPT
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
    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).bind_tools(COMPLAINT_TOOLS)

    # 拼接提示词：客服角色+技能+（长期记忆）+（历史对话摘要）+近期对话
    system_message = COMPLAINT_PROMPT + SKILL_INDEX_PROMPT
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