# Ontology và cách biểu diễn thời gian trong tri thức có cấu trúc

> **Vì sao có file này:** `01` chỉ liệt kê ontology như một đầu của phổ biểu diễn rồi bỏ qua, trong khi ontology là phần nền của mọi cách mô hình hóa "sự việc đúng trong khoảng thời gian nào". File này đi sâu: ontology là gì và khác các thứ gần giống ra sao, người ta biểu diễn thời gian bằng những cách nào, các chuẩn nào có thể mượn, và đồ án nên dùng đến mức nào.
> **Độ tin cậy:** đã mở trực tiếp **Wikidata Help:Ranking**, **Wikidata Help:Qualifiers**, trang **arXiv 2506.07853**. **Không mở được** trang W3C (OWL-Time, PROV-O trả về lỗi 403), nên phần OWL-Time và PROV-O dựa trên **kết quả tìm kiếm** và đánh dấu **[thứ cấp]**. Chỗ ghi **[kiến thức chung]** là kiến thức nền chưa kiểm lại bằng nguồn trong phiên này. **[suy luận]** là phân tích của nhóm.

## Giải thích nhanh các từ nền và thuật ngữ của đồ án

Phần này giải thích trước các từ sẽ xuất hiện sớm, để đọc các mục sau không bị vấp. Các chuẩn kỹ thuật (RDF, OWL, SHACL...) được giải thích kỹ hơn ngay tại §1 và §2.

**Từ nền**
- **W3C** (World Wide Web Consortium): tổ chức đặt chuẩn cho web. **Wikidata**: cơ sở tri thức mở do cộng đồng Wikimedia biên tập, lưu thông tin dạng "thực thể - thuộc tính - giá trị". **Wikibase**: phần mềm chạy Wikidata.
- **Thực thể (entity)**: một đối tượng cụ thể như một người, một công ty, một điều luật. **Quan hệ (relation)**: mối liên hệ giữa hai thực thể, ví dụ "làm giám đốc của". **Ràng buộc (constraint)**: điều kiện dữ liệu phải thỏa, ví dụ "ngày kết thúc không được trước ngày bắt đầu".
- **Triplet / bộ ba**: một câu tri thức gồm chủ thể - quan hệ - đối tượng. Ví dụ: "Ông A - làm giám đốc - Công ty X".
- **LLM** (Large Language Model, mô hình ngôn ngữ lớn như Claude, GPT): mô hình AI đọc và viết văn bản. **RAG** (Retrieval-Augmented Generation): kỹ thuật tìm các đoạn văn bản liên quan rồi đưa cho LLM đọc để trả lời. **Chunk**: một đoạn văn bản được cắt ra để lưu và tìm kiếm.
- **Zep / Graphiti** và **Mem0**: các hệ thống trí nhớ cho agent (chương trình dùng LLM để tự lập kế hoạch và gọi công cụ); xem `07`, `08`. **OKF** (Open Knowledge Format): định dạng mở của Google Cloud lưu tri thức thành thư mục file markdown, mỗi file có khối metadata YAML ở đầu (frontmatter); xem `09`.
- **Neo4j**: cơ sở dữ liệu đồ thị phổ biến, dự kiến dùng cho đồ án. **Cơ sở tri thức / KG** (Knowledge Graph, đồ thị tri thức): tập dữ liệu thật dạng nút (thực thể) và cạnh (quan hệ).

**Thuật ngữ thời gian và riêng của đồ án**
- **`start_time` / `end_time`**: ngày một sự việc bắt đầu và hết đúng ngoài đời (ví dụ A làm giám đốc từ 2005 đến 2007). `end_time` trống nghĩa là chưa biết hoặc còn hiệu lực. **Valid time** (thời gian hiệu lực) là loại thời gian này. Loại khác là thời gian hệ thống biết thông tin, lưu ở `ingested_at` (lúc hệ thống nạp thông tin vào).
- **Evolution** (tiến hóa): sự việc từng đúng rồi thay đổi, ví dụ nhân viên lên giám đốc; xử lý bằng cách đóng `end_time`, vẫn trả về khi hỏi về quá khứ. **Falsehood** (sai từ đầu): thông tin chưa từng đúng, ví dụ tin đồn bị đính chính; đánh dấu bằng `invalidated_at`, bị loại khỏi truy xuất thông thường. Bất biến lõi của đồ án là **Evolution khác Falsehood**.
- **Cơ chế 1 / 2 / 3** của đồ án: Temporal Retrieval (tìm theo mốc thời gian được hỏi), Timeline Summarization (tóm tắt dòng thời gian của một thực thể), Conflict Resolution (xử lý thông tin mâu thuẫn).
- **`T_req`**: mốc thời gian mà câu hỏi nhắm tới. **Case 1**: `T_req` nằm trong khoảng `[start_time, end_time]` của một fact, nên fact khớp hoàn toàn.
- **`SUPERSEDES` / `CORRECTS` / `SUSPECTS` / `TIẾP_THEO`**: các loại cạnh của đồ thị trong đồ án. Lần lượt nghĩa là "thay thế bản cũ", "sửa lỗi bản cũ", "bị nghi ngờ" (cáo buộc, chưa phải sự thật, ví dụ cơ quan chức năng nghi ông A) và "kế tiếp" (chặng sự nghiệp sau của cùng một người).
- **`ongoing` / `unknown`**: hai giá trị mà thiết kế tuần 5 dùng cho `end_time` trống, nghĩa là "đang còn hiệu lực" và "không rõ ngày kết thúc".
- **`Chunk_ID`**: mã của chunk gốc; đồ thị lưu mã này để quay về lấy văn bản gốc. **Structural chunking**: cắt chunk theo cấu trúc tài liệu, ví dụ theo từng điều/khoản của văn bản luật.

## 1. Phân biệt các khái niệm hay bị trộn

"Ontology" (bản thể luận) là một đặc tả hình thức về các loại thực thể, quan hệ giữa chúng và ràng buộc/luật suy diễn trong một miền. Hiểu đơn giản, ontology là "bản thiết kế" nói miền này có những loại đối tượng nào, chúng được nối với nhau bằng những quan hệ nào, và từ đó máy có thể suy ra điều mới. Ví dụ: ontology khai báo "Giám đốc là một loại Nhân viên", nên khi biết "Ông A là Giám đốc", máy tự suy ra "Ông A là Nhân viên". Từ này thường bị dùng lẫn với những thứ nhẹ hơn:

| Khái niệm | Là gì | Ví dụ | Có luật suy diễn? |
|---|---|---|---|
| **Từ vựng (vocabulary)** | Danh sách thuật ngữ/thuộc tính dùng chung | Dublin Core, schema.org | Không hoặc rất ít |
| **Taxonomy** | Phân cấp cha-con | Phân loại tin tức | Không |
| **Thesaurus** | Thuật ngữ + quan hệ rộng/hẹp/liên quan | SKOS | Không |
| **Schema** | Cấu trúc dữ liệu cần tuân theo | Schema của cơ sở dữ liệu, JSON Schema | Không (chỉ kiểm tra hợp lệ) |
| **Ontology** | Lớp, thuộc tính, ràng buộc, có thể có axiom để suy diễn | Ontology viết bằng OWL | **Có** (qua reasoner) |
| **Knowledge Graph (KG)** | **Dữ liệu cụ thể** (thực thể thật, quan hệ thật) | Wikidata, đồ thị Neo4j | Tùy |

Giải thích nhanh các từ trong bảng:
- **Dublin Core**: bộ từ vựng chuẩn để mô tả tài liệu, gồm các thuộc tính như tiêu đề, tác giả, ngày tạo. **schema.org**: bộ từ vựng chung để đánh dấu nội dung trang web, ví dụ loại `Person`, `Event`.
- **Taxonomy**: cây phân loại, ví dụ Tin tức > Kinh tế > Chứng khoán. Chỉ có quan hệ cha-con.
- **Thesaurus** (từ điển đồng nghĩa có cấu trúc): ngoài cha-con còn có quan hệ "rộng hơn / hẹp hơn / liên quan". **SKOS** (Simple Knowledge Organization System) là chuẩn W3C để viết thesaurus và phân loại.
- **Schema**: khuôn quy định dữ liệu phải có những trường nào, kiểu gì (như lược đồ cơ sở dữ liệu, hay **JSON Schema** là chuẩn mô tả hình dạng dữ liệu JSON). Nó chỉ kiểm tra dữ liệu có hợp lệ không, không suy ra điều mới.
- **Axiom** (tiên đề): một câu luật được khai báo là luôn đúng trong miền, ví dụ "Giám đốc là một loại Nhân viên". **Reasoner** (bộ máy suy diễn): chương trình đọc các axiom và dữ liệu để tự suy ra điều chưa được ghi, ví dụ từ "Ông A là Giám đốc" suy ra "Ông A là Nhân viên".
- **OWL** (Web Ontology Language): ngôn ngữ chuẩn W3C để viết ontology có axiom, mạnh hơn SKOS.
- **KG** (Knowledge Graph, đồ thị tri thức): đồ thị nút là thực thể thật, cạnh là quan hệ thật, ví dụ nút "Ông A" nối cạnh "làm giám đốc" tới nút "Công ty X". Wikidata và đồ thị trong Neo4j là KG.

Ý quan trọng: **ontology là phần "khuôn" (các loại và quan hệ cho phép), KG là phần "dữ liệu" đổ vào khuôn.** Một đồ thị Neo4j có nhãn node và kiểu cạnh *đã ngầm có một schema*; nó trở thành "ontology" theo nghĩa chặt chỉ khi có đặc tả hình thức và suy diễn.

### Chồng chuẩn W3C **[kiến thức chung]**

W3C (World Wide Web Consortium) là tổ chức đặt chuẩn web. Bộ chuẩn này gọi là Semantic Web (web ngữ nghĩa), xếp thành các lớp chồng lên nhau, lớp dưới là nền của lớp trên:

| Lớp | Chuẩn | Vai trò |
|---|---|---|
| Mô hình dữ liệu | **RDF** (Resource Description Framework) | Mọi thứ là bộ ba chủ ngữ - vị ngữ - tân ngữ, định danh bằng IRI |
| Từ vựng nhẹ | **RDFS** (RDF Schema) | Lớp, lớp con, miền/miền giá trị của thuộc tính |
| Ontology | **OWL** | Ràng buộc và suy diễn phong phú hơn (OWL 2 có các profile nhẹ như EL, QL, RL) |
| Thesaurus | **SKOS** | Khái niệm, rộng/hẹp, nhãn đa ngôn ngữ |
| Kiểm tra dữ liệu | **SHACL** (Shapes Constraint Language) | Kiểm tra dữ liệu có đúng "hình dạng" mong muốn không |
| Truy vấn | **SPARQL** | Ngôn ngữ truy vấn RDF |
| Trao đổi | **JSON-LD** | Cách viết RDF dưới dạng JSON |

Giải thích nhanh các chuẩn trong bảng:
- **RDF**: mô hình dữ liệu cơ bản của web ngữ nghĩa. Mọi tri thức là bộ ba "chủ ngữ - vị ngữ - tân ngữ", ví dụ "Ông A - làm giám đốc - Công ty X". Mỗi thành phần được định danh bằng **IRI** (Internationalized Resource Identifier), một chuỗi giống URL như `http://example.org/OngA`, để hai nguồn dữ liệu khác nhau nói về cùng một thực thể thì dùng chung một định danh.
- **RDFS**: thêm khả năng khai báo lớp (ví dụ `Người`), lớp con (`Giám đốc` là lớp con của `Người`), miền và miền giá trị của thuộc tính (thuộc tính "làm giám đốc" nối từ `Người` tới `Công ty`).
- **OWL**: dựng trên RDF, cho phép khai báo axiom và nhờ reasoner suy diễn. **Profile** EL, QL, RL là các tập con của OWL 2 bị giới hạn bớt để suy diễn nhanh hơn.
- **SKOS**: dành cho thesaurus và phân loại (khái niệm rộng/hẹp, nhãn nhiều ngôn ngữ).
- **SHACL**: viết các "hình dạng" mong muốn, ví dụ "mỗi Người phải có đúng một ngày sinh", rồi kiểm tra dữ liệu có khớp không.
- **SPARQL**: ngôn ngữ truy vấn dữ liệu RDF, giống vai trò của SQL với bảng.
- **JSON-LD**: cách viết dữ liệu RDF dưới dạng JSON, tiện trao đổi giữa các ứng dụng web.

Đối lập với RDF là **property graph** (đồ thị thuộc tính) của Neo4j: node (nút) và cạnh đều có thể mang cặp khóa-giá trị, ví dụ cạnh "làm giám đốc" mang thêm `start_time = 2005`. Đây là lựa chọn dự kiến của đồ án.

| | RDF / OWL | Property graph (Neo4j) |
|---|---|---|
| Thuộc tính trên cạnh | Không có sẵn (cạnh là bộ ba, phải dùng reification hay RDF-star, xem §2) | **Có sẵn** (`start_time`, `end_time` ngay trên cạnh) |
| Suy diễn tự động | Có (nhờ reasoner) | Hầu như không |
| Liên kết dữ liệu mở (dùng chung IRI toàn cầu) | Mạnh | Yếu |
| Dễ dùng cho nhóm không chuyên | Khó | Dễ hơn |

## 2. Thời gian là điểm yếu bẩm sinh của ontology cổ điển

RDF và OWL xây trên **quan hệ hai ngôi** (chủ ngữ - vị ngữ - tân ngữ: nối đúng hai thứ với nhau, ví dụ "Ông A - làm giám đốc - Công ty X"). Một sự việc có thời hạn ("A làm giám đốc từ 2005 đến 2007") thực chất là quan hệ **nhiều ngôi** (người, chức vụ, bắt đầu, kết thúc): bốn thứ cùng lúc, không nhét vừa một bộ ba. Các nguồn học thuật tổng hợp ([Temporal Representation and Reasoning in OWL 2](https://semantic-web-journal.net/content/temporal-representation-and-reasoning-owl-2), [Temporal Extensions to RDF](https://journals.riverpublishers.com/index.php/JWE/article/view/3177)) đều nêu: cần một dạng *reification* (biến cả một câu tri thức thành một đối tượng để có thể gắn thêm thông tin lên nó, ví dụ gắn thời gian) để gắn thời gian vào sự việc, và phần lớn đề xuất chỉ lo **valid time** (thời gian hiệu lực ngoài đời), ít khi lo thời gian hệ thống biết.

### Các cách biểu diễn

| Cách | Ý tưởng | Ưu | Nhược |
|---|---|---|---|
| **Reification chuẩn** | Biến cả câu "A làm X" thành một node rồi gắn thời gian vào node đó | Chuẩn, đi được trong RDF thuần | Rườm rà, nhiều node phụ, mất khả năng suy diễn thuộc tính thường (đảo ngược, bắc cầu) |
| **N-ary relation** | Tạo node "sự kiện nắm giữ chức vụ" nối người, chức vụ, thời gian | Dễ hiểu, tương thích OWL | Thêm nhiều node, truy vấn dài |
| **4D fluents / time slices** | Mỗi "lát cắt thời gian" của một thực thể là một node riêng chứa giá trị tại khoảng đó | Hỗ trợ suy luận thời gian qua OWL/SWRL | Số node tăng nhanh, mô hình phức tạp |
| **Named graph** | Gom các bộ ba vào một "đồ thị đặt tên" rồi gắn khoảng hiệu lực cho cả đồ thị | Gom nhiều fact cùng thời hạn | Hạt thô (cả nhóm), không theo từng fact |
| **RDF-star / triple term (RDF 1.2)** | Bộ ba có thể làm tân ngữ của bộ ba khác, nên gắn chú thích lên từng fact | Gọn nhất trong thế giới RDF | **Tình trạng chuẩn chưa chắc** (Wikipedia ghi RDF 1.2 và SPARQL 1.2 phát hành 04/2026; kết quả tìm kiếm khác vẫn thấy bản Working Draft đến 09/2026; xem `01` §7.9): tìm kiếm cho thấy các tài liệu RDF 1.2 vẫn là Working Draft **[thứ cấp]** |
| **Cạnh có thuộc tính (property graph)** | `start_time`, `end_time` ngay trên cạnh | Đơn giản nhất cho kỹ sư | Không có chuẩn trao đổi; ngữ nghĩa do người dùng tự quy ước |
| **Qualifier + rank (Wikidata)** | Fact có "qualifier" (thời gian, phạm vi) và "rank" (độ ưu tiên/độ tin) | Đã chạy ở quy mô lớn, xem §3 | Mô hình riêng của Wikibase, không phải RDF thuần |

Giải thích nhanh các cách trong bảng, lấy cùng một ví dụ "Ông A làm giám đốc Công ty X từ 2005 đến 2007":
- **Reification chuẩn**: tạo một node "Phát biểu #1" đại diện cho câu "A làm giám đốc X", rồi nối node này tới `bắt đầu = 2005` và `kết thúc = 2007`.
- **N-ary relation** (quan hệ n ngôi): tạo node "Nhiệm kỳ giám đốc" nối tới Ông A, Công ty X và hai mốc thời gian.
- **4D fluents / time slices**: Ông A được tách thành nhiều "lát cắt" theo thời gian, ví dụ "Ông A (2005-2007)" là một node có chức vụ giám đốc. **SWRL** (Semantic Web Rule Language) là ngôn ngữ viết luật suy diễn trên OWL.
- **Named graph**: bỏ các bộ ba về nhiệm kỳ này vào một nhóm có tên, rồi ghi "nhóm này hiệu lực 2005-2007".
- **RDF-star / triple term**: gắn trực tiếp "hiệu lực 2005-2007" lên chính bộ ba "Ông A - làm giám đốc - Công ty X". **Recommendation** là mức chuẩn chính thức cao nhất của W3C; **Working Draft** là bản nháp đang soạn, chưa chính thức.
- **Qualifier** (thuộc tính phụ gắn vào một fact, như thời gian bắt đầu/kết thúc) và **rank** (nhãn ưu tiên của fact: normal, preferred, deprecated; giải thích ở §3) là cách Wikidata làm. **Wikibase** là phần mềm chạy Wikidata.

Hệ quả cho đồ án **[suy luận]**: Zep/Graphiti (xem `07`), thiết kế Neo4j của đồ án và Wikidata đều đi theo kiểu "thuộc tính gắn lên fact". Ta không cần chọn một cách trong số reification/4D fluents; nhưng nên biết rằng đó là lựa chọn *thực dụng* chứ không phải chuẩn.

## 3. Wikidata: tiền lệ trực tiếp cho Evolution ≠ Falsehood

Đã đọc trực tiếp hai trang trợ giúp của Wikidata:

Wikidata lưu mỗi fact thành một "statement" (phát biểu): thực thể - thuộc tính - giá trị, rồi gắn thêm qualifier và rank. Các mã dạng P580 là mã định danh của từng thuộc tính trong Wikidata ("P" là property, thuộc tính).

**Qualifier (từ [Help:Qualifiers](https://www.wikidata.org/wiki/Help:Qualifiers))**: thuộc tính phụ gắn vào một fact để bổ sung ngữ cảnh như thời gian hoặc phạm vi.
- `start time` (P580) và `end time` (P582) giới hạn thời gian hiệu lực của một giá trị; `point in time` (P585) gắn một mốc đơn. Ví dụ: Louis XIV giữ chức "King of France and Navarre" từ 14/05/1643 đến 01/09/1715; dân số Berlin 3.500.000 vào 2005 và 3.440.441 vào 2010.
- Nhờ qualifier, một thuộc tính chứa **nhiều giá trị có mốc thời gian mà không mâu thuẫn**.

**Rank (từ [Help:Ranking](https://www.wikidata.org/wiki/Help:Ranking))**: nhãn ưu tiên gắn vào từng fact khi một thuộc tính có nhiều giá trị. Có ba mức:
- **Normal** (mặc định): "không phán xét độ đúng hay độ hiện hành".
- **Preferred**: giá trị hiện hành, phản ánh đồng thuận.
- **Deprecated**: dành cho thông tin "known to include errors" hoặc *đã lỗi thời nhưng chưa từng đúng* (từng được tin). Trang nói rõ: **"giá trị lịch sử đúng thì không nên deprecate, hãy dùng qualifier start/end time"**.
- Truy vấn mặc định dùng preferred nếu có, không thì normal, và **loại deprecated** trừ khi yêu cầu riêng. Deprecate thay vì xóa để không ai thêm lại lỗi và để giữ lịch sử.

**Đối chiếu với đồ án (đây là phát hiện quan trọng nhất của file này):**

| Khái niệm đồ án | Tương đương Wikidata | Hành vi |
|---|---|---|
| Evolution: đóng `end_time`, vẫn trả về cho truy vấn lịch sử | `end time` (P582) qualifier, rank vẫn normal | Giữ nguyên, đúng trong khoảng của nó |
| Falsehood: `invalidated_at`, bị lọc cứng ở Cơ chế 1 | **Rank deprecated** | Mặc định loại khỏi truy vấn |
| "Hiện hành" | Rank preferred | Ưu tiên khi trả lời "hiện tại" |

Wikidata đã tách *đúng một lần, hết hạn* (qualifier thời gian) khỏi *sai/chưa từng đúng* (rank deprecated) từ lâu. Điều này cho đồ án một **tiền lệ ngoài văn liệu agent memory** để biện minh bất biến Evolution ≠ Falsehood, trong khi Zep và Mem0 không phân biệt (`07`, `08`). Khác biệt cần nêu cho công bằng: Wikidata là cơ sở tri thức do con người biên tập, gán rank thủ công/bán tự động; đồ án cần *tự động* hóa quyết định này.

## 4. Chuẩn thời gian và nguồn gốc có thể mượn

### 4.1. OWL-Time (Time Ontology in OWL) **[thứ cấp, không mở được trang W3C]**
- Chuẩn của W3C và OGC (Open Geospatial Consortium, tổ chức chuẩn dữ liệu địa không gian) về thời gian; nền tảng là **đại số khoảng của Allen** (Allen interval algebra): bộ 13 quan hệ có thể có giữa hai khoảng thời gian, ví dụ trước, sau, gặp nhau (khoảng này kết thúc đúng lúc khoảng kia bắt đầu), chồng lấn, nằm trong. Ví dụ nhiệm kỳ 2005-2007 và nhiệm kỳ 2007-2010 "gặp nhau". Namespace (tiền tố tên để tránh trùng, như một địa chỉ gốc) của chuẩn là `http://www.w3.org/2006/time#`.
- Lớp gốc `TemporalEntity` (thực thể thời gian) với `hasBeginning`, `hasEnd` trỏ tới các `Instant` (thời điểm), `hasTemporalDuration` mô tả độ dài; `ProperInterval` là khoảng có đầu khác cuối.
- Bản Recommendation (chuẩn chính thức) 2017-10-19; theo kết quả tìm kiếm, bản mới nhất là Candidate Recommendation Draft (bản dự thảo ứng viên chuẩn) 15/11/2022 (chưa xác nhận đã thành Recommendation).

Cách mượn cho đồ án **[suy luận]**:

| Đồ án | OWL-Time |
|---|---|
| `[start_time, end_time]` | khoảng với `hasBeginning`/`hasEnd` |
| Case 1: `T_req` nằm trong `[start_time, end_time]` | quan hệ "during/inside" |
| Chuỗi sự nghiệp (cạnh `TIẾP_THEO`) | quan hệ "meets/before" giữa hai khoảng liên tiếp |
| `end_time` bỏ trống | OWL-Time theo giả định thế giới mở (open world: cái gì chưa được ghi thì là chưa biết, chứ không phải không tồn tại): thiếu đầu cuối nghĩa là *không biết*, không phải "đang còn". Đồ án đã phân biệt `ongoing` và `unknown` (tuần 5), đúng tinh thần này |

### 4.2. PROV-O (Provenance Ontology, W3C) **[thứ cấp]**
- Mô hình **nguồn gốc** (provenance: một thông tin từ đâu ra, do ai và việc gì tạo ra): Entity (thực thể, thứ được tạo ra, ví dụ một tài liệu), Activity (hoạt động, việc đã làm), Agent (tác nhân, người hoặc chương trình chịu trách nhiệm); có các quan hệ `wasGeneratedBy` (được sinh ra bởi), `wasDerivedFrom` (dẫn xuất từ), `wasAttributedTo` (do ai tạo), `wasInvalidatedBy` (bị chấm dứt bởi).
- **Cẩn thận:** `wasInvalidatedBy` trong PROV-O là hoạt động *chấm dứt việc dùng* một thực thể (theo kết quả tìm kiếm), tức là chuyện **vòng đời của dữ liệu/tạo phẩm**, *không* phải "sự việc sai từ đầu". Đừng đồng nhất với `invalidated_at` của đồ án.
- Dùng được cho: `ingested_at` ≈ thời điểm sinh ra bản ghi, `sources` ≈ `wasDerivedFrom`. Đây cũng chính là họ trường `sources`/`generated` mà OKF v0.2 thêm vào (`09`).

### 4.3. Ontology pháp luật: ELI, Akoma Ntoso, LRMoo
Vì đồ án có kịch bản văn bản pháp luật (sửa đổi từng điều khoản):
- **ELI** (European Legislation Identifier): lược đồ định danh URI (địa chỉ định danh dạng URL, mỗi văn bản luật một địa chỉ cố định) và metadata (thông tin mô tả) cho luật EU. Nó dựa trên **FRBR** (Functional Requirements for Bibliographic Records), mô hình của ngành thư viện phân biệt "tác phẩm" (nội dung trừu tượng) với "bản" cụ thể của tác phẩm đó. ELI có thành phần thời điểm trong URI cho phiên bản theo thời gian, siêu dữ liệu về ngày hiệu lực/ngày áp dụng, và quan hệ như `eli:amends` (sửa đổi). Nặng về *tài liệu* (document-centric: lấy cả văn bản làm đơn vị).
- **Akoma Ntoso**: chuẩn định dạng XML (ngôn ngữ đánh dấu bằng thẻ) cho văn bản lập pháp, ghi các sự kiện (sửa đổi, hủy bỏ một phần) làm metadata; bản 3.1 được đưa ra lấy ý kiến công khai tháng 09/2025 **[thứ cấp]**.
- Hạn chế chung theo tổng quan của một paper: trạng thái tại một thời điểm thường được tạo bằng cách lưu **bản hợp nhất riêng** (consolidated version: toàn văn đã gộp mọi sửa đổi có hiệu lực tới ngày đó) cho mỗi thời điểm, nên lịch sử của *từng thành phần* (từng điều, khoản) chỉ ngầm hiểu.
- **LRMoo** (mô hình khái niệm thư mục kế thừa FRBR, ở đây áp dụng cho tác phẩm pháp luật): paper [Modeling the Diachronic Evolution of Legal Norms](https://arxiv.org/abs/2506.07853) (Hudson de Martim, cs.AI/cs.IR, bản v5 ngày 05/06/2026) đề xuất mô hình **ở mức thành phần, theo sự kiện**. Diachronic nghĩa là theo dòng thời gian, norm là quy phạm (một quy định cụ thể trong luật). Mỗi phiên bản theo thời gian của một quy phạm là một Work (tác phẩm, theo thuật ngữ FRBR/LRMoo) riêng, các sửa đổi mô hình hóa như sự kiện lập pháp, nhằm *dựng lại đúng một phần văn bản tại ngày bất kỳ*. Mới có **một ca nghiên cứu** (Hiến pháp Brazil); trang không nói tới RAG, đánh giá truy hồi hay việc công bố mã nguồn.

**Liên hệ với đồ án:** tư tưởng "mỗi điều/khoản có vòng đời riêng, sửa đổi chỉ đóng phần bị ảnh hưởng" **trùng** với bất biến *structural chunking* (cắt chunk theo điều/khoản để sửa đổi một phần chỉ đóng chunk bị ảnh hưởng). Có thể trích dẫn như nền học thuật cho quyết định đó, kèm lưu ý bằng chứng còn mỏng.

### 4.4. Ontology sự kiện **[kiến thức chung, chưa kiểm]**
Một số ontology mô hình hóa sự kiện làm thực thể hạng nhất, tức "sự kiện" là một nút riêng có thời gian, địa điểm, người tham gia, chứ không chỉ là cạnh nối (ví dụ LODE, SEM - Simple Event Model, Event Ontology). Hợp với Timeline Summarization vì dòng thời gian là chuỗi sự kiện, nhưng chưa tìm hiểu kỹ trong phiên này nên chỉ ghi là hướng đọc thêm.

## 5. Ontology và LLM: trích xuất theo schema hay tự do?

Khi dùng LLM trích fact để đổ vào đồ thị, có hai kiểu (theo tổng quan [LLM-empowered KG construction: A survey, arXiv 2510.20345](https://arxiv.org/abs/2510.20345), chỉ đọc abstract/tóm tắt):

| Kiểu | Cách làm | Đặc điểm theo các nguồn |
|---|---|---|
| **Theo schema (ontology-guided)** | Cho LLM danh sách loại thực thể/quan hệ cho phép | **Độ chính xác cao hơn**, đồ thị gọn, nhất quán |
| **Tự do (Open IE)** | LLM tự sinh mọi bộ ba | **Độ phủ cao hơn**, nhưng đồ thị nhiễu, quan hệ trùng nghĩa khác tên |
| **Lai (ví dụ khung EDC: Extract-Define-Canonicalize)** | Trích tự do rồi định nghĩa và chuẩn hóa về schema (Zhang & Soh, EMNLP 2024, [arXiv 2404.03868](https://arxiv.org/abs/2404.03868); đã đọc abstract) | Cân bằng hai bên. Xem `16` §7 |

Giải thích nhanh: **Open IE** (Open Information Extraction, trích thông tin mở) là để LLM tự đặt tên quan hệ, nên cùng một ý có thể thành "làm giám đốc", "giữ chức giám đốc", "là CEO". **Chuẩn hóa (canonicalize)** là gộp các tên đồng nghĩa đó về một tên chuẩn trong schema. **Độ chính xác** là tỷ lệ kết quả trích ra đúng; **độ phủ** là tỷ lệ thông tin có trong văn bản mà trích ra được. **Survey** là bài tổng quan.

Nguồn khác ([arXiv 2412.20942](https://www.alphaxiv.org/overview/2412.20942)) thử cấu hình bị ràng buộc theo schema Wikidata và báo kết quả cạnh tranh, nhưng ta mới chỉ đọc tóm tắt.

Với đồ án **[suy luận]**: Graphiti/Zep để LLM tự đặt tên quan hệ (kiểu tự do), nên cùng một ý có thể thành nhiều tên cạnh khác nhau và việc so sánh "cùng ô quan hệ" để phát hiện mâu thuẫn khó hơn. Đồ án có thể dùng một **ontology tối giản** làm schema cho bước trích xuất để cố định từ vựng quan hệ, đặc biệt các cạnh điều khiển Cơ chế 2 và 3.

## 6. Đồ án nên dùng ontology đến mức nào?

**Khuyến nghị [suy luận]: "mini-ontology" thực dụng (một ontology thu nhỏ, chỉ gồm vài chục loại thực thể và quan hệ cần dùng), không cần OWL reasoner.**

| Thành phần | Có nên làm? | Lý do |
|---|---|---|
| Ontology OWL đầy đủ + suy diễn | **Không** | Quá nặng, ngoài phạm vi; thời gian trong OWL khó dùng (§2); không cải thiện Cơ chế 1 |
| Một **bảng schema** nhỏ: loại thực thể, ≈ 10 loại quan hệ (gồm `TIẾP_THEO`, `SUPERSEDES`, `CORRECTS`, `SUSPECTS`), thuộc tính thời gian | **Có** | Làm schema cho trích xuất LLM (§5) và cho GraphDB; tài liệu hóa trong `docs/design/` |
| **Ánh xạ tên** sang chuẩn có sẵn (bảng §7) | **Có**, chỉ là bảng tra | Cho phép xuất RDF/JSON-LD hoặc OKF sau này mà không đổi lõi |
| Xuất **JSON-LD / OKF** | Tùy chọn | Phục vụ trao đổi (xem `09`, `12`) |
| **SHACL** kiểm tra dữ liệu | Tùy chọn | Có thể thay bằng bài kiểm tra thường trong mã (ví dụ: `end_time >= start_time`; không có hai chunk cùng "ô" cùng hiệu lực) |

Giải thích nhanh: "ô" là một cặp (thực thể, quan hệ), ví dụ "chức vụ của ông A"; tại một thời điểm, mỗi ô chỉ nên có một giá trị hiệu lực. **Ánh xạ tên** là bảng đối chiếu tên trường của đồ án với tên trong chuẩn có sẵn. **Schema cho trích xuất LLM** là danh sách loại thực thể/quan hệ cho phép, đưa vào prompt (lời dặn gửi cho LLM) để LLM chỉ trích theo danh sách đó.

Ba ràng buộc nên có (dù không dùng OWL) **[suy luận]**: (1) `start_time <= end_time` khi cả hai có; (2) một chunk bị `invalidated_at` thì không được là đích của `TIẾP_THEO`; (3) `SUPERSEDES` luôn từ chunk mới đến chunk cũ hơn theo `start_time`.

## 7. Bảng ánh xạ đề xuất (đồ án ↔ chuẩn)

Đối chiếu tên để biết "đồ án đang tự định nghĩa lại cái gì đã có chuẩn". Ánh xạ chỉ mang tính gần đúng; cột "Độ chắc" cho biết đã kiểm hay chưa.

| Trường/cạnh đồ án | Chuẩn gần nhất | Độ chắc |
|---|---|---|
| `start_time` | Wikidata `start time` P580; `time:hasBeginning` (OWL-Time) | P580 đã đọc; OWL-Time thứ cấp |
| `end_time` | Wikidata `end time` P582; `time:hasEnd` | như trên |
| `end_time = NULL` (đang còn) vs không rõ | Wikidata có giá trị đặc biệt "unknown/no value" **[kiến thức chung]**; OWL-Time thế giới mở | Chưa kiểm |
| `invalidated_at` (sai từ đầu) | **Wikidata rank deprecated** (§3) | Đã đọc |
| Hiện hành | Wikidata rank preferred | Đã đọc |
| `ingested_at` / `first_seen` (lúc hệ thống nạp / thấy lần đầu) | `prov:generatedAtTime` (PROV-O, "thời điểm được sinh ra") | Thứ cấp |
| `sources` / `Chunk_ID` trỏ về văn bản gốc | `prov:wasDerivedFrom`; `sources` của OKF v0.2 | PROV thứ cấp; OKF đã đọc |
| `SUPERSEDES` (thay thế) | Wikidata `replaces`/`replaced by` (P1365/P1366) **[kiến thức chung]**; `eli:amends` (luật) | Chưa kiểm cả Wikidata lẫn ELI chi tiết |
| `TIẾP_THEO` (chuỗi sự nghiệp) | quan hệ "meets/before" của Allen | Thứ cấp |
| `SUSPECTS` (cáo buộc, không phải sự thật) | Không thấy tương đương; Wikidata dùng qualifier `statement disputed by` **[kiến thức chung]** | Chưa kiểm |

## 8. Công cụ nếu muốn thử **[kiến thức chung, chưa kiểm trong phiên này]**

> Bảng công cụ đã được kiểm tra thêm bằng tìm kiếm (rdflib, owlready2, pySHACL, Protégé, triple store, neosemantics) và ghi ở [`01` §2B](01_Knowledge_Representation_Spectrum.md), kèm lưu ý rdflib không hỗ trợ OWL 2 và n10s chỉ chạy trên Neo4j tự cài. Danh sách dưới đây là bản ngắn viết trước đó.
- Python: `rdflib` (thư viện đọc/ghi RDF, chạy SPARQL), `pySHACL` (thư viện kiểm tra ràng buộc SHACL).
- Java: Apache Jena (bộ thư viện làm việc với RDF). Soạn ontology: Protégé (phần mềm đồ họa để soạn và xem ontology OWL).
- Neo4j: tiện ích neosemantics (n10s) để nhập/xuất RDF từ đồ thị thuộc tính (property graph).
- Nếu chỉ cần ánh xạ nhẹ: tự sinh JSON-LD từ bảng §7, không cần cài thêm.

## 9. Câu hỏi mở
- Có cần xuất RDF/JSON-LD cho hội đồng ("tuân thủ chuẩn mở") hay chỉ cần bảng ánh xạ?
- `end_time = NULL`: dùng hai giá trị riêng `ongoing`/`unknown` (như tuần 5) hay một cờ riêng? Wikidata và OWL-Time xử lý "không rõ" khác nhau, cần đọc kỹ trước khi chốt.
- Có nên thêm trường lý do đóng (`invalid_reason`) để khớp tách qualifier thời gian khỏi rank deprecated (`11` §5)?
- Cần mở được trang W3C (OWL-Time, PROV-O) bằng cách khác (tải tay, hoặc bản mirror) để xác minh §4.1, §4.2.

## 10. Tài liệu tham khảo
**Đã mở trực tiếp**
- Wikidata — [Help:Ranking](https://www.wikidata.org/wiki/Help:Ranking), [Help:Qualifiers](https://www.wikidata.org/wiki/Help:Qualifiers)
- arXiv — [2506.07853: Modeling the Diachronic Evolution of Legal Norms (LRMoo)](https://arxiv.org/abs/2506.07853)

**Qua kết quả tìm kiếm (thứ cấp, trang gốc W3C trả về 403)**
- W3C — [Time Ontology in OWL](https://www.w3.org/TR/owl-time/), [bản Recommendation 2017](https://www.w3.org/TR/2017/REC-owl-time-20171019/), [tin W3C](https://www.w3.org/blog/news/archives/6578)
- W3C — [PROV-O](https://www.w3.org/TR/prov-o/)
- W3C — [RDF 1.2 (RDF/XML, Working Draft)](https://www.w3.org/TR/rdf12-xml/)
- [Temporal Representation and Reasoning in OWL 2 (Semantic Web Journal)](https://semantic-web-journal.net/content/temporal-representation-and-reasoning-owl-2), [Temporal Extensions to RDF](https://journals.riverpublishers.com/index.php/JWE/article/view/3177), [Temporally Enhanced Ontologies in OWL](https://personal.eur.nl/frasincar/papers/WISE2015/wise2015p.pdf)
- [LLM-empowered KG construction: A survey (arXiv 2510.20345)](https://arxiv.org/abs/2510.20345); [arXiv 2412.20942](https://www.alphaxiv.org/overview/2412.20942)
- Luật: [Akoma Ntoso 3.1 (OASIS)](https://groups.oasis-open.org/discussion/akoma-ntoso-version-31-schemas-ready-for-public-review), [rOWLer (Jusletter IT 2015)](https://author.weblaw.ch/magnoliaAuthor/jusletter-it/en/issues/2015/IRIS/rowler---a-hybrid-ru_62514d1008.html)
