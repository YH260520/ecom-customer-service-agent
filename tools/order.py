from tools.database import build_connection
from langchain_core.tools import tool

def _query_order(order_id: str) -> dict:
    """根据订单号查询订单详情，包括状态、商品、物流单号等信息。

    Args:
        order_id: 订单号

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为订单详细信息；如果失败，为失败原因描述
        }
    """
    conn = build_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.orders WHERE order_id = %s;", (order_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"success": False, "error": f"未找到订单 {order_id}，请核实单号"}
    else:
        return {"success": True, "logistics": dict(row)}


@tool
def query_order(order_id: str) -> dict:
    """根据订单号查询订单详情，包括状态、商品、物流单号等信息。

    Args:
        order_id: 订单号

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为订单详细信息；如果失败，为失败原因描述
        }
    """
    return _query_order(order_id)

def _list_user_orders(customer_id: str) -> dict:
    """根据用户ID查询用户的所有订单详情。

    Args:
        customer_id: 用户ID

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为当前用户全部订单列表；如果失败，为失败原因描述
        }
    """
    conn = build_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.orders WHERE customer_id = %s;", (customer_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return {"success": False, "message": f"未找到用户 {customer_id}的订单，请核实情况"}
    else:
        return {"success": True, "message": [dict(row) for row in rows]}

@tool
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
    return _list_user_orders(customer_id)