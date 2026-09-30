# Bộ dữ liệu TempLAMA

## 1. Nguồn gốc

- **Paper gốc:** "Time-Aware Language Models as Knowledge Bases" (TACL 2022).
- **Đơn vị xây dựng:** Bhuwan Dhingra và cộng sự (Google Research).
- **Ngôn ngữ:** Tiếng Anh.
- **Link chính thức:**
  - Paper: https://arxiv.org/abs/2102.11956
  - Hugging Face: https://huggingface.co/datasets/Yova/templama

## 2. Mục đích ban đầu của paper

Nghiên cứu khả năng của các mô hình ngôn ngữ (Language Models) trong việc tự ghi nhớ các sự kiện thực tế thay đổi theo thời gian, xem liệu chúng có thể hoạt động như một Cơ sở tri thức (Knowledge Base) nhạy cảm thời gian hay không. Bộ dữ liệu này được thiết kế để "hỏi xoáy" mô hình (Probing), ép mô hình điền vào chỗ trống thay vì sinh câu dài.

## 3. Chủ đề / phạm vi nội dung

- Lấy dữ liệu từ **Wikidata**, tập trung vào các quan hệ (relations) có ngày bắt đầu và kết thúc (VD: cầu thủ thi đấu cho đội nào, ai là tổng thống, ai làm CEO).
- Rất giống phạm vi chủ đề của TimeSensitiveQA (tiểu sử nhân vật, tổ chức).

## 4. Cấu trúc dữ liệu và Dung lượng

- **Dung lượng:** Rất nhẹ (vài chục MB), tải bằng Hugging Face `datasets` dễ dàng.
- **Cấu trúc:** Khác biệt hoàn toàn với hệ thống RAG thông thường. Nó sử dụng định dạng **Cloze-style query (Điền vào chỗ trống)** thay vì Câu hỏi tự nhiên.
- Nó **KHÔNG cung cấp Văn bản thô (Raw text/Corpus)**. Chỉ chứa câu truy vấn và đáp án.
- **Ví dụ một bản ghi:**
  ```json
  {
    "query": "Cristiano Ronaldo plays for [MASK].",
    "date": "2012",
    "answer": [{"name": "Real Madrid", "wikidata_id": "Q8682"}],
    "relation": "member of sports team"
  }
  ```

## 5. Timestamp thể hiện ở đâu?

- Giống SituatedQA, mốc thời gian nằm ở Metadata của câu truy vấn (`"date"`).
- Không có văn bản thô nên không có timestamp trong văn bản.

## 6. Tính chất — Nên dùng cho gì / Không nên dùng cho gì

| Tính chất | Có/Không | Ghi chú |
|---|---|---|
| Mốc thời gian tách biệt rõ ràng làm Metadata | ✅ Có | Nằm ở câu truy vấn. |
| Có sẵn Văn bản thô (Raw text) đã chia chunk | ❌ Không | Bộ này chỉ là Knowledge Graph thu nhỏ dạng điền từ. |
| Theo dõi 1 sự kiện liên tục qua thời gian | ✅ Có | Có nhiều truy vấn về cùng 1 người ở các năm khác nhau. |

## 7. Phù hợp với bài toán của nhóm không?

**KHÔNG PHÙ HỢP.**
Mặc dù TempLAMA bám rất sát ý tưởng "Sự tiến hóa của nhân vật theo thời gian" (rất hợp kịch bản Vụ án), nhưng nó lại vướng phải khuyết điểm chí mạng giống SituatedQA: **Nó không có dữ liệu văn bản thô (Corpus)**. 
Bài toán RAG bắt buộc phải có văn bản thô để VectorDB lưu trữ, băm nhỏ (chunking) và tìm kiếm. TempLAMA chỉ sinh ra để test xem "bộ não" của LLM có nhớ sự kiện lịch sử không, chứ không thiết kế để test hệ thống tra cứu RAG bên ngoài.
