from tools.database import build_connection
from langchain_core.tools import tool
from typing import Optional

def _query_logistics(tracking_number: str) -> dict:
    """根据快递单号查询物流信息。

    Args：
        tracking_number：快递单号

    return:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为快递单详细信息；如果失败，为失败原因描述
        }
    """
    conn = build_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.logistics WHERE tracking_number = %s;", (tracking_number,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"success": False, "message": f"未找到快递单 {tracking_number}，请核实快递单号"}
    else:
        return {"success": True, "message": dict(row)}


@tool
def query_logistics(tracking_number: str) -> dict:
    """根据快递单号查询物流信息。

    Args：
        tracking_number：快递单号

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为快递单详细信息；如果失败，为失败原因描述
        }
    """
    return _query_logistics(tracking_number)


def _modify_logistics(
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
    # 收集需要更新的字段与参数
    update_parts = []
    params = []

    if recipient is not None:
        update_parts.append("recipient = %s")
        params.append(recipient)
    if phone_number is not None:
        update_parts.append("phone_number = %s")
        params.append(phone_number)
    if destination is not None:
        update_parts.append("destination = %s")
        params.append(destination)

    # 防护：如果没有任何字段需要更新，直接返回，避免生成无效 SQL
    if not update_parts:
        return {"success": False, "msg": "未提供需要更新的字段", "row_count": 0}

    # 拼接SQL（字段名是代码内硬编码的白名单，非用户输入，不存在注入风险）
    set_clause = ", ".join(update_parts)
    sql = f"""
        UPDATE public.logistics
        SET {set_clause}
        WHERE tracking_number = %s;
    """
    conn = build_connection()
    cur = conn.cursor()
    cur.execute(sql, (tracking_number,))
    conn.commit()
    row_cnt = cur.rowcount
    cur.close()
    conn.close()
    if row_cnt == 0:
        return {"success": False, "msg": "未查询到该物流单号", "row_count": 0}
    else:
        return {"success": True, "msg": f"成功更新{row_cnt}条物流记录", "row_count": row_cnt}

@tool
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
    return _modify_logistics(tracking_number, recipient, phone_number, destination)
