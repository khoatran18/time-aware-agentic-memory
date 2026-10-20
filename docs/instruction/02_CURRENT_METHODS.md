# Hiện có những phương pháp nào (tính đến 2026-10-19)

Bảng tra nhanh, dùng khi cần trả lời "đồ án đã có gì, chưa có gì". Cách chạy: [`01_RUN_PIPELINE.md`](01_RUN_PIPELINE.md). Lý do thiết kế: [`../decisions/`](../decisions/).

## Ingestion (tầng 1)

| | Trạng thái | Ở đâu |
|---|---|---|
| Chia chunk theo đoạn của dataset, header "Tên bài \| Tên mục", khử trùng bằng hash | **Có** (1 cách) | `src/tam/ingestion/chunking.py` |
| LLM gán `start`, `end`, `ongoing`, `domain` (tối đa 3 nhãn) kèm lý do; kiểm tra bằng chứng `ongoing` | **Có** | `time_extraction.py`, prompt `src/tam/llm/prompts/ingestion_time_v1.md` |
| Ghi Qdrant (dense + BM25, 4 chỉ mục payload) | **Có** (`VectorSink`) | `pipeline.py`, `src/tam/stores/vector/qdrant_store.py` |
| Chọn LLM, cache kết quả LLM | **Có** | `configs/config.dev.yaml` mục `llm.roles`; `src/tam/llm/cache.py` |
| Chunk không có `start` | Mặc định **bỏ**; `--keep-undated` giữ chunk có nội dung (nhãn domain khác rỗng) với `start_time` rỗng | [`decisions/04`](../decisions/04_UNDATED_CHUNKS.md) |
| Lưu `end_status` (known, ongoing, unknown) | **Đã code, chưa chạy thật** (cần nạp lại Qdrant, tức gọi lại LLM cho 37 trang vì cache lần 4 không còn: cache chỉ được thêm sau lần chạy đó) | [`decisions/02`](../decisions/02_END_TIME_ONGOING.md) |
| Ghi đồ thị (`GraphSink`, Neo4j) | Chưa | Cơ chế 2 và 3 |
| Mốc ở mức sự việc (không phải mức chunk) | Chưa | Cần đồ thị |

Điểm vào: `scripts/ingest.py`. Biến thể bằng tham số: `--dry-run` (không ghi Qdrant), `--recreate`, `--limit-pages`, `--no-cache`, `--refresh-cache`.

## Retrieval (tầng 3)

| | Trạng thái | Ở đâu |
|---|---|---|
| **Cơ chế 1** `TemporalRetriever`: dense + BM25, lọc cứng thời gian, RRF, `W1·Semantic + W2·Temporal` | **Có** (1 bộ truy xuất) | `src/tam/retrieval/temporal/` (`filters`, `scoring`, `fusion`, `retriever`); tham số trong `configs/*.yaml` mục `retrieval` |
| Lọc cứng theo `domain` (facet) | **Có**, chỉ dùng khi đo (`--facets domain`) | `filters.py` |
| Cộng điểm `domain` (`W3·Domain_Match`) | **Đã code, mặc định tắt** (`retrieval.w3 = 0`; `evaluate.py --facets boost --w3 0.1`) | [`decisions/01`](../decisions/01_DOMAIN_AS_SOFT_BOOST.md) |
| Cách chấm `end` A / B / C | **Đã code, mặc định C** (`retrieval.end_mode`: `open` = A, `decay` = B, `stored` = C; cần `end_status` trong kho) | [`decisions/02`](../decisions/02_END_TIME_ONGOING.md) |
| Mở rộng chunk liền kề (trước, sau) | **Đã code, mặc định tắt** (`retrieval.neighbor_window`; `evaluate.py --neighbors 1`). Kết quả ở `RetrievalResult.neighbors`, không xếp hạng, vẫn qua hard filter | `eval/01` mục 10 |
| Baseline plain RAG (`dense`, `bm25`, `hybrid`) | **Đã code** (`src/tam/retrieval/baseline.py`, `evaluate.py --method`) | `eval/03` đợt 1 |
| Số đo từng bước (ứng viên, lọc cứng, trước/sau điểm thời gian, Profiler) | **Đã code** (`src/tam/evaluation/funnel.py`, trong `metrics.json`) | `eval/03` đợt 2 |
| Nhánh chunk không mốc, `T_unknown` | **Đã code, mặc định tắt** (`ingest.py --keep-undated`, `retrieval.t_unknown`) | [`decisions/04`](../decisions/04_UNDATED_CHUNKS.md) |
| Metric câu cần nhiều chunk và ngữ cảnh | **Đã code**: `recall@k`, `multi_all_hit@k`, `multi_recall@k`, `ctx_hit`, `ctx_recall`, `ctx_multi_all_hit`, `ctx_size_mean`, `rescued_by_neighbors` | `src/tam/evaluation/metrics_temporal.py` |
| Điểm thời gian cho khoảng câu hỏi (`t_req_start`, giao khoảng) | Chưa | `process/05` mục 4 |
| Cơ chế 2 (Timeline), Cơ chế 3 (Conflict), router chọn cơ chế | Chưa | `docs/planning/00_OVERALL_PLAN.md` |

## Query và sinh đáp án

| | Trạng thái | Ở đâu |
|---|---|---|
| Profiler: câu hỏi và `T_now` → `semantic_query`, `t_req`, `filters` | **Có** | `src/tam/query/profiler.py`, prompt `time_extractor_v1.md`; scripts `profile_eval.py` |
| Sinh đáp án (Time-CoT), LangGraph, baseline plain RAG, EM/F1 | Chưa | `docs/planning/01` mục 5 |

## Đo và đánh giá

| | Trạng thái | Ở đâu |
|---|---|---|
| Dựng bộ câu hỏi, nhãn chunk đúng (bộ local 40 câu) | **Có** | `scripts/make_eval_subset.py`, `src/tam/evaluation/subset.py` |
| Hit@k, MRR, rò rỉ tương lai (chế độ `oracle` và `e2e`; bỏ điểm thời gian; lọc cứng domain) | **Có**: 1 bộ truy xuất, 5 cấu hình chạy | `scripts/evaluate.py`, `src/tam/evaluation/retrieval_eval.py` |
| Báo cáo ingestion và Profiler | **Có** | `scripts/ingestion_report.py`, `src/tam/evaluation/{ingestion,profiler}_report.py` |
| Bộ thật (400 câu, 8 domain × 50) | Chưa (quyết định tạm) | `docs/process/06_EVAL_SUBSET.md` |
| Tinh chỉnh `λ`, `W1/W2` trên `D/train` | Chưa | `docs/process/06_EVAL_SUBSET.md` |

Kết quả đo hiện có: [`../eval/`](../eval/).
