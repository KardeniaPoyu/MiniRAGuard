from __future__ import annotations

import json
import os
from typing import Any

try:
    from openai import OpenAI  # openai>=1.x
except Exception as e:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = e


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


def _client() -> "OpenAI":
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置")
    if OpenAI is None:
        raise RuntimeError(
            "openai SDK 版本过旧或不可用：需要 openai>=1.x。"
            f" 原始错误：{_OPENAI_IMPORT_ERROR}"
        )
    base_url = os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip()
    return OpenAI(base_url=base_url, api_key=api_key)


def chat(question: str, context: dict, history: list) -> str:
    """
    基于审查结果 context 和对话历史 history 回答 question，返回自由文本字符串。

    - 使用与 reviewer.py 相同的 DeepSeek 配置（DEEPSEEK_* 环境变量）
    - messages：system → history(按顺序) → 当前 question(user)
    """

    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip()
    context_json = json.dumps(context, ensure_ascii=False)

    system_prompt = (
        "你是一位租房法律助手，正在帮助一位大学生理解其租房合同的审查结果。\n"
        "用简洁易懂的语言回答，避免使用专业术语堆砌。\n"
        f"已知的合同审查结果如下：\n{context_json}"
    )

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    try:
        resp = _client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"DeepSeek API 调用失败：{e}") from e

    return (resp.choices[0].message.content or "").strip()

