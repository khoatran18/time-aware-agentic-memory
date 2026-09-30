# Bộ dữ liệu StreamingQA

## 1. Nguồn gốc

- **Paper gốc:** "StreamingQA: A Benchmark for Adaptation to New Knowledge over Time in Question Answering Models" (2022).
- **Đơn vị xây dựng:** Google DeepMind.
- **Ngôn ngữ:** Tiếng Anh.
- **Link chính thức:**
  - Paper: https://arxiv.org/abs/2205.11388
  - GitHub (dataset + code): https://github.com/google-deepmind/streamingqa

## 2. Mục đích ban đầu của paper

Các bộ dữ liệu QA truyền thống dựa trên một "ảnh chụp nhanh" (snapshot) tĩnh của thế giới (ví dụ: Wikipedia năm 2021). Tuy nhiên, thế giới thực luôn thay đổi. StreamingQA được sinh ra để đánh giá xem các mô hình ngôn ngữ lớn (LLM) và hệ thống RAG có thể **cập nhật kiến thức mới một cách liên tục (streaming knowledge)** mà không quên kiến thức cũ, hay không bị lẫn lộn giữa thông tin cũ - mới hay không.

## 3. Chủ đề / phạm vi nội dung

- Dựa trên kho lưu trữ báo chí khổng lồ **WMT News Crawl** kéo dài 14 năm (2007 - 2020).
- Chứa mọi chủ đề tổng hợp trên toàn thế giới: Chính trị, Thể thao, Kinh tế, Giải trí, Tai nạn, v.v.
- **Lưu ý về chủ đề:** Các bài báo về mọi lĩnh vực bị **trộn lẫn (mixed) vào chung một dòng chảy tin tức**, không hề được phân loại riêng rẽ hay tạo thư mục riêng cho từng chủ đề.

## 4. Cấu trúc dữ liệu và Dung lượng (ĐIỂM YẾU CHÍ MẠNG)

- **Dung lượng data:** Bất đối xứng và siêu khổng lồ. 
  - File chứa câu hỏi chỉ nặng vài chục MB.
  - Phần dữ liệu thô (WMT News Crawl) **lên tới hàng trăm GB**. Không thể tải về một file nén có sẵn text, mà bắt buộc phải chạy script trích xuất, tốn rất nhiều thời gian và dung lượng ổ cứng. Đây là nhược điểm chí mạng cho các máy tính cá nhân.

Dữ liệu chia làm 2 phần tách biệt hoàn toàn:
1. **Câu hỏi (JSONL):** Các file `train.jsonl`, `valid.jsonl`, `eval.jsonl`.
   - Chứa `question` (câu hỏi). **Loại câu hỏi:** Câu hỏi tự luận ngắn, sinh text bình thường (không phải trắc nghiệm).
   - `answers` (danh sách đáp án đúng).
   - `question_ts` (Thời điểm đặt ra câu hỏi).
   - `evidence_ts` (Thời điểm bài báo chứa đáp án được xuất bản).
   - `evidence_id` (Mã ID của bài báo gốc).
   - **Khả năng theo dõi (Tracking):** Vì lấy từ tin tức, các câu hỏi thường hỏi về các sự kiện rời rạc xuất hiện ngẫu nhiên. **Rất hiếm khi có chuỗi câu hỏi lặp lại theo dõi cùng 1 nhân vật/sự kiện qua nhiều mốc thời gian** (Khác với TimeQA).
2. **Văn bản thô (WMT News Crawl):** Dữ liệu văn bản thô cực kỳ lớn (hàng chục GB), không nằm sẵn trong repo. **Khả năng chunking:** Văn bản thô là nguyên một bài báo dài, **chưa hề được chia chunk chuẩn bị sẵn** cho VectorDB. 

### Ví dụ 1 bản ghi câu hỏi (JSON)
```json
{
  "question": "Who did Boris Johnson succeed as Prime Minister?",
  "answers": ["Theresa May"],
  "question_ts": 1563960000, 
  "evidence_id": "wmt_2019_12345",
  "evidence_ts": 1563955200
}
```

## 5. Timestamp thể hiện ở đâu?

- **Rất rõ ràng và chuyên nghiệp:** Timestamp được lưu riêng biệt dưới dạng Metadata (kiểu số nguyên UTC seconds) thông qua 2 trường `question_ts` và `evidence_ts`. 
- Nó tách rời hoàn toàn khỏi văn bản, giúp quá trình lọc (Filter) bằng code khi truy xuất vào Vector Database trở nên cực kỳ chính xác.

## 6. Về khái niệm ghi đè và xử lý thời gian

- Do lấy từ dòng chảy tin tức (News stream) trong 14 năm, dữ liệu có tính chất **ghi đè/xung đột đa nguồn (multi-source conflict)** rất mạnh mẽ.
- Một câu hỏi như "Thủ tướng Anh là ai?" sẽ có nhiều đáp án khác nhau tùy thuộc vào cái `question_ts` (thời điểm hỏi). Nếu hỏi vào năm 2009 đáp án là Gordon Brown, hỏi năm 2012 đáp án là David Cameron.

## 7. Tính chất — Nên dùng cho gì / Không nên dùng cho gì

| Tính chất | Có/Không | Ghi chú |
|---|---|---|
| Mốc thời gian tách biệt rõ ràng làm Metadata | ✅ Có | Rất dễ lập trình bộ lọc (Filter) cho RAG. |
| Temporal conflict / Đa nguồn | ✅ Có | Tin tức chạy dài 14 năm nên có đủ mọi sự kiện tiến hóa. |
| Streaming/Liên tục cập nhật | ✅ Có | Rất phù hợp để giả lập luồng dữ liệu đổ vào Database theo từng ngày. |
| Dễ sử dụng, tải về chạy được ngay | ❌ Không | Đây là **nhược điểm chí mạng**. Dữ liệu câu hỏi thì nhẹ, nhưng văn bản thô thì khổng lồ (hàng trăm GB). Quá trình trích xuất rất cồng kềnh, không phù hợp cho laptop sinh viên. |
| Lọc theo 1 chủ đề hẹp | ❌ Không | Dữ liệu hỗn tạp mọi lĩnh vực. |

**Kết luận sử dụng:**
- **Nên dùng cho:** Tham khảo thiết kế cấu trúc dữ liệu lưu Metadata thời gian (tách bạch `question_ts` và `evidence_ts`), dùng làm baseline nếu có server mạnh mẽ (hàng trăm GB ổ cứng) để đánh giá Cơ chế C (Streaming RAG).
- **Không nên dùng cho:** Đồ án sinh viên chạy trên laptop cá nhân, hoặc đồ án yêu cầu focus vào 1 domain hẹp (ví dụ: chỉ phân tích tài chính/luật pháp).

## 8. Cách đánh giá khi test

- Giả lập quá trình chạy thời gian thực: Bơm lần lượt văn bản gốc vào Vector Database theo từng tháng/quý.
- Ở mỗi quý (mốc `question_ts`), dừng lại và ném câu hỏi vào hệ thống để bắt hệ thống trả lời dựa trên những bài báo vừa được nạp.
- So khớp đáp án bằng Exact Match / LLM-as-a-Judge. Đánh giá xem hệ thống mất bao lâu để "nhận thức" được thông tin mới, và liệu nó có lấy nhầm bài báo cũ để trả lời cho sự kiện mới hay không.
