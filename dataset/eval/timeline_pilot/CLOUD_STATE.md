# CLOUD_STATE (nhánh cloud/valid-timelines)

Cập nhật: 2026-11-04, sau batch V9 và V10. Lượt sau: lấy N lớn nhất của `batchV<N>/` đang có (hiện là 10), làm N+1 và N+2, seed = 7200 + số batch.

## Đã xong (lượt này)
- batchV9 (seed 7209) và batchV10 (seed 7210), mỗi batch 10 trang, chạy lần lượt từng batch (haiku → kiểm → vá rồi mới sang batch sau). `DIR=rev check.py` = 0 lỗi cả hai; `gap.py` và `view.py` đã chạy cả 20 trang.
- V9: haiku 526 → 537 mốc (+11): Florence +9 công trình/cơ quan, Ty_Detmer +1, HJK +1; 5 cờ `derived_date` ở HJK và 1 sửa evidence ở Florence. Patch `tools/patch_bV9.py`, `batchV9/NOTES.md`.
- V10: haiku 558 → 558 mốc: không thêm mốc sau khi đọc kiểm; 2 cờ `derived_date` (Schröder e65, Greens e87). Patch `tools/patch_bV10.py`, `batchV10/NOTES.md` ghi lý do không thêm từng trang.
- Trang valid còn lại trong `reserved_valid.json` (chưa dùng trong bất kỳ `*/in`): 67.

## Quyết định tự đặt cần người dùng xác nhận (lượt V9, V10)
1. ACES_Colombia: 5 vụ tai nạn/không tặc của từng máy bay (1981, 1982, 1988, 1996, 2000) KHÔNG ghi, theo GUIDE_v7 (sự cố của vật mang). Nhưng ở V8 GCR_Class_11E có ghi một vụ tai nạn 1927. Cần thống nhất: trang hãng hàng không có ghi tai nạn của máy bay hãng không?
2. Florence (trang thành phố): ghi thêm công trình có năm (nhà thờ, cung điện, nhà hát, đài phun nước, rạp phim) theo quy ước V1 (Valladolid). Không ghi hội chợ đồ cổ 1959 (sự kiện định kỳ).
3. Năm TCN/CE: `check.py` không nhận (định dạng `\d{4}` bắt buộc). Florence "59 BC" Julius Caesar lập Fluentia giữ trong `undated_mentions`. Ngoài ra batchV7/rev/Han_dynasty (do session chính vá) đang có mốc "-0138" v.v. làm `DIR=rev check.py batchV7 Han_dynasty` báo 55 lỗi; mình không sửa (ngoài phạm vi). Cần chọn: sửa `check.py` cho phép dấu âm hay chuyển các mốc TCN sang undated.
4. Galatasaray (20 mốc cho 65 chunk): hầu như mọi năm là mùa giải nên vào `undated_mentions`. Nếu muốn mốc cho "mùa X–Y" thì cần quy ước đặt năm (hiện GUIDE_v7 không cho).
5. Bảng lãnh đạo (IMU, Federation of the Greens, HJK, KF Skënderbeu): giữ hai mốc bắt đầu/kết thúc mỗi nhiệm kỳ. Một số dòng chỉ ghi một năm "(1996)" hay "(2018)" nên đã ghi như mốc bắt đầu (và kết thúc cùng năm), không suy thêm.
6. Ty_Detmer, Helsingin Jalkapalloklubi: chấn thương và chuyển nhượng được ghi như mốc của nhân vật/CLB.
7. Danh hiệu từng năm của CLB (HJK: Veikkausliiga, Finnish Cup, đội nữ): ghi `other` với nhãn `award` theo mục "Giải thưởng từng năm" trong GUIDE_v7, cả danh hiệu của đội nữ và bandy (HJK có nhiều mục này).

## Quyết định cũ (V5, V6) vẫn còn hiệu lực
Ghi lại ở NOTES của V5/V6 (session chính đã sửa thêm bằng `fix_V56.py` trong lượt trước); xem `batchV5/NOTES.md`, `batchV6/NOTES.md`.

## Cạm bẫy gặp
- Số trang ghi trong "xong" của haiku không đủ: kiểm bằng `ls batchV<M>/sub` và `check.py` (nhiều haiku không nêu tên trang). Mình đã đếm sai số trang xong vài lần khi báo tiến độ; lần sau liệt kê tên file `sub/` thay vì đếm theo thông báo.
- `gap.py` chỉ thấy năm bốn chữ số: bỏ sót "59 BC", "by 1436" trong cùng câu thì vẫn bắt được, nhưng phải đọc tay các câu có BC/AD.
- Quote HJK dạng "Aulis Rytkönen ( 1960–71 )" (năm viết tắt) báo lỗi "không chứa năm": thêm `derived_date`.
- Quote `both` mà năm nằm ở câu trước (Schröder 10 October, Greens "In June"): thêm `derived_date`.
- Id trong `sub/` khác `rev/` sau `fin()`: khi vá, dùng id của `sub/` (patch đọc `rev/` đã copy từ `sub/`, id lúc đầu giống nhau).
- Vài haiku ở lượt V5–V6 gọi nhầm công cụ MCP ngoài phạm vi; lượt V9–V10 không thấy haiku nào báo gọi công cụ ngoài phạm vi.
- batchV4 trong repo thiếu `sub/Vladimir_Bukovsky.json`, `rev/` và `NOTES.md` (không sửa, ngoài phạm vi).
