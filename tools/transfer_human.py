from langchain_core.tools import tool

def _transfer_human() -> str:
    """转人工处理"""
    return "已经转人工"

@tool
def transfer_human() -> str:
    """转人工处理"""
    return _transfer_human()