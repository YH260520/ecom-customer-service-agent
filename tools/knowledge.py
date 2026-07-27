"""知识库检索工具：通过向量检索回答 FAQ、政策类问题。

与查订单/查物流这类「结构化数据查询」工具不同，
search_knowledge 面向非结构化文本（退换货政策、配送说明、FAQ 等），
返回 Top-K 命中片段及其来源，由 LLM 引用回答。

"""
import os
from qdrant_client import QdrantClient, models
from dashscope import TextEmbedding
from langchain_core.tools import tool


def _search_knowledge(query: str, top_k: int = 3) -> dict:
    """检索退换货政策、配送说明、会员权益、FAQ 等知识库内容。
       返回值是字典，包含查询字符串，结果列表，每条结果包含知识库文档内容和相关性分数。

    Returns:
        {
          "query": str,
          "results": [
                {
                    "text": str
                    "score": float
                }, ...
          ]
        }
    """
    dense_embedding_model = "qwen3.7-text-embedding"
    embedding_dim = 1024
    collection_name = "ecom_knowledge"
    client = QdrantClient(url=os.getenv("QDRANT_CLOUD_CLUSTER_URL"),
                          api_key=os.getenv("QDRANT_CLOUD_CLUSTER_API_KEY"),
                          cloud_inference=True)

    query_embedding_result = TextEmbedding.call(api_key=os.getenv("DASHSCOPE_API_KEY"),
                                                model=dense_embedding_model,
                                                input=query,
                                                distance=embedding_dim)
    dense_query_vector = query_embedding_result.output["embeddings"][0]["embedding"]
    # 在 Qdrant 中搜索与查询向量最相似的向量
    search_results = client.query_points(
        collection_name=collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_query_vector,
                using="dense",
                limit=top_k * 2
            ),
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="Qdrant/bm25"
                ),
                using="sparse",
                limit=top_k * 2
            )
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k
    )

    return {
        "query": query,
        "results": [
            {
                "text": search_result.payload["text"],
                "score": search_result.score
            } for search_result in search_results.points
        ]
    }

@tool
def search_knowledge(query: str, top_k: int = 3) -> dict:
    """检索退换货政策、配送说明、会员权益、FAQ 等知识库内容。
       返回值是字典，包含查询字符串，结果列表，每条结果包含知识库文档内容和相关性分数。

    Returns:
        {
          "query": str,
          "results": [
                {
                    "text": str
                    "score": float
                }, ...
          ]
        }
    """
    return _search_knowledge(query, top_k)