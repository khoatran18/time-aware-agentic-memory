"""Danh sách đóng các `domain` của chunk, dùng chung cho ingestion (gán nhãn) và Profiler (lọc). Xem dataset/full_dataset/TOPICS.md."""
from __future__ import annotations

MAX_DOMAINS_PER_CHUNK = 3

# nhãn -> mô tả đưa vào prompt cho LLM
DOMAINS: dict[str, str] = {
    "business": "companies and organisations: owners, operators, leaders, headquarters, parent/subsidiary companies",
    "sports": "sport: teams, leagues, coaching, home venues",
    "career": "a person's education and work: schools attended, employers, memberships of organisations",
    "person": "personal life: family, residence, citizenship, names, awards, detention",
    "politics": "politics and public office: positions held, political parties, heads of state/government, successors",
    "place": "places, territories, buildings, infrastructure",
    "media_arts": "media, music, publishing, the arts: broadcasters, labels, performers, notable works",
    "military": "armed forces: commanders, ranks, branches",
    "other": "none of the above",
}


def normalize_domains(raw: list[str] | None) -> list[str]:
    """Giữ nhãn hợp lệ (chữ thường, bỏ trùng, giữ thứ tự), tối đa MAX_DOMAINS_PER_CHUNK; nhãn lạ bị bỏ."""
    out: list[str] = []
    for label in raw or []:
        label = label.strip().lower()
        if label in DOMAINS and label not in out:
            out.append(label)
    return out[:MAX_DOMAINS_PER_CHUNK]


def domains_prompt() -> str:
    """Danh sách nhãn dạng gạch đầu dòng để thay vào `{domains}` trong prompt."""
    return "\n".join(f"  - `{name}`: {desc}" for name, desc in DOMAINS.items())


# relation (P) của câu hỏi -> domain, theo bảng ở dataset/full_dataset/TOPICS.md mục 3. Chỉ dùng để chia nhóm lúc lấy mẫu,
# báo cáo và kiểm chứng nhãn LLM; KHÔNG dùng khi xây kho. Relation không có trong bảng thì thuộc `other`.
_RELATIONS_BY_DOMAIN: dict[str, str] = {
    "business": "P127 P137 P169 P749 P159 P355 P176 P488 P1037 P8047 P366 P1830",
    "sports": "P54 P6087 P286 P641 P118 P115 P2962 P1344",
    "career": "P108 P69 P463 P106 P937 P1416 P1075",
    "person": "P26 P40 P551 P27 P1448 P2561 P734 P138 P2632 P166",
    "politics": "P39 P102 P6 P35 P1308 P97 P1366 P1365",
    "place": "P17 P36 P1376 P47 P150 P276 P121 P466 P559 P1435 P618",
    "media_arts": "P371 P449 P264 P175 P123 P98 P800 P608 P195",
    "military": "P4791 P410 P241",
}
RELATION_DOMAIN: dict[str, str] = {p: d for d, ps in _RELATIONS_BY_DOMAIN.items() for p in ps.split()}


def relation_domain(relation: str) -> str:
    """Domain của một relation (P…); không có trong bảng thì `other`."""
    return RELATION_DOMAIN.get(relation, "other")
