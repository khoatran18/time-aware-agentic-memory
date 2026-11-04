# batchV6 (valid set, seed 7206, GUIDE_v7)

10 trang từ `reserved_valid.json`. Haiku 313 mốc; sau vá 312 (+4, −5). `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV6.py`.

| Trang | Haiku | Sau sửa |
|---|---|---|
| Chemnitz | 49 | 48 |
| Escadron_de_Chasse_1_2_Cigognes | 36 | 36 |
| Fergie_singer | 54 | 54 |
| Gleaston_Castle | 16 | 12 |
| LB_amp_SCR_E4_class | 12 | 12 |
| La_Japonaise_painting | 9 | 9 |
| SV_Darmstadt_98 | 44 | 44 |
| Saadat_Hasan_Manto | 34 | 34 |
| Sergio_P_rez | 33 | 37 |
| Wilhelm_K_lz | 26 | 26 |

## Sửa lỗi
- Gleaston e3 và e8: quote thiếu khoảng trắng trước dấu phẩy so với chunk → chép lại nguyên văn.
- Darmstadt e8: `check.py` coi "1963 on into the 70s" là mốc thập kỷ → rút quote và text về mốc 1963.
- Pérez (sub e25): quote "first point for Force India" cắt sai → sửa.

## Mốc thêm / bỏ
- Thêm (Pérez): 1997 hạng Youth Class kart, 2000 Shifter 80cc, 2002 á quân quốc gia Shifter 125cc, 2012-09-28 xác nhận thay Hamilton ở McLaren.
- Bỏ: Gleaston e9–e12 (tranh khắc/vẽ lâu đài của Buck 1727, Close 1805, Green 1809, Waugh 1860: sự kiện của tác phẩm); Chemnitz e47 (buổi hòa nhạc miễn phí 2018, sự kiện của thực thể khác).

## Quyết định tự đặt (không có trong GUIDE_v7)
- Fergie: không ghi phát hành, tour và đĩa đơn của Black Eyed Peas hay Wild Orchid (trừ gia nhập/rời nhóm); không ghi ngày sinh con (2013-08-29).
- Chemnitz: ghi kết nghĩa thành phố, nhiệm kỳ thị trưởng, bầu cử thị trưởng/hội đồng; không ghi dân số, Auto Union 1932.
- Darmstadt: ghi từng chức vô địch giải khu vực và Hessen Cup; không ghi thống kê mùa (undated_mentions).
- Manto: các tuyển tập năm 1955 giữ nguyên, nhưng nguồn chỉ nêu năm nên có thể xuất bản sau khi ông mất (1955-01-18); xem CLOUD_STATE.md.

## Session chính đọc kiểm và vá thêm (`tools/fix_V56.py`, chạy sau `patch_bV6.py`)
Sau khi đọc kỹ các trang dài và chạy `gap.py`, mình thêm 16 mốc và bỏ 7 mốc Manto; V6 từ 312 lên 321. `DIR=rev check.py` = 0 lỗi.
- Sergio_P_rez (+7): A1GP 2006-07 và GP2 Asia 2008-09 (cờ `approximate_date`); bục nhận giải Nga 2015, Monaco 2016, Azerbaijan 2018 (cờ `derived_date`); Force India bị quản lý và bị mua lại 2018.
- LB_amp_SCR_E4_class (+8): Hellingly bị hư hại 1942 và phế 1944-07, No. 2510 thử ở Isle of Wight 1947, đầu máy bảo tồn No. 32473 (rút 1971, chạy lại 1997, sơn lại 2005, rút 2008-05, xong đại tu 2010-01).
- Gleaston_Castle (+1): 1291 manor Aldingham thuộc dòng Harrington.
- Saadat_Hasan_Manto (−7): bỏ các tuyển tập và truyện ghi năm 1955 (ông mất 1955-01-18; có thể là di cảo, quy ước 12); chuyển vào `undated_mentions`. Đây là lựa chọn của mình, chờ người dùng xác nhận.
- Chemnitz, Fergie, Darmstadt, Külz, Escadron, La Japonaise: đọc `gap.py` và danh sách mốc, không thấy mốc sót đáng kể (các câu còn lại là thống kê, kết quả mùa, mốc của tổ chức khác).
