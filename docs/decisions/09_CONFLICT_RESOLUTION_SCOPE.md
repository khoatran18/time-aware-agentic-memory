# 09. Phạm vi Cơ chế 3 (Conflict Resolution): bỏ đa nguồn, làm Evolution và Falsehood

**Trạng thái:** Đã quyết về phạm vi; dữ liệu và code chưa làm.

## Bối cảnh

Cơ chế 3 trong scope gồm hai nhánh: (a) xung đột đa nguồn, ưu tiên nguồn uy tín (Credibility); (b) tiến hóa và đính chính thông tin theo thời gian (Evolution ≠ Falsehood, Belief Revision). Nhánh (a) cần hai nguồn mâu thuẫn nhau tại cùng một mốc thời gian; hiện không có benchmark công khai phù hợp và chưa đủ thời gian tự xây dựng.

## Quyết định

- **Bỏ nhánh đa nguồn** và cơ chế Credibility Score. Ghi vào phần hạn chế của luận văn, không cam kết trong phiếu giao nhiệm vụ.
- **Giữ Cơ chế 3 ở nhánh (b):** đóng `end_time` khi thông tin tiến hóa, đặt `invalidated_at` khi thông tin sai từ đầu, cạnh `SUPERSEDES`/`CORRECTS`, `SUSPECTS` cho cáo buộc.
- Dữ liệu đánh giá tự tạo từ lịch sử Wikidata/Wikipedia (xem dưới).

## Kế hoạch dữ liệu và câu hỏi đánh giá (chưa làm)

**Tạo dữ liệu**
- Nhãn đáp án lấy từ **lịch sử Wikidata** (giá trị thuộc tính, `start_time`, `end_time` của đáp án cũ và mới), không để LLM đọc diff Wikipedia. Wikipedia chỉ cung cấp văn bản nạp kho.
- Dựng nhiều snapshot của cùng một trang (S0 cũ, S1 mới); nạp S0 rồi S1 để mô phỏng luồng cập nhật.
- Ưu tiên thuộc tính hay đổi, đã có nhiều trong TimeQA: P54 (đội bóng), P39 (chức vụ), P108 (nơi làm việc), P488 (chủ tịch).
- Quy mô dự kiến: khoảng 100–150 cặp S0/S1.
- Mốc thời gian của chunk lấy theo thời điểm sự kiện (từ Wikidata), không lấy theo ngày chỉnh sửa Wikipedia.

**Các loại câu hỏi**

| # | Loại | Ví dụ | Đáp án đúng | Đo |
|---|---|---|---|---|
| 1 | Hiện tại sau cập nhật | "Hiện nay ai là chủ tịch CLB X?" (sau S1) | Giá trị mới | Temporal Freshness (EM) |
| 2 | Lịch sử sau cập nhật | "Năm 2015 ai là chủ tịch CLB X?" (sau S1) | Giá trị cũ | Đóng `end_time` mà không mất lịch sử |
| 3 | Chuyển tiếp | "Ai kế nhiệm A?", "A rời vị trí khi nào?" | Giá trị mới hoặc mốc thay đổi | Đồ thị tiến hóa |
| 4 | Đính chính (sai từ đầu) | Hỏi về thông tin đã bị sửa vì ghi sai | Giá trị đã sửa, kèm cảnh báo | `invalidated_at` |
| 5 | Đối chứng không đổi | Thuộc tính không đổi giữa S0 và S1 | Giữ nguyên | Tỉ lệ đóng nhầm, xử lý hash trùng |
| 6 | Thăng tiến, không phải mâu thuẫn | "Năm 2010 làm gì?", "Năm 2018 làm gì?" | Cả hai đều còn đúng | Timeline ≠ Conflict |

Loại 1 và 2 luôn đi thành cặp: thiếu loại 2 thì hệ luôn trả "mới nhất" vẫn đạt điểm freshness.

**Chỉ số tổng hợp:** Freshness accuracy (loại 1), Historical retention (loại 2), False-invalidation rate (loại 5, 6), độ chính xác phân loại Evolution và Falsehood (loại 3, 4). Chạy thêm một lượt không có ngữ cảnh để biết LLM tự biết đáp án (xem hạn chế bên dưới).

## Hạn chế đã biết (ghi vào luận văn)

1. **Không có xung đột đa nguồn.** Không đánh giá được việc chọn nguồn theo độ tin cậy; hệ thống chỉ xử lý mâu thuẫn theo trục thời gian trong cùng một nguồn.
2. **Loại 4 (đính chính) khó lấy từ Wikipedia.** Lịch sử sửa lỗi lẫn nhiều vandalism và chỉnh sửa văn phong. Hướng xử lý: lọc thủ công một bộ nhỏ (vài chục cặp) hoặc chèn đoạn đính chính vào S1; trong cả hai trường hợp phải ghi rõ đây là dữ liệu bán tổng hợp.
3. **Nhiễm tri thức tham số.** LLM đã biết sẵn nhiều nội dung Wikipedia nên có thể đúng mà không cần kho, làm điểm freshness cao giả. Giảm bằng lượt đo không ngữ cảnh và ưu tiên thay đổi sau mốc kiến thức của LLM.
4. **Quy mô nhỏ**, do chi phí gọi LLM cho ingestion; kết quả mang tính kiểm chứng ý tưởng.

## Liên quan

- Metric `Temporal Freshness` đặt ở `metrics_conflict.py` (chưa có); đo được chỉ ở Cơ chế 3, không đo được ở Cơ chế 1 và 2.
- Ảnh hưởng tới phiếu giao nhiệm vụ: bỏ "xử lý xung đột đa nguồn", ghi "Evolution và Falsehood" ở Cơ chế 3.
- Scope: `docs/scope/01_PROJECT_SCOPE.md` (mục 1 và 2); kế hoạch: `docs/planning/00_OVERALL_PLAN.md`.
