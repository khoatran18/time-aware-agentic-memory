# Đánh giá và dữ liệu: việc chưa chốt

- **Chấm `list` so với `summary`:** cả hai có đáp án là tập sự kiện gold theo thứ tự thời gian, chỉ khác khung câu hỏi. Cách chấm của hệ thống chưa quyết (`list`: khớp tập, kèm thứ tự?; `summary`: độ bao phủ sự kiện, ai chấm, ngưỡng?). Người dùng (2026-11-09): sẽ xem xét thêm, có thể gộp hai loại sau nếu cần, vì lõi vẫn là danh sách các sự kiện trong chunk.
- **Tỷ lệ theo loại câu** chưa đặt trong docs. Hiện v8+v8n 448 câu: `list` 31%, `first_last_next` 29%, `order_gap` 23%, `summary` 16%. Mục tiêu tham khảo: tune 300, valid 300, test 400 câu, khoảng 8–9 câu mỗi thực thể (hiện khoảng 4,5 mỗi trang).
- **Dữ liệu:** `valid` (167 trang) có gold nhưng chưa sinh câu hỏi; `test_clean` (186 trang) chưa có gold; 23 trang gold có tên file mất ký tự có dấu nên không gán tự động vào tune/valid bằng tên.
- **Soát gold:** gold 50 trang mới mới qua một vòng DeepSeek và đọc tay các ca nghi, chưa có người đọc thứ hai. Có 13 mốc thiếu phát hiện (Vologda 8, ACS_Poli 4, Alemannia 1); chưa quyết có đưa vào `extras` hay không.
- **`extras/`:** thư mục `dataset/eval/timeline_pilot/extras/` chưa tạo (bước gộp `local/chain_apply.py --apply` sẽ tạo khi có ca thật). Hai mốc từ v7n (Cochran, Sam_Selvon) chưa từng qua ingest, nên chưa dùng được cho precision.
- **Ranh giới với Cơ chế 3:** theo người dùng, Cơ chế 3 gốc xử lý mâu thuẫn khi nạp lại trang với bản mới hơn (ví dụ cùng trang Wikipedia bản mới). Mâu thuẫn trong cùng một trang (`source_inconsistent`) có thuộc Cơ chế 3 hay không thì chưa biết.
- **Lưu ý gold `source_inconsistent`:** gold lưu không đồng nhất (1 mốc cờ không mốc cho phiên bản kia, 2 mốc cùng cờ, 1 mốc cờ cạnh mốc chính); chưa lưu ngày thay thế. 156 mốc trên 73 trang.
- **Bước kiểm/gộp:** `local/chain_derived.py` và `local/chain_apply.py` đã viết và chạy thử; chưa áp thật vì bộ chính (v8, v8n) cần 0 ca.
- Việc cũ: ingest v10, Cơ chế 3, soát độc lập Gemini, `outdated_infos` HoH, ontology.
