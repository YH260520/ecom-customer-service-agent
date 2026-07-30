from langchain_core.tools import tool

def _exec_refund(order_id: str) -> dict:
    """为指定订单申请退款。

    Args:
        order_id: 订单号

    Returns:
        {
            "success": 退款是否成功
            "message": 退款结果消息
        }
    """
    return {
        "success": True,
        "message": "退款申请成功"
    }

@tool
def exec_refund(order_id: str, reason: str) -> dict:
    """为指定订单申请退款。

    Args:
        order_id: 订单号

    Returns:
        {
            "success": 退款是否成功
            "message": 退款结果消息
        }
    """
    return _exec_refund(order_id, reason)
