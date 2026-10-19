# Kết quả retrieval Cơ chế 1 trên bộ local

Chạy 2026-10-19 bằng `scripts/evaluate.py` trên kho Qdrant nạp từ lần chạy ingestion 4 (`output/20261019_120005/`, 949 chunk của 37 trang, model phía sau combo 9router là `gemini-3.1-flash-lite`). 40 câu (8 domain × 5), mức `hard`. Mã: `src/tam/evaluation/retrieval_eval.py`, `scripts/evaluate.py`. Cấu hình retrieval: `W1=0.7`, `W2=0.3`, `λ=0.5`, `top_n=50` mỗi nhánh, `top_k=5`.

## Cách đo

- **Truy xuất:** hai nhánh độc lập (dense cosine và BM25) cùng áp lọc cứng `start_time <= t_req` và `invalidated_at` rỗng, gộp bằng RRF (`k=60`), min-max, rồi `Final = W1·Semantic + W2·Temporal`. Hit@k xét trên `top_k=5` chunk.
- **Chế độ `oracle`:** `t_req` là điểm giữa khoảng nhãn (`time_start` đến `time_end`, tính theo năm). Đây là quy ước của em, không phải mốc người hỏi nói. `semantic_query` lấy từ Profiler để hai chế độ chỉ khác nhau ở `t_req`.
- **Chế độ `e2e`:** `t_req` và `semantic_query` do Profiler tạo (`output/20261019_115213/profiler.jsonl`).
- **Hit@k (cột "chỉ chunk còn sống")**: chỉ tính trên 37 câu có ít nhất một chunk đáp án đã vào kho; 3 câu còn lại có chunk đáp án bị bỏ lúc ingestion nên không thể trúng. **Hit@k (cột "mọi chunk đáp án")**: tính trên cả 40 câu, chunk bị bỏ vẫn tính là trượt.
- `--no-temporal` đặt `W1=1, W2=0` (bỏ điểm thời gian; lọc cứng thời gian vẫn bật). `--facets domain` lọc cứng theo domain Profiler điền.
- Không có baseline plain RAG (`baselines/` chưa viết), nên đây là số tuyệt đối, chưa phải so sánh với đối chứng.

## Kết quả

| Cấu hình | Hit@1 | Hit@3 | Hit@5 | MRR | Hit@5 (mọi chunk đáp án) | MRR (mọi chunk đáp án) |
|---|---:|---:|---:|---:|---:|---:|
| oracle | 0.270 | 0.541 | 0.784 | 0.445 | 0.725 | 0.412 |
| oracle, bỏ điểm thời gian | 0.216 | 0.486 | 0.730 | 0.391 | 0.675 | 0.361 |
| e2e (Profiler) | 0.270 | 0.568 | 0.730 | 0.446 | 0.675 | 0.412 |
| e2e, bỏ điểm thời gian | 0.216 | 0.486 | 0.703 | 0.385 | 0.650 | 0.356 |
| e2e, lọc cứng domain | 0.270 | 0.595 | 0.730 | 0.448 | 0.675 | 0.415 |

Rò rỉ tương lai (`leakage_rate`) và chunk đã vô hiệu (`invalidated_rate`) bằng 0% ở mọi cấu hình.

## Đọc kết quả thế nào

- **Mẫu rất nhỏ:** 37 câu có thể trúng. Một câu đổi chiều là 2.7 điểm phần trăm; sai số 95% của một tỉ lệ ở n=37 khoảng ±15 điểm. **Mọi chênh lệch trong bảng đều nhỏ hơn sai số**, nên chưa kết luận được cấu hình nào tốt hơn. Bộ local cũng đã được ghi rõ là chỉ để kiểm tra chạy được (`EVAL_PLAN.md`).
- **Điểm thời gian có vẻ giúp một chút** (MRR 0.39 → 0.445 ở oracle, Hit@1 0.22 → 0.27) nhưng ở mức vài câu. Cần bộ lớn để khẳng định.
- **Lọc cứng domain** chỉ khác 1 câu ở Hit@3. Profiler chỉ điền domain cho 14/40 câu (26 câu để trống), nên bộ lọc hầu như không có tác dụng ở đây.
- **Profiler và oracle gần nhau** (Hit@5 0.73 so 0.78), nhưng `t_req` của Profiler đã nằm trong khoảng nhãn ở 40/40 câu, nên bản thân `t_req` không phải điểm nghẽn.
- **Hit@1 chỉ khoảng 0.27** dù kho nhỏ: mỗi trang có tới vài chục chunk cùng chủ đề (cùng một người, cùng một đội), nên phân biệt đúng chunk trong trang mới là khó khăn chính, không phải tìm đúng trang.
- Trần của ingestion: 3/40 câu có chunk đáp án bị bỏ lúc nạp, nên Hit@k tối đa khoảng 0.925 trên toàn bộ 40 câu.

## Chưa làm

- Baseline plain RAG (dense-only, không lọc, không điểm thời gian) để so.
- Phân tích 8 câu trượt ở Hit@5 (oracle): trượt vì chunk đúng không lọt top-N hay vì bị xếp sau chunk cùng trang.
- Tinh chỉnh `λ`, `W1/W2` trên mẫu `D/train` (chưa có code).
