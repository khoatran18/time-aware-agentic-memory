# Nhật ký triển khai 06: Dựng bộ câu hỏi local và nhãn chunk đúng

Tiếp nối [`05_TIME_SEMANTICS_AND_CHUNKING.md`](05_TIME_SEMANTICS_AND_CHUNKING.md) mục 2.4 và `dataset/full_dataset/EVAL_PLAN.md`. Không gọi LLM.

## Đã làm

| File | Việc |
|---|---|
| `src/tam/evaluation/subset.py` | `sample_cases` (lấy mẫu theo chủ đề, seed cố định), `paragraph_spans`, `gold_paragraph_indices`, `build_subset` |
| `scripts/make_eval_subset.py` | `python scripts/make_eval_subset.py --subset local` (hoặc `real`), mặc định seed 42 |
| `dataset/eval/local_subset.json` | Kết quả: 40 câu (80 dòng easy + hard), 37 trang, có `domain` và `gold_chunk_ids` |
| `tests/test_eval_subset.py` | Ánh xạ đáp án sang đoạn, tính tất định của lấy mẫu |

## Cách làm

1. Đọc `D/test.hard.jsonl`; mỗi **domain** trong 8 domain (business, sports, career, person, politics, place, media_arts, military; bỏ `other` vì cả `D/test` chỉ có 5 câu) lấy 5 câu bằng `random.Random(seed)`; domain suy từ `relation` qua `RELATION_DOMAIN` (`schemas/domains.py`, theo `TOPICS.md`). Bộ thật vẫn chia theo relation sau khi sắp theo `idx`. Câu `easy` lấy theo cùng `idx` và lưu kèm.
2. Trang cần nạp = tập `page_id` của các câu (truyền vào `load_pages(page_ids)`).
3. Nhãn: tìm tuần tự từng đoạn trong `context`, rồi đối chiếu `from`/`end` (vị trí ký tự trong `context`) với đoạn. `gold_chunk_ids = "<page_id>#<chỉ số đoạn>"`, cùng quy tắc với `chunk_document`.
   **Chỉ dùng `from`/`end` cấp ngoài** của mỗi dòng trong `D/test.*.jsonl` (cùng cấp với `question`): đó là vị trí ký tự trong `context` của trang (`pages.jsonl`), khớp `context[from:end] == target` ở 887/887 đáp án. **Không dùng** `answers[].para/from/end` lồng bên trong: đối chiếu với `paragraphs` thì sai 861/887, chưa rõ `para` đánh số theo cách nào.
4. Đổi vị trí ký tự thành chỉ số đoạn: đoạn nào giao với `[from, end)` thì lấy. Đáp án trúng khe giữa hai đoạn (tiêu đề mục) thì lấy đoạn kế tiếp.

### Thống kê trên cả `D/test.hard` (830 câu)

| Trường hợp | Số câu |
|---|---:|
| Đáp án nằm ở tiêu đề mục (lấy đoạn kế tiếp) | 41 |
| Đáp án **vắt qua 2 đoạn** (`answer_spans_paragraphs`) | 2: `John_Campbell_Brown#P108#1` (đoạn 5, 6), `Vuk_Drašković#P102#1` (đoạn 10, 11) |
| Có từ 2 chunk đúng (gồm hai câu vắt đoạn ở trên và các câu có nhiều đáp án) | 28 |
| Không xác định được (`unmapped`) | 2 |

Bộ local seed 42 không dính hai câu vắt đoạn.

## Kết quả (seed 42)

- 40 câu (8 domain × 5), **37 trang**; 1 câu có nhiều chunk đúng; 1 câu đáp án nằm ở tiêu đề mục (cờ `answer_in_heading`, lấy đoạn kế tiếp). Kế hoạch ban đầu là 25 câu / 21 trang theo 5 relation, đã đổi sang chia theo domain để kiểm chứng đủ 8 nhãn.
- Kiểm tra: mọi chunk đúng đều chứa nguyên văn `targets` của câu.

## Ingestion bộ local: `scripts/ingest.py`

`python scripts/ingest.py --dry-run [--limit-pages N]` chỉ gọi LLM (role `ingestion_time`, hiện là 9router/`basic-llm`) và ghi `output/<timestamp>/extractions.jsonl`: mỗi chunk một dòng gồm `start`, `end`, `ongoing`, `skipped`, `reason_end_date`, `text`. Bỏ `--dry-run` thì ghi thêm vào Qdrant (`--recreate` để tạo lại collection). Để ghi vết, `IngestionPipeline` có thêm tham số `on_result` và `TimeResult` có thêm `ongoing`, `note` (không đổi schema kho).

**Domain:** cùng lệnh gọi LLM còn trả `domain` (1 đến 3 nhãn trong 8 domain + `other`, danh sách ở `src/tam/schemas/domains.py`, theo `TOPICS.md`). Nhãn lạ bị bỏ, quá 3 thì cắt. Chunk lưu `domain_features.domain` dạng **danh sách**; payload index vẫn là keyword nên `MatchValue` khớp nếu nhãn nằm trong danh sách, và `passes_hard_filter` cũng chấp nhận danh sách. Profiler **chưa** đổi sang danh sách đóng (vẫn chuỗi tự do).

**Xử lý lỗi định dạng của `basic-llm` (9router):** combo bỏ qua structured output, trả JSON trong khối ```` ```json ````, đôi khi viết hoa khóa (`Index`) hoặc sai dấu phẩy. `TimeExtractor` giờ: thử structured output, lỗi thì đọc JSON từ văn bản (bỏ hàng rào markdown, hạ chữ thường khóa), tối đa 3 lần; hết lần thì đánh dấu `llm_error` (đếm riêng `skipped_llm_error`, không lẫn với `no_time`).

**Kết quả chạy local (`--dry-run`, 37 trang, 2026-10-19):**

| Đo | Kết quả |
|---|---|
| Chunk / có mốc / bỏ `no_time` / `invalid_time` / `llm_error` | 1275 / 1058 / 216 / 1 / 0 |
| Chunk đáp án còn sống | 39/41. Mất 2: `Central_European_University#62` ("Monica Macovei"), `Pskov#0` ("Russia"), đều `no_time` |
| Nhãn `domain` của câu hỏi nằm trong nhãn LLM gán cho chunk đáp án | 31/39 (79%) |
| Số nhãn mỗi chunk 0 / 1 / 2 / 3 | 23 / 807 / 429 / 16 |
| `ongoing = true` | 177 chunk, trong đó 42 chunk có `reason_end_date` nói "không có ngày kết thúc / không được nhắc" |

**Vấn đề thấy được:** `basic-llm` hay đặt `ongoing = true` khi văn bản không nói gì về lúc kết thúc, trái quy tắc "trạng thái 3: `end` null, `ongoing` false". Ví dụ lý do viết "No end date is mentioned" nhưng vẫn `ongoing = true`. Hậu quả: `end_time = None`, chunk đó được `Temporal_Score = 1.0` với mọi `t_req` sau `start`. Chưa sửa; cần siết prompt hoặc thêm bước kiểm tra, rồi so lại số liệu trên.

## Bộ thật: đã dựng (`dataset/eval/real_subset.json`)

`python scripts/make_eval_subset.py --subset real` (seed 42, không gọi LLM): **8 domain × 50 câu = 400 câu, 204 trang**. Mã: `build_topup_subset` trong `src/tam/evaluation/subset.py`.

- Ưu tiên `D/test.hard`; domain nào thiếu thì mượn `D/train.hard`: military 18, media_arts 16 (34 câu, ghi trong `borrowed_from_train`; mỗi câu có trường `split`). **Phải loại các câu mượn khỏi mẫu tinh chỉnh** (đợt 6) để không dùng chung câu giữa tune và test.
- Trong mỗi domain, lấy **xoay vòng qua các relation** (`sample_balanced`) để relation lớn không lấn hết. Quỹ relation của hai domain nhỏ vẫn hẹp: military chỉ có P4791 (27), P410 (17), P241 (6).
- **Bỏ câu trước Công nguyên** ([`decisions/05`](../decisions/05_EXCLUDE_BEFORE_COMMON_ERA.md)): bỏ nếu câu hỏi, nhãn thời gian, đáp án hoặc đoạn chứa đáp án có dấu hiệu `BC`/`BCE`/`B.C.` (`mentions_bce`). Kết quả: `D/test` 0 câu, `D/train` 2 câu. Chỉ bắt dấu hiệu viết ra bằng chữ; năm BC chỉ hiện ở chỗ khác trong trang thì ingestion vẫn tự bỏ chunk đó (`invalid_time`).
- Bỏ câu không xác định được chunk đáp án (`unmapped`): `D/test` 2, `D/train` 4. Trong 400 câu còn 12 câu có đáp án ở tiêu đề mục (`answer_in_heading`) và 12 câu có nhiều chunk đúng.
- 25/400 câu trùng với bộ local (cùng lấy từ `D/test`); chấp nhận vì local chỉ để kiểm tra chạy được.
- Kho riêng: `ingest.py` và `evaluate.py` mặc định ghi/đọc collection `<tên trong config>_<subset>` (vd `tam_chunks_dev_real`) với bộ không phải local, nên không xóa kho local. Đổi bằng `--collection`.

## Tinh chỉnh tham số: chưa có code

`λ` (`decay_lambda`), `W1`, `W2` hiện là giá trị cố định trong `configs/config.*.yaml` (0.5, 0.7, 0.3), chưa được chọn bằng dữ liệu. Chưa có script quét tham số, chưa có mẫu `D/train` nào. Kế hoạch (process 04 mục 6, overall plan tuần 4): quét trên mẫu `D/train`, tách khỏi `D/test` dùng báo cáo. Tinh chỉnh = chọn λ, W1/W2, top-N/top-K; chọn trên chính tập báo cáo sẽ làm điểm bị thiên vị.

## Mã đo và đánh giá

| File | Việc |
|---|---|
| `src/tam/llm/structured.py` | Gọi LLM lấy JSON, chịu được combo bỏ qua structured output (đọc JSON từ văn bản, thử lại) |
| `src/tam/evaluation/ingestion_report.py` | Báo cáo ingestion so với nhãn bộ con (chunk bị bỏ, `ongoing`, chunk đáp án còn sống, domain, độ đúng mốc) |
| `src/tam/evaluation/profiler_report.py` | Báo cáo Profiler (`t_req` trong nhãn, domain khớp chunk) |
| `src/tam/evaluation/retrieval_eval.py` | Dựng `EvalCase` (oracle hoặc e2e) cho `evaluate_retrieval` |
| `scripts/profile_eval.py`, `scripts/ingestion_report.py`, `scripts/evaluate.py` | Điểm vào dòng lệnh |
| `src/tam/llm/cache.py` | Cache kết quả LLM trên đĩa (`data/llm_cache/cache.sqlite` làm nguồn sự thật, `cache.json` để xem), dùng trong `invoke_structured`; cờ `--no-cache`, `--refresh-cache` ở `ingest.py` và `profile_eval.py` |
| `tests/test_eval_reports.py`, `tests/test_llm_cache.py` | Test các báo cáo và cache trên dữ liệu giả |

Hướng dẫn chạy lại từng bước: [`../instruction/01_RUN_PIPELINE.md`](../instruction/01_RUN_PIPELINE.md).

Kết quả: [`../eval/01_LOCAL_INGESTION.md`](../eval/01_LOCAL_INGESTION.md), [`../eval/02_RETRIEVAL_LOCAL.md`](../eval/02_RETRIEVAL_LOCAL.md).

## Quyết định liên quan

Ghi ở [`../decisions/`](../decisions/README.md): `domain` chỉ cộng điểm (01) và xử lý `end_time` / `ongoing` bị gán sai (02). Kết quả chạy: [`../eval/01_LOCAL_INGESTION.md`](../eval/01_LOCAL_INGESTION.md).

## Chưa làm

- Nạp vào Qdrant (chưa bật Qdrant; mới chạy `--dry-run`).
- Chỉ số "tỉ lệ chunk đáp án còn sống sau ingestion".
