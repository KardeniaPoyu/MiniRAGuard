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
    "你是一位专业的检察机关法律监督助手，擅长分析社会治理线索及识别根治欠薪相关的违法违规风险。\n"
    "你的任务是根据线索原文和参考法条，给出专业的法律定性分析及处理建议。\n"
    "只返回 JSON，不输出任何解释文字，不使用 markdown 代码块。"
)


USER_PROMPT_TPL = """请分析以下法律监督线索（可能涉及欠薪或企业违规），结合参考法条，识别其中的法律风险点。
观察是否触及行政监督或民事检察监督的情形。

【线索原文】
{contract_text}

【参考法条】
{legal_context}

⚠️ 【严格约束】：
1. 在输出的 `legal_basis` 字段中，必须提取并使用上述【参考法条】中 `【来源：真实名称】` 中的法典全称（例如填入《保障农民工工资支付条例》），以此替换下方模板中的“《具体法规名称》”。
2. **严禁自行编造**。
3. 如果原文涉及欠薪，应重点引用《保障农民工工资支付条例》或《劳动法》相关条款。

严格按以下 JSON 格式返回，不输出其他内容：
{{
  "overall_risk": "高风险/中风险/低风险",
  "summary": "一句话总结线索定性",
  "analysis_results": [
    {{
      "clause_id": 序号,
      "original_text": "线索中的关键片段",
      "risk_level": "高风险/中风险/低风险",
      "risk_type": "风险点/违规点类型",
      "reason": "法律依据分析与风险说明",
      "legal_basis": "《具体法规名称》第X条",
      "advice": "针对该项的法律建议/告知"
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


def review_contract(contract_text: str, 
                    legal_context: str, 
                    system_prompt: str, 
                    user_prompt_tpl: str) -> dict:
    """
    Assembles the review prompt and calls DeepSeek, returning structured results.
    """
    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip()
    user_prompt = user_prompt_tpl.format(contract_text=contract_text, legal_context=legal_context)

    try:
        resp = _client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=2000,
        )
    except Exception as e:
        raise RuntimeError(f"DeepSeek API call failed: {e}") from e

    content = (resp.choices[0].message.content or "").strip()
    result = _parse_json_with_fallback(content)

    required_fields = ["overall_risk", "summary", "analysis_results"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"DeepSeek returned JSON missing field: {field}")

    if not isinstance(result["analysis_results"], list):
        raise ValueError("analysis_results must be a list")

    for item in result["analysis_results"]:
        item.setdefault("risk_level", "Medium")
        item.setdefault("risk_type", "Pending")
        item.setdefault("reason", "")
        item.setdefault("legal_basis", "")
        item.setdefault("advice", "")

    return result


if __name__ == "__main__":
    demo_contract_text = "租客若提前退租，押金概不退还；未经允许不得转租；违约金为月租金的三倍。"
    demo_legal_context = "民法典租赁合同相关条款：维修义务、转租需同意等。"
    result = review_contract(demo_contract_text, demo_legal_context)
    s = json.dumps(result, ensure_ascii=False, indent=2)
    print(s)
    json.loads(s)
    print("JSON 格式正确")

