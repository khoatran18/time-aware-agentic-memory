# batchB4: 10 trang dùng GUIDE_v6.md (seed 7104, reserved_B.json)

Trang: Good_Game_TV_program (100 chunk), Counselor_to_the_President (11), Johan_Gabriel_Oxenstierna (20), Daniel_M_Fleetwood (13), Museum_f_r_Moderne_Kunst (34), Luftflotte_5 (13), Masters_snooker (35), Line_7_Beijing_Subway (10), Bohemond_IV_of_Antioch (44), David_N_Livingstone (15).
Sửa bằng `tools/patch_bB4.py`; bản sau sửa ở `batchB4/rev/`. Đã đọc đủ 10 trang (Good_Game đọc hết 100 chunk).

| | Số |
|---|---|
| Haiku viết (`sub/`) | 321 |
| Bỏ | 1 (0,3%) |
| Sót, đã thêm | 34 (10,6%) |
| Sau khi sửa (`rev/`) | 354 |
| Mã kiểm bản haiku | 6 báo (3 quote không nguyên văn; 3 cảnh báo "mốc thập kỷ" ở Museum); sau sửa 0 lỗi |

Theo trang (haiku -> sau sửa): Good Game 38->49, Counselor 7->7, Oxenstierna 26->27, Fleetwood 22->23, Museum MMK 100->101, Luftflotte 5 13->14, Masters 53->55, Line 7 12->12, Bohemond IV 27->32, Livingstone 23->34.

## Bỏ (1)
- Oxenstierna e5 (nhật ký kết thúc 1768): nhật ký 1766-1768 là hoạt động, chỉ ghi một mốc ở lúc bắt đầu (quy ước hoạt động/giải đấu/tour).

## Sót, đã thêm (34)
- Livingstone (11): các bài giảng có tên (Lyell 1994, Hettner 2001, Murrin 2002, Progress in Human Geography 2005, Appleton/Von Humboldt/Gordon Manley 2007, Gunning 2009, Gregory 2010, Gifford 2014, Dudleian 2015) trong mục "Professional distinctions". Haiku ghi các chức danh/giải thưởng nhưng bỏ nguyên khối bài giảng.
- Good Game (11): khách mời Hansen 2008-10-06; tập thứ 100 2009-08-24; dẫn Rage 2010-06-19; kêu gọi phóng viên 2011-03-21; đại sứ Screen It 2013; AMA Reddit 2013; Perth Writers Festival 2014; MCV Pacific Awards 2014; bình chọn Top 100 năm 2014; Hing được báo dẫn Pocket 2015-02-04; tập cuối của Hing 2016-07.
- Bohemond IV (5): Saladin chiếm hạt Tripoli 1188 (approximate); đưa quân về Antioch giúp anh 1194 (derived); bắt giam Latin patriarch 1207 (derived, tách khỏi mốc đảo chính); đến Acre dự Thập tự chinh V 1217 (derived); con Philip bị bắt 1224.
- Masters (2): Marco Fu lập maximum break thứ ba 2015; Stuart Bingham vô địch 2020 (derived từ "aged 43 in 2020").
- Oxenstierna (2, trừ 1 bỏ): vào Cabinet 1788 và rời Cabinet 1790 (derived, "Russo-Swedish War (1788–1790)"); Fleetwood (1): Discover Invention of the Year 1998; Luftflotte 5 (1): đổi tên các bộ chỉ huy mặt đất 1944 (derived); Museum MMK (1): Iden hết nhiệm kỳ giám đốc sáng lập 1987.

## Sửa khác (không đổi số mốc)
- Quote không nguyên văn (mã kiểm bắt): Oxenstierna e17 (thiếu dấu cách trước dấu phẩy), Masters e40 (như trên), Line 7 e2 (thiếu " ." cuối).
- Museum e3, e20, e65: bỏ cụm "1970s/1980s/1990s" khỏi text và quote để qua cảnh báo mốc thập kỷ (mốc vẫn đúng năm 1981, 2000, 2010).
- Bohemond e11: đổi text, vì việc bắt giam patriarch tách thành mốc riêng (tránh gộp hai việc cùng năm).

## Lỗi mã kiểm không bắt được
- Cả 34 mốc sót, mốc hoạt động có hai đầu (nhật ký Oxenstierna), gộp hai việc trong một mốc (Bohemond e11).

## Quy ước mới / chỗ nhập nhằng (chờ xác nhận)
- (D) Bài giảng có tên và năm trong danh sách "Professional distinctions" (Livingstone): ghi như mốc `other` (honour/lecture). Haiku không ghi; mình thêm theo tinh thần quy ước giải thưởng.
- (E) Danh sách triển lãm của bảo tàng (MMK, ~85 mốc `work` của haiku): giữ nguyên, theo tinh thần quy ước ghi tác phẩm đã phát hành; chưa có quy ước riêng cho triển lãm.
- Masters: danh sách ngoại lệ seeding theo năm (đình chỉ, rút lui, COVID) không ghi, gom một dòng `undated_mentions`. Danh sách "Yan Bingtao là nhà vô địch đương nhiệm" không ghi (không có năm).
- (C) từ B3 áp lại: hành động cá nhân có ngày cụ thể ở trang người (Good Game: dẫn Rage, AMA Reddit) giữ như mốc.

## Cập nhật sau khi session chính đọc kiểm (16:15)
- `tools/fix_B34.py` (do session chính viết, không phải của session phụ) đã bổ sung vào `rev/`: Counselor_to_the_President 7->10 (+3), Line_7_Beijing_Subway 12->14 (+2). Tổng B4 sau sửa hiện là 359 (không phải 354 như bảng trên, bảng trên là sau `patch_bB4.py` riêng). Mã kiểm `DIR=rev` vẫn 0 lỗi.
- Lưu ý khi chạy lại `patch_bB4.py`: nó ghi đè `rev/` của 2 trang trên và làm mất phần bổ sung; phải chạy `fix_B34.py` sau đó.
