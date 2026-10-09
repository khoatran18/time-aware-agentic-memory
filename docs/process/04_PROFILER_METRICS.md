# Nhật ký triển khai 04: Profiler (Time Extractor) và metric retrieval Cơ chế 1

Tiếp nối [`03_TEMPORAL_RETRIEVAL_CORE.md`](03_TEMPORAL_RETRIEVAL_CORE.md) mục 5, việc 2 và 3. Kế hoạch: [`../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md`](../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md) mục 5, bước 3. Thiết kế: [`../design/02_TEMPORAL_RETRIEVAL_DESIGN.md`](../design/02_TEMPORAL_RETRIEVAL_DESIGN.md) mục 3.2. **Chưa có** ingestion, generation, pipeline, baseline.

---

## 1. Đã làm được

| Hạng mục | File | Ghi chú |
|---|---|---|
| Profiler | `src/tam/query/profiler.py` | `Profiler(llm).profile(question, t_now) -> ProfiledQuery` |
| Prompt | `src/tam/llm/prompts/time_extractor.md` | Tiếng Anh, few-shot 8 ví dụ, có chỗ `{t_now}` |
| Metric CC1 | `src/tam/evaluation/metrics_temporal.py` | Hit@k, MRR, leakage, invalidated, forbidden |
| Test | `tests/test_profiler.py`, `tests/test_metrics_temporal.py` | 18 test mới; toàn bộ: 96 xanh, 4 xfail cũ |

## 2. Profiler

### 2.1 Luồng một lần `profile(question, t_now)`

1. Đọc `time_extractor.md`, thay `{t_now}` bằng `t_now.date().isoformat()`, gửi làm system message. Câu hỏi là human message.
2. LLM trả structured output `Extraction` (`llm.with_structured_output(Extraction)`): `semantic_query`, `t_req` (chuỗi ISO hoặc `null`), `domain`, `country`.
3. Chuẩn hóa trong code (không tin hoàn toàn vào LLM):
   - `t_req` đọc bằng `dateutil.isoparse`, chấp nhận `2020`, `2020-03`, `2020-03-01`, có hoặc không giờ; quy về UTC. Không đọc được thì ném `ValueError` kèm câu hỏi.
   - `t_req = null` (câu hỏi không nhắc thời gian) thì dùng `T_now`.
   - `t_req > T_now` chỉ cảnh báo log, vẫn cho qua.
   - `domain` viết thường, `country` viết hoa, chuỗi rỗng bỏ. Chỉ còn hai khóa nằm trong `FACET_KEYS` (khớp payload index).
   - `semantic_query` rỗng thì quay về nguyên câu hỏi.
4. Trả `ProfiledQuery(mechanism="temporal")`.

### 2.2 Quyết định thiết kế

- **LLM và đồng hồ được tiêm vào**: `Profiler.__init__(llm)` và tham số `t_now`. Không đọc đồng hồ hay biến môi trường bên trong, nên test bằng đồng hồ giả và LLM giả.
- **`T_now` đi qua placeholder `{t_now}` trong file `.md`**, thay bằng `str.replace` (không dùng `format`, vì prompt có thể chứa dấu ngoặc nhọn).
- **Prompt tiếng Anh**: dataset (TimeQA) là tiếng Anh nên câu hỏi là tiếng Anh; prompt và mô tả field của `Extraction` cũng tiếng Anh vì LLM đọc cả schema. Prompt dặn không dịch và không đổi ngôn ngữ câu hỏi.
- **Few-shot nằm trong system prompt**, không dùng lượt hội thoại giả: với structured output (tool calling) lượt giả của AI phải kèm tool-call, rất rườm rà. Mọi ví dụ cùng `T_now = 2023-10-10`; ngày đã tính tay (vd "last week" = 2023-10-03).
- **Quy ước khoảng thời gian**: lấy mốc cuối khoảng ("during the 1990s" -> `1999-01-01`), vì `t_req` là một điểm.
- **`domain`, `country` chỉ điền khi câu hỏi nêu rõ**: đoán sai sẽ làm filter lọc mất đáp án đúng (kết quả rỗng), tệ hơn là không lọc.
- **Làm sạch `semantic_query` ngay trong lần gọi này** (bỏ từ đệm, sửa lỗi gõ, giữ tên riêng), để nhánh BM25 không bị nhiễu. Xem 03 mục 2b về BM25.
- Dùng role `time_extractor` trong config (hiện `claude_haiku`); chỗ lắp ráp mới được gọi `get_llm_for_role`.

### 2.3 Test (`tests/test_profiler.py`)

LLM giả (`FakeLLM.with_structured_output`) ghi lại message nhận được. Phủ: `T_now` vào system prompt; quy đổi tương đối thành tuyệt đối UTC; `parse_t_req` (chỉ năm, năm-tháng, trước 1970, có múi giờ); không nhắc thời gian thì `T_now`; chuẩn hóa filter; đầu ra dạng dict; `semantic_query` rỗng; `t_req` rác ném lỗi; `t_req` tương lai chỉ cảnh báo.

## 3. Metric retrieval Cơ chế 1

`evaluation/metrics_temporal.py`, không gọi LLM. Nhãn ở mức `chunk_id`.

| Metric | Định nghĩa | Kỳ vọng |
|---|---|---|
| `hit@k` | Có chunk đúng trong top-k (k = 1, 3, 5) | cao |
| `mrr` | Trung bình 1/hạng của chunk đúng đầu tiên | cao |
| `leakage_rate` | Tỉ lệ câu hỏi có ít nhất một chunk với `start_time > t_req` | 0% |
| `invalidated_rate` | Tỉ lệ câu hỏi có chunk đã `invalidated_at` | 0% |
| `forbidden_rate` | Tỉ lệ câu hỏi có chunk thuộc `expect_absent` (tương lai, tin giả, sai facet) | 0% |

- `EvalCase(id, query, t_req, gold_ids, forbidden_ids, filters)`; `cases_from_corpus` đổi `cases` của `temporal_corpus.json`.
- `evaluate_retrieval(retriever, cases, ks)` chạy **chế độ oracle `t_req`** (bỏ qua profiler, xem planning mục 6.3), trả `{"summary", "cases"}` để ghi `metrics.json` / `predictions.jsonl`.
- Case không có đáp án hợp lệ (vd `t_req` trước mọi phiên bản) bị loại khỏi Hit@k/MRR nhưng vẫn tính vào ba tỉ lệ vi phạm. Không có case thì giá trị là `None`.
- Test bất biến: trên 11 case corpus với kho giả, ba tỉ lệ vi phạm bằng 0%, kể cả 4 case min-max đang xfail (xfail chỉ là top-1 sai, không phải rò rỉ).

### Tên file và Cơ chế 2/3

Đổi `metrics.py` thành `metrics_temporal.py` để mỗi cơ chế một file: `metrics_timeline.py` (coverage, thứ tự thời gian, token efficiency, Boomerang) và `metrics_conflict.py` (Evolution vs Falsehood, Temporal Freshness, chọn đúng nguồn) thêm sau, không sửa file này. Hàm dùng chung (`hit_at_k`, `is_future_leak`, `is_invalidated`) hiện còn nằm trong `metrics_temporal.py`; khi bắt đầu CC2 sẽ tách phần dùng chung ra `metrics.py`.

## 4. Đã kiểm chứng và chưa

- Đã: logic profiler và metric bằng LLM giả, kho giả; ba tỉ lệ vi phạm bằng 0% trên corpus.
- **Chưa:** chạy profiler với LLM thật (chưa biết Haiku quy đổi "last week", "last year", khoảng thời gian có đúng không); metric trên Qdrant thật và TimeQA; chưa có `metrics.json` ghi ra `output/`.

## 5. Việc tiếp theo

1. Script chạy thử profiler với LLM thật trên khoảng 15 câu (cần key), so `t_req` với kỳ vọng; sửa few-shot nếu sai.
2. Ingestion TimeQA bộ local: loader, chunking + content hash, `time_extraction` (prompt `ingestion_time.md`).
3. `generation/time_cot.py` (đưa `start_time`/`end_time` của chunk vào context), rồi LangGraph nấc A.
4. `baselines/plain_rag.py`, `runner`, EM/F1; chạy bộ local.
