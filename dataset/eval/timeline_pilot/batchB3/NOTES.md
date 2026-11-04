# batchB3: 10 trang dùng GUIDE_v6.md (seed 7103, reserved_B.json)

Trang: Rush_Holt_Jr (54 chunk), Milton_Friedman (100), Irene_Kharisma_Sukandar (14), Razorfish_company (25), Hugh_Scott (33), Henry_Stommel (15), First_Things (24), Hsu_Hsin_liang (18), Permanent_Secretary_to_the_Treasury (8), World_Festival_of_Black_Arts (9).
Sửa bằng `tools/patch_bB3.py`; bản sau sửa ở `batchB3/rev/`. Đã đọc đủ 10 trang (Milton_Friedman đọc hết 100 chunk).

| | Số |
|---|---|
| Haiku viết (`sub/`) | 319 |
| Bỏ | 0 |
| Sót, đã thêm | 20 (6,3% so với haiku) |
| Sửa text/cờ (không đổi số mốc) | 5 chỗ |
| Sau khi sửa (`rev/`) | 339 |
| Mã kiểm bản haiku | 0 báo; sau sửa 0 lỗi |

Theo trang (haiku -> sau sửa): Rush Holt 34->34, Milton Friedman 41->45, Irene 29->29, Razorfish 31->37, Hugh Scott 39->39, Stommel 21->22, First Things 26->28, Hsu 28->33, Perm. Secretary 67->69, World Festival 3->3.

## Sót, đã thêm (20)
- Razorfish (6): phỏng vấn 60 Minutes II 2000-02; Forrester xếp hạng 2006; Microsoft công bố ý định mua 2007-05-18; Forrester Wave 2007-12; Ad Age A-List 2012 (#4) và 2013 (#9).
- Hsu (5): bị luận tội/bãi chức 1979 (derived); ủng hộ Lien-Soong 2004; Tuyên bố chung Tang Wai 2004-03; ủng hộ Frank Hsieh 2008 (tách khỏi mốc "hết ủng hộ Pan-Blue"); kêu gọi đối thoại hai bờ 2013-04.
- Milton Friedman (4): con trai David sinh 1945-02-12; cột Newsweek từ 1966; sách Free To Choose 1980; lập Friedman Foundation 1996.
- First Things (2): David Blum hết nhiệm kỳ 2010 (haiku chỉ ghi một mốc "serves"); Shalom Carmy bắt đầu cột 2017-05.
- Permanent Secretary (2): Murray vận động Lords 1909; Macpherson công bố thư cố vấn 2014 (hai sự cố giữ theo quy ước 8).
- Stommel (1): rời MIT, quay lại Woods Hole 1978 (derived).

## Sửa khác (không đổi số mốc)
- Hsu: e25 chỉ còn "hết ủng hộ Pan-Blue" (việc ủng hộ Hsieh tách mốc riêng, tránh gộp hai việc cùng năm); e18 (rời DPP 1999) và e24 (rời DPP 2006) gắn `source_inconsistent` vì cùng nguồn nói hai lần rời DPP; e24 bỏ `approximate_date`.
- First Things: e12 đổi text "serves" thành "begins".

## Lỗi mã kiểm không bắt được
- Cả 20 mốc sót (mã kiểm báo 0 lỗi ở bản haiku).
- Gộp hai việc trong một mốc (Hsu e25); mốc "khoảng năm" một sự kiện thay vì hai (Blum).

## Chỗ nhập nhằng, quyết định không đổi haiku (chờ xác nhận)
- (C) Hành động lập pháp có ngày cụ thể (Holt bỏ phiếu, Hugh Scott phản đối veto): giữ như haiku ghi. Danh sách phiếu bầu theo luật theo năm (Civil Rights Acts) và lời ủng hộ ứng viên (Rockefeller, Scranton) của Hugh Scott không ghi, chưa có quy ước rõ.
- Hai chức danh khác trong trang Treasury (Second Permanent Secretary 2009, Head of GES đến 2007) không ghi, đưa vào `undated_mentions` một dòng (chức danh khác).
- Quy ước (A) và (B) của B2: không có trường hợp mới trong B3.
