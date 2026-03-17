from __future__ import annotations

from pathlib import Path

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore


DATA_DIR = Path("data")
VECTOR_STORE_DIR = Path("vector_store")
COLLECTION_NAME = "civil_code"
EMBED_MODEL_NAME = "BAAI/bge-small-zh-v1.5"


def main() -> None:
    """
    一次性脚本：读取 data/ 下所有 .txt 法条文本，构建向量库并写入本地 ChromaDB。

    约束：
    - Settings.llm = None（建库阶段不需要 LLM）
    - Settings.embed_model 必须显式指定为 HuggingFaceEmbedding（严禁使用 OpenAI embedding）
    - ChromaDB 使用 PersistentClient，路径为 ./vector_store，collection 为 civil_code
    """

    Settings.llm = None
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"未找到数据目录：{DATA_DIR.resolve()}")

    txt_files = sorted(DATA_DIR.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"{DATA_DIR.resolve()} 下未找到任何 .txt 文件")

    documents = SimpleDirectoryReader(input_dir=str(DATA_DIR), required_exts=[".txt"]).load_data()

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    collection = client.get_or_create_collection(COLLECTION_NAME)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    print("向量库构建完成")


if __name__ == "__main__":
    main()

