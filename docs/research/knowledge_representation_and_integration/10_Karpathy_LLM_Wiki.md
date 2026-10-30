# LLM Wiki (Karpathy) — mẫu "idea file" về tri thức tích lũy

> **Nguồn:** gist [karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (đăng đầu tháng 04/2026 theo các bài viết thứ cấp), đã đọc qua WebFetch. Công cụ tóm tắt không trả nguyên văn, nên các tên lớp/thao tác dưới đây là **diễn giải đã kiểm tra** chứ không phải trích nguyên văn; chỉ các trích ngắn trong ngoặc kép là từ gist.
> Gist (một ghi chú ngắn đăng trên GitHub Gist) cố ý **trừu tượng**: là "idea file" (file ý tưởng) để người dùng dán cho một agent rồi để nó tự dựng phiên bản phù hợp, không phải công cụ hay đặc tả. Agent ở đây là chương trình dùng LLM (Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT, Gemini) để tự lập kế hoạch và gọi công cụ. Markdown là định dạng văn bản có tiêu đề, danh sách, liên kết viết bằng ký hiệu đơn giản. Wiki là tập các trang có liên kết chéo với nhau, như Wikipedia.

## 1. Ý tưởng cốt lõi

- Cách làm phổ biến là RAG (Retrieval-Augmented Generation, sinh câu trả lời có tăng cường truy xuất): mỗi lần có câu hỏi, hệ thống tìm vài đoạn liên quan trong file thô rồi đưa cho LLM đọc để trả lời. Gist đề xuất khác: một LLM **xây dựng và bảo trì dần một wiki markdown có liên kết** nằm giữa người dùng và nguồn. Nguồn mới được đọc, rút fact (mẩu thông tin), **hợp nhất vào trang hiện có**. Tri thức được "biên dịch" một lần và giữ cập nhật thay vì suy lại mỗi truy vấn.
- "the wiki is a persistent, compounding artifact" (wiki là một sản phẩm bền vững, càng dùng càng dày): liên kết chéo, mâu thuẫn được gắn cờ và phần tổng hợp tích lũy theo thời gian.
- Phân vai: con người chọn nguồn và đặt câu hỏi; LLM viết và bảo trì wiki. Phép ví von của tác giả: Obsidian (ứng dụng ghi chú dùng file markdown) là IDE (Integrated Development Environment, môi trường lập trình tích hợp, tức phần mềm để viết mã), LLM là lập trình viên, wiki là codebase (kho mã).
- Lý do hiệu quả: rào cản của wiki cá nhân là *công việc sổ sách* (cập nhật liên kết, giữ nhất quán), LLM làm việc đó gần như miễn phí. Tác giả liên hệ với Memex của Vannevar Bush (1945; ý tưởng "máy lưu trữ tri thức cá nhân có liên kết", tiền thân của siêu văn bản).

## 2. Ba lớp

| Lớp | Nội dung | Ai sở hữu |
|---|---|---|
| **Raw sources** | Bài báo, paper, ảnh, dữ liệu; **bất biến**, là nguồn chân lý | Con người chọn; LLM chỉ đọc |
| **Wiki** | Markdown do LLM sinh: tóm tắt, trang thực thể/khái niệm, so sánh, tổng quan, tổng hợp | LLM viết, người đọc |
| **Schema** | Tài liệu cấu hình (kiểu `CLAUDE.md`/`AGENTS.md`) quy định cấu trúc, quy ước, quy trình | Người và LLM cùng tiến hóa |

Giải thích nhanh: ở đây "schema" không phải lược đồ cơ sở dữ liệu mà là một file hướng dẫn bằng chữ, nói cho LLM biết wiki được tổ chức thế nào và phải làm việc theo quy trình nào (giống bản "nội quy" của wiki). `CLAUDE.md`/`AGENTS.md` là các file hướng dẫn mà công cụ lập trình bằng AI đọc trước khi làm việc. "Entity" (thực thể) là một đối tượng cụ thể như một người, một công ty, một sản phẩm.

## 3. Ba thao tác

- **Ingest** (nạp tài liệu vào hệ thống): thêm một nguồn → LLM đọc, trao đổi điểm chính với người dùng, viết trang tóm tắt, cập nhật `index` (mục lục), sửa các trang thực thể/khái niệm liên quan, ghi vào `log` (nhật ký). Một nguồn có thể chạm **10–15 trang**. Tác giả thích nạp từng nguồn một có giám sát.
- **Query** (hỏi đáp): LLM tìm trong wiki, đọc trang liên quan, trả lời có trích dẫn; câu trả lời hay có thể được lưu lại thành trang mới.
- **Lint** (kiểm tra định kỳ, mượn tên công cụ dò lỗi trong lập trình): dò **mâu thuẫn giữa các trang, claim (khẳng định) cũ đã bị nguồn mới thay thế, trang mồ côi (không có trang nào link tới), thiếu trang khái niệm, thiếu liên kết, khoảng trống dữ liệu**.

## 4. `index.md` và `log.md`

- `index.md`: danh mục theo nội dung, mỗi trang một link + tóm tắt một dòng (+ metadata như ngày, số nguồn); LLM cập nhật mỗi lần ingest và **đọc đầu tiên khi trả lời**.
- `log.md`: *chỉ ghi thêm* (không sửa dòng cũ), theo thứ tự thời gian, mỗi dòng có tiền tố nhất quán (ví dụ ngày) để lệnh `grep` (lệnh tìm dòng chứa một chuỗi trong file) đọc nhanh lịch sử gần đây.
- OKF (Open Knowledge Format, định dạng mở của Google Cloud để lưu tri thức thành thư mục file markdown, mỗi file có khối metadata YAML gọi là frontmatter ở đầu) v0.2 chính thức hóa đúng hai file này (xem `09`).

## 5. Quy mô và công cụ

- Cách dùng `index` hoạt động tạm ổn ở khoảng **~100 nguồn, vài trăm trang**, không cần hạ tầng embedding (embedding là vector số biểu diễn ý nghĩa của văn bản; hai văn bản gần nghĩa thì vector gần nhau, nhờ đó tìm theo nghĩa được). Vượt mức đó nên có công cụ tìm kiếm riêng.
- Công cụ nhắc tới:
  - **qmd**: công cụ tìm kiếm markdown chạy cục bộ. Nó kết hợp (hybrid) BM25 và tìm bằng vector. BM25 là thuật toán xếp hạng theo từ khóa, đếm mức trùng từ giữa câu hỏi và văn bản. Sau đó LLM re-rank (chấm lại thứ hạng các kết quả). qmd có CLI (Command-Line Interface, giao diện dòng lệnh) và một **MCP server**. MCP (Model Context Protocol) là giao thức chuẩn để ứng dụng AI gọi công cụ và dữ liệu của một server bên ngoài.
  - **Obsidian** kèm Web Clipper (tiện ích lưu trang web vào ghi chú), Dataview (truy vấn trên frontmatter, tức khối metadata YAML ở đầu file markdown) và graph view (xem các trang dưới dạng đồ thị liên kết).
  - **Marp** (tạo slide từ markdown) và **Git** (quản lý lịch sử thay đổi file).

## 6. Xử lý mâu thuẫn và claim cũ

- Khi nguồn mới mâu thuẫn nội dung có sẵn, LLM được kỳ vọng **ghi nhận mâu thuẫn và sửa/thách thức bản tổng hợp, không lặng lẽ ghi đè**.
- Lint nhắm riêng vào mâu thuẫn và claim bị thay thế. **Nhưng gist không đưa ra mô hình thời gian**: không có khoảng hiệu lực (khoảng thời gian một sự việc còn đúng), không phân biệt đổi theo thời gian với sai từ đầu; chỉ là việc LLM tự phán đoán khi sửa trang. Đây là điểm cốt yếu so với đồ án.

## 7. Phân biệt LLM wiki và RAG kiểu đồ án

Giải thích nhanh các từ trong bảng (đồ án là hệ thống time-aware RAG, tức RAG có xét thời gian, kết hợp Vector DB và đồ thị):
- **Chunk**: một đoạn văn bản được cắt ra từ tài liệu để lưu và tìm kiếm.
- **Triplet**: bộ ba (chủ thể, quan hệ, đối tượng), ví dụ (Ông A, bị bắt, 2024). Trong đồ án, triplet nhẹ nằm ở đồ thị và trỏ ngược về chunk gốc.
- **`end_time`**: ngày một sự việc hết đúng; "đóng `end_time`" là điền ngày đó khi có thông tin mới thay thế.
- **Boomerang**: mẫu thiết kế của đồ án, đồ thị chỉ giữ con trỏ `Chunk_ID`, khi cần chi tiết thì "quay về" VectorDB lấy chunk gốc.
- **Chặn rò rỉ tương lai**: hỏi về ngày D thì không được dùng thông tin chỉ xuất hiện sau ngày D.
- **Raw**: lớp nguồn thô ở §2. **git diff**: lệnh Git hiển thị chính xác dòng nào thay đổi.

| Tiêu chí | LLM wiki | RAG thuần | Đồ án (Vector+Graph, time-aware) |
|---|---|---|---|
| Khi nào xử lý tri thức | Lúc nạp (biên dịch) | Lúc hỏi (truy xuất) | Lúc nạp (trích fact, đóng `end_time`) **và** lúc hỏi (lọc, điểm thời gian) |
| Đơn vị | Trang markdown do LLM viết lại | Chunk của văn bản gốc | Chunk gốc + triplet nhẹ trỏ về chunk |
| Văn bản gốc | Bất biến ở lớp raw, nhưng wiki là bản **LLM diễn đạt lại** | Chính là văn bản gốc | Giữ nguyên chunk (Boomerang) |
| Rủi ro | LLM diễn đạt sai/trôi nghĩa khi gộp trang (**[suy luận]**) | Truy xuất nhầm bản cũ | Trích triplet sai; đồng bộ 2 kho |
| Thời gian | Do LLM tự suy | Không có | Mô hình tường minh + chặn rò rỉ tương lai |
| Quy mô | ~100 nguồn (theo gist) | Lớn | Lớn |
| Kiểm tra thủ công | Dễ (đọc file, git diff) | Khó | Trung bình |

**Rút ra:** LLM wiki tối ưu cho *tri thức cá nhân tích lũy ở quy mô nhỏ*; không thay thế được cơ chế lọc thời gian có bảo đảm. Nhưng **thao tác `lint`** (tìm claim đã bị thay thế, mâu thuẫn giữa trang) rất gần với nhiệm vụ của Cơ chế 3 và có thể là một *pass offline* định kỳ trên kho chunk: tìm cặp chunk có khả năng `SUPERSEDES` để người/LLM duyệt (**[suy luận]**).

## 8. Áp dụng vào đồ án

Đồ án có ba cơ chế: Cơ chế 1 là Temporal Retrieval (tìm theo mốc thời gian được hỏi), Cơ chế 2 là Timeline Summarization (tóm tắt dòng thời gian của một thực thể), Cơ chế 3 là Conflict Resolution (xử lý thông tin mâu thuẫn).

- **Cơ chế 1:** không dùng (wiki không có lọc cứng, tức loại hẳn kết quả không thỏa điều kiện thời gian). Có thể dùng `index.md` làm *lớp điều hướng* cho agent trước khi gọi tool `search` (hàm tìm kiếm mà agent được phép gọi).
- **Cơ chế 2:** trang thực thể do LLM duy trì ≈ timeline đã biên dịch sẵn (phương án D ở `03`). Ưu: rất ít token (token là đơn vị văn bản LLM xử lý và tính phí), đọc được. Nhược: trang là diễn đạt lại của LLM, cần giữ liên kết `Chunk_ID` (mã chunk gốc) hoặc `sources` (nguồn) về văn bản gốc để kiểm chứng.
- **Cơ chế 3:** `lint` là cơ chế gợi ý ứng viên mâu thuẫn; còn việc *quyết định* thay thế/sai từ đầu vẫn phải theo bất biến Evolution ≠ Falsehood. Evolution (tiến hóa) là sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên lên giám đốc; xử lý bằng cách đóng `end_time`. Falsehood là thông tin sai ngay từ đầu, ví dụ tin đồn bị đính chính; đánh dấu bằng `invalidated_at`.
- **Schema file:** `CLAUDE.md` của chính repo này là một ví dụ của "lớp schema".

## Tài liệu tham khảo (docs, git)

- **Gist gốc:** [Karpathy — LLM Wiki (gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- **Bài viết thứ cấp:** [Atlan — LLM wiki vs RAG](https://atlan.com/know/llm-wiki-vs-rag-knowledge-base/), [MindStudio](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison), [AI Builder Club](https://www.aibuilderclub.com/blog/karpathy-llm-wiki), [Implicator](https://implicator.ai/karpathys-llm-wiki-got-16-million-views-the-code-isnt-the-point-2/)
- **Định dạng chuẩn hóa từ mẫu này:** [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (repo hiện hành, có `SPEC.md`)
- **Công cụ nhắc trong gist:** [Obsidian](https://obsidian.md); qmd (công cụ tìm kiếm markdown cục bộ, chưa tìm được link gốc).
