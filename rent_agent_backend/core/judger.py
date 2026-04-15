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
    "你是一位检察院『根治欠薪与支持起诉』专项行动的智能研判检察官。你的任务是从杂乱的诉求文本和证据中，精准提取欠薪事实，评估群体性风险或刑事犯罪风险（如拒不支付劳动报酬罪），并严格输出 JSON。"
)

USER_PROMPT_TPL = """请对以下基层线索进行深度检察业务风险研判。

【卷宗/线索内容】
标题: {title}
涉事企业/人: {enterprise}
金额: {amount}元, 涉及人数: {count}
详情: {clue_content}

【参考法规及办案指南】
{legal_context}

请严格按以下 JSON 格式返回结果（无外部前缀，直接输出 {{）：
{{
  "employer": "提取的欠薪企业或包工头名称",
  "amount": "提取的涉及金额(数字或估算)",
  "worker_count": "提取的涉及人数(数字)",
  "risk_level": "高风险/中风险/低风险",
  "risk_summary": "100字内的案情概要及危害分析",
  "case_type": "必须选一: 行政监督线索/民事支持起诉线索/刑事拒不支付劳动报酬线索/公益诉讼线索",
  "risk_factors": [
    {{
      "factor": "提取的违法行为（如:未将工资汇入专用账户/恶意欠薪跑路/非法排污）",
      "description": "结合案情详述",
      "legal_basis": "《相关法规》第X条",
      "severity": "高/中/低"
    }}
  ],
  "recommended_action": "给出检察官下一步的行动建议，比如制发行政检察建议给住建局/移送公安等",
  "procuratorial_advice": "起草一小段简要《检察建议书》框架"
}}"""

def _client() -> "OpenAI":
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置")
    if OpenAI is None:
        raise RuntimeError(f"openai SDK 不可用：{_OPENAI_IMPORT_ERROR}")
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

def judge_clue(title: str, enterprise: str, amount: float, count: int, clue_content: str, legal_context: str) -> dict:
    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip()
    user_prompt = USER_PROMPT_TPL.format(
        title=title, 
        enterprise=enterprise, 
        amount=amount, 
        count=count, 
        clue_content=clue_content, 
        legal_context=legal_context
    )

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

    required_fields = ["risk_level", "risk_summary", "case_type", "risk_factors", "recommended_action"]
    for field in required_fields:
        if field not in result:
            result[field] = "" if field != "risk_factors" else []
    if not isinstance(result.get("risk_factors"), list):
        result["risk_factors"] = []

    return result
