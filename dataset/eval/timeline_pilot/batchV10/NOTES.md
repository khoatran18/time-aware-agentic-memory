# batchV10 (valid set, seed 7210, GUIDE_v7)

10 trang từ `reserved_valid.json`, chạy 10 haiku sau khi V9 đã sửa xong (không gộp với V9). Haiku 558 mốc; sau vá 558 (+0, −0; chỉ thêm 2 cờ `derived_date`). `DIR=sub check.py` = 2 lỗi, `DIR=rev check.py` = 0 lỗi; `gap.py` và `view.py` đã chạy cả 10 trang và đọc từng câu gap. mtime `sub/` ổn định (sửa lần cuối 12:46:14, kiểm 12:48). Patch: `tools/patch_bV10.py`.

| Trang | Chunk | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|---|
| Alfred_Drury | 21 | 29 | 0 | 0 | 29 |
| Federation_of_the_Greens | 43 | 106 | 0 | 0 | 106 |
| Fernand_Braudel | 44 | 44 | 0 | 0 | 44 |
| Galatasaray_S_K_football | 65 | 20 | 0 | 0 | 20 |
| Gerhard_Schr_der | 87 | 96 | 0 | 0 | 96 |
| International_Mathematical_Union | 29 | 129 | 0 | 0 | 129 |
| Liina_Tennosaar | 12 | 29 | 0 | 0 | 29 |
| Meg_Whitman | 61 | 41 | 0 | 0 | 41 |
| Writers_Guild_of_America_West | 18 | 24 | 0 | 0 | 24 |
| Y_Combinator | 25 | 40 | 0 | 0 | 40 |

## Sửa lỗi
- Gerhard_Schr_der e65 (2005-10-10, thỏa thuận đại liên minh) và Federation_of_the_Greens e87 (2015-06, thượng nghị sĩ De Pin gia nhập): quote `both` không chứa năm vì năm nằm ở câu trước → thêm cờ `derived_date` theo GUIDE.

## Mốc thêm
- Không có. Mình đã đọc từng câu `gap.py` in ra cho cả 10 trang và danh sách mốc của từng trang; không câu nào vừa có năm rõ vừa thuộc thực thể chính mà haiku chưa ghi. Lý do cho các trang dài và các câu gap chính nằm ở mục dưới.

## Không ghi (quyết định có chủ đích)
- Galatasaray_S_K_football (65 chunk, 20 mốc): haiku ít nhưng đúng. Gần như mọi năm trong trang là mùa giải ("1999–2000", "2014–15", "1986–87", "1988–89"), danh sách nhà cung cấp áo/nhà tài trợ theo khoảng mùa, danh hiệu theo mùa → `undated_mentions` (20 mục). Không ghi: 1921 sân Taksim (của cả thành phố), 1952 Istanbul Professional League (của liên đoàn), 1993 giảm sức chứa sân, 2011 phá sân Ali Sami Yen (đã có mốc chuyển sang sân mới), 2002 World Cup (đội tuyển), 2012/2019 khảo sát cổ động viên.
- Meg_Whitman (61 chunk, 41 mốc): không ghi 2002 PayPal và 2005/2009/2011 Skype (việc của eBay), 2010 Giving Pledge (từ chối, phát biểu), 2020 Quibi đóng cửa và bài phát biểu DNC 2020 (ủng hộ ứng viên), 2008 NYT nhận xét, 2013 đổi quan điểm Prop 8 (phát biểu), 2010 Santillan (người khác), 2004 quyên góp cho Boxer, các thống kê doanh thu/nhân viên.
- Gerhard_Schr_der (87 chunk, 96 mốc): không ghi 2005-10-24 bảo lãnh 1 tỷ euro cho Nord Stream (hành vi của chính phủ), 2005-11-14 kêu gọi SPD ủng hộ liên minh, 2001 tuyên bố đoàn kết sau 11/9, 1999 phát biểu "great power", 2003-10 Chirac đại diện Schröder (việc của Chirac), 1999 Đức giữ chủ tịch luân phiên EU (việc của nước Đức), 2017-11 Paradise Papers (bài điều tra về ông), 2007-06 điếu văn Immendorff, 1982 lời nói lúc say; chương trình Agenda 2010 và nhiều chính sách vào `undated_mentions`.
- Federation_of_the_Greens (43 chunk, 106 mốc, hầu hết là bảng lãnh đạo): không ghi kết quả bầu cử (1992, 1994, 2004, 2006, 2014), bầu cử vùng 2018/2020, 2012 Bonelli ứng cử thị trưởng Taranto (vẫn chỉ là ứng cử), Pecoraro Scanio làm bộ trưởng 2006–2008 và Cento làm thứ trưởng (chức vụ chính phủ của cá nhân).
- Fernand_Braudel: 1950 "sau 1950" (nhận xét), 1943 sáp nhập địa danh quê, 2011 khảo sát History Today, các niên đại chu kỳ (1250–1510...) là mô tả chung; 18 mục `undated_mentions` giữ nguyên (thành viên viện hàn lâm, bằng danh dự không có năm).
- Alfred_Drury: 1904 "by 1904 established" (nhận xét), 1914 huân chương chiến tranh Rhodes University (đài tưởng niệm không có năm khởi công).
- Writers_Guild_of_America_West: 1988 "strike showed..." và số liệu đủ tư cách bỏ phiếu từ 2006 (thống kê).
- Y_Combinator: 2021 tổng giá trị, 2019 số công ty đầu tư (thống kê), 2016 kế hoạch thăm 11 nước ("would visit"), 2005/2007 câu nói của Graham/Zuckerberg, 2017–2019 một khoảng gộp nhiều chương trình (`undated_mentions`).
- Liina_Tennosaar: 1985 sinh con trai (quy ước: không ghi ngày sinh con); kết hôn lần hai với Sten Zupping không có năm.
- International_Mathematical_Union: chunk 28 là liên kết ngoài; 2015/2018 tuổi nhiệm kỳ đã có trong bảng chức vụ.

## Ghi chú
- Các bảng lãnh đạo (IMU 129 mốc, Greens 106) chiếm phần lớn số mốc: mỗi nhiệm kỳ tách thành hai mốc bắt đầu và kết thúc đúng GUIDE.
- Haiku Whitman, Galatasaray, Braudel, Schröder, Greens, IMU, Y Combinator báo "xong" mà không nêu tên trang; đã khớp theo tên file `sub/`.
- Haiku Greens báo chưa tự kiểm tra cú pháp JSON; `check.py` đọc được cả 10 file.
