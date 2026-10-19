# Nhật ký thay đổi prompt

Mỗi dòng: ngày, file prompt, đổi gì, vì sao, hiệu quả đo được (nếu có). Quyết định lớn có file riêng ở thư mục này; đây chỉ là sổ ghi để biết kết quả ở `docs/eval/` ứng với phiên bản prompt nào. Số liệu so sánh nhiều lần chạy phải kèm lưu ý: model phía sau combo `basic-llm` của 9router **thay đổi theo thời gian** (ngày 2026-10-19 một model bị ngừng và combo chuyển sang `gemini-3.1-flash-lite`), nên khác biệt giữa hai lần chạy không hoàn toàn do prompt.

## `src/tam/llm/prompts/ingestion_time.md` (gán mốc và domain cho chunk)

| Ngày | Đổi gì | Vì sao | Hiệu quả |
|---|---|---|---|
| trước 2026-10-19 | Cho phép lấy ngày từ chunk khác của trang; ba trạng thái của `end`; 5 ví dụ nhiều chunk | Chunk thiếu năm riêng bị bỏ oan | Chưa đo (`process/05` mục 3) |
| 2026-10-19 | Thêm trường `reason_end_date` (đặt trước `end`, `ongoing`) | Cần biết vì sao LLM suy ra `end`/`ongoing` | Phát hiện 42 chunk lý do tự mâu thuẫn với `ongoing` |
| 2026-10-19 | Thêm `domain` (danh sách đóng 8 + `other`, tối đa 3 nhãn), ví dụ gán nhãn tự đặt, mục "Output format" với JSON mẫu | Điểm cộng domain ở retrieval (decisions/01) | Nhãn có cho mọi chunk; 32/39 chunk đáp án khớp domain suy từ P (thước đo thô) |
| 2026-10-19 | Thêm `reason_domain` (trước `domain`) | Truy lại vì sao lệch nhãn | Cho thấy 7 ca lệch đều theo nội dung chunk; lệch nằm ở thước đo P→domain |
| 2026-10-19 | Thêm `ongoing_evidence` và siết quy tắc `ongoing` ("thiếu ngày kết thúc không phải bằng chứng") | `basic-llm` đặt `ongoing` bừa (decisions/02) | `ongoing` trên chunk đã nạp 170 → 35 |
| 2026-10-19 | Thử "bằng chứng nằm trong chính chunk", **đã gỡ** | Nghi `Casus_Belli` mượn câu của chunk khác; điều tra lại thì suy luận chéo chunk là đúng | Không áp dụng (xem decisions/02) |
| 2026-10-19 | Mốc trước Công nguyên: từ "coi như không có mốc" thành "viết năm âm"; parser chặn mọi năm < 1 về `0001-01-01` | 3 chunk `Zambia` bị `invalid_time` vì LLM trả `-2000`, `-300000`, `-150000` | Chưa chạy lại; mất thứ tự giữa các mốc trước Công nguyên |

### Dự kiến, chưa làm
- ~~Quy tắc ưu tiên "lĩnh vực của chủ thể hơn khía cạnh"~~ **bỏ** (2026-10-19): domain chỉ cộng điểm và gắn theo khía cạnh được hỏi, chunk được mang tới 3 nhãn gồm cả hai loại, nên không cần chọn một. Xem docs/eval/01 mục 3.
- Ghi nhận: `ingestion_time.md` có thời gian sửa 11:48 giữa lần 2 và lần 4 mà sổ này không có dòng tương ứng; nội dung thay đổi chưa dựng lại được. Từ nay mỗi lần đổi prompt phải ghi dòng ở đây trước khi chạy.

## `src/tam/llm/prompts/time_extractor.md` (Profiler)

Chưa đổi prompt. Phát hiện 2026-10-19: với `basic-llm`, các ví dụ dạng `semantic_query: ... | t_req: ...` khiến combo trả văn bản tự do thay vì JSON (40/40 câu lỗi). Xử lý bằng code (`tam/llm/structured.py`: đọc JSON từ văn bản, thử lại), không đổi prompt. Sau đó 0/40 lỗi.
