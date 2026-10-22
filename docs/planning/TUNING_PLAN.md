# Kế hoạch tune theo đợt (ghi 2026-10-21)

Mục tiêu: chọn cấu hình cuối mà không tune trên tập báo cáo. Tập dùng: `tune` (tìm), `valid` (xác nhận), `test_clean` (một lần), `real` (đã xem, chỉ mô tả và kiểm tra hợp lý). Quy ước chung cho mọi đợt:

- Chỉ số chính `mrr`; phụ `hit@1`, `hit@5`, `ans_valid@5`, `leakage_rate`; luôn so ghép cặp theo câu với cấu hình đối chứng, báo sai số chuẩn.
- Chọn bằng quy tắc một sai số chuẩn: trong các cấu hình cách cấu hình tốt nhất không quá một sai số chuẩn ghép cặp, lấy cái đơn giản nhất.
- Mỗi đợt giữ lại top 3 và 2 cấu hình đa dạng (không chỉ top 1), vì tương tác giữa tham số có thể làm cấu hình cũ tệ trở nên tốt khi thêm cơ chế mới.
- Khi thêm một cơ chế mới, mở lại 2 đến 3 tham số gắn chặt với nó quanh vùng tốt (ví dụ cross-encoder: `w2`, cỡ nhóm chấm lại, `decay_lambda`), không chỉ so với cấu hình cũ.
- Cache điểm cross-encoder và cache LLM nên giữ; không xóa.

## Đợt 0. Khóa nền (không tốn LLM)
Chốt định nghĩa chỉ số, cách chọn, phân bố các tập (xong: `decisions/08`). Cấu hình đối chứng: Plain RAG (dense), Plain RAG + cùng cross-encoder, Cơ chế 1 không cross-encoder.

## Đợt 1. Prompt (tốn LLM, làm TRƯỚC vì đổi prompt là đổi nhãn của cả kho)
| Mục | Ứng viên | Tập | Cách đo | Chi phí |
|---|---|---|---|---|
| Prompt ingestion | v3 (hiện tại), v4 (luật nguồn của `end`, xử lý lô bị chặn nội dung) | một phần tune (~60 trang, ~85 lô) | cấu hình truy xuất cố định (nền hiện tại + MiniLM-L12), so ghép cặp `mrr`, `ans_valid@5`, tỉ lệ nhãn (`known`/`unknown`/`ongoing`) | ~85 lô mỗi ứng viên |
| Prompt Profiler | v2 (hiện tại), một ứng viên v3 | tune (400 câu) | `t_req_in_label_range`, `t_req_abs_error_years`, rồi `mrr` | 400 request mỗi ứng viên |

Chỉ nạp lại toàn bộ tune, valid, test bằng prompt mới nếu ứng viên hơn vượt sai số (hạn mức Gemini miễn phí: ~560 lô). Đầu ra giữ lại: prompt đã chốt và kho tương ứng.

## Đợt 2. Tham số điểm thời gian với cross-encoder (không LLM)
- Model thay thế để tune: MiniLM-L12 (nhanh); sau đó xác nhận trên L6 và bge-v2-m3.
- Cố định (đã khảo sát, mục 6.19): dense, `replace`, nhóm `final`, min-max, không ghép thời gian, không BM25.
- Tìm kiếm ngẫu nhiên 60 đến 100 tổ hợp trên `tune`: `w2` ∈ {0.15, 0.3, 0.4, 0.5, 0.6}, `decay_lambda` ∈ {0.25, 0.5, 1, 2}, `end_mode` ∈ {`unknown_decay` 0.02/0.05/0.1, `stored`}, `decay_from` ∈ {`end`, `start`}, `t_unknown` ∈ {0.05, 0.1, 0.2, 0.3}, cỡ nhóm chấm lại ∈ {10, 20, 30}.
- Loại sớm: chạy 150 câu đầu, giữ nửa tốt nhất rồi chạy hết 400 câu.
- Đầu ra: top 3 + 2 cấu hình đa dạng.

## Đợt 3. Cơ chế bổ sung, từng cái một (không LLM)
Mỗi cái so với đầu ra đợt 2, rồi mở lại `w2` và `decay_lambda` quanh vùng tốt: chunk liền kề w = 0, 1, 2, 3 (ngữ cảnh, báo riêng và áp cho cả Plain RAG), chế độ `range`, mốc suy từ chunk liền kề, BM25 (đã âm), cùng trang (đã âm). Chỉ giữ cái nào hơn vượt sai số.

## Đợt 4. Ba mức model (không LLM)
Cho từng mức (L6 nhanh, L12 cân bằng, bge-v2-m3 chất lượng): tune nhẹ `w2`, cỡ nhóm, `decay_lambda` quanh đầu ra đợt 2/3. Đo độ trễ dưới tải. Đầu ra: 1 cấu hình mỗi mức, 3 cấu hình + cấu hình đơn giản không cross-encoder + Plain RAG + Plain RAG + cross-encoder làm đối chứng.

## Đợt 5. Xác nhận trên `valid` (không LLM nếu valid đã nạp)
Chỉ 5 đến 8 cấu hình (đầu ra đợt 4 + đối chứng). So ghép cặp, quy tắc một sai số chuẩn. Làm các thí nghiệm tắt-mở cho luận văn (bỏ `Temporal`, bỏ cross-encoder, bỏ lọc cứng) để có bảng đóng góp từng thành phần. Khóa cấu hình, ghi vào `configs/`.

## Đợt 6. Cổng đầu-cuối (tốn LLM sinh câu trả lời)
EM/F1 với bộ sinh cố định trên `valid` cho 3 mức + Plain RAG + Plain RAG + cross-encoder, cùng ngân sách token, rồi chọn kích thước ngữ cảnh (top-k và chunk liền kề). Mới biết chênh lệch `mrr` có làm câu trả lời đúng hơn không.

## Đợt 7. Test sạch, MỘT lần
`test_clean` với cấu hình đã khóa (và các đối chứng), báo micro và macro, khoảng tin cậy bootstrap, lớp 177 câu trang mới riêng; không tune lại sau đợt này. Thêm EM/F1 đầu-cuối trên test.

## Thứ tự và phụ thuộc
Đợt 1 phải xong trước đợt 2 nếu đổi prompt (đổi nhãn). Nếu giữ v3 thì đợt 2 có thể bắt đầu ngay khi `tune` nạp kho và có Profiler. Các đợt 2 đến 5 không dùng LLM nên không bị hạn mức chặn.

## Vấn đề kỹ thuật đã gặp (2026-10-21, để tránh lặp lại)

- **Lệnh gọi LLM không có giới hạn thời gian** làm Profiler và nạp kho treo hơn 30 phút khi một kết nối Google bị treo (CPU 0%, bộ nhớ đệm gần như không tăng). Đã thêm `timeout: 90` (giây) cho profile `google_35` và `google_31` (`providers/google.py`, tùy chọn).
- **`pkill -f <chuỗi>` giết chính shell** nếu chuỗi cũng nằm trong lệnh đang chạy (đã gặp ba lần, mã thoát 144). Luôn kill theo PID.
- **Gemini `503 UNAVAILABLE`** (quá tải phía Google) làm Profiler rất chậm: 54 câu trong ~45 phút. Không phải quota (quota là 429). Thử lại vào lúc khác hoặc đổi profile.
- **Lô bị chặn nội dung** (`PROHIBITED_CONTENT`, trả rỗng): không phải lỗi quota. Script làm nóng cache phải phân biệt hai trường hợp (đã sửa trong `local/scripts/warm_ingest_cache.py`: chỉ dừng khi 3 lô liên tiếp lỗi).
- **Hạn mức ngày** google_35 (500 request) đã hết lúc ~23:35; nạp kho `tune` còn khoảng 170 lô. Reset khoảng 14:00 giờ VN.
- **Nhiệt độ** CPU chạm 97 đến 99°C khi chạy 5 đến 8 tiến trình `evaluate.py`; mỗi tiến trình dùng 4 đến 5 nhân. Dùng `local/scripts/thermal_guard.sh` (tạm dừng khi 100°C ba phút liên tiếp) và giữ tối đa 3 tiến trình song song.
- **GPU** (RTX 3050 6 GB) có nhưng driver NVIDIA chưa nạp (không có module kernel `nvidia` cho kernel 7.0.0-38); onnxruntime hiện chỉ CPU. Bỏ qua tạm.
