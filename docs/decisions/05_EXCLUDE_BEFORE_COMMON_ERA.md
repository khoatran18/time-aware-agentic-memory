# Quyết định 05: loại mốc trước Công nguyên

**Ngày:** 2026-10-19. **Trạng thái:** đã quyết; không cần code thêm.

## Bối cảnh

Ở bộ local, 3 chunk `Zambia` (#7, #8, #12, nói về thời tiền sử) bị `invalid_time` vì LLM trả `-2000`, `-300000`, `-150000`. `datetime` của Python và payload Qdrant không biểu diễn được năm < 1.

## Phương án

| Phương án | Hệ quả |
|---|---|
| Chặn mọi năm < 1 về `0001-01-01` (đã thử rồi gỡ) | Chunk vào kho nhưng mất thứ tự giữa các mốc trước Công nguyên; điểm thời gian trong vùng đó vô nghĩa |
| Lưu năm âm bằng kiểu số | Phải đổi schema `start_time`/`end_time` sang số, kéo theo lọc Qdrant và công thức `Δyears`; quá lớn so với 1 đến 5 chunk bị ảnh hưởng |
| **Loại (chọn)** | Parser từ chối năm < 1 (`invalid_time`), prompt bảo LLM coi mốc trước Công nguyên là không có mốc |

## Quyết định

Chunk có mốc trước Công nguyên bị bỏ khỏi kho. Câu hỏi có nhãn thời gian trước Công nguyên bị loại khỏi bộ đánh giá; nếu bộ thật có, bù bằng câu từ `D/train`. Bộ local hiện không có câu nào như vậy (đã kiểm tra `time_start`/`time_end` của 40 câu). TimeQA chủ yếu là thời hiện đại nên mất mát nhỏ (1 đến 5 chunk trên 1275).
