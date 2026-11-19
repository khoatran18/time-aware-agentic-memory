"""Đáp án chuẩn và bộ chấm cho câu hỏi v9 (không gọi LLM).

Đáp án chuẩn đọc từ chính dòng câu hỏi + gold `rev/<Trang>.json`:
  order_gap        -> số năm (|năm sau - năm trước|, theo năm lịch)
  first_last_next  -> các mốc trong `answer_ids` (1 mốc, hoặc 2 mốc theo thứ tự thời gian)
  list, summary    -> các mốc trong `gold_event_ids`, theo thứ tự ngày (cùng ngày: thứ tự nào cũng được)

Định dạng câu trả lời của hệ thống (đã thống nhất):
  order_gap        -> một số nguyên (hoặc chuỗi có số)
  các loại còn lại -> danh sách {"date": "1983" | "1983-05" | "1983-05-16", "text": "mô tả ngắn"}

Ghép mốc dự đoán với mốc chuẩn theo NGÀY, ngày tương thích nếu: (cả hai chỉ cần trùng ở phần cả hai cùng có) thì năm trùng khi một bên chỉ có năm
(người dùng chốt 2026-11-12). Nhiều mốc chuẩn cùng ngày tương thích thì chọn theo độ trùng từ khóa của `text`.
Điểm: precision, recall, f1 (theo mốc), order (cặp mốc khác ngày đúng thứ tự), exact (đủ, không thừa, đúng thứ tự); order_gap: exact.

Dùng:  python3 -I local/v9_score.py <repo> selftest      (kiểm bộ chấm bằng đáp án oracle + biến dạng cố ý, không gọi LLM)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^\s*(-?\d{1,4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?\s*$")
STOP = set("the a an of in on at to and for by with was were is as his her their its from that which this he she it after before".split())


def parse_date(s):
    """'1983-05-16' -> (1983, 5, 16); '1983' -> (1983, None, None); không đọc được -> None."""
    m = DATE_RE.match(str(s)) if s is not None else None
    if not m:
        return _lenient_date(s)
    y, mo, d = m.groups()
    return (int(y), int(mo) if mo else None, int(d) if d else None)


MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}  # khóa 3 chữ đầu: nhận cả "Oct", "Sept", "October"
MON_RE = r"(" + "|".join(MONTHS) + r")[a-z]*\.?"


def _lenient_date(s):
    """Định dạng LLM hay trả ngoài khuôn: '1 February 1939', 'February 1939', 'Feb 1, 1939', khoảng '1977 to 1986', '1966–67', '1962-10 and 1962-12'.
    Lấy ngày ĐẦU TIÊN tìm được (khoảng -> đầu khoảng). Không có năm -> None."""
    if s is None:
        return None
    t = str(s).lower()
    SEP = r"\s*[\u2013\u2014-]\s*"
    m = re.search(r"(\d{1,2})\s+" + MON_RE + SEP + r"\d{1,2}\s+" + MON_RE + r"\s+(-?\d{3,4})", t)  # '4 April-21 November 1966' -> đầu khoảng
    if m: return (int(m.group(4)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.search(MON_RE + SEP + MON_RE + r"\s+(-?\d{3,4})", t)  # 'March-April 1962'
    if m: return (int(m.group(3)), MONTHS[m.group(1)], None)
    m = re.search(r"(\d{1,2})" + SEP + r"\d{1,2}\s+" + MON_RE + r"\s+(-?\d{3,4})", t)  # '14-28 November 1960'
    if m: return (int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.search(r"(\d{1,2})\s+" + MON_RE + r"\s+(-?\d{3,4})", t)
    if m: return (int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.search(MON_RE + r"\s+(\d{1,2}),?\s+(-?\d{3,4})", t)
    if m: return (int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    m = re.search(MON_RE + r"\s+(-?\d{3,4})", t)
    if m: return (int(m.group(2)), MONTHS[m.group(1)], None)
    m = re.search(r"(-?\d{3,4})-(\d{1,2})(?:-(\d{1,2}))?(?!\d)", t)
    if m and 1 <= int(m.group(2)) <= 12: return (int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
    m = re.search(r"(?<!\d)(-?\d{3,4})(?!\d)", t)
    return (int(m.group(1)), None, None) if m else None


def compatible(a, b):
    """Hai ngày (bộ y, m, d) tương thích nếu mọi phần cả hai cùng có thì bằng nhau (chỉ-năm tương thích với mọi ngày cùng năm)."""
    if a is None or b is None:
        return False
    return all(x is None or y is None or x == y for x, y in zip(a, b))


def season_alt(s):
    """'2009-10' / '2009–2010' (hai năm liền, mùa giải) -> (năm đầu, năm sau) để chấp nhận khớp một trong hai năm (người dùng đồng ý 2026-11-13); không phải dạng đó -> None."""
    m = re.fullmatch(r"\s*(\d{4})\s*[\u2013\u2014-]\s*(\d{2}|\d{4})\s*", str(s)) if s is not None else None
    if not m:
        return None
    y1, y2 = int(m.group(1)), m.group(2)
    y2 = int(y2) if len(y2) == 4 else (y1 // 100) * 100 + int(y2)
    return (y1, y2) if y2 == y1 + 1 else None


def sort_key(d):
    return (d[0], d[1] or 0, d[2] or 0)


def _cmp_key(a, b):
    """Hai ngày cắt về độ chính xác chung (năm; thêm tháng nếu cả hai có; thêm ngày nếu cả hai có)."""
    n = 1 + (a[1] is not None and b[1] is not None) + (a[1] is not None and b[1] is not None and a[2] is not None and b[2] is not None)
    return a[:n], b[:n]


def words(t):
    return {w for w in re.findall(r"[a-z0-9]+", str(t).lower()) if w not in STOP}


# ---------------------------------------------------------------- đáp án chuẩn

def load_gold(repo, page):
    P = Path(repo) / "dataset/eval/timeline_pilot"
    f = next(P.glob(f"*/rev/{page}.json"))
    return {e["id"]: e for e in json.load(open(f, encoding="utf-8"))["events"]}


def load_questions(repo):
    """Mọi câu v9 (từ questions_v9/ đã lưu git), mỗi câu thêm `qid` = Trang:chỉ số (chỉ số theo dòng không rỗng)."""
    out = []
    for f in sorted((Path(repo) / "dataset/eval/timeline_pilot/questions_v9").glob("*.jsonl")):
        i = 0
        for line in open(f, encoding="utf-8"):
            if line.strip():
                q = json.loads(line); q["qid"] = f"{f.stem}:{i}"; out.append(q); i += 1
    return out


def expected(q, E):
    """Đáp án chuẩn: {'kind': 'number', 'value': n} hoặc {'kind': 'events', 'events': [{'id','date','text'}...]} (theo thứ tự ngày)."""
    if q["type"] == "order_gap":
        a, b = (parse_date(E[i]["date"]) for i in q["gold_event_ids"])
        return {"kind": "number", "value": abs(a[0] - b[0])}
    ids = q["answer_ids"] if q["type"] == "first_last_next" else q["gold_event_ids"]
    ev = [{"id": i, "date": E[i]["date"], "text": E[i]["text"]} for i in ids]
    ev.sort(key=lambda e: sort_key(parse_date(e["date"])))
    return {"kind": "events", "events": ev}


# ---------------------------------------------------------------- bộ chấm

def parse_number(pred):
    if isinstance(pred, bool):
        return None
    if isinstance(pred, (int, float)):
        return int(pred)
    if isinstance(pred, str):
        m = re.search(r"-?\d+", pred)
        return int(m.group()) if m else None
    return None


def score(exp, pred):
    """Chấm một câu: exp từ `expected`, pred là câu trả lời của hệ thống (số hoặc danh sách {date,text}). Rỗng/sai kiểu -> 0."""
    if exp["kind"] == "number":
        return {"exact": float(parse_number(pred) == exp["value"])}
    gold = exp["events"]
    pred = [p for p in (pred if isinstance(pred, list) else []) if isinstance(p, dict) and parse_date(p.get("date")) is not None]
    gd = [parse_date(g["date"]) for g in gold]
    # ghép tham lam: mỗi mốc chuẩn lấy mốc dự đoán chưa dùng, tương thích ngày, có độ trùng từ khóa cao nhất
    used, match = set(), {}
    for gi, g in enumerate(gold):
        best, bs = None, -1.0
        wg = words(g["text"])
        for pi, p in enumerate(pred):
            pd_ = parse_date(p["date"]); sa = season_alt(p["date"])
            ok = compatible(gd[gi], pd_) or (sa is not None and gd[gi] is not None and gd[gi][1] is None and gd[gi][0] in sa)  # mùa giải 'YYYY-YY' khớp năm đầu hoặc năm sau, chỉ với gold dạng chỉ-năm
            if pi in used or not ok:
                continue
            wp = words(p.get("text", ""))
            s = len(wg & wp) / (len(wg | wp) or 1)
            if s > bs:
                best, bs = pi, s
        if best is not None:
            used.add(best); match[gi] = best
    tp = len(match)
    prec, rec = (tp / len(pred) if pred else 0.0), (tp / len(gold) if gold else 0.0)
    f1 = 2 * prec * rec / (prec + rec) if tp else 0.0
    ms = sorted(match)
    pairs = [(a, b) for k, a in enumerate(ms) for b in ms[k + 1:] if _cmp_key(gd[a], gd[b])[0] != _cmp_key(gd[a], gd[b])[1]]  # chỉ cặp khác ngày ở độ chính xác chung (cùng năm, một bên chỉ có năm: không tính thứ tự)
    order = sum(1 for a, b in pairs if match[a] < match[b]) / len(pairs) if pairs else 1.0
    ex = float(tp == len(gold) == len(pred) and order == 1.0)
    return {"precision": prec, "recall": rec, "f1": f1, "order": order, "exact": ex, "exact_m2o": max(ex, exact_m2o(gold, gd, pred))}  # m2o chỉ nới thêm, không bao giờ thấp hơn exact


def exact_m2o(gold, gd, pred):
    """Chấm bổ sung 'nhiều-một': mốc chuẩn gộp nhiều việc (\"routes to London and Saipan\") được phép khớp với nhiều mốc dự đoán cùng ngày.
    Đạt khi: mọi mốc chuẩn có ít nhất một mốc dự đoán, mọi mốc dự đoán khớp một mốc chuẩn tương thích ngày (chọn theo độ trùng từ khóa), thứ tự đúng giữa các cặp mốc chuẩn khác nhau ở độ chính xác chung."""
    if not pred or not gold:
        return 0.0
    assign = []
    for p in pred:
        pdt, wp, best, bs = parse_date(p["date"]), words(p.get("text", "")), None, -1.0
        for gi, g in enumerate(gold):
            if compatible(gd[gi], pdt):
                sc = len(words(g["text"]) & wp) / (len(words(g["text"]) | wp) or 1)
                if sc > bs: best, bs = gi, sc
        if best is None:
            return 0.0
        assign.append(best)
    if set(assign) != set(range(len(gold))):
        return 0.0
    for a in range(len(assign)):
        for b in range(a + 1, len(assign)):
            ga, gb = assign[a], assign[b]
            if ga != gb:
                ka, kb = _cmp_key(gd[ga], gd[gb])
                if ka != kb and ka > kb:
                    return 0.0
    return 1.0


# ---------------------------------------------------------------- tự kiểm

def oracle_answer(exp, shuffle_ties=False):
    if exp["kind"] == "number":
        return exp["value"]
    ev = [{"date": e["date"], "text": e["text"]} for e in exp["events"]]
    if shuffle_ties:  # đảo ngược toàn bộ rồi sắp ổn định theo ngày -> mốc cùng ngày đổi chỗ, khác ngày vẫn đúng thứ tự
        ev.reverse(); ev.sort(key=lambda e: sort_key(parse_date(e["date"])))
    return ev


def selftest(repo):
    qs = load_questions(repo); cache = {}; bad = []; per = {}
    def E_of(page):
        if page not in cache: cache[page] = load_gold(repo, page)
        return cache[page]
    unparsable = []
    for q in qs:
        E = E_of(q["page"])
        for i in (q["gold_event_ids"] + (q.get("answer_ids") or [])):
            if parse_date(E[i]["date"]) is None: unparsable.append((q["qid"], i, E[i]["date"]))
        exp = expected(q, E)
        for tag, pred in (("oracle", oracle_answer(exp)), ("oracle_tie_shuffled", oracle_answer(exp, True))):
            s = score(exp, pred)
            per.setdefault((q["type"], tag), []).append(s["exact"])
            if s["exact"] != 1.0: bad.append((q["qid"], tag, s))
    print(f"{len(qs)} câu; không đọc được ngày: {len(unparsable)} {unparsable[:3]}")
    for k, v in sorted(per.items()): print(f"  {k[0]:16s} {k[1]:20s} exact={sum(v)/len(v):.4f} (n={len(v)})")
    print(f"oracle không ra 100%: {len(bad)} {bad[:5]}")
    # biến dạng cố ý: phải bị trừ điểm đúng
    chk = {"drop_one": 0, "drop_one_ok": 0, "swap": 0, "swap_ok": 0, "extra": 0, "extra_ok": 0, "wrong_number": 0, "wrong_number_ok": 0}
    for q in qs:
        exp = expected(q, E_of(q["page"]))
        if exp["kind"] == "number":
            chk["wrong_number"] += 1; chk["wrong_number_ok"] += score(exp, exp["value"] + 1)["exact"] == 0.0
            continue
        ev = oracle_answer(exp)
        if len(ev) >= 2:
            chk["drop_one"] += 1; s = score(exp, ev[:-1]); chk["drop_one_ok"] += (s["exact"] == 0.0 and s["recall"] < 1.0 and s["precision"] == 1.0)
            dates = [parse_date(e["date"]) for e in ev]
            if sort_key(dates[0]) != sort_key(dates[-1]):  # có ít nhất hai ngày khác nhau mới đảo được
                sw = ev[::-1]; chk["swap"] += 1; s = score(exp, sw); chk["swap_ok"] += (s["exact"] == 0.0 and s["order"] < 1.0)
        chk["extra"] += 1; s = score(exp, ev + [{"date": "1066", "text": "unrelated thing"}]); chk["extra_ok"] += (s["exact"] == 0.0 and s["recall"] == 1.0 and s["precision"] < 1.0)
    print("biến dạng cố ý (đúng = bị trừ điểm như mong đợi):", chk)
    return len(bad) == 0 and not unparsable


if __name__ == "__main__":
    repo = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "selftest":
        sys.exit(0 if selftest(repo) else 1)
    print(__doc__)
