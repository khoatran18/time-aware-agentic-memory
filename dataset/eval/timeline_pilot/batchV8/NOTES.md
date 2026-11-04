# batchV8 (valid set, seed 7208, GUIDE_v7)

10 trang từ `reserved_valid.json`, chạy cùng đợt 20 haiku với V7. Haiku 258 mốc; sau vá 266 (+8 ròng: thêm 9, bỏ 1 mốc trùng ở Myanmar). `DIR=sub check.py` = 0 lỗi, `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV78.py`.

| Trang | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|
| Anna_Ter_Avetikian | 17 | 0 | 0 | 17 |
| Big_Brother_Swedish_TV_series | 16 | 0 | 0 | 16 |
| Curt_von_Fran_ois | 29 | 0 | 0 | 29 |
| GCR_Class_11E | 7 | 1 | 0 | 8 |
| Harry_Holtzman | 23 | 1 | 0 | 24 |
| Myanmar | 75 | 3 | 0 | 78 |
| Nico_H_lkenberg | 29 | 3 | 0 | 32 |
| Niva_magazine | 17 | 0 | 0 | 17 |
| Pakistan_Football_Federation | 22 | 0 | 0 | 22 |
| Philip_A_Kuhn | 23 | 0 | 0 | 23 |

(Cột Thêm/Bỏ là chênh lệch ròng giữa `sub/` và `rev/`; Myanmar thêm 4 mốc và bỏ 1.)

## Mốc thêm
- Myanmar (100 chunk, haiku 75 mốc, khá đủ): Mrauk U thống nhất Arakan 1437, Hanthawaddy phục hưng 1740, Aung San lập Burma Independence Army 1940, U Thant làm Tổng thư ký LHQ 1961; bỏ mốc trùng "Multi-party elections (period end)" của 1952.
- Nico_H_lkenberg: 2006 hạng 5 giải F3 Đức, 2006-07 A1GP (cờ `approximate_date`), 2008-09 GP2 Asia ra mắt (cờ `approximate_date`). Harry_Holtzman: 1932 vận động đưa Grosz và Hofmann vào Art Students League. GCR_Class_11E: tai nạn 1927-02-27.

## Không ghi (quyết định có chủ đích)
- Harry_Holtzman: triển lãm và xuất bản sau khi mất (1990, 2013, 2014) theo quy ước 12; mục tài liệu tham khảo.
- Curt_von_Fran_ois: tượng dựng 1965 (sau khi ông mất 1944); Lüderitz mua đất 1883 (nhân vật khác).
- Niva_magazine: Marx mất 1904 (nhân vật khác), số thuê bao theo năm.
- Anna_Ter_Avetikian, Philip_A_Kuhn, Big_Brother_Swedish, Pakistan_Football_Federation: `gap.py` chỉ còn tài liệu tham khảo, thống kê hoặc mốc ngoài thực thể.
- Nico_H_lkenberg: kết quả từng chặng (Brazil 2012, Baku 2016), kỷ lục số chặng không podium 2017.

## Ghi chú
- Cùng đợt haiku với V7 (20 haiku song song); không có haiku nào gọi công cụ ngoài phạm vi.
