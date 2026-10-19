# Quyết định 01: `domain` chỉ cộng điểm, không lọc cứng

**Ngày:** 2026-10-19. **Trạng thái:** đã quyết; ingestion gán `domain` đã code; phần cộng điểm ở retrieval đã code (`w3`, `ProfiledQuery.domains`, mặc định tắt), **chưa chạy so sánh**.

## Bối cảnh

Design 02 mô tả `domain_features.domain` là bộ lọc cứng ("Faceted Pre-filtering", bước 2). Ingestion giờ do LLM gán 1 đến 3 nhãn `domain` cho chunk (xem `dataset/full_dataset/TOPICS.md`). Chạy thử bộ local (`docs/eval/01_LOCAL_INGESTION.md`): nhãn LLM của chunk đáp án khớp domain suy từ `relation` ở 31/39 chunk, các ca lệch phần lớn là nhãn LLM hợp lý theo nội dung.

## Vấn đề của lọc cứng

Lọc cứng cần **hai** lần gán nhãn cùng đúng: nhãn chunk (lúc ingestion) và nhãn câu hỏi (Profiler, lúc truy vấn), cả hai do LLM đoán. Chỉ cần một bên khác nhãn thì chunk đúng bị loại hẳn và không có cách cứu. Khác với `start_time <= T_req`, vốn là dữ liệu tất định.

## Phương án

| Phương án | Ưu | Nhược |
|---|---|---|
| Lọc cứng (design cũ) | Thu hẹp kho trước khi tìm; nhanh | Sai nhãn thì mất chunk đúng |
| **Cộng điểm (chọn)** | Sai nhãn chỉ mất một phần điểm, chunk đúng vẫn có mặt | Không thu hẹp kho: chunk đúng vẫn phải lọt top-N bằng điểm hybrid; kho rất lớn thì top-N có thể bị chunk cùng chủ đề khác domain chiếm chỗ |
| Lọc cứng có dự phòng (tìm lại không lọc nếu ít kết quả) | Nhanh khi nhãn đúng | Phức tạp hơn, cần ngưỡng "ít kết quả" |

Tốc độ không phải mối lo: tìm xấp xỉ (HNSW) tăng rất chậm theo số chunk. Mối lo là recall của top-N khi kho lớn.

## Quyết định

`domain` chỉ **cộng điểm**: `Final = W1·Semantic + W2·Temporal + W3·Domain_Match`, với `Domain_Match` = 1 khi nhãn câu hỏi nằm trong nhãn chunk, 0 nếu không (hoặc câu hỏi không có nhãn). `W3` nhỏ, tinh chỉnh sau. Điều kiện thời gian (`start_time <= T_req`, `invalidated_at IS NULL`) **vẫn lọc cứng** vì tất định.

- Chunk lưu `domain_features.domain` dạng danh sách; Profiler điền khi câu hỏi nêu rõ, còn lại để trống (không cộng điểm).
- Chỉ mục payload `domain_features.domain` vẫn giữ (bất biến "4 chỉ mục" không đổi) để còn chạy chế độ lọc cứng trong ablation.
- `country` chưa bàn tới, giữ như design cũ.

## Ablation sẽ chạy

Không dùng domain / lọc cứng / cộng điểm / lọc cứng có dự phòng. Bộ local chỉ ~1058 chunk nên khác biệt nhỏ; kết luận chỉ có sức nặng trên bộ lớn.

## Việc còn lại

- Sửa `retrieval/temporal` thêm `Domain_Match` và `W3` (config `retrieval.w3`), Profiler trả domain là danh sách đóng.
- `design/02` đã ghi chú (xem bước 2 mục 3 và bước 4).
