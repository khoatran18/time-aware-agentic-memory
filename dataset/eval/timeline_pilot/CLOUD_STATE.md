# CLOUD_STATE (nhánh cloud/valid-timelines)

Cập nhật: 2026-11-04, sau batch V5 và V6.

## Đã xong
- batchV5 và batchV6, mỗi batch 10 trang: haiku soạn `sub/`, vá bằng `tools/patch_bV5.py`, `tools/patch_bV6.py` ra `rev/`. `DIR=rev check.py` = 0 lỗi cả hai batch. `gap.py` đã chạy 20 trang.
- Tổng: V5 200 mốc, V6 312 mốc (sau vá).
- Trang valid còn lại trong `reserved_valid.json` (chưa dùng trong bất kỳ `*/in`): 107.

## Quyết định tự đặt cần người dùng xác nhận
1. Việc người thuê vào/ra tòa nhà (Flatiron): không ghi. Cân nhắc nếu muốn ghi (Macmillan rời 2019, St Martin's 1959).
2. Sự kiện của vật được vẽ/khắc (tranh khắc lâu đài Gleaston): không ghi.
3. Kiểm kê trong lịch sử sở hữu tranh (Arnolfini 1523–4, 1700): không ghi vì không nêu đổi chủ.
4. Phát hành và tour của nhóm nhạc mà nhân vật là thành viên (Fergie/Black Eyed Peas, Wild Orchid): không ghi.
5. Manto: các tuyển tập ghi năm 1955 (e27–e33 trong `rev/`) có thể xuất bản sau 1955-01-18; GUIDE_v7 cấm di cảo sau khi mất, nhưng nguồn chỉ ghi năm nên giữ. Cần quyết định bỏ hay giữ.
6. Pérez: các kết quả "điểm đầu tiên / bục đầu tiên cho Force India" 2014 giữ như mốc "lần đầu"; năm lấy từ tiêu đề mục, không có ngày chắc chắn.

## Cạm bẫy gặp
- Haiku sót mốc ngày lẻ trong các câu về sở hữu/thương mại; gap.py bắt được 1899 Flatiron, 1972 Gamvik, 1986/1989 Lubbers.
- Quote bị mất khoảng trắng trước dấu phẩy ("5th Baron Harington" vs "5th , Baron"): `check.py` đòi nguyên văn, chép từ chunk.
- `check.py` coi cụm "1963 on into the 70s" là mốc thập kỷ; cắt quote ngắn lại.
- Id trong `sub/` khác `rev/` sau khi `fin()` đánh số lại: khi vá, dùng id của `sub/`.
- Vài haiku gọi nhầm công cụ MCP ngoài phạm vi (list_triggers, list_environments, list_sessions, archive_session với id "none", send_message thiếu tham số); chỉ đọc hoặc bị từ chối, không có tác dụng phụ.
- batchV4 trong repo thiếu `sub/Vladimir_Bukovsky.json`, `rev/` và `NOTES.md` (không sửa, ngoài phạm vi). mk_batch đã loại trang V4 nên V5/V6 không trùng.
