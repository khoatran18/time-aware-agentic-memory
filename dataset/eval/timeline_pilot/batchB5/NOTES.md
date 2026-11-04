# batchB5 (seed 7105, reserved_B.json)

Trang (10): PEN_America, William_Dwight_Whitney, New_South_Wales_C38_class_locomotive, Beugró, Tyne_and_Wear_Passenger_Transport_Executive, Henri_Becquerel, Ferdinand_Schörner, Alexander_Mountbatten_1st_Marquess_of_Carisbrooke, George_Cambridge_2nd_Marquess_of_Cambridge, Aleksandra_Goryachkina.

## Số liệu (mốc)
- Haiku viết: 278. Bỏ 3. Thêm 33 (sót). Sau sửa: **308** (`tools/patch_bB5.py`, `DIR=rev check.py` = 0 lỗi).
- Từng trang sau sửa: Goryachkina 63, Beugró 58, Schörner 50, Whitney 49, Carisbrooke 27, Becquerel 22, Cambridge 17, C38 12, PEN 7, Tyne&Wear 3.
- Haiku `DIR=sub` lúc đầu: 4 lỗi quote ở Beugró (haiku tự sửa sau khi mình kiểm; patch vẫn ghi đè các quote đó cho chắc).

## Bỏ (3)
- Whitney e5 "đang sống ở Yale" (trạng thái, không phải mốc).
- Carisbrooke e19 "gia nhập RAF" (trùng cùng ngày với e20 được bổ nhiệm acting pilot officer); e13 "thăng captain năm 1915" thay bằng mốc 1915-07-15 (ngày thâm niên, derived_date).

## Sót (33)
- Whitney 10: sáu lần sinh con và hai lần con mất (ngày đầy đủ trong danh sách), kết thúc Atharva Veda 1857, kết thúc Century Dictionary 1891.
- Goryachkina 12: ba mốc 2011 (WIM, lần đầu giải châu Âu, Rudenko), PriFR 2008, đồng nhì U20 2012, ba IM norm (2013/2014/2015), bạc châu Âu 2017, thua vòng 2 WCh 2018, top 10 lần đầu 2018, bạc World Team 2019.
- C38 4 (Western Endeavour 1970-08, overhaul 3813 1972, phim 1974, Perth 1988-04). Becquerel 2 (27/02 và 02/03/1896). Carisbrooke 2 (captain 1915-07-15, con gái 1920). Cambridge 1 (con gái 1924). Beugró 2 (board game hết hàng 2009-12, thu hình mùa 6 từ 2010-09-27).
- Khối haiku sót nhiều nhất: danh sách con có ngày đầy đủ, các câu "bởi/before" trong văn xuôi dài, mốc phụ trong đoạn tiểu sử (IM norm, giải phụ).

## Lỗi mã kiểm không bắt
- PEN e4: flag approximate_date sai (nguồn ghi thẳng 2011; năm đó sai sự thật nhưng nguồn nói vậy). Mình bỏ flag, giữ 2011.
- Beugró e17: quote role both không chứa năm; sửa thành description + date.
- Haiku ghi hai đầu cho các khoảng "mùa phát sóng/ thu hình tải lên" ở Beugró; mình giữ cả hai đầu (khoảng giữa hai mốc ngày = hai mốc).

## Quy ước mới (chờ xác nhận)
- (F) Sinh/mất của con có ngày đầy đủ ghi là mốc `family` (theo B3 Friedman). Ngày mất vợ/chồng ghi khi xảy ra lúc nhân vật còn sống (Carisbrooke); không ghi nếu sau khi nhân vật mất (Cambridge).
- (G) Mốc xếp hạng/rating (đạt 2400, 2500, peak rating) không ghi vì là thống kê; "lần đầu vào top 10" ghi vì là thay đổi thứ hạng.
- (H) Danh hiệu "title norm" (IM, GM norm) ghi là `other` theo năm.
