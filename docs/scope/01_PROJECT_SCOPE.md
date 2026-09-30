# Đề tài: Time-Aware Agentic Memory (Bộ nhớ có nhận thức thời gian cho AI)

## 1. Bối cảnh và vấn đề cốt lõi

Các hệ thống AI (đặc biệt là LLM + RAG) thường xử lý thông tin như một **kho dữ liệu tĩnh**: toàn bộ tài liệu được embed và lưu trữ như thể chúng đều "đúng ngang nhau tại mọi thời điểm". Nhưng thực tế, thông tin luôn thay đổi theo thời gian, và điều này gây ra 3 loại lỗi phổ biến:

| Loại lỗi | Ví dụ |
|---|---|
| **"Lời nguyền" của dữ liệu tĩnh** | AI học từ tài liệu cũ, không biết thông tin đã lỗi thời |
| **Mâu thuẫn thông tin theo thời gian** | Hôm qua ai đó là "nghi phạm", hôm nay là "bị cáo" — AI dùng nhầm nhãn cũ |
| **Thời gian tương đối** | Văn bản viết "tuần trước" — AI đọc lại nhiều tháng sau sẽ hiểu sai mốc thời gian tuyệt đối |

**Mục tiêu đề tài:** xây dựng cơ chế giúp AI "nhận thức được thời gian" — biết đâu là thông tin còn hiệu lực, đâu là thông tin đã cũ, và tự tổng hợp được diễn biến của một sự kiện/thực thể theo đúng trình tự thời gian.

## 2. Ba cơ chế nghiên cứu (không bắt buộc làm cả 3)

> **Lưu ý phạm vi:** Đây là 3 hướng tiếp cận được liệt kê trong tổng quan nghiên cứu, không phải 3 yêu cầu bắt buộc phải hoàn thành hết. Với nhóm 2 người và thời lượng đồ án, nên **chọn 1 (hoặc 1 chính + 1 phụ)** để đi sâu, thay vì dàn trải cả 3.

### A. Timeline Summarization (Tóm tắt theo dòng thời gian)
- **Ý tưởng:** thay vì lưu thông tin rời rạc, hệ thống tự trích xuất sự kiện + gắn nhãn thời gian, rồi dựng thành 1 chuỗi thời gian liên tục cho mỗi thực thể/chủ đề.
- **Input điển hình:** văn bản thô (không có sẵn timestamp tách riêng) → AI phải tự đọc và suy luận ra mốc thời gian từ câu chữ.
- **Output:** chuỗi các trạng thái theo thời gian, ví dụ: `[1997–2009: MP] → [2009–2013: journalist] → ...`
- **Lợi ích:** khi hỏi "hiện tại ra sao?", AI nhìn vào điểm cuối dòng thời gian thay vì bị nhiễu bởi thông tin cũ nằm rải rác trong văn bản.

### B. Longitudinal Event Tracing (Truy vết sự kiện theo chiều dọc)
- **Horizontal (ngang):** tổng hợp nhiều tin/nguồn trong cùng 1 thời điểm (VD: tất cả tin trong ngày hôm nay về 1 chủ đề).
- **Longitudinal (dọc):** nối các mốc thông tin về cùng 1 chủ đề qua nhiều tháng/năm để thấy được sự thay đổi (VD: dự thảo luật → luật chính thức).
- Đây là cơ chế mở rộng của A, thêm khả năng nhìn xuyên nhiều nguồn/thời điểm chứ không chỉ 1 timeline đơn lẻ.

### C. Streaming RAG & Conflict Resolution (RAG dạng luồng + xử lý mâu thuẫn)
Có **2 dạng "conflict"** cần phân biệt rõ (điểm dễ hiểu nhầm ban đầu):

1. **Temporal conflict (đơn nguồn, khác thời điểm)** — cùng 1 nguồn dữ liệu, nhưng thông tin về 1 thực thể thay đổi qua các giai đoạn khác nhau (VD: Ian Gibson là "MP" giai đoạn 1997–2009, rồi là "journalist" giai đoạn 2009–2013). Nếu RAG retrieval không phân biệt được câu hỏi đang hỏi về giai đoạn nào, nó dễ trộn lẫn 2 thông tin này lại. → **Không cần dữ liệu đa nguồn để test dạng conflict này.**
2. **Multi-source conflict (đa nguồn, cùng thời điểm)** — 2 nguồn tin khác nhau nói khác nhau về cùng 1 sự kiện tại cùng 1 thời điểm (VD: báo A nói 5 người chết, báo B nói 8 người chết). Cần cơ chế ưu tiên timestamp mới nhất + độ uy tín nguồn.

- **Cơ chế đề xuất:** coi dữ liệu như dòng chảy liên tục (streaming), có bộ lọc ưu tiên timestamp mới nhất và nguồn uy tín cao hơn khi có mâu thuẫn, lọc bớt nhiễu (heavy-hitter filter).

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