"""Sinh câu trả lời ngắn từ kết quả truy xuất của một lần chạy evaluate.py rồi chấm EM/F1.

    python scripts/generate_answers.py --run output/<lần chạy evaluate> --subset test_clean --prompt v1 [--sample 100] [--batch 4]

Đọc `predictions.jsonl` của lần chạy (top-K chunk), lấy văn bản chunk từ Qdrant, gộp `--batch` câu mỗi request LLM (profile `--profile`,
mặc định google_35), chạy song song `--workers` luồng dưới một lịch chung `--rpm` request/phút. Ghi `output/<thời điểm>/answers.jsonl`
và `metrics.json`. Sai định dạng (thiếu/lặp số câu hoặc JSON hỏng) quá `--max-bad` lô thì DỪNG, ghi `format_errors.jsonl` để kiểm tra
(thoát mã 3); LLM hết hạn mức thì dừng (mã 1), chạy lại sẽ dùng cache cho phần đã xong.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from profile_eval import PacedCache, Pacer  # noqa: E402

from tam.config.loader import load_config  # noqa: E402
from tam.config.logging import get_logger, get_run_dir, setup_logging  # noqa: E402
from tam.embedding.factory import get_embedder  # noqa: E402
from tam.generation.answerer import Answerer, is_refusal  # noqa: E402
from tam.generation.scoring import contains, exact_match, f1_score  # noqa: E402
from tam.llm.factory import get_llm  # noqa: E402
from tam.llm.structured import LlmUnavailable  # noqa: E402
from tam.stores.vector.qdrant_store import QdrantStore, collection_for  # noqa: E402

logger = get_logger("generate_answers")


def pick_sample(cases: list[dict], n: int, seed: int) -> list[str]:
    """n id, chia đều theo domain (xoay vòng giữa các domain trong thứ tự ngẫu nhiên cố định theo seed); cùng seed thì cùng mẫu."""
    rng = random.Random(seed)
    by = {}
    for c in cases:
        by.setdefault(c["domain"], []).append(c["idx"])
    for ids in by.values():
        rng.shuffle(ids)
    out, doms = [], sorted(by)
    while len(out) < n and any(by.values()):
        for d in doms:
            if by[d] and len(out) < n:
                out.append(by[d].pop())
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="thư mục output của lần chạy evaluate.py (có predictions.jsonl)")
    ap.add_argument("--subset", required=True)
    ap.add_argument("--prompt", choices=["v1", "v2", "v3", "v4"], default="v1")
    ap.add_argument("--profile", default="google_35", help="profile LLM trong config (llm.profiles)")
    ap.add_argument("--top-k", type=int, default=15, help="số chunk đưa vào ngữ cảnh mỗi câu")
    ap.add_argument("--batch", type=int, default=4, help="số câu mỗi request")
    ap.add_argument("--sample", type=int, default=0, help=">0: chỉ n câu, chia đều theo domain (seed cố định)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help=">0: chỉ n câu đầu (thử nhanh)")
    ap.add_argument("--ids-file", default="", help="tệp JSON danh sách id: chỉ chạy các câu này (chạy bù câu còn thiếu)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rpm", type=float, default=12.0, help="tổng số request mỗi phút (hạn mức Gemini 15)")
    ap.add_argument("--max-bad", type=int, default=3, help="dừng khi có chừng này lô sai định dạng")
    ap.add_argument("--label", default="", help="tên hệ thống ghi vào kết quả")
    args = ap.parse_args()

    cfg = load_config()
    setup_logging(cfg)
    run_dir = get_run_dir()
    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    cases = {c["idx"]: c for c in subset["cases"]}
    preds = [json.loads(l) for l in (ROOT / args.run / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
    preds = [p for p in preds if p["id"] in cases and p.get("has_gold")]
    if args.sample:
        keep = set(pick_sample(list(cases.values()), args.sample, args.seed))
        preds = [p for p in preds if p["id"] in keep]
    if args.ids_file:
        keep_ids = set(json.loads(Path(args.ids_file).read_text(encoding="utf-8")))
        preds = [p for p in preds if p["id"] in keep_ids]
    if args.limit:
        preds = preds[: args.limit]
    store = QdrantStore.from_config(cfg, get_embedder(cfg), collection_for(cfg, args.subset))
    chunk_lock = threading.Lock()
    chunk_cache: dict[str, object] = {}

    def context(p: dict) -> list:
        ids = p["ranked_ids"][: args.top_k]
        with chunk_lock:
            missing = [i for i in ids if i not in chunk_cache]
        if missing:
            got = {c.chunk_id: c for c in store.get_chunks(missing)}
            with chunk_lock:
                chunk_cache.update(got)
        return [chunk_cache[i] for i in ids if i in chunk_cache]

    batches = [preds[i: i + args.batch] for i in range(0, len(preds), args.batch)]
    pacer, local, stop = Pacer(args.rpm), threading.local(), threading.Event()
    lock, rows, bad, state = threading.Lock(), [], [], {"stopped": None, "done": 0}

    def work(batch: list[dict]) -> None:
        if stop.is_set():
            return
        if not hasattr(local, "answerer"):
            local.cache = PacedCache(ROOT / "data" / "llm_cache" / "cache.sqlite", pacer)
            local.answerer = Answerer(get_llm(cfg, args.profile), version=args.prompt, cache=local.cache)
        ctxs = [context(p) for p in batch]
        questions = [cases[p["id"]]["question_hard"] for p in batch]
        try:
            out = local.answerer.answer(questions, ctxs)
        except LlmUnavailable as exc:
            logger.error("LLM chưa dùng được: %s", str(exc)[:150])
            with lock:
                state["stopped"] = state["stopped"] or "llm"
            stop.set()
            return
        if out is None:
            with lock:
                bad.append({"ids": [p["id"] for p in batch], "questions": questions})
                if len(bad) >= args.max_bad:
                    state["stopped"] = "format"
                    stop.set()
            return
        by_n = {a.n: a for a in out.answers}
        with lock:
            for k, (p, ctx) in enumerate(zip(batch, ctxs), 1):
                case, a = cases[p["id"]], by_n[k]
                golds = [str(t) for t in case["targets"]]
                ev = [ctx[e - 1].chunk_id for e in a.evidence if 0 < e <= len(ctx)]
                rows.append({"id": p["id"], "system": args.label or args.run, "prompt": args.prompt, "domain": case["domain"],
                             "question": case["question_hard"], "targets": golds, "answer": a.answer, "refused": is_refusal(a.answer),
                             "evidence": ev, "context_ids": [c.chunk_id for c in ctx],
                             "em": exact_match(a.answer, golds), "f1": f1_score(a.answer, golds), "contains": contains(a.answer, golds)})
            state["done"] += 1
            if state["done"] % 10 == 0:
                print(f"{state['done']}/{len(batches)} lô", flush=True)

    with ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(work, batches))

    rows.sort(key=lambda r: r["id"])
    (run_dir / "answers.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    if bad:
        (run_dir / "format_errors.jsonl").write_text("".join(json.dumps(b, ensure_ascii=False) + "\n" for b in bad), encoding="utf-8")
    n = len(rows)
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    answered = [r for r in rows if not r["refused"]]
    metrics = {"run": args.run, "label": args.label, "subset": args.subset, "prompt": args.prompt, "profile": args.profile, "batch": args.batch,
               "top_k": args.top_k, "n_questions": len(preds), "n_answered_rows": n, "em": mean([r["em"] for r in rows]),
               "f1": mean([r["f1"] for r in rows]), "contains": mean([r["contains"] for r in rows]),
               "refusal_rate": mean([float(r["refused"]) for r in rows]), "em_when_answered": mean([r["em"] for r in answered]),
               "wrong_rate": mean([float(not r["refused"] and r["contains"] == 0) for r in rows]), "bad_batches": len(bad),
               "per_domain_em": {d: mean([r["em"] for r in rows if r["domain"] == d]) for d in sorted({r["domain"] for r in rows})},
               "stopped": state["stopped"]}
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in metrics.items() if k != "per_domain_em"}, ensure_ascii=False))
    print(f"Ghi vào {run_dir}")
    if state["stopped"] == "format":
        print(f"DỪNG: {len(bad)} lô sai định dạng; xem {run_dir / 'format_errors.jsonl'} và log run.log", file=sys.stderr)
        sys.exit(3)
    if state["stopped"] == "llm" or n < len(preds):
        print(f"Chưa xong {len(preds) - n}/{len(preds)} câu; chạy lại để làm tiếp từ cache", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
