from tools.database import build_connection
from langchain_core.tools import tool
from typing import Literal

def _query_product(category: Literal["家用电器", "手机", "数码", "服装鞋帽", "电脑", "食品生鲜"]) -> dict:
    """根据商品类别查询此类商品列表，包括商品ID、名称、价格、库存、描述、参数等。

    Args:
        category: 查询的商品类别，目前只支持6个类型["家用电器", "手机", "数码", "服装鞋帽", "电脑", "食品生鲜"]

    Returns:
        {
            "success": 查询是否成功
            "message": 结果消息，如果成功，为查询的商品类型列表，包括商品ID、名称、价格、库存、描述、参数等；
                               如果失败，为失败原因描述
        }
    """
    conn = build_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.products WHERE category = %s;", (category,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return {"success": False, "error": f"未找到{category}类型商品"}
    else:
        return {"success": True, "products": [dict(product) for product in rows]}

@tool
def query_product(category: str) -> dict:
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
    return _query_product(category)