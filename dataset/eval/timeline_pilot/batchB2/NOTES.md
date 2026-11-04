# batchB2: 10 trang dùng GUIDE_v6.md (seed 7102, reserved_B.json)

Trang: Charles_Lee_general (57 chunk), Real_Madrid_Baloncesto (52), London_Fire_Brigade (100), Department_of_Computing_Imperial_College_London (27), Luftflotte_1 (17), Frans_Hals_Museum (31), Georges_Duby (26), Humongous_Entertainment (22), Desmond_Patrick_Costello (40), Air_Component_Command (13).
Sửa bằng `tools/patch_bB2.py`; bản sau sửa ở `batchB2/rev/`. Đã đọc đủ 10 trang.

| | Số |
|---|---|
| Haiku viết (`sub/`) | 538 |
| Bỏ | 16 (3,0%) |
| Sót, đã thêm | 19 (3,5%) |
| Sau khi sửa (`rev/`) | 541 |
| Mã kiểm bản haiku | 2 báo (LFB e33 quote cắt cụt; Costello e28 quote description chứa năm); sau sửa 0 lỗi |

Theo trang (haiku -> sau sửa): Charles Lee 34->35, Real Madrid 160->160, LFB 89->92, Imperial 38->38, Luftflotte 1 34->34, Frans Hals 15->14, Duby 22->26, Humongous 64->61, Costello 28->29, Air Component Command 54->52.

## Bỏ (16)
- Humongous (12): các mục "Released untitled ... game (name missing in source)": danh sách game bị mất tên, không xác định được việc nào. Theo tinh thần quy ước 10 (tên bị mất) nên không ghi; gom vào `undated_mentions` một dòng. Chờ xác nhận (xem dưới).
- Air Component Command (3): hai mốc năm của Persson (2013 bắt đầu/kết thúc) trùng với hai mốc ngày chi tiết "acting 14/10/2013 đến 31/12/2013"; đề xuất cải tổ 2018-02 (kế hoạch và việc của Lực lượng vũ trang, không phải thực thể).
- Frans Hals Museum (1): Hội Khoa học Hà Lan được thành lập 1752 (thực thể khác; mốc 1754 thuê phòng vẫn giữ).

## Sót, đã thêm (19)
- Humongous (9): thành lập Cavedog 1995, Total Annihilation 1997, hai gói mở rộng 1998; GT Interactive bị Infogrames mua 11/1999; đồng sáng lập rời công ty 2001; công ty mẹ mua Hasbro Interactive và đổi tên Atari 5/2003; Atari SA nộp đơn phá sản 2013; Backyard Sports và MoonBase Commander bán trong thủ tục phá sản 2013 (hai mốc derived).
- Georges Duby (4): bản dịch tiếng Anh có năm trong thư mục: Chivalrous Society 1978, William Marshal 1984, Legend of Bouvines 1990, History Continues 1994.
- London Fire Brigade (3): cháy Cung điện Westminster 1834; tổ chức 11 sư đoàn A–L năm 1965; dịch vụ sơ cứu từ 2016.
- Charles Lee (1): giải ngũ hưởng nửa lương 1763 (derived). Costello (1): bị thẩm vấn về hộ chiếu Kroger sau vụ bắt 1961 (derived). Air Component Command (1): lập Air Force Tactical Center 1/7/1994.

## Sửa khác (không đổi số mốc)
- LFB e33 (1965): thay evidence bằng ba quote đầy đủ (chunk 9, 19, 88); Costello e28 (cái chết): đổi evidence thành cặp `both` (chunk 17) + `date` (chunk 0); Humongous e58: sửa `text` ("sold to parent and majority stockholder"), vì việc đóng cửa đã có mốc riêng.

## Lỗi mã kiểm không bắt được
- Sót 19, thừa 16: chỉ đọc mới thấy. Điển hình là khối "tên bị mất" (12 mốc trong Humongous) mà mã kiểm coi là hợp lệ.
- Hai mốc trùng một việc ở mức năm và mức ngày (Persson).

## Quy ước mới tự đặt (chờ xác nhận)
- (A) Danh sách phát hành/tác phẩm bị mất tên (ví dụ "- ( 1996 )"): không ghi sự kiện "untitled/name missing", chỉ ghi một dòng vào `undated_mentions`. Là mở rộng quy ước 10 từ người sang tác phẩm.
- (B) Bản dịch/tái bản có năm trong thư mục (Duby): ghi như sự kiện `work` riêng (không tính tái bản "repr."). Dùng lại nguyên tắc ghi phát hành.
Các chỗ quyết theo quy ước cũ, không mới: giải giao hữu của Real Madrid (có năm) giữ; giải theo mùa ("1941/42") để undated; chuyến đi từng sự cố của LFB (đám cháy do đội cứu hỏa tham gia) giữ như sự cố trong tổ chức (quy ước 8); bài viết/sách về Costello và mọi mốc sau khi ông mất (2007, 2012, 2017...) không ghi (quy ước 6, 7).
