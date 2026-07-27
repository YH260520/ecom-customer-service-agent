"""MCP Server：通过 Streamable HTTP 暴露电商工具服务。

启动方式：python mcp_server/server.py
默认监听：http://127.0.0.1:9123/mcp
"""

import json
from mcp.server.fastmcp import FastMCP
from tools.order import _query_order, _modify_order
from tools.product import _query_product
from tools.logistics import _query_logistics
from tools.refund import _apply_refund
from tools.knowledge import _search_knowledge
from tools.transfer_human import _transfer_human
from tools.load_skill import _load_skill

mcp = FastMCP("ecommerce", host="127.0.0.1", port=9123)


@mcp.tool()
def query_order(order_id: str) -> str:
    """根据订单号查询订单详情，包括订单状态、商品信息、金额、物流单号等"""
    result = _query_order(order_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def modify_order(order_id: str) -> str:
    """根据订单号修改收件人姓名、电话、地址。"""
    result = _modify_order(order_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def query_product(keyword: str) -> str:
    """根据商品名称关键词或商品ID查询商品信息，包括价格、库存、规格等。支持模糊搜索"""
    result = _query_product(keyword)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def query_logistics(order_id: str) -> str:
    """根据订单号查询物流轨迹信息，包括快递公司、运单号、运输状态和轨迹事件"""
    result = _query_logistics(order_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def apply_refund(order_id: str, reason: str) -> str:
    """为指定订单申请退款。注意：这是一个敏感操作，调用前应先与用户确认"""
    result = _apply_refund(order_id, reason)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def search_knowledge(query: str, top_k: int = 3) -> str:
    """检索京东的政策与帮助文档。
    当顾客询问规则、流程、时效、是否支持等政策类问题时使用。
    返回 Top-K 命中片段及来源文档，请基于检索结果回答，不要编造政策。
    """
    result = _search_knowledge(query, top_k=top_k)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def transfer_human() -> str:
    """转人工处理"""
    result = _transfer_human()
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def load_skill(skill_name: str) -> str:
    """
        当判断某个技能（如退款流程）与当前用户请求相关时，调用此工具加载该技能的完整操作指南。
        参数 skill_name 必须是系统提示词中列出的技能名称之一。
    """
    result = _load_skill(skill_name)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
