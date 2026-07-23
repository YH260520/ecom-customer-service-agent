import asyncio
from mcp_server.server import search_knowledge
from mcp_client.client import MCPClientManager
from tools.logistics import query_logistics
from tools.order import query_order
from tools.product import query_product
from tools.refund import apply_refund
from tools.load_skill import load_skill

fallback_tool_list = [
    query_logistics,
    query_order,
    query_product,
    apply_refund,
    search_knowledge,
    load_skill
]

def filter_tools(tools: list, allowed_names: set[str]) -> list:
    """按工具名筛选出子智能体需要的那部分,一行代码复用给所有子智能体"""
    return [t for t in tools if t.name in allowed_names]

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

mcp_tool_list = asyncio.run(mcp_manager.get_tools())
PRESALE_TOOLS = filter_tools(mcp_tool_list, {"query_product", "search_knowledge"}) + [load_skill]
AFTERSALE_TOOLS = filter_tools(mcp_tool_list, {"query_logistics", "query_order", "apply_refund", "search_knowledge"}) + [load_skill]
COMPLAINT_TOOLS = filter_tools(mcp_tool_list, {"query_logistics", "query_order", "apply_refund", "search_knowledge"}) + [load_skill]
