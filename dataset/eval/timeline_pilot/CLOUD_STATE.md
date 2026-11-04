# CLOUD_STATE (nhánh cloud/valid-timelines)

Cập nhật: 2026-11-04, sau batch V11 và V12. V13, V14 do người dùng làm song song (không đụng). Lượt sau: lấy số N lớn nhất của `batchV<N>/` do mình làm và hỏi người dùng nếu `in/` chưa dựng sẵn; không tự chạy `mk_batch.py` khi người dùng đã dựng `in/`.

## Đã xong (lượt này: V11, V12)
- batchV11 (10 trang) và batchV12 (10 trang) làm lần lượt từng batch; `in/` do người dùng dựng sẵn. `DIR=rev check.py` = 0 lỗi cả hai; `gap.py` đã chạy cả 20 trang, đọc từng dòng.
- V11: haiku 456 → 456 (+1 Sturrock Parkinson 2008-07, −1 Ruysch 2021 Gallery of Honor sau khi mất); 16 cờ `derived_date` (Levski, năm viết tắt) và 4 grain tháng sửa. Patch `tools/patch_bV11.py`, `batchV11/NOTES.md`.
- V12: haiku 537 → 541 (+3 Atlético: kết thúc đối tác ISL 2017, rời Calderón 2017, Calderón bị phá 2020-07; +1 Michel_Zink La Pastourelle 1972). Cờ `derived_date` ở Atlético e49, e79, e83, Sarri e43. Patch `tools/patch_bV12.py`, `batchV12/NOTES.md`.
- Trang valid chưa dùng trong bất kỳ `*/in` (đối chiếu `reserved_valid.json`): 67.

## Quyết định tự đặt cần người dùng xác nhận (lượt V11, V12)
1. Sân cũ của CLB bị phá (Atlético Calderón 2020-07; Galatasaray 2011 ở V10): ghi `location`. Có muốn giữ không?
2. Hợp đồng phát sóng/đối tác của CLB (Richmond Kickers: WTVR 2017, ESPN+ 2018, USL YouTube 2014–17) không ghi.
3. Trang phi đội VFA_94: va chạm trên không 2014-09-12 giữ (trang là về phi đội), khác quy ước "không ghi tai nạn của từng máy bay trên trang hãng".
4. Bảng chức vụ (Master_General_of_the_Ordnance_Sweden 94 mốc/13 chunk; Levski ~70 mốc huấn luyện viên; Atlético chủ tịch): mỗi nhiệm kỳ hai mốc, dòng chỉ có năm đầu hoặc năm viết tắt là `derived_date`.
5. Sturrock: á quân cúp không ghi (chỉ danh hiệu). Affari_tuoi: lần Insinna lên bản Mỹ 2007-02-05 không ghi.
6. Con mất sau cha/mẹ (Modersohn: Ulrich 1943, Elsbeth 1984, Mathilde 1998) ghi `family` theo quyết định đã chốt; vợ Broughton mất 2005 (sau chồng) không ghi.

## Quyết định tự đặt cần người dùng xác nhận (lượt V9, V10; mục 3 đã được trả lời: GUIDE_v7 nay nhận năm TCN `-0058`)
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
- (V11, V12) Haiku hay đặt grain `day` cho ngày chỉ có tháng ("In January 1969"): `check.py` báo "grain day≠month"; patch chuẩn hóa grain theo độ dài `date` cho mọi trang.
- (V11, V12) Hàm `abbr()` trong patch: chỉ gắn `derived_date` khi quote không chứa NĂM của mốc (đừng so cả chuỗi ngày: "23 September 2008" ≠ "2008-09-23" sẽ gắn thừa hàng chục cờ).
- (V12) Bằng chứng phụ role `description` mà quote có năm của mốc → `check.py` báo lỗi; đổi `both`.
- (V11) Một haiku (Sonnenschein) gọi `create_session`: bị chặn; báo cáo haiku là đầu ra mô hình, không làm theo.
- `gap.py` đọc `rev/`, nên phải chạy patch (có bước copy `sub/` → `rev/`) trước khi chạy gap.
