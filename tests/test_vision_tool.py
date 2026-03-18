"""
运行前需确保 .env 已配置（vision_tool 和 reviewer 需要真实 API Key）。

本脚本仅测试 core/vision_tool.py，不依赖 pytest，使用 assert + print 验证。

可选：若设置环境变量 VISION_TEST_IMAGE_B64（一张图片的 base64，不含 data: 前缀），
则会执行一次真实 API 调用测试；否则只跑本地异常路径测试。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def _require_deps() -> None:
    missing: list[str] = []
    try:
        import openai
    except ModuleNotFoundError:
        missing.append("openai")

    if missing:
        print("依赖缺失，无法运行 vision_tool 测试：", ", ".join(missing))
        print("请先安装后端依赖，例如：")
        print("  pip install -r rent_agent_backend/requirements.txt")
        print("或按需安装：")
        print("  pip install openai")
        raise SystemExit(1)

    # vision_tool 使用 openai v1 SDK（需要 OpenAI 客户端类）
    if not hasattr(openai, "OpenAI"):
        print("openai SDK 版本过旧：未找到 OpenAI 客户端类，无法进行多模态调用。")
        print("请升级：")
        print("  pip install -U openai")
        raise SystemExit(1)


def _import_extract_contract():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from core.vision_tool import extract_contract  # noqa: WPS433 (runtime import)

    return extract_contract


def test_missing_api_key_raises() -> None:
    """
    异常路径：缺少 QWEN_API_KEY 时应抛 RuntimeError。
    """

    extract_contract = _import_extract_contract()

    old = os.environ.pop("QWEN_API_KEY", None)
    try:
        try:
            extract_contract("dGVzdA==")  # "test" 的 base64，占位即可（不会真正发出请求）
            assert False, "预期抛出 RuntimeError（QWEN_API_KEY 未配置），但未抛出"
        except RuntimeError as e:
            assert "QWEN_API_KEY" in str(e)
            print("异常路径通过：缺少 QWEN_API_KEY 会报错")
    finally:
        if old is not None:
            os.environ["QWEN_API_KEY"] = old


def test_real_api_call_optional() -> None:
    """
    正常路径（可选）：当 VISION_TEST_IMAGE_B64 存在时，进行一次真实 API 调用。

    断言：
    - 成功返回时为非空字符串
    - 或识别为非合同页时抛 ValueError("NOT_CONTRACT")
    """

    image_b64 = (os.getenv("VISION_TEST_IMAGE_B64") or "").strip()
    if not image_b64:
        print("跳过真实调用：未设置 VISION_TEST_IMAGE_B64")
        return

    api_key = (os.getenv("QWEN_API_KEY") or "").strip()
    assert api_key, "执行真实调用前请先配置 QWEN_API_KEY"

    extract_contract = _import_extract_contract()
    try:
        text = extract_contract(image_b64)
        assert isinstance(text, str)
        assert text.strip(), "识别为合同页时 contract_text 不应为空"
        print("正常路径通过：真实调用返回了合同文本（非空）")
    except ValueError as e:
        assert str(e) == "NOT_CONTRACT"
        print("正常路径通过：真实调用识别为非合同页（NOT_CONTRACT）")


if __name__ == "__main__":
    _require_deps()
    test_missing_api_key_raises()
    test_real_api_call_optional()
    print("vision_tool测试通过")

