# Nhật ký triển khai 06: Dựng bộ câu hỏi local và nhãn chunk đúng

Tiếp nối [`05_TIME_SEMANTICS_AND_CHUNKING.md`](05_TIME_SEMANTICS_AND_CHUNKING.md) mục 2.4 và `dataset/full_dataset/EVAL_PLAN.md`. Không gọi LLM.

## Đã làm

| File | Việc |
|---|---|
| `src/tam/evaluation/subset.py` | `sample_cases` (lấy mẫu theo chủ đề, seed cố định), `paragraph_spans`, `gold_paragraph_indices`, `build_subset` |
| `scripts/make_eval_subset.py` | `python scripts/make_eval_subset.py --subset local` (hoặc `real`), mặc định seed 42 |
| `dataset/eval/local_subset.json` | Kết quả: 25 câu, 19 trang, có `gold_chunk_ids` |
| `tests/test_eval_subset.py` | Ánh xạ đáp án sang đoạn, tính tất định của lấy mẫu |

## Cách làm

1. Đọc `D/test.hard.jsonl`; mỗi chủ đề P54, P39, P26, P108, P69 lấy 5 câu bằng `random.Random(seed)` sau khi sắp theo `idx`. Câu `easy` lấy theo cùng `idx` và lưu kèm.
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

Bộ local seed 42 không dính hai câu vắt đoạn: chỉ có 1 câu đáp án ở tiêu đề mục, 0 câu nhiều chunk.

## Kết quả (seed 42)

- 25 câu (5 × 5), **19 trang** (kế hoạch ước 21, vì seed khác); 0 câu nhiều chunk đúng; 1 câu đáp án nằm ở tiêu đề mục (cờ `answer_in_heading`, lấy đoạn kế tiếp).
- Kiểm tra: mọi chunk đúng đều chứa nguyên văn `targets` của câu.

## Chưa làm

- Chạy ingestion bộ local với LLM thật và Qdrant (`scripts/ingest.py` chưa có).
- Chỉ số "tỉ lệ chunk đáp án còn sống sau ingestion".
