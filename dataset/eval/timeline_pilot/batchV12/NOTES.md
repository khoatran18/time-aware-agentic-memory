# batchV12 – ghi chú đọc kiểm (seed 7212, 10 trang)

Haiku ghi `sub/`; `tools/patch_bV12.py` sinh `rev/` (chạy lại được, ghi đè từ `sub/`). `DIR=rev check.py batchV12` = 0 lỗi.
Đã chạy `gap.py` cho cả 10 trang và đọc từng dòng; `view.py`/đọc chunk gốc cho Michel_Zink và Atlético; dò tay BC/AD/CE: không có mốc nào.

| Trang | Haiku | Thêm | Bỏ | Sau vá |
|---|---|---|---|---|
| Atl_tico_Madrid | 157 | 3 | 0 | 160 |
| Lou_Scheper_Berkenkamp | 34 | 0 | 0 | 34 |
| Master_General_of_the_Ordnance_Sweden | 94 | 0 | 0 | 94 |
| Maurizio_Sarri | 48 | 0 | 0 | 48 |
| Michel_Zink | 50 | 1 | 0 | 51 |
| Otto_Modersohn | 22 | 0 | 0 | 22 |
| Oumar_Niasse | 24 | 0 | 0 | 24 |
| Preston_Smith_governor | 20 | 0 | 0 | 20 |
| Richmond_Kickers | 31 | 0 | 0 | 31 |
| VFA_94 | 57 | 0 | 0 | 57 |
| **Tổng** | **537** | **4** | **0** | **541** |

## Mốc thêm
- Atl_tico_Madrid +`2017` (ownership_structure, chunk 4): chấm dứt hợp tác nhượng quyền với CLB ISL ở Kolkata ("in 2017 Atlético decided to end its franchise partnership"). Quyết định của chính CLB, có năm.
- Atl_tico_Madrid +`2017` (location, chunk 77): thôi chơi sân nhà tại Vicente Calderón ("until 2017"), cặp với mốc đầu tiên ở Wanda Metropolitano 2017-09-17 đã có.
- Atl_tico_Madrid +`2020-07` (location, chunk 78): sân Vicente Calderón bị phá, thay bằng công viên; giữ cùng cách ghi với Galatasaray V10 (sân cũ bị phá).
- Michel_Zink +`1972` (work, chunk 5): xuất bản La Pastourelle (Bordas); haiku bỏ sót cuốn đầu danh mục.

## Sửa định dạng / cờ (không đổi số mốc)
- Atl_tico_Madrid: e49, e79, e83 (nhiệm kỳ chủ tịch dạng "( 1946–47 )", "( 1964–80 )", "( 1980–82 )", quote không chứa năm kết thúc) → `derived_date`. e76, e77, e92: bằng chứng phụ ghi role `description` nhưng quote có năm → đổi `both`.
- Maurizio_Sarri e43 (2019, quote "end of the 2018–19 season"): `approximate_date` → `derived_date` (năm kết thúc suy từ mùa).
- Mọi trang: chuẩn hóa grain theo độ dài `date`, đánh lại id.

## Cố ý KHÔNG ghi (đã đọc, theo GUIDE_v7)
- **Atl_tico_Madrid**: chung kết/á quân (Cúp Winners' Cup 1963, European Cup 1974, Champions League 2014 và 2016, Copa del Rey 2000, á quân La Liga 1990–91, Copa 1921, 1926) là kết quả; thống kê (Real Madrid thắng La Liga 14 lần 1961–80, Adelardo 551 trận 1959–76, chuỗi 14 năm không thắng derby); Pichichi của Gárate 1969–71 (giải của cầu thủ); công ty Compañía Urbanizadora mua đất 1919, Real Madrid ứng cử Olympic 2016, Athletic Bilbao thắng cúp 1911 (thực thể khác); CLB Atletico Madrid Lahore 2020 (CLB khác, nhưng chương trình học viện Lahore 2018–19 đã ghi); sân đổi chủ "2016" (kế hoạch); Nike không logo nhà tài trợ 2002–2005 (mô tả thiết kế áo). Mùa giải và chuyển nhượng trong undated_mentions giữ nguyên.
- **Lou_Scheper_Berkenkamp**: ngày sinh con (1923, 1926, 1938); việc của chồng (Hinnerk Scheper gọi vào Bauhaus Dessau 1925, đóng viện 1933-07-20, nghĩa vụ quân sự 1942–45, bổ nhiệm 1945); Bauhaus đóng cửa 1932-10-01 và Triadisches Ballett 1922 (thực thể khác); các mục thư mục, tái bản, dẫn nguồn.
- **Master_General_of_the_Ordnance_Sweden**: gap.py không có dòng nào (mọi câu có năm đã được trích).
- **Maurizio_Sarri**: ý kiến/đánh giá của giới bình luận; Leipzig lập phòng hút thuốc 2018; thống kê mùa (Napoli hạng nhì 2015–16, 2017–18; Empoli 2012–13; Sansovino 2000–01...), vào undated vì nằm ngoài quy ước mới (chỉ danh hiệu, thăng/xuống hạng, đổi HLV). Danh hiệu cá nhân (Panchina d'Argento, d'Oro) đã được haiku ghi.
- **Michel_Zink**: tái bản (2001, 2006, 2009, 2019) ghi trong `text` của mốc gốc, không tách; Froissart dans sa forge ghi theo năm xuất bản 2006, không theo năm hội thảo 2004.
- **Otto_Modersohn**: Overbeck/Vogeler đến Worpswede 1893/1894 (người khác); bảo tàng Otto Modersohn ở Tecklenburg mở 2015 (sau khi mất); thư mục.
- **Oumar_Niasse**: trận EFL Cup đấu Sunderland 2017-09-20 (kết quả trận; mốc ra sân lại sau khi trở về Everton); số trận 2019–20 (thống kê); lệnh treo giò, cáo buộc FA (không ngày).
- **Preston_Smith_governor**: kết quả bầu cử 1968, 1970 (số phiếu); đổi nhiệm kỳ bốn năm 1974 (luật); Pressler chuyển đảng 1973, Koop chuyển Dallas 1986 (người khác); sân bay đổi tên 2004 (sau khi mất); sách xuất bản 1973 chỉ liệt kê trong nguồn tham khảo.
- **Richmond_Kickers**: tứ kết US Open Cup 2011, các trận 2007, 2008 (kết quả); đội Virginia Beach giải thể 2007, hai nhóm cổ động viên thành lập 2010 và 2020 (thực thể khác); hợp đồng phát sóng từ 2017, 2018, Selecta 1320 AM 2003–05 (đối tác phát sóng); màu áo "từ mùa 2001", Adidas "từ ít nhất 2009" (mô tả đồng phục).
- **VFA_94**: chuyến hải trình vòng quanh thế giới 1954 của phi đội thứ hai (thực thể khác); VA-94 đầu tiên giải thể 1949 (thực thể khác).

## Điểm theo quy ước mới (2026-11-04)
- Mùa giải: haiku đã ghi danh hiệu theo mùa của Richmond ("1998 Commissioners Cup", James River Cup), Atlético (1939–40, 1958–59, 1996–97), Niasse (Ouakam 2008–09), Sarri (2013–14, 2015–16, 2016–17 danh hiệu cá nhân); thống kê mùa không ghi.
- Tai nạn: VFA_94 e55 (va chạm trên không 2014-09-12 của F/A-18C với máy bay VFA-113) được giữ vì trang là về phi đội, không phải trang hãng; Atlético/Richmond không có.
- Không thấy haiku V12 nào báo gọi công cụ ngoài phạm vi.

## Điểm mơ hồ cần người dùng quyết
1. Sân cũ bị phá (Calderón 2020-07; Galatasaray V10 2011): ghi như `location` của CLB. Có muốn ghi không, hay chỉ ghi khi CLB bán/đổi chủ sân?
2. Richmond Kickers: hợp đồng phát sóng (WTVR 2017, ESPN+ 2018, USL YouTube 2014–2017) hiện không ghi vì xem là đối tác; nếu xem là sự kiện của CLB thì thêm vào.
3. Master_General_of_the_Ordnance_Sweden: giữ 94 mốc, trong đó hơn 70 mốc là cặp "takes office/leaves office" tách từ bảng, nên số mốc cho trang rất cao so với 13 chunk.
