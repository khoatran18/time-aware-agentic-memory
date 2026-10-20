# Quyết định 02: `end_time` / `ongoing` bị LLM gán sai

**Ngày:** 2026-10-19. **Trạng thái:** ingestion (bằng chứng + kiểm tra), lưu `end_status` và ba cách chấm A/B/C đã code (`end_mode`), **chưa chạy so sánh**. `end_time` vẫn được lưu như cũ; `end_status` là trường thêm, không thay `end_time`.

## Bối cảnh

Chạy bộ local (`docs/eval/01_LOCAL_INGESTION.md`): `basic-llm` đặt `ongoing = true` ở 177/1058 chunk, trong đó 42 chunk có `reason_end_date` tự nói "không có ngày kết thúc". Trái quy tắc prompt (không biết thì `ongoing = false`). Hệ quả: `end_time = None`, chunk được `Temporal_Score = 1.0` (TH1) với mọi `t_req` sau `start`; hai chunk của cùng một sự việc ở hai thời điểm cùng được 1.0 nên thời gian không phân biệt được chunk mới hơn.

## Các trường liên quan và bước tạo ra chúng

Ba bước nối tiếp nhau. Bốn tên `end`, `ongoing`, `end_time`, `end_status` không phải bốn thứ độc lập: hai cái đầu là **đầu ra thô của LLM**, hai cái sau là **giá trị code suy ra**.

| Bước | Ai làm | Khi nào | Tạo ra |
|---|---|---|---|
| 1. Gán nhãn | LLM (`ingestion_time_v1.md`) | Ingestion | `end` (chuỗi ngày hoặc rỗng), `ongoing` (đúng/sai), kèm `reason_end_date`, `ongoing_evidence` |
| 2. Chuẩn hóa và lưu | Code (`to_span` trong `time_extraction.py`) | Ingestion | `end_time` lưu trong Qdrant: nếu `ongoing` thì `None`; nếu có `end` thì cuối kỳ của `end`; nếu rỗng thì cuối kỳ của `start`. Đồng thời kiểm tra `ongoing_evidence` |
| 3. Chấm điểm | Code (`TemporalRetriever`) | Truy vấn | `Temporal_Score` từ `[start_time, end_time]` và `t_req` |

| Tên | Là gì | Đã code? |
|---|---|---|
| `end` | Ngày kết thúc LLM trả (có thể rỗng) | Có |
| `ongoing` | LLM khẳng định sự việc còn tiếp diễn | Có |
| `end_time` | Giá trị lưu trong kho, suy từ hai trường trên. `None` có nghĩa "còn hiệu lực" | Có |
| `end_status` | Nhãn `known` / `ongoing` / `unknown` suy từ `end` và `ongoing` (`known`: có `end`; `ongoing`: `ongoing` đúng; `unknown`: không `end`, không `ongoing`). Lưu trong payload, không index | Có (`Chunk.end_status`, `to_span`) |

Vấn đề: sau bước 2 hai trường hợp `ongoing` và `unknown` khác nhau về ý nghĩa nhưng bước chấm điểm (3) không phân biệt được vì `unknown` đã bị đổi thành cuối kỳ của `start`. `end_status` bổ sung thông tin này để bước 3 có thể chọn cách chấm (mục Quyết định).

## Quyết định

1. **Siết gán nhãn lúc ingestion (đã code).** Thêm trường `ongoing_evidence`: khi `ongoing = true`, LLM phải trích **nguyên văn** câu cho thấy tình huống còn tiếp diễn. Code kiểm tra (a) câu đó có trong văn bản của lô chunk (cả trang; bằng chứng ở chunk khác của trang vẫn được, vì cùng một sự việc có thể được nói tiếp ở chunk sau), (b) chứa dấu hiệu còn hiệu lực (`since`, `present`, `currently`, `still`, `remains`, `continues`, `to date`, `incumbent`, `today`, `ongoing`...). Không đạt thì hạ `ongoing = false` (trạng thái "không biết"), ghi vào `note`. Đây là kiểm tra heuristic cho tiếng Anh (TimeQA), không thay được hiểu ngữ nghĩa.
2. **Chấm điểm chịu được nhãn sai (chưa code).** Lưu thêm `end_status` (`known` / `ongoing` / `unknown`, không index). Chấm điểm sẽ ablation 3 cách:
   - A. `ongoing` / `unknown` → `end_time = None`, TH1 = 1.0 mãi (hành vi hiện tại của `ongoing`).
   - B. `ongoing` / `unknown` → TH1 nhưng giảm nhẹ theo khoảng cách `start` tới `t_req`, để chunk bắt đầu gần `t_req` nhất thắng.
   - C. `unknown` → coi như kết thúc cuối kỳ của `start` (hành vi hiện tại của `unknown`).

Hai việc bổ sung nhau: (1) giảm số nhãn sai, (2) hạn chế thiệt hại của nhãn sai còn sót.

## Phương án đã thử rồi bỏ: bằng chứng phải nằm trong chính chunk

Nghi ngờ ban đầu: ở lần chạy 2, `Casus_Belli_(magazine)#3, #4, #6` có bằng chứng "Since 2020" (nói về kênh Casus TV) mà mốc chunk là 2011, 1992, 1980, tức bằng chứng mượn từ chunk khác và có vẻ nói về sự việc khác. Đã code rule "bằng chứng phải nằm trong chính chunk" rồi **gỡ trước khi chạy thật**, vì đọc kỹ lại thì các ca này **đúng**: tạp chí vẫn đang xuất bản ("published by Black Book Éditions since 2011", "Since 2020, Black Book Éditions also publishes ..."), chunk 4 và 6 mô tả/nhận xét về cùng tạp chí đó nên `ongoing` suy từ chunk 0 và 3 là hợp lý (lý do LLM ghi: "ongoing status comes from chunk 0"). Rule nghiêm sẽ hạ nhầm chính những ca suy luận chéo chunk hợp lý, trái mục đích đưa cả trang vào ngữ cảnh. Điều cần học: câu bằng chứng LLM trích có thể không phải câu đúng nhất (nó trích "Since 2020" thay vì "since 2011"), nhưng kết luận `ongoing` vẫn đúng; kiểm tra chỉ nên chặn bằng chứng bịa hoặc không có dấu hiệu, không nên đòi bằng chứng nằm trong chunk.

## Nguyên nhân `ongoing` còn sai sau khi siết (đọc tay 7 chunk, lần chạy 2)

Phần lớn chunk `ongoing` đáng ngờ hóa ra **đúng** (`Volvo_9700#29` "At present, they offer...", `Condor_(airline)#29` "is now headquartered in Frankfurt", `Gerhard_Schröder#61` "since his retirement", `Lisa_Marie_Presley#63` "continue to be on exhibit"). Chỗ sai còn lại có hai nguyên nhân cấu trúc, không sửa được bằng prompt:

1. **Một chunk nhiều sự việc, một khoảng thời gian.** `Atlético_Madrid#83` nói màu áo đổi năm 1911 (đã xong) và hợp đồng Nike "since 2001" (còn tiếp diễn): LLM gán `ongoing` cho cả chunk nên sự việc 1911 bị coi còn hiệu lực. `Condor#29`: trụ sở cũ ở Kelsterbach (đã kết thúc) và mới ở Frankfurt (đang có). Gốc: chunk theo đoạn của dataset, mốc là hợp các sự việc (`process/04` mục 5.3). Chỉ gán mốc ở mức sự việc (đồ thị, Cơ chế 2) mới hết hẳn.
2. **Chọn nhầm câu bằng chứng.** `Casus_Belli`: LLM trích "Since 2020" thay vì "since 2011" nhưng kết luận `ongoing` vẫn đúng. Kiểm tra chỉ chặn được bằng chứng bịa hoặc không có dấu hiệu, không đánh giá được câu có phải câu tốt nhất.

Chưa kiểm tay đủ 35 chunk. Số liệu theo lần chạy: `docs/eval/01_LOCAL_INGESTION.md`.

### Đề xuất sửa cho hai nguyên nhân trên (chưa làm)

| Nguyên nhân | Hướng | Đánh giá |
|---|---|---|
| Chunk nhiều sự việc, một khoảng thời gian | (a) Chấm điểm cách B (`ongoing` giảm nhẹ theo khoảng cách `start` tới `t_req`) để chunk `ongoing` quá rộng không thắng mọi chunk khác | Rẻ, chỉ cần lưu `end_status`; không làm mốc chunk đúng hơn |
| | (b) Mốc theo sự việc (Cơ chế 2, đồ thị): mỗi sự việc một `[start, end]` riêng | Đúng gốc nhưng ngoài phạm vi Cơ chế 1 |
| | (c) Cho LLM trả danh sách mốc cho từng sự việc trong chunk, lưu nhiều khoảng cho một chunk | Tốn thay đổi schema Qdrant, chưa cân nhắc kỹ |
| Chọn nhầm câu bằng chứng | Không cần sửa: kết luận vẫn đúng. Có thể ghi thêm "câu đầu tiên có dấu hiệu" vào prompt nhưng lợi ích nhỏ | Bỏ qua |

Khuyến nghị: làm (a) trước vì rẻ và đo được bằng ablation; (b), (c) chỉ khi (a) cho thấy lỗi `ongoing` thực sự làm tụt hạng chunk đáp án.

## Kết quả đo (bộ local, 2026-10-19)

Ba cách chấm đã code (`end_mode`) và chạy so ở [`../eval/04_TEST_RESULTS.md`](../eval/04_TEST_RESULTS.md) đợt 3: `stored` (C) `mrr` 0.420, `open` (A) 0.418, `decay` (B) 0.390 đến 0.408. **Không cách nào hơn rõ** (chênh dưới 1 câu), nên giữ `stored` (mặc định). Trên nền tìm kiếm dense kết quả cũng tương tự (`open` 0.519 so với `stored` 0.494, nhưng 3 câu lên, 5 xuống).

Phân tích câu sai cho thấy `end_status = unknown` là nguyên nhân của 5/9 câu còn sai ở cấu hình tốt nhất: chunk `unknown` bị coi hết hiệu lực cuối năm `start`, nhưng sự việc còn đúng ở `t_req`. Ba cách chấm không phân biệt được chunk `unknown` còn đúng với chunk đã hết hạn thật, và chúng xử lý `ongoing` và `unknown` cùng một cách. Đề xuất tách hai loại: `06`. Các hướng đề xuất: [`06_END_UNKNOWN_REMEDIES.md`](06_END_UNKNOWN_REMEDIES.md).

Cập nhật 2026-10-20: thêm cách chấm thứ tư `unknown_decay` (chỉ `unknown` giảm dần, `ongoing` giữ 1.0), đo ở `eval/04` đợt 3d: `mrr` 0.580 so với 0.544 (`decay`) và 0.542 (`stored`) ở nền dense, `t_unknown` 0.1. Chi tiết và các hướng khác: [`06`](06_END_UNKNOWN_REMEDIES.md). Ba cách A/B/C ở trên giữ nguyên.
