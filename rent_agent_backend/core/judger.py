import json
import os
import re
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None
    _OPENAI_IMPORT_ERROR = e

load_dotenv()

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT = (
    "你是一位检察院基层治理风险研判专家，\n"
    "擅长识别食品安全、环境污染、劳动违法、公房产纠纷、金融风险等领域的违法隐患。\n"
    "只返回 JSON，不输出任何解释文字。"
)

USER_PROMPT_TPL = """请对以下基层治理线索进行风险研判，
结合参考法规，给出结构化研判意见。

【线索内容】
{clue_content}

【参考法规】
{legal_context}

严格按以下 JSON 格式返回：
{{
  "risk_level": "高风险/中风险/低风险",
  "risk_summary": "一句话概括风险性质",
  "domain": "识别所属领域：食品安全/环境/劳动/房产/金融/其他",
  "risk_factors": [
    {{
      "factor": "风险因素名称",
      "description": "具体描述",
      "legal_basis": "《相关法规》第X条",
      "severity": "高/中/低"
    }}
  ],
  "recommended_action": "建议推送至哪个监管部门及处置建议",
  "urgency": "立即处置/一周内处置/常规跟踪"
}}"""


def _client() -> "OpenAI":
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置")
    if OpenAI is None:
        raise RuntimeError(
            f"openai SDK 不可用：{_OPENAI_IMPORT_ERROR}"
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


def judge_clue(clue_content: str, legal_context: str) -> dict:
    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip()
    user_prompt = USER_PROMPT_TPL.format(clue_content=clue_content, legal_context=legal_context)

    try:
        resp = _client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=2000,
            response_format={"type": "json_object"} if "deepseek" not in model.lower() else None
        )
    except Exception as e:
        raise RuntimeError(f"DeepSeek API 调用失败：{e}") from e

    content = (resp.choices[0].message.content or "").strip()
    result = _parse_json_with_fallback(content)

    required_fields = ["risk_level", "risk_summary", "domain", "risk_factors", "recommended_action", "urgency"]
    for field in required_fields:
        if field not in result:
            result[field] = "" if field != "risk_factors" else []

    if not isinstance(result.get("risk_factors"), list):
        result["risk_factors"] = []

    return result
