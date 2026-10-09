# Kế hoạch đánh giá: bộ local và bộ thật

Ghi lại các quyết định khi dựng bộ hỏi đáp về thời gian để test nhiều phương pháp bằng API. Chưa có file dữ liệu mẫu nào được tạo; đây chỉ là kế hoạch.

## 1. Nguồn dữ liệu

- Lấy từ **`D/test`**: 830 câu do người viết, 50 chủ đề, 251 trang. Chủ đề cân bằng hơn `C/test` (P54 chỉ 56 câu, trong khi `C/test` có 794 câu P54 trên 2,613 câu).
- **hard là mức chính** (mốc thời gian ngầm, cần suy luận). **easy là đối chứng**: cùng `idx`, cùng đáp án, chỉ khác cách nêu thời gian, nên chênh lệch điểm giữa hai mức cho thấy khó khăn nằm ở suy luận thời gian hay ở đọc hiểu.
- Chạy thêm một mức **không đưa văn bản trang** (chỉ hỏi câu hỏi) để biết mô hình trả lời được bao nhiêu nhờ nhớ sẵn kiến thức Wikipedia. Mức này rất rẻ.
- Chọn mẫu với **seed cố định** và lưu danh sách `idx` ra file, để mọi phương pháp chạy đúng cùng bộ câu.

## 2. Hai bộ

| | Bộ local | Bộ thật |
|---|---|---|
| Mục đích | Kiểm tra phương pháp chạy được, sửa lỗi code/prompt | So sánh các phương pháp |
| Chủ đề × câu mỗi chủ đề | 5 × 5 | 15 × 20 |
| Số câu hỏi | 25 | 300 |
| Số dòng (× easy và hard) | 50 | 600 |
| Số trang | 21 | 130 |
| Chủ đề | P54, P39, P26, P108, P69 | P54, P488, P39, P108, P127, P26, P1448, P937, P102, P137, P551, P463, P4791, P27, P69 |

Các chủ đề của bộ thật đều có ít nhất 20 câu trong `D/test`. Tôi không lấy cả hai chủ đề huấn luyện viên (P6087, P286) vì gần giống chủ đề thể thao.

Ý nghĩa: P54 member of sports team, P488 chairperson, P39 position held, P108 employer, P127 owned by, P26 spouse, P1448 official name, P937 work location, P102 member of political party, P137 operator, P551 residence, P463 member of, P4791 commanded by, P27 country of citizenship, P69 educated at.

## 3. Độ tin cậy

Sai số 95% của điểm tuyệt đối một phương pháp (mỗi câu chấm đúng/sai, độ chính xác khoảng 50%):

| Số câu | Sai số |
|---|---|
| 25 (local) | ±20% |
| 150 | ±8% |
| 300 (bộ thật) | ±5.7% |
| 500 | ±4.4% |
| 830 (cả `D/test`) | ±3.4% |

- Bộ local chỉ để kiểm tra chạy được, **không** dùng để so sánh điểm.
- **Chênh lệch giữa hai phương pháp** có sai số riêng, phụ thuộc số câu mà hai phương pháp cho kết quả khác nhau. Ví dụ bất đồng ở 30 trong 150 câu (20%) thì sai số khoảng ±7 điểm. Nên dùng kiểm định cặp (McNemar cho đúng/sai) để biết chênh lệch có đáng tin không.
- Điểm theo **từng chủ đề riêng** (20 câu mỗi chủ đề, sai số khoảng ±22%) chỉ để tham khảo. Nếu cần chia nhỏ hơn thì gộp thành vài họ chủ đề (thể thao, chức vụ, việc làm/học vấn, gia đình, khác).
- 15 chủ đề này chỉ đại diện cho nhóm chủ đề đó, không phải cả bộ.

## 4. Cách chấm

LLM sinh câu trả lời tự do, nên cần một cách chấm biến câu trả lời thành đúng/sai (hoặc điểm 0 đến 1). Đáp án ngắn (trung vị 2 từ), 5.9% câu ở `D/test` có nhiều đáp án.

| Cách chấm | Ưu | Nhược |
|---|---|---|
| EM sau chuẩn hoá (bỏ hoa thường, dấu câu, mạo từ) | Đơn giản, rẻ | Khắt khe: "The team was Port F.C." bị chấm sai |
| **Chứa đáp án** | Rẻ, chịu được câu trả lời dài dòng | Liệt kê nhiều đáp án cũng được tính đúng |
| **F1 theo từ** | Cho điểm từng phần; có sẵn trong `../utils.py` (`normalize_answer`, `compute_exact`, `compute_f1`) | "University of Arizona" so với "University of Arizona , Tucson" vẫn bị trừ điểm |
| LLM giám khảo | Chính xác nhất khi khác cách viết | Tốn thêm tiền; chỉ dùng cho ca khó |

Đề xuất: **chứa đáp án và F1 làm chính**, báo cáo thêm EM; LLM giám khảo chỉ cho các câu F1 ở mức nửa chừng.

### Câu nhiều đáp án

Trong `D/test`, 49 trong 830 câu (5.9%) có từ 2 đáp án trở lên (bộ thật 300 câu khoảng 18 câu). Có hai kiểu:

- **Cùng một thứ viết khác nhau:** *The German charter airline Condor had who as its owner in Jan 2018?* → `Thomas Cook AG`, `Thomas Cook Group`. Hay *Where did portrait painter jan anthonie coxie work in Feb 1719?* → `Milan`, `Lombardia` (thành phố và vùng chứa nó).
- **Nhiều đáp án khác nhau, đều đúng:** trong khoảng thời gian hỏi, đối tượng gắn với nhiều thứ. *What football team was Olivier Bernard a member of between Jul 2005 and Nov 2005?* → `Rangers`, `Southampton`. *The Sydney Trains C set had which depot or depots controlling it in late 1980s?* → `Mortdale Maintenance Depot`, `Hornsby Maintenance Depot`, `Punchbowl Maintenance Depot`.

**Quyết định: chấm khớp.** Câu trả lời chỉ cần khớp **một** trong các đáp án là được điểm đầy đủ. Đây cũng là cách chấm gốc của dataset (`../utils.py`, hàm `get_raw_scores` lấy điểm cao nhất `max` trên các đáp án), nên so sánh được với kết quả gốc. Dùng quy ước này giống nhau cho mọi phương pháp.

Với cách chấm "chứa đáp án", một mô hình liệt kê nhiều đáp án cùng lúc cũng được tính đúng nếu có một đáp án khớp, nên hãy đặt giới hạn độ dài câu trả lời trong prompt (ví dụ "trả lời bằng một cụm ngắn").

## 5. Chi phí mỗi lần chạy

Phạm vi: **2 phương pháp**, mỗi phương pháp chạy **3 lần** (tổng 6 lần chạy), dùng mô hình rẻ **haiku-5-5 hoặc DeepSeek V4 Flash**, ở hai trường hợp: **chỉ hard** và **hard + easy**.

Đơn vị: **token** (đơn vị tính tiền của API), **M = triệu token**, tiền tính bằng **USD**. Mẫu seed 0, đếm token bằng `tiktoken cl100k_base` (xấp xỉ). Mỗi dòng gồm văn bản cả trang + khoảng 200 token cho hướng dẫn và câu hỏi.

| Bộ | Số dòng | Token đầu vào (M) | Trung bình mỗi dòng (token) |
|---|---:|---:|---:|
| Local (25 câu × easy+hard) | 50 | 0.169 | 3,388 |
| Thật, chỉ hard (300 câu) | 300 | 0.782 | 2,607 |
| Thật, hard + easy (300 câu × 2 mức) | 600 | 1.564 | 2,607 |

Giá, tính theo **USD trên 1 triệu token**:

| Mô hình | Giá đầu vào (USD / 1M token) | Giá đầu ra (USD / 1M token) |
|---|---:|---:|
| haiku-5-5 (bảng giá Claude, ghi ngày 2026-10-06) | 0.10 | 0.50 |
| DeepSeek V4 Flash | 0.14 | 0.28 |

Giá DeepSeek V4 Flash lấy từ một trang tổng hợp trích bảng giá chính thức; các trang khác ghi mức khác nhau (0.07 đến 0.44 cho đầu vào) tùy phiên bản và nhà cung cấp, nên **kiểm tra lại ở trang giá chính thức** của DeepSeek trước khi chạy. DeepSeek đếm token bằng tokenizer riêng, và nếu mô hình có bước suy luận thì token suy luận tính vào đầu ra, nên hãy xem số token đầu ra thật ở vài câu đầu tiên.

Giả định đầu ra: **60 token mỗi câu** (trả lời ngắn) hoặc **800 token mỗi câu** (có suy luận).

**Tiền cho một lần chạy (USD):**

| Bộ | Số dòng | Đầu ra mỗi câu | haiku-5-5 | DeepSeek V4 Flash |
|---|---:|---|---:|---:|
| Local (25 câu × easy+hard) | 50 | 60 token | 0.02 | 0.02 |
|  |  | 800 token | 0.04 | 0.03 |
| Thật, chỉ hard | 300 | 60 token | 0.09 | 0.11 |
|  |  | 800 token | 0.20 | 0.18 |
| Thật, hard + easy | 600 | 60 token | 0.17 | 0.23 |
|  |  | 800 token | 0.40 | 0.35 |

**Tiền cho cả đợt: 2 phương pháp × 3 lần = 6 lần chạy (USD):**

| Trường hợp | Đầu ra mỗi câu | haiku-5-5 | DeepSeek V4 Flash |
|---|---|---:|---:|
| Thật, chỉ hard | 60 token | 0.52 | 0.69 |
| Thật, hard + easy | 60 token | 1.05 | 1.37 |
| Thật, chỉ hard | 800 token | 1.19 | 1.06 |
| Thật, hard + easy | 800 token | 2.38 | 2.12 |

Chạy cả hai mô hình thì cộng hai cột. Ví dụ hard + easy, 60 token đầu ra: khoảng **2.4 USD**; chỉ hard: khoảng **1.2 USD**. Chi phí rất nhỏ nên nhiều khả năng không cần giảm thêm; nếu muốn, nhóm các câu cùng trang chạy liền nhau để dùng prompt caching, hoặc dùng Message Batches (giảm 50% giá, chạy không đồng bộ).

## 6. Lưu ý

- Tokenizer của Claude có thể đếm nhiều hơn `tiktoken` khoảng 1 đến 1.35 lần, nên số trên có thể thấp hơn thực tế. Đo chính xác bằng `count_tokens` trước khi chạy lớn.
- Đầu ra có thinking (800 token) chỉ là giả định; số thật phụ thuộc mức effort và độ khó câu hỏi.
- Trang dài kéo chi phí lên: trung bình khoảng 2,600 đến 3,400 token mỗi dòng, p90 khoảng 7,500. Giảm bằng cách nhóm câu theo trang và dùng prompt caching, bỏ trang quá dài (có thể gây lệch mẫu), hoặc dùng truy xuất thay vì đưa cả trang.
- Chi phí chạy trên các mô hình nhỏ rất thấp (bộ thật dưới 1 USD mỗi lần chạy với haiku-5-5); chi phí lớn chủ yếu đến từ mô hình lớn có thinking hoặc từ việc nhân số phương pháp và số lần chạy.
