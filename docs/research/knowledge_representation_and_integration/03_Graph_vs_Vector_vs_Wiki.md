# Graph có còn cần cho Temporal Retrieval không? So sánh Vector / Graph / Wiki / Bảng quan hệ

> Câu hỏi gốc: *RAG (Retrieval-Augmented Generation, tìm đoạn tài liệu liên quan rồi đưa cho LLM đọc để trả lời) có thêm khả năng tìm theo thời gian (time retrieval) thì có cần graph (đồ thị: nút là thực thể, cạnh là quan hệ giữa chúng) nữa không, hay làm cách khác?* LLM (Large Language Model) là mô hình ngôn ngữ lớn như Claude, GPT, Gemini. Kết luận ngắn (**[suy luận]** dựa trên bằng chứng bên dưới + thiết kế sẵn có): **Cơ chế 1 (Temporal Retrieval, tìm thông tin đúng tại một mốc thời gian) không cần graph; Cơ chế 2 (Timeline Summarization, tóm tắt diễn biến của một đối tượng theo thời gian) cần "cấu trúc theo thực thể và thời gian" nhưng không nhất thiết là graph database (cơ sở dữ liệu đồ thị); Cơ chế 3 (Conflict Resolution, xử lý thông tin mâu thuẫn; nếu làm) hưởng lợi nhiều nhất từ quan hệ có kiểu (mỗi cạnh có nhãn như "thay thế", "đính chính").**
>
> *Thực thể (entity) là một đối tượng cụ thể được nhắc đến, như một người, một tổ chức, một điều luật. Multi-hop là câu hỏi phải đi qua nhiều bước nối mới trả lời được, ví dụ "vợ của giám đốc công ty X sinh ở đâu".*

## 1. Bằng chứng về chi phí và lợi ích của graph

Các số liệu dưới đây từ preprint/blog, **mỗi nguồn dùng cấu hình khác nhau**, chỉ lấy hướng chung:

- **Truy vấn đơn giản gần như hòa:** GraphRAG-Bench (bộ đo so sánh các phương pháp RAG dùng đồ thị) cho thấy, theo một bản tổng hợp, cách dùng text chunk (một đoạn văn bản được cắt ra để lưu và tìm kiếm) đạt 60.9 so với graph 60.1 ở fact retrieval đơn (tìm một sự kiện đơn lẻ); graph hơn ~10 điểm ở suy luận phức tạp/multi-hop ([GraphRAG-Bench](https://arxiv.org/pdf/2506.02404), qua blog tổng hợp). Một blog khác báo vector RAG thắng ở tìm đúng tài liệu/điều khoản cụ thể (54% vs 35%) **[blog, chưa kiểm]**.
- **Chi phí index** (index là bước dựng chỉ mục, tức xử lý trước toàn bộ tài liệu để sau này tìm nhanh): trích xuất entity bằng LLM chiếm phần lớn token index (token là đơn vị văn bản LLM xử lý, khoảng một âm tiết hoặc một phần từ, và là đơn vị tính tiền); ước tính blog cho corpus (kho tài liệu) 500 trang: vector < $5, Microsoft GraphRAG $50–200 (các con số rất lệch nhau giữa nguồn) **[blog]**. Microsoft GraphRAG là cách làm RAG dùng đồ thị tri thức thay vì chỉ các đoạn văn rời rạc. LazyGraphRAG hoãn việc trích xuất đến lúc truy vấn để giảm chi phí index.
- **Chi phí lúc hỏi** (số token của prompt, tức đoạn văn bản gửi cho LLM, cho mỗi câu hỏi): vector ~879; HippoRAG2 ~1.008; GraphRAG local ~38.7K; LightRAG ~100.8K; GraphRAG global ~331K **[blog trích benchmark]** (HippoRAG2, LightRAG, GraphRAG local/global là tên các biến thể RAG dùng đồ thị). Điều này ngược chiều với mục tiêu "<1K token" của đồ án: **chỉ graph dạng triplet nhẹ mới giữ được token thấp**, GraphRAG kiểu community report (báo cáo tóm tắt cho từng cụm nút trong đồ thị) thì không. Triplet là bộ ba (chủ thể, quan hệ, đối tượng), ví dụ (Ông A, bị bắt, 2024). "Boomerang" là mẫu thiết kế của đồ án: đồ thị chỉ giữ triplet và một con trỏ, khi cần chi tiết thì quay về VectorDB (cơ sở dữ liệu vector, xem §2) lấy chunk gốc.
- Một preprint (bản thảo bài báo chưa qua phản biện) ([UnWeaving the knots of GraphRAG](https://arxiv.org/pdf/2603.29875)) cho rằng "VectorRAG (RAG chỉ dùng tìm kiếm vector) gần như đủ" ở nhiều tác vụ; ta chưa đọc kỹ.

## 2. Phân tích theo từng cơ chế của đồ án

| Cơ chế | Cần gì | Graph có cần? | Lựa chọn thay thế |
|---|---|---|---|
| **1. Temporal Retrieval** (tại mốc T) | Lọc cứng `start_time ≤ T`, điểm thời gian, cross-encoder | **Không.** Tuần 5 cho thấy VectorDB + lọc cứng + rerank đã đạt `leakage_rate = 0%`, `mrr` 0.62 vs 0.336 của Plain RAG | Giữ nguyên VectorDB |
| **2. Timeline Summarization** | Gom mọi sự kiện của **một thực thể** theo thứ tự thời gian, nén gọn | **Cần cấu trúc "thực thể → chuỗi sự kiện có thứ tự"**, không cần suy luận multi-hop | (a) Graph DB (Neo4j) như thiết kế; (b) **bảng quan hệ**: `events(entity_id, start, end, chunk_id, summary)` có chỉ mục theo `(entity_id, start)`; (c) **trang wiki theo thực thể** (một file `entity.md` có các mục theo thời gian), cập nhật khi có chunk mới |
| **3. Conflict Resolution** | Quan hệ có kiểu `SUPERSEDES`/`CORRECTS`/`SUSPECTS`, độ tin cậy nguồn | **Có lợi**, nhưng đồ thị nhỏ | Bảng cạnh `(from_chunk, to_chunk, rel_type)` đủ dùng; graph DB là tiện chứ không bắt buộc. Scope doc đã cho phép bỏ phần đa nguồn |

Giải thích nhanh các thuật ngữ trong bảng:
- `start_time` là thời điểm một thông tin bắt đầu đúng; T là mốc thời gian người dùng hỏi (trong tài liệu thiết kế gọi là `T_req`). "Lọc cứng `start_time ≤ T`" nghĩa là loại hẳn mọi tài liệu bắt đầu sau mốc T, để không "rò rỉ tương lai" (không dùng thông tin chưa xảy ra tại thời điểm hỏi). `leakage_rate` là tỷ lệ kết quả bị rò rỉ như vậy; 0% là không có kết quả nào vi phạm.
- VectorDB là cơ sở dữ liệu vector: lưu embedding (dãy số biểu diễn ý nghĩa văn bản) và tìm theo độ giống nghĩa. Rerank là chấm lại thứ hạng các kết quả đã tìm được. Cross-encoder là mô hình đọc cùng lúc câu hỏi và đoạn văn để chấm độ liên quan, chính xác hơn nhưng chậm hơn.
- `mrr` (Mean Reciprocal Rank, trung bình nghịch đảo thứ hạng) đo đáp án đúng nằm ở vị trí thứ mấy trong kết quả; càng gần 1 càng tốt. Plain RAG là RAG thuần, chỉ tìm theo độ giống nghĩa và không kiểm soát thời gian.
- Neo4j là một graph database phổ biến. `SUSPECTS` là cạnh "bị nghi ngờ" (cáo buộc chưa được xác nhận, được lưu như một lời nghi ngờ chứ không phải sự thật). Scope doc là tài liệu phạm vi đồ án (`docs/scope/01_PROJECT_SCOPE.md`).
- `chunk_id` là mã định danh của một chunk; `rel_type` là loại quan hệ; `(from_chunk, to_chunk, rel_type)` là một dòng của bảng cạnh: "chunk này liên hệ với chunk kia theo kiểu gì". Chỉ mục (index) theo `(entity_id, start)` giúp truy vấn "mọi sự kiện của thực thể này theo thứ tự thời gian" chạy nhanh.

Nhận xét **[suy luận]**: lợi ích thật của GraphDB (cơ sở dữ liệu đồ thị, ví dụ Neo4j) trong thiết kế hiện tại là **đi theo cạnh thời gian (next-event, cạnh nối sự kiện này tới sự kiện kế tiếp)** và **gom theo thực thể**, đều là truy vấn một bước hoặc theo chuỗi, không phải multi-hop khó. Hai việc này làm được bằng chỉ mục quan hệ hoặc payload của VectorDB (payload là dữ liệu kèm theo mỗi vector, ví dụ ngày và nguồn; ở đây dùng `entity_id` + sắp xếp theo `start_time`). Nếu ép thêm chỉ mục `entity_id` vào Qdrant (cơ sở dữ liệu vector mã nguồn mở) thì phá nguyên tắc "chỉ 4 trường payload được index" của thiết kế; cần cân nhắc (xem `06`).

## 3. Bốn phương án kiến trúc

| Phương án | Mô tả | Ưu | Nhược | Hợp với |
|---|---|---|---|---|
| **A. Vector-only + metadata** | Chunk + `start/end/invalidated_at`, lọc cứng + rerank | Đơn giản, đã có kết quả; rẻ | Timeline dài tràn context; không có quan hệ | Cơ chế 1 |
| **B. Vector + Graph DB (Boomerang)** (thiết kế hiện tại) | Graph chứa triplet + `Chunk_ID` | Nén timeline <1K token; quan hệ có kiểu; hai hướng truy vấn | Hai hệ thống phải đồng bộ; Neo4j nặng; trích triplet bằng LLM tốn kém và có thể sai | Cơ chế 2 + 3 |
| **C. Vector + bảng quan hệ** | Postgres (`pgvector`, kiểu `tstzrange`) hoặc SQLite lưu `events` và `relations` | Một DB, truy vấn theo khoảng thời gian rất tự nhiên, có ACID; rẻ | Không có ngôn ngữ truy vấn đồ thị; multi-hop phải viết CTE đệ quy | Cơ chế 2 (+3 nhỏ) |
| **D. Wiki markdown (OKF profile) + index** | File per concept/thực thể; vector index trên file/section; agent đọc file | Dễ kiểm tra, dễ đưa cho agent (xem `05`); LLM tự bảo trì | Không đảm bảo ràng buộc thời gian; lọc cứng phải làm ở lớp index | Lớp **trình bày/trao đổi**, kết hợp với A/B/C |

Giải thích nhanh các thuật ngữ trong bảng:
- **Metadata** (siêu dữ liệu) là thông tin mô tả đi kèm mỗi chunk, ở đây là `start`, `end` (thời điểm bắt đầu và hết hiệu lực) và `invalidated_at` (thời điểm thông tin bị coi là sai ngay từ đầu). **Triplet** và **`Chunk_ID`**: triplet là bộ ba (chủ thể, quan hệ, đối tượng), `Chunk_ID` là con trỏ về chunk gốc trong VectorDB (mẫu Boomerang). **Context** là lượng văn bản LLM đọc được trong một lần, nên "tràn context" nghĩa là timeline quá dài, không nhét vừa.
- **Postgres** và **SQLite** là hai hệ quản trị cơ sở dữ liệu quan hệ (lưu dữ liệu theo bảng, truy vấn bằng SQL); `pgvector` là phần mở rộng cho Postgres để lưu và tìm vector; `tstzrange` là kiểu dữ liệu của Postgres lưu một khoảng thời gian (có múi giờ) trong một ô.
- **ACID** (Atomicity, Consistency, Isolation, Durability) là bốn đảm bảo giao dịch của cơ sở dữ liệu, tóm lại là ghi dữ liệu đáng tin cậy, không bị dở dang. **CTE** (Common Table Expression) là truy vấn SQL con có đặt tên, dùng được đệ quy (tự gọi lại chính nó) để đi theo chuỗi quan hệ nhiều bước.
- **OKF profile** là bộ trường bổ sung của đồ án đặt lên định dạng OKF (xem `02`, `09`). **Agent** là chương trình dùng LLM để tự lập kế hoạch và gọi công cụ. "Đồng bộ" nghĩa là hai hệ thống phải luôn chứa dữ liệu khớp nhau.

Điểm quan trọng **[suy luận]**: **D không thay thế A–C mà nằm ở lớp khác**. D là *định dạng nguồn và định dạng trả về cho agent*; A–C là *bộ máy truy xuất*. Có thể sinh ra bundle OKF từ dữ liệu trong VectorDB/Graph để cho con người và agent khác đọc.

## 4. Khi nào nên chọn gì

- Corpus nhỏ, ổn định, ít hơn vài trăm nghìn token → wiki (bộ trang markdown liên kết nhau) + đọc thẳng vào context có thể đủ (nhưng đồ án có luồng cập nhật liên tục, và cần **lọc cứng chống rò rỉ tương lai** — thứ mà "đọc cả wiki" không đảm bảo).
- Câu hỏi đa số là "tại mốc T, X là gì" → A.
- Cần timeline nhiều thực thể, nhiều nguồn → B hoặc C. C rẻ hơn nhiều; B mạnh hơn khi cần quan hệ có kiểu và mở rộng.
- Cần chia sẻ tri thức cho nhiều agent/công cụ → bọc thêm D hoặc MCP, tức Model Context Protocol, giao thức chuẩn để ứng dụng AI gọi công cụ và dữ liệu của một server bên ngoài (xem `05`).

## 5. Nguồn

- [GraphRAG-Bench](https://arxiv.org/pdf/2506.02404); [LinearRAG](https://arxiv.org/pdf/2510.10114); [UnWeaving the knots of GraphRAG](https://arxiv.org/pdf/2603.29875)
- Blog: [tianpan.co — GraphRAG in production](https://tianpan.co/blog/2026-04-09-graphrag-production-when-vector-search-hits-ceiling), [beri.net — chi phí index](https://www.beri.net/article/graphrag-vs-vector-rag-indexing-query-cost-lightrag-lazygraphrag-2026), [st-hakky](https://book.st-hakky.com/en/news/graphrag-vs-vector-rag-when-it-wins)
- Kết quả tuần 5: `docs/weekly_reports/week_5/WEEK_5.md`
