# Time-Aware Agentic Memory: Initial Ideas & Literature

Đây là nơi lưu trữ các ý tưởng thiết kế cốt lõi và các tài liệu tham khảo quan trọng để định hình kiến trúc của dự án.

## 1. Phương pháp: Event-Centric Temporal Knowledge Graph (TKG)
- **Nguồn:** [Nghiên cứu "Event-Centric Temporal Knowledge Graph Construction: A Survey"](https://www.researchgate.net/publication/376181551_Event-Centric_Temporal_Knowledge_Graph_Construction_A_Survey)
- **Ý tưởng cốt lõi:** Các đồ thị tri thức và cơ sở dữ liệu vector truyền thống chỉ lưu trữ các "Thực thể tĩnh" (Ví dụ: Obama là tổng thống). Cách làm này thất bại khi áp dụng vào trục thời gian dài hạn.
- **Áp dụng vào Dự án DATN:**
  - Chuyển hướng lưu trữ sang **Lấy Sự Kiện (Event) làm trung tâm**.
  - Mỗi Chunk được đưa vào VectorDB không phải là một đoạn văn chung chung, mà phải là một **Sự kiện cụ thể đi kèm chặt chẽ với Mốc thời gian (Timestamp)**.
  - Công thức: `Chunk = Event Text + [Start_Time, End_Time]`.
  - Khớp hoàn toàn với cấu trúc của file `annotated` trong bộ dữ liệu TimeSensitiveQA mà chúng ta đang sử dụng để làm dữ liệu tiền xử lý (Preprocessing).

## 2. Phương pháp: Streaming RAG (Cập nhật dữ liệu thời gian thực)
- **Nguồn:** [Nghiên cứu "From Static to Dynamic: A Streaming RAG Approach to Real-time Knowledge Base"](https://arxiv.org/abs/2508.05662)
- **Ý tưởng cốt lõi:** Đề xuất cơ chế đường ống cập nhật gia tăng (Incremental Upsert Mechanism) để đưa dữ liệu luồng (news feed, mạng xã hội) vào VectorDB ngay lập tức.
- **Cơ chế Upsert (Chèn & Ghi đè) và Bài toán Tốc độ:**
  - **Khó khăn của VectorDB truyền thống:** Khác với CSDL SQL thông thường, VectorDB lưu trữ dữ liệu dưới dạng Không gian đa chiều (như cấu trúc đồ thị HNSW). Việc tự ý chèn hay ghi đè một Vector mới đòi hỏi phải tính toán lại khoảng cách với hàng triệu Vector cũ để nối lại các mắt xích đồ thị. Việc này cực kỳ chậm (độ trễ cao) và thường làm treo hệ thống (phải offline để Rebuild Index).
  - **Cách thuật toán khắc phục:** Thay vì bắt VectorDB nuốt từng tin tức một, thuật toán xây dựng một "phễu lọc" cực mạnh gồm 3 bước:
    1. *Sàng lọc Cosine (Cosine screening):* Loại bỏ cực nhanh các tin tức rác không liên quan đến kho tri thức hiện tại.
    2. *Bộ đếm dội bom (Heavy-hitter filter):* Nhận diện các sự kiện đang "hot" được nhiều báo đưa tin trùng lặp, từ đó gộp chúng lại để không lưu trữ dư thừa.
    3. *Gom cụm (Mini-batch clustering):* Ép 100 văn bản lọt qua bộ lọc lại thành 10 Vector cốt lõi (Prototypes) mang tính đại diện.
  - **Kết quả:** Nhờ khối lượng dữ liệu đã bị nén lại cực nhỏ gọn và tinh túy, quá trình Upsert (Ghi đè/Chèn mới) diễn ra trơn tru ở dưới nền (background) chỉ trong 15ms mà không hề làm gián đoạn các truy vấn đang chạy của người dùng.
- **Ghi chú đối với DATN:** Việc **"Ghi đè" (làm mất lịch sử cũ)** đi ngược lại với nguyên lý của Agentic Memory (Cần nhớ cả quá khứ dài hạn). Tuy nhiên, kiến trúc gom cụm (mini-batch clustering) và bộ lọc chống trùng lặp của bài báo này là một tư tưởng xuất sắc để áp dụng nhằm tăng tốc độ nạp dữ liệu cho hệ thống của chúng ta.

## 3. Kiến trúc Lưu trữ: Context Graphs kết hợp Vector Search
- **Nguồn:** [Context Graphs vs. Vector Search: When RAG Falls Short (Redis Blog)](https://redis.io/blog/context-graphs-vs-vector-search/)
- **Ý tưởng cốt lõi:** Chỉ ra nhược điểm chí mạng của Vector Search là tuy tìm kiếm ngữ nghĩa (Semantic similarity) rất giỏi nhưng lại "mù" về mặt quan hệ cấu trúc (không hiểu rõ A có quan hệ gì với B). Trong khi đó, Đồ thị ngữ cảnh (Context Graphs) lại vẽ ra các mối quan hệ rất rành mạch nhưng lại cứng nhắc.
- **Áp dụng vào Dự án DATN:** Củng cố thiết kế Hybrid (Lai tạo). Hệ thống Agentic Memory cần tận dụng khả năng tìm kiếm của Vector Search, kết hợp với các siêu dữ liệu (Metadata) dưới dạng Đồ thị Thời gian (Temporal Graph) để AI hiểu được luồng diễn biến của sự kiện.

## 4. Giải quyết Vấn đề: Lỗi "Conflicting Context" (Ngữ cảnh xung đột)
- **Nguồn:** [Your RAG System Retrieves the Right Data but Still Produces Wrong Answers: Here’s Why (Towards Data Science)](https://towardsdatascience.com/your-rag-system-retrieves-the-right-data-but-still-produces-wrong-answers-heres-why-and-how-to-fix-it/)
- **Ý tưởng cốt lõi:** Hệ thống RAG thường dính một lỗi "tàng hình": Database kéo về đúng các tài liệu liên quan, nhưng nội dung của các tài liệu đó lại mâu thuẫn/xung đột với nhau (Ví dụ: Năm 2018 nói A làm giám đốc, Năm 2023 nói B làm giám đốc). Do không có khả năng phân xử thời gian, AI sẽ bị "lú" và đoán mò, dẫn đến trả lời sai bét dù điểm Cosine Similarity của bước Retrieval rất cao.
- **Áp dụng vào Dự án DATN:** 
  - Đây chính là **Lời biện minh lý thuyết (Theoretical Justification)** hoàn hảo cho toàn bộ dự án. 
  - Hệ thống Time-Aware Agentic Memory ra đời chính là để đóng vai trò làm lớp "Giải quyết xung đột" (Resolution layer). Bằng cách băm Chunk gắn liền với Timestamp và sắp xếp chúng theo trục thời gian trước khi đưa vào Prompt (cảm hứng từ bài báo FreshPrompt), AI sẽ không còn bị lú lẫn bởi các Context xung đột nữa.
