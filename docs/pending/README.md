# Việc đang dở, chờ chốt, sắp làm

Thư mục này giữ những thứ **chưa chốt hoặc chưa làm**. Quy tắc:
- Mỗi file một chủ đề, ghi rõ "chờ ai quyết gì" hoặc "sắp làm gì".
- Khi một mục đã chốt: chuyển sang `docs/decisions/` (nếu là quyết định thiết kế), hoặc `docs/eval/`, `docs/process/` (nếu là kết quả đo, nhật ký làm việc), rồi xóa hoặc đánh dấu "đã chuyển" ở đây.
- Số liệu ghi kèm nguồn; điều chưa kiểm chứng ghi "chưa kiểm chứng".

| File | Chủ đề | Trạng thái |
|---|---|---|
| [`01_QUESTION_PROMPT_V9.md`](01_QUESTION_PROMPT_V9.md) | Prompt sinh câu hỏi v9 (cho các session Haiku) và `check_questions.py` đi kèm | Prompt và checker v9 đã viết; cả 4 session đã chạy, 364 câu trên 100 trang (docs/eval/10 mục 10.5av, 10.5aw); chờ người dùng chốt v9 hay v8 làm bản chính; còn sửa `chain_apply.py` cho mốc có cờ, gộp `list`/`summary`, đo nhiễu |
| [`02_INGEST_AND_PRECISION.md`](02_INGEST_AND_PRECISION.md) | Ingest: định nghĩa `derived_date`, năm viết tắt, gộp mốc trùng, chọn model, precision | Chưa chốt |
| [`03_EVAL_AND_DATA_OPEN.md`](03_EVAL_AND_DATA_OPEN.md) | Chấm `list`/`summary`, tỷ lệ loại câu, valid/test, soát gold, `extras`, ranh giới với Cơ chế 3 | Chưa chốt |
| [`04_QUESTION_AUDIT_STEP4.md`](04_QUESTION_AUDIT_STEP4.md) | Bước [4]: giám khảo LLM kiểm câu hỏi (thay đọc mù), kiểm cùng loại với `criterion` | Đã viết bản thử và chạy trên v8/v9/v8n (docs/eval/10 mục 10.5aw); bắt ít lỗi tinh, dùng làm bộ lọc sơ bộ; chờ người dùng quyết hướng tiếp |

Các quyết định đã chốt liên quan: `docs/decisions/13_QUESTION_GENERATION_V8.md`, `docs/decisions/14_CHAIN_CHECK_AND_FLAGS.md`. Kết quả đo: `docs/eval/10_TIMELINE_DATASET_DESIGN.md` (10.5ar đến 10.5aw).
