# Quyết định 08: tách tập train, valid, test cho bộ đánh giá

**Ngày:** 2026-10-20. **Trạng thái:** **kế hoạch, chưa làm** (hoãn vì hạn mức API Gemini miễn phí chưa đủ để nạp kho và chạy Profiler cho hai tập mới). Chưa có code lấy mẫu.

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

## Việc cần làm khi tiếp tục

1. Viết bộ lấy mẫu (mở rộng `evaluation/subset.py`): trả hai bộ con `tune`, `valid` theo bảng trên, kiểm tra không trùng `idx` và `page_id`, ghi `dataset/eval/{tune,valid}_subset.json` và CSV danh sách câu.
2. Nạp kho vào collection riêng (`tam_chunks_dev_tune`, `..._valid`), chạy `profile_eval.py --ranges` (prompt `v2` hoặc `v3` nếu đã có) cho từng tập.
3. Quét tham số trên train; xác nhận trên valid bằng so sánh ghép cặp (chỉ nhận khi vượt khoảng 95%); khóa cấu hình, ghi vào `configs/`.
4. Chạy test sạch **một lần**; báo cáo cùng cấu hình đã chọn từ local trước (không phải cấu hình đứng đầu bộ `real`).

Phương án rẻ hơn nếu hạn mức vẫn thiếu: train 200 + valid 200 (phát hiện chênh khoảng 0.019), hoặc chỉ nạp phần câu của 5 domain lớn.
