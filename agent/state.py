from typing import Optional, Literal
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class IntentClassification(BaseModel):
    """用户消息分类结果,供路由节点强制约束 LLM 输出格式"""
    intent: Literal["presale", "aftersale", "complaint", "general"] = Field(
        description=(
            "用户消息所属类别:\n"
            "- presale:商品咨询、价格、促销活动、库存等购买前问题\n"
            "- aftersale:订单查询、物流、退换货、退款等购买后问题\n"
            "- complaint:客户表达不满、投诉、要求赔偿、情绪激烈的反馈\n"
            "- general:客户日常交流、闲聊等非诉求类型的消息或者需要进一步澄清客户意图时\n"
        )
    )
    confidence: float = Field(description="分类置信度,0到1之间")
    reasoning: str = Field(description="做出该分类判断的简要理由,用于日志追溯")

class GraphState(MessagesState):
    user_memory: str
    summary: str
    customer_intent: IntentClassification

class UserProfile(BaseModel):
    """用户长期画像结构,每轮对话结束后增量更新"""
    id: Optional[str] = Field(default=None, description="用户身份信息")
    preferences: list[str] = Field(default_factory=list, description="用户表现出的兴趣爱好、消费偏好")
    emotional_tendency: Optional[str] = Field(default=None, description="用户情绪倾向,如'容易急躁''重视服务态度''对价格敏感'")
    interested_products: list[str] = Field(default_factory=list, description="用户咨询/关注过的商品或品类")
    summary: Optional[str] = Field(default=None, description="一到两句话的综合画像摘要,用于快速理解该用户特点")

