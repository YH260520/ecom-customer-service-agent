"""MCP Server：通过 Streamable HTTP 暴露电商工具服务。

启动方式：python mcp_server/server.py
默认监听：http://127.0.0.1:9123/mcp
"""

import json
from mcp.server.fastmcp import FastMCP
from tools.order import _query_order, _list_user_orders
from tools.product import _query_product
from tools.logistics import _query_logistics, _modify_logistics
from tools.refund import _exec_refund
from tools.knowledge import _search_knowledge
from tools.transfer_human import _transfer_human
from tools.load_skill import _load_skill
from typing import Optional

mcp = FastMCP("ecommerce", host="127.0.0.1", port=9123)


@mcp.tool()
def query_order(order_id: str) -> str:
    """根据订单号查询订单详情，包括状态、商品、物流单号等信息。

    Args:
        order_id: 订单号

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为订单详细信息；如果失败，为失败原因描述
        }
    """
    result = _query_order(order_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def list_user_orders(customer_id: str) -> dict:
    """根据用户ID查询用户的所有订单详情。

    Args:
        customer_id: 用户ID

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为当前用户全部订单列表；如果失败，为失败原因描述
        }
    """
    result = _list_user_orders(customer_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def query_product(category: str) -> str:
    """根据商品类别查询此类商品列表，包括商品ID、名称、价格、库存、描述、参数等。

    Args:
        category: 查询的商品类别，目前只支持6个类型["家用电器", "手机", "数码", "服装鞋帽", "电脑", "数码生鲜"]

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为查询的商品类型列表，包括商品ID、名称、价格、库存、描述、参数等；
                               如果失败，为失败原因描述
        }
    """
    result = _query_product(category)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def query_logistics(order_id: str) -> str:
    """根据快递单号查询物流信息。

    Args：
        tracking_number：快递单号

    return:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为快递单详细信息；如果失败，为失败原因描述
        }
    """
    result = _query_logistics(order_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def modify_logistics(
    tracking_number: str,
    recipient: Optional[str] = None,
    phone_number: Optional[str] = None,
    destination: Optional[str] = None
) -> dict:
    """根据物流单号修改物流信息，仅更新传入不为None的字段。

    Args:
        tracking_number: 物流单号【必填】
        recipient: 收件人名称，不传则不更新
        phone_number: 收件手机号，不传则不更新
        destination: 收货地址，不传则不更新

    Returns:
        {
            "success": 修改是否成功
            "message": 结果消息，如果成功，为更新成功描述；如果失败，为失败原因描述
        }
    """
    result = _modify_logistics(tracking_number, recipient, phone_number, destination)
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def exec_refund(order_id: str) -> str:
    """为指定订单申请退款。

    Args:
        order_id: 订单号

    Returns:
        {
            "success": 退款是否成功
            "message": 退款结果消息
        }
    """
    result = _exec_refund(order_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def search_knowledge(query: str, top_k: int = 3) -> str:
    """检索京东的政策与帮助文档。
       当顾客询问规则、流程、时效、是否支持等政策类问题时使用。
       返回值是字典，包含查询字符串，结果列表，每条结果包含知识库文档内容和相关性分数。
       请基于检索结果回答，不要编造政策。

    Args:
        query: 查询的文本块
        top_k: 返回的最相关文本块数量

    Returns:
        {
          "query": 查询的文本块,
          "results": [
                {
                    "text": 结果文本块
                    "score": 相关性分数
                }, ...
          ]
        }
    """
    result = _search_knowledge(query, top_k=top_k)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def transfer_human() -> str:
    """转人工处理

    Returns:
        "success": 转人工操作是否成功
        "message": 结果消息
    """
    result = _transfer_human()
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def load_skill(skill_name: str) -> str:
    """
    当判断某个技能（如退款流程）与当前用户请求相关时，调用此工具加载该技能的完整操作指南。
    参数 skill_name 必须是系统提示词中列出的技能名称之一。

    Args:
        skill_name: 技能名

    Returns:
        str: 技能的完整操作指南
    """
    result = _load_skill(skill_name)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
