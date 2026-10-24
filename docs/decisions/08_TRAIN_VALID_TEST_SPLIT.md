# Quyết định 08: tách tập train, valid, test cho bộ đánh giá

**Ngày:** 2026-10-20. **Trạng thái:** **đã tạo các bộ con (2026-10-21), chưa nạp kho và chưa chạy Profiler** (hoãn vì hạn mức API Gemini miễn phí chưa đủ). Code lấy mẫu: `src/tam/evaluation/splits.py`, `scripts/make_splits.py` (3 test).

## Bối cảnh

Mọi con số trong [`eval/05`](../eval/05_REAL_RESULTS.md) nằm trên **một** tập 400 câu (365 câu `D/test` + 35 câu `D/train`), và hơn 200 cấu hình đã được xem kết quả trên chính tập đó. Nên tập này không còn là tập test sạch: cấu hình đứng đầu bảng là cận trên. `D` không có tập dev; `C` có đủ train/dev/test nhưng là câu sinh theo mẫu.

## Số câu hiện có (đếm ngày 2026-10-20; `hard`, đã bỏ câu trước Công nguyên và câu không xác định được chunk đáp án)

| Domain | `D/train` hợp lệ | `D/train` chưa dùng | `D/test` hợp lệ | `D/test` chưa dùng | `C/dev` | `C/train` |
|---|---:|---:|---:|---:|---:|---:|
| business | 170 | 169 | 177 | 124 | 246 | 961 |
| sports | 162 | 162 | 158 | 103 | 897 | 4317 |
| career | 94 | 94 | 136 | 85 | 474 | 2164 |
| person | 142 | 142 | 116 | 63 | 234 | 1143 |
| politics | 105 | 105 | 91 | 39 | 662 | 3197 |
| place | 132 | 132 | 79 | 27 | 86 | 403 |
| media_arts | 98 | 82 | 34 | 0 | 31 | 135 |
| military | 52 | 34 | 32 | 0 | 39 | 191 |
| **Tổng** | 955 | 920 | 823 | 441 | 2669 | 12511 |

"Chưa dùng" = không nằm trong bộ `real` hay `local`. Trang của `D/train` và `D/test` gần như tách nhau (2 trang chung). `C/train` có 324 trang trùng với `D`, `C/dev` có 7.

## Đề xuất chia

| Tập | Số câu | Mỗi domain | Nguồn | Dùng để |
|---|---:|---|---|---|
| **Train (tune)** | 400 | 50 | `D/train` chưa dùng, bù `C` | Quét `λ`, `W1/W2`, `end_mode`, `t_unknown`, `decay_from`, `time_mode`, `overlap` |
| **Valid** | 400 | 50 | `D/train` chưa dùng, bù `C` | Xác nhận cấu hình chọn ở train; quyết định cuối trước test |
| **Test đã xem** | 400 | 50 | bộ `real` hiện tại | Mô tả theo domain; đã xem nhiều lần nên **không** dùng làm kết quả chính |
| **Test sạch** | 441 | không cân bằng | `D/test` chưa dùng | **Chạy một lần** với cấu hình đã khóa |

Cách chia train và valid (mỗi tập, cùng cách để phân phối giống nhau):

| Domain | Từ `D/train` | Từ `C` | Tổng |
|---|---:|---:|---:|
| business, sports, person, politics, place | 50 | 0 | 50 |
| career | 47 | 3 | 50 |
| media_arts | 41 | 9 | 50 |
| military | 17 | 33 | 50 |

Mỗi tập có khoảng 45 câu `C` (11%). Phân bố 441 câu test sạch theo domain: business 124, sports 103, career 85, person 63, politics 39, place 27, media_arts 0, military 0, nên **không cân bằng và không có military, media_arts**; báo cáo theo domain chỉ dùng 400 câu cân bằng.

Quy tắc: (1) không trùng `idx` và **không trùng `page_id`** giữa các tập; trang của test (cả đã xem và sạch) bị loại khỏi train và valid; (2) loại 35 câu mượn của bộ `real`; (3) gắn nhãn nguồn (`D`/`C`) cho từng câu, chia phân tầng theo nguồn × domain; (4) seed cố định, ghi trong file bộ con; (5) hai tập train/valid nên dồn câu vào ít trang để giảm chi phí nạp kho.

## Đủ để so sánh chưa

Sai số chuẩn của `mrr` khoảng 0.02 ở 400 câu. So ghép cặp hai cấu hình gần nhau có sai số chuẩn khoảng 0.005 (đo ở `decay_from`), nên:

| Cỡ mẫu | Chênh `mrr` phát hiện được (khoảng 80% power) |
|---|---|
| 400 | khoảng 0.013 |
| 720 | khoảng 0.010 |
| 2900 | khoảng 0.005 |

Đủ để so Cơ chế 1 với Plain RAG (chênh +0.08 đến +0.10). Các cấu hình dense hiện chênh nhau dưới 0.012: chỉ thấy được xu hướng ở 400 câu; muốn quyết cần khoảng 700 câu valid (thêm khoảng 200 câu `D/train` dư ở business, sports, person, place, nhưng lệch domain). Theo từng domain n khoảng 50 (military khoảng 17): sai số chuẩn khoảng 0.06 trở lên, chỉ mô tả.

## Chi phí LLM ước tính (chưa chạy)

- Mỗi tập khoảng 130 trang, khoảng 4,400 chunk, khoảng 150 lô nạp kho (Gemini 3.5) cộng khoảng 400 request Profiler (Gemini 3.1) mỗi tập. Tune + valid: khoảng 300 lô + 800 request, tức khoảng **1,100 request**.
- Test sạch: 67 trang chưa nạp (khoảng 120 lô) cộng 441 request Profiler.
- Hạn mức Gemini miễn phí: 500 request/ngày mỗi model và 15 request/phút. Có thể chia hai model, nhưng với thất bại và gọi lại thì cần 2–3 ngày. **Đây là lý do hoãn.**

## Đã tạo (2026-10-21, chế độ `pooled`)

`python scripts/make_splits.py` (seed 42, không gọi LLM, không nạp kho) ghi `dataset/eval/{tune,valid,test_clean}_subset.json` và CSV danh sách câu. **Chia lại theo quyết định của người dùng:** D/train và D/test cùng một phân phối (câu do người viết; xem số liệu so sánh trong lịch sử trao đổi: kiểu câu, độ dài, domain gần nhau, hơn nhau ở số relation), nên gộp lại làm một kho D rồi chia; chỉ loại các `idx` đã nằm trong `real`/`local`, **không loại trang**.

| Tập | Câu | Trang | Chunk | Nguồn câu | Domain |
|---|---:|---:|---:|---|---|
| `test_clean` | 400 | 186 | ~5,680 | D/test 266, D/train 117, C 17 | 50 mỗi domain (military: 33 câu D + 17 câu C chọn theo độ khó tương xứng) |
| `valid` | 400 | 167 | ~5,060 | D/train 302, D/test 98 | sports 93, business 81, career 70, person 61, politics 43, place 27, media_arts 25; không military |
| `tune` | 400 | 140 | ~4,040 | D/train 237, D/test 30, C 133 | 50 mỗi domain (military và media_arts bù từ C) |

- **`test_clean` phủ đủ 8 domain, cân bằng hoàn toàn (50 mỗi domain):** lấy D/test trước, thiếu thì bù D/train (media_arts và military không có trong D/test); military vẫn thiếu 17 câu D nên bù 17 câu C (`pick_similar`), chọn tham lam sao cho phân bố đặc trưng thay cho độ khó gần phân bố của 34 câu D military: relation, kiểu nêu thời gian, khoảng hay mốc, số chunk đáp án, cỡ trang, độ dài câu hỏi, vị trí chunk đáp án. Kết quả khớp tốt ở relation (P241 26/24%, P410 24/24%, P4791 50/53%), kiểu nêu thời gian (between 44/47%, in 38/35%, after 12/12%), cỡ trang, vị trí; **chưa khớp độ dài câu hỏi** (D có 38% câu trên 16 từ, C không có câu nào: câu mẫu ngắn hơn). Đây chỉ là đặc trưng bề ngoài, không phải thước đo độ khó thật; độ khó thật chỉ biết sau khi nạp kho và chạy truy xuất. Báo cáo của `test_clean` ghi nguồn C (17 câu, 4%) để loại ra khi cần kiểm tra. Chi tiết phân bố lưu trong `test_clean_subset.json`, khóa `bu_tu_C`.
- **`valid` = 400 câu D lấy từ phần còn lại (chặn trên 400 bằng `--valid-size` để giữ chi phí Profiler), bám phân bố relation của test**; sau cả ba tập còn thừa 337 câu D (290 câu ở trang chưa đụng tập nào; business 112, sports 72, person 44, place 32, career 23, politics 22, other 26, media_arts 5, military 1), có thể thêm vào valid nếu cần: phủ 25 trong 32 relation của test (các relation chưa phủ vì quá ít câu: P4791 16, P175 13, P241 9, P410 8, P608 4, P195 2, P800 2 đã vào test hết), domain không cân bằng. Thứ tự ưu tiên khi chia: test, rồi valid, rồi tune.
- Không trùng `idx` và không trùng `page_id` giữa ba tập (script kiểm tra bằng `assert`); cả ba được chung trang với `real`/`local`. Quy tắc cũ "loại trang của `real`/`local`" bỏ trong chế độ này.
- Hai chế độ cũ vẫn dùng được: `--valid-mode match-test` (valid chỉ D/train, test sạch 446 câu D/test không cân bằng), `--valid-mode balanced` (tune và valid cân bằng, bù C).
- Chi phí LLM nếu nạp hết (số lô tính đúng theo cách cắt lô 30 chunk mỗi lô, mỗi trang tối đa 100 đoạn; công thức tái hiện chính xác bộ `real`: 330 lô cho 6,880 chunk). Tái dùng các trang đã có trong kho `tam_chunks_dev_real_v2`: `tune` 185 lô (127 trang mới), `valid` 192 lô (136 trang mới), `test_clean` 111 lô (82 trang mới) = **488 lô**; Profiler 1 request mỗi câu: 400 + 400 + 400 = **1,200**. Tổng khoảng 1,690 request, 2 đến 3 ngày với hạn mức Gemini miễn phí (500 request mỗi ngày mỗi model, hai model song song). Nạp lại cả các trang đã có trong `real` thì 730 lô.
- **Tiến độ nạp kho và Profiler (cập nhật 2026-10-23, prompt v3, nạp kho google_35, Profiler khoảng google_31 = Gemini 3.1, `--keep-undated`):**

| Tập | Nạp kho | Profiler khoảng (google_31) |
|---|---|---|
| `valid` | **xong** `tam_chunks_dev_valid`: 4,884 điểm / 5,063 chunk; 21 chunk bị Gemini chặn `PROHIBITED_CONTENT` (1 trang, `Young Girl with a Flower Basket`), ảnh hưởng 1 câu | **xong** 400/400 (`output/20261022_140127/profiler.jsonl`) |
| `test_clean` | **xong** `tam_chunks_dev_test_clean`: 5,572 điểm / 5,682 chunk; **0 chunk bị chặn**, nên không phải thay câu nào từ `valid` | chưa chạy (400 câu) |
| `tune` | **xong** `tam_chunks_dev_tune` (22/10): 140 trang, 4,039 chunk, 3,974 điểm (613 chunk không mốc), 56 chunk bỏ vì không có mốc, 9 vì mốc không hợp lệ, 0 lỗi LLM | **dở** 241/400 đến hết hạn mức ngày 22/10; chạy tiếp từ 23/10 |

  Quy tắc xử lý lô bị chặn nội dung: câu có mọi chunk đáp án nằm trong lô bị chặn thì bỏ khỏi tập; ở `test_clean` thay bằng câu D cùng domain từ `valid`, `valid` bù từ phần D còn thừa (337 câu); mỗi tập phải còn ít nhất 400 câu dùng được (hiện `valid` 399, `test_clean` 400).
- Cách báo cáo vẫn như trước: kết luận chính bằng so sánh ghép cặp; số tuyệt đối báo micro và macro kèm bootstrap; military có n nhỏ (33) chỉ mô tả.

## Việc cần làm khi tiếp tục

1. ~~Viết bộ lấy mẫu~~ **Xong** (xem mục trên).
2. Nạp kho vào collection riêng (`tam_chunks_dev_tune`, `..._valid`), chạy `profile_eval.py --ranges` (prompt `v2` hoặc `v3` nếu đã có) cho từng tập.
3. Quét tham số trên train; xác nhận trên valid bằng so sánh ghép cặp (chỉ nhận khi vượt khoảng 95%); khóa cấu hình, ghi vào `configs/`.
4. Chạy test sạch **một lần**; báo cáo cùng cấu hình đã chọn từ local trước (không phải cấu hình đứng đầu bộ `real`).

Phương án rẻ hơn nếu hạn mức vẫn thiếu: train 200 + valid 200 (phát hiện chênh khoảng 0.019), hoặc chỉ nạp phần câu của 5 domain lớn.

## Ghi chú 2026-10-22: bổ sung câu của `real` vào tập tune (chưa làm)

Đo chồng chéo (đọc `dataset/eval/*_cases.csv`): các tập `valid`, `test_clean`, `tune` không trùng câu hay trang với nhau; `real` không trùng câu nhưng trùng trang với `valid` (27/204 trang), `test_clean` (**102**/204) và `tune` (12/204). `real` gồm 365 câu `D/test` và 35 câu `D/train`.

**Dự định:** tập tune = `tune` hiện có **cộng** các câu của `real` có trang **không** nằm trong `test_clean`. Lý do: `real` đã có kho và Profiler nên đỡ tốn request, tăng cỡ mẫu tune (sai số chuẩn nhỏ hơn); loại câu cùng trang với `test_clean` để các tham số tune không mang thông tin của trang test.

**Cần chốt khi làm:**
- Câu `real` cùng trang với `valid` (27 trang) có bỏ không. Quy tắc hiện chỉ loại theo `test_clean`; nếu giữ, `valid` không còn độc lập hoàn toàn với tune ở mức trang.
- `real` là bộ đã xem nhiều khi thiết kế, nên kết quả trên phần này vẫn chỉ là cận trên; chỉ dùng để chọn tham số, không báo cáo như số độc lập.
- Số câu đủ điều kiện chưa đếm; Profiler `tune` (241/400) cứ chạy tiếp, phần `real` đã có Profiler cũ ở `output/20261020_173521/profiler.jsonl`.
