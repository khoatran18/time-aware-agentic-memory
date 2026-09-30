# Bộ dữ liệu SituatedQA

## 1. Nguồn gốc

- **Paper gốc:** "SituatedQA: Incorporating Extra-Linguistic Contexts into QA" (EMNLP 2021).
- **Đơn vị xây dựng:** Đại học Texas at Austin (UT Austin) / Nhóm nghiên cứu của Eunsol Choi.
- **Ngôn ngữ:** Tiếng Anh.
- **Link chính thức:**
  - Paper: https://arxiv.org/abs/2109.06157
  - GitHub: https://github.com/mikejqzhang/SituatedQA
  - Hugging Face: https://huggingface.co/datasets/siyue/SituatedQA

## 2. Mục đích ban đầu của paper

Nghiên cứu khả năng của các mô hình QA khi đối mặt với các câu hỏi mà đáp án phụ thuộc mạnh vào **Bối cảnh ngoài ngôn ngữ (Extra-Linguistic Context)**, cụ thể là **Thời gian (Temporal)** và **Địa lý (Geographical)**. Ví dụ câu hỏi "Tổng thống là ai?" sẽ có đáp án khác nhau nếu đặt trong bối cảnh năm 2005 (George W. Bush) so với 2021 (Joe Biden), hoặc ở Mỹ so với Pháp.

## 3. Chủ đề / phạm vi nội dung

- Lấy nền tảng từ bộ Natural Questions (NQ) của Google (các câu hỏi tra cứu thực tế trên Google Search).
- Tập trung vào các câu hỏi mở về con người, tổ chức, chức vụ, địa điểm. Không chia chủ đề cụ thể.

## 4. Cấu trúc dữ liệu và Dung lượng

- **Dung lượng:** Rất nhẹ (vài MB), chỉ chứa file câu hỏi JSONL.
- **Cấu trúc:** Chỉ cung cấp bộ **Câu hỏi (Queries)**, **không có Văn bản thô (Raw text/Corpus)** đi kèm.
- **Các trường chính:** `question`, `date` (hoặc `location`), `answer`.
- **Ví dụ một bản ghi:**
  ```json
  {
    "question": "who is the prime minister of australia?",
    "date": "2012",
    "answer": ["Julia Gillard"]
  }
  ```

## 5. Timestamp thể hiện ở đâu?

- Mốc thời gian được gắn trực tiếp vào **Metadata của Câu hỏi** thông qua trường `"date"`.
- Hoàn toàn **KHÔNG CÓ** timestamp gắn trong văn bản thô, vì bộ dataset này không hề cung cấp văn bản thô.

## 6. Tính chất — Nên dùng cho gì / Không nên dùng cho gì

| Tính chất | Có/Không | Ghi chú |
|---|---|---|
| Mốc thời gian tách biệt rõ ràng làm Metadata | ✅ Có | Nằm ở câu hỏi. |
| Có sẵn Văn bản thô (Raw text) đã chia chunk | ❌ Không | Chỉ là bộ Benchmark câu hỏi. Đòi hỏi bạn phải tự lấy một bộ Wikipedia khổng lồ để làm data retrieval. |
| Theo dõi 1 sự kiện liên tục qua thời gian | ❌ Không | Các câu hỏi rời rạc, độc lập. |

## 7. Phù hợp với bài toán của nhóm không?

**KHÔNG PHÙ HỢP.**
Mục tiêu hiện tại của nhóm là tìm một bộ dữ liệu có **Văn bản thô (Raw data) chứa các mốc thời gian đã được chia chunk rõ ràng**. SituatedQA lại là một bộ đánh giá (Benchmark) thuần túy chỉ chứa Câu hỏi và Đáp án. Nó mặc định người dùng phải tự đi kiếm một kho dữ liệu (như Wikipedia lịch sử) để hệ thống RAG tự bơi vào đó tìm kiếm. Nó không cung cấp đoạn text nào để bóc tách cả.
