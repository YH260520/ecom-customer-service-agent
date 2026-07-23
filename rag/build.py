import os
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from dashscope import TextEmbedding

from rag.chunker import split_markdown_documents
from rag.loader import load_markdown_files_with_metadata

def main():
    load_dotenv()
    knowledge_base_dir = "./knowledge"
    docs = load_markdown_files_with_metadata(knowledge_base_dir)
    chunks = split_markdown_documents(docs, chunk_size=500, chunk_overlap=50)
    # 创建Qdrant客户端,连接到云服务器
    client = QdrantClient(url=os.getenv("QDRANT_CLOUD_CLUSTER_URL"),
                          api_key=os.getenv("QDRANT_CLOUD_CLUSTER_API_KEY"),
                          cloud_inference=True)

    # 如果 collection 不存在则创建(避免重复运行报错)
    collection_name = "ecom_knowledge"
    embedding_dim = 1024
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
        )

    points = []
    embedding_model = "qwen3.7-text-embedding"
    for chunk in chunks:
        # 生成嵌入向量
        response = TextEmbedding.call(api_key=os.getenv("DASHSCOPE_API_KEY"),
                                      model=embedding_model,
                                      input=chunk.page_content,
                                      distance=embedding_dim)
        embedding_vector = response.output["embeddings"][0]["embedding"]

        # 创建数据点
        point = models.PointStruct(id = uuid.uuid4(),
                                   vector = embedding_vector,
                                   payload={"text": chunk.page_content, **chunk.metadata})
        points.append(point)

    # 批量导入数据库
    client.upsert(collection_name=collection_name, points=points)
    print(f"已将 {len(points)} 条文本块嵌入并存储到 '{collection_name}'.")

if __name__ == "__main__":
    main()
