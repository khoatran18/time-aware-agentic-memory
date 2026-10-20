"""Vẽ hai biểu đồ SVG cho `docs/eval/04_TEST_RESULTS.md` từ `dataset/eval/results_local.csv` (không cần thư viện vẽ).

1. `ranking.svg`: cột ngang, mỗi họ cấu hình lấy lần chạy `mrr` cao nhất, sắp theo `mrr`.
2. `t_unknown_grid.svg`: bảng màu có ghi số, hàng = họ cấu hình, cột = `t_unknown` (đủ mọi giá trị đã đo).
3. `t_unknown_curve.svg`: `mrr` theo `t_unknown` cho từng nền (đường nhạy cảm của đợt 4b).

Dùng: python scripts/plot_results.py [--csv dataset/eval/results_local.csv] [--out docs/eval/figures]
"""
from __future__ import annotations

import argparse
import csv
from html import escape
from pathlib import Path

from summarize_runs import group_rows

ROOT = Path(__file__).resolve().parents[1]

# Bảng màu và mực: nền tham chiếu đã qua scripts/validate_palette.js (xanh, cam, aqua, vàng, hồng)
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2dd"
BLUE, ORANGE, AQUA, YELLOW, PINK, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#9b9a93"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def load(path: Path) -> list[dict]:
    """Đọc CSV, ép kiểu số."""
    rows = []
    with open(path, encoding="utf-8") as f:
        loaded = list(csv.DictReader(f))
    for r in loaded:
        for k in ("hit@1", "hit@3", "hit@5", "mrr", "ctx_hit", "leakage_rate", "undated_in_results_rate"):
            r[k] = float(r[k])
        r["neighbors"] = int(r["neighbors"] or 0)
        r["tu"] = float(r["t_unknown"]) if r["t_unknown"] != "" else None
        rows.append(r)
    return rows


def best(rows: list[dict], **kw) -> dict:
    """Dòng `mrr` cao nhất trong các dòng e2e, không chunk liền kề, không domain, khớp các điều kiện `kw`."""
    pool = [r for r in rows if r["mode"] == "e2e" and not r["neighbors"] and r["facets"] == "none"
            and all(r.get(k) == v for k, v in kw.items() if k != "only_filter" and k != "has_tu")]
    if kw.get("has_tu") is not None:
        pool = [r for r in pool if (r["tu"] is not None) == kw["has_tu"]]
    pool = [r for r in pool if (r["only_filter"] == "yes") == bool(kw.get("only_filter"))]
    return max(pool, key=lambda r: r["mrr"])


def svg_open(w: int, h: int, title: str) -> list[str]:
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{escape(title)}" font-family="{FONT}" font-size="12">')
    return [head, f"<title>{escape(title)}</title>", f'<rect width="{w}" height="{h}" rx="10" fill="{SURFACE}"/>']


def text(x: float, y: float, s: str, *, fill: str = INK, anchor: str = "start", size: int = 12, weight: str = "normal",
         halo: bool = False) -> str:
    """Chữ; `halo` vẽ viền màu nền quanh chữ để không dính vào đường lưới."""
    extra = f' paint-order="stroke" stroke="{SURFACE}" stroke-width="4" stroke-linejoin="round"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}"{extra}>{escape(s)}</text>')


TUS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7]
FAMILIES = [("hybrid", "stored"), ("hybrid", "open"), ("hybrid", "decay 0.05"), ("hybrid", "decay 0.1"), ("hybrid", "decay 0.2"),
            ("dense", "stored"), ("dense", "open"), ("dense", "decay 0.1"), ("dense", "unknown decay 0.05"),
            ("dense", "unknown decay 0.1"), ("dense", "unknown decay 0.2"), ("dense", "unknown decay 0.3"), ("BM25 0.25", "stored"),
            ("BM25 0.25", "open"), ("BM25 0.5", "stored")]


def pick(rows: list[dict], base: str, end: str, tu: float | None) -> dict | None:
    """Dòng e2e của họ (nền tìm kiếm, cách chấm end) với giá trị `t_unknown` đã cho (None = tắt)."""
    pool = [r for r in rows if r["mode"] == "e2e" and not r["neighbors"] and r["facets"] == "none" and r["only_filter"] != "yes"
            and r["base"] == base and r["end_mode"] == end and r["tu"] == tu]
    return pool[0] if pool else None


def short_name(config: str) -> str:
    """Tên gọn cho biểu đồ (cùng nội dung với bảng): bỏ tiền tố dài, giữ nền tìm kiếm · end · t_unknown."""
    return (config.replace("Cơ chế 1 · tìm kiếm ", "").replace("chunk không mốc tắt", "không t_unknown")
            .replace("chunk không mốc ", "").replace("Chỉ lọc thời gian (bỏ điểm thời gian) · tìm kiếm ", "Chỉ lọc thời gian · ")
            .replace("Oracle (t_req từ nhãn) · ", "Oracle · "))


def ranking_svg(rows: list[dict]) -> str:
    """Cột ngang: MỌI nhóm cấu hình như trong bảng xếp hạng (cùng số hạng), các dòng chỉ khác `t_unknown` mà kết quả y hệt đã gộp."""
    inputs = []
    for r in rows:
        if r["neighbors"]:
            continue  # chunk liền kề không đổi thứ hạng: nằm ở bảng riêng
        stem, sep, _ = r["config"].partition(" · chunk không mốc ")
        inputs.append({**r, "stem": stem, "has_tu_part": bool(sep), "t_unknown": r["t_unknown"]})
    groups = group_rows(inputs)

    w, left, right, top, row_h = 1240, 560, 150, 96, 18
    h = top + row_h * len(groups) + 60
    plot_w = w - left - right
    x = lambda v: left + v / 0.6 * plot_w
    out = svg_open(w, h, f"Xếp hạng toàn bộ {len(groups)} nhóm cấu hình theo mrr (bộ local, 40 câu)")
    out.append(text(24, 28, f"Xếp hạng theo mrr: toàn bộ {len(groups)} nhóm cấu hình (bộ local, 40 câu), cùng thứ tự với bảng bên dưới", size=15, weight="600"))
    for i, (name, color) in enumerate([("Cơ chế 1 + nhánh chunk không mốc (t_unknown)", ORANGE), ("Cơ chế 1, không nhánh chunk không mốc", BLUE),
                                       ("Plain RAG (không lọc thời gian)", GRAY)]):
        lx = [24, 340, 640][i]
        out.append(f'<rect x="{lx}" y="46" width="12" height="12" rx="2" fill="{color}"/>')
        out.append(text(lx + 18, 56, name, fill=INK2))
    out.append(text(24, 76, "Oracle (t_req lấy từ nhãn, không xếp hạng) vẽ cột rỗng. Mỗi dòng: hạng · tên · cột mrr · mrr, hit@5. Chỉ khác t_unknown mà kết quả y hệt thì gộp (vd 0.2 / 0.3).", fill=INK2, size=11))
    for v in (0, 0.2, 0.4, 0.6):
        out.append(f'<line x1="{x(v):.1f}" y1="{top - 6}" x2="{x(v):.1f}" y2="{h - 44}" stroke="{GRID}" stroke-width="1"/>')
        out.append(text(x(v), h - 28, f"{v:.1f}", fill=INK2, anchor="middle"))
    out.append(text(left + plot_w / 2, h - 10, "mrr (càng cao càng tốt)", fill=INK2, anchor="middle"))
    plain = next(g for g in groups if g["kind"] == "baseline" and g["base"] == "dense")
    ref = x(plain["mrr"])
    out.append(f'<line x1="{ref:.1f}" y1="{top - 6}" x2="{ref:.1f}" y2="{h - 44}" stroke="{INK2}" stroke-width="1" stroke-dasharray="4 3"/>')
    out.append(text(ref + 5, top - 12, "plain RAG (dense) 0.340", fill=INK2, size=11, halo=True))
    for i, g in enumerate(groups):
        y = top + i * row_h
        oracle = g["mode"] == "oracle"
        color = GRAY if g["kind"] == "baseline" else (ORANGE if g["t_unknown"] != "" else BLUE)
        out.append(text(24, y + 13, str(g["rank"]), fill=INK2, size=11))
        out.append(text(left - 10, y + 13, short_name(g["config"]), anchor="end", size=11))
        bar = f'M{left} {y + 3} H{x(g["mrr"]) - 3:.1f} a3 3 0 0 1 3 3 v6 a3 3 0 0 1 -3 3 H{left} Z'
        style = f'fill="none" stroke="{INK2}" stroke-width="1.5"' if oracle else f'fill="{color}"'
        out.append(f'<path d="{bar}" {style}><title>{escape(g["config"])}: mrr {g["mrr"]:.3f}, hit@5 {g["hit@5"]:.3f}</title></path>')
        out.append(text(x(g["mrr"]) + 8, y + 13, f'{g["mrr"]:.3f} · {g["hit@5"]:.3f}', size=11, weight="600", halo=True))
    out.append("</svg>")
    return "\n".join(out)


def mix(c1: str, c2: str, t: float) -> str:
    """Màu trộn tuyến tính giữa hai màu hex."""
    a, b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)], [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x0 + (x1 - x0) * t):02x}" for x0, x1 in zip(a, b))


def grid_svg(rows: list[dict]) -> str:
    """Bảng màu: hàng = họ cấu hình, cột = tắt và từng `t_unknown`; màu càng đậm `mrr` càng cao; viền = đỉnh của hàng."""
    cols = ["tắt", *[f"{t:.1f}" for t in TUS]]
    data = []
    for base, end in FAMILIES:
        vals = [pick(rows, base, end, None), *[pick(rows, base, end, tu) for tu in TUS]]
        data.append((f"{base} · end {end}", [v["mrr"] if v else None for v in vals]))
    data.sort(key=lambda d: -max(v for v in d[1] if v is not None))
    flat = [v for _, vs in data for v in vs if v is not None]
    lo, hi = min(flat), max(flat)
    w, left, top, cw, ch = 900, 230, 96, 80, 30
    h = top + ch * len(data) + 70
    out = svg_open(w, h, "mrr theo họ cấu hình và giá trị t_unknown (bảng màu)")
    out.append(text(24, 28, "mrr theo họ cấu hình (hàng) và t_unknown (cột), bộ local 40 câu", size=15, weight="600"))
    out.append(text(24, 48, "Màu càng đậm mrr càng cao; ô viền đen = giá trị cao nhất của hàng; \"tắt\" = không bật nhánh chunk không mốc.", fill=INK2, size=11))
    for j, c in enumerate(cols):
        out.append(text(left + j * cw + cw / 2, top - 10, c if c == "tắt" else f"t_unknown {c}", fill=INK2, anchor="middle", size=11))
    for i, (name, vals) in enumerate(data):
        y = top + i * ch
        out.append(text(left - 10, y + ch / 2 + 4, name, anchor="end"))
        peak = max(v for v in vals if v is not None)
        for j, v in enumerate(vals):
            x0 = left + j * cw
            if v is None:
                out.append(text(x0 + cw / 2, y + ch / 2 + 4, "—", fill=INK2, anchor="middle"))
                continue
            t = (v - lo) / (hi - lo)
            fill = mix("#e6eefb", "#1f5bb0", t)
            stroke = f'stroke="{INK}" stroke-width="2"' if v == peak else f'stroke="{SURFACE}" stroke-width="2"'
            out.append(f'<rect x="{x0 + 1}" y="{y + 1}" width="{cw - 2}" height="{ch - 2}" rx="3" fill="{fill}" {stroke}>'
                       f'<title>{escape(name)} · {cols[j] if j == 0 else "t_unknown " + cols[j]}: mrr {v:.3f}</title></rect>')
            out.append(text(x0 + cw / 2, y + ch / 2 + 4, f"{v:.3f}", fill="#ffffff" if t > 0.55 else INK, anchor="middle", weight="600" if v == peak else "normal"))
    out.append("</svg>")
    return "\n".join(out)


MARKERS = ["circle", "square", "diamond", "triangle", "cross"]


def marker(kind: str, cx: float, cy: float, color: str, title: str, r: float = 5) -> str:
    """Dấu điểm >= 8px, viền nền 2px để không dính nhau."""
    ring = f'stroke="{SURFACE}" stroke-width="2"'
    if kind == "circle":
        shape = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{color}" {ring}>'
    elif kind == "square":
        shape = f'<rect x="{cx - r:.1f}" y="{cy - r:.1f}" width="{2 * r}" height="{2 * r}" fill="{color}" {ring}>'
    elif kind == "diamond":
        shape = f'<path d="M{cx:.1f} {cy - r - 1:.1f} L{cx + r + 1:.1f} {cy:.1f} L{cx:.1f} {cy + r + 1:.1f} L{cx - r - 1:.1f} {cy:.1f} Z" fill="{color}" {ring}>'
    elif kind == "triangle":
        shape = f'<path d="M{cx:.1f} {cy - r - 1:.1f} L{cx + r + 1:.1f} {cy + r:.1f} L{cx - r - 1:.1f} {cy + r:.1f} Z" fill="{color}" {ring}>'
    else:
        shape = (f'<path d="M{cx - r:.1f} {cy - r:.1f} L{cx + r:.1f} {cy + r:.1f} M{cx + r:.1f} {cy - r:.1f} L{cx - r:.1f} {cy + r:.1f}" '
                 f'stroke="{color}" stroke-width="3" fill="none">')
    tag = "path" if kind in ("diamond", "triangle", "cross") else kind if kind != "square" else "rect"
    return f"{shape}<title>{escape(title)}</title></{tag}>"


def curve_svg(rows: list[dict]) -> str:
    """Đường mrr theo t_unknown cho từng nền."""
    tus = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7]
    series = [("hybrid · end stored", {'base': 'hybrid', 'end_mode': 'stored'}, BLUE), ("dense · end stored", {'base': 'dense', 'end_mode': 'stored'}, ORANGE),
              ("BM25 0.25 · end stored", {'base': 'BM25 0.25', 'end_mode': 'stored'}, AQUA),
              ("dense · end open", {'base': 'dense', 'end_mode': 'open'}, YELLOW),
              ("dense · end unknown decay 0.1", {'base': 'dense', 'end_mode': 'unknown decay 0.1'}, PINK)]

    def val(kw, tu):
        pool = [r for r in rows if r["mode"] == "e2e" and not r["neighbors"] and r["facets"] == "none" and r["only_filter"] != "yes"
                and r["base"] == kw["base"] and r["end_mode"] == kw["end_mode"] and r["tu"] == tu]
        return pool[0]["mrr"] if pool else None

    w, h, left, right, top, bottom = 960, 450, 70, 40, 106, 70
    plot_w, plot_h = w - left - right, h - top - bottom
    lo, hi = 0.40, 0.60
    xs = [left + 70 + i * (plot_w - 70) / (len(tus) - 1) for i in range(len(tus))]  # 70px đầu dành cho "tắt"
    x_off = left + 12
    y = lambda v: top + (hi - v) / (hi - lo) * plot_h
    out = svg_open(w, h, "mrr theo t_unknown cho từng nền tìm kiếm (bộ local)")
    out.append(text(24, 28, "mrr theo t_unknown, từng nền tìm kiếm (bộ local, 40 câu)", size=15, weight="600"))
    lx, ly = 24, 52
    for i, (name, _kw, color) in enumerate(series):
        width = 30 + 7 * len(name) + 20
        if lx + width > w - 24:  # xuống hàng khi hết chỗ
            lx, ly = 24, ly + 20
        out.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 16}" y2="{ly}" stroke="{color}" stroke-width="2"/>')
        out.append(marker(MARKERS[i], lx + 8, ly, color, name))
        out.append(text(lx + 24, ly + 4, name, fill=INK2))
        lx += width
    for v in (0.40, 0.44, 0.48, 0.52, 0.56, 0.60):
        out.append(f'<line x1="{left}" y1="{y(v):.1f}" x2="{w - right}" y2="{y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(text(left - 8, y(v) + 4, f"{v:.2f}", fill=INK2, anchor="end"))
    div = (x_off + xs[0]) / 2 + 6
    out.append(f'<line x1="{div:.1f}" y1="{top}" x2="{div:.1f}" y2="{top + plot_h}" stroke="{INK2}" stroke-width="1" stroke-dasharray="4 3"/>')
    out.append(text(x_off, h - 40, "tắt", fill=INK2, anchor="middle"))
    for xi, tu in zip(xs, tus):
        out.append(text(xi, h - 40, f"{tu:.1f}", fill=INK2, anchor="middle"))
    out.append(text(left + plot_w / 2, h - 12, "t_unknown (các mốc cách đều nhau, không theo tỉ lệ; \"tắt\" = không bật nhánh chunk không mốc)", fill=INK2, anchor="middle"))
    out.append(text(18, top + plot_h / 2, "mrr", fill=INK2, anchor="middle"))
    peaks = []
    for i, (name, kw, color) in enumerate(series):
        off_rows = [r for r in rows if r["mode"] == "e2e" and not r["neighbors"] and r["facets"] == "none" and r["only_filter"] != "yes"
                    and r["base"] == kw["base"] and r["end_mode"] == kw["end_mode"] and r["tu"] is None]
        pts = [(x_off, off_rows[0]["mrr"])] if off_rows else []
        pts += [(xi, val(kw, tu)) for xi, tu in zip(xs, tus) if val(kw, tu) is not None]
        d = " ".join(f"{'M' if j == 0 else 'L'}{px:.1f} {y(v):.1f}" for j, (px, v) in enumerate(pts))
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
        for px, v in pts:
            tu_txt = "tắt" if px == x_off else f"{tus[xs.index(px)]:.1f}"
            out.append(marker(MARKERS[i], px, y(v), color, f"{name}, t_unknown {tu_txt}: mrr {v:.3f}"))
        peak = max(pts, key=lambda p: p[1])
        peaks.append((name, peak))
    # nhãn trực tiếp cho ba đường chính (điểm đỉnh)
    short = {"hybrid · end stored": "hybrid · stored", "dense · end stored": "dense · stored", "dense · end unknown decay 0.1": "dense · unknown decay 0.1"}
    for name, (px, v) in peaks:
        if name in short:
            out.append(text(px, y(v) - 12, f"{short[name]}: {v:.3f}", fill=INK, anchor="middle", weight="600"))
    out.append("</svg>")
    return "\n".join(out)


def family_of(r: dict) -> str:
    """Nhóm màu của một dòng: Plain RAG, chỉ lọc, hybrid, dense, hoặc trộn BM25 một phần."""
    if r["kind"] == "baseline":
        return "Plain RAG"
    if r["only_filter"] == "yes":
        return "Chỉ lọc thời gian"
    return {"hybrid": "Cơ chế 1 · hybrid", "dense": "Cơ chế 1 · dense"}.get(r["base"], "Cơ chế 1 · BM25 một phần")


FAMILY_COLORS = {"Plain RAG": GRAY, "Chỉ lọc thời gian": PINK, "Cơ chế 1 · hybrid": BLUE, "Cơ chế 1 · dense": ORANGE,
                 "Cơ chế 1 · BM25 một phần": AQUA}


def compare_svg(local: list[dict], real: list[dict], metric: str = "mrr") -> str:
    """Điểm = một cấu hình: x = `metric` ở local, y = ở bộ thật. Đường chéo y = x; điểm dưới đường chéo là thấp hơn ở bộ thật."""
    by_real = {r["config"]: r for r in real if r["mode"] == "e2e"}
    pts = [(r, by_real[r["config"]]) for r in local if r["mode"] == "e2e" and r["config"] in by_real]
    lo, hi = (0.35, 0.9) if metric == "hit@5" else (0.15, 0.62)
    w, h, m = 640, 560, 64
    px = lambda v: m + (v - lo) / (hi - lo) * (w - 2 * m)
    py = lambda v: h - m - (v - lo) / (hi - lo) * (h - 2 * m)
    out = svg_open(w, h, f"{metric} ở bộ local so với bộ thật")
    out.append(text(m, 26, f"{metric}: bộ local (x) so với bộ thật (y), mỗi điểm một cấu hình", size=14, weight="600"))
    step = 0.05 if metric == "mrr" else 0.1
    t = lo
    while t <= hi + 1e-9:
        out.append(f'<line x1="{px(t):.1f}" y1="{py(lo):.1f}" x2="{px(t):.1f}" y2="{py(hi):.1f}" stroke="{GRID}"/>')
        out.append(f'<line x1="{px(lo):.1f}" y1="{py(t):.1f}" x2="{px(hi):.1f}" y2="{py(t):.1f}" stroke="{GRID}"/>')
        out.append(text(px(t), h - m + 18, f"{t:.2f}", fill=INK2, anchor="middle", size=11))
        out.append(text(m - 8, py(t) + 4, f"{t:.2f}", fill=INK2, anchor="end", size=11))
        t += step
    out.append(f'<line x1="{px(lo):.1f}" y1="{py(lo):.1f}" x2="{px(hi):.1f}" y2="{py(hi):.1f}" stroke="{INK2}" stroke-dasharray="5 4"/>')
    out.append(text(px(hi) - 4, py(hi) + 14, "y = x", fill=INK2, anchor="end", size=11))
    out.append(text((w) / 2, h - 14, f"{metric} bộ local (40 câu)", fill=INK2, anchor="middle"))
    out.append(f'<text transform="translate(16 {h / 2:.0f}) rotate(-90)" fill="{INK2}" text-anchor="middle">{metric} bộ thật (400 câu)</text>')
    for a, b in pts:
        fam = family_of(a)
        out.append(f'<circle cx="{px(a[metric]):.1f}" cy="{py(b[metric]):.1f}" r="4.5" fill="{FAMILY_COLORS[fam]}" fill-opacity="0.8" '
                   f'stroke="{SURFACE}" stroke-width="1"><title>{escape(a["config"])}: local {a[metric]:.3f}, thật {b[metric]:.3f}</title></circle>')
    bl = max(pts, key=lambda p: p[0][metric])
    br = max(pts, key=lambda p: p[1][metric])
    for (a, b), label in ((bl, "tốt nhất ở local"), (br, "tốt nhất ở bộ thật")):
        out.append(f'<circle cx="{px(a[metric]):.1f}" cy="{py(b[metric]):.1f}" r="8" fill="none" stroke="{INK}" stroke-width="1.5"/>')
        dy = 26 if label.endswith("local") else -22  # tốt nhất ở local: nhãn phía dưới; ở bộ thật: nhãn phía trên
        out.append(f'<line x1="{px(a[metric]):.1f}" y1="{py(b[metric]):.1f}" x2="{px(a[metric]) - 10:.1f}" y2="{py(b[metric]) + dy - 4:.1f}" stroke="{INK}" stroke-width="0.8"/>')
        out.append(text(px(a[metric]) - 12, py(b[metric]) + dy, label, anchor="end", size=11, halo=True))
    lx, ly = m + 8, 62  # góc trái trên: vùng trống phía trên đường chéo
    for i, (fam, color) in enumerate(FAMILY_COLORS.items()):
        out.append(f'<circle cx="{lx + 6}" cy="{ly + 20 * i}" r="5" fill="{color}"/>')
        out.append(text(lx + 18, ly + 20 * i + 4, fam, size=11))
    out.append("</svg>")
    return "\n".join(out)


FUNNEL_COLORS = [BLUE, GRAY, YELLOW, PINK, ORANGE]


def funnel_svg(path: Path) -> str:
    """Thanh chồng ngang: mỗi câu có chunk đúng rơi vào một nhóm (trúng top-5, không vào ứng viên, bị lọc, xếp sau top-5)."""
    with open(path, encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    groups = [k for k in data[0] if k not in ("config", "n", "dir")]
    w, row_h, left, right = 960, 54, 380, 20
    h = 90 + row_h * len(data) + 40
    out = svg_open(w, h, "Chunk đúng rơi ở đâu trong phễu")
    out.append(text(20, 26, "Mỗi câu rơi vào đúng một nhóm: chunk đúng ở đâu trong phễu (bộ thật, 399 câu có đáp án)", size=14, weight="600"))
    for i, g in enumerate(groups):
        x = 20 + i * 185
        out.append(f'<rect x="{x}" y="42" width="12" height="12" rx="2" fill="{FUNNEL_COLORS[i]}"/>')
        out.append(text(x + 18, 53, g.replace("bị lọc: chunk đúng không có mốc", "lọc: chunk đúng không mốc").replace("bị lọc: ", "lọc: "), size=11))
    scale = (w - left - right) / max(int(r["n"]) for r in data)
    for j, r in enumerate(data):
        y = 80 + j * row_h
        out.append(text(left - 10, y + 24, r["config"], anchor="end", size=12))
        x = left
        for i, g in enumerate(groups):
            v = int(r[g])
            bw = v * scale
            if v:
                out.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="34" fill="{FUNNEL_COLORS[i]}">'
                           f'<title>{escape(r["config"])} · {escape(g)}: {v} câu ({v / int(r["n"]):.1%})</title></rect>')
                if bw > 34:
                    fg = "#ffffff" if FUNNEL_COLORS[i] in (BLUE, PINK, ORANGE) else INK
                    out.append(text(x + bw / 2, y + 22, str(v), fill=fg, anchor="middle", size=12, weight="600"))
            x += bw
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(ROOT / "dataset" / "eval" / "results_local.csv"))
    ap.add_argument("--out", default=str(ROOT / "docs" / "eval" / "figures"))
    ap.add_argument("--compare-with", help="CSV của bộ local khi --csv là bộ thật: vẽ thêm compare_mrr.svg, compare_hit5.svg (x = local, y = bộ thật)")
    ap.add_argument("--funnel", help="CSV từ scripts/funnel_real.py: vẽ thêm funnel.svg")
    args = ap.parse_args()
    rows = load(Path(args.csv))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ranking.svg").write_text(ranking_svg(rows), encoding="utf-8")
    (out / "t_unknown_grid.svg").write_text(grid_svg(rows), encoding="utf-8")
    (out / "t_unknown_curve.svg").write_text(curve_svg(rows), encoding="utf-8")
    if args.compare_with:
        local = load(Path(args.compare_with))
        (out / "compare_mrr.svg").write_text(compare_svg(local, rows, "mrr"), encoding="utf-8")
        (out / "compare_hit5.svg").write_text(compare_svg(local, rows, "hit@5"), encoding="utf-8")
    if args.funnel:
        (out / "funnel.svg").write_text(funnel_svg(Path(args.funnel)), encoding="utf-8")
    print(f"Ghi {out}/ranking.svg, {out}/t_unknown_grid.svg và {out}/t_unknown_curve.svg")


if __name__ == "__main__":
    main()
