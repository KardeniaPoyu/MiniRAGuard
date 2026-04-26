from __future__ import annotations

import re
from typing import Iterable


_ARTICLE_START_RE = re.compile(r"^第[一二三四五六七八九十百千万零〇\d]+条\b.*", re.M)


def split_by_article(text: str) -> list[str]:
    """
    基于“第xxx条”语义边界切分，确保每个 chunk 是一条完整法规条文。

    - 精准识别以“第xxx条”开头的条文起始行
    - 每个 chunk 从“第xxx条”起始行开始，到下一条起始行（不含）结束
    """

    matches = list(_ARTICLE_START_RE.finditer(text))
    if not matches:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in items:
        norm = " ".join(s.split())
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(s.strip())
    return out

