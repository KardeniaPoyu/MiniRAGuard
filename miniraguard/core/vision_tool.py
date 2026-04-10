from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv

try:
    # openai>=1.x
    from openai import OpenAI
except Exception as e:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = e

load_dotenv()


DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_MODEL = "qwen-vl-max"

SYSTEM_PROMPT = "你是一个专业的合同文字提取助手，只提取文字，不做任何分析。"

USER_PROMPT = """你将收到一张图片（可能是合规文档页面，也可能不是合同）。
请你严格只输出以下 JSON，不要输出任何其他内容（不要代码块、不要解释、不要额外字段）：
{
  "is_contract": true或false,
  "contract_text": "若is_contract为true，按条款编号提取全部文字；否则为空字符串"
}

要求：
1) 只输出 JSON，必须可被 json.loads() 解析；
2) 如果不是合同页面或无法确认是合同页面，is_contract 输出 false，contract_text 输出空字符串；
3) 如果是合同页面，contract_text 输出该页全部文字，并尽量按条款编号/段落顺序组织。
"""


def extract_contract(image_base64: str, system_prompt: str, user_prompt_tpl: str) -> str:
    """
    Extracts text from an image using a VLM with provided prompts.
    Returns the extracted text.
    """
    base_url = os.getenv("QWEN_BASE_URL", DEFAULT_QWEN_BASE_URL).strip()
    model = os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL).strip()
    api_key = (os.getenv("QWEN_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("QWEN_API_KEY not configured")

    if OpenAI is None:
        raise RuntimeError(
            "openai SDK is outdated or unavailable: requires openai>=1.x."
        )

    client = OpenAI(base_url=base_url, api_key=api_key)

    data_url = f"data:image/jpeg;base64,{image_base64}"
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt_tpl},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
    except Exception as e:
        raise RuntimeError(f"Qwen-VL API call failed: {e}") from e

    content = (resp.choices[0].message.content or "").strip()
    
    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        raise RuntimeError(f"JSON structure not found in VLM response: {content}")
    content = match.group()

    try:
        payload = json.loads(content)
    except Exception as e:
        raise RuntimeError(f"VLM returned invalid JSON: {content}") from e

    is_valid = payload.get("is_contract") or payload.get("is_valid")
    text = payload.get("contract_text") or payload.get("text", "")

    if is_valid is False:
        raise ValueError("INVALID_DOCUMENT")
    
    return str(text)

