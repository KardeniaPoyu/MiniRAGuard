"""
运行前需确保 .env 已配置（vision_tool 和 reviewer 需要真实 API Key）。

本脚本仅测试 rag_tool 的向量检索与关键词召回逻辑，不依赖 pytest。
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Workaround for OpenMP duplicate library and DLL paths on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
_venv_path = os.path.abspath(".venv")
_torch_lib = os.path.join(_venv_path, "Lib", "site-packages", "torch", "lib")
if os.path.isdir(_torch_lib):
    os.environ['PATH'] = _torch_lib + os.pathsep + os.environ['PATH']
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(_torch_lib)
        except Exception:
            pass



REPO_ROOT = Path(__file__).resolve().parent
VECTOR_STORE_DIR = REPO_ROOT / "vector_store"
VECTOR_STORE_BAK_DIR = REPO_ROOT / "vector_store.__bak__"


def _require_deps() -> None:
    """
    rag_tool 依赖 llama-index 与 chromadb；若未安装则给出提示并退出。
    """

    missing: list[str] = []
    try:
        import chromadb  # noqa: F401
    except ModuleNotFoundError:
        missing.append("chromadb")

    try:
        import llama_index  # noqa: F401
    except ModuleNotFoundError:
        missing.append("llama-index-core (llama_index)")

    if missing:
        print("依赖缺失，无法运行 rag_tool 测试：", ", ".join(missing))
        print("请先安装后端依赖，例如：")
        print("  pip install -r rent_agent_backend/requirements.txt")
        print("或按需安装：")
        print("  pip install llama-index-core llama-index-vector-stores-chroma "
              "llama-index-embeddings-huggingface chromadb sentence-transformers")
        raise SystemExit(1)


def _import_retrieve_legal_context():
    # 确保可从仓库根目录导入 core/rag_tool.py
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from core.rag_tool import retrieve_legal_context  # noqa: WPS433 (runtime import)

    return retrieve_legal_context


def _ensure_vector_store_exists() -> None:
    """
    若向量库不存在，则运行一次 scripts/build_index.py 构建。

    注意：首次构建可能会下载 embedding 模型（约 100MB）。
    """

    if VECTOR_STORE_DIR.exists():
        return

    build_script = REPO_ROOT / "scripts" / "build_index.py"
    assert build_script.exists(), f"缺少构建脚本：{build_script}"

    import runpy

    runpy.run_path(str(build_script), run_name="__main__")
    assert VECTOR_STORE_DIR.exists(), "向量库构建脚本执行后仍未生成 ./vector_store"


def test_exception_path_missing_vector_store() -> None:
    """
    异常路径：./vector_store 不存在时应抛出 FileNotFoundError。
    """

    retrieve_legal_context = _import_retrieve_legal_context()

    moved_aside = False
    try:
        if VECTOR_STORE_DIR.exists():
            if VECTOR_STORE_BAK_DIR.exists():
                shutil.rmtree(VECTOR_STORE_BAK_DIR)
            shutil.move(str(VECTOR_STORE_DIR), str(VECTOR_STORE_BAK_DIR))
            moved_aside = True

        try:
            retrieve_legal_context("测试合同文本：押金、提前退租、违约金。")
            assert False, "预期抛出 FileNotFoundError，但未抛出"
        except FileNotFoundError:
            print("异常路径通过：vector_store 缺失时会抛 FileNotFoundError")
    finally:
        if moved_aside:
            if VECTOR_STORE_DIR.exists():
                shutil.rmtree(VECTOR_STORE_DIR)
            shutil.move(str(VECTOR_STORE_BAK_DIR), str(VECTOR_STORE_DIR))


def test_normal_path_retrieve_and_keyword_recall() -> None:
    """
    正常路径：语义检索 Top-3 + 关键词强制召回，返回合并后的字符串。
    """

    _ensure_vector_store_exists()
    retrieve_legal_context = _import_retrieve_legal_context()

    contract_text = (
        "本合同约定押金为两个月租金。租客提前退租，押金不退。"
        "未经允许不得转租，另有违约金条款。房屋维修由房东负责。"
    )
    ctx = retrieve_legal_context(contract_text)

    assert isinstance(ctx, str)
    assert ctx.strip(), "检索结果不应为空字符串"

    # 关键词强制召回断言（至少验证几个关键字确实能拼入）
    assert "[关键词召回] 押金" in ctx
    assert "[关键词召回] 提前退租" in ctx
    assert "[关键词召回] 转租" in ctx
    assert "[关键词召回] 房屋维修" in ctx
    assert "[关键词召回] 违约金" in ctx

    print("正常路径通过：检索结果非空，且关键词召回生效")


if __name__ == "__main__":
    _require_deps()
    test_exception_path_missing_vector_store()
    test_normal_path_retrieve_and_keyword_recall()
    print("rag_tool测试通过")

