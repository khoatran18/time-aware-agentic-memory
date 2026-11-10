# Prompt sinh câu hỏi v9 và checker đi kèm (đã viết 2026-11-09; Session 3–4 đã chạy 2026-11-10, kết quả ở docs/eval/10 mục 10.5av)

**Trạng thái:** `local/prompts/sinh_cau_hoi_v9.md` (4 session × 5 agent × 5 trang = 100 trang tune, ra `local/questions/v9/`) và `local/questions/check_questions.py v9` đã viết; chưa chạy Haiku. Checker v9: lỗi nếu dùng `source_inconsistent` ở mọi loại, thiếu `flagged_nearby_ids`, `summary` có cả mốc bắt đầu và kết thúc cùng quote; cảnh báo mốc cờ cùng track trong ±2 năm chưa khai, hai id chữ trùng cao ngày khác nhau; năm trong ngoặc "in any order" không còn tính là lộ đáp án (sửa Bill_Goldberg:3, Washington_Spirit:2). Mục "Dự định sửa" bên dưới đã thực hiện, trừ việc mốc cờ "cùng loại với criterion" vẫn cần người đọc.

"v9 câu hỏi" là prompt cho các session Haiku (cùng loại với `local/prompts/sinh_cau_hoi_v7.md`, `_v8.md`), khác với "bản 9 của ingest" (`pass3_p9.py`). Quyết định hiện hành: dùng v8 (`decisions/13`); v9 chỉ thay v8 nếu đo tốt hơn.

## Đã chốt (người dùng, 2026-11-09)
Luật cờ **mức 2 = quy tắc 1 + quy tắc 2** (ghi cả ở `decisions/14` mục 4):
1. Mốc `source_inconsistent` không nằm trong đáp án và không làm điểm neo, ở cả bốn loại câu.
2. Nếu mốc cờ B cùng loại với `criterion` và nằm gần chuỗi, đáp án phải không đổi khi B lệch ±2 năm (độ lệch giả định, chưa đo): `list`/`summary` cần khoảng của câu loại hẳn B; `order_gap` cần B không là điểm neo; `first_last_next` cần "đầu" sớm hơn d−2, "cuối" muộn hơn d+2, "kế tiếp" không có B nằm giữa mốc cho trước và đáp án.

## Dự định sửa prompt v8 → v9 (chưa viết)
- Mục A: `source_inconsistent` cấm ở cả 4 loại.
- Mục B: viết lại theo quy tắc 2, thêm trường `flagged_nearby_ids` (mốc cờ cùng track gần chuỗi và lý do không ảnh hưởng).
- Hai mốc trong chuỗi cùng một sự kiện (text/quote gần giống hoặc cùng mang cờ mâu thuẫn): chỉ giữ một hoặc bỏ câu (lỗi Steele_Hall:3).
- Thông báo và hoàn tất của cùng một giao dịch không đếm thành hai mục trừ khi câu hỏi hỏi cả hai (lỗi Condor).
- Mục I: thêm ví dụ "first overnight service" không phải "new route" (lỗi Panair).
- Giữ `derived_date` cấm hoàn toàn, trừ khi chốt khác (xem mục dưới).

## Dự định sửa `local/questions/check_questions.py`
- Báo lỗi khi dùng `source_inconsistent` ở bất kỳ loại nào.
- Cảnh báo khi mốc cờ cùng track nằm trong ±2 năm quanh chuỗi mà câu không khai `flagged_nearby_ids` (so khớp loại sự kiện bằng mã chỉ xấp xỉ qua track/label; so với `criterion` cần người hoặc LLM).
- Cảnh báo khi hai id trong chuỗi có chữ trùng cao.
- Sửa hai lỗi "any order + năm" (Bill_Goldberg:3, Washington_Spirit:2); thêm kiểm `summary` chứa cả đầu lẫn cuối một giai đoạn.

## Bốn câu lỗi cũ của v8 (chưa xử lý)
Steele_Hall:3 (`summary`, e11/e12 là cùng một lần từ chức bị hai chunk ghi hai năm, đếm đôi), Condor `summary` (thông báo e29 + hoàn tất e31), Panair `list` (e16 "first overnight service" không phải tuyến mới), Talk_im_Turm `list` (e5 `source_inconsistent`, e10 `approximate_date` trong chuỗi). Ba trong bốn câu cũng nằm trong 6 câu dùng `source_inconsistent`.

## Chưa quyết
- Có cho `derived_date` vào `list`/`summary` hay không. Số liệu để cân nhắc (gold, 1165 mốc `derived_date`): 325 mốc có năm trong chính quote (cờ vì tháng/ngày hoặc lý do khác), 98 mốc quote là năm viết tắt, 430 mốc năm nằm trong chunk nhưng không trong quote (câu trước, tiêu đề mục), 312 mốc năm không có trong chunk bằng chứng. Hiện cả 1165 mốc bị cấm trong câu hỏi; 755 mốc (nhóm đầu, thứ ba) có năm sẵn trong chunk, có thể bị loại quá tay. Chưa kiểm chứng độ tin cậy của nhóm này.
- Phương án đo v9: chạy trên 100 trang tune (50 cũ + 50 mới) để so cặp với v7 và v8; chỉ số: số câu mỗi loại, checker, [1] tỷ lệ ứng viên thật, [2][3] đóng góp thật, đọc mù mẫu, số câu dùng mốc cờ (mục tiêu 0). Chưa đo nhiễu giữa hai lần sinh cùng prompt; nên chạy hai lần nếu muốn kết luận.

## Cách dùng mốc derived và mốc mới trong đáp án (thảo luận 2026-11-09)

**Đã chốt (người dùng, 2026-11-09):** (1) mốc derived đã có trong gold và [2] duyệt: thêm id vào đáp án của câu đó; (2) mốc derived mới chưa có trong gold: chỉ ghi `extras`, **không** cho vào đáp án, bỏ câu nếu nó nằm trong khoảng chuỗi và thỏa tiêu chí; (3) mốc ngày rõ nhưng mới chưa có trong gold: bỏ câu, ghi `extras` (hướng b). **Chưa chốt, không phải việc trước mắt:** phương án giữ câu với id `extra_<trang>_<n>` / `answer_extra` (xem bảng và điều kiện nhất quán dưới đây); xem lại nếu số ca tăng ở valid/test.

**Hướng người dùng nêu (phần (1) đã chốt, xem trên):** khi sinh câu hỏi, mốc `derived_date` không làm điểm neo và không dựa vào làm đáp án. Sau đó [1] đọc cả trang; nếu [1] đề xuất mốc derived thỏa tiêu chí và [2] duyệt (năm lấy từ chính chunk hoặc từ năm viết tắt do mã tính; năm phải suy từ chunk khác thì không cho) thì mốc được thêm vào **đáp án của câu đó**, không thêm vào gold. Lợi ích: không phải bỏ câu chỉ vì có mốc derived xen giữa (mục B của prompt v8 hiện bắt bỏ câu hoặc thu hẹp phạm vi).

Phân loại theo nơi mốc nằm:

| Mốc | Logic hiện tại (người dùng nêu) | Phương án thay thế (đang cân nhắc) |
|---|---|---|
| Có trong gold, mang cờ `derived_date`, [2] duyệt | thêm id vào đáp án câu đó (`add_ids`; `chain_apply.py` cần cho phép khi quyết định ghi `verified_derived: true`) | — |
| Derived mới, chưa có trong gold | ghi `extras` (để tính precision ingest); **bỏ câu** nếu mốc nằm trong khoảng chuỗi và thỏa tiêu chí | giữ câu, thêm vào đáp án qua `answer_extra` |
| Ngày rõ cùng câu, chưa có trong gold (ví dụ Cochran DFC, Sam_Selvon Chaconia) | ghi `extras`, **bỏ câu** (hướng b) | giữ câu, thêm id kiểu `extra_<trang>_<n>` vào đáp án |

**Ý kiến của mình (đề xuất, chưa chốt):**
- Giữ logic hiện tại (bỏ câu + ghi `extras`) cho giai đoạn này. Số ca thật rất ít: v7n 2/254 câu (Cochran:2, Sam_Selvon:1), v8n 0, v8 0, nên bỏ câu chỉ mất dưới 1%; còn việc dựng id `extra_*` và trường `answer_extra` thêm schema và chấm điểm.
- Nếu sau này số ca tăng (ví dụ valid/test có gold chưa soát kỹ), đáng cân nhắc phương án giữ câu: mốc ngày rõ nhưng chưa có trong gold đáng tin ngang mốc gold (quote đã được mã và giám khảo kiểm), còn derived mới thì kém tin hơn nên giữ bỏ câu.
- Điều kiện để phương án giữ câu nhất quán giữa các câu cùng trang: sau khi tạo `extras`, phải chạy lại [1] cho **mọi** câu liên quan của trang với `extras` được đưa vào danh sách `ALREADY RECORDED`; nếu không thì câu khác có tiêu chí khớp mốc đó sẽ thiếu mốc trong đáp án trong khi câu đầu có. Hiện [1] chỉ đưa gold ngoài chuỗi vào `ALREADY RECORDED`, chưa có `extras`.
- Cần định nghĩa rõ "[2] duyệt derived" (xem luật chặt ở trên) trước khi dùng.
