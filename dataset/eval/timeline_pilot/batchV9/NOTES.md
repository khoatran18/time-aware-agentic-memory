# batchV9 (valid set, seed 7209, GUIDE_v7)

10 trang từ `reserved_valid.json`, chạy 10 haiku (một batch, không gộp với V10). Haiku 526 mốc; sau vá 537 (+11, −0). `DIR=sub check.py` = 6 lỗi (Florence 1, HJK 5), `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang, `view.py` đã xem cả 10 trang. mtime `sub/` ổn định trước khi kiểm. Patch: `tools/patch_bV9.py`.

| Trang | Chunk | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|---|
| ACES_Colombia | 13 | 16 | 0 | 0 | 16 |
| Anna_Karina | 32 | 35 | 0 | 0 | 35 |
| Carrier_Air_Wing_Seven | 20 | 36 | 0 | 0 | 36 |
| Florence | 100 | 46 | 9 | 0 | 55 |
| Helsingin_Jalkapalloklubi | 54 | 183 | 1 | 0 | 184 |
| James_Parmentier | 9 | 7 | 0 | 0 | 7 |
| KF_Sk_nderbeu_Kor | 59 | 87 | 0 | 0 | 87 |
| Matthias_Platzeck | 19 | 48 | 0 | 0 | 48 |
| S_rgio_Concei_o | 30 | 36 | 0 | 0 | 36 |
| Ty_Detmer | 25 | 32 | 1 | 0 | 33 |

## Sửa lỗi
- Florence e30 (1814): evidence chỉ có role `date` → đổi `both` (quote "from 1808 to the fall of Napoleon in 1814" có cả mô tả).
- Helsingin_Jalkapalloklubi e54, e64, e65, e72, e83: quote danh sách huấn luyện viên viết tắt năm ("1960–71", "1973–74", "1975–79", "1981–82") → thêm cờ `derived_date`.

## Mốc thêm (từng mốc)
- Florence (trang thành phố 100 chunk; haiku chỉ 46 mốc, bỏ công trình có năm):
  - 1013 xây Basilica di San Miniato al Monte.
  - 1059 trùng tu mặt tiền San Miniato theo Romanesque ("between 1059 and 1128", một mốc, cờ `approximate_date`).
  - 1296 khởi công Nhà thờ chính tòa Santa Maria del Fiore.
  - 1436 nhà thờ hoàn thành cấu trúc, mái vòm của Brunelleschi ("by 1436", cờ `approximate_date`).
  - 1445 Palazzo Medici Riccardi xây ("between 1445 and 1460", cờ `approximate_date`).
  - 1563 Đài phun nước Neptune của Ammannati (1563–1565).
  - 1861 Tuscany thành một vùng của Vương quốc Ý.
  - 1862-05-17 khánh thành nhà hát ngoài trời Politeama Fiorentino Vittorio Emanuele.
  - 1920 rạp Cinema Teatro Savoia (sau là Odeon) thành lập ("from 1920 to 1922", cờ `approximate_date`).
- Ty_Detmer: 2000 chấn thương gân Achilles phải, nghỉ cả mùa (đưa ra khỏi `undated_mentions`).
- Helsingin_Jalkapalloklubi: 2015 ký Havenaar, Tanaka, Moussi trong kỳ chuyển nhượng mùa đông (cờ `approximate_date`).

## Không ghi (quyết định có chủ đích)
- ACES_Colombia: năm vụ tai nạn/không tặc của từng máy bay (1981, 1982, 1988, 1996, 2000) do `gap.py` liệt kê. GUIDE_v7 coi tai nạn của từng máy bay là sự kiện của vật mang. Cần người dùng xác nhận (ở V8, GCR_Class_11E có 1927 tai nạn).
- Anna_Karina: 1960 phim Breathless và 1958 Gigi (phim của người khác), phát biểu 2016; "11th Berlin Film Festival" Gấu Bạc (chỉ số thứ tự, không năm) vẫn trong `undated_mentions`.
- Carrier_Air_Wing_Seven: 1944 (thời gian tồn tại của CVG-7 thứ nhất, đơn vị khác).
- Florence: 59 BC Julius Caesar lập Fluentia và 80 BC Sulla phá Fiesole (`check.py` không nhận năm TCN, dạng "-0059" bị báo lỗi định dạng); giữ 59 BC trong `undated_mentions`. Dân số, thống kê du lịch, xếp hạng (Condé Nast 2013, Travel + Leisure 2010), nhiệt độ kỷ lục, 1559 Catherine de Medici nhiếp chính (nhân vật khác), 1490 Savonarola làm prior San Marco, 1959 hội chợ đồ cổ (sự kiện định kỳ).
- Helsingin_Jalkapalloklubi: 1930 thể thức giải quốc gia (của liên đoàn), thống kê mùa, á quân (đã nằm trong `undated_mentions`), derby với HIFK 1972, đối thủ Lahti.
- KF_Sk_nderbeu_Kor: 1920–1923 clubs khác thành lập (Përparimi, Shpresa), 1926–27 các đội khu phố, 3 lần thua chung kết cúp (1958, 1965, 1976), 2008 nhóm cổ động viên thành lập.
- Matthias_Platzeck: 2010 phát biểu "Anschluss", 2014 phát biểu về Crimea (phát biểu, không phải hành vi chính thức); 2004/05 Chủ tịch Bundesrat (cụm "2004/05" nằm trong `undated_mentions`).
- S_rgio_Concei_o: mọi danh hiệu theo mùa ("1996–97", "2017–18") nằm trong `undated_mentions`; 2007 thua chung kết cúp Bỉ (kết quả trận).
- Ty_Detmer: kết quả trận (1990 thắng Miami, 2001 bảy lần bị chặn), xếp hạng bình chọn Heisman 1989/1991.
- James_Parmentier: 1671 cậu Bourdon mất (người khác).

## Ghi chú
- Haiku Anna_Karina, Platzeck, Škënderbeu báo "xong" mà không nêu tên trang; đã khớp theo tên file `sub/`.
- `check.py` không nhận ngày TCN. Kiểm thử `DIR=rev check.py batchV7 Han_dynasty` hiện báo lỗi (các mốc "-0138"...): ngoài phạm vi của mình, ghi lại trong CLOUD_STATE.md.

## Đọc kiểm của session chính (2026-11-04): 537 → 549 (+12, `tools/fix_V910.py`, chạy sau `patch_bV9.py`)
- KF_Skënderbeu +7: thua chung kết Cúp Albania 1958, 1965, 1976, 2012; vô địch hạng nhất 1976–77 và 2008–09 (mùa giải, `approximate_date`); trận thắng Champions League/châu Âu đầu tiên mùa 2012–13 (`approximate_date`). Không ghi: trận thắng lớn nhất 2015–16 (kết quả trận, không phải "lần đầu"), nhóm cổ động 2008, vụ chia sân cổ động viên.
- Anna_Karina +2: tiểu thuyết 1973 và 1988 (tên sách mất trong nguồn, ghi tên chung). Sérgio_Conceição +3: Cup Winners' Cup 1998–99 với Lazio (`approximate_date`), thua chung kết Cúp Bỉ 2007, làm đội trưởng 2008–09 (`approximate_date`).
- Không thêm: Florence (số liệu dân số, xếp hạng, nhân vật Medici không thuộc thành phố), HJK 2011–12 thắng Bangor 13–0 (kỷ lục kết quả trận), Platzeck 2010/2014 (phát biểu).
