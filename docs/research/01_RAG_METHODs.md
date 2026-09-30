# Các phương pháp RAG (Retrieval-Augmented Generation) — Chi tiết từ cơ bản đến nâng cao

> RAG năm 2025–2026 không còn là một kỹ thuật duy nhất mà là một **phổ (spectrum)** các phương pháp — chọn phương pháp nào phụ thuộc vào loại câu hỏi, kích thước/cấu trúc dữ liệu, và ngân sách chi phí/độ trễ chấp nhận được.

---

## 1. Naive RAG (RAG cơ bản)

**Khi nào dùng:** Điểm khởi đầu mặc định cho hầu hết ứng dụng (được khuyến nghị cho ~80% use case). Phù hợp khi câu hỏi là tra cứu sự kiện đơn giản, corpus không quá lớn/phức tạp, và bạn chưa chứng minh được rằng cách này không đủ.

**Các bước:**
1. Thu thập tài liệu → làm sạch văn bản.
2. Chia nhỏ (chunk) văn bản thành các đoạn cố định (thường 200–500 token, có overlap).
3. Dùng mô hình embedding chuyển mỗi chunk thành vector, lưu vào vector database (FAISS, Pinecone, Qdrant, pgvector...).
4. Khi có câu hỏi: embed câu hỏi → tìm top-k chunk gần nhất bằng cosine similarity.
5. Ghép các chunk tìm được vào prompt → gửi cho LLM sinh câu trả lời.

**Ví dụ thực tế:** Một startup nhỏ (5 người) làm chatbot hỗ trợ khách hàng cho cửa hàng bán đồ gia dụng online. Họ có ~50 trang FAQ + chính sách đổi trả. Chỉ cần nhét toàn bộ vào một vector DB (ví dụ Chroma chạy local), khách hỏi "chính sách đổi trả trong bao lâu?" → tìm đúng đoạn FAQ nói về đổi trả → LLM trả lời. Không cần gì phức tạp hơn.

- **Ưu điểm:** Dễ triển khai, chi phí thấp, độ trễ thấp.
- **Nhược điểm:** Retrieval "một lần" — nếu sai/thiếu thì không có cơ chế sửa; chunk cố định dễ cắt đứt ngữ cảnh; kém với câu hỏi đa bước, đa tài liệu.

**Tham khảo:**
- [The 2026 Guide to Retrieval-Augmented Generation (RAG) — EdenAI](https://www.edenai.co/post/the-2026-guide-to-retrieval-augmented-generation-rag)
- [12 Advanced RAG Techniques: Beyond Naive Retrieval — Atlan](https://atlan.com/know/advanced-rag-techniques/)
- [How to Improve RAG Performance: 5 Key Techniques — DataCamp](https://www.datacamp.com/tutorial/how-to-improve-rag-performance)

---

## 2. Chunking & Indexing nâng cao

### 2.1 Sentence-Window / Parent-Child Retrieval

**Khi nào dùng:** Tài liệu dài, câu trả lời cần ngữ cảnh xung quanh nhiều hơn đoạn văn tìm thấy (ví dụ: tài liệu pháp lý, hợp đồng, sách kỹ thuật).

**Các bước:**
1. Chia tài liệu thành chunk nhỏ (câu hoặc vài câu) — dùng để **embedding và truy xuất** (match chính xác).
2. Đồng thời lưu chunk "cha" lớn hơn (đoạn/section) bao quanh mỗi chunk nhỏ, kèm liên kết metadata (parent_id).
3. Khi truy vấn: tìm chunk nhỏ khớp nhất, nhưng khi đưa vào LLM thì **thay bằng chunk cha** để có đủ ngữ cảnh.

**Ví dụ thực tế:** Một công ty luật số hóa hợp đồng dài 80 trang. Khách hỏi "điều khoản phạt vi phạm hợp đồng là gì?". Câu "Bên B phải chịu phạt 10% giá trị hợp đồng" nếu đứng một mình (chunk nhỏ) thì không rõ "Bên B" là ai, phạt trong trường hợp nào. Hệ thống tìm đúng câu đó (chunk nhỏ) nhưng trả về cả đoạn/điều khoản (chunk cha) chứa đầy đủ ngữ cảnh về Bên A, Bên B, điều kiện áp dụng.

- **Ưu điểm:** Tách biệt độ chính xác truy xuất và độ đầy đủ ngữ cảnh sinh câu trả lời.
- **Nhược điểm:** Cần quản lý index phức tạp hơn (metadata liên kết cha-con), tăng dung lượng lưu trữ.

**Tham khảo:**
- [ARAGOG: Advanced RAG Output Grading (arXiv:2404.01037)](https://arxiv.org/pdf/2404.01037)
- [Recursive Retrieval for RAG — DataCamp](https://www.datacamp.com/tutorial/contextual-retrieval-anthropic)

### 2.2 Document Summary Index / Recursive Retrieval (Phân cấp / Đệ quy)

**Khi nào dùng:** Corpus rất lớn, nhiều tài liệu (hàng nghìn+), cần định tuyến nhanh trước khi vào chi tiết để ngăn chặn nhiễu chéo (cross-document noise).

**Các bước (ví dụ bằng LlamaIndex):**
1. Với mỗi tài liệu, tạo một Vector Index riêng chứa các chunk chi tiết của tài liệu đó.
2. Dùng LLM tạo một tóm tắt ngắn cho từng tài liệu và gói vào đối tượng `IndexNode` (liên kết với index chi tiết tương ứng).
3. Tạo một Vector Index cấp cao (Top-Level) chứa các bản tóm tắt này.
4. Khi truy vấn: Hệ thống đối chiếu bản tóm tắt trước (tầng trên) → nhận diện tài liệu phù hợp nhất → "đào sâu" (drill down) xuống chính các chunk con chi tiết của tài liệu đó (tầng dưới).

**Ví dụ thực tế:** Một tập đoàn có 10.000 báo cáo dự án nội bộ. Khách hỏi "dự án nào từng làm về tối ưu chuỗi cung ứng ở khu vực miền Trung?". Hệ thống trước tiên lọc qua 10.000 bản tóm tắt ở tầng 1 để tìm ra báo cáo phù hợp nhất, sau đó mới nhảy thẳng vào vector store của báo cáo đó để lấy các chunk chi tiết. Tránh việc quét toàn bộ hàng triệu chunk cùng lúc.

- **Ưu điểm:** Giảm thiểu tối đa việc "nhiễu chéo" — tránh trường hợp câu trả lời gom nhầm 2 đoạn văn ở 2 tài liệu hoàn toàn khác nhau vào cùng một prompt. Độ chính xác rất cao cho câu hỏi liên quan đến tài liệu cụ thể.
- **Nhược điểm:** Tốn chi phí tạo tóm tắt bằng LLM. Nếu câu hỏi mang tính chất so sánh bao quát (global cross-document queries), việc định tuyến tầng 1 có thể vô tình bỏ sót tài liệu nếu cấu hình `top_k` quá nhỏ.

**Tham khảo:**
- [LlamaIndex - Recursive Retriever Documentation](https://docs.llamaindex.ai/en/stable/examples/query_engine/recursive_retriever_nodes/)

### 2.3 Long RAG

**Khi nào dùng:** Khi có LLM hỗ trợ context window dài (128K–1M+ token) và tài liệu có tính liền mạch cao, việc chia nhỏ làm mất ý nghĩa (ví dụ: hợp đồng dài, báo cáo tài chính, code).

**Các bước:**
1. Thay vì chunk nhỏ, dùng đơn vị truy xuất lớn (toàn bộ section hoặc tài liệu).
2. Embedding các đơn vị lớn này để retrieval.
3. Truy xuất top-k tài liệu/section lớn, đưa nguyên vào context của LLM.

**Ví dụ thực tế:** Một quỹ đầu tư cần phân tích báo cáo tài chính (10-K) dài 200 trang của một công ty niêm yết. Câu hỏi "rủi ro pháp lý được nêu trong phần Risk Factors liên quan gì đến phần MD&A không?" cần đọc xuyên suốt nhiều phần liên kết nhau — thay vì chia nhỏ thành 500 chunk rời rạc, hệ thống truy xuất nguyên chương "Risk Factors" và "MD&A" (mỗi phần vài chục trang) rồi đưa thẳng vào LLM có context 200K token.

- **Ưu điểm:** Giữ nguyên ngữ cảnh, giảm mất mát thông tin do chia nhỏ, giảm số lần retrieval.
- **Nhược điểm:** Tốn token/chi phí inference hơn nhiều; cần LLM hỗ trợ context dài.

**Tham khảo:**
- [The 2026 Guide to RAG — EdenAI](https://www.edenai.co/post/the-2026-guide-to-retrieval-augmented-generation-rag)

### 2.4 Contextual Retrieval (Anthropic)

**Khi nào dùng:** Corpus có nhiều chunk "mơ hồ khi đứng riêng lẻ" — codebase, tài liệu chính sách nội bộ, báo cáo tài chính, bài nghiên cứu — nơi một đoạn văn tách rời sẽ mất đi ai/cái gì/thời điểm nào đang được nhắc đến.

**Các bước:**
1. Với mỗi chunk, dùng LLM (Claude) sinh một đoạn ngữ cảnh ngắn (~50–100 token) mô tả chunk đó nằm ở đâu, nói về ai/cái gì trong toàn tài liệu.
2. Gắn đoạn ngữ cảnh này vào **trước** chunk gốc.
3. Embedding chunk đã gắn ngữ cảnh (Contextual Embeddings) + đồng thời đưa vào index BM25 (Contextual BM25).
4. Kết hợp kết quả dense + BM25 (xem Hybrid Search bên dưới), tùy chọn thêm bước rerank.
5. Dùng prompt caching (nếu dùng Claude) để giảm chi phí sinh ngữ cảnh lặp lại.

**Ví dụ thực tế:** Một chunk trong báo cáo quý của công ty ACME chỉ ghi "Doanh thu tăng 3% so với quý trước." — đứng một mình, không rõ công ty nào, quý nào. Contextual Retrieval sẽ tự động thêm câu ngữ cảnh phía trước: "Đoạn này trích từ báo cáo tài chính quý 2/2025 của công ty ACME Corp, phần kết quả kinh doanh." → giờ chunk đủ ngữ cảnh để retrieval chính xác khi có ai hỏi "doanh thu ACME quý 2/2025 tăng bao nhiêu?".

- **Ưu điểm:** Giảm tỷ lệ truy xuất sai rõ rệt — theo công bố của Anthropic: embedding ngữ cảnh giảm ~35% lỗi truy xuất, kết hợp thêm BM25 ngữ cảnh giảm ~49%, thêm rerank giảm tới ~67%.
- **Nhược điểm:** Tăng chi phí và thời gian index hóa vì phải gọi LLM cho mỗi chunk (dù có thể giảm nhờ prompt caching).

**Tham khảo:**
- [Introducing Contextual Retrieval — Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- [Anthropic's Contextual Retrieval: A Guide With Implementation — DataCamp](https://www.datacamp.com/tutorial/contextual-retrieval-anthropic)
- [Anthropic Contextual Retrieval cookbook — LlamaIndex](https://developers.llamaindex.ai/python/examples/cookbooks/contextual_retrieval/)

---

## 3. Hybrid Retrieval + Re-ranking (chuẩn production 2025–2026)

### 3.1 Hybrid Search (Dense + Sparse)

**Khi nào dùng:** Gần như mọi hệ thống production nghiêm túc — đặc biệt khi truy vấn có thể chứa từ khóa chính xác (mã sản phẩm, tên riêng, số liệu) mà dense embedding dễ bỏ lỡ.

**Các bước:**
1. Xây dựng song song hai index: (a) vector index (dense embedding) và (b) index từ khóa BM25/SPLADE (sparse).
2. Khi truy vấn: chạy đồng thời cả hai kiểu tìm kiếm, mỗi loại trả về danh sách xếp hạng riêng.
3. Hợp nhất hai danh sách bằng **Reciprocal Rank Fusion (RRF)**: điểm hợp nhất = tổng 1/(k + rank) của mỗi danh sách.
4. Lấy top-k sau khi hợp nhất để đưa vào bước tiếp theo (rerank hoặc trực tiếp vào LLM).

**Ví dụ thực tế:** Một trang thương mại điện tử có trợ lý tra cứu thông số kỹ thuật sản phẩm. Khách hỏi "laptop nào có mã SKU LT-4471X còn hàng không?" — dense embedding có thể không "hiểu" mã sản phẩm là gì và tìm sai, nhưng BM25 (tìm từ khóa chính xác) sẽ khớp thẳng "LT-4471X". Hybrid search đảm bảo tìm đúng dù câu hỏi có mã kỹ thuật lẫn ngôn ngữ tự nhiên.

- **Ưu điểm:** Bù trừ điểm yếu của nhau — dense tốt về ngữ nghĩa, sparse tốt về khớp từ khóa/số liệu/tên riêng chính xác. Được xem là "chuẩn mực thực tế" (de facto standard) năm 2025–2026.
- **Nhược điểm:** Cần duy trì 2 hệ thống index song song, tăng độ phức tạp hạ tầng.

**Tham khảo:**
- [12 Advanced RAG Techniques — Atlan](https://atlan.com/know/advanced-rag-techniques/)
- [RAG Techniques Compared 2026 — StarMorph](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide)

### 3.2 Two-Stage RAG + Cross-Encoder Reranking (Cohere, BGE)

**Khi nào dùng:** Mọi hệ thống RAG môi trường production cần cân bằng giữa độ chính xác và độ trễ (<200ms). Khắc phục điểm yếu của Bi-Encoder: bắt rộng nhưng thứ tự ưu tiên lộn xộn, nhiều chunk rác.

**Các bước:**
1. Giai đoạn 1: Lấy ứng viên rộng (Top 100–150) qua Hybrid Retrieval (Vector + BM25).
2. Giai đoạn 2: Với mỗi cặp (câu hỏi, ứng viên), đưa vào một **cross-encoder** (như Cohere Rerank, BGE-Reranker) để chấm điểm chi tiết.
3. Xếp hạng lại toàn bộ, lọc xuống Top 10–20 để đưa vào LLM.

**Ví dụ thực tế:** Ứng dụng tra cứu y khoa cho bác sĩ. Câu hỏi "thuốc X có chống chỉ định với bệnh nhân suy thận không?" trả về 100 đoạn văn có chứa từ "thuốc X" và "thận" (dense/BM25 thô). Cross-encoder đọc kỹ từng cặp (câu hỏi + đoạn) để xếp đúng 3–4 đoạn nói về chống chỉ định suy thận lên đầu, lọc bỏ các chunk rác.

- **Ưu điểm:** Cải thiện độ chính xác đáng kể so với chỉ dùng similarity score ban đầu.
- **Nhược điểm:** Tăng độ trễ, chi phí tính toán cao hơn nhiều so với cosine similarity thuần.

**Tham khảo:**
- [12 Advanced RAG Techniques — Atlan](https://atlan.com/know/advanced-rag-techniques/)
- [Boost LLM Accuracy with RAG and Reranking — DataCamp](https://www.datacamp.com/tutorial/boost-llm-accuracy-with-retrieval-augmented-generation-and-reranking)

### 3.3 RankGPT (Reranking bằng LLM)

**Khi nào dùng:** Khắc phục giới hạn của mô hình rerank truyền thống nhờ khả năng lập luận sâu của LLM lớn. Thường dùng trong nghiên cứu học thuật hoặc dùng offline để sinh nhãn dữ liệu phục vụ chưng cất (distillation).

**Các bước:**
1. Đưa toàn bộ danh sách các chunks ứng viên vào LLM (như GPT-4, Claude 3.5) qua prompt.
2. Yêu cầu mô hình tự suy luận và hoán vị thứ tự các chunk (ví dụ: `[1] > [3] > [2]`).
3. Lấy kết quả xếp hạng từ LLM để dùng làm ngữ cảnh cuối cùng.

- **Ưu điểm:** Khả năng lập luận sâu, xử lý ngữ cảnh dài cực tốt so với cross-encoder thông thường.
- **Nhược điểm:** Rất tốn kém (về token) và độ trễ cao, khó áp dụng trực tiếp cho hệ thống real-time.

### 3.4 Query Transformation: HyDE, RAG-Fusion, Multi-query

**HyDE (Hypothetical Document Embeddings)**

**Khi nào dùng:** Câu hỏi ngắn, viết kém, hoặc dùng từ ngữ khác với tài liệu gốc (khoảng cách ngữ nghĩa giữa câu hỏi và tài liệu lớn).

**Các bước:**
1. Dùng LLM sinh một "tài liệu giả định" trả lời câu hỏi (có thể sai sự thật, nhưng đúng về *dạng/pattern* liên quan).
2. Embedding tài liệu giả định này (thay vì embedding câu hỏi gốc).
3. Dùng vector đó để tìm tài liệu thật gần nhất trong corpus (so khớp answer-to-answer thay vì question-to-answer).

**Ví dụ thực tế:** Người dùng gõ câu hỏi cụt lủn "sao máy lạnh kêu tạch tạch". Câu này không khớp trực tiếp với tài liệu kỹ thuật viết "Tiếng gõ bất thường từ dàn nóng có thể do giãn nở nhiệt của vỏ máy hoặc lỏng ốc quạt." HyDE cho LLM tự "tưởng tượng" một câu trả lời giả định trước (dù có thể chưa chính xác), rồi dùng chính câu trả lời giả định đó để tìm tài liệu thật — vì câu trả lời giả định dùng từ ngữ kỹ thuật gần với tài liệu gốc hơn là câu hỏi thô của người dùng.

- **Ưu điểm:** Cải thiện recall cho câu hỏi mơ hồ; hiệu quả tương đương retriever đã fine-tune mà không cần dữ liệu huấn luyện.
- **Nhược điểm:** Thêm một lượt gọi LLM trước khi retrieval → tăng độ trễ/chi phí; chất lượng phụ thuộc vào "tài liệu giả định" có đúng hướng không.

**Tham khảo:**
- [Precise Zero-Shot Dense Retrieval without Relevance Labels (arXiv:2212.10496)](https://arxiv.org/abs/2212.10496)

**RAG-Fusion / Multi-query retrieval**

**Khi nào dùng:** Câu hỏi phức tạp, có thể diễn đạt theo nhiều cách, hoặc câu hỏi mà một truy vấn đơn không bao phủ hết các khía cạnh.

**Các bước:**
1. Dùng LLM sinh ra nhiều biến thể của câu hỏi gốc (ví dụ 3–5 câu hỏi con/diễn đạt khác nhau).
2. Truy xuất song song cho từng biến thể.
3. Hợp nhất tất cả kết quả bằng Reciprocal Rank Fusion (RRF), loại trùng lặp.
4. Đưa top-k sau hợp nhất vào LLM sinh câu trả lời cuối.

**Ví dụ thực tế:** Trợ lý HR nội bộ nhận câu hỏi "công ty có hỗ trợ gì khi nhân viên nghỉ sinh không?". Hệ thống tự sinh thêm các biến thể: "chính sách thai sản của công ty", "quyền lợi nghỉ sinh cho nhân viên nữ", "hỗ trợ tài chính khi sinh con". Mỗi biến thể truy xuất ra một vài tài liệu khác nhau (một cái ra chính sách thai sản, một cái ra chính sách bảo hiểm, một cái ra quy định nghỉ phép) — gộp lại cho câu trả lời đầy đủ hơn là chỉ dùng câu hỏi gốc.

- **Ưu điểm:** Tăng recall, giảm rủi ro bỏ sót tài liệu do cách diễn đạt câu hỏi không khớp corpus.
- **Nhược điểm:** Tăng số lần gọi LLM/embedding (chi phí × số biến thể), có thể đưa vào nhiễu nếu biến thể câu hỏi lệch hướng.

**Tham khảo:**
- [RAG-Fusion: a New Take on Retrieval-Augmented Generation — Rackauckas (dẫn trong Atlan)](https://atlan.com/know/advanced-rag-techniques/)

---

## 4. Self-correcting / Adaptive RAG (RAG có phản hồi và tự sửa)

### 4.1 Self-RAG

**Khi nào dùng:** Cần giảm hallucination và tránh retrieval thừa (câu hỏi không cần tra cứu ngoài vẫn bị ép retrieval trong Naive RAG).

**Các bước (mô hình được huấn luyện đặc biệt với "reflection tokens"):**
1. Mô hình bắt đầu sinh câu trả lời theo kiểu tự hồi quy (autoregressive).
2. Khi cần thêm thông tin, mô hình tự phát ra token đặc biệt `[Retrieve]` → dừng sinh, gọi retriever lấy tài liệu.
3. Mô hình đánh giá tài liệu vừa lấy: phát token `[Relevant]` hoặc `[Irrelevant]`.
4. Nếu liên quan, mô hình tiếp tục sinh câu trả lời dựa trên tài liệu đó và tự đánh giá tính hỗ trợ/hữu ích của câu trả lời (critique).
5. Nếu không liên quan hoặc câu trả lời chưa tốt, có thể retrieval lại hoặc bỏ qua retrieval.

**Ví dụ thực tế:** Chatbot nội bộ được hỏi hai câu liên tiếp: (1) "1 + 1 bằng mấy?" — mô hình tự biết không cần retrieval, trả lời thẳng "2". (2) "Chính sách nghỉ phép năm 2026 của công ty thay đổi thế nào so với 2025?" — mô hình tự phát token `[Retrieve]`, lấy tài liệu, tự đánh giá tài liệu có liên quan không trước khi trả lời, tránh bịa nếu tài liệu tìm được không thực sự nói về thay đổi chính sách.

- **Ưu điểm:** Giảm retrieval không cần thiết, tăng độ tin cậy nhờ cơ chế tự phê bình (self-reflection).
- **Nhược điểm:** Cần huấn luyện/fine-tune mô hình với reflection tokens (không phải plug-and-play với LLM bất kỳ); nhãn huấn luyện ban đầu phụ thuộc vào một mô hình giám khảo lớn (GPT-4) tốn chi phí.

**Tham khảo:**
- [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection (arXiv:2310.11511)](https://arxiv.org/abs/2310.11511)
- [Self-RAG — Learn Prompting (giải thích trực quan)](https://learnprompting.org/docs/retrieval_augmented_generation/self-rag)
- [Self-Rag: A Guide With LangGraph Implementation — DataCamp](https://www.datacamp.com/tutorial/self-rag)

### 4.2 Corrective RAG (CRAG) (LangGraph)

**Khi nào dùng:** Giải quyết vấn đề cơ sở dữ liệu nội bộ bị thiếu thông tin hoặc tài liệu retrieved bị sai lệch gây ảo giác. Áp dụng cho hệ thống hỏi đáp mở, tri thức biến động liên tục theo thời gian thực (tin tức, thị trường).

**Các bước:**
1. Sau khi retrieval, dùng một **bộ đánh giá (Evaluator)** kiểm tra tài liệu.
2. Nếu tài liệu **Đúng** → Tinh lọc (loại nhiễu, giữ phần liên quan) rồi đưa vào prompt.
3. Nếu tài liệu **Sai** → Bỏ qua, kích hoạt tìm kiếm Web (Web Search).
4. Nếu tài liệu **Mơ hồ** → Kết hợp cả hai (tinh lọc tài liệu + tìm kiếm Web).
5. Sinh câu trả lời từ tập tài liệu đã được lọc/bổ sung.

**Ví dụ thực tế:** Một trợ lý hỏi-đáp về sản phẩm công nghệ chỉ được nạp tài liệu nội bộ đến tháng 12/2025. Khách hỏi "phiên bản phần mềm mới nhất ra tháng nào?" — retrieval nội bộ trả về tài liệu cũ (đánh giá "sai/lỗi thời"), hệ thống tự động kích hoạt tìm kiếm web để lấy thông tin cập nhật thay vì trả lời sai dựa trên tài liệu cũ.

- **Ưu điểm:** Có cơ chế "sửa sai" khi retrieval ban đầu kém chất lượng, giảm hallucination. Dễ dàng triển khai hơn so với Self-RAG.
- **Nhược điểm:** Thêm bước đánh giá và lệnh gọi web search → tăng độ trễ và chi phí. Phụ thuộc lớn vào chất lượng của bộ đánh giá.

**Tham khảo:**
- [Corrective Retrieval Augmented Generation — Yan et al. (arXiv:2401.15884)](https://arxiv.org/abs/2401.15884)
- [Corrective RAG (CRAG) Implementation With LangGraph](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)
- [Corrective RAG (CRAG) Implementation — DataCamp](https://www.datacamp.com/tutorial/corrective-rag-crag)

### 4.3 Adaptive RAG

**Khi nào dùng:** Hệ thống thực tế thường có nhiều dạng câu hỏi (đơn giản lẫn phức tạp) — đây là **best practice phổ biến năm 2026** để cân bằng chi phí/tốc độ và độ chính xác.

**Các bước:**
1. Huấn luyện một bộ phân loại nhỏ (ví dụ T5-large) để dự đoán độ phức tạp của câu hỏi: đơn giản / trung bình / phức tạp.
2. Định tuyến:
   - Câu hỏi đơn giản → trả lời trực tiếp bằng LLM, không cần retrieval.
   - Câu hỏi trung bình → RAG một bước (retrieval một lần rồi sinh câu trả lời).
   - Câu hỏi phức tạp (đa bước) → pipeline lặp (iterative retrieval-augmented generation, có thể nhiều vòng retrieval).
3. Trả kết quả tương ứng với nhánh đã chọn.

**Ví dụ thực tế:** Cổng tra cứu pháp luật công cộng nhận cả câu hỏi "thủ đô Việt Nam là gì?" (không cần retrieval, trả lời thẳng) lẫn câu "so sánh quy định về thuế thu nhập cá nhân giữa Luật thuế 2020 và bản sửa đổi 2024, áp dụng cho trường hợp thu nhập từ nhiều nguồn" (cần retrieval nhiều vòng qua nhiều điều luật, so sánh chéo). Bộ phân loại giúp câu đơn giản được trả lời ngay lập tức (rẻ, nhanh), còn câu phức tạp mới kích hoạt pipeline retrieval nhiều bước tốn kém hơn.

- **Ưu điểm:** Tối ưu chi phí (không tốn retrieval cho câu hỏi đơn giản) trong khi vẫn đủ mạnh cho câu hỏi khó.
- **Nhược điểm:** Cần huấn luyện/thiết kế bộ phân loại tốt; phân loại sai có thể khiến chọn nhầm pipeline (quá đơn giản hoặc quá tốn kém).

**Tham khảo:**
- [Adaptive-RAG: Learning to Adapt Retrieval-Augmented LLMs through Question Complexity — Jeong et al., NAACL 2024](https://aclanthology.org/2024.naacl-long.389/)
- [GitHub — Adaptive-RAG (code chính thức)](https://github.com/starsuzi/Adaptive-RAG)

### 4.4 MemoRAG

**Khi nào dùng:** Ứng dụng hội thoại dài, trợ lý cá nhân hóa, hoặc cần nhớ ngữ cảnh của phiên làm việc/lịch sử truy vấn trước.

**Các bước:**
1. Duy trì một bộ nhớ dài hạn (memory module) lưu tóm tắt các tương tác/truy vấn trước.
2. Khi có câu hỏi mới, kết hợp bộ nhớ này với retrieval từ corpus để định hướng truy vấn tốt hơn (ví dụ gợi ý "manh mối" cần tìm).
3. Retrieval dựa trên cả câu hỏi hiện tại và ngữ cảnh bộ nhớ.
4. Cập nhật lại bộ nhớ sau mỗi lượt hội thoại.

**Ví dụ thực tế:** Trợ lý học tập cá nhân trò chuyện với một học sinh suốt học kỳ. Đầu học kỳ học sinh nói "em đang học yếu phần đạo hàm". Ba tuần sau, học sinh hỏi "giải giúp em bài này" mà không nhắc lại bối cảnh — MemoRAG nhớ lại điểm yếu về đạo hàm để ưu tiên giải thích kỹ hơn ở bước đó, thay vì coi đây là một câu hỏi hoàn toàn mới không có ngữ cảnh.

- **Ưu điểm:** Tốt cho ứng dụng hội thoại dài, cá nhân hóa theo người dùng theo thời gian.
- **Nhược điểm:** Quản lý bộ nhớ phức tạp, rủi ro rò rỉ ngữ cảnh cũ không còn phù hợp (context drift).

**Tham khảo:**
- [Enterprise LLM Evaluation Benchmark (arXiv:2506.20274) — mục 2.2 tổng quan MemoRAG](https://arxiv.org/pdf/2506.20274)

---

## 5. Graph-based RAG (RAG dựa trên đồ thị tri thức)

### 5.1 GraphRAG (Microsoft)

**Khi nào dùng:** Câu hỏi "toàn cảnh" (global sensemaking) như "chủ đề chính của tập dữ liệu này là gì?" — loại câu hỏi mà câu trả lời không nằm gọn trong một đoạn văn mà cần tổng hợp qua toàn bộ corpus. Không phù hợp cho tra cứu sự kiện đơn lẻ (dùng vector RAG sẽ rẻ và nhanh hơn).

**Các bước (2 giai đoạn — index và query):**
1. **Trích xuất:** Dùng LLM đọc từng chunk, trích xuất thực thể (entity), quan hệ (relationship) và các claim.
2. **Xây graph:** Lắp ráp thành một đồ thị tri thức có trọng số (nodes = thực thể, edges = quan hệ).
3. **Phát hiện cộng đồng:** Chạy thuật toán phát hiện cộng đồng (ví dụ Leiden) để phân graph thành các cụm (community) thực thể liên quan chặt chẽ, theo nhiều cấp độ phân cấp.
4. **Tóm tắt cộng đồng:** Dùng LLM sinh tóm tắt cho mỗi cộng đồng ở mỗi cấp, từ dưới lên (cộng đồng cấp cao tổng hợp lại tóm tắt của cấp thấp hơn).
5. **Truy vấn:** Với câu hỏi toàn cảnh, lấy các tóm tắt cộng đồng liên quan, sinh câu trả lời từng phần (map), rồi hợp nhất (reduce) thành câu trả lời cuối.

**Ví dụ thực tế:** Một nhà báo điều tra có 5.000 email nội bộ của một tập đoàn (rò rỉ dữ liệu) và muốn hỏi "những nhóm nhân vật/phòng ban nào có mối liên hệ đáng ngờ với nhau trong toàn bộ kho email này?". Đây không phải câu hỏi tìm 1 email cụ thể mà cần thấy "bức tranh toàn cảnh" các mối quan hệ. GraphRAG xây đồ thị tên người/phòng ban/công ty liên quan xuất hiện trong email, nhóm thành các cụm cộng đồng, rồi tóm tắt "cụm A gồm giám đốc X, Y thường trao đổi về hợp đồng Z với đối tác W" — trả lời được câu hỏi mà vector RAG (chỉ tìm 5 email giống câu hỏi) không thể làm.

- **Ưu điểm:** Rất mạnh cho câu hỏi cần suy luận đa bước, tổng hợp thông tin xuyên nhiều tài liệu; cải thiện đáng kể độ đầy đủ câu trả lời cho câu hỏi toàn cảnh so với vector RAG truyền thống.
- **Nhược điểm:** Chi phí xây dựng và bảo trì graph rất cao (nhiều lượt gọi LLM để trích xuất + tóm tắt), khó cập nhật real-time khi dữ liệu thay đổi liên tục.

**Tham khảo:**
- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization (arXiv:2404.16130) — Microsoft Research](https://arxiv.org/abs/2404.16130)
- [GitHub — microsoft/graphrag](https://github.com/microsoft/graphrag)
- [Tài liệu chính thức GraphRAG](https://microsoft.github.io/graphrag)
- [GraphRAG: Graph-Based Retrieval-Augmented Generation — DataCamp](https://www.datacamp.com/tutorial/graphrag)

### 5.2 RAPTOR

**Khi nào dùng:** Tài liệu dài (sách, báo cáo dài) cần trả lời cả câu hỏi chi tiết lẫn câu hỏi khái quát/tổng hợp toàn văn bản, ví dụ: suy luận đa bước phức tạp qua nhiều phần của một cuốn sách.

**Các bước:**
1. Chia văn bản thành các chunk nhỏ (leaf nodes), embedding bằng SBERT hoặc mô hình tương tự.
2. Gom cụm (clustering) các chunk có liên quan bằng Gaussian Mixture Model kết hợp giảm chiều UMAP.
3. Với mỗi cụm, dùng LLM tóm tắt thành một node cha (tóm tắt trừu tượng của cụm đó).
4. Lặp lại đệ quy: gom cụm các node cha → tóm tắt tiếp → xây dựng cây nhiều tầng từ dưới lên.
5. Khi truy vấn: tìm kiếm trên toàn bộ cây (kỹ thuật "collapsed tree retrieval") — có thể lấy cả node lá chi tiết lẫn node tóm tắt cấp cao tùy loại câu hỏi.

**Ví dụ thực tế:** Một ứng dụng đọc sách hỗ trợ hỏi-đáp về tiểu thuyết trinh thám dài 400 trang. Người đọc hỏi câu chi tiết "tên hung thủ được nhắc lần đầu ở chương nào?" (cần node lá chi tiết), nhưng cũng hỏi câu tổng hợp "động cơ giết người xuyên suốt cả câu chuyện là gì?" (câu trả lời rải rác nhiều chương, cần node tóm tắt cấp cao). RAPTOR trả lời tốt cả hai loại vì cây có cả chi tiết lẫn tóm tắt ở nhiều tầng.

- **Ưu điểm:** Xử lý tốt cả câu hỏi chi tiết lẫn câu hỏi tổng hợp/khái quát trên tài liệu dài; đạt kết quả tốt trên các benchmark suy luận đa bước phức tạp (ví dụ cải thiện 20% độ chính xác tuyệt đối trên QuALITY khi kết hợp với GPT-4).
- **Nhược điểm:** Chi phí xây cây tốn kém (nhiều lượt gọi LLM để tóm tắt đệ quy), độ phức tạp triển khai cao hơn RAG truyền thống.

**Tham khảo:**
- [RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval (arXiv:2401.18059) — ICLR 2024](https://arxiv.org/abs/2401.18059)

---

## 6. Agentic RAG (RAG với tác tử/agent)

**Khi nào dùng:** Truy vấn phức tạp cần suy luận nhiều bước, kết hợp nhiều nguồn dữ liệu/công cụ khác nhau (database, API, web search, nhiều vector store), hoặc khi cần khả năng tự lên kế hoạch và sửa lỗi giữa chừng. Không nên dùng cho câu hỏi đơn giản vì rất tốn chi phí.

**Các bước:**
1. Agent (LLM có khả năng gọi công cụ) nhận câu hỏi, tự lập kế hoạch các bước cần làm.
2. Agent chọn công cụ phù hợp cho từng bước (ví dụ: tìm trong vector DB A, sau đó gọi API B, sau đó web search).
3. Sau mỗi bước, agent đánh giá kết quả: đã đủ thông tin chưa, có cần điều chỉnh kế hoạch không.
4. Lặp lại các bước truy xuất/gọi công cụ cho đến khi agent tự xác định đã đủ dữ liệu.
5. Tổng hợp toàn bộ thông tin thu thập được để sinh câu trả lời cuối cùng.

**Ví dụ thực tế:** Trợ lý phân tích đầu tư nhận câu hỏi "so sánh hiệu suất cổ phiếu FPT quý này với đối thủ cùng ngành, và cho biết tin tức nào ảnh hưởng đến biến động giá tuần qua". Agent tự lên kế hoạch: (1) gọi API dữ liệu giá cổ phiếu lấy số liệu FPT, (2) tra cứu vector DB nội bộ để tìm "đối thủ cùng ngành", (3) gọi lại API giá cho các đối thủ đó, (4) web search tin tức tuần qua liên quan đến FPT, (5) tổng hợp tất cả thành báo cáo so sánh. Đây là chuỗi 4-5 bước không thể làm trong một lần retrieval đơn giản.

- **Ưu điểm:** Xử lý được truy vấn phức tạp, đa nguồn, cần suy luận nhiều bước hoặc kết hợp nhiều công cụ; linh hoạt, có thể tự sửa lỗi giữa chừng.
- **Nhược điểm:** Chậm và tốn chi phí nhất trong các phương pháp (nhiều lượt gọi LLM tuần tự); khó kiểm soát, khó debug; có thể "loop" không hiệu quả nếu thiết kế kém.

### Federated / Decentralized Agentic RAG (A-RAG và các biến thể 2026)

**Khi nào dùng:** Tổ chức có dữ liệu phân tán ở nhiều hệ thống/phòng ban khác nhau, không thể (hoặc không muốn vì lý do bảo mật/compliance) tập trung hóa toàn bộ vào một vector DB duy nhất.

**Các bước:**
1. Agent xác định câu hỏi cần thông tin từ những nguồn/hệ thống nào.
2. Gửi truy vấn con song song đến từng nguồn dữ liệu phân tán (mỗi nguồn có index/quyền truy cập riêng).
3. Thu thập kết quả từ các nguồn, agent điều phối và hợp nhất.
4. Sinh câu trả lời cuối từ dữ liệu tổng hợp đa nguồn.

**Ví dụ thực tế:** Một ngân hàng có dữ liệu khách hàng nằm ở hệ thống CRM (bộ phận bán hàng), dữ liệu giao dịch ở hệ thống core banking (bộ phận vận hành), và hồ sơ tín dụng ở hệ thống rủi ro — mỗi hệ thống có quyền truy cập và quy định bảo mật riêng, không được gộp vào một kho dữ liệu chung. Khi nhân viên hỏi "hồ sơ vay của khách hàng A có rủi ro gì cần lưu ý?", agent gửi truy vấn con song song tới cả 3 hệ thống (trong phạm vi quyền truy cập được cấp), rồi tổng hợp câu trả lời mà không cần di chuyển dữ liệu nhạy cảm ra khỏi hệ thống gốc.

- **Ưu điểm:** Không cần tập trung hóa toàn bộ dữ liệu, phù hợp yêu cầu privacy/compliance.
- **Nhược điểm:** Kiến trúc phức tạp nhất trong tất cả các phương pháp, điều phối nhiều nguồn truy xuất khó tối ưu độ trễ.

**Tham khảo:**
- [20 Advanced RAG Types to Know in 2026 — Turing Post](https://www.turingpost.com/p/ragtypes)
- [RAG Techniques Compared 2026 — StarMorph](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide)

---

## 7. Modular RAG

**Khi nào dùng:** Hệ thống cần tiến hóa liên tục theo thời gian (thêm kỹ thuật mới khi có nghiên cứu mới), hoặc team cần A/B test nhiều chiến lược retrieval/rerank khác nhau mà không viết lại toàn bộ pipeline.

**Các bước:**
1. Thiết kế pipeline thành các module độc lập, có giao diện chuẩn: Query Transformer → Retriever → Reranker → Generator → (tùy chọn) Verifier.
2. Mỗi module có thể thay thế/nâng cấp riêng lẻ mà không ảnh hưởng module khác.
3. Dùng cấu hình/orchestration layer để định tuyến linh hoạt giữa các module tùy loại truy vấn (có thể kết hợp với Adaptive RAG ở bước định tuyến).

**Ví dụ thực tế:** Một công ty SaaS B2B vận hành trợ lý tra cứu tài liệu sản phẩm cho 200 khách hàng doanh nghiệp. Ban đầu họ dùng reranker của Cohere, sau 6 tháng đội kỹ thuật muốn thử reranker mã nguồn mở để giảm chi phí. Vì kiến trúc modular, họ chỉ thay module Reranker (không đụng vào Retriever hay Generator), chạy A/B test 2 tuần để so sánh chất lượng trước khi quyết định chuyển hẳn — không phải viết lại cả hệ thống.

- **Ưu điểm:** Dễ nâng cấp từng phần khi có kỹ thuật mới, dễ A/B test, phù hợp hệ thống cần tiến hóa liên tục.
- **Nhược điểm:** Yêu cầu thiết kế kiến trúc tốt ngay từ đầu, tăng chi phí kỹ thuật/kiến trúc ban đầu.

**Tham khảo:**
- [12 Advanced RAG Techniques — Atlan](https://atlan.com/know/advanced-rag-techniques/)

---

## 8. Multimodal RAG

**Khi nào dùng:** Tài liệu nguồn chứa nhiều hình ảnh, biểu đồ, bảng biểu quan trọng (báo cáo tài chính, tài liệu kỹ thuật/y tế, slide thuyết trình) — nơi thông tin quan trọng không chỉ nằm ở văn bản thuần.

**Các bước:**
1. Trích xuất nội dung đa phương thức: OCR cho ảnh chứa chữ, parsing bảng thành cấu trúc, tách hình ảnh riêng.
2. Dùng mô hình embedding đa phương thức (ví dụ CLIP hoặc embedding đa phương thức của các nhà cung cấp LLM) để embed cả văn bản và hình ảnh vào cùng một không gian vector.
3. Lưu index kết hợp (văn bản + hình ảnh + bảng đã cấu trúc hóa).
4. Truy vấn: tìm kiếm trên index đa phương thức, có thể trả về cả đoạn văn lẫn hình ảnh/bảng liên quan.
5. Đưa cả văn bản và hình ảnh (nếu LLM hỗ trợ input đa phương thức) vào prompt để sinh câu trả lời.

**Ví dụ thực tế:** Một nhà máy sản xuất có bộ tài liệu hướng dẫn bảo trì máy móc dạng PDF, trong đó lỗi thường được minh họa bằng sơ đồ mạch điện và ảnh chụp linh kiện, không chỉ mô tả bằng chữ. Kỹ thuật viên chụp ảnh một linh kiện bị lỗi và hỏi "linh kiện này bị lỗi gì, cách sửa ra sao?" — hệ thống multimodal RAG so khớp ảnh chụp với các hình ảnh linh kiện trong tài liệu hướng dẫn, tìm ra đúng trang có sơ đồ và văn bản mô tả cách sửa lỗi đó.

- **Ưu điểm:** Cần thiết cho tài liệu có hình ảnh/biểu đồ/bảng mà văn bản thuần không đủ diễn đạt.
- **Nhược điểm:** Chất lượng embedding đa phương thức hiện chưa đồng đều bằng văn bản thuần; xử lý phức tạp hơn (OCR, parsing bảng, đồng bộ nhiều loại dữ liệu).

**Tham khảo:**
- [20 Advanced RAG Types to Know in 2026 — Turing Post](https://www.turingpost.com/p/ragtypes)
- [Multimodal RAG: A Hands-On Guide to Learning from Documents — DataCamp](https://www.datacamp.com/tutorial/multimodal-rag-hands-on-guide)

---

## 9. Chiến lược Caching trong LLM / RAG

**Khi nào dùng:** Khi hệ thống đã vào production, có lượng người dùng lớn và cần tối ưu chi phí cũng như độ trễ phản hồi.

### 9.1 Semantic Caching (Application Cache)
- **Bản chất:** Lưu cặp `Query -> Response` vào Vector DB hoặc Redis. Khi có câu hỏi mới đạt độ tương đồng ngữ nghĩa cao với câu hỏi cũ (Threshold khoảng `0.88–0.92`), hệ thống trả về câu trả lời có sẵn.
- **Lợi ích:** Chi phí 0đ cho LLM và độ trễ gần như tức thì.

### 9.2 Prompt Caching (KV Cache)
- **Bản chất:** Lưu lại trạng thái tính toán của đoạn System Prompt hoặc tài liệu gốc dài (context) trên server của nhà cung cấp mô hình (như Anthropic, OpenAI, Gemini). 
- **Lợi ích:** LLM vẫn sinh câu trả lời mới cho từng câu hỏi khác nhau nhưng tiết kiệm tới **90% chi phí token đầu vào** (vì phần tài liệu dài đã được cache).

---

## 10. Khung kiến trúc khuyến nghị cho hệ thống thực chiến (Production)

Một pipeline RAG toàn diện, ổn định và tối ưu chi phí hiện nay thường kết hợp các thành phần theo chuỗi:

```text
[User Query]
     │
     ▼
[Semantic Cache] ──(Trùng khớp ≥ 0.90)──► [Trả về Response ngay lập tức]
     │ (Cache Miss)
     ▼
[Hybrid Retrieval: Contextual Vector + Contextual BM25] (Lấy Top 100)
     │
     ▼
[Reranker: Cross-Encoder như Cohere / BGE-Reranker] (Lọc xuống Top 10–20)
     │
     ▼
[Kiểm tra độ liên quan (Evaluator cơ bản dạng CRAG)]
     ├── Nếu thiếu/sai ──► [Web Search bổ sung]
     └── Nếu đủ ─────────► [Đưa vào Generator LLM cùng Prompt Caching]
```

---

## Bảng so sánh tổng hợp các kỹ thuật RAG

| Phương pháp | Cơ chế hoạt động cốt lõi | Vấn đề chính cần giải quyết | Khi nào nên áp dụng? |
|---|---|---|---|
| **Standard RAG** | Chia văn bản thành chunks → Vector → Top-K Cosine | Tìm kiếm cơ bản | Dự án PoC, kho tài liệu nhỏ, văn bản đơn giản |
| **Contextual Retrieval** | LLM sinh ngữ cảnh ghép vào chunk trước khi tạo vector/BM25 | Hiện tượng mất ngữ cảnh (context loss) khi cắt nhỏ | Tài liệu pháp lý, tài chính, kỹ thuật cần độ chính xác cao |
| **Two-Stage RAG + Reranking** | B1: Lấy rộng Top 100-150. B2: Cross-Encoder chọn Top 10-20 | Bi-Encoder bắt rộng nhưng lộn xộn, nhiều rác | Mọi hệ thống RAG production cần cân bằng chính xác - độ trễ |
| **RankGPT** | Đưa chunks vào LLM để suy luận và hoán vị thứ tự | Khắc phục giới hạn của mô hình rerank truyền thống | Nghiên cứu học thuật, sinh nhãn dữ liệu chưng cất |
| **Corrective RAG (CRAG)** | Evaluator kiểm tra tài liệu: Đúng -> Tinh lọc; Sai -> Web Search | CSDL nội bộ thiếu thông tin hoặc sai lệch | Hỏi đáp mở, tri thức biến động liên tục (tin tức, thị trường) |
| **Recursive Retrieval** | Tầng 1: Đối chiếu Summary. Tầng 2: Đào sâu vào chunks | Ngăn chặn nhiễu chéo (cross-document noise) | Tài liệu dạng sách, báo cáo chuyên sâu, tri thức phân cấp |
| **GraphRAG / RAPTOR** | Đồ thị tri thức, cụm tóm tắt đệ quy | Suy luận đa bước, tổng hợp toàn cục | Tra cứu cần góc nhìn toàn cảnh (global sensemaking) |
| **Agentic RAG** | Agent điều phối tool, DB, API | Cần tra cứu kết hợp đa nguồn, tự phản tư lập kế hoạch | Câu hỏi cực kì phức tạp, tốn kém chi phí |

## Gợi ý lộ trình chọn phương pháp

1. Bắt đầu với **Hybrid RAG (dense + BM25) + Cross-encoder Reranker** — đủ tốt cho phần lớn trường hợp và là chuẩn production hiện nay.
2. Nếu tài liệu dài/cấu trúc phức tạp → thêm **Parent-Child chunking** hoặc **Contextual Retrieval**.
3. Nếu cần giảm hallucination/tự sửa lỗi → thêm **Self-RAG** hoặc **Corrective RAG**.
4. Nếu hệ thống có nhiều dạng câu hỏi (đơn giản lẫn phức tạp) → dùng **Adaptive RAG** để định tuyến, tiết kiệm chi phí.
5. Chỉ dùng **GraphRAG / RAPTOR / Agentic RAG** khi đã chứng minh các phương pháp trên không đủ cho loại câu hỏi cần suy luận đa bước/toàn cảnh — vì chi phí và độ phức tạp tăng mạnh.

---

*Tổng hợp từ các bài nghiên cứu gốc và bài phân tích 2025–2026 — xem link tham khảo trong từng mục ở trên.*
