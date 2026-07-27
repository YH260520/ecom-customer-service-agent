from tools.mock_data import ORDERS
from langchain_core.tools import tool


def _query_order(order_id: str) -> dict:
    """根据订单号查询订单详情，包括状态、商品、金额、物流等信息。"""
    order = ORDERS.get(order_id)
    if not order:
        return {"success": False, "error": f"未找到订单 {order_id}，请核实订单号"}
    return {"success": True, "order": order}

@tool
def query_order(order_id: str) -> dict:
    """根据订单号查询订单详情，包括状态、商品、金额、物流等信息。"""
    return _query_order(order_id)

def _modify_order(order_id: str) -> dict:
    """根据订单号修改收件人姓名、电话、地址。"""
    # order = ORDERS.get(order_id)
    # if not order:
    #     return {"success": False, "error": f"未找到订单 {order_id}，请核实订单号"}
    return {"success": True, "order": order}

@tool
def modify_order(order_id: str) -> dict:
    """根据订单号修改收件人姓名、电话、地址。"""
    return _modify_order(order_id)
