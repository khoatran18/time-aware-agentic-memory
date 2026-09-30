# Bộ dữ liệu RealTime QA

## 1. Nguồn gốc

- **Paper gốc:** "RealTime QA: What's the Answer Right Now?" (Kasai và cộng sự, NeurIPS 2023 Datasets and Benchmarks Track).
- **Đơn vị xây dựng:** Sự hợp tác giữa University of Washington, Allen Institute for AI (AI2), và Tohoku University.
- **Ngôn ngữ:** Tiếng Anh.
- **Link chính thức:**
  - Paper: https://arxiv.org/abs/2207.13332
  - GitHub (dataset + code): https://github.com/realtimeqa/realtimeqa_public
  - Website: https://realtimeqa.github.io/

## 2. Mục đích ban đầu của paper

Mục đích chính của RealTime QA **không phải** để giải quyết bài toán Xung đột thời gian (Conflict Resolution), mà là để test **Khả năng cập nhật kiến thức mới (Freshness / Novelty)** của các hệ thống AI.
Các mô hình Ngôn ngữ Lớn (LLM) bị "đóng băng" kiến thức tại thời điểm huấn luyện (ví dụ: cắt tại tháng 9/2021). RealTime QA ném cho hệ thống các câu hỏi về sự kiện *vừa mới xảy ra ngày hôm qua*, nhằm đánh giá xem hệ thống RAG có thể cung cấp đúng văn bản thời sự mới nhất và LLM có ngoan ngoãn trả lời theo văn bản đó hay không (tránh bị "ảo giác" - hallucination dùng kiến thức cũ trong não để trả lời sự kiện mới).

## 3. Chủ đề / phạm vi nội dung

- **Sự kiện thời sự nóng hổi (Current Events).**
- Dữ liệu được trích xuất trực tiếp và cập nhật liên tục hàng tuần từ các trang tin tức lớn như CNN, USA Today, The Week.
- Bao gồm đa dạng các sự kiện ngẫu nhiên: Tai nạn, Chính trị, Thể thao, Giải thưởng... diễn ra trong tuần đó.
- **Lưu ý về chủ đề:** Tất cả các tin tức về mọi chủ đề đều bị **trộn lẫn (mixed)** vào trong 1 bộ dữ liệu của mỗi tuần. Không có sự tách biệt chuyên sâu cho từng lĩnh vực.

## 4. Cấu trúc dữ liệu và Dung lượng

Đặc điểm tuyệt vời nhất của bộ dữ liệu này là **RẤT NHẸ (Dung lượng siêu nhỏ)** và được chia file vô cùng khoa học theo từng tuần (Ví dụ thư mục `past/2023/`).
- **Dung lượng data:** Tổng dung lượng tất cả các năm cộng lại chỉ khoảng **~400MB**. Mỗi folder của 1 tuần chỉ loanh quanh vài trăm KB đến vài MB. Đây là bộ dữ liệu dễ thở nhất cho bất kỳ máy tính cá nhân nào.

Mỗi tuần (thường là thứ Sáu) sẽ có một bộ file:
1. **`[date]_qa.jsonl`**: File chứa câu hỏi. 
   - **Loại câu hỏi:** Đây là **câu hỏi trắc nghiệm (Multiple Choice)** (có mảng `choices` A,B,C,D). Tuy nhiên khi test thực tế, có thể giấu `choices` đi để ép nó sinh text tự luận.
   - **Khả năng theo dõi (Tracking):** Rất kém. Các câu hỏi rời rạc theo tin hot trong tuần. **Không có chuỗi câu hỏi lặp lại theo dõi 1 sự kiện/con người qua thời gian dài.**
2. **`[date]_gcs.jsonl` (Google Custom Search)**: Chứa **Văn bản thô (Context/Documents)**. 
   - **Khả năng chia chunk:** Văn bản thô là nguyên một bài báo/đoạn trích xuất từ Google, **không được chia chunk theo kiểu gắn timestamp vào từng câu** (mốc thời gian của nó đơn giản là ngày xuất bản của bài báo đó). Không chứa diễn biến sự kiện qua nhiều mốc thời gian trong cùng 1 bài.
3. **`[date]_dpr.jsonl` (Dense Passage Retrieval)**: Tương tự như file GCS nhưng văn bản thô được truy xuất bằng mô hình AI (DPR).
4. **`[date]_qa_nota.jsonl` (None Of The Above)**: Một file bẫy!

### Ví dụ 1 bản ghi câu hỏi (JSONL)
```json
{
  "question_id": "20230106_0",
  "question_sentence": "Who was named the 2022 TIME Person of the Year?",
  "choices": ["Elon Musk", "Volodymyr Zelensky", "Joe Biden", "Greta Thunberg"],
  "answer": "Volodymyr Zelensky",
  "question_date": "2023/01/06"
}
```

## 5. Timestamp thể hiện ở đâu?

- **Rất rành mạch dưới dạng Metadata:** Mốc thời gian được gắn trực tiếp vào từng câu hỏi thông qua trường `"question_date"` (VD: `"2023/01/05"`).
- Nó tách rời hoàn toàn khỏi câu hỏi ngôn ngữ tự nhiên. Trong câu hỏi, người ta chỉ dùng các từ chỉ thời gian ẩn ý (Implicit Time) như *"this week"*, *"recently"*, *"today"*.

## 6. Về khái niệm ghi đè và xử lý thời gian

- **Không chứa kịch bản thay đổi/ghi đè của cùng 1 thực thể (Longitudinal Tracking):** Đây là điểm yếu so với TimeQA. Bộ này là tin tức ngẫu nhiên ngắt quãng (Breaking News). Nó hiếm khi hỏi lại cùng 1 tổ chức qua nhiều tháng để bạn thấy sự thay đổi.
- **Sử dụng làm Mốc chặn (Cut-off Time):** Trường `question_date` đóng vai trò là "hiện tại giả định". Hệ thống RAG bắt buộc phải dùng mốc này làm Hard-filter để loại bỏ (không cho phép đọc) các bài báo xuất bản sau ngày này, ngăn chặn "gian lận" biết trước tương lai (Data Leakage).

## 7. Tính chất — Nên dùng cho gì / Không nên dùng cho gì

| Tính chất | Có/Không | Ghi chú |
|---|---|---|
| Mốc thời gian tách biệt rõ ràng làm Metadata | ✅ Có | Trường `question_date` cực kỳ dễ lập trình cho VectorDB. |
| Có sẵn Văn bản thô (Raw text) đi kèm | ✅ Có | Tích hợp sẵn trong file `_gcs.jsonl`, không phải tự đi cào tin tức ở ngoài. |
| Dung lượng nhẹ, phù hợp máy cá nhân | ✅ Có | Cực kỳ tối ưu, khoảng vài trăm KB cho mỗi tuần. |
| Theo dõi 1 thực thể bị thay đổi qua nhiều năm | ❌ Không | Chỉ phù hợp hỏi sự kiện tuần. Nếu muốn theo dõi chức vụ nhân vật đổi qua từng năm, phải dùng TimeQA / TempLAMA. |

**Kết luận sử dụng:**
- **Nên dùng cho:** Demo thuật toán RAG có khả năng cập nhật tin mới (Freshness) bằng cách nạp dần tin tức theo từng tuần. Lý tưởng cho đồ án vì data nhẹ, đủ tiếng Anh, chia file rất rõ ràng.
- **Không nên dùng cho:** Kịch bản "Vụ án" (Cốt truyện tiến hóa phức tạp, nay đúng mai sai của cùng 1 người) hay Bài toán theo dõi tiểu sử nhân vật qua nhiều giai đoạn.

## 8. Cách đánh giá khi test

- **Bước 1 (Nạp Data):** Bóc toàn bộ text trong các file `_gcs.jsonl` (hoặc `_dpr.jsonl`), ném vào Vector Database với Metadata là ngày xuất bản bài viết.
- **Bước 2 (Chạy Retrieval):** Đưa câu hỏi và mốc `question_date` cho VectorDB. Lọc cứng: *Chỉ lấy văn bản <= question_date*.
- **Bước 3 (Đánh giá):** Có 2 chế độ test:
  1. *Trắc nghiệm (Multiple-choice):* Yêu cầu mô hình chọn A, B, C, D dựa trên Context vừa tìm được.
  2. *Tự luận (Open-ended Generation):* Giấu trường `choices` đi, bắt mô hình tự sinh câu trả lời bằng text, sau đó so khớp bằng Exact Match hoặc LLM-as-a-judge. (Cách này khó và thực tế hơn).
