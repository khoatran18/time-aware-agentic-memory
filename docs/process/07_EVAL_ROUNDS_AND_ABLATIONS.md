# Nhật ký triển khai 07: đánh giá theo đợt, các thành phần so sánh và bộ thật

Tiếp nối [`06_EVAL_SUBSET.md`](06_EVAL_SUBSET.md). Giai đoạn 2026-10-19: code các thành phần để so sánh (baseline, chấm `end`, chunk không mốc, chunk liền kề, trọng số RRF), chạy đợt test trên bộ local và dựng bộ thật. Kế hoạch: [`../eval/03_TEST_ROUNDS.md`](../eval/03_TEST_ROUNDS.md); kết quả local: [`../eval/04_TEST_RESULTS.md`](../eval/04_TEST_RESULTS.md); kết quả bộ thật (142 kịch bản, 2026-10-20): [`../eval/05_REAL_RESULTS.md`](../eval/05_REAL_RESULTS.md).

## Đã làm

| Nhóm | File | Việc |
|---|---|---|
| Chấm điểm và truy xuất | `retrieval/temporal/scoring.py`, `retriever.py` | `end_mode` (`stored`/`open`/`decay`/`unknown_decay`), `W3·Domain_Match`, nhánh chunk không mốc (`t_unknown`), `neighbor_window`, `sparse_weight` |
| | `retrieval/temporal/fusion.py` | RRF có trọng số từng nhánh (`weights`); `sparse_weight = 0` bỏ hẳn BM25 |
| | `retrieval/baseline.py` | `PlainRetriever`: dense, BM25, hybrid, không lọc thời gian (baseline plain RAG) |
| | `retrieval/temporal/expansion.py`, `stores/vector/*` | Lấy chunk liền kề (`get_chunks`), điều kiện `IsNull(start_time)` |
| Ingestion | `ingestion/time_extraction.py`, `pipeline.py` | `end_status`, `--keep-undated`, bỏ chunk trước Công nguyên |
| LLM | `llm/structured.py`, `llm/cache.py` | Chờ 1 đến 32 giây khi LLM lỗi tạm thời; cache SQLite (nguồn sự thật) cộng JSON (xem nhanh) |
| Profiler | `query/profiler.py`, `prompts/time_extractor_v1.md` | Trường `use_t_now`: câu phụ thuộc "bây giờ" không cache; khóa cache không chứa ngày; `profiler.jsonl` ghi thêm `t_now` |
| Đánh giá | `evaluation/funnel.py`, `metrics_temporal.py` | Số đo từng bước (ứng viên, lọc, điểm thời gian, Profiler), multi-gold, ngữ cảnh chunk liền kề |
| | `scripts/evaluate.py` | Cờ `--method`, `--t-unknown`, `--w3`, `--end-mode`, `--open-decay`, `--neighbors`, `--sparse-weight`, `--facets`, `--collection` |
| | `scripts/summarize_runs.py`, `scripts/plot_results.py`, `dataset/eval/results_local.csv`, `docs/eval/figures/*.svg` | Gom `metrics.json` nhiều lần chạy thành bảng xếp hạng (CSV + markdown) và vẽ biểu đồ SVG (cột ngang xếp hạng, bảng màu và đường theo `t_unknown`), không cần thư viện vẽ |
| Bộ thật | `evaluation/subset.py`, `scripts/make_eval_subset.py`, `dataset/eval/real_subset.json` | 8 domain × 50 câu, mượn 35 câu từ `D/train`, bỏ câu trước Công nguyên và câu không xác định đáp án; kho riêng `<tên>_real` |

## Quyết định ghi riêng

[`decisions/02`](../decisions/02_END_TIME_ONGOING.md) (chấm `end`), [`04`](../decisions/04_UNDATED_CHUNKS.md) (chunk không mốc), [`05`](../decisions/05_EXCLUDE_BEFORE_COMMON_ERA.md) (bỏ trước Công nguyên), [`06`](../decisions/06_END_UNKNOWN_REMEDIES.md) (đề xuất sửa `end` unknown, chưa quyết).

## Điều rút ra khi chạy

- 9router: combo `basic-gemini-3.1-flash-lite` bị Gemini trả 503 "high demand"; đổi sang `basic-gemini-3.5-flash-lite` thì chạy ổn. Một lần nạp kho có yêu cầu LLM treo ở 0% CPU, không có cảnh báo; chưa có timeout riêng cho lệnh gọi.
- Lệnh `evaluate.py` mất vài giây (không phải 1 phút như ước tính ban đầu), nên quét tham số rẻ; nút thắt luôn là lệnh gọi LLM của Profiler và ingestion.
- Quét nhiều cấu hình trên 40 câu: cấu hình đứng đầu bị đánh giá cao (chọn lọc); chỉ coi là cận trên.

## Chưa làm

- Bộ thật: Profiler (`profile_eval.py --subset real`) và nạp kho (`ingest.py --subset real`) chưa chạy; đợt 7.
- Đợt 6: quét `λ`, `W1/W2` trên mẫu `D/train` (chưa có code lấy mẫu); nhớ loại 35 câu mượn.
- Đề xuất 2 đến 5 ở [`decisions/06`](../decisions/06_END_UNKNOWN_REMEDIES.md) (LLM ghi loại sự việc, một chunk nhiều khoảng, reranker): chưa làm. Đề xuất 1 (tách `ongoing`/`unknown`, `end_mode: unknown_decay`) đã code và đo (`eval/04` đợt 3d).
- Chưa đổi mặc định trong `config.*.yaml` theo kết quả local (`sparse_weight` 0, `t_unknown` 0.2, `neighbor_window` 1). Bộ thật ([`05`](../eval/05_REAL_RESULTS.md)) xác nhận `sparse_weight` 0 và `t_unknown` 0.1; `unknown_decay` không hơn `stored`. Chờ bạn chốt rồi mới đổi.
