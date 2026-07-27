import os
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams
from dashscope import TextEmbedding

from rag.chunker import split_markdown_documents
from rag.loader import load_markdown_files_with_metadata

def build_knowledge_base(client: QdrantClient, dense_embedding_model: str, embedding_dim: int):
    knowledge_base_dir = "./knowledge"
    docs = load_markdown_files_with_metadata(knowledge_base_dir)
    chunks = split_markdown_documents(docs, chunk_size=500, chunk_overlap=50)

    # 如果 collection 不存在则创建(避免重复运行报错)
    collection_name = "ecom_knowledge"
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={"dense": VectorParams(size=embedding_dim, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )

    # 初始化数据点
    points = []
    for chunk in chunks:
        # 生成嵌入向量
        response = TextEmbedding.call(api_key=os.getenv("DASHSCOPE_API_KEY"),
                                      model=dense_embedding_model,
                                      input=chunk.page_content,
                                      distance=embedding_dim)
        dense_embed_vector = response.output["embeddings"][0]["embedding"]

        # 创建数据点
        point = models.PointStruct(id = uuid.uuid4(),
                                   vector = {"dense": dense_embed_vector,
                                             "sparse": models.Document(text=chunk.page_content, model="Qdrant/bm25")},
                                   payload={"text": chunk.page_content, **chunk.metadata})
        points.append(point)

    # 批量导入数据库
    client.upsert(collection_name=collection_name, points=points)
    print(f"已将 {len(points)} 条文本块嵌入并存储到 '{collection_name}'.")

def build_router_template(client: QdrantClient, dense_embedding_model: str, embedding_dim: int):
    router_template_docs = {
    "presale": [
        "这款产品支持什么颜色和尺寸？",
        "现在下单有什么满减或优惠券吗？",
        "这个型号还有货吗，什么时候能发货？",
        "这个和隔壁那款有什么区别，哪个更适合我？",
    ],
    "aftersale": [
        "我的订单大概什么时候能到？",
        "快递显示已经三天没更新了，是不是卡在哪了？",
        "商品尺码不合适，想申请退货怎么操作？",
        "收到的东西有破损，可以换一个吗？",
        "申请的退款审核多久能到账？",
    ],
    "complaint": [
        "你们的服务态度真的很差！",
        "这个问题已经反馈好几次了，一直没人处理！",
        "东西坏了还让我自己出运费，太不合理了，必须给我补偿！",
        "找了三次客服都没解决，你们是不是根本不重视用户？",
        "如果今天还不给我答复，我就去平台投诉了！",
    ],
    "general": [
        "你好，在吗？",
        "谢谢你的帮助，辛苦了",
        "我想问一下那个",
    ]
    }

    # 如果 collection 不存在则创建(避免重复运行报错)
    collection_name = "router_template"
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )

    # 初始化数据点
    points = []
    for intent, templates in router_template_docs.items():
        for template in templates:
            # 生成嵌入向量
            response = TextEmbedding.call(api_key=os.getenv("DASHSCOPE_API_KEY"),
                                          model=dense_embedding_model,
                                          input=template,
                                          distance=embedding_dim)
            dense_embed_vector = response.output["embeddings"][0]["embedding"]

            # 创建数据点
            point = models.PointStruct(id=uuid.uuid4(),
                                       vector=dense_embed_vector)
            points.append(point)

    # 批量导入数据库
    client.upsert(collection_name=collection_name, points=points)
    print(f"已将 {len(points)} 条文本块嵌入并存储到 '{collection_name}'.")

if __name__ == "__main__":
    load_dotenv()
    # 创建Qdrant客户端,连接到云服务器
    client = QdrantClient(url=os.getenv("QDRANT_CLOUD_CLUSTER_URL"),
                          api_key=os.getenv("QDRANT_CLOUD_CLUSTER_API_KEY"),
                          cloud_inference=True)
    dense_embedding_model = "qwen3.7-text-embedding"
    embedding_dim = 1024
    build_router_template(client, dense_embedding_model, embedding_dim)
    build_knowledge_base(client, dense_embedding_model, embedding_dim)
