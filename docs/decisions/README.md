# Nhật ký quyết định thiết kế

Mỗi file ghi **một** quyết định: bối cảnh, các phương án, chọn gì và vì sao, ảnh hưởng tới design, trạng thái. Khác với `docs/process/` (nhật ký làm gì theo thứ tự thời gian) và `docs/design/` (thiết kế hiện hành): đây là nơi tra lại "vì sao thiết kế thành thế này" khi viết luận văn. Khi một quyết định đổi design, sửa `docs/design/` rồi trỏ về file ở đây.

| File | Quyết định | Trạng thái |
|---|---|---|
| [`01_DOMAIN_AS_SOFT_BOOST.md`](01_DOMAIN_AS_SOFT_BOOST.md) | `domain` chỉ cộng điểm, không lọc cứng | Đã quyết, chưa code ở retrieval |
| [`02_END_TIME_ONGOING.md`](02_END_TIME_ONGOING.md) | Xử lý `end_time` / `ongoing` bị LLM gán sai | Đã quyết; ingestion và 3 cách chấm đã code; đo ở local: không cách nào hơn rõ (`eval/04` đợt 3) |
| [`03_PROMPT_CHANGELOG.md`](03_PROMPT_CHANGELOG.md) | Sổ thay đổi prompt kèm hiệu quả | Cập nhật liên tục |
| [`04_UNDATED_CHUNKS.md`](04_UNDATED_CHUNKS.md) | Chunk không có `start` và câu hỏi không nêu thời gian | Đã code; đo ở local cho thấy có lợi (`eval/04` đợt 4b), chờ xác nhận ở bộ thật |
| [`05_EXCLUDE_BEFORE_COMMON_ERA.md`](05_EXCLUDE_BEFORE_COMMON_ERA.md) | Loại chunk và câu hỏi có mốc trước Công nguyên | Đã quyết |
| [`06_END_UNKNOWN_REMEDIES.md`](06_END_UNKNOWN_REMEDIES.md) | Nhóm câu còn sai ở cấu hình tốt nhất và cách xử lý chunk `end_status = unknown` (tách `ongoing`/`unknown`) | Đề xuất 1 đã code và đo (`mrr` 0.580), chờ xác nhận ở bộ thật; còn lại chưa quyết |
| [`07_RANKING_AND_TIME_RANGE_PROPOSALS.md`](07_RANKING_AND_TIME_RANGE_PROPOSALS.md) | Nâng thứ hạng sau bộ thật: Profiler trích khoảng thời gian + độ chồng lấn, phạt `end` từ `end`, reranker, chỉ số chuỗi đáp án | Đề xuất, chưa code, chưa thử |
| [`08_TRAIN_VALID_TEST_SPLIT.md`](08_TRAIN_VALID_TEST_SPLIT.md) | Tách train/valid/test cân bằng domain, cỡ mẫu, chi phí | Đã tạo các bộ con, đã chọn phương pháp và quét tham số trên tune/valid ([`eval/07`](../eval/07_TUNE_VALID_RESULTS.md)); `test_clean` đã chạy một lần |
| [`09_CONFLICT_RESOLUTION_SCOPE.md`](09_CONFLICT_RESOLUTION_SCOPE.md) | Cơ chế 3: bỏ đa nguồn, làm Evolution và Falsehood trên dữ liệu Wikidata/Wikipedia; kế hoạch câu hỏi đánh giá và hạn chế | Đã quyết phạm vi; đã crawl và đo sơ bộ ([`eval/06`](../eval/06_WIKI_REVISION_CRAWL.md)); dữ liệu đánh giá và code chưa làm |
| [`10_TIMELINE_GRAPH_AND_VECTOR_LINK.md`](10_TIMELINE_GRAPH_AND_VECTOR_LINK.md) | Cơ chế 2: nút sự kiện theo ô (trang, quan hệ), liên kết n-n với chunk, trích xuất và cập nhật nút, so sánh graph với vector top-k (cố định và thích nghi) bằng độ phủ theo token | Đã thống nhất thiết kế; chưa code |
