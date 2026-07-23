from langgraph.store.base import BaseStore
from langchain_core.messages import SystemMessage
from agent.state import *
from langchain_openai import ChatOpenAI

from prompt.memory_extraction import MEMORY_EXTRACTION_PROMPT

import os


async def extract_and_save_memory(
    messages: list,
    user_id: str,
    store: BaseStore,
) -> UserProfile:
    """
    独立的记忆提取函数,不属于 graph 的任何节点,
    可以在任意时机(对话结束时)被单独调用。
    """
    namespace = ("memory", user_id)
    existing = await store.aget(namespace, "profile")
    existing_profile = UserProfile(**existing.value) if existing else UserProfile()

    llm = ChatOpenAI(
        model="qwen3.7-max",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ).with_structured_output(UserProfile)

    updated_profile = await llm.ainvoke([
        SystemMessage(content=MEMORY_EXTRACTION_PROMPT.format(
            existing_profile_json=existing_profile.model_dump_json(indent=2)
        )), *messages
    ])

    await store.aput(namespace, "profile", updated_profile.model_dump())
    return updated_profile

async def end_conversation(thread_id: str, user_id: str, app, store: BaseStore):
    """
    客户端在用户点击'结束对话'或关闭聊天窗口时调用这个函数,
    只在这一刻触发一次记忆提取,而不是每轮对话都提取。
    """
    config = {"configurable": {"thread_id": thread_id}}

    # 从 checkpointer 里取出这个 thread 积累的完整消息历史,不需要手动拼接
    state_snapshot = await app.aget_state(config)
    full_messages = state_snapshot.values.get("messages", [])

    if not full_messages:
        return   # 空对话,没什么可提取的

    profile = await extract_and_save_memory(full_messages, user_id, store)
    print(f"✅ 对话 {thread_id} 结束,已更新用户 {user_id} 的画像:{profile.summary}")
