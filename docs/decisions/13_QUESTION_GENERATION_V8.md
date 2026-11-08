# 13. Sinh câu hỏi Cơ chế 2: chốt prompt v8 và quy ước chuỗi đáp án

Ghi ngày 2026-11-08. Bằng chứng và số liệu chi tiết ở [`eval/10`](../eval/10_TIMELINE_DATASET_DESIGN.md) (mục 10.5ap đến 10.5at); file này chỉ ghi quyết định.

## 1. Bối cảnh

Câu hỏi của bộ timeline do Haiku sinh từ timeline vàng. Với `list`, `summary`, `first_last_next`, đáp án là chuỗi mốc (`gold_event_ids`, `group_event_ids`) do người sinh chọn; ở prompt v5 nhiều khi chỉ là tập con của chuỗi thật, nên đáp án thiếu mốc. Đo bằng bước [1] (DeepSeek đọc cả trang) cùng prompt: v5 có ứng viên thật ở 31/192 lượt (16%).

## 2. Phương án

| Bản | Thay đổi so với bản trước | [1] lượt có ứng viên thật |
|---|---|---|
| v5 | bản cũ | 16% |
| v6 | chuỗi đầy đủ (duyệt toàn bộ `events`, bỏ câu nếu nghi thiếu), mốc cờ/`undated_mentions` xen chuỗi thì thu hẹp hoặc bỏ, `order_gap` chỉ hỏi khoảng cách năm giữa hai mốc nêu tên, bỏ tiêu chí mơ hồ (`work`), ghi `criterion`, `window_from/to`, `flagged_ids` | 5% |
| v7 | v6 + `summary` là tổng hợp đầy đủ một giai đoạn hẹp (3 đến 8 mốc, không gồm cả đầu lẫn cuối một nhiệm kỳ) + mỗi agent chỉ ghi file trang của mình | 4% |
| v8 | v7 + chuỗi khớp nghĩa đen câu hỏi (`criterion` viết trước, mỗi cụm của câu hỏi ánh xạ vào `criterion`, mốc cùng track bị loại phải ghi lý do, câu hỏi chung thì chuỗi phải đủ, `summary` ≥3 mốc) | 3% |

So v7 với v8 trên 50 trang cũ (v7 179 câu, v8 171) và trên 50 trang mới, cùng bộ trang (v7n 254, v8n 277): [1] 5,8% so với 3,7% (mới); số câu thiếu mốc thật 4/190 (v7n) so với 0/215 (v8n); đọc mù 48 câu: v7n 4 lỗi nhẹ, v8n 2. Trên 50 trang cũ hai bản ngang nhau. Một người đọc, mỗi bản sinh một lần, chưa đo nhiễu.

## 3. Quyết định (người dùng chốt 2026-11-08)

1. **Dùng prompt v8** (`local/prompts/sinh_cau_hoi_v8.md`) để sinh câu hỏi. Bộ chính hiện có: `local/questions/v8` (171 câu, 50 trang) và `local/questions/v8n` (277 câu, 50 trang mới), tổng 448 câu. v7 chỉ là đối chứng, không dùng.
2. **Không thêm mốc vào gold timeline.** Gold dùng chung cho mọi câu của trang, thêm mốc có thể đổi đáp án câu khác; và công cụ chỉ bắt một phần mốc thiếu nên bổ sung sẽ thiên lệch.
3. **Chỉ điều chỉnh chuỗi đáp án của từng câu** (đề xuất cách làm, chưa code): mốc có trong gold, ngày rõ, bỏ sót thì thêm id và tính lại `answer_ids`; mốc `derived` đã qua bước kiểm `derived` thì dùng được ở `list`/`summary`; mốc mới ngoài gold thì bỏ câu.
4. **Mốc mới, ngày rõ, ngoài gold** ghi vào `dataset/eval/timeline_pilot/extras/<Trang>.json` để tính precision của ingest, không để làm đáp án (đề xuất, thư mục chưa tạo).
5. **[1], [2], [3] là công cụ đo và kiểm**, không phải bước sửa: cải thiện chuỗi đầy đủ đến từ prompt (v5 → v8). [1] một mình báo nhầm nhiều, nên [2], [3] bắt buộc.
6. Bỏ khỏi bộ chính: nhóm `work`, câu "không đủ thông tin" (đã chốt ở `eval/10`, 10.5aj).

## 4. Ảnh hưởng

- Số câu giảm 32–35% so với v5 trên cùng 50 trang (262 → 171–179) vì luật chuỗi đầy đủ; `summary` còn 19–20 (v5: 26) vì loại câu "chọn vài điểm chính". Hiện khoảng 4,5 câu mỗi trang, thấp hơn mục tiêu 8 đến 9 câu mỗi thực thể ở `eval/10`.
- Cơ cấu v8 + v8n: `list` 31%, `first_last_next` 29%, `order_gap` 23%, `summary` 16%. Docs chưa đặt tỷ lệ mục tiêu theo loại.
- Gold 50 trang mới chưa qua vòng soát độc lập (chỉ một vòng DeepSeek và đọc tay các ca nghi): 13 mốc thiếu, không rơi vào câu nào.

## 5. Chưa làm / chưa chốt

- Bước kiểm `derived`, bước gộp (chạy thử, sao lưu, nhật ký), ghi `extras/`.
- Bốn câu lỗi đã biết: Steele_Hall q3 (hai mốc từ chức đếm đôi), Condor `summary` (thông báo cộng hoàn tất), Panair `list` (`e16` không phải tuyến mới), Talk_im_Turm `list` (mốc cờ trong chuỗi); hai lỗi checker "any order" (Bill_Goldberg:3, Washington_Spirit:2).
- Cách chấm `list` so với `summary` ở bước đánh giá (`eval/10` mục 6: `summary` chấm bằng độ phủ sự kiện, chưa chốt).
- Đo nhiễu giữa hai lần sinh; đọc mù v5 cùng chuẩn để so chất lượng nội dung.

## Trạng thái

Đã chốt dùng v8 (2026-11-08). Phần xử lý chuỗi và `extras` là đề xuất, chưa code.
