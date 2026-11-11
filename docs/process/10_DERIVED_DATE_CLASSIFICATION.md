# 10. Phân loại mốc `derived_date` trong gold (loại a / b / khác)

Ghi 2026-11-11. Trạng thái: **mã đã viết và chạy trên gold test_clean (186 trang); chưa kiểm chứng bằng người đọc độc lập; chưa quyết định dùng loại a để sinh câu hỏi.** Gold KHÔNG bị sửa.

## 1. Vì sao có việc này
Luật hiện hành (`local/questions/check_questions.py:125`, prompt `sinh_cau_hoi_v9.md` luật 1): mốc có cờ `derived_date` bị cấm ở mọi câu hỏi. Cờ gộp nhiều loại có độ tin cậy khác nhau; gold chỉ có một giá trị `flag` nên không phân biệt được. Câu hỏi: có loại "năm lấy từ ngữ cảnh liền kề" đủ chắc để dùng không (loại a), còn loại tương đối/viết tắt (loại b) vẫn cấm.

## 2. Nơi lưu (bản cũ không mất)
- **Gold gốc, không đổi:** `dataset/eval/timeline_pilot/batchT/sub/*.json` (bản Haiku) và `batchT/rev/*.json` (50 trang đã soát). Cờ `derived_date` vẫn nguyên.
- **Bản chụp cờ cũ:** `dataset/eval/timeline_pilot/derived_classify/2026-11-11_flags_snapshot.jsonl` (mỗi dòng: page, nguồn `rev`/`sub`, id, date, flag, cho MỌI mốc có cờ: 1083 dòng).
- **Kết quả phân loại (lớp phủ, tách khỏi gold):** `.../derived_classify/2026-11-11_classes.jsonl` (713 mốc derived; trường `class`, `why`, `anchor`, `quote`).
- **Mã:** `local/derived_classify.py` (gitignore); bản sao `.../derived_classify/derived_classify.py.copy`. Chạy: `python3 -I local/derived_classify.py [--out-tag TAG]` từ gốc repo; không gọi API.
- Nếu sau này đổi cờ trong gold, phải qua bản chụp này để khôi phục.

## 3. Logic (đọc `local/derived_classify.py`)
Mốc phải có cờ `derived_date` (không kèm `approximate_date`/`source_inconsistent`), không BC; xét mọi quote vai `date`/`both`. Thứ tự quyết định:
1. quote có năm: `c_exact_day`/`c_exact_month` (quote chứa đủ ngày/tháng/năm trùng `date`: cờ có vẻ thừa, **chưa kiểm chứng**) hoặc `c_year_in_quote`; năm viết tắt (1984–85): `b_abbrev_year`.
2. từ tương đối mạnh trong câu (following, next, later, same, that year, ...): `b_relative`.
3. quote không có ngày+tháng (grain day) hoặc tháng (grain month) khớp `date`: `x_no_day_month`, `x_dm_mismatch`, `x_month_mismatch`; grain năm: `x_year_grain`; ngày không tồn tại ("31 November"): `x_invalid_day`.
4. **Neo năm** trong CÙNG chunk, trước quote: năm đứng ngay sau tháng hoặc giới từ ngày, bằng năm của `date`, giữa neo và quote không có năm khác, tháng nhắc giữa chúng không giảm (không qua năm mới). Không có neo: `b_no_anchor`, hoặc `b_anchor_prev_chunk` (neo ở chunk liền trước, chỉ ghi nhận, không tính a); neo khác năm: `b_anchor_year_differs`; tháng giảm: `b_month_rollover`; ngữ cảnh neo lạ: `b_anchor_context`.
5. Qua hết: `a_day` (grain ngày) hoặc `a_month` (grain tháng). Biến thể cần đọc thêm, KHÔNG tính a chặt: `a_weakrel_*` (có từ yếu before/after/until/then/since/while/when), `a_far_*` (neo cách quote > 300 ký tự hoặc > 2 dấu câu).
Loại a chặt = `a_day` + `a_month`. Chọn "cùng chunk" vì `decisions/14` mục 12 chốt: năm phải suy từ chunk khác thì không cho.

## 4. Kết quả trên test_clean (713 mốc derived; gold: rev cho 50 trang session 1–10, sub cho 136 trang còn lại)
`c_year_in_quote` 186, `b_relative` 132, `b_no_anchor` 89, `x_year_grain` 51, `b_anchor_prev_chunk` 50, `a_day` 38, `x_no_day_month` 30, `c_exact_month` 26, `c_exact_day` 23, `a_far_day` 13, `a_weakrel_day` 13, `b_month_rollover` 13, `a_month` 11, `x_month_mismatch` 9, `b_anchor_year_differs` 7, `a_weakrel_month` 7, `x_dm_mismatch` 6, `b_anchor_context` 3, `a_far_month` 2, `a_weakrel_day_far` 2, `a_weakrel_month_far` 1, `x_invalid_day` 1.
- **a chặt = 49/713 (6,9%).** Nếu thêm a_far và a_weakrel: 88.
- **Trang U-boat: phát hiện quan trọng.** Chunk của U_101 (ví dụ `#6` "She sailed again from Kiel on 21 May ... On 22 May ...") KHÔNG chứa năm nào; năm 1940 chỉ có ở chunk khác hoặc tên trang. Vì vậy 29/74 mốc U_101 rơi vào `b_no_anchor`, 19 `b_relative`, chỉ 3 `a_day`. Nhận định ở `docs/eval/10` mục 10.5bf ("năm lấy từ đầu đoạn") là **sai** (đã đính chính ở đó): đa số mốc U-boat là năm suy từ chunk khác, nên không thuộc a.
- Hệ quả: nới luật cho loại a chặt chỉ cứu được rất ít mốc (khoảng 7% mốc derived, khoảng 49 trên 6236 mốc gold); không giải quyết vấn đề ít câu ở trang U-boat.

## 5. Đã đọc / chưa kiểm chứng
- Đã đọc tay: toàn bộ 51 mốc `a_day` và 14 `a_month` của lần chạy đầu (trước khi thêm `a_far`, `x_invalid_day`): neo năm và quote hợp lý ở các ca đọc; phát hiện 1 ca ngày không tồn tại ("On 31 November", U_101 e33) và các neo xa (Audie_Murphy e15, U_101 e37: cách 400 ký tự/5 câu) nên tách `a_far`.
- Rủi ro còn lại của loại a (mã không thấy được): năm của neo thuộc sự kiện khác chuỗi thời gian (ví dụ "launched on 12 May 1941 and ... commissioned on 23 August" giả định cùng năm 1941).
- Chưa đọc: `a_far_*`, `a_weakrel_*` (23 mốc), các lớp `c_*`, `b_anchor_prev_chunk` (50 mốc: có thể cứu nếu quyết cho chunk liền trước), mẫu của `b_no_anchor`/`b_relative` để tìm ca phân loại nhầm (đã xem 6 mẫu mỗi lớp: vài ca "then"/"that year" nằm ở b_relative theo mã).
- Chưa làm: chạy trên tune/valid gold (`batch*/rev`), chưa đo số câu thực sự cứu được.
