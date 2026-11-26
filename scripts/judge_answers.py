"""Chấm lại câu trả lời bằng LLM judge (schema có lý do). Chạy thử: python scripts/judge_answers.py --run <thư mục có answers.jsonl> --ids-file ids.json --profile opencode_glm_5_3 --cache-dir data/llm_cache/judge_glm_try
Mỗi câu một lần gọi; cache riêng; ghi judgments.jsonl vào thư mục output của lần chạy (kèm số đo của llm_calls.jsonl)."""
from __future__ import annotations
import argparse, json, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from tam.config.loader import Config, load_config
from tam.config.logging import get_logger, get_run_dir, setup_logging
from tam.embedding.factory import get_embedder
from tam.llm.cache import SqliteCache
from tam.llm.factory import get_llm
from tam.llm.prompt_files import prompt_path
from tam.llm.structured import LlmUnavailable, invoke_structured
from tam.stores.vector.qdrant_store import QdrantStore, collection_for
logger = get_logger(__name__)


class Judgment(BaseModel):
    reason: str = Field(description="1-2 sentences: which passage or gold answer you relied on and why the verdict follows.")
    verdict: Literal["correct", "partial", "wrong", "refusal"]
    match_type: Literal["same", "format_variant", "alternate_valid", "subset", "superset", "different", "none"]
    gold_in_passages: bool
    relevant_passages: list[int]
    matches_gold: bool
    grounded: bool
    hallucinated: bool
    answer_relevant: bool
    completeness: Literal["complete", "incomplete", "not_applicable"]
    refusal_quality: Literal["not_refusal", "justified", "borderline", "unjustified"]
    citation_support: Literal["true", "false", "none"]
    label_issue: Literal["none", "multi_gold", "ambiguous", "gold_not_an_answer", "time_mismatch"]


import re, unicodedata
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def answer_in_passages(answer: str, passages: list[str]) -> bool:
    a = _norm(answer)
    return bool(a) and any(a in _norm(p) for p in passages)


_CH = re.compile(r"(?:^|\n\n)(?:\d+\. )?(/wiki/\S+#\d+) \(([^)]*)\) ")


_RP = re.compile(r"(?:^|\n\n)\[#(\d+)\] ")  # kết quả read_page: "[#idx] Tiêu đề | Mục\nnội dung"
_GR = re.compile(r"(?m)^(\S+) \[#(\d+)\] \((\d+) lần\): (.*)$")  # kết quả grep: "Trang [#idx] (n lần): trích đoạn"
_CUT = re.compile(r"\n*\(đã cắt theo giới hạn[^)]*\)\s*$")


def agent_passages(tool_texts_raw, answer_text: str, cap: int = 20, extended: bool = False) -> tuple[list[str], list[int]]:
    """Đoạn văn mà agent đã thấy (theo thứ tự thấy lần đầu, tối đa `cap`) và số thứ tự các đoạn được nêu trong câu trả lời.

    `extended=False`: chỉ đoạn dạng vector_search/read_chunk (`/wiki/...#id (thời kỳ) văn bản`), như các lần chấm cũ của A2/A4.
    `extended=True` (agent kind A, C có grep/read_page): thêm đoạn đọc bằng `read_page` (không có thời kỳ, nội dung nguyên đoạn) và trích đoạn của `grep`
    (chỉ khi chưa có bản đầy đủ của cùng đoạn); khóa gộp `/wiki/<trang>#<idx>`, ưu tiên vector > read_page > grep."""
    texts = tool_texts_raw if isinstance(tool_texts_raw, list) else json.loads(tool_texts_raw)
    seen: dict[str, str] = {}
    for _, txt in texts:
        ms = list(_CH.finditer(txt))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(txt)
            seen.setdefault(m.group(1), f"({m.group(2)}) " + txt[m.end():end].strip())
    if extended:
        for _, txt in texts:
            ms = list(_RP.finditer(txt))
            for i, m in enumerate(ms):
                end = ms[i + 1].start() if i + 1 < len(ms) else len(txt)
                body = _CUT.sub("", txt[m.end():end]).strip()
                head = body.split("\n", 1)[0]
                page = head.split(" | ", 1)[0].replace(" ", "_") if " | " in head else None
                seen.setdefault(f"/wiki/{page}#{m.group(1)}" if page else f"?#{m.group(1)}:{hash(body) % 10**6}", body)
        for _, txt in texts:
            for m in _GR.finditer(txt):
                seen.setdefault(f"/wiki/{m.group(1)}#{m.group(2)}", "(grep snippet) " + m.group(4).strip())
    ids = list(seen)
    pages = {c.rsplit("#", 1)[0] for c in ids}

    def is_cited(c: str) -> bool:
        if c in (answer_text or ""): return True
        if not extended: return False
        page, idx = c.rsplit("#", 1)[0], c.rsplit("#", 1)[1].split(":")[0]
        return f"[#{idx}]" in (answer_text or "") and (page.removeprefix("/wiki/") in (answer_text or "") or len(pages) == 1)
    cited_ids = [c for c in ids if is_cited(c)]
    keep = list(dict.fromkeys(cited_ids + ids))[:cap]
    keep = [c for c in ids if c in set(keep)]
    return [seen[c] for c in keep], [keep.index(c) + 1 for c in cited_ids if c in keep]


def user_message(question: str, golds: list[str], answer: str, passages: list[str], cited: list[int]) -> str:
    ps = "\n".join(f"[{i}] {p}" for i, p in enumerate(passages, 1))
    return f"Question: {question}\nGold answers: {json.dumps(golds, ensure_ascii=False)}\nPassages the system had:\n{ps}\nSystem cited passages: {cited if cited else 'none'}\nSystem answer: {answer if (answer or '').strip() else '(none: the system refused)'}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="thư mục có answers.jsonl (đầu ra generate_answers.py)")
    ap.add_argument("--subset", default="tune100"); ap.add_argument("--collection", default="tam_chunks_dev_tune")
    ap.add_argument("--ids-file", default=""); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--profile", default="opencode_glm_5_3"); ap.add_argument("--prompt", default="judge_m1")
    ap.add_argument("--workers", type=int, default=4); ap.add_argument("--cache-dir", required=True)
    a = ap.parse_args()
    cfg = load_config(); setup_logging(cfg); run_dir = get_run_dir()
    prof = cfg.llm.profiles[a.profile]; llm_cfg = cfg
    if prof.get("session_header"):
        data = cfg.to_dict(masked=False); data["llm"]["profiles"][a.profile].setdefault("default_headers", {})[prof["session_header"]] = f"{run_dir.name}-judge"; llm_cfg = Config(data)
    llm = get_llm(llm_cfg, a.profile); chain = llm.with_structured_output(Judgment)
    system = prompt_path(a.prompt).read_text(encoding="utf-8")
    cache = SqliteCache(Path(a.cache_dir) / "cache.sqlite", threadsafe=True)
    run = ROOT / a.run
    if (run / "answers.jsonl").exists():
        rows = [json.loads(l) for l in (run / "answers.jsonl").read_text(encoding="utf-8").splitlines()]
    else:  # đầu ra của run_agent_search.py
        from score_agent_runs import REFUSAL, answer_line
        tt = {}
        for l in (run / "tool_texts.jsonl").read_text(encoding="utf-8").splitlines():
            o = json.loads(l); tt[o["idx"]] = o["tool_texts"]
        rows = []; kind = json.load(open(run / "run_meta.json")).get("kind")
        for r in map(json.loads, (run / "results.jsonl").read_text(encoding="utf-8").splitlines()):
            ps, cited = agent_passages(tt.get(r["idx"], "[]"), r["answer"] or "", extended=kind in ("A", "C"))
            al = answer_line(r["answer"] or "")
            refused = bool(REFUSAL.search(al)) or not al.strip()
            rows.append({"id": r["idx"], "system": json.load(open(run / "run_meta.json")).get("kind"), "question": r["question"], "targets": r["targets"],
                         "answer": None if refused else al, "em": None, "_passages": ps, "_cited": cited})
    if a.ids_file: keep = set(json.loads(Path(a.ids_file).read_text())); rows = [r for r in rows if r["id"] in keep]
    if a.limit: rows = rows[: a.limit]
    store = QdrantStore.from_config(cfg, get_embedder(cfg), collection_for(cfg, a.subset, a.collection))
    out, lock = [], threading.Lock()

    def work(r: dict) -> None:
        if "_passages" in r: passages, cited = r["_passages"], r["_cited"]
        else:
            chunks = {c.chunk_id: c for c in store.get_chunks(r["context_ids"])}
            ids = [i for i in r["context_ids"] if i in chunks]
            passages = [chunks[i].text.strip() for i in ids]
            cited = [ids.index(e) + 1 for e in (r.get("evidence") or []) if e in ids]
        t0 = time.perf_counter()
        try:
            j = invoke_structured(llm, chain, Judgment, [("system", system), ("human", user_message(r["question"], r["targets"], r["answer"], passages, cited))], max_attempts=3, cache=cache)
        except LlmUnavailable as exc:
            logger.error("judge lỗi %s: %s", r["id"], exc); return
        with lock: out.append({"id": r["id"], "system": r.get("system"), "question": r["question"], "targets": r["targets"], "answer": r["answer"], "em": r.get("em"),
                               "answer_in_passages": answer_in_passages(r["answer"], passages), "n_passages": len(passages), "cited": cited, "judgment": j.model_dump() if j else None, "wall_s": round(time.perf_counter() - t0, 2)})
    with ThreadPoolExecutor(a.workers) as ex: list(ex.map(work, rows))
    (run_dir / "judgments.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")
    print(f"Ghi vào {run_dir}")


if __name__ == "__main__":
    main()
