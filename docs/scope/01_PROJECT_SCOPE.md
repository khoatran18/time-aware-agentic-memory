# Đề tài: Time-Aware Agentic Memory (Bộ nhớ có nhận thức thời gian cho AI)

## 1. Bối cảnh và vấn đề cốt lõi

Các hệ thống AI (đặc biệt là LLM + RAG) thường xử lý thông tin như một **kho dữ liệu tĩnh**: toàn bộ tài liệu được embed và lưu trữ như thể chúng đều "đúng ngang nhau tại mọi thời điểm". Nhưng thực tế, thông tin luôn thay đổi theo thời gian, và điều này gây ra 3 loại lỗi phổ biến:

| Loại lỗi | Ví dụ |
|---|---|
| **"Lời nguyền" của dữ liệu tĩnh** | AI học từ tài liệu cũ, không biết thông tin đã lỗi thời |
| **Mâu thuẫn thông tin theo thời gian** | Hôm qua ai đó là "nghi phạm", hôm nay là "bị cáo" — AI dùng nhầm nhãn cũ |
| **Thời gian tương đối** | Văn bản viết "tuần trước" — AI đọc lại nhiều tháng sau sẽ hiểu sai mốc thời gian tuyệt đối |

**Mục tiêu đề tài:** xây dựng cơ chế giúp AI "nhận thức được thời gian" — biết đâu là thông tin còn hiệu lực, đâu là thông tin đã cũ, và tự tổng hợp được diễn biến của một sự kiện/thực thể theo đúng trình tự thời gian.

### Các loại truy vấn/xử lý hệ thống cần giải quyết
Để đáp ứng mục tiêu trên, hệ thống cần xử lý tốt 3 tình huống/loại câu hỏi chính:
1. **Truy xuất thông tin tại một mốc thời gian cụ thể:** Lấy đúng thông tin tại thời điểm được hỏi (Ví dụ: "Hiện tại ai là Tổng thống Mỹ?", hoặc "Năm 2005 ai là Thủ tướng Anh?").
2. **Tóm tắt sự kiện theo dòng thời gian:** Tổng hợp thông tin từ nhiều mốc thời gian để vẽ nên một bức tranh toàn cảnh (Ví dụ: "Tóm tắt quá trình phát triển sự nghiệp của nhân vật X").
3. **Xử lý xung đột dữ liệu & Cập nhật luồng tin (Streaming Updates & Belief Revision):** Khi có thông tin mâu thuẫn, hệ thống không chỉ áp dụng luật "mới nhất là đúng nhất". Nó phải biết cách xử lý linh hoạt:
   - **Xung đột đa nguồn:** Ưu tiên thông tin từ các nguồn uy tín hơn (Credibility) khi 2 nguồn đưa tin khác nhau cùng lúc.
   - **Cập nhật tin tức phá vỡ (Breaking News / Amendments):** Nhận diện được tính "ghi đè" của tin mới lên tin cũ (ví dụ: ngày 1 A là nghi phạm, ngày 2 A là thủ phạm, ngày 3 B bị oan) và dùng thuật toán (như Re-ranking bằng khoảng cách thời gian) để truy xuất chính xác trạng thái sự việc tại bất kỳ mốc thời gian nào người dùng yêu cầu.

## 2. Phân tách rạch ròi 3 Cơ chế cốt lõi (Scope Boundaries)

Đây là phần định nghĩa ranh giới cực kỳ quan trọng để tránh nhầm lẫn về mặt khái niệm khi thiết kế kiến trúc hệ thống và bảo vệ trước hội đồng. Đồ án sẽ tập trung vào 3 cơ chế sau (có thể chọn 2/3 để đi sâu):

### Cơ chế 1: Temporal Retrieval (Truy xuất dựa trên Thời gian)
- **Định nghĩa:** Khả năng hệ thống hiểu được mốc thời gian NGẦM Ý trong câu hỏi để tìm ra đúng tài liệu.
- **Bản chất:** Câu hỏi thường chứa các từ như *"gần đây", "mới nhất", "hiện tại", "năm ngoái"*.
- **Ví dụ:** *"Quy định xây dựng hiện tại là gì?"* -> Hệ thống phải biết tự lấy năm 2024 làm mốc.
- **Công nghệ đề xuất:** Time-aware Query Rewriting (Agent tự phân tích prompt để nhét thêm timestamp) + Metadata Filtering.

### Cơ chế 2: Timeline Summarization (Tóm tắt Dòng thời gian)
- **Định nghĩa:** Việc hệ thống tổng hợp một loạt các sự kiện thay đổi theo thời gian của một Thực thể/Vấn đề cụ thể. 
- **Lưu ý ranh giới (Sự tiến hóa - Evolution):** *"Năm 2005 ông A làm Giám đốc, năm 2007 ông A làm Chủ tịch"*. **ĐÂY KHÔNG PHẢI LÀ XUNG ĐỘT (CONFLICT).** Đây là một tiến trình logic hợp lý, con người lớn lên và thay đổi. Nhiệm vụ của hệ thống ở đây là nhặt đủ các mảng ký ức đó và xếp nó thành một sợi dây liền mạch.
- **Ví dụ:** *"Tóm tắt sự nghiệp của ông A từ 2005 đến nay"*. Hoặc *"Diễn biến vụ án X"*.
- **Công nghệ đề xuất:** TA-RAG (Băm Bucket trên VectorDB) hoặc Đồ thị TG-RAG (Nếu muốn mở rộng).

### Cơ chế 3: Conflict Resolution (Giải quyết Xung đột / Mâu thuẫn)
Đây là phần dễ bị nhầm lẫn nhất với Cơ chế 2. Cần phân định rạch ròi: **Có Timestamp KHÔNG đồng nghĩa với việc hết xung đột!**
Xung đột xảy ra khi tồn tại một lượng thông tin mâu thuẫn nhau về cùng một Vấn đề/Sự kiện. Có 3 nguyên nhân cốt lõi gây ra xung đột mà hệ thống phải xử lý:

1. **Sự thiên vị của VectorDB (Semantic Bias):**
   - Luật năm 2020: *"Cho phép xây nhà 5 tầng ở phố X"* (VectorDB chấm Semantic = 0.9 vì wording cực giống câu hỏi).
   - Luật năm 2024: *"Quy hoạch mới cấm xây nhà 5 tầng"* (VectorDB chấm = 0.6 vì dùng từ vựng khác).
   - *Kết quả:* Vector lôi quy định 2020 ra làm top 1. Nếu không có thuật toán đánh trọng số (Half-life Decay), LLM sẽ trả lời sai thực tại.
2. **Nhiễu loạn Nguồn tin (Cùng 1 Timestamp):**
   - Báo A (15/10/2023): *"Ông X bị bắt"*.
   - Báo B (15/10/2023): *"Ông X chỉ bị triệu tập"*.
   - *Kết quả:* Cùng một mốc thời gian, nhưng 2 nguồn nói khác nhau. Không thể dùng bộ lọc Timestamp thông thường. Agent phải dùng khả năng suy luận để đối chiếu điểm uy tín (Credibility Score) của Nguồn tin.
3. **Sự thay thế không rõ ràng (Implicit Supersede / Knowledge Drift):**
   - Nhiều quy định/sự kiện mới sinh ra không hề có câu *"Quy định này bãi bỏ quy định cũ"*, mà nó chỉ âm thầm phủ định. LLM đọc cả 2 sẽ bị lú lẫn không biết dùng cái nào.
   - *Giải pháp đề xuất:* Dùng Đồ thị Tiến hóa Sự kiện (Chronos Event Evolution Graph) để dán nhãn rạch ròi: `[Sự thật 2024] --(Lật đổ/Thay thế)--> [Sự thật 2020]`.

**=> Tóm tắt ranh giới:**
- **Cơ chế 2 (Timeline):** *"Cho tôi xem quá trình thay đổi"*. (Giữ lại tất cả).
- **Cơ chế 3 (Conflict):** *"Có 2 thông tin đang đập nhau, hãy nói cho tôi biết hiện tại cái nào mới là sự thật"*. (Lọc bỏ cái sai/cái cũ).

## 3. Ứng dụng thực tế minh họa (không bắt buộc làm cả 2)

- **LegalMind:** theo dõi thay đổi quy định pháp lý, cảnh báo khi điều khoản cũ đã bị thay thế bởi văn bản mới.
- **StockMem:** theo dõi tin tức tài chính để hiểu vì sao 1 sự kiện cũ (VD: cuộc họp Fed 2 tuần trước) vẫn đang ảnh hưởng đến giá cổ phiếu hôm nay.

→ Đây là ví dụ minh họa cho lý thuyết, nhóm nên chọn **1 domain** (luật, tài chính, hoặc giữ nguyên domain tin tức/tiểu sử như trong dataset có sẵn) để làm case study, không cần làm cả 2.

## 4. Cách đánh giá

**Temporal Freshness (độ tươi mới thời gian):** đo thời gian/độ chính xác mà hệ thống mất để "cập nhật" kiến thức mới sau khi có thông tin thay đổi. Hệ thống càng tốt thì phục hồi càng nhanh và chính xác sau khi dữ liệu cập nhật.

Trong thực nghiệm, có thể quy về các metric cụ thể hơn:
- **Exact Match (EM) / F1** — so khớp câu trả lời sinh ra với đáp án đúng theo đúng khung thời gian được hỏi.
- **Accuracy theo từng "time slice"** — chia câu hỏi theo giai đoạn thời gian, đo độ chính xác riêng cho từng giai đoạn để xem hệ thống có bị lệch về phía thông tin "mới nhất" hay "cũ nhất" hay không.

## 5. Kiến trúc hệ thống cần tự xây dựng (không có sẵn trong dataset)

Các bộ dữ liệu benchmark (TimeQA, StreamingQA...) chỉ cung cấp **câu hỏi + văn bản + đáp án chuẩn** để đo khả năng đọc-hiểu thô của mô hình. Phần kiến trúc "time-aware" là **đóng góp chính của nhóm**, cần tự thiết kế, bao gồm:

- Bước tiền xử lý: trích xuất timestamp từ văn bản, gắn nhãn cho từng đoạn/chunk trước khi embedding.
- Bước retrieval có ưu tiên thời gian: khi có nhiều đoạn liên quan, ưu tiên đoạn có timestamp phù hợp nhất với câu hỏi (thay vì chỉ dựa vào độ tương đồng ngữ nghĩa thuần túy).
- Bước tổng hợp: nếu câu hỏi không nêu rõ mốc thời gian, cần quyết định chính sách mặc định (ưu tiên thông tin mới nhất, hoặc yêu cầu làm rõ) — đây là lựa chọn thiết kế của nhóm, dataset không quy định sẵn.
- Bước so sánh: đánh giá hệ thống "time-aware" của nhóm so với baseline RAG thông thường (không phân biệt thời gian) để chứng minh giá trị đóng góp.

## 6. Lựa chọn dataset theo từng cơ chế (tóm tắt)

| Cơ chế | Dataset phù hợp | Ghi chú |
|---|---|---|
| A – Timeline Summarization | TimeQA | Có sẵn context, dễ triển khai nhất |
| B – Longitudinal Tracing | TimeQA (thiếu phần "horizontal") | Cần bổ sung dữ liệu đa nguồn nếu muốn làm đủ cả ngang-dọc |
| C – Temporal conflict (đơn giản hóa) | TimeQA | Có thể test dạng "temporal conflict" đơn nguồn |
| C – Multi-source conflict (đầy đủ) | StreamingQA, ChronoQA, LiveFact (mới, 2026) | Cần dữ liệu tin tức có timestamp ngày/giờ thực; hiện ít benchmark public đã hoàn thiện — có thể cần tự crawl bổ sung (VD: lịch sử chỉnh sửa Wikipedia) |

Xem chi tiết tính chất của TimeQA trong file `timeqa-dataset-info.md` đi kèm.