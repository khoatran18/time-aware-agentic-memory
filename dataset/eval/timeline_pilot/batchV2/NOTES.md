# batchV2 (valid set, seed 7202, GUIDE_v7)

10 trang từ `reserved_valid.json` (mk_batch giờ lấy cả trang dưới 8 chunk). Haiku 342 mốc; sau vá 355 (+16, −3). `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV2.py`.

| Trang | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|
| B_o_B | 80 | 5 | 2 | 83 |
| Dixie_State_University | 34 | 4 | 0 | 38 |
| European_Central_Bank | 37 | 1 | 0 | 38 |
| James_Lanier | 22 | 5 | 0 | 27 |
| Numedal_Line | 18 | 0 | 1 | 17 |
| Stefano_Pioli | 31 | 0 | 0 | 31 |
| Sydney_Trains_K_set | 20 | 1 | 0 | 21 |
| The_Clitheroe_Kid | 10 | 0 | 0 | 10 |
| Vologda_Governorate | 73 | 0 | 0 | 73 |
| Zerelda_James | 17 | 0 | 0 | 17 |

## Sửa lỗi
- `check.py` báo 10 lỗi ở `sub/`: B_o_B 8 (e35, e40, e44, e48, e55, e57, e78 thiếu evidence `date` vì năm lấy từ câu khác; e36 quote `description` chứa năm) → viết lại evidence thành cặp `date` + `description`, cờ `derived_date`; Sydney e9 thiếu " ." cuối câu; Clitheroe e3 quote `date` không chứa 1957 → dùng "originally broadcast between April 1957".
- Numedal e18: haiku gán ngày 2014-04 cho việc nâng cấp tà vẹt; nguồn chỉ nói "sau vụ trật bánh tháng 4/2014" → đổi text thành mốc trật bánh, bỏ `derived_date`.

## Mốc bỏ
- B_o_B e11 và e20 ("bắt đầu/kết thúc chuỗi mixtape 2007-2008"): trùng với từng mixtape đã ghi riêng.
- Numedal e16 (1993 NSB chở sỏi và gỗ): thống kê vận chuyển, không phải sự kiện.

## Mốc thêm
- B_o_B: 2009 "Nothin on You" đứng số 1 Mỹ/Anh, 2010-08-14 được công bố mở màn tour Paramore, 2011-03-22 bài hát trong trailer Crysis 2, 2014-10-07 ca sĩ ký hợp đồng với hãng No Genre của anh, 2016-08-02 album debut đạt 2x platinum.
- Dixie: 2014-12 giáo sư Davenport nhận thông báo sa thải, 2016 đội nam bóng đá lần đầu vô địch PacWest, 2019-08 chi hội Kappa Sigma, 2020-01 sân vận động đổi tên Greater Zion (bỏ hai dòng undated tương ứng).
- James_Lanier: tử vong của 5 người con trưởng thành (1885, 1895, 1903, 1910, 1926) theo quy ước (L).
- ECB: 2019-07 lãnh đạo EU đề cử Lagarde. Sydney: 1988 các bộ 4 toa thôi chạy ghép 8 toa.

## Quyết định tự đặt (không có trong GUIDE_v7)
- (L) áp nguyên văn: ngày mất của con ghi `family` kể cả sau khi cha/mẹ mất (Lanier ×5; Zerelda giữ 1915, 1921, 1922, 1934 do haiku ghi). Nếu người dùng muốn giới hạn như vợ/chồng ("chỉ khi nhân vật còn sống") thì bỏ 5 mốc Lanier và 4 mốc Zerelda.
- ECB: chỉ ghi sự kiện của chính ECB. Không ghi các nước gia nhập khu vực euro (Greece 2001... Lithuania 2015, thuộc Eurozone), vụ phát hành promissory note của Ireland, báo cáo Nghị viện châu Âu 2014 (chỉ trích về thực thể), cáo buộc can thiệp trưng cầu Hy Lạp 2015, số liệu mua trái phiếu, quy mô QE, TLTRO 1.3 nghìn tỷ.
- ECB e1 (1219-06-01) giữ với `source_inconsistent`: nguồn tự ghi "1 June 1219" cạnh "1 June 1998".
- Vologda: sự kiện của thực thể khác không ghi (Union of Northern Oblast Communes 1918-1919, thánh Stephen of Perm 1383).
- Numedal: các mốc Sørland Line 1871, cuộc họp các xã 1873, quyền xây nhà máy điện 1907, mức tần suất 1945/1947 không ghi.
- Pioli: Astori mất 2018-03-04 và Ibrahimović đến 2020-01 là việc của người khác; kết quả theo mùa (2003–04, 2008–09, hạng ba 2014–15) vào `undated_mentions`.
- Zerelda: em trai tự tử 1895 không ghi (anh chị em, không phải con).
- B_o_B: ghi các phát hành đơn lẻ/mixtape/EP có ngày (đúng với mẫu trang); không ghi phát biểu/phỏng vấn (2011-12-01, 2012-04, 2015-12-07, 2016-01 niềm tin Trái Đất phẳng), kết quả bán hàng tuần đầu, thứ hạng, tweet tiết lộ tên album.
- Sydney K set là một lớp toa: tai nạn/hành trình từng bộ không ghi (haiku không ghi); giữ các mốc chuyển depot/tuyến của cả lớp.

## Ghi chú
- Haiku V2 không có gì bất thường; B_o_B (71 chunk) và ECB (100 chunk) là hai trang dài, haiku sót ít (1–5 mốc).
