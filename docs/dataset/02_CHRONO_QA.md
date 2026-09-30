# Bộ dữ liệu ChronoQA

## 1. Nguồn gốc

- **Paper gốc:** "ChronoQA: A Question Answering Dataset for Temporal-Sensitive Retrieval-Augmented Generation" (2024), công bố trên tạp chí Nature Scientific Data.
- **Đơn vị xây dựng:** Nhóm nghiên cứu độc lập (được công bố trên arXiv và GitHub).
- **Ngôn ngữ:** Tiếng Trung (Chinese).
- **Link chính thức:**
  - Paper: https://www.nature.com/articles/s41597-025-06098-y (hoặc các bản preprint trên arXiv).
  - GitHub (dataset + code): https://github.com/czy1999/ChronoQA

## 2. Mục đích ban đầu của paper

Nghiên cứu này ra đời nhằm giải quyết điểm yếu chí mạng của các hệ thống Retrieval-Augmented Generation (RAG) hiện tại: **tính nhạy cảm với thời gian**. Các hệ thống RAG thông thường dựa vào so khớp ngữ nghĩa (Semantic Matching) nên thường bỏ qua các ràng buộc về thời gian trong câu hỏi hoặc truy xuất ra các thông tin đã lỗi thời. ChronoQA được tạo ra làm benchmark (thước đo) để đánh giá xem hệ thống RAG xử lý các truy vấn liên quan đến thời gian tốt đến đâu.

## 3. Chủ đề / phạm vi nội dung

Khác với TimeQA (chỉ dùng Wikidata tiểu sử), ChronoQA lấy dữ liệu từ **báo chí thực tế (Sina News)** trong giai đoạn từ 2019 đến 2024. Phạm vi nội dung rất đa dạng và thay đổi liên tục theo dòng sự kiện:
- Công nghệ, Sản phẩm mới.
- Xã hội, Pháp luật, Tai nạn giao thông.
- Y tế (đặc biệt là các bản tin thay đổi theo ngày như số ca nhiễm Covid-19).
- Thể thao, Kinh tế.
→ **Lưu ý về Chủ đề:** Tất cả các bản tin thuộc các chủ đề trên đều bị **trộn lẫn (mixed)** vào trong cùng một file dữ liệu duy nhất, không có nhãn phân loại chủ đề riêng biệt.

## 4. Cấu trúc dữ liệu và Dung lượng

- **Dung lượng data:** Ở mức vừa phải. Tổng 360.000 cặp câu hỏi - đáp án. Vì phần văn bản thô (raw text) được nhúng trực tiếp vào bên trong file, nên file giải nén ra nặng khoảng **vài trăm MB đến tối đa 1-2 GB**. Rất dễ dàng xử lý bằng thư viện Pandas trên laptop cá nhân.
- **Định dạng:** CSV và JSON (`chronoqa.json`, `chronoqa.csv`).
- **Thành phần của một bản ghi (JSON):**
  - `question`: Câu hỏi bằng tiếng Trung. **Loại câu hỏi:** Đây là câu hỏi tự luận ngắn, sinh ra text (không phải trắc nghiệm). Đặc biệt: **Các câu hỏi mang tính chộp giật, đứt gãy. KHÔNG CÓ chuỗi câu hỏi theo dõi sự tiến hóa của 1 sự kiện/con người qua thời gian dài.**
  - `question_date`: Thời điểm người dùng (giả định) đặt ra câu hỏi.
  - `answer`: Đáp án ngắn gọn.
  - `temporal_type`: Loại câu hỏi thời gian (VD: Absolute - tuyệt đối, Relative - tương đối như "tháng trước", Aggregate - tổng hợp/so sánh).
  - `golden_chunks`: Mảng chứa các đoạn văn bản thô (raw text) **đã được chia chunk sẵn**. **Khả năng theo dõi:** Các chunk này thường là những đoạn tin vắn tắt (tách rời nhau), **không theo dõi xuyên suốt 1 sự kiện** qua nhiều giai đoạn như cấu trúc tiểu sử của TimeQA.
  - `golden_chunks_urls`: Link bài báo gốc.

### Ví dụ 1 bản ghi
```json
{
  "question": "Vào tháng trước, số ca nhiễm mới tại Bắc Kinh là bao nhiêu?",
  "question_date": "2020-05-15",
  "answer": "12 ca",
  "temporal_type": "relative",
  "golden_chunks": [
    "2020年4月 (Tháng 4 năm 2020), Ủy ban y tế Bắc Kinh ghi nhận 12 ca nhiễm mới...",
    "2020年5月 (Tháng 5 năm 2020), Bắc Kinh không có ca nhiễm mới..."
  ]
}
```

## 5. Timestamp thể hiện ở đâu?

- **Trong câu hỏi (Metadata):** Có trường `question_date` rõ ràng (ví dụ: `2024-08-30`). Đây là mốc rất quan trọng để xử lý các câu hỏi chứa từ "hôm nay", "tháng trước".
- **Trong văn bản thô (Context / golden_chunks):** Mốc thời gian được **nhúng (prepend) trực tiếp vào ngay đầu đoạn văn bản**. Ví dụ: `"2020年4月2日，广州天河区发生起公交车..."` (Ngày 2 tháng 4 năm 2020, tại Quảng Châu xảy ra...). Cách làm này ép bộ nhúng (Embedding) phải "học" luôn ngày tháng vào Vector ngữ nghĩa.

## 6. Về khái niệm ghi đè và xử lý thời gian

- **Nguồn tin tức (News):** Bản chất tin tức là liên tục ghi đè các trạng thái cũ. Hôm nay chính phủ ra dự thảo, ngày mai ra luật chính thức.
- Mô hình phải dùng mốc thời gian `question_date` để gióng xuống dòng thời gian của sự kiện (thông qua mốc thời gian ở đầu `golden_chunks`) nhằm chọn ra Chunk phù hợp nhất, thay vì chỉ chọn Chunk có nhiều từ khóa giống câu hỏi nhất.

## 7. Tính chất — Nên dùng cho gì / Không nên dùng cho gì

| Tính chất | Có/Không | Ghi chú |
|---|---|---|
| Mốc thời gian tách biệt rõ ràng làm Metadata | ✅ Có/Không | Có ở câu hỏi, nhưng ở phần Text lại trộn lẫn vào chữ (cần regex bóc ra nếu muốn làm hard-filter). |
| Temporal conflict / Đa nguồn | ✅ Có | Dữ liệu báo chí thực tế, nhiều bài báo về cùng một chủ đề ở các thời điểm khác nhau. |
| Phù hợp test câu hỏi thời gian tương đối ("Bây giờ", "Tháng trước") | ✅ Có | Hỗ trợ cực tốt thông qua trường `temporal_type = relative` và `question_date`. |
| Ngôn ngữ Tiếng Việt / Tiếng Anh | ❌ Không | Đây là **nhược điểm chí mạng**. Dữ liệu 100% tiếng Trung, việc dịch thuật tự động có thể làm hỏng logic mốc thời gian. |

**Kết luận sử dụng:**
- **Nên dùng cho:** Tham khảo kiến trúc, học hỏi cách họ chia Chunk (prepend ngày tháng vào đầu text), và cách họ phân loại các dạng câu hỏi thời gian (Tuyệt đối, Tương đối, So sánh).
- **Không nên dùng cho:** Làm bộ dataset chính thức để nộp trong đồ án nếu team bạn không có khả năng/kinh phí tự động dịch thuật chuẩn xác 300,000 bản ghi sang tiếng Việt/Anh.

## 8. Cách đánh giá khi test

Mô phỏng 1 hệ thống RAG hoàn chỉnh:
1. Nạp tất cả các `golden_chunks` vào Vector Database.
2. Đưa `question` và `question_date` cho mô hình. 
3. Đo lường xem mô hình có truy xuất (retrieve) đúng cái chunk chứa thời gian phù hợp không, và câu trả lời sinh ra (Generation) có trùng khớp với `answer` hay không (dùng Exact Match hoặc LLM-as-a-Judge).
