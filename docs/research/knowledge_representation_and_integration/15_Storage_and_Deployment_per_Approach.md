# Lưu trữ và triển khai (Docker) cho từng cách biểu diễn tri thức

> **Câu hỏi file này trả lời:** `01` mô tả 5 cách ghi tri thức (RDF/OWL, property graph, node là đoạn văn, markdown + frontmatter, chunk + metadata). Nhưng mỗi cách cần **cơ sở dữ liệu / công nghệ lưu trữ** nào, chạy bằng **Docker** ra sao, giấy phép gì, truy vấn bằng ngôn ngữ gì, và lọc theo thời gian thế nào? File này trả lời từng cách, rồi gợi ý cách ghép cho đồ án.
> **Độ tin cậy:** đã mở trực tiếp tài liệu/README chính thức của **Qdrant, Neo4j (operations manual), GraphDB (repo docker của Ontotext), Oxigraph, Apache Jena Fuseki, Apache AGE, pgvector, Memgraph**. Phần còn lại lấy từ kết quả tìm kiếm (blog, trang tổng hợp, bản sao tài liệu) và gắn **[thứ cấp]**. **[kiến thức chung]** là kiến thức nền chưa kiểm lại trong phiên này; **[suy luận]** là phân tích của nhóm. Các lệnh và tập tin Docker Compose ở đây **chưa chạy thử**; tag phiên bản đổi liên tục nên hãy lấy tag hiện hành từ Docker Hub.

## 0. Vài khái niệm Docker dùng trong file

- **Docker image**: gói đóng sẵn phần mềm cùng môi trường chạy (ví dụ `qdrant/qdrant`). **Container**: một bản đang chạy của image.
- **Port** (cổng): số hiệu để máy ngoài nói chuyện với container (`-p 6333:6333` nghĩa là cổng 6333 của máy nối vào cổng 6333 trong container).
- **Volume**: thư mục của máy được gắn vào container để dữ liệu không mất khi container bị xóa.
- **Docker Compose**: tệp `docker-compose.yml` mô tả nhiều container chạy cùng nhau (ví dụ kho vector + kho đồ thị + API).
- **REST / gRPC**: hai kiểu giao diện lập trình để gọi một server; gRPC thường nhanh hơn, REST dễ thử bằng trình duyệt.
- **ACID** (Atomicity, Consistency, Isolation, Durability): bốn đảm bảo của giao dịch cơ sở dữ liệu; nói đơn giản là một thao tác ghi hoặc xong hẳn hoặc không xảy ra, dù có sự cố.

## 1. Bảng tổng quan: mỗi cách cần lưu trữ gì

| Cách (ở `01`) | Loại lưu trữ cần | Lựa chọn hay gặp | Ngôn ngữ truy vấn | Cần Docker/DB riêng? |
|---|---|---|---|---|
| **1. RDF/OWL** | **Triple store** (kho bộ ba) | Apache Jena Fuseki, GraphDB, Oxigraph, Virtuoso, RDF4J | SPARQL | Có (một triple store) |
| **2. Property graph** | **Graph database** (cơ sở dữ liệu đồ thị) | Neo4j, Memgraph, FalkorDB, Apache AGE (trên Postgres), Kuzu (nhúng) | Cypher (hoặc openCypher) | Có (một graph DB) |
| **3. Node = đoạn văn** | Graph DB **có thuộc tính văn bản**, hoặc kho tài liệu, hoặc file + chỉ mục tìm kiếm | Neo4j/Memgraph/AGE (nút mang `text`), MongoDB, Postgres, hoặc engine wiki | Cypher, SQL, tìm văn bản | Thường dùng lại graph DB hoặc Postgres |
| **4. Markdown + frontmatter** | **Hệ thống file + git**, kèm chỉ mục tìm kiếm tùy chọn | Thư mục + git; Meilisearch/Typesense/Postgres full-text; qmd | Đọc file, grep, tìm kiếm | **Không cần DB**; chỉ volume và (tùy chọn) search engine |
| **5. Chunk + metadata** | **Vector database** (cơ sở dữ liệu vector) | Qdrant, Milvus, Weaviate, Chroma, pgvector | Tìm vector + lọc payload | Có (một vector DB) |

## 2. Cách 1: RDF/OWL cần triple store

**Triple store** là cơ sở dữ liệu chuyên lưu bộ ba RDF và trả lời SPARQL. Ontology (file `.ttl`/`.owl`) và dữ liệu đều nạp vào đó; một số store kèm **reasoner** để suy diễn khi nạp hoặc khi truy vấn.

| Triple store | Đã kiểm chứng gì | Docker | Giấy phép |
|---|---|---|---|
| **Apache Jena Fuseki** | Trang chính thức: máy chủ SPARQL, chạy độc lập hoặc nhúng; hỗ trợ SPARQL 1.1 query/update và Graph Store; lưu bền bằng **TDB** (kho bộ ba của Jena); điều khiển truy cập bằng Apache Shiro; có module GeoSPARQL; "có sẵn dạng Docker container" | Trang chính thức nói có Docker; các image **do cộng đồng** build (ví dụ dự án AtomGraph/fuseki-docker, nối cổng 3030, endpoint dạng `/ds/sparql`, `/ds/update`) **[thứ cấp]** | Apache 2.0 |
| **GraphDB** (Ontotext) | Repo Docker chính thức: image `ontotext/graphdb` (ví dụ tag `10.7.0`), cổng **7200**, dữ liệu ở `/opt/graphdb/home`, cấu hình qua `graphdb.properties` hoặc biến `GDB_JAVA_OPTS`; có công cụ nạp hàng loạt `importrdf`; **cần file giấy phép** (gắn vào `conf/graphdb.license` hoặc qua `-Dgraphdb.license.file`) | `docker run -p 7200:7200 ... ontotext/graphdb:<tag>` | Cần license (README không nói rõ bản miễn phí khác bản trả phí thế nào, **chưa kiểm**) |
| **Oxigraph** | README: viết bằng Rust; Apache-2.0 hoặc MIT; SPARQL 1.1 Query/Update/Federated; chạy server HTTP qua CLI; lưu bằng **RocksDB** (kho khóa-giá trị nhúng); có `pyoxigraph` (PyPI); "hỗ trợ sơ bộ bản nháp RDF 1.2 và SPARQL"; tự nhận **đang phát triển mạnh, chưa tối ưu truy vấn** | README chỉ nói hướng dẫn Docker nằm trong thư mục `cli`, không nêu tên image | Apache-2.0/MIT |
| **Virtuoso**, **RDF4J**, **Stardog**, **Blazegraph**, **Neptune**, **AllegroGraph** | Chỉ xuất hiện trong danh sách so sánh (bài giảng đại học 2025, benchmark LINCS cũ); tìm thấy image cộng đồng của Virtuoso (cổng 8890) | — | — |

Ghi chú:
- Hỗ trợ **suy diễn OWL/RDFS và SHACL** của từng store: các trang đã mở **không nêu** (Fuseki) hoặc **không nêu trong README** (GraphDB), nên tôi chưa khẳng định. **[kiến thức chung]** Jena có bộ suy diễn đi kèm và GraphDB nổi tiếng với suy diễn theo bộ luật; cần đối chiếu tài liệu trước khi dựa vào.
- **Lọc theo thời gian trong SPARQL** dùng `FILTER` trên giá trị ngày hoặc số (ví dụ ở `01` §7.8); mốc "chưa kết thúc" xử lý bằng `OPTIONAL` + `!BOUND`.
- **Soạn ontology**: **Protégé** là ứng dụng desktop, không cần Docker.

## 3. Cách 2: property graph cần graph database

| Graph DB | Đã kiểm chứng gì | Docker | Giấy phép |
|---|---|---|---|
| **Neo4j** | Tài liệu vận hành chính thức: image `neo4j`; bản Community không hậu tố tag, Enterprise thêm `-enterprise`; cổng **7474** (Neo4j Browser) và **7687** (giao thức **Bolt** cho driver); volume `/data`; đặt mật khẩu bằng `NEO4J_AUTH=neo4j/<mật_khẩu>` (tối thiểu 8 ký tự); Enterprise phải đặt `NEO4J_ACCEPT_LICENSE_AGREEMENT=yes`; ACID, Cypher; Community đủ cho cài **một máy**, Enterprise thêm sao lưu, cụm máy, chuyển dự phòng | `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/<mk> -v ./data:/data neo4j:<tag>` | Community **GPLv3**; Enterprise bản thương mại (các bản sao GitHub nói thêm AGPLv3 cho dự án mã nguồn mở, **[thứ cấp, không chắc]**). Thư viện GDS (Graph Data Science) bản Community giới hạn 4 lõi **[thứ cấp]** |
| **Memgraph** | README: bản Community theo giấy phép **BSL**, Enterprise theo **MEL**; thiết kế **trong bộ nhớ** (in-memory), engine C/C++; "tương thích hoàn toàn với Cypher của Neo4j"; **có chỉ mục vector** tìm tương tự ngay trong truy vấn đồ thị; Enterprise thêm HA (Raft), nhiều tenant, SSO, mã hóa, sao lưu | README không nêu tên image/cổng | BSL (Community) |
| **Apache AGE** | README: **tiện ích mở rộng của PostgreSQL**, giấy phép Apache-2.0, hỗ trợ Postgres 11 đến 18; chạy openCypher cạnh SQL qua hàm `cypher()`; image `apache/age`, ví dụ ánh xạ cổng 5455→5432; mỗi phiên cần `LOAD 'age'` và đặt `search_path` có `ag_catalog`. Một gói thứ cấp (`langchain-age`) ghi nhận AGE **không hỗ trợ Cypher có tham số `$param`** và không có thư viện **APOC** (bộ thủ tục mở rộng của Neo4j) | `apache/age`; có image cộng đồng gộp Postgres 18 + pgvector + AGE (`stden/postgres-vector-graph`) **[thứ cấp]** | Apache-2.0 |
| **FalkorDB** | Kết quả tìm kiếm: **module Redis** cho đồ thị, chạy trong bộ nhớ; Graphiti hỗ trợ làm backend **[thứ cấp]** | chưa kiểm | chưa kiểm |
| **Kuzu** | Kết quả tìm kiếm: cơ sở dữ liệu đồ thị **nhúng** (chạy trong tiến trình ứng dụng, không cần server riêng); Graphiti hỗ trợ **[thứ cấp]** | Không cần Docker riêng | chưa kiểm; nên **xem tình trạng bảo trì** trước khi chọn |
| **Amazon Neptune** | Dịch vụ đám mây của AWS; Graphiti hỗ trợ, cần thêm OpenSearch Serverless cho tìm văn bản **[thứ cấp]** | Không (dịch vụ trả phí) | Dịch vụ |

**Graphiti** (hệ thống bộ nhớ đồ thị của Zep, xem `07`) liệt kê bốn backend: Neo4j, FalkorDB, Kuzu, Neptune theo các trang tài liệu bản sao; một trang của Zep chỉ ghi hai (Neo4j, FalkorDB), có thể đã cũ **[thứ cấp, mâu thuẫn]**. Yêu cầu Neo4j 5.26 trở lên **[thứ cấp]**.

Lọc thời gian ở Cypher đọc thẳng thuộc tính trên cạnh (xem `01` §7.8). **[kiến thức chung]** Neo4j có kiểu ngày giờ (`date`, `datetime`, `duration`) sẵn có. Cầu nối với RDF: **neosemantics (n10s)** cho Neo4j tự cài (không có trên Aura), xem `01` §2B.

## 4. Cách 3: node là đoạn văn

Về lưu trữ, cách 3 **không cần một loại cơ sở dữ liệu riêng**; nó là cách 2 với "nút béo": mỗi nút mang thêm thuộc tính `text` dài. Lựa chọn:

| Phương án | Ý tưởng | Ưu | Nhược |
|---|---|---|---|
| **Graph DB với nút có `text`** (Neo4j/Memgraph/AGE) | Mỗi trang là một nút; link là cạnh | Một kho, truy vấn đi theo link được | Văn bản lớn làm nặng đồ thị; cần thêm chỉ mục văn bản/vector |
| **Postgres** (bảng `pages` + bảng `links`) | Quan hệ + full-text + pgvector | Một DB, giao dịch ACID | Duyệt link nhiều bước phải viết truy vấn đệ quy |
| **Kho tài liệu** (MongoDB…) **[kiến thức chung]** | Mỗi trang là một tài liệu JSON | Linh hoạt | Không tối ưu duyệt đồ thị |
| **Engine wiki** (MediaWiki…) **[kiến thức chung]** | Phần mềm wiki sẵn có | Có giao diện người dùng | Nặng, không thiết kế cho truy xuất của LLM |

**[suy luận]** So với thiết kế **Boomerang** của đồ án (nút mỏng, văn bản gốc ở VectorDB, nối bằng `Chunk_ID`): cách 3 là hướng ngược lại, nút béo chứa luôn văn bản. Boomerang cần giữ **hai kho khớp nhau**; nút béo bớt được chuyện đồng bộ nhưng đồ thị nặng và khó nén token.

## 5. Cách 4: markdown + frontmatter

Lưu trữ **không cần cơ sở dữ liệu**: một thư mục file `.md` (bundle OKF, xem `09`) đặt trong **git**. Trong Docker chỉ cần **bind-mount** thư mục đó làm volume. Muốn tìm kiếm nhanh thì thêm chỉ mục:

| Thành phần | Vai trò | Ghi chú | Độ tin |
|---|---|---|---|
| **git** | Lịch sử thay đổi, cộng tác | Miễn phí, có sẵn | — |
| **Meilisearch** | Công cụ tìm kiếm văn bản chạy bằng Docker | Cần đặt master key (≥ 16 byte); khuyến nghị gắn cổng vào `127.0.0.1`, đặt Nginx phía trước cho HTTPS, dùng volume bền, tạo khóa chỉ-tìm-kiếm cho phía công khai | thứ cấp |
| **Typesense** | Công cụ tìm kiếm tương tự | Một mẫu triển khai biết đọc frontmatter và nội dung markdown rồi đẩy tài liệu có cấu trúc vào chỉ mục (trang của vendor) | thứ cấp |
| **Postgres full-text** | Tìm văn bản ngay trong Postgres | Một DB cho nhiều việc | kiến thức chung |
| **qmd** | Công cụ tìm kiếm markdown cục bộ trong gist Karpathy: lai BM25 + vector, LLM xếp hạng lại, có CLI và **MCP server** | Xem `10` | gist, chưa kiểm repo |
| **Trình xem OKF** | Trang HTML tĩnh vẽ bundle thành đồ thị | Không cần backend (xem `09` §8) | spec/README |

**Lưu ý [suy luận]:** chỉ mục tìm kiếm chỉ giúp *tìm*; **lọc cứng theo thời gian** (chống rò rỉ tương lai) vẫn phải được cài ở lớp truy vấn, vì file markdown không có cơ chế sẵn.

## 6. Cách 5: chunk + metadata cần vector database

| Vector DB | Đã kiểm chứng gì | Docker |
|---|---|---|
| **Qdrant** | Trang quickstart chính thức: image `qdrant/qdrant`; cổng **6333** (REST và trang quản trị tại `/dashboard`) và **6334** (gRPC, dùng cho client Rust/Java/C#/Go); volume `/qdrant/storage`; **khuyến nghị tạo payload index** để lọc nhanh; trang này không bàn về tìm lai hay vector thưa | `docker run -p 6333:6333 -p 6334:6334 -v "$(pwd)/qdrant_storage:/qdrant/storage:z" qdrant/qdrant` |
| **pgvector** | README chính thức: tiện ích mở rộng của Postgres; bật bằng `CREATE EXTENSION vector;`; chỉ mục **HNSW** (đồ thị gần đúng, nhanh, tốn bộ nhớ khi xây) và **IVFFlat** (chia cụm, xây nhanh, truy vấn kém hơn); toán tử khoảng cách L2 `<->`, cosine `<=>`, tích trong âm `<#>`…; lọc bằng chỉ mục thường hoặc partial index, nên bật quét lặp (`hnsw.iterative_scan`) khi lọc sau chỉ mục gần đúng; **tìm lai bằng cách kết hợp full-text của Postgres** rồi gộp bằng RRF hoặc cross-encoder; mở rộng bằng `halfvec`, lượng tử hóa nhị phân, replica, Citus | image `pgvector/pgvector` (tag như `pg17`, `pg18-trixie`) |
| **Milvus** | Nguồn thứ cấp: tự cài cần nhiều thành phần, kiểu vận hành Kubernetes | chưa kiểm |
| **Weaviate** | Một nguồn thứ cấp đánh giá mạnh về tìm lai (chưa có đo kiểm) | chưa kiểm |
| **Chroma** | Thứ cấp: dễ chạy cục bộ, hợp thử nghiệm, không hợp cụm phân tán lớn | chưa kiểm |

Một bài so sánh (một cấu hình phần cứng, 1,18 triệu vector, **[thứ cấp]**) ghi Qdrant dùng ít bộ nhớ nhất (đỉnh khoảng 937 MiB) so với pgvector (2.765 MiB) và Weaviate (3.689 MiB), còn Milvus và Weaviate có độ trễ p95 thấp nhất (khoảng 3 ms, Qdrant 5,3 ms). Chính nhà xuất bản nói phiên bản đã đổi nên số liệu có thể lệch; **không dùng để chọn**.

**Đồ án đã dùng Qdrant** (kết quả tuần 4–5). Thiết kế hiện tại chỉ đánh chỉ mục 4 trường payload (`start_time`, `invalidated_at`, `domain_features.domain`, `domain_features.country`). **[kiến thức chung]** Qdrant có kiểu chỉ mục riêng cho ngày giờ; cần xác nhận trong tài liệu payload index khi cài.

## 7. Ghép lại: ít container hơn, hay đúng mỗi loại một DB?

| Phương án | Thành phần | Ưu | Nhược |
|---|---|---|---|
| **A. Thiết kế hiện tại** | Qdrant + Neo4j (+ API/MCP server) | Mỗi DB làm đúng việc; Qdrant tốt cho lọc payload | **Hai kho phải khớp nhau** (Boomerang); hai thứ phải vận hành |
| **B. Gói gọn trong Postgres** | Postgres + **pgvector** + **Apache AGE** + bảng quan hệ + full-text | Một DB; **giao dịch ACID bao cả chunk lẫn đồ thị** nên không lo lệch; `tstzrange` (kiểu khoảng thời gian, `03`) | AGE ít phổ biến hơn Neo4j, không hỗ trợ Cypher có tham số, thiếu APOC; pgvector tốn bộ nhớ hơn trong bài so sánh trên **[thứ cấp]** |
| **C. Chỉ Memgraph** | Memgraph (đồ thị + chỉ mục vector) | Một DB, trong bộ nhớ nên nhanh | Giấy phép BSL; bộ nhớ lớn; chưa kiểm khả năng lọc thời gian và tìm lai |
| **D. Chỉ Neo4j** | Neo4j với chỉ mục vector **[kiến thức chung]** | Một DB | Chưa kiểm hiệu năng lọc và tìm lai so với Qdrant |
| **E. Thêm triple store** | A + Fuseki/GraphDB/Oxigraph | Có SPARQL, ontology chuẩn | Thêm một DB nữa; chỉ cần nếu muốn dùng suy diễn OWL hay xuất dữ liệu liên kết (`01` §7.12) |

**[suy luận]** Với phạm vi đồ án: **A** là đường ngắn nhất vì Qdrant và code Cơ chế 1 đã có; **B** đáng thử như phương án so sánh vì loại bỏ được bài toán đồng bộ hai kho. **E** không cần trừ khi nhóm quyết định dùng RDF.

### Bài toán đồng bộ hai kho (phương án A)
Boomerang yêu cầu mỗi nút đồ thị có `Chunk_ID` trỏ đúng chunk còn tồn tại trong VectorDB. **[suy luận]** Một nguyên tắc an toàn: ghi chunk trước, ghi nút sau; mỗi thao tác idempotent (làm lại không đổi kết quả) nhờ **content hash** (bất biến của đồ án: hash trùng thì không làm gì); có bước dọn nút mồ côi định kỳ; nếu cần ACID thật sự thì cân nhắc phương án B.

## 8. Docker Compose mẫu cho thiết kế hiện tại (chưa chạy thử)

```yaml
services:
  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333", "6334:6334"]
    volumes: ["./qdrant_storage:/qdrant/storage"]

  neo4j:
    image: neo4j:2026.10.1            # tag lấy từ tài liệu; thay bằng tag hiện hành
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/doi_mat_khau_nay   # tối thiểu 8 ký tự
    volumes: ["./neo4j_data:/data"]

  memory-api:                          # MCP server / API của đồ án (xem 12)
    build: ./server
    depends_on: [qdrant, neo4j]
    environment:
      QDRANT_URL: http://qdrant:6333
      NEO4J_URI: bolt://neo4j:7687
    ports: ["8000:8000"]
```

Phương án B (Postgres gói gọn) đổi hai dịch vụ đầu thành một: image Postgres có **pgvector** và **AGE**. Bản chính thức riêng lẻ là `pgvector/pgvector` và `apache/age`; một image cộng đồng gộp cả hai (`stden/postgres-vector-graph`, **[thứ cấp]**) hoặc tự build từ một trong hai rồi cài phần còn lại.

## 9. Bảng chọn nhanh theo tiêu chí

| Tiêu chí | Qdrant | pgvector | Neo4j CE | Memgraph | AGE | Fuseki / GraphDB / Oxigraph |
|---|---|---|---|---|---|---|
| Loại | Vector DB | Vector trong Postgres | Graph DB | Graph DB trong bộ nhớ | Graph trong Postgres | Triple store |
| Truy vấn | REST/gRPC + lọc payload | SQL | Cypher | Cypher | SQL + openCypher | SPARQL |
| Giấy phép | (chưa mở trang) | (trang không nêu, xem LICENSE) | GPLv3 (thứ cấp) | BSL | Apache-2.0 | Apache-2.0 / cần license / Apache-2.0 hoặc MIT |
| Vector có sẵn | Là việc chính | Là việc chính | **[kiến thức chung]** có | **Có** | Qua pgvector cùng DB | Không nêu |
| Hợp cách | 5 | 5 (và 2, 3 cùng DB) | 2, 3 | 2, 3 | 2, 3 | 1 |

## 10. Câu hỏi mở
- Nhóm chấp nhận hai DB (phương án A) hay muốn thử gộp vào Postgres (B) để tránh đồng bộ? Cần một thử nghiệm nhỏ so độ trễ truy vấn lọc thời gian và độ phức tạp mã.
- Có cần suy diễn OWL/SHACL tại tầng lưu trữ không? Nếu không, bỏ phương án E.
- Giấy phép: GPLv3 của Neo4j Community và BSL của Memgraph có ảnh hưởng gì tới việc nộp/mở mã nguồn đồ án? Cần đọc giấy phép gốc.
- Kiểm tra lại các ô **[thứ cấp]** và "chưa kiểm" trước khi trích dẫn trong luận văn: Qdrant tìm lai/vector thưa/chỉ mục ngày giờ, tình trạng của Kuzu, tag Neo4j hiện hành.

## 11. Tài liệu tham khảo (docs, git)

**Đã mở trực tiếp**
- Qdrant — [Quickstart](https://qdrant.tech/documentation/quickstart/)
- Neo4j — [Operations Manual: Docker](https://neo4j.com/docs/operations-manual/current/docker/introduction/)
- Ontotext — [graphdb-docker](https://github.com/Ontotext-AD/graphdb-docker)
- Oxigraph — [oxigraph/oxigraph](https://github.com/oxigraph/oxigraph)
- Apache Jena — [Fuseki](https://jena.apache.org/documentation/fuseki2/)
- Apache AGE — [apache/age](https://github.com/apache/age)
- pgvector — [pgvector/pgvector](https://github.com/pgvector/pgvector)
- Memgraph — [memgraph/memgraph](https://github.com/memgraph/memgraph)

**Qua kết quả tìm kiếm (thứ cấp)**
- Neo4j license (bản sao GitHub, không chính thức): [neo4j mirror](https://github.com/umesh-prasad/neo4j); GDS: [Neo4j community](https://community.neo4j.com/t/license-model-of-gds/23664/3)
- Graphiti backends: [graph drivers (bản sao Mintlify)](https://mintlify.com/getzep/graphiti/guides/graph-drivers), [Zep docs](https://help.getzep.com/graphiti/configuration/graph-db-configuration)
- Fuseki Docker cộng đồng: [AtomGraph/fuseki-docker](https://github.com/AtomGraph/fuseki-docker)
- AGE + pgvector: [langchain-age](https://pypi.org/project/langchain-age/), [stden/postgres-vector-graph](https://hub.docker.com/r/stden/postgres-vector-graph)
- So sánh vector DB: [computingforgeeks](https://computingforgeeks.com/qdrant-weaviate-milvus-pgvector/), [datascienceinaction](https://datascienceinaction.substack.com/p/when-to-use-which-vector-database)
- Meilisearch / Typesense: [Meilisearch + VuePress](https://ecosystem.vuejs.press/plugins/search/meilisearch.html), [Typesense Markdown](https://railway.com/deploy/typesense-markdown)
- So sánh triple store (cũ): [LINCS](https://portal.lincsproject.ca/blog/triplestore-battle)
