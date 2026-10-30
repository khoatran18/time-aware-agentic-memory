# Áp dụng cho đồ án: đề xuất và câu hỏi mở

> Tổng hợp các file `01`–`05` (cùng thư mục) thành khuyến nghị. Mọi đề xuất ở đây là **[suy luận]** (nhóm nghiên cứu tự suy ra, chưa có nguồn xác nhận trực tiếp), cần quyết định trước khi sửa `docs/design/`.

## 1. Khuyến nghị theo mức ưu tiên

Bốn từ nền dùng trong bảng: **LLM** (Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT, Gemini); **agent** (chương trình dùng LLM để tự lập kế hoạch rồi gọi công cụ); **tool** (công cụ, thực chất là một hàm có tên và tham số mà LLM được phép yêu cầu chạy, ví dụ hàm tra cứu); **MCP** (Model Context Protocol, giao thức chuẩn để ứng dụng AI gọi công cụ và dữ liệu của một server bên ngoài; giải thích bằng ví dụ ở `05` §1).

| # | Khuyến nghị | Lý do | Tác động lên thiết kế |
|---|---|---|---|
| 1 | **Thêm một lớp "Serving" bằng MCP server chỉ đọc** phía trên pipeline hiện có (5 tool ở `05` §5) | Chi phí thấp, tái dùng code retrieval; cho phép demo với Claude Code / Claude / ChatGPT; thể hiện "agentic memory" thật | Thêm lớp 5 hoặc mở rộng lớp Generation; không đổi 3 cơ chế |
| 2 | **Giữ kiến trúc Vector + Graph (Boomerang)** nhưng ghi rõ phương án C (Postgres/bảng quan hệ) như phương án dự phòng/so sánh | Bằng chứng cho thấy graph không cần cho Cơ chế 1 và chỉ cần "một phần" cho Cơ chế 2 (`03`) | Cập nhật phần lựa chọn GraphDB; nêu lý do chọn Neo4j hay không |
| 3 | **Định nghĩa một "OKF profile" cho tri thức time-aware** làm định dạng xuất/nhập | OKF tối thiểu nhưng mở rộng được; giúp con người kiểm tra và agent khác dùng | Xem §2 |
| 4 | **Thêm `ingested_at` (thời gian hệ thống biết)** vào schema | Cần để đo Temporal Freshness và trả lời "hệ thống biết gì tại ngày D" (`04`) | Sửa schema ở `01_INITIAL_BASE_DESIGN.md`; **không** thêm vào danh sách 4 trường được index trừ khi có lý do |
| 5 | **Không chuyển hẳn sang LLM wiki** | Wiki không đảm bảo chặn rò rỉ tương lai và không có lọc cứng; cập nhật liên tục | Chỉ dùng wiki/OKF làm lớp biểu diễn |

Giải thích nhanh các từ trong bảng:

- **Serving** (lớp phục vụ): lớp đứng phía trên cùng, phơi chức năng tra cứu ra cho bên ngoài dùng. **Pipeline** là chuỗi bước xử lý nối tiếp (nạp tài liệu, lưu, truy xuất, sinh câu trả lời). **Agentic memory** là bộ nhớ dài hạn mà agent tự tra cứu (và có thể ghi) qua tool. **Claude Code** là công cụ lập trình của Anthropic chạy trong terminal.
- **Vector + Graph (Boomerang)**: dữ liệu nằm ở hai nơi. **Vector database** lưu đoạn văn dưới dạng dãy số để tìm theo ý nghĩa; **GraphDB** (cơ sở dữ liệu đồ thị, ví dụ **Neo4j**) lưu thực thể và quan hệ giữa chúng. **Boomerang** nghĩa là nút đồ thị chỉ giữ thông tin gọn kèm con trỏ `Chunk_ID` quay về cơ sở dữ liệu vector để lấy văn bản gốc khi cần. **Phương án C** (mô tả ở `03`) là thay graph database bằng bảng quan hệ trong **Postgres** (hệ quản trị cơ sở dữ liệu lưu dạng bảng, hàng, cột). **Cơ chế 1/2** lần lượt là Temporal Retrieval (truy xuất theo mốc thời gian) và Timeline Summarization (tóm tắt dòng thời gian).
- **OKF** (Open Knowledge Format, định dạng mở lưu tri thức thành thư mục file markdown, mỗi file có khối YAML ở đầu ghi metadata); **profile** là bản tùy biến của một định dạng chung cho riêng bài toán (thêm vài trường quy ước).
- **Schema** là bản khai báo cấu trúc dữ liệu (có những trường nào, kiểu gì). **Index** (chỉ mục) là cấu trúc phụ giúp lọc nhanh theo một trường; đồ án cố ý chỉ index 4 trường (`start_time`, `invalidated_at`, `domain_features.domain`, `domain_features.country`). **`ingested_at`** là lúc hệ thống nạp thông tin, khác với lúc sự việc xảy ra.
- **Temporal Freshness** (độ tươi mới theo thời gian): hệ thống cập nhật tri thức mới nhanh và đúng đến mức nào.
- **LLM wiki**: cách lưu tri thức thành các trang wiki do LLM tự viết và cập nhật. **Rò rỉ tương lai** (future leakage) là trả về thông tin xảy ra sau mốc thời gian được hỏi. **Lọc cứng** (hard filter) là loại hẳn kết quả không thỏa điều kiện, chứ không chỉ hạ điểm.

## 2. OKF profile đề xuất (nháp)

Mỗi **chunk** (một đoạn văn bản được cắt ra để lưu và tìm kiếm) hay điều khoản = một file markdown. Đầu file có **frontmatter** (khối YAML, tức danh sách dòng `khóa: giá trị`, ghi metadata). Dưới đây là các trường thêm lên trên trường `type` bắt buộc của OKF:

```markdown
---
type: LegalClause
title: Điều 12 – Chiều cao công trình, phố X
description: Quy định số tầng tối đa
resource: https://...             # nguồn gốc
tags: [xay-dung]
# --- khóa chuẩn OKF v0.2 ---
status: stable                    # stable | draft | deprecated (deprecated KHÔNG phân biệt hết hạn/sai)
generated: { by: pipeline/ingest-v1, at: 2026-10-30T09:00:00+00:00 }  # lúc GHI nội dung, không phải thời gian hiệu lực
sources:
  - { id: s1, resource: https://..., last_modified: 2024-03-01T00:00:00+00:00 }
# --- mở rộng time-aware (khóa tự đặt, hợp lệ theo spec) ---
start_time: 2024-03-01
end_time: null                    # null = còn hiệu lực
invalidated_at: null              # chỉ đặt khi sai từ đầu
ingested_at: 2026-10-30T09:00:00Z # thời gian hệ thống biết (đề xuất)
chunk_id: c_8f3a
content_hash: sha256:...
supersedes: [/clauses/2020/dieu-12.md]   # kiểu cạnh nằm trong frontmatter, không chỉ link trơn
---
Nội dung điều khoản...
```

Giải thích nhanh các trường: `start_time`/`end_time` là khoảng hiệu lực của thông tin (`end_time` null là còn hiệu lực); `invalidated_at` chỉ đặt khi thông tin sai ngay từ đầu (khác với hết hiệu lực); `generated.at` là lúc pipeline ghi file; `sources` là nguồn gốc; `chunk_id` là mã đoạn văn bản; `content_hash` là mã băm (dấu vân tay) của nội dung, hai đoạn trùng nội dung thì có cùng mã nên không cần nạp lại; `supersedes` là cạnh "bản này thay thế bản cũ" trỏ tới file cũ; `status` là trạng thái của file.

Lưu ý: `timestamp` của OKF v0.1 đã bị thay bằng `generated.at` ở v0.2 (`09` §7). `generated.at` là lúc ghi nội dung, tuyệt đối không dùng làm `start_time`. Tổng hợp phân biệt và đề xuất schema đầy đủ ở [`11`](11_Synthesis_and_Comparison.md) §5.

Điểm cần quyết định: kiểu cạnh (loại quan hệ giữa hai chunk, như `supersedes`) để trong frontmatter (máy đọc dễ) hay trong thân file dưới các mục tiêu đề quy ước (người đọc dễ). **Đề xuất: frontmatter.**

## 3. Ánh xạ bất biến của đồ án sang các lớp mới

| Bất biến | Phải được bảo đảm ở đâu |
|---|---|
| Evolution ≠ Falsehood | Schema (`end_time` vs `invalidated_at`) và cả output của tool `get_state_at`: hiện cờ `invalidated` |
| Timeline ≠ Conflict | Quan hệ `next_event` khác `supersedes`; trong OKF profile là hai trường khác nhau |
| No future leakage | **Phía server MCP**, không để agent tự lọc |
| Relative time → `T_now` | Server resolve, hoặc agent truyền `as_of` tuyệt đối; tuyệt đối không dùng giờ của client |
| Chỉ index 4 trường | Nếu thêm `entity_id` để làm Timeline trong Qdrant (phương án vector-only), phải mở lại quyết định này |
| Doc không có timestamp không vào store | Giữ nguyên ở Ingestion; `ingested_at` không thay thế được thời gian sự kiện |

Giải thích nhanh các dòng trong bảng:

- **Evolution** (tiến hóa): sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên lên giám đốc; xử lý bằng cách đóng `end_time` (vẫn trả về khi hỏi quá khứ). **Falsehood** (sai từ đầu): thông tin chưa bao giờ đúng, ví dụ tin đồn bị đính chính; đánh dấu bằng `invalidated_at` (bị lọc khỏi truy xuất thông thường, và khi trả lời chuyện quá khứ thì kèm cảnh báo). Vì thế tool `get_state_at` ("trạng thái tại một mốc") phải hiện cờ `invalidated` để agent biết.
- **Timeline ≠ Conflict**: `next_event` nối các sự kiện nối tiếp của cùng một đối tượng (nhân viên rồi giám đốc) và không đóng `end_time` của sự kiện trước; `supersedes` mới là "bản mới thay bản cũ" khi có đính chính, và đóng bản cũ.
- **No future leakage**: không trả về thông tin xảy ra sau mốc được hỏi (`as_of`); phải chặn ở **server MCP** (chương trình đứng giữa), không nhờ agent tự lọc. **Relative time**: thời gian tương đối như "tuần trước", "hiện nay"; `T_now` là ngày giờ hiện tại theo đồng hồ của server, dùng để đổi sang ngày tuyệt đối. **`as_of`** là "tính đến ngày".
- **Chỉ index 4 trường**: xem giải thích **index** ở trên; `entity_id` là mã của thực thể (người, công ty...) mà dòng thời gian bám vào. **Vector-only** là phương án chỉ dùng cơ sở dữ liệu vector (ở đây là **Qdrant**, một cơ sở dữ liệu vector mã nguồn mở), không dùng graph.
- **Ingestion**: giai đoạn nạp tài liệu vào hệ thống (cắt chunk, gắn mốc thời gian, lưu); tài liệu không khôi phục được mốc thời gian nào thì không vào kho time-aware.

## 4. Kế hoạch thực nghiệm nhỏ (nếu được duyệt)

1. Dựng MCP server (Python) bọc retrieval hiện có với `search` + `fetch` (tương thích ChatGPT) rồi `get_state_at`.
2. Cho Claude Code gọi server cục bộ (stdio: server chạy như chương trình con trên cùng máy; hoặc HTTP: server chạy như dịch vụ web) trên tập test của tuần 5 (xem báo cáo tuần 5); đo xem agent có truyền đúng `as_of` không, có bị rò rỉ tương lai không.
3. So sánh 3 cấu hình trả lời: (i) agent đọc thẳng bundle OKF (thư mục các file OKF, không qua server), (ii) MCP + Temporal Retrieval, (iii) Plain RAG qua MCP. **RAG** là Retrieval-Augmented Generation (tìm đoạn tài liệu liên quan rồi đưa cho LLM đọc để trả lời); **Plain RAG** là bản thuần, chỉ tìm theo độ giống nghĩa và không kiểm soát thời gian. Chỉ số: **EM** (Exact Match, tỉ lệ đáp án khớp hoàn toàn với đáp án chuẩn), **F1** (điểm cân bằng giữa độ chính xác và độ phủ khi so đáp án), `leakage_rate` (tỉ lệ kết quả trả về chứa thông tin sau mốc thời gian được hỏi), và số **token** (đơn vị đếm chữ của LLM, phản ánh chi phí).
4. (Tùy chọn) Dựng phương án C trên Postgres (xem §1) để so với Neo4j về độ phức tạp, thời gian truy vấn timeline và token.

## 5. Câu hỏi mở

- Phạm vi: mảng này là **đóng góp chính** hay **phụ lục/khả năng triển khai**? (Tài liệu phạm vi `docs/scope` hiện tập trung 3 cơ chế.)
- Có cần chạy được từ Claude.ai/ChatGPT (cần đặt server công khai trên Internet qua HTTPS, tức kết nối có mã hóa, và có xác thực) hay chỉ cần demo qua Claude Code / agent tự viết?
- OKF còn rất mới (v0.1 ra tháng 06/2026, nay đã là v0.2), chưa rõ mức chấp nhận; nên coi là "tham khảo định dạng" hơn là phụ thuộc.
- Quyền và tính năng connector (kết nối để chatbot dùng dịch vụ bên ngoài, ví dụ một MCP server) của ChatGPT cần kiểm tra lại trên tài liệu chính thức của OpenAI.
- Cần đọc spec OKF (đặc tả, tài liệu quy định chính thức) và gist Karpathy (ghi chú ngắn đăng trên GitHub của Andrej Karpathy, liên quan ý tưởng LLM wiki) trực tiếp, cùng paper Zep/Mem0 (hai hệ thống bộ nhớ dài hạn cho agent), trước khi trích dẫn trong báo cáo/luận văn.

## 6. Việc tiếp theo gợi ý

- [ ] Đọc spec OKF trên GitHub và gist gốc của Karpathy.
- [ ] Đọc paper Zep (temporal KG (Knowledge Graph, đồ thị tri thức: nút là thực thể, cạnh là quan hệ giữa chúng)) và Mem0, viết thành note riêng bằng `research-note`.
- [ ] Thử một MCP server nhỏ với `search` + `fetch`.
- [ ] Quyết định phạm vi (§5) rồi mới cập nhật `docs/design/`.

## Tài liệu tham khảo (docs, git)

- OKF v0.2: [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (repo hiện hành, có `SPEC.md`); chi tiết ở [`09`](09_OKF_v0.2_Spec.md)
- Ghi chú chung cho mục tham khảo: **repo** là kho mã nguồn trên GitHub; **MIT** và **Apache-2.0** là giấy phép mã nguồn mở cho phép dùng tự do; **SDK** là bộ thư viện lập trình sẵn; **arXiv** là kho bài báo khoa học đăng trước khi phản biện; **stdio**, **Streamable HTTP**, **SSE** là các cách truyền tin giữa client và server MCP (xem `05` §1).
- MCP và SDK: [Đặc tả MCP, changelog bản mới nhất](https://modelcontextprotocol.io/specification/latest/changelog); [Security Best Practices 2026-07-28](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices.md); [danh sách client](https://modelcontextprotocol.io/clients); [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) (MIT, Python 3.11+; stdio, Streamable HTTP, SSE); [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) (Apache-2.0, framework riêng, FastMCP 1.0 đã gộp vào SDK chính thức năm 2024)
- Triển khai đa LLM: [OpenAI — remote MCP](https://developers.openai.com/api/docs/guides/tools-connectors-mcp); [LiteLLM MCP Gateway](https://docs.litellm.ai/docs/mcp); [open-webui/mcpo](https://github.com/open-webui/mcpo); chi tiết ở [`12`](12_Chatbot_vs_MCP_Server_Multi_LLM.md)
- Ontology (bản mô tả có hệ thống các loại thực thể và quan hệ trong một lĩnh vực) / thời gian: [Wikidata Help:Ranking](https://www.wikidata.org/wiki/Help:Ranking), [Help:Qualifiers](https://www.wikidata.org/wiki/Help:Qualifiers); [arXiv 2506.07853 (LRMoo, luật)](https://arxiv.org/abs/2506.07853); chi tiết ở [`14`](14_Ontology_and_Temporal_Representation.md)
- Zep / Mem0: [Zep paper, arXiv 2501.13956](https://arxiv.org/abs/2501.13956); mã nguồn [getzep/graphiti](https://github.com/getzep/graphiti); [docs Zep — facts](https://help.getzep.com/v4/facts.md); [Mem0 paper, arXiv 2504.19413](https://arxiv.org/abs/2504.19413); mã nguồn [mem0ai/mem0](https://github.com/mem0ai/mem0) (tên repo theo kết quả tìm kiếm, chưa mở)
