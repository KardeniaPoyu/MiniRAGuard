from __future__ import annotations

import json
import os

try:
    # openai>=1.x
    from openai import OpenAI
except Exception as e:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = e


DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_MODEL = "qwen-vl-max"

SYSTEM_PROMPT = "你是一个专业的合同文字提取助手，只提取文字，不做任何分析。"

USER_PROMPT = """你将收到一张图片（可能是租房合同页面，也可能不是合同）。
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


def extract_contract(image_base64: str) -> str:
    """
    单张图片（base64）→ 该页合同纯文本。

    - 使用 openai SDK 调用阿里云 Qwen-VL-Max（兼容模式）
    - base_url / model / api_key 从环境变量读取：
      - QWEN_BASE_URL（默认 https://dashscope.aliyuncs.com/compatible-mode/v1）
      - QWEN_MODEL（默认 qwen-vl-max）
      - QWEN_API_KEY

    返回：
    - is_contract 为 true：返回 contract_text
    - is_contract 为 false：抛 ValueError("NOT_CONTRACT")

    异常：
    - API 调用失败：抛 RuntimeError，并附带原始错误信息
    - JSON 解析/字段不合法：抛 RuntimeError，并附带原始响应内容
    """

    base_url = os.getenv("QWEN_BASE_URL", DEFAULT_QWEN_BASE_URL).strip()
    model = os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL).strip()
    api_key = (os.getenv("QWEN_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("QWEN_API_KEY 未配置")

    if OpenAI is None:
        raise RuntimeError(
            "openai SDK 版本过旧或不可用：需要 openai>=1.x 以支持 OpenAI 客户端与多模态 messages。"
            f" 原始错误：{_OPENAI_IMPORT_ERROR}"
        )

    client = OpenAI(base_url=base_url, api_key=api_key)

    data_url = f"data:image/jpeg;base64,{image_base64}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": USER_PROMPT},
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
    except Exception as e:  # noqa: BLE001 - 需要透传原始错误信息
        raise RuntimeError(f"Qwen-VL API 调用失败：{e}") from e

    try:
        content = (resp.choices[0].message.content or "").strip()
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Qwen-VL 响应结构异常：{e}") from e

    try:
        payload = json.loads(content)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Qwen-VL 返回非 JSON：{content}") from e

    is_contract = payload.get("is_contract")
    contract_text = payload.get("contract_text", "")

    if is_contract is False:
        raise ValueError("NOT_CONTRACT")
    if is_contract is not True:
        raise RuntimeError(f"Qwen-VL JSON 字段不合法：{payload}")
    if not isinstance(contract_text, str):
        raise RuntimeError(f"Qwen-VL contract_text 非字符串：{payload}")

    return contract_text

