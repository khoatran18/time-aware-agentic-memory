# Các hệ thống agent memory hiện có (tổng quan)

> **Đã được thay thế phần lớn bởi các note đọc từ paper:** [`07_Zep_Graphiti_Temporal_KG.md`](07_Zep_Graphiti_Temporal_KG.md) (đọc PDF), [`08_Mem0_Agent_Memory.md`](08_Mem0_Agent_Memory.md) (đọc PDF), và bảng phân biệt tổng hợp ở [`11_Synthesis_and_Comparison.md`](11_Synthesis_and_Comparison.md) §2. File này giữ lại để tra nhanh Letta và A-Mem, **hai hệ thống chưa được đọc từ nguồn gốc**.

| Hệ thống | Biểu diễn | Thời gian | Mâu thuẫn | Độ tin cậy của mô tả |
|---|---|---|---|---|
| **Zep / Graphiti** | Temporal KG (đồ thị tri thức có thời gian), gồm entity, cạnh fact, episode | Bi-temporal: `valid_at`/`invalid_at` + `created_at`/`expired_at` | Đặt `invalid_at` cho cạnh cũ; không tách Evolution/Falsehood | Đã đọc paper → `07` |
| **Mem0 / Mem0^g** | Fact phẳng / triplet | Chỉ timestamp tạo; Mem0^g có cờ invalid | Mem0: DELETE; Mem0^g: đánh dấu invalid | Đã đọc paper → `08` |
| **Letta (MemGPT)** | Ngữ cảnh LLM như bộ nhớ ảo: core + archival + recall | Không có mô hình thời gian hiệu lực riêng **[chưa kiểm]** | Agent tự chỉnh bộ nhớ qua tool | Chỉ từ kết quả search, **chưa đọc paper** |
| **A-Mem** | Ghi chú kiểu Zettelkasten tự liên kết, tiến hóa | Hạn chế **[chưa kiểm]** | Ghi chú cũ được cập nhật theo ghi chú mới | Chỉ từ kết quả search, **chưa đọc paper** |

Giải thích nhanh các thuật ngữ trong bảng:
- **Agent memory** (trí nhớ của agent) là cách một chương trình dùng LLM (Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT, Gemini) lưu và nhớ lại thông tin giữa các lần trò chuyện. **Agent** là chương trình dùng LLM để tự lập kế hoạch và gọi công cụ. **Tool** là hàm mà LLM được phép gọi, ví dụ "ghi nhớ" hay "tìm lại".
- **KG** (Knowledge Graph, đồ thị tri thức) có nút là thực thể (người, tổ chức, sự vật) và cạnh là quan hệ giữa chúng. **Entity** là một thực thể; **fact** là một sự kiện được ghi thành cạnh (ví dụ "A làm việc tại X"); **episode** là một đơn vị dữ liệu đầu vào thô, như một tin nhắn hay một đoạn văn bản, mà từ đó hệ thống rút ra entity và fact.
- **Triplet** là bộ ba (chủ thể, quan hệ, đối tượng), ví dụ (Ông A, bị bắt, 2024). **Fact phẳng** là một câu sự kiện đơn lẻ, không nối với nhau thành đồ thị.
- **Bi-temporal** là theo dõi hai trục thời gian: lúc sự việc đúng ngoài đời (`valid_at` bắt đầu đúng, `invalid_at` hết đúng) và lúc hệ thống biết về nó (`created_at` thời điểm ghi vào hệ thống, `expired_at` thời điểm hệ thống coi bản ghi là hết hạn). **Timestamp tạo** là một mốc thời gian duy nhất ghi lúc bản ghi được tạo. **Cờ invalid** là dấu đánh dấu "không còn hợp lệ". **DELETE** là xóa hẳn bản ghi.
- **Evolution** (tiến hóa) là sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên lên giám đốc; đồ án xử lý bằng cách đóng `end_time` (thời điểm hết hiệu lực). **Falsehood** (sai lầm) là thông tin sai ngay từ đầu, ví dụ tin đồn bị đính chính; đồ án đánh dấu bằng `invalidated_at`. Zep dùng chung một cơ chế `invalid_at` cho cả hai nên không phân biệt được.
- **Letta (MemGPT)** coi cửa sổ ngữ cảnh của LLM như RAM của máy tính (bộ nhớ ảo): `core` là vùng luôn nằm trong ngữ cảnh, `archival` là kho lưu trữ dài hạn ngoài ngữ cảnh, `recall` là lịch sử hội thoại có thể tìm lại. **Zettelkasten** là phương pháp ghi chú bằng nhiều thẻ nhỏ, mỗi thẻ một ý và liên kết với thẻ khác.
- **Mem0^g** là biến thể của Mem0 lưu trí nhớ dưới dạng đồ thị (chữ g là graph).

Benchmark (bộ dữ liệu và câu hỏi chuẩn để đo và so sánh các hệ thống) chung của nhóm này gồm LoCoMo (Long-term Conversational Memory, hội thoại dài để đo trí nhớ của agent), LongMemEval (đo trí nhớ dài hạn của chatbot qua nhiều phiên hội thoại) và DMR (Deep Memory Retrieval, bộ câu hỏi hội thoại để đo trí nhớ của agent). Cả ba đều là hội thoại cá nhân, khác bộ dữ liệu của đồ án; số của vendor (nhà cung cấp sản phẩm) tự báo cáo và mâu thuẫn nhau (xem `08` §4.4). Bài học thiết kế rút ra từ Zep/Mem0 nằm ở `11` §3–§5.

## Tài liệu tham khảo (docs, git)

- **Zep / Graphiti:** [Zep paper, arXiv 2501.13956](https://arxiv.org/abs/2501.13956); mã nguồn [getzep/graphiti](https://github.com/getzep/graphiti); [docs Zep — facts](https://help.getzep.com/v4/facts.md)
- **Mem0:** [Mem0 paper, arXiv 2504.19413](https://arxiv.org/abs/2504.19413); mã nguồn [mem0ai/mem0](https://github.com/mem0ai/mem0) (tên repo theo kết quả tìm kiếm, chưa mở); [Membox, arXiv 2601.03785](https://arxiv.org/abs/2601.03785) (chạy lại các hệ thống để so sánh)
- **Letta (MemGPT):** [letta-ai/letta](https://github.com/letta-ai/letta) (agent runtime, tiền thân MemGPT; chưa mở repo)
- **A-Mem:** chưa tìm được link gốc trong phiên này.
- So sánh của vendor (thứ cấp, số liệu mâu thuẫn): [Mem0 vs Letta](https://mem0.ai/compare/mem0-vs-letta), [vectorize.io](https://vectorize.io/articles/mem0-vs-letta).
