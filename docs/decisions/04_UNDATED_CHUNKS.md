# Quyết định 04: chunk không có mốc `start` và câu hỏi không nêu thời gian

**Ngày:** 2026-10-19. **Trạng thái:** đã chọn làm thử và **đã code (mặc định tắt)**, chưa đo; quyết giữ hay bỏ sau đợt 4 của `eval/03`. Mặc định chunk không có `start` vẫn bị bỏ lúc nạp (`skipped_no_time`). Bản phác cũ: [`../process/05_TIME_SEMANTICS_AND_CHUNKING.md`](../process/05_TIME_SEMANTICS_AND_CHUNKING.md) mục 3.4.

## Hai trục khác nhau (hay bị gộp)

| Trục | Ví dụ | Hệ thống làm gì |
|---|---|---|
| **Câu hỏi** không nêu thời gian | "Quy định xây dựng hiện tại là gì?" | Profiler trả `t_req = null`, hệ thống dùng `T_now`. Mặc định "hỏi về hiện tại" là chính sách do nhóm chọn (scope mục 5), dataset không quy định |
| **Chunk** không có `start` | "Pskov is a city in northwestern Russia..." | Hiện bị bỏ, không vào kho |

Hai trục độc lập. Bộ local có 40/40 câu easy và 35/40 câu hard **có** năm hoặc mốc, nhưng vẫn có chunk đáp án không có năm (`Pskov#0`, `Central_European_University#62`), vì sự việc ổn định theo thời gian nên đoạn trả lời không ghi năm. Vậy chunk không mốc cần phục vụ cả câu hỏi có năm lẫn không có năm.

## Vì sao không chỉ để LLM đoán mốc

Mốc sai hại hơn không có mốc: làm hỏng cả lọc cứng `start_time <= t_req` lẫn điểm thời gian mà hệ không biết. Quy tắc giữ là "không bịa mốc". Prompt chỉ cho kế thừa mốc từ chunk lân cận khi chắc chắn cùng một giai đoạn. Đổi lại độ phủ giảm: lần chạy 4 của bộ local bỏ 321/1275 chunk, trong đó 3/41 chunk đáp án (`docs/eval/01_LOCAL_INGESTION.md` mục 8).

## Đề xuất

**Lưu trữ.** Chunk không mốc vào cùng collection với `start_time = NULL` (kèm cờ không mốc). Lọc cứng `start_time <= t_req` tự loại chúng khỏi nhánh time-aware (so khoảng với trường rỗng không khớp) nên không rò rỉ tương lai ở nhánh chính. Cần kiểm bằng test Qdrant thật.

**Truy xuất.** Thêm nhánh thứ ba lọc `start_time IS NULL` và `invalidated_at IS NULL`, cùng tìm dense và BM25, rồi gộp ứng viên với nhánh chính.

**Chấm điểm.** Chunk không mốc không có TH1 hay TH2; gán điểm thời gian trung tính cố định `T_unknown` (ví dụ 0.5):

`Final = W1·Semantic + W2·T_unknown`

| Loại chunk | Điểm thời gian |
|---|---|
| Có mốc, đúng lúc `t_req` (TH1) | 1.0 |
| Không mốc | `T_unknown` |
| Có mốc, hết hiệu lực xa (TH2) | `exp(-λ·Δ)` giảm dần về 0 |

Cách chấm **không phụ thuộc** câu hỏi có năm hay không; chỉ `t_req` khác (năm đã nêu hoặc `T_now`):
- Câu hỏi có năm: chunk có mốc đúng lúc thắng, chunk không mốc lên top khi nội dung (Semantic) khớp rõ hơn hoặc không có chunk có mốc phù hợp.
- Câu hỏi không có năm (`T_now`): chunk còn hiệu lực hiện tại (1.0) thắng; chunk ổn định không mốc vẫn đủ điểm nếu khớp nội dung; chunk hết hiệu lực xa thấp hơn.

## Đã cân nhắc và bỏ: tách chunk không mốc thành "đúng mọi lúc" và "không rõ"

Chunk không mốc chỉ có một loại: **chưa biết khi nào**. Không gán thêm nhãn "sự thật không đổi", vì hầu hết sự thật ổn định vẫn có mốc bắt đầu (Washington là thủ đô của Mỹ từ năm 1800, không phải mọi thời gian), chỉ là văn bản không ghi. Gán nhãn đó là khẳng định LLM không có cơ sở, và điểm cao cho nó có thể đưa chunk đã hết hiệu lực lên đầu. Mọi chunk không mốc dùng chung `T_unknown`.

## Rủi ro và điều phải đo

1. `T_unknown` là con số tự chọn: cao thì chunk không mốc lấn chunk đúng thời điểm, thấp thì không bao giờ được chọn. Cần ablation (ví dụ 0.3 / 0.5 / 0.7, và chế độ chỉ dùng nhánh không mốc khi kết quả ít). Vậy kịch bản đánh giá tổng thể thêm một tham số cần quét, cùng loại với `λ`, `W1/W2`; nên quét trên tập tinh chỉnh (`D/train`), không trên tập báo cáo.
2. Chunk không mốc có thể mô tả sự việc **sau** `t_req` mà hệ không biết (rò rỉ tương lai không phát hiện được). Giảm nhẹ: Time-CoT bắt buộc ghi "thông tin này không xác định được thời điểm" khi dùng chúng.
3. So sánh với plain RAG phải ghi rõ tỉ lệ câu chỉ trả lời được nhờ nhóm này (plain RAG thì mọi chunk đều dùng được).
4. Cần đo: Hit@k và MRR có và không có nhánh không mốc, trên các câu mà chunk đáp án không mốc (ở bộ local: 3 chunk).

## Việc nếu chấp nhận

`Chunk.start_time` thành tùy chọn; ingestion giữ chunk không mốc; `qdrant_store` thêm truy vấn `IsNull(start_time)`; `TemporalRetriever` thêm nhánh và `T_unknown` (config `retrieval.t_unknown`); sửa bất biến trong `design/02` và `CLAUDE.md` ("không có mốc thì không vào kho" thành "không vào nhánh time-aware").

## Đã code (khác với đề xuất ở chỗ nào)

- `Chunk.start_time` có thể rỗng; chunk có `end_time` mà không có `start_time` bị từ chối.
- `ingest.py --keep-undated`: giữ chunk `no_time` **nếu LLM gán được ít nhất một nhãn domain** (dùng nhãn domain làm dấu hiệu "có nội dung" để loại dòng tham khảo, mảnh vụn; ở lần 2 cả 24 chunk không domain đều là loại này). `invalid_time` (vd trước Công nguyên, [`05`](05_EXCLUDE_BEFORE_COMMON_ERA.md)) vẫn bị bỏ.
- Truy xuất: nhánh thứ ba lọc `start_time IS NULL` (dense và BM25), gộp với nhánh có mốc theo điểm gốc từng nhánh, rồi RRF như cũ. Bật bằng `retrieval.t_unknown` (vd 0.5) hoặc `evaluate.py --t-unknown 0.5`; `null` = tắt. Chunk không mốc nhận `Temporal_Score = t_unknown`.
- **Chưa làm:** sửa bất biến ở `design/02` và `CLAUDE.md` (chờ quyết sau khi đo).
- Chưa kiểm với Qdrant thật: điều kiện `IsNull(start_time)` cần chạy thử trên kho nạp bằng `--keep-undated`.
