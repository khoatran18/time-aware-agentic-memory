"""Gom `metrics.json` của nhiều lần `evaluate.py` thành một bảng: CSV (dữ liệu) và bảng markdown xếp hạng theo `mrr`.

Đầu vào: file TSV hai cột `<nhãn>\t<thư mục output>` (mỗi dòng một lần chạy). Các lần chạy cùng cấu hình (cùng tham số) chỉ giữ một; các cấu hình chỉ khác `t_unknown` mà kết quả y hệt được gộp thành một dòng trong bảng markdown (CSV vẫn đủ từng lần chạy).
Dùng: python scripts/summarize_runs.py runs.tsv --csv dataset/eval/results_local.csv > bang.md
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["config", "kind", "base", "end_mode", "neighbors", "t_unknown", "facets", "only_filter", "mode", "hit@1", "hit@3", "hit@5",
          "mrr", "ctx_hit", "leakage_rate", "undated_in_results_rate", "dir"]
METHOD_NAMES = {"dense": "dense", "bm25": "BM25", "hybrid": "hybrid"}
METRICS = ("hit@1", "hit@3", "hit@5", "mrr", "ctx_hit", "leakage_rate")


def base_name(sparse_weight: float) -> str:
    """Tên nền tìm kiếm của Cơ chế 1 theo trọng số BM25 trong RRF."""
    return {1.0: "hybrid", 0.0: "dense"}.get(sparse_weight, f"BM25 {sparse_weight:g}")


def undated_text(tu: float | str | None) -> str:
    """Phần tên về nhánh chunk không mốc: `tắt` hoặc `t_unknown X`."""
    return "tắt" if tu in (None, "") else f"t_unknown {float(tu):.1f}"


def describe(cfg: dict) -> dict:
    """Từ khối `config` của metrics.json: tên cấu hình dễ đọc và các thành phần để nhóm/vẽ.

    Quy ước tên: `Cơ chế 1 · tìm kiếm <nền> · end <cách chấm end> · chunk không mốc <tắt | t_unknown X>` (kèm chunk liền kề, domain nếu có).
    Plain RAG là baseline không lọc thời gian: `Plain RAG · <dense | BM25 | hybrid>`. `stem` là tên không gồm phần chunk không mốc,
    để gộp các dòng chỉ khác `t_unknown`.
    """
    r = cfg.get("retrieval", {})
    method, mode = cfg.get("method", "temporal"), cfg.get("mode", "e2e")
    if method != "temporal":
        return {"kind": "baseline", "base": method, "end_mode": "", "neighbors": 0, "t_unknown": "", "facets": "none",
                "only_filter": "", "stem": f"Plain RAG · {METHOD_NAMES[method]}", "has_tu_part": False}
    base = base_name(r.get("sparse_weight", 1.0))
    only_filter = bool(cfg.get("no_temporal"))
    end = r.get("end_mode", "stored")
    d = r.get("open_decay", 0.1)
    end_txt = {"stored": "stored", "open": "open", "decay": f"decay {d:g}", "unknown_decay": f"unknown decay {d:g}"}[end]
    nb, tu, facets = r.get("neighbor_window", 0), r.get("t_unknown"), cfg.get("facets", "none")
    if only_filter:
        stem = f"Chỉ lọc thời gian (bỏ điểm thời gian) · tìm kiếm {base}"
    else:
        stem = f"Cơ chế 1 · tìm kiếm {base} · end {end_txt}"
    if nb:
        stem += f" · lấy thêm {nb} chunk liền kề"
    if facets == "domain":
        stem += " · lọc cứng domain"
    elif facets == "boost":
        stem += f" · cộng điểm domain W3 {r.get('w3', 0):g}"
    if mode == "oracle":
        stem = "Oracle (t_req từ nhãn) · " + stem
    return {"kind": "co_che_1_tu" if tu is not None else "co_che_1", "base": base, "end_mode": end_txt if not only_filter else "",
            "neighbors": nb, "t_unknown": "" if tu is None else tu, "facets": facets, "only_filter": "yes" if only_filter else "",
            "stem": stem, "has_tu_part": not only_filter}


def full_name(stem: str, has_tu_part: bool, tus: list) -> str:
    """Tên đầy đủ: `stem` + phần chunk không mốc (một hoặc nhiều giá trị `t_unknown`, vd `t_unknown 0.1 / 0.2`)."""
    if not has_tu_part:
        return stem
    off = [t for t in tus if t in (None, "")]
    vals = sorted({float(t) for t in tus if t not in (None, "")})
    parts = (["tắt"] if off else []) + [f"{v:.1f}" for v in vals]
    label = "tắt" if not vals else ("t_unknown " if not off else "") + " / ".join(parts)
    return f"{stem} · chunk không mốc {label}"


def load_rows(runs_tsv: Path) -> list[dict]:
    """Đọc từng lần chạy, bỏ trùng cấu hình, trả danh sách dòng."""
    seen: dict[str, dict] = {}
    for line in runs_tsv.read_text(encoding="utf-8").splitlines():
        _label, d, rc = (line.split("\t") + ["", "0"])[:3]
        if rc.strip() not in ("", "0") or not d:
            continue
        m = json.loads((ROOT / d / "metrics.json").read_text(encoding="utf-8"))
        info = describe(m["config"])
        key = f"{info['stem']}|{info['t_unknown']}"
        if key in seen:
            continue
        info["config"] = full_name(info["stem"], info["has_tu_part"], [info["t_unknown"]])
        seen[key] = {
            **info, "mode": m["config"].get("mode", "e2e"), "hit@1": m["hit@1"], "hit@3": m["hit@3"], "hit@5": m["hit@5"],
            "mrr": m["mrr"], "ctx_hit": m["ctx_hit"], "leakage_rate": m["leakage_rate"],
            "undated_in_results_rate": m["undated_in_results_rate"], "dir": Path(d).name,
        }
    return list(seen.values())


def group_rows(rows: list[dict]) -> list[dict]:
    """Gộp các dòng chỉ khác `t_unknown` mà kết quả y hệt (cùng `stem`, cùng các số đo); xếp hạng theo `mrr` (3 chữ số).

    Hạng bằng nhau khi `mrr` bằng nhau; oracle không xếp hạng. Mỗi nhóm có `rows` (các lần chạy), `config` (tên gộp) và số đo.
    """
    buckets: dict[tuple, list[dict]] = {}
    for r in rows:
        buckets.setdefault((r["stem"], r["mode"], tuple(round(r[k], 3) for k in METRICS)), []).append(r)
    groups = []
    for rs in buckets.values():
        first = rs[0]
        groups.append({**first, "rows": rs, "config": full_name(first["stem"], first["has_tu_part"], [x["t_unknown"] for x in rs]),
                       "dir": ", ".join(f"`{x['dir']}`" for x in rs)})
    groups.sort(key=lambda g: (g["mode"] == "oracle", -round(g["mrr"], 3), -g["hit@5"], g["config"]))
    pos = prev = None
    for i, g in enumerate(groups, 1):
        if g["mode"] == "oracle":
            g["rank"] = "—"
            continue
        if round(g["mrr"], 3) != prev:
            pos, prev = i, round(g["mrr"], 3)
        g["rank"] = pos
    return groups


def markdown(groups: list[dict]) -> str:
    """Bảng markdown xếp hạng (mỗi nhóm một dòng)."""
    out = ["| Hạng | Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `ctx_hit` | `leakage_rate` | Thư mục |", "|---|---|---|---|---|---|---|---|---|"]
    for g in groups:
        out.append(f"| {g['rank']} | {g['config']} | {g['hit@1']:.3f} | {g['hit@3']:.3f} | {g['hit@5']:.3f} | **{g['mrr']:.3f}** | "
                   f"{g['ctx_hit']:.3f} | {g['leakage_rate']:.3f} | {g['dir'].replace('`', '')} |")
    return "\n".join(out)


def markdown_neighbors(groups: list[dict]) -> str:
    """Bảng riêng cho cấu hình có chunk liền kề: xếp hạng không đổi, chỉ `ctx_hit` (ngữ cảnh) đổi."""
    out = ["| Cấu hình | `hit@5` | `ctx_hit` | `mrr` | Thư mục |", "|---|---|---|---|---|"]
    for g in sorted(groups, key=lambda g: (-g["ctx_hit"], g["config"])):
        out.append(f"| {g['config']} | {g['hit@5']:.3f} | **{g['ctx_hit']:.3f}** | {g['mrr']:.3f} | {g['dir'].replace('`', '')} |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", help="TSV: nhãn<TAB>thư mục output<TAB>mã thoát (tùy chọn)")
    ap.add_argument("--csv", help="ghi dữ liệu ra CSV này")
    args = ap.parse_args()
    all_rows = load_rows(Path(args.runs))
    groups = group_rows([r for r in all_rows if not r["neighbors"]])  # chunk liền kề không đổi thứ hạng: bảng riêng
    nb_groups = group_rows([r for r in all_rows if r["neighbors"]])
    if args.csv:
        rank_of = {id(r): g["rank"] for g in groups for r in g["rows"]}
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["rank", *FIELDS], extrasaction="ignore")
            w.writeheader()
            for g in groups:
                w.writerows({**r, "rank": rank_of[id(r)]} for r in sorted(g["rows"], key=lambda r: str(r["t_unknown"])))
            for g in nb_groups:
                w.writerows({**r, "rank": "—"} for r in g["rows"])
    sys.stdout.write(markdown(groups) + "\n\n<!--NEIGHBORS-->\n\n" + markdown_neighbors(nb_groups) + "\n")
    sys.stderr.write(f"{len(groups)} nhóm xếp hạng, {len(nb_groups)} nhóm có chunk liền kề ({len(all_rows)} lần chạy khác cấu hình)\n")


if __name__ == "__main__":
    main()
