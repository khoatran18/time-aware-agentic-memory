# Nhật ký triển khai 08: Gemini gọi thẳng, Profiler khoảng, chế độ khoảng và chỉ số chuỗi đáp án

Tiếp nối [`07_EVAL_ROUNDS_AND_ABLATIONS.md`](07_EVAL_ROUNDS_AND_ABLATIONS.md). Giai đoạn 2026-10-20: nạp kho và chạy Profiler cho bộ thật, đo toàn bộ kịch bản trên bộ thật ([`eval/05`](../eval/05_REAL_RESULTS.md)), rồi code các đề xuất rút ra từ lỗi ([`decisions/07`](../decisions/07_RANKING_AND_TIME_RANGE_PROPOSALS.md)). Mọi thứ mới đều là **tùy chọn, mặc định giữ nguyên hành vi cũ**.

## Đã làm

| Nhóm | File | Việc |
|---|---|---|
| LLM | `llm/providers/google.py`, `llm/factory.py`, `configs/config.*.yaml` | Provider `google`: Gemini gọi thẳng API Google (structured output do Google ép khuôn). Profile `google_35`, `google_31`, `9router_31`. Khóa `cache_model` (dùng lại cache của profile khác cùng model) và `structured_output: false` (bỏ bước structured output, đi thẳng đường văn bản) |
| | `llm/structured.py` | Lỗi giới hạn tốc độ của langchain-google-genai (không có `status_code`) được nhận là lỗi tạm thời nên chờ rồi thử lại, thay vì dừng cả lượt |
| Prompt | `llm/prompts/*_v1.md`, `time_extractor_v2.md` | Prompt có phiên bản; sửa nội dung thì tạo `_v<N+1>`, giữ bản cũ (quy ước ở [`decisions/03`](../decisions/03_PROMPT_CHANGELOG.md)). `PROMPT_VERSION` cạnh `PROMPT_PATH`; `profile_eval.py` ghi `prompt_version` vào từng dòng |
| Profiler khoảng | `query/time_range.py`, `query/range_profiler.py`, `schemas/query.py` (`t_end`), `scripts/profile_eval.py --ranges` | LLM chỉ ghi mốc một phần (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`) cùng `bound` (`exact`/`after`/`before`/`none`); **code** mở rộng thành `[ngày đầu, ngày cuối]`; "after X" thì `[X, T_now]`, "before X" mặc định `[X, X]` (`--before-lower min` mở cận dưới). `Profiler` cũ giữ nguyên |
| Truy xuất | `retrieval/temporal/scoring.py` (`temporal_score_range`, `decay_from`), `filters.py` (`use_range`), `retriever.py` | `retrieval.time_mode: point \| range` (range: lọc `start <= qe`, điểm chồng lấn); `retrieval.overlap: binary \| coverage`; `retrieval.decay_from: start \| end` (phạt chunk đã hết hạn từ `start` hay `end`) |
| Đánh giá | `evaluation/answer_match.py`, `metrics_temporal.py`, `retrieval_eval.py` | `ans_hit@k` (top-k chứa chuỗi đáp án) và `ans_valid_hit@k` (chunk chứa chuỗi đáp án **và** hợp lệ tại `t_req` hoặc giao khoảng hỏi); `hit@k` theo chunk id giữ nguyên |
| | `scripts/evaluate.py` | Cờ `--decay-from`, `--time-mode`, `--overlap` |
| | `scripts/summarize_runs.py`, `plot_results.py`, `funnel_real.py` | Thêm cột `ans_hit@5`, `ans_valid_hit@5`; biểu đồ `compare_mrr.svg`, `compare_hit5.svg`, `funnel.svg`; phân loại câu theo chỗ rớt của chunk đúng (`dataset/eval/real_funnel.csv`) |
| Dữ liệu | `dataset/eval/*.csv` | Danh sách câu local/real, câu bị loại, kết quả local/real, so sánh hai bộ, `decay_from=end` |
| Công cụ | `.claude/skills/handoff/SKILL.md` | Skill ghi bàn giao vào `local/handoff/HANDOFF_<ngày>_<giờphút>.md` |

## Kiểm tra

- `pytest`: 196 pass, 4 xfailed; `ruff` sạch. Test mới: `test_answer_match.py`, `test_time_range.py`, thêm vào `test_scoring.py`, `test_temporal_retriever.py`, `test_llm_cache.py`, `test_llm_factory.py`.
- Chạy lại 204 cấu hình mỗi bộ để có cột chuỗi đáp án: bộ thật 170/170 `hit@5` và `mrr` giống hệt lần đầu; bộ local 161/170 giống, 9 cấu hình lệch tối đa 0.005 `mrr` (BM25 0.5 và một hybrid decay 0.05; chưa tìm nguyên nhân, nghi do hòa điểm).
- Lưới 140 kịch bản mỗi bộ cho chế độ khoảng (`eval/05` mục 6.9): `range` so với `point` +0.002 ± 0.014 `mrr` (giảm số câu bị lọc cứng 78 xuống 68), độ phủ kém nhị phân, `decay_from end` +0.006; không vượt sai số ở 400 câu.
- Profiler khoảng chạy 400/400 câu bộ thật, 0 lỗi; khoảng mới giao khoảng nhãn dữ liệu ở 395/400 câu (điểm cũ: 390/400); 2 câu hỏng do "late 1900s" (ghi ở `decisions/03`, dự kiến prompt v3).

## Quyết định ghi riêng

[`decisions/07`](../decisions/07_RANKING_AND_TIME_RANGE_PROPOSALS.md) (8 đề xuất, bảng trạng thái code), [`08`](../decisions/08_TRAIN_VALID_TEST_SPLIT.md) (kế hoạch chia train/valid/test, chưa làm), [`03`](../decisions/03_PROMPT_CHANGELOG.md) (phiên bản prompt).

## Điều rút ra khi chạy

- 9router/Gemini bỏ qua yêu cầu structured output ở request đầu (200 OK nhưng trả danh sách markdown, không phải JSON), nên mỗi lô tốn 2 request. Gọi thẳng Google thì chỉ 1 request mỗi lô.
- Hạn mức Gemini miễn phí: 500 request/ngày mỗi model và 15 request/phút; lỗi 429 của ngày và của phút khác nhau (`GenerateRequestsPerDayPerProjectPerModel` và `...PerMinute...`), reset 14:00 giờ VN.
- Google chặn một trang (`Young_Girl_with_a_Flower_Basket`, `block_reason` là `PROHIBITED_CONTENT`) ở mọi lần gọi; câu hỏi của trang đó đã được thay.
- `evaluate.py` mất khoảng 10 giây mỗi lần chạy (chạy 4 song song); nút thắt vẫn là lệnh gọi LLM.
- Lệnh chạy nền dạng `( ... &)` không phát thông báo khi xong: dùng `run_in_background`. `pkill -f` với chuỗi có trong lệnh của chính shell sẽ giết shell.

## Chưa làm

- Prompt `time_extractor_v3` (quy tắc chung cho thập niên và thế kỷ).
- Đề xuất 4 (cross-encoder), 7 (gom chunk cùng trang theo thời gian), 8 (một chunk nhiều khoảng), đợt 6 (quét `λ`, `W1/W2`) và chia train/valid/test.
- Chưa đổi mặc định trong `config.*.yaml`; chưa đổi tên `t_unknown`.
