# Ingest và precision: việc chưa chốt

Đã chốt: precision ingest **bỏ qua mốc không ngày** (`decisions/14` mục 1). Bản 9 tập C tính lại: chặt 67,0%, vừa 79,2%, rộng 100% (mẫu số 197).

## Chưa chốt
- **Định nghĩa `derived_date` lệch giữa gold và ingest.** Gold: Haiku gắn cờ theo quy ước "quote không chứa năm" (tools/check.py bỏ kiểm quote-chứa-năm cho mốc `derived_date`), nên cờ phủ nhiều tình huống. Ingest (`pass3_p9.py`): mã gắn khi chuỗi năm không nằm trong chunk. Phân bố 1165 mốc `derived_date` của gold: 325 năm có trong quote (cờ vì tháng/ngày hoặc lý do khác), 98 quote là năm viết tắt, 430 năm trong chunk nhưng không trong quote, 312 năm không có trong chunk bằng chứng. Ingest chỉ gắn cờ gần như nhóm cuối (và một phần nhóm năm viết tắt); việc ghép gold-ingest dựa vào ngày trùng chứ không dựa cờ, nên lệch chỉ ảnh hưởng báo cáo theo cờ. Cần chọn một định nghĩa.
- **Năm viết tắt** ("1827–29" → 1829): `pass3_p9.py` bỏ mốc nếu chuỗi năm không có trong trang (`year_not_in_page`); [1] (`chain_complete.py`) coi là `year_not_in_chunk`. Cần nhận dạng năm viết tắt ở cả hai nơi.
- **Gộp mốc trùng trong timeline của ingest** (một sự kiện trích hai lần từ hai chunk, hoặc hai ngày cho cùng chuyện): chưa thiết kế. Ảnh hưởng câu hỏi dạng đếm/`list`.
- **`source_inconsistent`:** ingest chưa nhận diện và chưa từng chạy trên trang có mốc này (tập C có 0). Chưa biết ingest ra một hay hai mốc. Chưa chốt có thêm nhận diện hay không (ranh giới với Cơ chế 3, xem `03`).
- **Precision theo cờ:** đề xuất báo riêng `derived_date` (1165 mốc) và `approximate_date` (389 mốc); với `source_inconsistent` (156 mốc, 73 trang) mức chặt chấp nhận cả ngày thay thế, recall tách riêng khỏi mẫu số hoặc báo riêng. Chưa chốt.
- Bản 8 chưa tính lại theo quy tắc mới; chỉ một người đọc, chưa có người đọc thứ hai; chưa kiểm số cũ có đối chiếu với `undated_mentions`.
- Đối chiếu sự kiện ingest không ngày với `undated_mentions`: chưa có.
- Chọn model ingest (hiện chỉ DeepSeek vì chi phí); ingest p9 hay v10.
