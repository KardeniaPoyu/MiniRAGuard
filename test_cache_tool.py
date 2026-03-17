"""
运行前需确保 .env 已配置

独立测试脚本：验证 core/cache_tool.py 的 SQLite+MD5 缓存逻辑。
不依赖 pytest，使用 assert + print。
"""

from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
TEST_DB = REPO_ROOT / "cache.__test__.db"


def _import_cache_tool():
    from core import cache_tool  # noqa: WPS433 (runtime import)

    return cache_tool


def test_normal_set_then_get() -> None:
    cache_tool = _import_cache_tool()

    if TEST_DB.exists():
        TEST_DB.unlink()
    cache_tool.DB_PATH = str(TEST_DB)

    text = "合同文本 A：押金、提前退租。"
    payload = {"overall_risk": "低风险", "analysis_results": [{"clause_id": 1}]}

    cache_tool.set_cache(text, payload)
    got = cache_tool.get_cache(text)

    assert got == payload, f"缓存命中结果不一致：{got} vs {payload}"
    assert TEST_DB.exists(), "测试 DB 文件应被创建"
    print("正常路径通过：set_cache 后 get_cache 可命中并返回 dict")


def test_exception_unserializable_result() -> None:
    cache_tool = _import_cache_tool()
    cache_tool.DB_PATH = str(TEST_DB)

    class _NotJson:
        pass

    try:
        cache_tool.set_cache("合同文本 B", {"x": _NotJson()})
        assert False, "预期 json.dumps 触发 TypeError，但未抛出"
    except TypeError:
        print("异常路径通过：result 不可 JSON 序列化会抛 TypeError")


def _cleanup() -> None:
    # Windows 下偶发文件占用（杀软/索引/短暂句柄未释放），清理失败不应影响测试结果
    if not TEST_DB.exists():
        return
    for _ in range(5):
        try:
            TEST_DB.unlink()
            return
        except PermissionError:
            import gc, time

            gc.collect()
            time.sleep(0.1)
    try:
        os.remove(str(TEST_DB))
    except Exception:
        print(f"提示：测试 DB 清理失败，请手动删除 {TEST_DB}")


if __name__ == "__main__":
    try:
        test_normal_set_then_get()
        test_exception_unserializable_result()
        print("cache_tool 测试通过")
    finally:
        _cleanup()

