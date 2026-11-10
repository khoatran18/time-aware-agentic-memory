# Bước [4]: giám khảo kiểm câu hỏi bằng LLM (đã viết bản thử `local/question_audit.py`, 2026-11-10; kết quả mục "Kết quả thử")

Mục đích: thay phần **đọc mù** các lỗi về nghĩa câu hỏi bằng một bước tự động, để người chỉ đọc các câu bị gắn "nghi". Không thay [1] (tìm mốc thiếu); [4] kiểm mốc **đã có** trong chuỗi. Người dùng hỏi (2026-11-10): có tự động hóa được thay vì cứ đọc mù không → đây là đề xuất; chưa chốt, chưa làm.

## Các lỗi đọc mù đã thấy mà mã không bắt được
- Mốc trong chuỗi không đúng loại sự kiện câu hỏi hỏi (v7: "từ chức" thay "bầu cử"); `criterion` hẹp hơn hoặc rộng hơn câu hỏi.
- Đếm đôi một sự kiện: Condor:3 (v8, e29 thông báo + e31 hoàn tất, vẫn còn trong v8), Steele_Hall:3 (đã bỏ), Chicago_Red_Stars (v7n).
- Câu hỏi hỏi nhiều hơn đáp án lưu ("first, and which...": Werner_Hartmann:4 của v8 còn lại; Veliky_Novgorod:2 và Lenin_Peak:3 của v9 đã sửa chữ).
- Quy tắc 2 của luật cờ: mốc cờ B "cùng loại với `criterion`" hay không (`local/flag_rules.py` báo 10 câu ứng viên trên v8+v8n bằng track/label, đọc tay thì 0 vi phạm thật).

## Thiết kế đề xuất
- Một lời gọi DeepSeek mỗi câu (cùng số lời gọi cỡ [1]: 160–440 cho cả bộ). Đầu vào: câu hỏi, `criterion`, `subtype`/`answer_ids` (với `first_last_next`), từng mốc trong chuỗi (id, ngày, text, quote, cờ), tùy chọn đoạn chunk quanh quote, mốc cờ gần chuỗi (từ `flagged_nearby_ids` hoặc tính bằng mã).
- Đầu ra có cấu trúc: mỗi mốc "thỏa nghĩa đen câu hỏi" (có/không + lý do); các cặp nghi cùng một sự kiện; câu hỏi có hỏi nhiều hơn đáp án lưu không; `criterion` có khớp câu hỏi không; với mỗi mốc cờ gần chuỗi: "cùng loại với `criterion`" có/không; nhãn tổng `ok` hoặc `nghi` kèm loại.
- Chi phí chữ vào: [4] khoảng 1.200 ký tự/lời gọi (ước lượng cho v9, chưa tính đoạn chunk) so với [1] khoảng 17.500 ký tự (trang v9 trung bình), tức khoảng 5–15% chữ vào của [1] (ước lượng theo ký tự, chưa tính tiền; log cũ không có token, bộ đo `src/tam/llm/metrics.py` mới sẽ ghi được).

## Cách kiểm chứng giám khảo (bắt buộc trước khi tin)
- Chạy [4] trên các câu **đã có nhãn đọc mù** (v7n, v8n, mẫu v9; vài chục câu, khoảng 10–15 câu lỗi nhẹ đã biết, cộng Condor:3 và Werner_Hartmann:4). Đo: bắt được bao nhiêu lỗi đã biết, báo oan bao nhiêu. Chỉ dùng cho cả bộ nếu bắt được phần lớn và ít báo oan.
- Giám khảo cũng có thể sai (bỏ sót hoặc báo oan); vẫn cần người đọc một mẫu nhỏ để ước lượng recall.

## Việc sắp làm
1. ~~Viết `local/question_audit.py`~~ **Đã viết (2026-11-10).**
2. ~~Thử trên mẫu có nhãn đọc mù~~ **Đã thử trên v8, v9, v8n (mục "Kết quả thử").**
3. Chưa làm: quyết có dùng [4] như bộ lọc sơ bộ cho bộ chính hay thử thêm (hai hướng ở cuối mục "Kết quả thử"); đọc tay các câu bị gắn nghi; dùng `chain_apply.py` áp các quyết định bỏ câu khi người dùng chốt.

## Kết quả thử (2026-11-10; số liệu đầy đủ ở `docs/eval/10` mục 10.5aw)
- **Cài đặt:** `local/question_audit.py <repo> <out_dir> <set|set:Trang|set:Trang:q>...` (`DRY=1` đo cỡ đầu vào, `CTX` đổi độ rộng ngữ cảnh, mặc định ±350 ký tự quanh quote). Một lời gọi DeepSeek mỗi câu (`deepseek_flash`), đầu ra có cấu trúc (`Audit`: mỗi mốc có thỏa nghĩa đen, cặp nghi cùng sự kiện, hỏi nhiều hơn đáp án, `criterion` khớp, nhãn ok/nghi + mã lỗi `wrong_kind`/`double_count`/`asks_more`/`criterion_mismatch`/`other`). Phần đầu prompt cố định (quy tắc, mã lỗi, 6 ví dụ bịa) đặt trước nội dung từng câu để hưởng cache tiền tố của DeepSeek. Cache cục bộ riêng `local/question_audit/cache.jsonl` (khóa = hash prompt hệ thống + nội dung câu; **đổi prompt thì mất hết**; `SqliteCache` của dự án không dùng được từ nhiều luồng nên không dùng); kết quả ghi dần vào `verdicts.partial.jsonl`; `verdicts.jsonl` khi xong cả lô; kết quả các lần thử ở `local/question_audit/t1`–`t9`.
- **Đã bỏ khỏi LLM:** phần "mốc cờ gần chuỗi" (lần chạy đầu: 12 trên 16 cảnh báo là `flag_same_kind`, đa số báo oan, nhiều mốc `derived_date` mà luật cờ đã chốt chưa tính). Việc đó nên làm bằng mã (`local/flag_rules.py`).
- **Bắt được:** Werner_Hartmann:4 (`asks_more`), Mercury:3 (`double_count`), Sirotkin:4 (v8n, `wrong_kind`), Humongous:1 (v9, `wrong_kind`). **Bỏ sót:** Condor:3 (kể cả sau khi thêm quote, ngữ cảnh và ví dụ "thông báo + hoàn tất"), Rezidor:3, Lenin_Peak:4, Hugh_Scott:4, Atlanta_Dream:1, John_Franklin:4, Real_Madrid:3. Theo danh sách đọc mù: bắt 1/2 lỗi chắc của v8, 2/10 theo đúng lý do.
- **Báo oan lặp lại:** nó gắn `double_count` cho cặp mốc không nằm trong đáp án (Maidan:5, Arnulf:2, Shackleton_Bailey:2, Rams:5), tức chưa biết đáp án nào được lưu quan trọng; và khắt khe quá về "loại" (Stefan_He_e:2).
- **Thêm quote và ±350 ký tự chunk:** làm số cảnh báo giảm và giúp thấy bằng chứng yếu (Vindobona:2), nhưng không tăng recall.
- **Chi phí:** 166–276 câu mỗi lượt, 465–780 nghìn token vào, 28–48 nghìn token ra, 63–110 giây. Cả v8 + v9 + v8n (≈ 640 câu) cần chạy lại sau khi đổi prompt vì cache cục bộ trượt.
- **Việc có thể làm tiếp (chưa làm):** (1) hỏi từng mốc "thuộc đúng loại X không" (khoảng 660 lời gọi cho v8; cần ước lượng chi phí trước); (2) vòng hai chỉ cho cặp mốc cùng/ gần năm hỏi "có phải một sự kiện không" (nhắm Condor:3), và chỉ xét cặp nằm trong đáp án; (3) dùng [4] như bộ lọc sơ bộ, đọc tay các câu bị gắn nghi; (4) thử mô hình mạnh hơn cho riêng [4].
- **Hiện dùng được ở mức:** bộ lọc sơ bộ (cảnh báo rõ ràng về chữ: hỏi nhiều hơn đáp án, hai mốc cùng nội dung, mốc không phải sự kiện), không thay đọc mù.

