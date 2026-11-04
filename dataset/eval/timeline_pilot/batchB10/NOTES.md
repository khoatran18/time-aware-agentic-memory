# batchB10 (seed 7110) — ghi chú

Haiku viết 273 mốc (sub/), sau `tools/patch_bB10.py` còn 291 mốc trong `rev/`; `DIR=rev check.py` 0 lỗi. `gap.py` chạy cho cả 10 trang, các câu còn lại đều thuộc thực thể khác hoặc là kế hoạch/thống kê.

| Trang | haiku | sau vá |
|---|---|---|
| Andrew_Mellon_Building | 8 | 11 |
| Eastern_Army_Division | 27 | 28 |
| Karls_y | 17 | 18 |
| Keith_Emerson | 61 | 66 |
| Lowell_State_College | 33 | 34 |
| Sarah_Palfrey_Cooke | 28 | 30 |
| Senate_of_Canada_Building | 13 | 14 |
| Sevilla_FC_Puerto_Rico | 17 | 17 |
| Swedish_Air_Force_Flying_School | 36 | 40 |
| Werner_Hartmann | 33 | 33 (-1 +1) |

## Thêm (sót)
- Mellon: 1922 và 1937 (thời gian ở của Andrew Mellon), 2010 (hội đồng rút tòa nhà khỏi thị trường, derived_date).
- Eastern Army: 2000 huy chương. Karlsøy: 1909 đổi chính tả tên (derived_date).
- Emerson: album 1973, 1992, 1994; phẫu thuật ghép dây thần kinh 1993; 2010-09 thông báo mổ.
- Lowell: 1914 hai người Mỹ gốc Phi đầu tiên tốt nghiệp. Palfrey: con gái 1942-12, con trai 1952-12 (family, quy ước L).
- Senate: 2011-01-29 gỡ mảnh Tường Berlin. Swedish: 1658, 1910, 1983 và 1996 (trường khí tượng, "between X and Y" nhưng đây là hai sự kiện thực thể bắt đầu/kết thúc).
- Werner: bắt đầu chuyến tuần tra đầu 1939-08-19.

## Sửa / bỏ
- Emerson e39: evidence trỏ nhầm chunk 9, chuyển sang chunk 58 (haiku `check` báo quote không nguyên văn).
- Werner e16 (1938, quote không có năm) bỏ; e15 thành một mốc approximate_date "1937-38" (quy ước "giữa X và Y" = một mốc). e29: chữ sai "Diamonds to Knight's Cross" sửa thành U-boat War Badge with Diamonds.

## Quy ước dùng
- I,J,K,L,M,N,O như handoff. Sự kiện của thực thể khác không ghi: lịch sử ga Broad Street/nhà ga trước (Senate), mốc của người khác (Barker 1980, Halleren 1942 ở Lowell). "Mid-1990s", "late 1960s" không có năm nên để undated.
- Kết quả trận (Sevilla 2008) chỉ ghi mốc đầu và nhà vô địch; mùa 2011 không ghi.
- Lowell: 1959/1960 và 1907/1908 giữ cờ source_inconsistent của haiku.
