# Định dạng tri thức mở & cách phục vụ cho Agent (Knowledge Format & Serving)

> Thư mục này trả lời một câu hỏi **ngoài 3 cơ chế lõi** của đồ án (Cơ chế 1: Temporal Retrieval, tìm thông tin đúng tại một mốc thời gian; Cơ chế 2: Timeline Summarization, tóm tắt diễn biến theo thời gian; Cơ chế 3: Conflict Resolution, xử lý thông tin mâu thuẫn): *tri thức time-aware (có nhận biết thời gian: biết thông tin nào đúng vào lúc nào) nên được **biểu diễn** ở dạng nào (không quá mịn như ontology, tức bản mô tả hình thức các loại thực thể và quan hệ được phép có, ví dụ "Người làm_việc_tại Tổ chức") và **đưa cho agent (chương trình dùng LLM để tự lập kế hoạch và gọi công cụ)** (Claude, ChatGPT, agent tự viết) bằng cách nào?*
> **Đọc `11` trước** nếu chỉ có ít thời gian: đó là bản tổng hợp, phân biệt và ý nghĩa cho từng cơ chế.

## Thứ tự đọc

| File | Nội dung | Nguồn đã đọc |
|---|---|---|
| [`11_Synthesis_and_Comparison.md`](11_Synthesis_and_Comparison.md) | **Tổng hợp**: 4 lớp, bảng phân biệt hệ thống, giúp gì cho Cơ chế 1/2/3, đề xuất schema | Tổng hợp `01`–`10` |
| [`01_Knowledge_Representation_Spectrum.md`](01_Knowledge_Representation_Spectrum.md) | Phổ biểu diễn: ontology → KG (Knowledge Graph, đồ thị tri thức: nút là thực thể, cạnh là quan hệ giữa chúng) → KG node-văn xuôi → wiki → chunk (một đoạn văn bản được cắt ra để lưu và tìm kiếm) phẳng | Kiến thức chung |
| [`02_Open_Knowledge_Format_OKF.md`](02_Open_Knowledge_Format_OKF.md) | OKF (Open Knowledge Format, định dạng mở lưu tri thức thành thư mục file markdown, mỗi file có một khối YAML là phần khai báo "khóa: giá trị" ở đầu) bản v0.1 (**đã cũ**, xem `09`) | Tin tức, trang Google Cloud |
| [`03_Graph_vs_Vector_vs_Wiki.md`](03_Graph_vs_Vector_vs_Wiki.md) | Temporal retrieval (tìm theo mốc thời gian) có cần graph (đồ thị) không; 4 phương án | Preprint + blog |
| [`04_Agent_Memory_Systems.md`](04_Agent_Memory_Systems.md) | Bảng tra nhanh các hệ thống "trí nhớ cho agent"; Letta, A-Mem chưa đọc gốc | Search |
| [`05_MCP_and_Agent_Tooling.md`](05_MCP_and_Agent_Tooling.md) | **Kiến thức nền** về MCP (Model Context Protocol, giao thức chuẩn để ứng dụng AI gọi công cụ và dữ liệu của một server bên ngoài) (bản 2026-07-28), Claude/ChatGPT, SDK (Software Development Kit, bộ thư viện lập trình) | Changelog MCP; ChatGPT từ nguồn thứ cấp |
| [`12_Chatbot_vs_MCP_Server_Multi_LLM.md`](12_Chatbot_vs_MCP_Server_Multi_LLM.md) | **Hướng triển khai đồ án**: chatbot vs MCP server, chạy đa LLM (Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT, Gemini) (Claude, OpenAI, Gemini, model mở), thiết kế tool (công cụ hay hàm mà LLM được phép gọi), bảo mật, đánh giá | Docs OpenAI, LiteLLM, mcpo, MCP security (đã mở); phần còn lại thứ cấp |
| [`06_Applicability_to_Thesis.md`](06_Applicability_to_Thesis.md) | Khuyến nghị, OKF profile nháp, kế hoạch thử, câu hỏi mở | Suy luận |
| [`07_Zep_Graphiti_Temporal_KG.md`](07_Zep_Graphiti_Temporal_KG.md) | Paper Zep: KG (đồ thị tri thức) bi-temporal (theo dõi hai trục thời gian: lúc sự việc đúng ngoài đời và lúc hệ thống biết về nó), so với các bất biến (quy tắc bắt buộc luôn đúng) của đồ án | **Paper (PDF)** + mã Graphiti (nhãn riêng) |
| [`08_Mem0_Agent_Memory.md`](08_Mem0_Agent_Memory.md) | Paper Mem0/Mem0^g, bảng số LoCoMo (Long-term Conversational Memory, bộ benchmark hội thoại dài để đo trí nhớ của agent) | **Paper (PDF)** |
| [`09_OKF_v0.2_Spec.md`](09_OKF_v0.2_Spec.md) | Đặc tả OKF v0.2 | `SPEC.md` (qua WebFetch, bản diễn giải) |
| [`10_Karpathy_LLM_Wiki.md`](10_Karpathy_LLM_Wiki.md) | Gist LLM Wiki: 3 lớp, ingest (nạp tài liệu vào hệ thống)/query/lint (kiểm tra định kỳ để tìm lỗi và mâu thuẫn) | Gist (qua WebFetch, bản diễn giải) |
| [`14_Ontology_and_Temporal_Representation.md`](14_Ontology_and_Temporal_Representation.md) | **Ontology**: phân biệt với taxonomy (cây phân loại, ví dụ Động vật → Có vú → Mèo) và KG, cách biểu diễn thời gian (reification: biến một quan hệ thành một nút để gắn thêm thông tin như ngày; 4D fluents: tách mỗi "phiên bản theo thời gian" của sự vật thành nút riêng; RDF-star: gắn thông tin lên chính một bộ ba; qualifier + rank của Wikidata: thuộc tính phụ và mức ưu tiên của mỗi giá trị), OWL-Time và PROV-O (hai chuẩn của W3C: một để mô tả thời gian, một để mô tả nguồn gốc dữ liệu), ontology pháp luật, ánh xạ trường của đồ án ↔ chuẩn | Wikidata Help, arXiv 2506.07853 (đã mở); W3C bị chặn 403 nên thứ cấp |
| [`15_Storage_and_Deployment_per_Approach.md`](15_Storage_and_Deployment_per_Approach.md) | **Lưu trữ và Docker** cho từng cách biểu diễn: triple store, graph database, vector database, file + git; giấy phép, cổng, cách lọc thời gian; phương án gộp vào Postgres; mẫu Docker Compose | Tài liệu chính thức Qdrant, Neo4j, GraphDB, Oxigraph, Fuseki, AGE, pgvector, Memgraph (đã mở); còn lại thứ cấp |

> **Giải thích nhanh các tên trong bảng:** LiteLLM là thư viện và proxy (máy chủ trung gian) để gọi nhiều nhà cung cấp LLM qua một giao diện chung; mcpo là proxy của Open WebUI, bọc một MCP server thành API theo chuẩn OpenAPI (cách mô tả API qua HTTP) để các ứng dụng không hỗ trợ MCP vẫn dùng được; multi-LLM (đa LLM) nghĩa là hệ thống chạy được với nhiều model khác nhau; Mem0^g là biến thể của Mem0 lưu trí nhớ dưới dạng đồ thị (chữ g là graph).

> **Gặp từ viết tắt hay thuật ngữ lạ:** mỗi file đều giải thích trong ngoặc ở lần đầu từ đó xuất hiện; có thể tra nhanh ở [`13_Glossary.md`](13_Glossary.md) (bảng thuật ngữ và từ viết tắt).

## Cách đọc độ tin cậy

- `07`, `08` đọc từ PDF paper. `09`, `10` đọc qua WebFetch (công cụ tải trang web, rồi một model nhỏ tóm tắt lại), nên tên khóa/enum (danh sách giá trị cố định cho phép) đáng tin hơn câu chữ.
- `SPEC.md` là file đặc tả (tài liệu mô tả chính thức) của một định dạng; gist là một đoạn ghi chú ngắn đăng trên GitHub Gist.
- `01`–`06` viết trước, chủ yếu từ blog/tin tức; nhãn **[blog]**, **[chưa kiểm]**, **[suy luận]** đánh dấu chỗ chưa chắc. Letta và A-Mem chưa đọc paper.
- Số benchmark của Zep/Mem0 mâu thuẫn giữa các bên chạy (`08` §4.4); không dùng làm bằng chứng xếp hạng.
- MCP và chính sách connector (kết nối để chatbot dùng dịch vụ bên ngoài, ví dụ một MCP server) Claude/ChatGPT đổi nhanh; kiểm tra tài liệu chính thức trước khi chốt (`05`).

## Liên hệ với tài liệu hiện có

- Thiết kế 4 lớp, schema (cấu trúc các trường dữ liệu) của VectorDB (cơ sở dữ liệu vector: lưu embedding, tức dãy số biểu diễn ý nghĩa của văn bản, và tìm theo độ giống nghĩa) và GraphDB (cơ sở dữ liệu đồ thị, ví dụ Neo4j): `docs/design/01_INITIAL_BASE_DESIGN.md`.
- Kiến trúc lai Vector + Graph, gọi là "Boomerang" (mẫu thiết kế: đồ thị chỉ giữ con trỏ, khi cần chi tiết thì quay về VectorDB lấy chunk gốc): `docs/research/timeline_summarization/03_Hybrid_Vector_Graph_RAG.md`.
- Hai bất biến của đồ án. Thứ nhất, Evolution ≠ Falsehood: Evolution (tiến hóa) là sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên lên giám đốc, xử lý bằng cách đóng `end_time` (thời điểm hết hiệu lực); Falsehood (sai lầm) là thông tin sai ngay từ đầu, ví dụ tin đồn bị đính chính, đánh dấu bằng `invalidated_at` (thời điểm bị coi là không hợp lệ). Thứ hai, Timeline ≠ Conflict: chuỗi sự kiện nối tiếp (lên chức) không phải là mâu thuẫn, chỉ có đính chính hoặc thay thế mới đóng sự kiện cũ. Xem `CLAUDE.md`, `docs/scope/01_PROJECT_SCOPE.md`; phạm vi Cơ chế 3: `docs/decisions/09_CONFLICT_RESOLUTION_SCOPE.md`.

## Tài liệu tham khảo (docs, git)

- **OKF:** [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (repo hiện hành, có `SPEC.md`); [GoogleCloudPlatform/knowledge-catalog/okf](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (bản đóng băng, không còn bảo trì)
- **LLM Wiki:** [Karpathy — LLM Wiki (gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- **Zep / Graphiti:** [Zep paper, arXiv 2501.13956](https://arxiv.org/abs/2501.13956); mã nguồn [getzep/graphiti](https://github.com/getzep/graphiti); [docs Zep — facts](https://help.getzep.com/v4/facts.md)
- **Mem0:** [Mem0 paper, arXiv 2504.19413](https://arxiv.org/abs/2504.19413); mã nguồn [mem0ai/mem0](https://github.com/mem0ai/mem0) (tên repo theo kết quả tìm kiếm, chưa mở)
- **Letta:** [letta-ai/letta](https://github.com/letta-ai/letta) (agent runtime, tức môi trường chạy agent; tiền thân là MemGPT; chưa mở repo)
- **MCP:** [Đặc tả MCP, changelog bản mới nhất](https://modelcontextprotocol.io/specification/latest/changelog); [Security Best Practices 2026-07-28](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices.md); [danh sách client](https://modelcontextprotocol.io/clients)
- **SDK server:** [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) (giấy phép MIT, cần Python 3.11+; hỗ trợ ba cách truyền tin giữa client và server: stdio là qua đầu vào/ra chuẩn của tiến trình, Streamable HTTP và SSE là qua HTTP); [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) (Apache-2.0, framework riêng, FastMCP 1.0 đã gộp vào SDK chính thức năm 2024)
- **Nền tảng và cổng:** [OpenAI — remote MCP](https://developers.openai.com/api/docs/guides/tools-connectors-mcp); [LiteLLM MCP Gateway](https://docs.litellm.ai/docs/mcp); [open-webui/mcpo](https://github.com/open-webui/mcpo)
- **Ontology / thời gian:** [Wikidata Help:Ranking](https://www.wikidata.org/wiki/Help:Ranking), [Help:Qualifiers](https://www.wikidata.org/wiki/Help:Qualifiers); [arXiv 2506.07853 (LRMoo, luật)](https://arxiv.org/abs/2506.07853); chi tiết ở [`14`](14_Ontology_and_Temporal_Representation.md) §10

Mỗi file có thêm mục nguồn riêng; mục này là mục lục tổng. Link đánh dấu *chưa mở* chỉ lấy từ kết quả tìm kiếm.
