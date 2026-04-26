from __future__ import annotations
from pathlib import Path
from core.semantic_chunking import dedupe_keep_order

# 注意：为了支持轻量模式，重型 AI 库（chromadb, llama_index）现在都在函数内部按需导入

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
COLLECTION_NAME = "civil_code"

# 优先使用本地模型（安装包或构建目录）
LOCAL_MODEL_PATH = BASE_DIR.parent / "models" / "bge-small-zh-v1.5"
BUILD_MODEL_PATH = BASE_DIR.parent / "build" / "models" / "bge-small-zh-v1.5"

if LOCAL_MODEL_PATH.exists():
    EMBED_MODEL_NAME = str(LOCAL_MODEL_PATH)
elif BUILD_MODEL_PATH.exists():
    EMBED_MODEL_NAME = str(BUILD_MODEL_PATH)
else:
    EMBED_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

KEYWORD_MAP: dict[str, str] = {
    "食品安全": "《食品安全法》关键条款：生产经营许可、违规添加、虚假标注",
    "环境污染": "《环境保护法》关键条款：污染物排放、违规处置废物",
    "劳动违法": "《劳动合同法》关键条款：克扣工资、拒签合同、违规解雇",
    "无证经营": "《行政许可法》关键条款：未经许可经营、超范围经营",
    "欺诈": "《消费者权益保护法》关键条款：虚假宣传、价格欺诈",
    "拆迁": "《国有土地上房屋征收与补偿条例》关键条款：强制拆迁、补偿标准",
    "非法集资": "《防范和处置非法集资条例》关键条款：未经许可吸收资金",
    "安全生产": "《安全生产法》关键条款：违规操作、隐患整改",
}


def retrieve_legal_context(contract_text: str) -> str:
    """
    双路检索：语义向量 Top-3 + 关键词强制召回，合并去重后返回法条上下文字符串。
    """
    import os
    if os.getenv("SKIP_RAG", "true").lower() == "true":
        return "（RAG 法律库已通过配置禁用，将基于通用法律知识进行研判）"

    # 动态导入重型库
    from llama_index.core import Settings
    Settings.llm = None

    if not VECTOR_STORE_DIR.exists():
        return "（本地法律检索库未就绪，将基于通用法律知识进行研判）"

    try:
        from llama_index.core import Settings, VectorStoreIndex
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        from llama_index.vector_stores.chroma import ChromaVectorStore
        import chromadb

        Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
        client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
        collection = client.get_or_create_collection(COLLECTION_NAME)
    except Exception as e:
        return f"（法律库检索系统初始化失败: {e}，将基于通用法律知识进行研判）"

    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core import VectorStoreIndex
    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # 路径一：分段语义检索（解决整页合同文本向量高度淡化、稀释，导致对不上具体法条的缺陷）
    import re
    clauses = re.split(r'(?=\b第[一二三四五六七八九十]+条\b|条款)|\n+', contract_text)
    clauses = [c.strip() for c in clauses if len(c.strip()) > 10]
    clauses = clauses[:15]  # 限制前15段，防阻塞超时

    retriever = index.as_retriever(similarity_top_k=2)
    semantic_hits: list[str] = []
    
    for clause in clauses:
        try:
            nodes = retriever.retrieve(clause)
            for n in nodes:
                node = getattr(n, "node", None)
                text = None
                if node is not None:
                    if hasattr(node, "get_content"):
                        text = node.get_content()
                    else:
                        text = getattr(node, "text", None)
                    
                    # ==== 新增：自动附带法规出处 ====
                    metadata = getattr(node, "metadata", {})
                    file_name = metadata.get("file_name", "") or ""
                    source_title = ""
                    if "beijing_rental_regulations" in file_name:
                        source_title = "《北京市住房租赁条例》"
                    elif "civil_code" in file_name:
                        source_title = "《民法典》"
                    elif "urban_housing_lease" in file_name:
                        source_title = "《最高法租赁纠纷司法解释》"
                    elif "rental_regulation" in file_name:
                        source_title = "《住房租赁管理条例(参考)》"

                    if source_title and text:
                        text = f"【来源：{source_title}】\n{text}"

                if not text:
                    text = str(n)
                if text:
                    semantic_hits.append(text)
        except Exception:
            pass

    # 路径二：关键词强制召回
    forced_hits: list[str] = []
    for keyword, hint in KEYWORD_MAP.items():
        if keyword in contract_text:
            forced_hits.append(f"[关键词召回] {keyword}：{hint}")

    merged = dedupe_keep_order([*semantic_hits, *forced_hits])
    return "\n\n".join(merged) if merged else "（未检索到直接关联法条，将基于通用法律知识研判）"


def is_rag_available() -> bool:
    """检查 RAG 是否可用（目录存在且未被显式禁用）"""
    import os
    # 默认禁用 RAG 以确保在所有设备上的极致启动速度和稳定性
    if os.getenv("SKIP_RAG", "true").lower() == "true":
        return False
    return VECTOR_STORE_DIR.exists()

