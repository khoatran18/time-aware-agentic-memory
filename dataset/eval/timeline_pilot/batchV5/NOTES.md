# batchV5 (valid set, seed 7205, GUIDE_v7)

10 trang từ `reserved_valid.json`. Haiku 195 mốc; sau vá 200 (+6, −1). `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV5.py`.

| Trang | Haiku | Sau sửa |
|---|---|---|
| Arnolfini_Portrait | 11 | 11 |
| Eleni_Theocharous | 17 | 17 |
| Flatiron_Building | 19 | 20 |
| Gamvik | 6 | 7 |
| Helsingin_Sanomat | 12 | 12 |
| John_Plumbe | 33 | 34 |
| Penrhyn_Castle | 13 | 12 |
| Ruud_Lubbers | 26 | 28 |
| SECR_N_class | 28 | 29 |
| Steven_Ozment | 30 | 30 |

## Sửa lỗi
- `check.py` báo 1 lỗi ở `sub/`: Lubbers e10 (quote `description` chứa năm 1977) → đổi sang "serving from 8 June" + evidence `date` "8 September 1977".

## Mốc thêm / bỏ
- Thêm: Flatiron 1899 (tài sản Eno thanh lý, lô đất rao bán); Gamvik 1972-06 (xây trạm SOSUS trong đô thị); Plumbe 1829 (khảo sát tuyến đường sắt, cờ AP); Lubbers 1986 và 1989 (Nội các Lubbers II, III, cờ `derived_date`); SECR N 1977 (đầu máy bảo tồn No. 1874 chạy lần đầu).
- Bỏ: Penrhyn e4 (1833 bồi thường nô lệ cho chủ sở hữu, là việc của người khác).

## Quyết định tự đặt (không có trong GUIDE_v7)
- Flatiron: không ghi việc người thuê vào/ra (Fuller/Black 1910 và 1916, St Martin's Press 1959, Macmillan 2004/2017/2019); không ghi thay đổi luật xây dựng 1892.
- Arnolfini: không ghi kiểm kê 1523–4 và 1700 (chỉ liệt kê, không đổi chủ rõ ràng).
- SECR N: không ghi livery lẻ (1939, 1941, 1946), thử nghiệm và tai nạn từng đầu máy (1958); ghi livery và sửa đổi cả lớp.
- Gamvik: không ghi vụ rơi máy bay Twin Otter 1982 (sự kiện của máy bay).

## Session chính đọc kiểm và vá thêm (`tools/fix_V56.py`, chạy sau `patch_bV5.py`)
Cloud sửa rất ít so với số mốc sót. Sau khi đọc kỹ các trang dài và chạy `gap.py`, mình thêm 26 mốc; V5 từ 200 lên 226. `DIR=rev check.py` = 0 lỗi.
- SECR_N_class (+19): Maunsell làm CME 1913; các thí nghiệm 1924–1935 (bơm Worthington, bộ Anderson, van Marshall); trưng bày Wembley 1925-05; nguyên mẫu W class 1932; sơn lại 1939, 1941, 1946; thử đốt dầu 1947–1948; tai nạn 1958-04-04; đầu máy bảo tồn No. 1874 (rút 1998, sơn lại 2012, chuyển Swanage 2014, đại tu 2014-08).
- Flatiron (+6): thay đổi quy chuẩn xây dựng 1892, nhà hàng được mua 1911, St Martin's Press 1959, Macmillan thuê kín 2004, thông báo rời 2017-07, rời hẳn 2019-06. Đây là quyết định của mình (cloud không ghi chuyện người thuê): các mốc này nhắm vào tòa nhà.
- Gamvik (+1): 1982-03-12 máy bay Widerøe rơi gần Mehamn.
- Giữ nguyên, không ghi: các bài viết nghiên cứu về tranh Arnolfini (1857, 1934, 1997), kiểm kê 1523 và 1700; bồi thường nô lệ 1833 và phong nam tước 1866 ở Penrhyn; thứ hạng phát hành báo Helsingin Sanomat; chuyện nội các Lubbers sau khi rời chức.
