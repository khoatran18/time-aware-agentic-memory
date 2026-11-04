# batchV1 (valid set, seed 7201, GUIDE_v7)

10 trang từ `reserved_valid.json`. Haiku 451 mốc; sau vá 481 (+30, −0). `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV1.py`.

| Trang | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|
| Alex_McLeish | 51 | 2 | 0 | 53 |
| Dennis_Quaid | 64 | 0 | 0 | 64 |
| James_Marape | 30 | 1 | 0 | 31 |
| Jon_Gruden | 31 | 1 | 0 | 32 |
| Knox_Cunningham | 22 | 0 | 0 | 22 |
| Liga_Veneta_Repubblica | 38 | 0 | 0 | 38 |
| Lykkehjulet | 19 | 4 | 0 | 23 |
| Scottish_National_Party | 138 | 3 | 0 | 141 |
| USCGC_Southwind | 32 | 0 | 0 | 32 |
| Valladolid | 26 | 19 | 0 | 45 |

## Sửa lỗi
- `check.py` báo 3 lỗi quote ở `sub/`: McLeish e5 và e47 (quote `description` chứa năm → bỏ evidence phụ), SNP e41 (quote `both` thiếu 1974 → dùng evidence `date` "1974 was to prove ... annus mirabilis" + `description`, cờ `derived_date`).
- Quaid e36: text sai "ten times-plus" → "1,000 times the common dosage".

## Mốc thêm
- Valladolid (haiku sót nhiều nhất, trang 70 chunk): 1084 (cờ AP), 1092/1095 (tên được ghi nhận), 1241 đại học, 1469 đám cưới Isabella–Ferdinand, 1506 Columbus mất, 1554 Joanna nhiếp chính, công trình 1668/1730/1861/1890-09-29/1982, công ty ENDASA 1950, FASA 1953 và 1954 (hai năm mâu thuẫn trong nguồn, cờ `source_inconsistent`), TECNAUTO 1956, SAVA 1957, Iveco 1990, tuyến AVE 2007-12-22.
- Lykkehjulet: bốn lần đổi giá trị đỉnh của bánh xe (1989, 1990, 1999, 2001) như `format change`.
- SNP: 1983 thất vọng bầu cử, 2003 thách thức lãnh đạo Swinney bất thành, 2004 Sturgeon được bầu Depute Leader.
- McLeish: 1998 Hibs xuống hạng, 2007-03-24 trận đầu dẫn Scotland. Marape: 2020-11-17 ngân sách 2021 thông qua. Gruden: 2008-11-30 chiến thắng thứ 100.

## Quyết định tự đặt (không có trong GUIDE_v7)
- Trang thành phố (Valladolid): GUIDE nói "cơ sở vật chất, thương mại" ở giữa trang hay bị sót, nên mình ghi công trình, công ty thành lập, tuyến tàu, đại học; vẫn KHÔNG ghi lễ hội (Seminci 1956), giải đấu, thành lập/giải thể CLB thể thao, cuộc hôn nhân/cái chết của nhân vật thuộc thực thể khác trừ khi diễn ra tại thành phố.
- Danh sách "lãnh đạo hội đồng địa phương since 2017" của SNP: người khác, không ghi.
- Không ghi kế hoạch trong nguồn: Quaid được xác nhận đóng Reagan (2018-03, "would portray").
- Không ghi: ngày sinh con (Quaid 1992, 2007), phát biểu/phỏng vấn (Quaid 2002/2018/2020, McLeish 2013), tin đồn rời Genk (2015-03), thống kê dân số, nhiệt độ kỷ lục.
- Không ghi mùa/kết quả mùa (Gruden từng mùa, McLeish "2000–01", Rangers theo mùa) → `undated_mentions`.

## Ghi chú
- Haiku James_Marape gọi nhầm công cụ Claude Docs; bị từ chối, không tác dụng phụ.
- SNP là trang dài nhất (138 mốc haiku, chủ yếu danh sách lãnh đạo); haiku bắt đủ các danh sách.
