# Khảo sát về Temporal Question Answering (TQA)

## 1. Thông tin chung về bài báo
- **Tên bài báo:** It's High Time: A Survey of Temporal Question Answering
- **Liên kết:**
  - **Mã arXiv (PDF gốc):** [2505.20243](https://arxiv.org/abs/2505.20243)
  - **Bản HTML (version 2):** [https://arxiv.org/html/2505.20243v2](https://arxiv.org/html/2505.20243v2)
- **Kho dữ liệu (GitHub):** [TemporalQA-Survey](https://github.com/DataScienceUIBK/TemporalQA-Survey)
- **Quy mô khảo sát:** Bài báo hệ thống hóa **27+ bộ dữ liệu**, hơn **2.5 triệu câu hỏi** trải dài từ năm 1367 đến 2025 trong các lĩnh vực News, Web và Knowledge Bases.

---

## 2. Phân loại 5 nhóm Dataset chính trong TQA
Dựa theo tổng hợp của bài báo, các bộ dữ liệu TQA được chia thành các nhóm sau:

### 2.1. 🗞️ Diachronic Datasets (Văn bản lịch sử theo dòng thời gian)
- Tương ứng với các kho tài liệu có gắn timestamp trải qua nhiều năm.
- **Tiêu biểu:** `ArchivalQA` (1987-2007), `ChroniclingAmericaQA` (1800-1920), `StreamingQA` (2007-2020), `NewsQA`, `TempLAMA`.
- **Giải đáp: Tại sao ChroniclingAmericaQA lại ÍT phù hợp với đồ án của bạn?**
  - Mặc dù đây là một bộ dữ liệu khổng lồ (485K câu hỏi), nhưng nội dung của nó là **báo chí cổ của Mỹ từ năm 1800 - 1920**. 
  - Nếu đồ án của bạn muốn biểu diễn năng lực của Agentic Memory trong việc cập nhật tin tức thời sự hiện đại, đính chính thông tin kinh tế/chính trị ngày nay, thì việc dùng báo từ thế kỷ 19 sẽ giống như đang xây dựng một "Nhà sử học AI" thay vì một trợ lý AI hiện đại. Các sự kiện trong đó đã "chốt hạ", không còn tính chất biến động (Streaming) của thời sự ngày nay. Thay vào đó, **StreamingQA** (2007-2020) sẽ là lựa chọn phù hợp hơn rất nhiều.

### 2.2. 📖 Synchronic Datasets (Dữ liệu dạng Snapshot tĩnh)
- Lấy một lát cắt của cơ sở tri thức tại một thời điểm (thường là Wikipedia).
- **Tiêu biểu:** `TimeQA` (bộ bạn đang dùng), `ComplexTempQA`, `SituatedQA`, `MenatQA`.
- **Nhận xét:** Rất tốt cho cơ chế tóm tắt dòng thời gian (Cơ chế 2) và truy xuất mốc thời gian (Cơ chế 1) của một thực thể (như quá trình công tác của một nhân vật). Nhưng nhược điểm là không có tính chất đa nguồn để xử lý xung đột (Cơ chế 3).

### 2.3. 🌐 Web & Real-Time Datasets (Dữ liệu thời gian thực)
- Đánh giá khả năng tìm kiếm thông tin đang biến động.
- **Tiêu biểu:** `ReaLTimeQA` (cập nhật hàng tuần), `FreshQA`.

### 2.4. 🧪 Synthetic & Reasoning-Focused (Bộ dữ liệu chuyên suy luận)
- Được sinh ra có chủ đích để ép AI giải quyết các logic thời gian hóc búa.
- **Tiêu biểu:** `ContextAQA`, `ContextTQE`, `COTEMPQA`.
- ⚠️ **Lưu ý về ContextAQA & ContextTQE:** Như đã phân tích, 2 bộ dữ liệu này được sinh ra trong bài báo *Context Matters* để test độ nhiễu. Tuy nhiên, tác giả **không public** link tải dataset (không có trên HuggingFace hay GitHub). Do đó, bạn chỉ có thể đọc paper để lấy cảm hứng thiết kế thuật toán, chứ **không thể tải về để train/test cho đồ án**.

### 2.5. 🧩 KG-based (Dựa trên Knowledge Graph)
- Cấu trúc suy luận dựa trên đồ thị tri thức có gắn nhãn thời gian.

---

## 3. Các hướng tiếp cận (Methods & Approaches)
Bài báo vẽ ra dòng thời gian tiến hóa của công nghệ xử lý TQA:

1. **2003-2010 (Rule-Based Era):** Dùng luật, regex, thẻ tag thủ công (TimeML, HeidelTime).
2. **2011-2019 (Statistical & Early Neural):** Dùng mô hình ngôn ngữ thống kê, embedding thời gian.
3. **2020-2022 (Transformer Revolution):** Ra đời các kiến trúc nhúng thẳng yếu tố thời gian vào model:
   - `TempoT5`, `TempoBERT`, `BiTimeBERT` (nhúng timestamp vào embedding).
4. **2023-2025 (LLM & RAG Era):** Sử dụng RAG kết hợp thời gian. 
   - **Các hệ thống Temporal RAG nổi bật:** `TempRetriever`, `TimeR4`, `MRAG`, `TempRALM`, `FreshLLMs`. *(Đây chính là mỏ vàng để bạn tham khảo các luồng thiết kế Agentic RAG cho đồ án của mình).*

---

## 4. Các Task xử lý thời gian cốt lõi (Temporal Tasks)
Bên cạnh việc trả lời câu hỏi, bài báo định nghĩa các "kỹ năng" ngầm AI cần có:
- **Event Dating:** Trích xuất mốc thời gian của một sự kiện từ văn bản.
- **Document Dating:** Đoán ngày viết tài liệu dựa trên văn phong và nội dung.
- **Focus Time Estimation:** Ước lượng khoảng thời gian mà văn bản đang đề cập tới.
- **Query Time Profiling:** Phân tích câu hỏi của người dùng để xem họ đang mồi tìm kiếm thông tin ở mốc thời gian nào.

---

## 5. Ứng dụng thực tế theo Domain
TQA không chỉ dùng để hỏi đáp chung chung, mà có tính ứng dụng sống còn ở các lĩnh vực:
- **Y tế (Medical):** Tái tạo dòng thời gian bệnh án, tiến triển triệu chứng (VD: `TimeText`, `Temporal Clinical QA`).
- **Pháp lý (Legal):** Theo dõi sửa đổi luật, sự thay đổi của tiền lệ pháp (VD: `ChronosLex`).
- **Tài chính (Financial):** Xử lý báo cáo tài chính, biến động thị trường theo thời gian thực (VD: `FinQA`, `FinDER`). 

---

## 6. 7 Định hướng Tương lai (Future Directions)
Bài báo chốt lại 7 vấn đề cốt lõi mà giới nghiên cứu đang phải giải quyết. Đây cũng là những điểm bạn có thể đưa vào phần **"Ý nghĩa khoa học"** hoặc **"Hướng phát triển"** của đồ án:

1. **Quản lý tri thức động (Dynamic Temporal Knowledge Management):** Duy trì Knowledge Graph theo thời gian thực thay vì dữ liệu tĩnh.
2. **Tác tử AI nhận thức thời gian (Temporally-Aware LLM Agents):** Chống lại việc AI bị ảo giác về ngày tháng, hiểu được các từ "thứ Ba tuần trước", "từ lần trò chuyện trước".
3. **Tích hợp Đồng đại - Lịch đại (Diachronic-Synchronic Integration):** Trộn lẫn dữ liệu quá khứ và hiện tại một cách mạch lạc.
4. **Xử lý độ bất định (Temporal Uncertainty & Confidence):** Hiểu các mốc thời gian không chính xác như "khoảng thế kỷ 20", "vào cuối thời kỳ đồ đá".
5. **Đa ngôn ngữ & Đa phương thức:** Mở rộng ra xử lý thời gian trên hình ảnh, video và các lịch pháp khác nhau (âm lịch, v.v.).
6. **Hiểu ý định thời gian ngầm ẩn (Implicit Temporal Intent):** Biết người dùng muốn hỏi về thời điểm nào dù họ không gõ ngày tháng cụ thể.
7. **Tiêu chuẩn đánh giá (Evaluation & Benchmarking):** Tạo ra các thước đo độ mạch lạc của thời gian thay vì chỉ chấm điểm Text Accuracy.

---

## 7. Bảng So sánh Tổng hợp: Chọn Dataset cho Đồ án

Dựa trên toàn bộ phân tích trên, dưới đây là tổng kết bạn nên dùng bộ nào cho 3 cơ chế của đồ án:

| Tiêu chí / Cơ chế Đồ án | TimeQA (`01_TIME_SENSITIVE_QA.md`) | StreamingQA / ReaLTimeQA | ChroniclingAmericaQA | ContextAQA / ContextTQE |
|---|---|---|---|---|
| **Phân loại** | Synchronic (Tĩnh) | Diachronic/Web (Thời sự/Động) | Diachronic (Lịch sử) | Synthetic (Tạo sinh có chủ đích) |
| **Trạng thái Public** | ✅ Sẵn sàng trên HuggingFace | ✅ Sẵn sàng trên HuggingFace | ✅ Sẵn sàng | ❌ KHÔNG public link tải |
| **Hỗ trợ Cơ chế 1 & 2** | 🟢 Rất Tốt | 🟢 Rất Tốt | 🟢 Rất Tốt (nhưng là Sử học) | 🟢 Rất Tốt |
| **Hỗ trợ Cơ chế 3 (Xung đột/Update)**| 🔴 Kém (Chỉ có 1 nguồn Wikipedia)| 🟢 Rất Tốt (Kiểm thử tin tức cập nhật) | 🔴 Kém (Báo cũ đã đóng băng) | 🟢 Tốt |

**Chốt lại:**
- Hãy giữ **TimeQA** làm baseline chính để báo cáo (Vì tính dễ dùng, tài liệu đã làm kỹ).
- Bổ sung thêm **StreamingQA** vào thiết kế nếu bạn muốn biểu diễn tính năng **Xử lý xung đột thông tin đa nguồn (Cơ chế 3)**.
- Bỏ qua *ChroniclingAmericaQA* (trừ khi làm app lịch sử) và *ContextAQA* (vì tác giả không cho data).
