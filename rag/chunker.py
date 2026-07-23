from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def split_markdown_documents(
    docs: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    headers_to_split_on = [
        ("#", "标题1"),
        ("##", "标题2"),
        ("###", "标题3"),
    ]
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )

    final_chunks = []
    for doc in docs:
        header_chunks = header_splitter.split_text(doc.page_content)

        for idx, chunk in enumerate(header_chunks):
            # 关键步骤:把原始文档的元数据(文件类型、修改时间等)合并进每个 chunk
            # 注意合并顺序:先放原始 metadata,再放标题 metadata,避免同名字段被覆盖错
            chunk.metadata = {**doc.metadata, **chunk.metadata, "chunk_index": idx}

            if len(chunk.page_content) > chunk_size:
                sub_chunks = recursive_splitter.split_documents([chunk])
                # 二次切分产生的子块也要保留元数据(split_documents 本身会自动继承,这里做个保险)
                for sub_idx, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata.update({"sub_chunk_index": sub_idx})
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

    print(f"✅ 切分完成,共生成 {len(final_chunks)} 个文本块,元数据字段:{list(final_chunks[0].metadata.keys())}")
    return final_chunks
