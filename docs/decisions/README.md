# Nhật ký quyết định thiết kế

Mỗi file ghi **một** quyết định: bối cảnh, các phương án, chọn gì và vì sao, ảnh hưởng tới design, trạng thái. Khác với `docs/process/` (nhật ký làm gì theo thứ tự thời gian) và `docs/design/` (thiết kế hiện hành): đây là nơi tra lại "vì sao thiết kế thành thế này" khi viết luận văn. Khi một quyết định đổi design, sửa `docs/design/` rồi trỏ về file ở đây.

| File | Quyết định | Trạng thái |
|---|---|---|
| [`01_DOMAIN_AS_SOFT_BOOST.md`](01_DOMAIN_AS_SOFT_BOOST.md) | `domain` chỉ cộng điểm, không lọc cứng | Đã quyết, chưa code ở retrieval |
| [`02_END_TIME_ONGOING.md`](02_END_TIME_ONGOING.md) | Xử lý `end_time` / `ongoing` bị LLM gán sai | Đã quyết; ingestion và 3 cách chấm đã code; đo ở local: không cách nào hơn rõ (`eval/04` đợt 3) |
| [`03_PROMPT_CHANGELOG.md`](03_PROMPT_CHANGELOG.md) | Sổ thay đổi prompt kèm hiệu quả | Cập nhật liên tục |
| [`04_UNDATED_CHUNKS.md`](04_UNDATED_CHUNKS.md) | Chunk không có `start` và câu hỏi không nêu thời gian | Đã code; đo ở local cho thấy có lợi (`eval/04` đợt 4b), chờ xác nhận ở bộ thật |
| [`05_EXCLUDE_BEFORE_COMMON_ERA.md`](05_EXCLUDE_BEFORE_COMMON_ERA.md) | Loại chunk và câu hỏi có mốc trước Công nguyên | Đã quyết |
| [`06_END_UNKNOWN_REMEDIES.md`](06_END_UNKNOWN_REMEDIES.md) | Chunk `end_status = unknown` và mốc `start` sai (nguyên nhân chính của câu sai còn lại) | **Đề xuất, chưa quyết, chưa code** |
