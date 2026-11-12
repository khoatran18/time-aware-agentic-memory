"""Hậu xử lý đầu ra ingest (không gọi LLM): sửa lỗi năm viết tắt, gộp trùng, ghép với gold.
Dùng như thư viện (import ingest_post) hoặc chạy: python3 -I ingest_post.py <out_dir_name>... -- <trang>...  (chạy trong timeline_pilot).
"""
import json, re
from pathlib import Path

norm = lambda s: re.sub(r"\s+", "", s).lower()
STOP = {"that", "this", "with", "from", "were", "was", "his", "her", "their", "after", "before", "into", "and", "the", "for", "has", "had"}
START_W = re.compile(r"\b(became|become|appointed|named|joined|founded|established|opened|began|started|elected|promoted|took|assumed|won|born|created|launched|moved|entered|signed|formed)\b", re.I)
END_W = re.compile(r"\b(ended|left|resigned|retired|stepped down|until|ceased|closed|dissolved|disbanded|died|lost|terminated|expired|abolished|finished|sold|departed|relinquished|replaced|succeeded by)\b", re.I)


def toks(t):
    return {w.lower().rstrip("s") for w in re.findall(r"[A-Za-zÀ-ÿ]{3,}|\d{2,}", t)} - STOP


def jacc(a, b):
    """Độ giống theo chữ, chia cho số chữ nhỏ hơn (dùng khi ghép gold)."""
    A, B = toks(a), toks(b)
    return len(A & B) / max(1, min(len(A), len(B)))


def jacc_u(a, b):
    """Jaccard trên hợp (dùng khi gộp trùng; chặt hơn jacc)."""
    A, B = toks(a), toks(b)
    return len(A & B) / max(1, len(A | B))


def caps(t):
    """Tên riêng/số hiệu ở giữa câu (bỏ chữ đầu câu)."""
    return {w.lower() for w in re.findall(r"(?<=[a-z,0-9] )[A-Z][\w'’-]{2,}", t)}


def phase(t):
    s, e = bool(START_W.search(t)), bool(END_W.search(t))
    return "end" if e and not s else "start" if s and not e else "?"


# ---- 1. sửa year_not_in_page cho năm cuối khoảng viết tắt -------------------------------
RANGE = re.compile(r"(?<!\d)(\d{4})\s*[-–—]\s*(\d{1,2})(?!\d)")


def expands_to(raw, year, tail):
    """True nếu trong trang có khoảng 'AAAA–bb' với bb == tail và năm cuối mở rộng bằng `year`."""
    for m in RANGE.finditer(raw or ""):
        a, b = m.group(1), m.group(2)
        if b == tail.strip() and a[: 4 - len(b)] + b == year:
            return True
    return False


def page_raw(pilot, name):
    t = next(Path(pilot).glob(f"batch*/in/{name}.txt")).read_text(encoding="utf-8")
    parts = re.split(r"^=== CHUNK (\S+) ===\n", t, flags=re.M)
    return " ".join(b.partition("\n")[2].strip() for b in parts[2::2])


def reinstate(res, raw):
    """Đưa lại các mốc bị loại `year_not_in_page` mà năm thực ra mở rộng được từ một khoảng 'AAAA–bb' có trong trang
    (date_text chỉ chép phần cuối '70'). Trả (events, số mốc cứu)."""
    ev = list(res["events"]); saved = 0
    for d in res["dropped"]:
        if d.get("reason") == "year_not_in_page" and d.get("date") and d.get("date_text") and expands_to(raw, d["date"][:4], d["date_text"]):
            e = {k: v for k, v in d.items() if k != "reason"}
            e["flags"] = list(e.get("flags", [])) + ["year_expanded_from_range"]; ev.append(e); saved += 1
    return ev, saved


# ---- 2. so ngày ------------------------------------------------------------------------
def compat(a, b):
    """Hai ngày tương thích nếu một cái là tiền tố của cái kia (1826 ~ 1826-03 ~ 1826-03-29)."""
    return bool(a and b and (a.startswith(b) or b.startswith(a)))


# ---- 3. gộp trùng ----------------------------------------------------------------------
def merge(events, thr=0.9, thr_same=0.8, guard=True, names=True):
    """Gộp mốc ingest trùng: ngày tương thích, cùng phase (nếu cả hai xác định), chữ giống >= thr.
    Không gộp khi một bên có số năm khác bên kia trong text. Giữ ngày chi tiết hơn; cid gộp vào `cids`."""
    out = []
    for e in sorted(events, key=lambda x: (x.get("section", 0), x["chunk"])):
        e = dict(e, cids=list(e.get("cids", [e["cid"]])), merged=e.get("merged", 1)); hit = None
        for m in out:
            if not compat(m["date"], e["date"]): continue
            p1, p2 = phase(m["text"]), phase(e["text"])
            if "?" not in (p1, p2) and p1 != p2: continue
            y1, y2 = set(re.findall(r"(?<!\d)\d{4}(?!\d)", m["text"])), set(re.findall(r"(?<!\d)\d{4}(?!\d)", e["text"]))
            if y1 and y2 and y1 != y2: continue
            if guard:
                c1, c2 = caps(m["text"]) - caps(e["text"]), caps(e["text"]) - caps(m["text"])
                if c1 and c2: continue  # mỗi bên có tên riêng mà bên kia không có: hai việc khác nhau
            t = thr_same if set(e["cids"]) & set(m["cids"]) else thr
            if jacc_u(m["text"], e["text"]) >= t: hit = m; break
            if names:  # cùng bộ tên riêng (không rỗng) + cùng phase xác định + ngày tương thích: cùng một sự kiện nói hai lần
                n1, n2 = caps(m["text"]), caps(e["text"])
                if n1 and n1 == n2 and jacc_u(m["text"], e["text"]) >= 0.3: hit = m; break
        if hit is None: out.append(e); continue
        hit["merged"] += e["merged"]
        hit["cids"] += [c for c in e["cids"] if c not in hit["cids"]]
        if len(e["date"]) > len(hit["date"]): hit["date"] = e["date"]
        hit["flags"] = sorted(set(hit["flags"]) | set(e["flags"]))
    return out


def merge_keyed(events):
    """Gộp theo nhãn của bản 10: ngày tương thích + cùng track + cùng phase + cùng `object` (chuẩn hóa, không rỗng). Chạy trước `merge`."""
    out = []
    for e in sorted(events, key=lambda x: (x.get("section", 0), x["chunk"])):
        e = dict(e, cids=e.get("cids", [e["cid"]]), merged=e.get("merged", 1)); obj = norm(e.get("object") or "")
        hit = next((m for m in out if obj and norm(m.get("object") or "") == obj and m["track"] == e["track"] and m["phase"] == e["phase"] and compat(m["date"], e["date"])), None)
        if hit is None: out.append(e); continue
        hit["merged"] += 1; hit["cids"] += [c for c in e["cids"] if c not in hit["cids"]]
        if len(e["date"]) > len(hit["date"]): hit["date"] = e["date"]
        hit["flags"] = sorted(set(hit["flags"]) | set(e["flags"]))
    return out


def assign(W):
    """Hungarian tối đa hoá tổng W (ma trận n x m, không cần vuông). Trả list (i, j)."""
    n, m = len(W), len(W[0]) if W else 0
    if not n or not m: return []
    T = n > m
    C = [[-(W[i][j] if not T else W[i][j]) for j in range(m)] for i in range(n)]
    if T: C = [[C[i][j] for i in range(n)] for j in range(m)]; n, m = m, n
    INF = float("inf"); u = [0.0] * (n + 1); v = [0.0] * (m + 1); p = [0] * (m + 1); way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i; j0 = 0; minv = [INF] * (m + 1); used = [False] * (m + 1)
        while True:
            used[j0] = True; i0 = p[j0]; d = INF; j1 = 0
            for j in range(1, m + 1):
                if used[j]: continue
                cur = C[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]: minv[j] = cur; way[j] = j0
                if minv[j] < d: d = minv[j]; j1 = j
            for j in range(m + 1):
                if used[j]: u[p[j]] += d; v[j] -= d
                else: minv[j] -= d
            j0 = j1
            if p[j0] == 0: break
        while j0:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
    pairs = [(p[j] - 1, j - 1) for j in range(1, m + 1) if p[j]]
    return [(j, i) for i, j in pairs] if T else pairs


# ---- 4. ghép với gold (hai phía tối ưu) -------------------------------------------------
def match(gold, ev, strict=True):
    """Ghép một-một gold<->ingest tối đa trọng số. Hợp lệ khi ngày tương thích và (strict) một cid của ingest nằm trong evidence gold.
    Trọng số: 100 + 10 nếu ngày bằng nhau + 5*overlap chữ. Trả dict gold_id -> chỉ số ingest."""
    W = [[0.0] * len(ev) for _ in gold]
    for i, g in enumerate(gold):
        gc = {x["chunk_id"] for x in g["evidence"]}
        for j, e in enumerate(ev):
            cids = set(e.get("cids", [e["cid"]]))
            if compat(g["date"], e["date"]) and (not strict or cids & gc):
                W[i][j] = 100 + 10 * (g["date"] == e["date"]) + 5 * jacc(g["text"], e["text"])
    return {gold[i]["id"]: j for i, j in assign(W) if W[i][j] > 0}


def load(pilot, outdir, name):
    gold = json.load(open(next(Path(pilot).glob(f"batch*/rev/{name}.json"))))
    res = json.load(open(Path(pilot) / "outline_trial" / outdir / f"{name}.json"))
    return gold, res


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]; i = a.index("--"); dirs, pages = a[:i], a[i + 1:]
    for d in dirs:
        tot = dict(gold=0, ev0=0, hit0=0, saved=0, ev1=0, hit1=0, hit_loose=0)
        for n in pages:
            gold, res = load(".", d, n); G = gold["events"]
            e0 = res["events"]; h0 = match(G, e0)
            e1, sv = reinstate(res, page_raw('.', n)); e1 = merge(e1); h1 = match(G, e1)
            tot["gold"] += len(G); tot["ev0"] += len(e0); tot["hit0"] += len(h0)
            tot["saved"] += sv; tot["ev1"] += len(e1); tot["hit1"] += len(h1)
            tot["hit_loose"] += len(match(G, e1, strict=False))
        t = tot
        print(f"{d}: gold {t['gold']} | trước: ingest {t['ev0']} khớp {t['hit0']} recall {t['hit0']/t['gold']:.1%} prec {t['hit0']/t['ev0']:.1%}"
              f" | sau (cứu {t['saved']}, gộp): ingest {t['ev1']} khớp {t['hit1']} recall {t['hit1']/t['gold']:.1%} prec {t['hit1']/t['ev1']:.1%} | recall nới chunk {t['hit_loose']/t['gold']:.1%}")
