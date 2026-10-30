# Open Knowledge Format (OKF) v0.2 — đặc tả chi tiết

> **Nguồn:** `SPEC.md` và README của repo [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (Apache-2.0), đã đọc trực tiếp (qua WebFetch, bản diễn giải có chú thích tên khóa gốc). Repo cũ `GoogleCloudPlatform/knowledge-catalog/tree/main/okf` chỉ còn là bản đóng băng, không còn bảo trì.
> **Đính chính cho `02`:** `02` mô tả v0.1 (ngày 12/06/2026). Bản hiện hành là **v0.2**, thêm cả một họ trường về nguồn gốc, độ tin cậy và vòng đời, **liên quan trực tiếp đến đồ án** hơn v0.1 rất nhiều.

## 1. Tổng quan

- **OKF (Open Knowledge Format, định dạng mở của Google Cloud)** là một quy ước để lưu tri thức thành một thư mục các file văn bản thường, thay vì nhét vào một cơ sở dữ liệu. Mỗi file mô tả một mẩu tri thức, ví dụ một bảng dữ liệu hay một chỉ số kinh doanh.
- **Mục đích:** biểu diễn tri thức (metadata là thông tin mô tả về dữ liệu, cùng ngữ cảnh và insight là nhận định đã được người hoặc máy biên tập) thành **file markdown kèm YAML frontmatter**. Markdown là định dạng văn bản có tiêu đề, danh sách, bảng viết bằng ký hiệu đơn giản như `#` và `-`. YAML là cách viết dữ liệu dạng `khóa: giá trị`. Frontmatter là khối YAML đặt ở đầu file, nằm giữa hai dòng `---`, chứa metadata của file đó.
- **Mục tiêu:** producer (bên tạo ra và ghi file) ghi được, consumer (bên đọc và dùng file, ví dụ một agent) đọc được, trao đổi được giữa các tổ chức, và *làm cho kho tri thức do agent bảo trì trở nên đáng tin*. Agent là chương trình dùng LLM (Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT, Gemini) để tự lập kế hoạch và gọi công cụ.
- **Phi mục tiêu:** không có taxonomy `type` cố định (taxonomy là bảng phân loại cha-con; ở đây nghĩa là OKF không quy định sẵn danh sách các loại `type`), không phải hạ tầng lưu trữ/truy vấn, không thay thế schema miền. Schema là bản mô tả cấu trúc dữ liệu phải tuân theo; Avro, Protobuf là hai định dạng schema cho dữ liệu nhị phân, còn OpenAPI là chuẩn mô tả API REST (giao diện gọi dịch vụ qua web) bằng JSON hoặc YAML.
- **Điểm mới v0.2:** provenance (nguồn gốc: thông tin này từ đâu ra), trust (độ tin cậy), lifecycle (vòng đời: nháp, hiện hành, hết hạn) và attestation (xác nhận rằng một phép tính đã chạy đúng, xem §6) trở thành các trường chính thức, gọi là "công dân hạng nhất".

## 2. Cấu trúc bundle và concept

- **Bundle** (gói) = một cây thư mục tự chứa mọi file tri thức, là đơn vị để phân phối (khuyến nghị đặt trong một git repo, tức kho mã có lưu lịch sử thay đổi).
- **Concept** (khái niệm) = một file `.md` mô tả một đơn vị tri thức; **Concept ID = đường dẫn file bỏ `.md`**. Ví dụ file `tables/orders.md` có Concept ID là `tables/orders`.
- Tên file dành riêng: `index.md` (mục lục thư mục), `log.md` (lịch sử cập nhật). Không dùng làm concept.
- Bundle gốc có thể khai báo `okf_version: "0.2"` trong frontmatter của `index.md` gốc. Consumer không nhận ra phiên bản thì **cố gắng đọc best-effort** (đọc phần hiểu được, bỏ qua phần không hiểu), không từ chối.
- **Bắt buộc duy nhất:** `type` (chuỗi ngắn nói concept thuộc loại gì, không đăng ký tập trung; consumer phải chấp nhận `type` lạ).
- Khuyến nghị: `title`, `description` (1 câu, tái dùng trong index), `resource` (URI chuẩn của tài sản; URI, Uniform Resource Identifier, là chuỗi định danh tài nguyên, ví dụ một URL), `tags` (nhãn).
- Thân: markdown thường, ưu tiên cấu trúc (heading là tiêu đề, bảng, list là danh sách) hơn văn xuôi; tiêu đề quy ước `# Schema`, `# Examples`, `# Computation`.
- **Thuộc tính mở rộng:** producer thêm khóa tùy ý; consumer **phải giữ nguyên khóa lạ khi round-trip** (tức đọc rồi ghi lại mà không làm mất khóa mình không hiểu), không được từ chối.

## 3. Họ trường provenance / trust / lifecycle (mới ở v0.2)

Tất cả là tùy chọn; vắng mặt có ý nghĩa nhưng **không bao giờ là lý do từ chối**. Mọi mốc thời gian theo ISO 8601 (chuẩn viết ngày giờ, ví dụ `2026-06-12T09:00:00+07:00`) có kèm offset UTC (độ lệch so với giờ chuẩn quốc tế, ví dụ `+07:00` là giờ Việt Nam).

| Khóa | Cấu trúc | Ngữ nghĩa |
|---|---|---|
| `sources` | list; mỗi mục: `resource` (**bắt buộc trong mục**), `id`, `title`, `author`, `usage_count`, `last_modified` | Nguồn mà concept dẫn xuất. `author` là tín hiệu thẩm quyền; `usage_count` (trong `usage_window {from,to}`) là tín hiệu dùng/sống-chết (đọc theo xu hướng, không xếp hạng); `last_modified` = lần nguồn đổi, khác `generated.at` |
| `generated` | `{by, at}` | `by` bắt buộc: actor viết nội dung hiện tại; `at`: lần đổi nội dung có ý nghĩa gần nhất |
| `verified` | list `{by, at}` (một mapping trần được coi là list 1 phần tử) | Các sự kiện xác minh độc lập; độc lập với `generated.at` |
| `status` | `draft` / `stable` (mặc định) / `deprecated` | `deprecated` = giữ cho link và lịch sử, **không còn hiện hành** |
| `stale_after` | datetime tuyệt đối | Concept "cũ" khi `now >= stale_after` (tuyệt đối để so sánh trơn, không phải TTL tương đối) |

**Giải thích nhanh các khóa trong bảng:**
- `sources`: danh sách nơi concept này lấy thông tin. Ví dụ một concept về chỉ số doanh thu có thể ghi nguồn là một bảng dữ liệu và người viết ra nó. `usage_count` là số lần nguồn được dùng trong một khoảng thời gian `usage_window` (từ ngày này đến ngày kia); nguồn càng ít dùng càng có thể đã "chết".
- `generated`: ai (hoặc cái gì) viết ra nội dung hiện tại và vào lúc nào. `by` là actor (bên thực hiện hành động, xem quy ước bên dưới).
- `verified`: các lần có người hoặc máy kiểm tra lại độc lập và xác nhận nội dung đúng.
- `deprecated`: concept cũ, vẫn giữ để link và lịch sử không bị hỏng, nhưng không nên dùng nữa.
- TTL (Time To Live, thời gian sống) là cách đặt hạn dùng kiểu "còn sống N giờ kể từ lúc lưu" thường gặp trong cache (bộ nhớ đệm); `stale_after` khác ở chỗ là một mốc ngày giờ cụ thể.

**Quy ước nguồn của hành động (actor):** `<producer>/<version>` cho agent/công cụ, `human:<id>` cho người, `process:<id>` cho tiến trình tự động.

**Trust tier (bậc tin cậy; suy ra, chỉ tư vấn, không phải kiểm soát truy cập, tức không dùng để quyết định ai được đọc hay ghi):**
- không có `verified` → *unverified*
- `verified` chỉ bởi actor không phải `human:` → *machine-confirmed*
- `verified` bởi ít nhất một `human:<id>` → *human-reviewed*

**Credibility** (độ đáng tin của một nguồn, ví dụ nguồn do chuyên gia viết và còn được cập nhật thì đáng tin hơn) do consumer *suy ra* từ `author`, `usage_count`, `last_modified`; **không bao giờ lưu thành điểm số**.

**Chú thích theo từng claim** (claim là một khẳng định cụ thể trong nội dung): dùng footnote markdown (chú thích cuối trang dạng `[^1]`) có nhãn trùng `sources[].id`, để đảo thứ tự các nguồn không làm sai chỗ trích dẫn.

## 4. Liên kết

- Link markdown chuẩn, dạng tuyệt đối theo bundle (bắt đầu bằng `/`, tính từ thư mục gốc của bundle; khuyến nghị) hoặc tương đối (tính từ vị trí file hiện tại).
- Một link **khẳng định một quan hệ không đặc tả**; ý nghĩa nằm trong văn xuôi xung quanh. **Không có kiểu cạnh.**
- Link hỏng phải được chấp nhận (có thể là tri thức chưa viết).
- Quy ước thư mục `references/` cho tài liệu ngoài, hướng dẫn chạy, mã.

## 5. `index.md` và `log.md`

- `index.md`: tùy chọn ở mọi thư mục; thường không có frontmatter (trừ gốc có `okf_version`); gồm các mục có tiêu đề với danh sách link + mô tả ngắn (tái dùng `description`); thư mục kết thúc bằng `/`. Phục vụ *tiết lộ dần* (progressive disclosure: đọc mục lục ngắn trước, chỉ mở file chi tiết khi cần, để đỡ tốn ngữ cảnh của LLM). Có thể sinh tự động; consumer có thể tự tổng hợp nếu thiếu.
- `log.md`: danh sách phẳng theo ngày (`YYYY-MM-DD`, ví dụ `2026-06-12`), **mới nhất trước**, mục là văn xuôi, nhãn đậm quy ước `**Update**`, `**Creation**`, `**Deprecation**`.

## 6. Attested Computation (tóm tắt)

Concept `type: Attested Computation` định nghĩa *cách tính được phép* cho một giá trị (ví dụ cách tính "doanh thu tháng"), gồm các khóa `runtime` (môi trường chạy), `parameters` (tham số), `computation` (phép tính), `executor` (bên chạy), `attester` (bên xác nhận). Agent chỉ cung cấp giá trị tham số, không được viết lại phép tính. Một *attester* tất định (luôn cho cùng kết quả với cùng đầu vào, không dùng LLM) kiểm tra biên nhận (receipt: bản ghi cho thấy phép tính đã chạy đúng định nghĩa). Cho thấy hai khái niệm khác nhau: **`verified`** (xác nhận định nghĩa ở cấp tài liệu, lưu trong bundle) và **attestation** (xác nhận từng lần chạy, *không lưu*). Phần này hướng đến số liệu doanh nghiệp (viết bằng SQL là ngôn ngữ truy vấn bảng dữ liệu, dbt là công cụ biến đổi dữ liệu bằng SQL, Looker là công cụ báo cáo) nên **ít liên quan** đồ án; ghi nhận để biết OKF đi theo hướng "tri thức có thể kiểm chứng".

## 7. Conformance và tương thích

- Conformance là mức tuân thủ spec. Bundle hợp lệ: mọi `.md` không dành riêng có frontmatter đọc được; mọi frontmatter có `type` không rỗng; file dành riêng theo §5.
- Consumer **không được từ chối** vì thiếu khóa tùy chọn, `type` lạ, khóa lạ, link hỏng hay thiếu `index.md`.
- Phiên bản `<major>.<minor>`: minor = thêm tương thích ngược; major = có thể phá khóa bắt buộc/tên file dành riêng.
- **Thay đổi v0.1 → v0.2:** `timestamp` bị thay bằng `generated.at` (consumer có thể fallback về `timestamp`); danh sách `# Citations` trong thân bị thay bằng `sources`.
- **Trì hoãn sang bản sau:** giao thức runtime (lúc chạy) đầy đủ cho receipt (biên nhận) và verdict (kết luận đúng/sai), ABI của attester (quy ước giao tiếp giữa attester và chương trình gọi nó), tính di động và sandbox (môi trường chạy cô lập, an toàn), cache attestation (lưu tạm kết quả xác nhận).
- Lưu ý bảo mật duy nhất của spec: trust tier và `verified` **không phải kiểm soát truy cập**.

## 8. Reference tooling

Repo có agent tham chiếu chạy 2 lượt. Lượt BigQuery (BigQuery là kho dữ liệu phân tích của Google Cloud) sinh một doc cho mỗi concept từ metadata. Lượt web: LLM lấy URL khởi đầu (seed) qua tool `fetch_url` (tool là hàm mà LLM được phép gọi), tự quyết định theo link nào, rồi làm giàu doc hoặc tạo `references/<slug>` (slug là tên ngắn viết liền dùng làm tên file); lượt này có giới hạn số trang và lọc host (chỉ cho phép một số tên miền). Có trình hiển thị HTML tĩnh (dùng thư viện Cytoscape.js) với đồ thị lực (các nút tự dàn ra như lò xo), backlink "Cited by" (danh sách các trang đang trích dẫn trang này), tìm kiếm, lọc theo type. Bundle mẫu: `ga4`, `stackoverflow`, `crypto_bitcoin`, `acme_retail`.

## 9. OKF v0.2 trả lời gì cho đồ án, và còn thiếu gì

### 9.1 Đối chiếu với các bất biến

Bất biến là các quy tắc lõi của đồ án mà mọi thiết kế phải giữ. Các thuật ngữ riêng của đồ án dùng trong bảng:
- `start_time`/`end_time`: ngày sự việc bắt đầu và hết đúng ngoài đời (ví dụ ông A làm giám đốc từ 2005 đến 2007). `end_time` để trống nghĩa là chưa biết hoặc còn hiệu lực.
- **Evolution** (tiến hóa): sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên được lên giám đốc. Xử lý bằng cách đóng `end_time` của trạng thái cũ; trạng thái cũ vẫn được trả về khi hỏi về quá khứ.
- **Falsehood** (sai từ đầu): thông tin chưa bao giờ đúng, ví dụ tin đồn bị đính chính. Đánh dấu bằng `invalidated_at` (thời điểm bị coi là không hợp lệ); loại khỏi kết quả truy xuất, và nếu hỏi lịch sử thì kèm cảnh báo.
- `SUPERSEDES`/`CORRECTS`: cạnh nối hai mẩu tri thức, nghĩa là "bản mới thay thế bản cũ" và "bản mới sửa lỗi của bản cũ".
- **Cơ chế 1/2/3**: ba cơ chế của đồ án: Temporal Retrieval (tìm theo mốc thời gian), Timeline Summarization (tóm tắt dòng thời gian của một thực thể), Conflict Resolution (xử lý thông tin mâu thuẫn).
- "Chặn rò rỉ tương lai": khi người dùng hỏi về ngày D, hệ thống không được dùng thông tin chỉ xuất hiện sau ngày D.

| Nhu cầu / bất biến | OKF v0.2 | Đánh giá |
|---|---|---|
| Thời gian hiệu lực `start_time`/`end_time` | **Không có.** Chỉ có `generated.at` (lúc *ghi nội dung*), `sources[].last_modified`, `stale_after` | Thiếu → tự thêm khóa mở rộng. Nhớ: `generated.at` là thời gian ghi tri thức, **không phải** thời gian hiệu lực của sự kiện |
| Evolution (đóng `end_time`) | `status: deprecated` = "không còn hiện hành, giữ cho lịch sử" | **Khớp ý** nhưng thô: không biết *từ khi nào* hết hiệu lực |
| Falsehood (`invalidated_at`, sai từ đầu) | **Không phân biệt** với deprecated | Thiếu. Cần khóa mở rộng, hoặc giá trị `status` riêng (không phải chuẩn) |
| Quan hệ có kiểu `SUPERSEDES`/`CORRECTS` | Link không kiểu; nghĩa nằm trong văn xuôi | Thiếu → đặt `supersedes`/`corrects` trong frontmatter (khóa mở rộng hợp lệ) |
| Nhiều nguồn mâu thuẫn, credibility | `sources[]` với `author`, `usage_count`, `last_modified`; credibility *suy ra, không lưu điểm* | **Gần ý nhất** với Cơ chế 3 đa nguồn, tức trường hợp nhiều nguồn nói khác nhau và phải cân độ tin cậy giữa chúng (hiện ngoài phạm vi thực hiện; có thể dùng làm *thiết kế/định hướng* trong phần hạn chế) |
| Dấu hiệu "cũ" | `stale_after` tuyệt đối | Tương tự `end_time` suy đoán; xem §9.2 |
| Chặn rò rỉ tương lai | Không có khái niệm | Phải do bộ máy truy xuất bảo đảm (lớp khác) |
| Lịch sử thay đổi | `log.md` (văn xuôi) | Không truy vấn có cấu trúc "tại ngày D" được |

### 9.2 Hai liên hệ đáng chú ý **[suy luận]**

1. **`stale_after` ↔ ba trạng thái `end_time` của tuần 5.** Thiết kế có `ongoing` (đang hiệu lực) và `unknown` (không rõ ngày kết thúc), và các chế độ `open`/`decay`/`unknown_decay` để chấm điểm: chế độ quyết định một sự việc chưa có `end_time` được tính điểm thời gian thế nào (giữ nguyên điểm, hay giảm dần theo thời gian vì có thể đã hết hạn mà chưa ai ghi). `stale_after` là một *hạn dùng do producer khẳng định*, có thể làm đầu vào cho chế độ `open_decay` (giảm dần điểm cho sự việc đang mở) thay vì một hằng số chung. Cần thử nghiệm mới biết có lợi hay không.
2. **`sources` + tín hiệu credibility suy ra, không lưu điểm** là nguyên tắc rất hợp với Cơ chế 3: chấm điểm tin cậy lúc truy vấn từ các tín hiệu thô để đổi chính sách không cần ingest (nạp lại toàn bộ tài liệu vào hệ thống) lại. Chỉ là hướng thiết kế vì Cơ chế 3 đa nguồn nằm ngoài phạm vi thực hiện.

### 9.3 Điểm cần cẩn trọng

- **Kiểu quan hệ không có chuẩn**: nếu dùng `supersedes` trong frontmatter, các consumer OKF khác sẽ bỏ qua (nhưng không hỏng, vì phải giữ khóa lạ).
- `generated.at` bị đọc nhầm thành "thời gian sự kiện" là lỗi dễ mắc; cần đặt tên khóa riêng (`valid_from`/`valid_to`/`ingested_at`, tức "hiệu lực từ", "hiệu lực đến", "ngày hệ thống nạp") và ghi rõ trong profile (bản quy ước riêng của đồ án về những khóa nào được thêm và có nghĩa gì).
- Spec chưa nói gì về *truy vấn*; OKF là định dạng, không phải bộ máy tìm kiếm.
- Là định dạng còn rất mới (v0.1 ngày 12/06/2026, v0.2 sau đó); mức chấp nhận ngoài hệ sinh thái Google chưa biết.

## Tài liệu tham khảo (docs, git)

- **Đặc tả và mã:** [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (repo hiện hành, có `SPEC.md`)
- **Bản cũ (v0.1, đóng băng):** [GoogleCloudPlatform/knowledge-catalog/okf](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (bản đóng băng, không còn bảo trì)
- **Thông báo:** [Google Cloud blog — How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing); [The Decoder](https://the-decoder.com/google-clouds-open-knowledge-format-turns-scattered-docs-into-markdown-files-for-ai-agents/)
- **Chuẩn nền liên quan:** [Wikidata Help:Ranking](https://www.wikidata.org/wiki/Help:Ranking) (so sánh với `status`/`stale_after`), PROV-O trong [`14`](14_Ontology_and_Temporal_Representation.md) §4.2 (so sánh với `sources`/`generated`)

Spec đọc qua WebFetch (bản diễn giải của công cụ), không phải văn bản thô; tên khóa và giá trị enum đáng tin hơn câu chữ.
