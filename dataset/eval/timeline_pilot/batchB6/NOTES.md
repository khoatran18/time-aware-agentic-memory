# batchB6 (seed 7106, reserved_B.json mở rộng 108 trang)

Trang (10): German_submarine_U_96_1940 (57 chunk), Panair_do_Brasil, Mike_Lee_American_politician (75 chunk), Orchard_Supply_Hardware, Wetten_dass, Rainier_Brewing_Company, Milan_Metro_Line_3, MS_GNV_Azzurra, Sergey_Sirotkin_racing_driver, Line_15_Beijing_Subway.

## Số liệu (mốc)
- Haiku viết: 343. Bỏ 4. Thêm 9. Sau sửa: **348** (`tools/patch_bB6.py`, `DIR=rev check.py` = 0 lỗi).
- Từng trang sau sửa: U-96 74, Mike Lee 57, Panair 43, Sirotkin 33, Orchard 32, Azzurra 31, Rainier 31, Wetten 29, Milan 11, Line 15 7.
- Haiku `DIR=sub` lúc đầu: 6 lỗi (U-96 5 quote both thiếu năm 1941; Panair e38 thiếu bộ chunk date).

## Bỏ (4)
- U-96 e14, e25, e49, e70: tàu bị đánh chìm / tàu nhận người ốm mà tên bị mất trong nguồn (quy ước: tên mất không thành mốc "không rõ tên"); thêm một dòng undated nêu cụ thể. e20 giữ, sửa text thành Black Osprey (tên có ở câu sau).

## Sót (9)
- Sirotkin 6: danh hiệu Formula Abarth châu Âu 2011, thắng Auto GP đầu 2012, thắng FR3.5 đầu 2014, thắng GP2 đầu 2015, điểm F1 đầu tiên 2018, thông báo rời Williams 2018.
- Orchard 1 (đóng 17 cửa hàng 2013-08). Panair 1 (Voo da amizade kết thúc 1965). Mike Lee 1 (2010 tên lên lá phiếu sơ bộ).
- Haiku sót ít hơn B5 (2,6%): trang nhiều mốc đã được liệt kê kỹ; sót nằm ở "lần thắng/điểm đầu tiên" trong văn xuôi.

## Lỗi mã kiểm không bắt
- U-96: 5 mốc ghi flag đúng nhưng quote không có năm (mã kiểm bắt); các mốc ngày đơn của U-96 có `derived_date` hợp lý vì năm chỉ có ở câu đầu mỗi chuyến.
- Không thấy flag `derived_date` thừa đáng kể; Beugró-style "seasonal" không có ở B6.
- Wetten: ví dụ cược có ngày (2/1983, 11/1991, 10/1995, 11/2002) giữ như mốc work (theo (E)); 2018 "một buổi hồi sinh" ghi, kế hoạch 2021 không ghi.

## Quyết định theo quy ước cũ (chờ xác nhận)
- Mike Lee: giữ phiếu bầu/thư/đồng bảo trợ có ngày (C); không ghi ủng hộ ứng viên (Cruz 2016, Moore 2017), phát biểu/tweet (Captain Moroni, For the People Act, mulligan) và vị trí chính sách.
- Panair: tai nạn và sự cố từng chiếc máy bay, sự kiện của tác phẩm khác về hãng không ghi (vật mang / thực thể khác).
- Tên tàu mất trong nguồn: không ghi thành mốc (xem trên).
