import os
import asyncio
import selectors

from langchain_core.messages import HumanMessage
from agent.graph import *
from mcp_client.client import MCPClientManager
from langgraph.store.postgres import AsyncPostgresStore


def build_db_uri() -> str:
    """从环境变量拼接数据库连接字符串"""
    pg_password = os.getenv("POSTGRES_PASSWORD")
    pg_port = os.getenv("POSTGRE_PORT")
    return f"postgresql://postgres:{pg_password}@localhost:{pg_port}/customer_service_db"


async def run_agent(store):
    """编译 agent 并执行一次会话"""
    config = {"configurable": {"thread_id": 1, "user_id": 123456}}
    agent = main_graph.compile(checkpointer=InMemorySaver(), store=store)

    result = await agent.ainvoke(
        {"messages": HumanMessage("我买的鞋子尺码不对，想退掉，订单号是 ORD-20240115-001")},
        config=config,
    )

    for m in result["messages"]:
        m.pretty_print()


async def main():
    db_uri = build_db_uri()

    async with (
        mcp_manager,
        AsyncPostgresStore.from_conn_string(db_uri) as store,
    ):
        await store.setup()
        await run_agent(store)


if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    )
