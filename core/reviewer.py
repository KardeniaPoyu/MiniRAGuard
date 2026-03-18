from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv

try:
    from openai import OpenAI  # openai>=1.x
except Exception as e:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = e

load_dotenv()


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT = (
    "你是一位专业的租房合同法律顾问，擅长识别霸王条款和不公平条款。\n"
    "只返回 JSON，不输出任何解释文字，不使用 markdown 代码块。"
)

USER_PROMPT_TPL = """请分析以下租房合同，结合参考法条，识别所有风险条款。

【合同原文】
{contract_text}

【参考法条】
{legal_context}

严格按以下 JSON 格式返回，不输出其他内容：
{{
  "overall_risk": "高风险/中风险/低风险",
  "summary": "一句话总结",
  "analysis_results": [
    {{
      "clause_id": 序号,
      "original_text": "原文片段",
      "risk_level": "高风险/中风险/低风险",
      "risk_type": "类型描述",
      "reason": "违规原因",
      "legal_basis": "《法规》第X条",
      "advice": "修改建议"
    }}
  ]
}}"""


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


def _parse_json_with_fallback(raw: str) -> dict:
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict):
            return obj
    raise ValueError(f"无法解析为 JSON：{raw}")


def review_contract(contract_text: str, legal_context: str) -> dict:
    """
    组装审查 Prompt 并调用 DeepSeek，返回结构化审查结果 dict。

    - 使用 openai SDK
    - base_url/model/api_key 从环境变量读取：
      - DEEPSEEK_BASE_URL（默认 https://api.deepseek.com）
      - DEEPSEEK_MODEL（默认 deepseek-chat）
      - DEEPSEEK_API_KEY
    - 返回值必须可被 json.loads() 解析为 dict；解析失败会尝试从响应中提取 {...} 重试一次
    """

    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip()
    user_prompt = USER_PROMPT_TPL.format(contract_text=contract_text, legal_context=legal_context)

    try:
        resp = _client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=2000,
        )
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"DeepSeek API 调用失败：{e}") from e

    content = (resp.choices[0].message.content or "").strip()
    return _parse_json_with_fallback(content)


if __name__ == "__main__":
    demo_contract_text = "租客若提前退租，押金概不退还；未经允许不得转租；违约金为月租金的三倍。"
    demo_legal_context = "民法典租赁合同相关条款：维修义务、转租需同意等。"
    result = review_contract(demo_contract_text, demo_legal_context)
    s = json.dumps(result, ensure_ascii=False, indent=2)
    print(s)
    json.loads(s)
    print("JSON 格式正确")

