# batchV11 – ghi chú đọc kiểm (seed 7211, 10 trang)

Haiku ghi `sub/`; `tools/patch_bV11.py` sinh `rev/` (chạy lại được, ghi đè từ `sub/`). `DIR=rev check.py batchV11` = 0 lỗi.
Đã chạy `gap.py` cho cả 10 trang và đọc từng dòng; `view.py` cho Sturrock và Levski (chunk không mốc); dò tay BC/AD/CE (chỉ có "AD 69-81" trong tên luận án ở Broughton, không phải mốc).

| Trang | Haiku | Thêm | Bỏ | Sau vá |
|---|---|---|---|---|
| Affari_tuoi | 53 | 0 | 0 | 53 |
| Bayerisches_Armeemuseum | 53 | 0 | 0 | 53 |
| Edward_Adolf_Sonnenschein | 14 | 0 | 0 | 14 |
| John_J_Pettus | 14 | 0 | 0 | 14 |
| Marcia_Bunge | 28 | 0 | 0 | 28 |
| PFC_Levski_Sofia | 193 | 0 | 0 | 193 |
| Paul_Sturrock | 55 | 1 | 0 | 56 |
| Rachel_Ruysch | 12 | 0 | 1 | 11 |
| Thomas_Robert_Shannon_Broughton | 22 | 0 | 0 | 22 |
| William_Duncan_missionary | 12 | 0 | 0 | 12 |
| **Tổng** | **456** | **1** | **1** | **456** |

## Mốc thêm hoặc bỏ
- Paul_Sturrock +`2008-07` (other/health): công bố mắc Parkinson thể nhẹ (chunk 3). Mốc đơn lẻ của chính nhân vật mà haiku bỏ sót.
- Rachel_Ruysch −`2021-03` e12: đưa vào Rijksmuseum Gallery of Honor, vinh danh sau khi mất (GUIDE_v7: không ghi).

## Sửa định dạng / cờ (không đổi số mốc)
- PFC_Levski_Sofia: 4 mốc tháng bị haiku đặt grain `day` (e68, e69 `1969-01`; e100, e101 `1990-01`) → `month`. 16 dòng danh sách huấn luyện viên có năm viết tắt ("Boris Vasilev ( 1921–23 )", quote không chứa năm kết thúc) → thêm `derived_date` (e8, e13, e18, e33, e37, e50, e54, e58, e64, e72, e75, e82, e84, e91, e95, e109 là các mốc "rời chức"). Đã làm bằng hàm chung `abbr()` + chuẩn hóa grain theo độ dài `date` cho mọi trang.

## Cố ý KHÔNG ghi (đã đọc, theo GUIDE_v7)
- **Affari_tuoi**: khách quay US Deal or No Deal 2007-02-05 (Insinna xuất hiện trên bản Mỹ; việc của show khác, mơ hồ); bảng giá trị hộp "as of"; hippo prize mùa 2006–07 (undated).
- **Bayerisches_Armeemuseum**: kế hoạch mở rộng của Aichner 1992 (kế hoạch); "bất biến đến 2014", chuyển địa điểm dự kiến từ 2018 (kế hoạch); Hội Bạn bè (1967 thành lập, Dumann chủ tịch 1989–2016, từ chức 2016-08, bài Donaukurier 2017-10) là thực thể khác; báo cáo thường niên 2010–2014; Starfighter không năm.
- **Edward_Adolf_Sonnenschein**: tất cả "N editions between X and Y" (thống kê số bản in; năm xuất bản đã được haiku ghi ở các chunk khác); Who's Who 1907; hôn nhân không ngày (undated); William Swan Sonnenschein (anh/em) và công ty Swan Sonnenschein là thực thể khác.
- **John_J_Pettus**: dân số nô lệ 1850 (thống kê); Hiến pháp 1832, Foote 1853, Hội nghị ly khai 1861-01-07 (việc của thực thể khác/lập pháp).
- **Marcia_Bunge**: xuất bản lại (2005, 2011) ghi trong `text`, không tách mốc; mục viện sĩ/hội đồng không ngày vào undated.
- **PFC_Levski_Sofia**: kết quả cúp châu Âu theo mùa (1969–70, 1975–76, 1976–77, 1983–84, 1984–85, 1986–87, 2005–06, 2008–09, 2009–10, 2010–11, 2011–12, 2013–14), tứ kết, đánh bại Barcelona/Stuttgart (kết quả trận, thứ hạng); "chưa từng xuống hạng từ 1937", giải đầu tiên 1924 (thống kê/việc của giải); danh sách Cầu thủ xuất sắc nhất năm và vua phá lưới (giải của cầu thủ, thực thể khác); chuyển nhượng Vutov/Rodrigues 2013–14 (cầu thủ, không ngày cụ thể); danh sách cầu thủ.
- **Paul_Sturrock**: trận Wales U21 1977-02-09 (kết quả trận); xếp hạng nghiên cứu 2012 và phân tích Financial Times (bài đánh giá về nhân vật); Widdrington rời Southend 2010-12-15, bán Dodds 1999-12 (người khác); mùa 2007–08 vị trí giữa bảng; á quân cúp 1981–82, 1984–85, 1986–87, 1987–88 (á quân, không phải danh hiệu); thăng hạng Championship cùng Sheffield Wednesday và Plymouth (mùa không đặt được năm, có trong undated).
- **Rachel_Ruysch**: bán tranh 1999 (sau khi mất); thơ tưởng niệm 1750 (sau khi mất).
- **Thomas_Robert_Shannon_Broughton**: Mrs. Broughton mất 2005-09-19 (vợ mất sau chồng: GUIDE_v7 không ghi); Alan Broughton sinh 1936 (ngày sinh con); Colloquium 1994 (tưởng niệm sau khi mất); danh sách luận án các học trò (1969–1974) và tài liệu tham khảo.
- **William_Duncan_missionary**: người phụ tá phục vụ cùng Duncan 1908–1912 (người khác); điều tra dân số 1841, 1851 (thống kê); thư mục.

## Điểm theo quy ước mới (2026-11-04)
- Mùa giải: haiku đã ghi danh hiệu theo mùa (Sturrock e14 "1982–83", e20 "1996–97"; Dundee United League Cup 1979, 1980 là mùa 1979–80, 1980–81) theo mục mới, có `approximate_date`. Không có tai nạn máy bay hay năm TCN trong batch này.
- Haiku Edward_Adolf_Sonnenschein tự báo đã gọi `create_session` ngoài yêu cầu; bị chặn, không tạo phiên nào. Không thấy haiku nào khác báo gọi công cụ ngoài phạm vi.

## Điểm mơ hồ cần người dùng quyết
1. Levski: bảng huấn luyện viên nhiều dòng chỉ có năm ("Vyacheslav Hrozny ( 1998 )") nên đều ghi một mốc "becomes manager"; bảng có cả hai mốc ngày cụ thể ở giai đoạn sau 2004. Giữ như haiku.
2. Affari_tuoi: lần xuất hiện của người dẫn chương trình trên bản Mỹ (2007-02-05) có tính là sự kiện của chương trình không? Hiện không ghi.
3. Sturrock: á quân cúp (4 lần Scottish Cup, 1 UEFA Cup) có ghi như danh hiệu mùa giải không? Hiện không ghi (không phải danh hiệu).

## Đọc kiểm của session chính (2026-11-04): 456 → 465 (+9, `tools/fix_V1112.py`, chạy sau `patch_bV11.py`)
- Edward_Adolf_Sonnenschein (cloud +0, `gap.py` 28 dòng): thêm 9 tác phẩm trong mục thư mục dạng "N editions between X and Y" mà haiku mới ghi một phần (1879, 1884, 1891, 1910, 1927 đã có): Bentley's Plautine emendations 1883, A Greek Grammar for Schools 1898, Ora Maritima 1902, A New Latin Grammar 1912, Recommendations of the Classical Association 1912, Through German Eyes 1914, A new English Grammar 1916, The Gateway 1924, What is Rhythm? 1925. Mỗi mốc ở năm xuất bản đầu.
- Các trang khác (Levski 24 dòng gap, Bayerisches_Armeemuseum 18, William_Duncan 16, Broughton 13, Sturrock 10): đọc dòng gap, chủ yếu là thư mục, danh sách cầu thủ, kết quả mùa giải, việc của người khác hoặc đã có mốc ở dạng quote khác (bảng huấn luyện viên Levski đủ 2008–2014). Không thêm.
