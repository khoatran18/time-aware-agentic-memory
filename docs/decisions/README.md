# Nhật ký quyết định thiết kế

Mỗi file ghi **một** quyết định: bối cảnh, các phương án, chọn gì và vì sao, ảnh hưởng tới design, trạng thái. Khác với `docs/process/` (nhật ký làm gì theo thứ tự thời gian) và `docs/design/` (thiết kế hiện hành): đây là nơi tra lại "vì sao thiết kế thành thế này" khi viết luận văn. Khi một quyết định đổi design, sửa `docs/design/` rồi trỏ về file ở đây.

| File | Quyết định | Trạng thái |
|---|---|---|
| [`01_DOMAIN_AS_SOFT_BOOST.md`](01_DOMAIN_AS_SOFT_BOOST.md) | `domain` chỉ cộng điểm, không lọc cứng | Đã quyết, chưa code ở retrieval |
| [`02_END_TIME_ONGOING.md`](02_END_TIME_ONGOING.md) | Xử lý `end_time` / `ongoing` bị LLM gán sai | Đã quyết; ingestion đã code, scoring chưa |
| [`03_PROMPT_CHANGELOG.md`](03_PROMPT_CHANGELOG.md) | Sổ thay đổi prompt kèm hiệu quả | Cập nhật liên tục |
| [`04_UNDATED_CHUNKS.md`](04_UNDATED_CHUNKS.md) | Chunk không có `start` và câu hỏi không nêu thời gian | **Đề xuất, chưa quyết** |
