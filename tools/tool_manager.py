import asyncio

from mcp_client.client import MCPClientManager
from tools.logistics import query_logistics
from tools.order import query_order, modify_order
from tools.product import query_product
from tools.refund import apply_refund
from tools.load_skill import load_skill
from tools.transfer_human import transfer_human
from tools.knowledge import search_knowledge

fallback_tool_list = [
    query_logistics,
    query_order,
    modify_order,
    query_product,
    apply_refund,
    load_skill,
    transfer_human,
    search_knowledge
]

class ToolManager:
    def __init__(self):
        # 初始化MCP客户端
        mcp_manager = MCPClientManager(
            mcp_server_config={
                "ecommerce": {
                    "url": "http://127.0.0.1:9123/mcp",
                    "transport": "streamable_http",
                },
            },
            local_fallback_tools=fallback_tool_list,
            connect_timeout=5.0,
            max_retries=2,
            health_check_interval=60.0,
        )

        # 获取完整工具列表
        self.mcp_tools = asyncio.run(mcp_manager.get_tools())

        # 定义不同子智能体的工具过滤列表
        self.tool_filter = {
            "presale": ["query_product", "search_knowledge", "load_skill"],
            "aftersale": ["query_logistics", "query_order", "modify_order", "apply_refund", "search_knowledge", "load_skill"],
            "complaint": ["query_logistics", "query_order", "apply_refund", "search_knowledge", "load_skill", "transfer_human"],
            "general": ["search_knowledge", "transfer_human"],
        }


    def get_filted_tools(self, agent_type: str) -> list:
        """按工具名筛选出子智能体需要的那部分,一行代码复用给所有子智能体"""
        allowed_names = self.tool_filter[agent_type]
        return [t for t in self.mcp_tools if t.name in allowed_names]


TOOL_MGR = ToolManager()