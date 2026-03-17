"""
运行前需确保 .env 已配置

独立测试脚本：验证 core/chat_tool.py 的 messages 拼装与错误处理。
不依赖 pytest，使用 assert + print。

说明：本测试通过运行时替换 chat_tool._client 为假客户端，避免真实 API 调用与密钥依赖。
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_normal_path_messages_and_return() -> None:
    from core import chat_tool  # noqa: WPS433 (runtime import)

    captured: dict[str, object] = {}

    class _FakeResp:
        def __init__(self, content: str) -> None:
            self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]

    class _FakeCompletions:
        def create(self, model, messages, temperature):  # noqa: ANN001
            captured["model"] = model
            captured["messages"] = messages
            captured["temperature"] = temperature
            return _FakeResp("好的，我明白了。")

    class _FakeChat:
        def __init__(self) -> None:
            self.completions = _FakeCompletions()

    class _FakeClient:
        def __init__(self) -> None:
            self.chat = _FakeChat()

    chat_tool._client = lambda: _FakeClient()  # type: ignore[assignment]

    context = {"overall_risk": "中风险", "analysis_results": [{"clause_id": 1, "risk_level": "高风险"}]}
    history = [
        {"role": "user", "content": "这份合同总体怎么样？"},
        {"role": "assistant", "content": "整体中风险，有几处需要注意。"},
        {"role": "system", "content": "这条应被忽略"},  # 非法 role，应被过滤
        {"role": "user", "content": 123},  # 非字符串 content，应被过滤
    ]
    question = "押金条款为什么有风险？"

    out = chat_tool.chat(question=question, context=context, history=history)
    assert isinstance(out, str)
    assert out.strip() == "好的，我明白了。"

    msgs = captured.get("messages")
    assert isinstance(msgs, list) and len(msgs) >= 3
    assert msgs[0]["role"] == "system"
    assert "合同审查结果如下" in msgs[0]["content"]
    assert msgs[-1] == {"role": "user", "content": question}

    roles = [m["role"] for m in msgs]  # type: ignore[index]
    assert roles.count("user") >= 2 and roles.count("assistant") >= 1
    assert "system" not in roles[1:], "除首条外不应包含 system role"

    print("正常路径通过：messages 拼装顺序正确，返回文本字符串")


def test_exception_path_api_failure() -> None:
    from core import chat_tool  # noqa: WPS433 (runtime import)

    class _BoomCompletions:
        def create(self, *args, **kwargs):  # noqa: ANN001, D401
            raise Exception("boom")

    class _BoomChat:
        def __init__(self) -> None:
            self.completions = _BoomCompletions()

    class _BoomClient:
        def __init__(self) -> None:
            self.chat = _BoomChat()

    chat_tool._client = lambda: _BoomClient()  # type: ignore[assignment]

    try:
        chat_tool.chat(question="hi", context={}, history=[])
        assert False, "预期抛出 RuntimeError，但未抛出"
    except RuntimeError as e:
        assert "DeepSeek API 调用失败" in str(e)
        print("异常路径通过：底层调用失败会抛 RuntimeError")


if __name__ == "__main__":
    test_normal_path_messages_and_return()
    test_exception_path_api_failure()
    print("chat_tool 测试通过")

