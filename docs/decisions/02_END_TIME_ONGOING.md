# Quyết định 02: `end_time` / `ongoing` bị LLM gán sai

**Ngày:** 2026-10-19. **Trạng thái:** phần ingestion (bằng chứng + kiểm tra) đã code; phần chấm điểm và lưu `end_status` **chưa code**.

## Bối cảnh

Chạy bộ local (`docs/eval/01_LOCAL_INGESTION.md`): `basic-llm` đặt `ongoing = true` ở 177/1058 chunk, trong đó 42 chunk có `reason_end_date` tự nói "không có ngày kết thúc". Trái quy tắc prompt (không biết thì `ongoing = false`). Hệ quả: `end_time = None`, chunk được `Temporal_Score = 1.0` (TH1) với mọi `t_req` sau `start`; hai chunk của cùng một sự việc ở hai thời điểm cùng được 1.0 nên thời gian không phân biệt được chunk mới hơn.

## Ba chỗ khác nhau (đừng nhầm)

| Chỗ | Việc | Khi nào |
|---|---|---|
| Gán nhãn | LLM quyết `end` / `ongoing` cho chunk | Ingestion |
| Lưu | Kho giữ `end_time` (`ongoing` chỉ còn là `end_time = None`); **chưa** lưu phân biệt "ongoing" với "không biết" | Ingestion |
| Chấm điểm | Cách đổi `[start_time, end_time]` thành `Temporal_Score` | Truy vấn |

"Ba cách chấm" bên dưới thuộc dòng thứ ba, nhưng chỉ thực hiện được nếu dòng thứ hai lưu đủ thông tin (`end_status`).

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
