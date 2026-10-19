# Quyết định 06: chunk có `end_status = unknown` và mốc `start` sai

**Ngày:** 2026-10-19. **Trạng thái:** **đề xuất, chưa quyết, chưa code.** Ghi lại để chọn hướng khi quay lại cải thiện ingestion. Số liệu: [`../eval/04_TEST_RESULTS.md`](../eval/04_TEST_RESULTS.md) mục "Phân tích câu sai". Nền: [`02_END_TIME_ONGOING.md`](02_END_TIME_ONGOING.md).

## Vấn đề (đã đo)

Phương pháp tốt nhất ở bộ local (Cơ chế 1 (tìm kiếm dense) + `t_unknown`) vẫn sai 9/40 câu. Tra từng câu: **7/9 do mốc của chunk không đúng hoặc không đủ**, chỉ 2/9 do truy xuất ngữ nghĩa.

| Nhóm | Số câu | Gốc |
|---|---|---|
| A. Mốc `start` sai làm chunk đáp án bị lọc cứng loại | 2 | LLM ingestion gán `start` sai (chunk bắt đầu sau `t_req`, hoặc sai nhiều năm so với nhãn) |
| B. `end_status = unknown` bị điểm thời gian đẩy xuống | 5 | LLM không biết khi nào kết thúc; `to_span` coi như hết cuối kỳ của `start`; điểm TH2 giảm dần `exp(-0.5·số năm)` dù sự việc còn đúng ở `t_req` |
| C. Ngữ nghĩa yếu | 2 | Dense xếp chunk đáp án hạng 12 và 46 |

Đã thử cách chấm khác ở truy vấn: `open` (coi `unknown` còn hiệu lực mãi) và `decay`. Cả hai **không sửa được tổng thể**: `open` đẩy cả chunk đã thật sự hết hiệu lực lên (3 câu lên, 5 xuống). Lý do: ở chỗ chấm điểm không có thông tin nào để phân biệt chunk `unknown` còn đúng với chunk `unknown` đã hết hạn thật; thông tin đó phải đến từ ingestion hoặc từ cấu trúc (thứ tự chunk).

## Ảnh hưởng thiết kế

- `docs/design/02` (Temporal_Score: TH1 khi `t_req` trong `[start, end]`, TH2 giảm dần) giả định `end_time` đáng tin. Thực tế `end` thường là `unknown`, nên TH2 phạt oan. Nếu chọn hướng (b) hoặc (c) dưới đây thì bước 3 của design 02 phải ghi cách xử lý `unknown`.
- Hướng (b) dùng quan hệ "chunk kế tiếp của cùng thực thể" chính là cạnh trạng-thái-kế-tiếp của Cơ chế 2 (Timeline). Tức là Cơ chế 1 hưởng lợi từ một thứ vốn cần cho Cơ chế 2; nên thiết kế chung chứ không làm riêng hai lần.

## Các hướng đề xuất

| Hướng | Làm gì | Chi phí | Rủi ro | Trị được nhóm |
|---|---|---|---|---|
| (a) Chấm riêng `unknown` | Tách `unknown` khỏi `ongoing` khi chấm: `ongoing` giữ TH1 mãi, `unknown` giảm chậm (decay nhỏ) hoặc ngưỡng riêng. Thêm chế độ mới cho `end_mode` | Rẻ; chỉ sửa `scoring.py`, không nạp lại kho | `decay` và `open` hiện cho `mrr` không hơn `stored`; có thể chỉ dời lỗi sang chỗ khác | B |
| (b) Suy `end` từ chunk kế tiếp | Sau khi LLM xong cả trang, với chunk `unknown`: `end` = `start` của chunk kế tiếp có `start` sau nó và cùng nhãn domain (hoặc cùng thực thể). Cần thứ tự chunk trong trang | Vừa; xử lý sau ingestion (không gọi LLM thêm), kiểm thử được trên `extractions.jsonl` | Chunk kế tiếp có thể nói chuyện khác (nối nhầm); trang nhiều chủ đề; thứ tự đoạn không phải thứ tự thời gian | B |
| (c) Sửa prompt ingestion | Yêu cầu LLM suy `end` từ ngữ cảnh ("còn đúng đến mốc xa nhất mà văn bản hỗ trợ"; có trích dẫn câu như `ongoing_evidence`) | Phải nạp lại kho (khoảng 15 phút local, vài giờ bộ thật); đổi prompt phải ghi `03_PROMPT_CHANGELOG` | LLM bịa; đã thấy chúng hay đặt `ongoing` sai | B, một phần A |
| (d) Kiểm tra `start` | Thêm `start_evidence` (trích nguyên văn câu chứa mốc) và đối chiếu như `ongoing_evidence`; chunk không có bằng chứng thì hạ về không mốc (để nhánh `t_unknown` xử lý) | Vừa; đổi schema đầu ra LLM, nạp lại kho | Hạ nhầm chunk mốc đúng; không bắt được lỗi LLM tự tin nhưng sai | A |
| (e) Cải thiện xếp hạng ngữ nghĩa | Reranker (cross-encoder) hoặc model embedding lớn hơn `bge-small` | Tốn tính toán; độc lập với mốc | Tăng độ trễ | C |

## Gợi ý thứ tự

1. **(b)** trước: không tốn LLM, kiểm tra được ngay trên dữ liệu có sẵn bằng cách tính lại `end_time` rồi chạy lại đợt 3 trên bộ local. Mục tiêu: sửa được ít nhất 3/5 câu nhóm B mà không có quá 1 câu mới hỏng.
2. **(a)** làm cùng vì rẻ, so sánh với (b).
3. **(c)(d)** chỉ làm khi (b) không đủ, vì buộc nạp lại kho; gộp vào cùng lần nạp lại với bộ thật để tiết kiệm chi phí.
4. **(e)** làm riêng, sau.

## Điều cần đo nếu làm

- Cùng 5 câu nhóm B và 2 câu nhóm A: có lên top 5 không; số câu mới tụt.
- `mrr` và `hit@5` toàn bộ local (nền tìm kiếm dense + `t_unknown` 0.2) trước và sau.
- Xác nhận trên bộ thật (400 câu) vì local chỉ 5 câu nhóm B (sai số lớn).
