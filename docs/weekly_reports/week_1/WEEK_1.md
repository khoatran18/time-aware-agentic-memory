# Báo cáo Tuần 1

## Phần 1: Các phương pháp RAG (Retrieval-Augmented Generation) tổng quát

Trong tuần đầu tiên, nhóm đã tiến hành khảo sát và tổng hợp các phương pháp RAG từ cơ bản đến nâng cao (theo các nghiên cứu cập nhật 2025-2026). Dưới đây là các nhóm kỹ thuật nổi bật (chi tiết tham khảo tại [01_RAG_METHODs.md](../../research/01_RAG_METHODs.md)):

1. **Naive RAG (RAG cơ bản):**
   - **Cơ chế:** Cắt nhỏ văn bản thành các chunk cố định, nhúng (embedding) thành vector và tìm kiếm thông qua cosine similarity.
   - **Ưu/Nhược:** Dễ triển khai, chi phí thấp, nhưng thiếu ngữ cảnh diện rộng và dễ truy xuất sai nếu từ ngữ trong câu hỏi không khớp hoàn toàn với văn bản gốc.

2. **Nâng cao Chunking & Indexing:**
   - **Parent-Child Retrieval:** Tìm kiếm trên các chunk nhỏ để tăng độ chính xác (match), nhưng khi đưa vào LLM thì trả về nguyên đoạn văn lớn bao quanh nó (Parent) để giữ trọn vẹn ngữ cảnh.
   - **Contextual Retrieval:** Sử dụng LLM để viết thêm một đoạn ngữ cảnh giới thiệu ngắn (ví dụ: "Đoạn văn này nói về...") và gắn vào đầu mỗi chunk trước khi đưa vào lưu trữ, giúp chunk đứng độc lập không bị tối nghĩa.

3. **Hybrid Retrieval & Re-ranking (Tiêu chuẩn hiện nay):**
   - **Hybrid Search:** Kết hợp song song tìm kiếm theo Ngữ nghĩa (Dense Vector) và tìm kiếm theo Từ khóa chính xác (Sparse/BM25). Cực kỳ hiệu quả cho dữ liệu chứa nhiều tên riêng, mã số.
   - **Cross-Encoder Reranking:** Đưa top kết quả thô qua một mô hình đánh giá lại (Reranker) để tinh chỉnh thứ hạng ưu tiên trước khi đưa cho LLM tổng hợp.

4. **Query Transformation (Tối ưu câu hỏi đầu vào):**
   - Dùng các kỹ thuật như **HyDE** (LLM sinh trước một câu trả lời giả định) hoặc **RAG-Fusion** (LLM tách câu hỏi ban đầu thành nhiều biến thể khác nhau) để dùng chính những biến thể/giả định này đem đi tìm kiếm, giúp mở rộng phạm vi và tăng tỷ lệ tìm thấy tài liệu liên quan.

5. **Adaptive & Self-Correcting RAG:**
   - **Adaptive RAG:** Phân loại tự động xem câu hỏi đang hỏi là dễ hay khó. Nếu dễ thì gọi thẳng LLM trả lời, nếu khó thì mới kích hoạt cơ chế tra cứu đa bước.
   - **CRAG / Self-RAG:** Cung cấp cho LLM khả năng tự chấm điểm tài liệu tìm được. Nếu tài liệu bị sai, cũ, hoặc không liên quan, LLM có thể tự động bỏ qua và kích hoạt chế độ Web Search để lấy thông tin mới.

6. **GraphRAG & Agentic RAG:**
   - **GraphRAG:** Xây dựng một đồ thị tri thức (Knowledge Graph) toàn diện bằng LLM. Siêu việt trong việc trả lời các câu hỏi mang tính khái quát cao (cần phải tóm tắt thông tin trên toàn bộ hệ thống tài liệu).
   - **Agentic RAG:** Tác tử AI tự động lập kế hoạch, truy vấn từng phần qua nhiều công cụ khác nhau (VectorDB, APIs) một cách tuần tự để hoàn thiện một báo cáo phức tạp. Cực mạnh nhưng vô cùng đắt đỏ.

---

## Phần 2: Đánh giá các bộ Dataset phục vụ bài toán RAG Nhạy cảm thời gian

Để phục vụ cho hệ thống *Time-Aware Agentic Memory*, nhóm đã đọc và so sánh 4 bộ dữ liệu (Dataset) công khai. Kết quả phân tích cụ thể:

### 1. [TimeSensitiveQA](../../dataset/01_TIME_SENSITIVE_QA.md) ([GitHub](https://github.com/wenhuchen/Time-Sensitive-QA))
- **Ngôn ngữ:** Tiếng Anh.
- **Dung lượng:** Rất nhẹ (File nén ~100MB, tổng giải nén < 1GB). Tối ưu cho cấu hình máy tính cá nhân.
- **Cấu trúc:** Gồm câu hỏi tự luận ngắn và văn bản gốc là tiểu sử nhân vật.
- **Dạng câu hỏi & Đánh giá (Evaluation):** Câu hỏi tự luận (Generative/Extractive QA). Hệ thống tự động chấm điểm bằng độ đo **Exact Match (EM)** và **F1-score** (so khớp chuỗi từ vựng do AI sinh ra xem có chứa đáp án chuẩn "Gold answers" không).
- **Điểm mạnh:** Có hệ thống câu hỏi lặp lại theo dõi sự thay đổi của cùng 1 đối tượng qua nhiều mốc thời gian (Longitudinal Tracking). Cực kỳ lý tưởng cho bài toán theo dõi tiến trình sự kiện dài hạn.
- **Điểm yếu:** Đoạn văn bản thô (raw data) chưa được chia nhỏ theo dòng thời gian mà bị trộn lẫn; cần phải tự viết script tiền xử lý (chunking).

### 2. [ChronoQA](../../dataset/02_CHRONO_QA.md) ([GitHub](https://github.com/czy1999/ChronoQA))
- **Ngôn ngữ:** Tiếng Trung (Chinese).
- **Dung lượng:** Trung bình (Vài trăm MB - 2GB).
- **Cấu trúc:** Các bài báo nhỏ được dán nhãn mốc thời gian cụ thể ngay từ đầu dòng.
- **Dạng câu hỏi & Đánh giá (Evaluation):** Câu hỏi tự luận. Chấm điểm bằng **Exact Match (EM)**, **F1-score** và **Rouge-L**.
- **Điểm mạnh:** Rất tốt cho việc kiểm tra khả năng bắt filter thời gian của mô hình (ví dụ hỏi "hôm nay", "tháng trước").
- **Điểm yếu:** Dữ liệu hoàn toàn bằng Tiếng Trung, nguy cơ hỏng ngữ cảnh khi dịch máy. Các sự kiện rất rời rạc, **không** có tính liên tục theo dõi 1 đối tượng.

### 3. [StreamingQA](../../dataset/03_STREAMING_QA.md) ([GitHub](https://github.com/google-deepmind/streamingqa))
- **Ngôn ngữ:** Tiếng Anh.
- **Dung lượng:** Bất đối xứng và siêu khổng lồ (văn bản thô lên tới hàng trăm GB).
- **Cấu trúc:** Dựa trên tập WMT News Crawl (14 năm tin tức quốc tế).
- **Dạng câu hỏi & Đánh giá (Evaluation):** Câu hỏi tự luận. Chấm điểm bằng **Exact Match (EM)** và **F1-score**.
- **Điểm mạnh:** Giả lập xuất sắc một luồng tin tức liên tục cập nhật theo thời gian, tính ghi đè thông tin cực mạnh.
- **Điểm yếu:** Dung lượng cực lớn là **điểm yếu chí mạng**, không thể trích xuất và triển khai trên máy tính cá nhân. Nội dung quá rộng, không tập trung được vào một lĩnh vực cụ thể.

### 4. [RealTime QA](../../dataset/04_REALTIME_QA.md) ([GitHub](https://github.com/realtimeqa/realtimeqa_public))
- **Ngôn ngữ:** Tiếng Anh.
- **Dung lượng:** Cực kỳ nhỏ gọn (~400MB cho toàn bộ các năm).
- **Cấu trúc:** Câu hỏi trắc nghiệm cập nhật theo từng tuần dựa trên Breaking News.
- **Dạng câu hỏi & Đánh giá (Evaluation):** Câu hỏi **Trắc nghiệm (Multiple Choice - A,B,C,D)**. Chấm điểm cực kỳ đơn giản bằng tỷ lệ chọn đúng đáp án **(Accuracy)**.
- **Điểm mạnh:** Phân chia theo tuần (Folder) rất khoa học, dễ dàng nạp vào hệ thống để test tính cập nhật kiến thức mới (Freshness).
- **Điểm yếu:** Các câu hỏi hoàn toàn rời rạc (sự kiện ngẫu nhiên trong tuần). **Không** dùng được cho bài toán cốt truyện phức tạp có tính tiến hóa dài hạn.

### 5. [SituatedQA](../../dataset/05_SITUATED_QA.md) ([HuggingFace](https://huggingface.co/datasets/siyue/SituatedQA))
- **Ngôn ngữ:** Tiếng Anh.
- **Cấu trúc:** Chỉ là tập câu hỏi (Queries) có gắn nhãn thời gian hoặc địa lý. Ví dụ: `"who is the prime minister of australia?" + date: "2012"`.
- **Dạng câu hỏi & Đánh giá (Evaluation):** Câu hỏi mở tự luận. Chấm điểm bằng **Exact Match (EM)**.
- **Điểm mạnh:** Kiểm tra rất tốt khả năng LLM hiểu bối cảnh ngoài ngôn ngữ (Extra-Linguistic Context).
- **Điểm yếu (Chí mạng):** Hoàn toàn **KHÔNG CÓ văn bản thô (Corpus)** đi kèm. Nó đòi hỏi hệ thống RAG phải tự lấy một kho dữ liệu khổng lồ (như Wikipedia) để tìm kiếm. Do đó, không có gì để ta "chia chunk gắn timestamp" ở đây cả.

### 6. [TempLAMA](../../dataset/06_TEMPLAMA.md) ([HuggingFace](https://huggingface.co/datasets/Yova/templama))
- **Ngôn ngữ:** Tiếng Anh.
- **Cấu trúc:** Truy vấn dạng điền vào chỗ trống (Cloze-style) lấy từ Wikidata. Ví dụ: `"Cristiano Ronaldo plays for [MASK]" + date: "2012"`.
- **Dạng câu hỏi & Đánh giá (Evaluation):** Điền vào chỗ trống. Chấm điểm bằng **Exact Match (Hits@1)** (xem từ điền vào có khớp chính xác 100% với tên thực thể gốc không).
- **Điểm mạnh:** Có sự theo dõi dọc sự nghiệp của 1 người qua các năm (Rất giống TimeSensitiveQA).
- **Điểm yếu (Chí mạng):** Giống như SituatedQA, nó **KHÔNG CÓ văn bản thô (Corpus)**. Bộ này chỉ sinh ra để test trí nhớ nội tại của LLM (Knowledge Graph), không dùng để nạp vào VectorDB làm RAG.

### 📌 Kết luận Tuần 1:
Qua đánh giá Ngôn ngữ, Dung lượng và Cấu trúc:
- **StreamingQA** bị loại (Quá nặng).
- **ChronoQA** bị loại (Tiếng Trung).
- **RealTime QA** bị loại (Quá rời rạc, không theo dõi sự kiện liên tục).
- **SituatedQA & TempLAMA** bị loại (Chỉ có câu hỏi, không hề cung cấp Văn bản thô/Raw text để làm RAG).

Bộ **TimeSensitiveQA** là ứng viên duy nhất hội đủ tính chất theo dõi dọc (Longitudinal Tracking). Vấn đề lớn nhất của bộ dữ liệu này không phải là ngôn ngữ, mà là văn bản thô (`paras`) đang chứa lẫn lộn nhiều sự kiện ở các mốc thời gian khác nhau trong cùng một đoạn dài. Do đó, hướng đi cốt lõi tiếp theo là **xây dựng thuật toán tiền xử lý (Preprocessing)** để tự động bóc tách các sự kiện trong `paras` thành những chunk nhỏ, mỗi chunk được gán một `timestamp` riêng biệt rõ ràng trước khi nạp vào Vector Database.
