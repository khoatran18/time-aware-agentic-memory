# 15. Bộ chấm câu hỏi v9 và kiểm câu hỏi bằng "chunk đúng" (không qua truy xuất)

**Trạng thái (2026-11-13):** hai điều đã chốt (cách ghép ngày, `summary` chấm như `list`); phần còn lại là cách làm đã dùng và đề xuất, chưa chốt.

Bối cảnh: câu v9 (`dataset/eval/timeline_pilot/questions_v9/`, 1857 câu) là câu của Cơ chế 2 và chưa có bộ chạy hay bộ chấm riêng. Các bộ cũ (`generate_answers.py`, `answer_v1..v4.md`, `metrics_timeline.score_answer`) viết cho câu TimeQA (đáp án đơn) hoặc bộ câu cũ có `gold_answer`. Chi tiết số liệu và từng câu: `docs/pending/03_EVAL_AND_DATA_OPEN.md` mục 4f đến 4j.

## 1. Đã chốt (người dùng, 2026-11-12)

- Ghép mốc dự đoán với mốc chuẩn theo ngày; **khi một bên chỉ có năm thì khớp nếu năm trùng**.
- **`summary` chấm giống `list`** (nêu đủ các mốc, theo thứ tự ngày; mốc cùng ngày thứ tự nào cũng được).
- Không gọi API khi chưa hỏi; mỗi lần cho phép có phạm vi cụ thể (ở đây: OpenCode DeepSeek, tune, mọi lần gọi qua cache `data/llm_cache/lvl1/`).

## 2. Đáp án chuẩn và bộ chấm (`local/v9_score.py`, gitignored)

| Loại | Đáp án chuẩn | Câu trả lời của hệ thống |
|---|---|---|
| `order_gap` | \|năm sau − năm trước\| của hai mốc trong `gold_event_ids` | một số nguyên |
| `first_last_next` | các mốc trong `answer_ids` (1 hoặc 2) | danh sách `{date, text}` |
| `list`, `summary` | các mốc trong `gold_event_ids` theo ngày | danh sách `{date, text}` |

Điểm: precision, recall, f1, order (chỉ cặp khác ngày), exact; `order_gap` chỉ có exact. Mốc cùng ngày tương thích được ghép theo độ trùng từ khóa của `text`. Tự kiểm (`python3 -I local/v9_score.py . selftest`, không gọi LLM): đáp án oracle ra 100% ở cả 1857 câu (kể cả khi đảo thứ tự mốc cùng ngày và khi chỉ trả năm); bỏ một mốc, đảo thứ tự, thêm mốc lạ, sai số năm đều bị trừ điểm đúng. Không có câu `order_gap` nào băng qua trước Công nguyên.

Giới hạn đã thấy: gold gộp hai giải cùng năm thành một mốc thì LLM tách hai bị trừ precision (Daniel_M_Fleetwood:1).

## 3. "Chunk đúng" (không phải Cơ chế 1 hay 2)

Với mỗi câu, đưa LLM đúng các chunk bằng chứng của mọi mốc trong chuỗi (`group_event_ids` hoặc `gold_event_ids`) và hỏi lại câu hỏi. Mục đích: **bắt câu hỏi mơ hồ hoặc sai**, không đo hệ thống. Đây là **cận trên**: LLM thấy đúng các chunk của chuỗi nên dễ hơn hệ thống tự truy xuất. Prompt: `local/prompts/answer_v9_lvl1.md` (tiếng Anh; "the timeline" nghĩa là các sự kiện có ngày mà đoạn văn nêu; ngày ghi chính xác như văn bản; theo sát cửa sổ và loại trừ của câu).

Cơ chế 1 chỉ áp cho câu truy xuất tại một thời điểm và có bộ riêng (TimeQA); câu v9 không dùng để đo Cơ chế 1. Phương án so sánh cho Cơ chế 2 (theo `decisions/10`): vector top-k, cả trang, chuỗi oracle (graph chưa có mã trong `src/tam`).

## 4. Kết quả 100 câu tune (opencode_deepseek_flash)

Exact: order_gap 25/25, first_last_next 24/25, list 20/25, summary 20/25 (F1 0,98 / 0,96 / 0,98). 11 câu chưa đạt; 6 do câu hỏi hoặc gold (đã sửa 5 câu và giữ Fort_Tilden:1 vì mốc đã cờ `approximate_date`), 5 do LLM hoặc mơ hồ nhỏ. Chi phí khoảng $0,09 (token ra 116 nghìn, gấp khoảng 5 lần ước tính). So với bài báo (TLQA golden F1 0,88 đến 0,93; ECT-QA LLM-GT 90,2%): cùng mức cận trên, khác bộ dữ liệu, LLM và cách chấm nên không gộp một bảng.

## 5. Luật sửa lời câu hỏi rút ra

- Không viết năm trùng với năm của một mốc gold vào lời hỏi (checker báo lỗi). Cần neo cửa sổ thì dùng mốc sự kiện ("after X began ...").
- Cụm "early/mid/late <thập niên>" phải khớp cận cửa sổ (early 0–3, mid 4–6, late 7–9); nếu gold hoặc cửa sổ kéo ra ngoài thì sửa lời, không sửa gold.
- Tiêu chí phải nói đúng chiều của sự kiện (báo là bên mua hay bị mua).
- Mốc chỉ có "by <năm>", "at least <năm>" là cận, không phải ngày xảy ra: `at least` thành `approximate_date` (đã cờ); `by <năm>` chưa có cờ, **đề xuất** bỏ câu `order_gap` phụ thuộc trực tiếp vào năm đó (ACES_Colombia:3, Richard_Sanderson_MP:3), giữ câu `list` và ghi nhóm riêng. Chưa chốt.

## 6. Cập nhật 2026-11-13 (sau khi chạy valid, test_clean và 15 câu sửa)

- Đã chạy chunk đúng cho cả ba tập (tune 638, valid 555, test_clean 662 lượt, cộng 15 lượt chạy lại câu đã sửa). Ghi chú chi tiết: `pending/03` mục 4k.
- Sửa quy ước bộ chấm: ngày dạng khoảng có tên tháng lấy mốc đầu; tên tháng viết tắt ("Oct", "Sept") đọc được; mùa giải "YYYY–YY" khớp năm đầu hoặc năm sau (chỉ với gold chỉ-năm); thêm chỉ số bổ sung `exact_m2o` (mốc chuẩn gộp nhiều việc được khớp nhiều mốc dự đoán cùng ngày; không bao giờ thấp hơn `exact`). `exact` vẫn là số chính.
- Bảng điểm chính thức: `python3 -I local/lvl1_report.py .` (không gọi LLM) ghép kết quả đã lưu với v9 hiện tại theo (trang, lời hỏi), chấm lại với gold hiện tại, ghi `local/lvl1/report_final.txt`. Số hiện tại (1850 câu, đủ 1850 có kết quả, exact; `exact_m2o` trong ngoặc): order_gap 0,998; first_last_next 0,964; list 0,901 (0,909); summary 0,883 (0,903); F1 0,973 đến 0,978. Câu có `flagged_ids`: list 0,875 (n=32), summary 0,875 (n=8). Mức này là trần (chunk đúng, không truy xuất) và đã chọn lọc vì các câu lỗi rõ đã bị sửa hoặc bỏ nên không so trực tiếp với số trước khi sửa.
- Bổ sung 2026-11-13 (người dùng cho phép): chạy nốt 7 câu chưa có kết quả cho đúng lời hỏi hiện tại (Archaeologia_Cambrensis:1, Lower_Norrland_Military_District:1, Real_Madrid_Baloncesto:0, The_Mercury_News:0, Vindobona_train:1, Alemannia_Aachen:0, D_R_Shackleton_Bailey:4) bằng `opencode_deepseek_flash`, 7 lượt, 39 giây, 0 lỗi, kết quả `local/lvl1/run_fix7/`; cả 7 đạt (list 4/4, summary 3/3). Nay 1850 câu đều có kết quả cho lời hỏi hiện tại.
- Gold `Dom_2` e44, e56, e63, e71, e75, e79 (Man of the Year for the Official Website): đã đối chiếu lại, năm và người thắng đầu khớp nguyên văn, không sai. e56, e71, e75 là đồng hạng mà gold chỉ ghi một người, nên nếu sinh câu chỉ dùng e44, e63, e79. Không động vào `rev/`; không câu v9 nào dùng nhóm này.

## 7. Việc còn lại

- Mức truy xuất thật (vector top-k, cả trang, chuỗi oracle) chưa chạy; cần chốt và hỏi chi phí trước. Mốc có `flagged_ids` đã báo riêng ở mục 6.
