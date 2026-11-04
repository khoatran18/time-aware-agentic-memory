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
