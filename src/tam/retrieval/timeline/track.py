"""Suy track (loại thay đổi) từ câu hỏi bằng từ khóa (không LLM). Trả tập track khớp, rỗng nếu không khớp (khi đó dùng track của nút vào).
Track trùng bộ nhãn ingest: role, affiliation, location, ownership_structure, work, naming, family, education, other."""
from __future__ import annotations

import re

RULES: dict[str, str] = {
    "role": r"\b(appoint\w*|head(?:s|ed)?\b|director\w*|command\w*|chief|chair\w*|president\w*|minister\w*|rank\w*|office|term|succe\w+|took over|took up the post|editor\w*|coach\w*|captain\w*|manager\w*|leader\w*|post of|headship|governor|mayor)\b",
    "affiliation": r"\b(join\w*|left the|club|team|party|member\w*|employer|signed|transfer\w*|league|affiliat\w*)\b",
    "location": r"\b(mov\w+|relocat\w*|headquarter\w*|resid\w*|based in|home ground|stadium)\b",
    "ownership_structure": r"\b(acqui\w+|bought|sold|owner\w*|merg\w*|parent company|sale of|taken private|publisher|operator|subsidiar\w*)\b",
    "work": r"\b(built|construct\w*|releas\w*|publish\w*|complet\w*|premier\w*|design\w*|product\w*|building\w*|album\w*|film\w*|episode\w*|series|opened|opening)\b",
    "naming": r"\b(renam\w*|name[ds]?\b|called|known as|official name)\b",
    "family": r"\b(married|marriage|wife|husband|child\w*|son|daughter|divorc\w*)\b",
    "education": r"\b(studied|graduat\w*|school|universit\w*|degree|doctorate|enrol\w*|college|academy|fellowship)\b",
    "other": r"\b(award\w*|prize\w*|medal\w*|honou?r\w*|won|champion\w*|title\w*|born|died|death|founded|founding|ranking\w*|tournament\w*|protest\w*)\b",
}
_C = {k: re.compile(v, re.I) for k, v in RULES.items()}


def infer_tracks(question: str) -> set[str]:
    return {k for k, rx in _C.items() if rx.search(question)}
