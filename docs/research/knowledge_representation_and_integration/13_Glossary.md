# Bảng thuật ngữ và từ viết tắt

> Tra nhanh các từ viết tắt và thuật ngữ dùng trong thư mục này. Mỗi file cũng giải thích lần đầu từ đó xuất hiện. Sắp xếp theo nhóm.

## Giao thức, định dạng, sản phẩm

| Thuật ngữ | Giải thích |
|---|---|
| ACID | Atomicity, Consistency, Isolation, Durability, bốn đảm bảo giao dịch của cơ sở dữ liệu |
| API | Application Programming Interface, giao diện để chương trình này gọi chương trình khác |
| BFS | Breadth-First Search, duyệt đồ thị theo từng lớp hàng xóm |
| BM25 | thuật toán xếp hạng theo từ khóa, đếm mức trùng từ giữa câu hỏi và văn bản |
| CIMD | Client ID Metadata Document, client dùng một URL chứa metadata làm danh tính |
| CLI | Command-Line Interface, giao diện dòng lệnh |
| CSP | Content Security Policy, header HTTP giới hạn mã được chạy trên trang |
| CSRF | Cross-Site Request Forgery, giả mạo yêu cầu từ một trang web khác |
| CTE | Common Table Expression, truy vấn SQL con có đặt tên, dùng được đệ quy |
| Cypher | ngôn ngữ truy vấn đồ thị của Neo4j |
| DCR | Dynamic Client Registration, client tự đăng ký với máy chủ xác thực lúc chạy |
| DMR | Deep Memory Retrieval, bộ câu hỏi hội thoại để đo trí nhớ của agent |
| GraphRAG | RAG dùng đồ thị tri thức thay vì chỉ các đoạn văn rời rạc |
| IDE | Integrated Development Environment, môi trường lập trình tích hợp |
| IdP | Identity Provider, nhà cung cấp danh tính để đăng nhập |
| JSON-RPC | giao thức gọi hàm từ xa bằng JSON, nền của MCP |
| KG | Knowledge Graph, đồ thị tri thức: nút là thực thể, cạnh là quan hệ giữa chúng |
| LLM | Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT, Gemini |
| LoCoMo | Long-term Conversational Memory, bộ benchmark hội thoại dài để đo trí nhớ của agent |
| LongMemEval | bộ benchmark đo trí nhớ dài hạn của chatbot qua nhiều phiên hội thoại |
| MCP | Model Context Protocol, giao thức chuẩn để ứng dụng AI gọi công cụ và dữ liệu của một server bên ngoài |
| MMR | Maximal Marginal Relevance, xếp hạng ưu tiên kết quả vừa liên quan vừa không trùng nhau |
| OAuth | chuẩn ủy quyền cho phép ứng dụng truy cập dịch vụ thay người dùng mà không lộ mật khẩu |
| OKF | Open Knowledge Format, định dạng mở lưu tri thức thành thư mục file markdown có khối YAML ở đầu mỗi file |
| OpenAPI | chuẩn mô tả API REST bằng JSON hoặc YAML |
| OWL | Web Ontology Language, ngôn ngữ mô tả ontology |
| RAG | Retrieval-Augmented Generation, tìm đoạn tài liệu liên quan rồi đưa cho LLM đọc để trả lời |
| RDF | Resource Description Framework, mô hình dữ liệu dạng bộ ba chủ ngữ, vị ngữ, tân ngữ |
| REST | kiểu API web gọi qua HTTP |
| RRF | Reciprocal Rank Fusion, cách gộp nhiều bảng xếp hạng thành một bằng cách cộng 1 chia hạng |
| SDK | Software Development Kit, bộ thư viện lập trình |
| SEP | Specification Enhancement Proposal, đề xuất thay đổi đặc tả MCP |
| SPARQL | ngôn ngữ truy vấn dữ liệu RDF |
| SSE | Server-Sent Events, kênh HTTP một chiều để server đẩy dữ liệu về client |
| SSRF | Server-Side Request Forgery, lừa server gửi request tới địa chỉ nội bộ |
| stdio | standard input/output, giao tiếp qua đầu vào/ra chuẩn của tiến trình, dùng cho server chạy trên máy cục bộ |
| Streamable HTTP | kiểu truyền của MCP qua HTTP, thay cho HTTP+SSE cũ |
| TTL | Time To Live, thời gian sống của dữ liệu trong cache |
| UI | User Interface, giao diện người dùng |
| URI | Uniform Resource Identifier, chuỗi định danh tài nguyên, URL là một loại |
| VRAM | bộ nhớ của card đồ họa |
| YAML | định dạng văn bản khai báo dạng khóa: giá trị |

## Đánh giá

| Thuật ngữ | Giải thích |
|---|---|
| ablation | thí nghiệm bỏ từng thành phần để xem nó đóng góp bao nhiêu |
| baseline | hệ thống đối chứng dùng để so sánh |
| EM | Exact Match, tỉ lệ đáp án khớp hoàn toàn với đáp án chuẩn |
| F1 | điểm cân bằng giữa độ chính xác và độ phủ khi so đáp án |
| harness | bộ khung chạy thí nghiệm với điều kiện cố định |
| MRR | Mean Reciprocal Rank, trung bình của 1 chia hạng của kết quả đúng |
| p95 | phân vị 95, 95 phần trăm lượt chạy nhanh hơn mức này |

## Công cụ, thư viện

| Thuật ngữ | Giải thích |
|---|---|
| BigQuery | kho dữ liệu phân tích của Google Cloud |
| Chainlit | framework Python để dựng giao diện chatbot |
| FastMCP | framework Python rút gọn việc viết MCP server |
| Gradio | thư viện Python dựng nhanh giao diện demo |
| LangChain | framework xây ứng dụng dùng LLM |
| LiteLLM | thư viện và proxy để gọi nhiều nhà cung cấp LLM qua một giao diện chung |
| mcpo | proxy của Open WebUI, bọc MCP server thành API OpenAPI |
| Neo4j | cơ sở dữ liệu đồ thị phổ biến |
| Obsidian | ứng dụng ghi chú dùng file markdown |
| Ollama | công cụ chạy LLM mã nguồn mở ngay trên máy cá nhân |
| Open WebUI | giao diện chat mã nguồn mở, nối được với Ollama và các API tương thích OpenAI |
| pgvector | phần mở rộng của PostgreSQL để lưu và tìm vector |
| Qdrant | cơ sở dữ liệu vector mã nguồn mở |
| Streamlit | thư viện Python dựng nhanh ứng dụng web dữ liệu |
| vLLM | engine phục vụ LLM mã nguồn mở với tốc độ cao |

## Thuật ngữ chuyên môn

| Thuật ngữ | Giải thích |
|---|---|
| agent | chương trình dùng LLM để tự lập kế hoạch và gọi công cụ |
| bi-temporal | theo dõi hai trục thời gian: lúc sự việc đúng ngoài đời và lúc hệ thống biết về nó |
| Boomerang | mẫu thiết kế: đồ thị chỉ giữ con trỏ, khi cần chi tiết thì quay về VectorDB lấy chunk gốc |
| chunk | một đoạn văn bản được cắt ra để lưu và tìm kiếm |
| connector | kết nối để chatbot dùng dịch vụ bên ngoài, ví dụ một MCP server |
| CoT | Chain-of-Thought, bắt LLM suy luận từng bước trước khi trả lời |
| cross-encoder | mô hình đọc cùng lúc câu hỏi và đoạn văn để chấm độ liên quan, chính xác hơn nhưng chậm hơn |
| embedding | vector số biểu diễn ý nghĩa của văn bản, hai văn bản gần nghĩa thì vector gần nhau |
| Evolution | tiến hóa: sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên lên giám đốc; xử lý bằng cách đóng end_time |
| Falsehood | thông tin sai ngay từ đầu, ví dụ tin đồn bị đính chính; đánh dấu bằng invalidated_at |
| frontmatter | khối YAML ở đầu file markdown chứa metadata |
| function calling | LLM trả về yêu cầu gọi một hàm kèm tham số, chương trình chạy hàm rồi trả kết quả lại cho LLM |
| GraphDB | cơ sở dữ liệu đồ thị, ví dụ Neo4j |
| half-life decay | điểm giảm dần theo thời gian, sau mỗi chu kỳ bán rã chỉ còn một nửa |
| hard filter | bộ lọc cứng, loại bỏ hẳn kết quả không thỏa điều kiện |
| hybrid search | tìm kiếm kết hợp theo nghĩa embedding và theo từ khóa BM25 |
| ingest | nạp tài liệu vào hệ thống |
| Ingestion | giai đoạn nạp tài liệu vào hệ thống |
| lint | kiểm tra định kỳ để tìm lỗi và mâu thuẫn |
| payload | dữ liệu kèm theo mỗi vector, ví dụ ngày và nguồn |
| Plain RAG | RAG thuần, chỉ tìm theo độ giống nghĩa và không kiểm soát thời gian |
| progressive disclosure | tiết lộ dần, chỉ mở thêm chi tiết khi cần |
| prompt injection | nhét chỉ thị độc hại vào nội dung để LLM làm theo |
| provenance | nguồn gốc của thông tin |
| rerank | chấm lại thứ hạng của các kết quả đã tìm được |
| reranker | mô hình chấm lại thứ hạng của các kết quả đã tìm được |
| stateless | không giữ trạng thái giữa các request |
| T_now | giờ hiện tại của server, dùng để đổi thời gian tương đối như năm ngoái thành ngày cụ thể |
| T_req | mốc thời gian mà câu hỏi nhắm tới |
| Temporal Freshness | độ tươi mới theo thời gian: hệ thống cập nhật tri thức mới nhanh và đúng đến mức nào |
| Time-CoT | Chain-of-Thought theo thời gian: bắt LLM suy luận từng bước, trước hết xác định mốc thời gian |
| tool | công cụ hay hàm mà LLM được phép gọi |
| tool call | một lần LLM yêu cầu gọi công cụ kèm tham số |
| triplet | bộ ba chủ thể, quan hệ, đối tượng, ví dụ Ông A, bị bắt, 2024 |
| VectorDB | cơ sở dữ liệu vector, lưu embedding và tìm theo độ giống nghĩa |

## Ontology và web ngữ nghĩa

| Thuật ngữ | Giải thích |
|---|---|
| 4D fluents | cách biểu diễn thời gian bằng các lát cắt thời gian của thực thể |
| Akoma Ntoso | chuẩn XML cho văn bản lập pháp |
| Allen interval algebra | đại số 13 quan hệ giữa hai khoảng thời gian: trước, sau, gặp, chồng lấn, nằm trong… |
| ELI | European Legislation Identifier, chuẩn định danh và metadata cho luật EU |
| FRBR | Functional Requirements for Bibliographic Records, mô hình thư mục học |
| IRI | Internationalized Resource Identifier, định danh dạng URL cho tài nguyên RDF |
| JSON-LD | cách viết dữ liệu RDF dưới dạng JSON |
| LRMoo | ontology thư mục học dùng để mô hình phiên bản của tác phẩm, kể cả văn bản luật |
| N-ary relation | quan hệ nhiều ngôi, nối từ ba thực thể trở lên |
| Named graph | đồ thị đặt tên, gom nhiều bộ ba để gắn thông tin chung như thời hạn |
| Ontology | đặc tả hình thức các loại thực thể, quan hệ và ràng buộc trong một miền; khác KG ở chỗ KG là dữ liệu cụ thể |
| OWL | Web Ontology Language, ngôn ngữ ontology có suy diễn |
| OWL-Time | ontology W3C về thời gian, dựa trên 13 quan hệ khoảng của Allen |
| Property graph | đồ thị thuộc tính: node và cạnh đều mang được cặp khóa-giá trị, như Neo4j |
| PROV-O | Provenance Ontology, ontology W3C về nguồn gốc dữ liệu |
| Qualifier | trong Wikidata: thuộc tính phụ gắn vào một fact, như start time, end time |
| Rank | trong Wikidata: mức normal, preferred, deprecated của một fact |
| RDF | Resource Description Framework, mô hình dữ liệu dạng bộ ba chủ ngữ, vị ngữ, tân ngữ |
| RDF-star | mở rộng RDF cho phép bộ ba làm tân ngữ của bộ ba khác, nay là triple term trong RDF 1.2 |
| RDFS | RDF Schema, mở rộng RDF với lớp và thuộc tính |
| Reification | biến một câu quan hệ thành một node để gắn thêm thông tin như thời gian |
| SHACL | Shapes Constraint Language, kiểm tra dữ liệu có đúng hình dạng mong muốn |
| SKOS | Simple Knowledge Organization System, chuẩn W3C mô tả thesaurus và phân loại |
| Taxonomy | phân loại theo cấp bậc cha-con |
| Thesaurus | bảng thuật ngữ có quan hệ rộng, hẹp, liên quan |
| W3C | World Wide Web Consortium, tổ chức đặt chuẩn web |

# Bổ sung từ lần duyệt toàn bộ file

## Khái niệm riêng của đồ án

| Thuật ngữ | Giải thích |
|---|---|
| as_of | tham số của tool: tra cứu tri thức như nó có hiệu lực tại ngày này |
| Boomerang | đồ thị chỉ giữ bộ ba gọn và Chunk_ID, cần chi tiết thì quay về VectorDB lấy chunk gốc |
| Case 1 / Case 2 | hai trường hợp chấm điểm thời gian: Case 1 mốc hỏi nằm trong khoảng hiệu lực (điểm 1.0), Case 2 lấy bản gần nhất trong quá khứ và giảm điểm theo số năm |
| Chunk_ID | mã của chunk, dùng làm con trỏ từ đồ thị về văn bản gốc |
| Cơ chế 1 / 2 / 3 | ba hướng của đồ án: Temporal Retrieval (tìm theo mốc thời gian), Timeline Summarization (tóm tắt dòng thời gian), Conflict Resolution (xử lý thông tin mâu thuẫn) |
| Cạnh SUPERSEDES / CORRECTS / SUSPECTS / TIẾP_THEO | thay thế, đính chính, bị nghi ngờ (cáo buộc chứ không phải sự thật), và sự kiện kế tiếp trong một chuỗi |
| Evolution | sự việc từng đúng rồi thay đổi theo thời gian; đóng bằng end_time, vẫn trả về cho câu hỏi về quá khứ |
| Falsehood | thông tin sai từ đầu; đánh dấu bằng invalidated_at, bị lọc khỏi kết quả mặc định |
| ingested_at | thời điểm hệ thống nạp thông tin (đề xuất thêm vào schema); khác với thời gian sự việc xảy ra |
| invalidated_at | thời điểm đánh dấu một chunk là sai từ gốc hoặc không còn thuộc bản hiện tại |
| leakage_rate | tỉ lệ câu hỏi mà top kết quả chứa thông tin của tương lai so với mốc hỏi; kỳ vọng 0 phần trăm |
| No future leakage | không để lộ thông tin sau mốc hỏi; mọi chunk có start_time lớn hơn T_req bị loại |
| Query Profiler | bước phân tích câu hỏi để rút ra mốc thời gian và loại câu hỏi |
| start_time / end_time | ngày bắt đầu và kết thúc hiệu lực của một thông tin ngoài đời; end_time rỗng nghĩa là còn hiệu lực |

## Bộ nhớ agent và đánh giá

| Thuật ngữ | Giải thích |
|---|---|
| ADD / UPDATE / DELETE / NOOP | bốn thao tác Mem0 chọn khi gặp thông tin mới: thêm, sửa, xóa, bỏ qua |
| Agent memory | bộ nhớ dài hạn cho chương trình dùng LLM: tự ghi, tìm lại và cập nhật thông tin qua nhiều lượt trò chuyện |
| BLEU-1 (B1) | điểm đo mức trùng từ đơn giữa câu trả lời và đáp án chuẩn |
| Community (Zep) | cụm các node liên quan trong đồ thị được tóm tắt thành một mô tả chung |
| Context window | lượng token tối đa LLM đọc được trong một lần |
| Core / archival / recall (Letta) | ba tầng bộ nhớ của Letta (kiến thức chung, chưa kiểm): ngữ cảnh chính, kho lưu dài hạn, lịch sử hội thoại |
| Episode (Zep) | một đơn vị dữ liệu gốc đưa vào Zep, ví dụ một tin nhắn hay một văn bản |
| Full-context | đưa toàn bộ lịch sử hội thoại vào LLM mỗi lần hỏi, làm đối chứng đắt nhưng đầy đủ |
| J (LLM-as-a-Judge) | điểm do một LLM chấm câu trả lời đúng hay sai |
| Latency | độ trễ từ lúc hỏi đến lúc có kết quả |
| Mem0^g | biến thể đồ thị của Mem0, lưu bộ ba thay vì câu fact phẳng |
| Single-hop / Multi-hop | câu hỏi cần một bước tra cứu hay nhiều bước nối nhau |
| Temporal / Open-domain (LoCoMo) | hai loại câu hỏi: về thời gian, và cần kiến thức ngoài hội thoại |
| Token | đơn vị cắt nhỏ văn bản mà LLM đọc; chi phí và giới hạn ngữ cảnh tính theo token |
| valid_at / invalid_at / created_at / expired_at | bốn mốc thời gian trên cạnh của Zep: hai mốc đầu là hiệu lực ngoài đời, hai mốc sau là lúc hệ thống ghi nhận và lúc hệ thống thấy nó hết hiệu lực |
| Zettelkasten (A-Mem) | kiểu ghi chú nhỏ nối với nhau bằng liên kết, dùng làm ý tưởng cho bộ nhớ agent |

## OKF và wiki

| Thuật ngữ | Giải thích |
|---|---|
| Attestation | xác nhận mỗi lần chạy rằng một con số được tính đúng cách đã được phê duyệt; khác với verified ở cấp tài liệu |
| Bundle | một thư mục OKF tự chứa, đơn vị phân phối |
| Concept (OKF) | một file markdown mô tả một đơn vị tri thức; đường dẫn file là danh tính của nó |
| Idea file / gist | tệp ý tưởng đăng dạng gist (một trang ghi chú trên GitHub), để dán cho agent tự dựng phiên bản phù hợp |
| Memex | ý tưởng năm 1945 của Vannevar Bush về kho tri thức cá nhân nối bằng liên kết |
| OKF profile | bộ quy ước riêng đặt lên trên OKF, ví dụ thêm các trường thời gian của đồ án |
| Producer / Consumer | bên ghi bundle OKF và bên đọc nó |
| sources / generated / verified | khóa OKF v0.2: nguồn của nội dung, ai viết và lúc nào, ai đã xác minh |
| status / stale_after | khóa OKF v0.2: trạng thái draft, stable hoặc deprecated; và thời điểm sau đó nội dung được coi là cũ |
| Trust tier | mức tin cậy suy ra từ verified: chưa xác minh, máy xác nhận, hoặc người xem xét |

## MCP, triển khai và bảo mật

| Thuật ngữ | Giải thích |
|---|---|
| Automatic function calling | SDK tự chạy hàm mà LLM yêu cầu rồi gửi kết quả lại, không cần viết vòng lặp tay |
| Confused deputy | server dùng quyền của mình thay cho kẻ không có quyền |
| Docker / Docker Compose | đóng gói chương trình vào container; Compose chạy nhiều container cùng lúc |
| FastAPI | framework Python dựng API web |
| Host / Client / Server (MCP) | ứng dụng AI người dùng dùng, phần nối bên trong nó, và chương trình cung cấp công cụ hay dữ liệu |
| OpenAI-compatible | API theo định dạng của OpenAI, nhiều hệ khác (Ollama, vLLM, LiteLLM) cũng hỗ trợ |
| Proxy / Gateway / Bridge | lớp trung gian chuyển tiếp hay dịch giữa hai bên; gateway quản lý nhiều server tập trung, bridge nối hệ không nói MCP |
| Quantization (lượng tử hóa) | nén trọng số mô hình để chạy trên máy yếu, đổi lại có thể giảm chất lượng |
| Scope (OAuth) | phạm vi quyền một token được cấp; nên chỉ cấp tối thiểu |
| Token passthrough | server chuyển tiếp token không cấp riêng cho nó; spec MCP cấm |
| Tool poisoning / rug pull | giấu chỉ thị độc trong mô tả tool; hoặc đổi mô tả sau khi người dùng đã tin |
| Tools / Resources / Prompts | ba loại thứ MCP server phơi: hàm gọi được, dữ liệu đọc được theo địa chỉ, và mẫu lời nhắc |
| Transport | cách MCP truyền tin: stdio cho máy cục bộ, Streamable HTTP cho từ xa |
| Tunnel (ngrok, Cloudflare Tunnel) | đường hầm đưa một server trên máy cá nhân ra Internet với địa chỉ HTTPS công khai |
| Zero Data Retention | chế độ nhà cung cấp không lưu dữ liệu sau khi xử lý |

## Lưu trữ và triển khai

| Thuật ngữ | Giải thích |
|---|---|
| APOC | bộ thủ tục mở rộng của Neo4j; Apache AGE không có |
| Bolt | giao thức Neo4j dùng cho driver, cổng 7687 |
| BSL | Business Source License, giấy phép mã nguồn có điều kiện, Memgraph Community dùng |
| Docker Compose | tệp mô tả nhiều container chạy cùng nhau |
| Docker image / container / volume | gói phần mềm đóng sẵn; bản đang chạy của nó; thư mục của máy gắn vào container để giữ dữ liệu |
| Embedded database (nhúng) | cơ sở dữ liệu chạy ngay trong tiến trình ứng dụng, không cần server riêng, ví dụ Kuzu |
| Graph database | cơ sở dữ liệu đồ thị, lưu nút và cạnh, ví dụ Neo4j, Memgraph |
| gRPC | kiểu giao diện lập trình nhanh giữa các chương trình; Qdrant dùng cổng 6334 |
| HNSW / IVFFlat | hai loại chỉ mục tìm vector gần đúng của pgvector: đồ thị nhiều tầng nhanh nhưng tốn bộ nhớ; chia cụm xây nhanh nhưng truy vấn kém hơn |
| Idempotent | làm lại nhiều lần cho cùng kết quả; hash nội dung giúp nạp tài liệu idempotent |
| RocksDB | kho khóa-giá trị nhúng, Oxigraph dùng làm nơi lưu |
| TDB (Jena) | kho bộ ba bền của Apache Jena |
| Triple store | cơ sở dữ liệu lưu bộ ba RDF và trả lời SPARQL, ví dụ Fuseki, GraphDB, Oxigraph |
| Vector database | cơ sở dữ liệu lưu embedding và tìm theo độ giống nghĩa, ví dụ Qdrant |
