# Câu hỏi v9 (Mechanism 2, Timeline Summarization)

Bản lưu của `local/questions/v9/` tại 2026-11-12 (checker `check_questions.py v9`: 0 lỗi; đã bỏ Butch_Levy:0 và Meg_Whitman:4, thêm e25 vào Sergio_P_rez:0 sau bước [1][2][3]). Mỗi trang một file `<Trang>.jsonl`, mỗi dòng một câu; id mốc (`gold_event_ids`, `group_event_ids`, `answer_ids`, `flagged_*`) tham chiếu gold cùng trang ở `../batch*/rev/<Trang>.json` (tune v1–v3: `../pilot5`, `../pilot10`, `../batch2`).

| Tập | Gold | Câu | Trang có câu |
|---|---|---|---|
| tune | `batch2..9`, `batchB*`, `pilot5`, `pilot10` | 638 | 179 |
| valid | `batchV*` | 556 | 154 |
| test_clean | `batchT/rev` | 665 | 173 (186 trang, 13 trang không có câu) |
| Cộng | | 1859 | 506 |

Loại câu (tune / valid / test_clean): `order_gap` 166 / 211 / 213, `first_last_next` 177 / 128 / 166, `list` 227 / 159 / 215, `summary` 68 / 58 / 71.

Đã làm: bước [1][2][3] (`chain_complete`, `chain_verify`, kiểm bằng mã) đã chạy xong cho cả ba tập (tune 213 nhóm, valid 346 nhóm, test_clean 452 nhóm; tune cũ có 90 trang chạy từ trước theo phiên bản câu cũ). Còn lại: chạy hệ thống trên test_clean. Câu có `flagged_ids` không rỗng nên báo điểm riêng. Gold chỉ để sinh và kiểm câu hỏi, không phải đáp án của hệ thống.
