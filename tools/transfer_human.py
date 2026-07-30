from langchain_core.tools import tool

def _transfer_human() -> str:
    """转人工处理

    Returns:
        "success": 转人工操作是否成功
        "message": 结果消息
    """
    return {
        "success": True,
        "message": "已经将对话转人工客服处理"
    }

@tool
def transfer_human() -> str:
    """转人工处理"""
    return _transfer_human()