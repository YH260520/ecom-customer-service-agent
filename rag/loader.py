import os
import re
from pathlib import Path
from datetime import datetime
from langchain_core.documents import Document

def extract_frontmatter_metadata(content: str) -> tuple[dict, str]:
    """
    解析 Markdown 文件头部的 YAML Front Matter(如果存在)。
    格式示例:
    ---
    category: 退款政策
    version: 2.1
    author: 客服知识库团队
    ---
    正文内容...

    返回:(元数据字典, 去除 Front Matter 后的正文内容)
    """
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return {}, content   # 没有 Front Matter

    raw_yaml, remaining_content = match.group(1), match.group(2)

    metadata = {}
    for line in raw_yaml.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata, remaining_content


def load_markdown_files_with_metadata(knowledge_base_dir: str) -> list[Document]:
    """加载 Markdown 文件,并附加文件系统元数据 + Front Matter 元数据"""
    docs = []
    md_paths = list(Path(knowledge_base_dir).rglob("*.md"))

    if not md_paths:
        raise FileNotFoundError(f"在 {knowledge_base_dir} 下没有找到任何 .md 文件")

    for path in md_paths:
        raw_content = path.read_text(encoding="utf-8")

        # 提取 Front Matter 元数据,并拿到去除 Front Matter 后的正文
        frontmatter_meta, content = extract_frontmatter_metadata(raw_content)

        docs.append(Document(page_content=content, metadata=frontmatter_meta))

    print(f"✅ 共加载 {len(docs)} 个 Markdown 文件,并附加元数据")
    return docs