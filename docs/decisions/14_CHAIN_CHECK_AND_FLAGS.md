# 14. Kiểm chuỗi đáp án [1][2][3], cờ trong gold và precision ingest

**Trạng thái (2026-11-09):** một điều **đã chốt** (precision ingest bỏ qua mốc không ngày). Mọi điều còn lại là **đề xuất**, chưa chốt và chưa code, trừ phần tách trạng thái `derived_pending` (đã sửa `local/chain_verify.py`). Số liệu của một người đọc.

Bối cảnh và số liệu chi tiết: `docs/eval/10_TIMELINE_DATASET_DESIGN.md` (10.5ar đến 10.5au). Quyết định dùng prompt v8: `13_QUESTION_GENERATION_V8.md`.

## 1. Đã chốt

- **Precision ingest bỏ qua sự kiện không ngày** (`date = None`): không tính đúng, không tính sai. Các số precision cũ (bản 9, tập C) tính cả 14 mốc không ngày vào mẫu số; tính lại với mẫu số 197: chặt 67,0%, vừa 79,2%, rộng 100% (số cũ: 62,6%, 73,9%, 93,4%).
- Bộ chính là v8 + v8n; v7 và v7n chưa cần sửa chuỗi (người dùng, 2026-11-09).
- **Luật cờ trong câu hỏi: mức 2 = quy tắc 1 + quy tắc 2** (mục 4; người dùng chốt 2026-11-09). Độ lệch ±2 năm vẫn là giả định chưa đo. Việc viết prompt v9 và sửa checker: `docs/pending/01_QUESTION_PROMPT_V9.md`.

## 2. Sơ đồ các tầng gán trạng thái

```mermaid
flowchart TD
    Q["Câu hỏi + chuỗi đáp án"] --> A["[1] DeepSeek đọc cả trang: ứng viên (chunk, date, quote, text, recorded_id, derived)"]
    A --> M{"Mã của [1] gán trạng thái, theo thứ tự"}
    M -->|"quote không nằm nguyên văn trong chunk"| S1["quote_not_in_chunk: bỏ, không qua giám khảo"]
    M -->|"quote đúng, chuỗi năm không có trong quote hay chunk"| S2["year_not_in_chunk"]
    S2 --> P1["pending_year_in_other_chunk (năm có ở chunk khác)"]
    S2 --> P2["pending_year_nowhere (năm không có ở đâu)"]
    P1 --> PF["derived_pending.jsonl: chưa có bước kiểm derived"]
    P2 --> PF
    M -->|"còn lại"| S3["excluded_on_purpose / in_gold_not_in_group / undated_only / new_not_in_gold"]
    S3 --> J["[2] giám khảo, chỉ đọc chunk của ứng viên"]
    J --> C["[3] mã kiểm: quote và năm trong chunk, trùng gold, trùng undated"]
    C --> F["nhãn cuối trong verdicts.jsonl"]
    F --> H["người đọc kết luận: thêm id vào chuỗi / bỏ câu + ghi extras / không đổi"]
```

Nhãn cuối (thứ tự quyết định): quote hoặc năm không có trong chunk → `reject_code`; trùng mốc trong chuỗi → `duplicate_in_chain`; trùng mốc gold ngoài chuỗi → `duplicate_of_gold`; trùng `undated_mentions` → `duplicate_of_undated`; giám khảo chấp nhận, ngày rõ cùng câu → `auto_accept`; chấp nhận nhưng ngày không cùng câu → `derived_candidate`; `reject` → `reject`; còn lại → `human`. `auto_accept` và `derived_candidate` chỉ là nhãn, chưa bước nào thực thi.

Đối chiếu số ứng viên (đọc tay bằng mã): v7n_1 29 = 22 qua giám khảo + 6 pending + 1 `quote_not_in_chunk`; v8n_1 19 = 17 + 1 + 1. Chạy kiểm `LIMIT=1` trên `v7n_1`: 6 ca pending được tách đúng như đọc tay (2 `nowhere`, 4 `in_other_chunk`), chỉ 1 ca đi qua giám khảo; 21 ca giám khảo còn lại không chạy lại.

## 3. Hành động sau nhãn (đề xuất)

| Mốc [1] báo | Câu hỏi | Ghi vào |
|---|---|---|
| Có trong gold, ngoài chuỗi, thỏa tiêu chí | thêm id vào chuỗi, tính lại `answer_ids` | chỉ đáp án |
| Không có trong gold, ngày rõ cùng câu | bỏ câu (hướng b) | `extras` |
| Không có trong gold, ngày suy ra đã kiểm | bỏ câu nếu nằm trong khoảng chuỗi và thỏa tiêu chí | `extras` kèm cờ `derived` |
| Gold chỉ để ở `undated_mentions` nhưng văn bản có ngày rõ | như dòng 2 | `extras` |
| Không có ngày rõ, không có trong `undated_mentions` | không đổi | không ghi (`verdicts.jsonl`) |
| Trùng gold, trùng undated, trùng chuỗi | không đổi | không ghi |

Bước gộp, kiểm derived và ghi `extras` chưa viết. Kết quả thực tế trên bộ chính (v8, v8n): 0 ca cần sửa.

## 4. Cờ trong gold và câu hỏi (đề xuất)

Gold có 11.980 mốc trên 355 trang: 1165 `derived_date`, 389 `approximate_date`, 156 `source_inconsistent` (73 trang). Cờ `source_inconsistent` gộp ít nhất ba loại mâu thuẫn: ngày xung đột (Sevilla 2008/2009, Talk_im_Turm 1990/1991), sự kiện bị trộn (Charles_Lee e15), hai thực thể khác nhau (Humongous). Gold không lưu ngày thay thế.

Hiện 6 câu của v8+v8n dùng `source_inconsistent` (Humongous:1, Jimmy_Lai:1, Sevilla:1, Talk_im_Turm:1, Steele_Hall:3, Charles_Lee_general:2 ở v8n). Đọc nội dung: Steele_Hall:3 sai (đếm đôi), Talk_im_Turm:1 mơ hồ, Jimmy_Lai:1 đáng ngờ, ba câu còn lại ổn.

**Hai quy tắc cho cả bốn loại (mức 2, đã chốt 2026-11-09):**
1. Mốc `source_inconsistent` không nằm trong đáp án và không làm điểm neo.
2. Nếu mốc cờ B thỏa tiêu chí của câu (`criterion`) và nằm gần chuỗi thì đáp án phải không đổi khi B dịch ±2 năm (độ lệch giả định, chưa đo):
   - `list`/`summary`: khoảng của câu phải loại hẳn B (kết thúc trước d−2 hoặc bắt đầu sau d+2).
   - `order_gap`: B không là điểm neo.
   - `first_last_next`: "đầu" cần A sớm hơn d−2; "cuối" cần C muộn hơn d+2; "kế tiếp" cần B không nằm giữa mốc cho trước và đáp án.

Kiểm bằng mã trong `check_questions.py`, không cần LLM. Với 6 câu hiện có, B đều nằm trong chuỗi nên đều bị bỏ (1,3% của 448 câu).

## 5. Precision và ingest với cờ (đề xuất)

- Ingest nhận `derived_date` (mã: năm không nằm trong chunk) và `approximate_date` (model khai); không nhận `source_inconsistent`. Đề xuất không thêm (chưa chốt, xem mục 8 về ranh giới với Cơ chế 3). Khi trang tự mâu thuẫn, ingest có thể trích hai mốc (mỗi mốc có chunk riêng); điều đó đúng về tính trung thực với chunk nhưng làm timeline có hai mốc cho một chuyện, cần bước gộp nếu muốn timeline sạch (chưa thiết kế).
- Precision tính cả mốc có cờ; mốc ingest được tính đúng khi chunk của nó nói như vậy. Mức chặt chỉ ghép theo ngày gold nên báo thêm một dòng riêng "khớp ngày thay thế của mốc `source_inconsistent`". Recall: tách 156 mốc `source_inconsistent` ra khỏi mẫu số hoặc báo riêng.
- `derived_date` và `approximate_date` báo precision theo cờ riêng. Định nghĩa `derived_date` giữa gold (năm không cùng câu) và ingest (năm không trong chunk) đang khác nhau.

## 6. Việc chưa làm

- Bước kiểm derived (nhận `derived_pending.jsonl`), bước gộp chuỗi, ghi `extras/`.
- Nhận dạng năm viết tắt ("1827–29" → 1829) trong `chain_complete.py` và ingest; kiểm trùng bằng mã trước khi đẩy vào pending; đưa các ca `quote_not_in_chunk` vào giám khảo; ghép chunk kế tiếp khi câu bị cắt ngang ranh giới.
- Thêm quy tắc cờ vào prompt v8 và `check_questions.py`; sửa hai lỗi checker "any order" (Bill_Goldberg:3, Washington_Spirit:2); bốn câu lỗi cũ (Steele_Hall:3, Condor, Panair, Talk_im_Turm).
- Đối chiếu sự kiện ingest không ngày với `undated_mentions` (hiện chỉ bị bỏ qua khi tính precision).

## 7. Gold lưu mốc `source_inconsistent` không đồng nhất; vai trò của `criterion`

Quy ước trong docs/eval/10 (10.5f, 10.5g): nguồn tự mâu thuẫn thì giữ từng mục và gắn `source_inconsistent`, hoặc gắn cho mốc không nằm trong danh sách chính. Trong gold thực tế có bốn kiểu (ví dụ thật):

| Trang | Gold lưu | Chi tiết |
|---|---|---|
| Talk_im_Turm | 1 mốc có cờ, không có mốc cho phiên bản kia | `e5` Maischberger 1990 (cờ); chunk 8 ghi (1991) không có mốc riêng; `e9` 1991 là lúc rời đi, `derived_date` |
| Steele_Hall | 2 mốc, cả hai có cờ | `e11` 1972-03-15 và `e12` 1973 (cùng một lần từ chức) |
| Charles_Lee | 2 mốc, cả hai có cờ | `e15` 1773 và `e17` 1775 (mua điền trang); `e15` còn trộn "chuyển sang Bắc Mỹ" |
| Sevilla | 1 mốc cờ cạnh mốc chính không cờ | `e8` 2008 (cờ) cạnh `e13` 2009 (không cờ) và `e16` 2010 (cờ) |

Ước lượng thô bằng so từ chung (chưa kiểm): trong 156 mốc `source_inconsistent`, khoảng 58 có mốc khác cùng nội dung khác năm, khoảng 98 thì không. Vì gold không lưu ngày thay thế, không thể kiểm bằng mã ngày thay thế có đổi đáp án hay không; đây là lý do quy tắc ±2 năm ở mục 4 là giả định.

`criterion` (trường của mỗi câu hỏi): một câu tiếng Anh mô tả loại sự kiện chuỗi thu thập; từ v8 Haiku viết nó trước câu hỏi và mỗi cụm trong câu phải có tương ứng trong `criterion`. Mã không dùng giá trị `criterion` (`chain_complete.py` và `chain_verify.py` chỉ nhắc "the question's criterion" trong prompt). Vai trò với cờ: mốc cờ chỉ gây vấn đề nếu cùng loại với `criterion`; việc so khớp đó hiện do Haiku tự phán đoán, chưa có mã.

Ingest (`pass3_p9.py`) chưa từng chạy trên trang có mốc `source_inconsistent` (tập C có 0 mốc). Chưa biết ingest ra một hay hai mốc ở trang như vậy.

## 8. Ranh giới với Cơ chế 3 (ghi tạm, chưa kết luận)

Theo người dùng (2026-11-09): Cơ chế 3 ban đầu để xử lý mâu thuẫn xuất hiện khi **nạp lại một trang với bản mới hơn** (ví dụ cùng trang Wikipedia, bản cập nhật). Còn mâu thuẫn **trong cùng một trang** (`source_inconsistent`) có thuộc Cơ chế 3 hay không thì **chưa biết**. Mục 5 trước đó viết "mâu thuẫn nguồn là việc của Cơ chế 3" là chưa chắc; đã sửa thành chưa chốt.

Cách tránh vấn đề cho bộ câu hỏi (không phụ thuộc kết luận trên): câu hỏi sinh từ gold, Haiku được dặn né mốc cờ; ingest trích trùng không ảnh hưởng việc sinh câu. Đây là né, chưa phải giải quyết: 6/448 câu vẫn dùng mốc cờ; và việc ingest trích trùng một sự kiện (kể cả không do mâu thuẫn, ví dụ Maidan trích hai lần) làm sai câu hỏi dạng đếm/`list` nếu câu chạm đến sự kiện đó.

## 9. Kế hoạch tiếp theo (người dùng nêu: lên v9 để so với v8 và v7 cho sinh câu hỏi bằng Haiku)

Lưu ý tên: **v9 của sinh câu hỏi** (`sinh_cau_hoi_v9.md`, chưa viết) khác **bản 9 của ingest** (`pass3_p9.py`). Quyết định ở `13_QUESTION_GENERATION_V8.md` vẫn là dùng v8; v9 chỉ thay v8 nếu đo tốt hơn (chưa quyết tiêu chí).

Nội dung dự kiến của v9 (đề xuất, chưa chốt): hai quy tắc cờ ở mục 4 (kể cả `list`/`summary`); xử lý bốn câu lỗi cũ (Steele_Hall:3 đếm đôi một sự kiện do hai chunk ghi hai năm, Condor thông báo + hoàn tất, Panair "first service" không phải tuyến mới, Talk_im_Turm mốc cờ trong chuỗi); luật `summary` không chứa cả đầu lẫn cuối một giai đoạn và không chứa hai mốc cờ cùng một sự kiện; quyết định có cho `derived_date` vào `list`/`summary` hay không (hiện cấm hoàn toàn).

Phương án đo (đề xuất): chạy v9 trên cùng 100 trang tune như v7/v8 (50 trang cũ + 50 trang mới, cùng trang để so cặp); chỉ số: số câu mỗi loại, checker (cần cập nhật luật cờ), [1] tỷ lệ lượt có ứng viên thật, [2][3] đóng góp thật, đọc mù mẫu, số câu dùng mốc cờ (mục tiêu 0). Chưa đo nhiễu giữa hai lần sinh cùng prompt; nên chạy hai lần nếu muốn kết luận.

## 10. Danh sách việc còn lại (tổng hợp)

- ~~Prompt v9 và cập nhật `check_questions.py`~~ **Đã viết và chạy Session 3–4 (2026-11-10); kết quả ở `docs/eval/10` mục 10.5av.** Còn: Session 1–2, đọc chunk Vologda:4, quyết các câu Haiku đề nghị, gộp `list`/`summary`.
- Bước kiểm derived, bước gộp chuỗi, tạo `extras/` (và có đưa 13 mốc thiếu của soát gold 50 trang mới vào đó hay không).
- Sửa [1] và [2]: năm viết tắt, kiểm trùng bằng mã trước khi đẩy pending, đưa `quote_not_in_chunk` vào giám khảo, ghép chunk kế tiếp khi câu bị cắt ngang ranh giới; giám khảo xét sai `in_window` (Alemannia), năm trong tên riêng, sự kiện của thực thể khác.
- Ingest: thống nhất định nghĩa `derived_date` với gold; nhận dạng năm viết tắt; bước gộp mốc trùng trong timeline; đối chiếu mốc ingest không ngày với `undated_mentions`; chọn model ingest (hiện chỉ DeepSeek); tính lại precision bản 8 theo quy tắc mới, thêm người đọc thứ hai.
- Dữ liệu: 23 trang gold có tên file mất ký tự có dấu (ví dụ `S_rgio_Concei_o`) nên không khớp tự động vào `tune`/`valid` bằng tên; khớp tự động cho tune 179, valid 153 (còn 23 trang chưa gán); `test_clean` (186 trang) chưa có gold; `valid` (167 trang) có gold nhưng chưa sinh câu hỏi.
- Chưa quyết: cách chấm `list` so với `summary`; tỷ lệ theo loại câu; soát gold 50 trang mới bằng người đọc thứ hai; quyết định xử lý mâu thuẫn trong cùng trang (mục 8).

## 11. Công cụ đã viết cho bước kiểm derived, gộp và `extras` (2026-11-09, đã chạy thử, chưa áp thật)

- **`local/chain_derived.py`** (kiểm derived, lười): đọc `derived_pending.jsonl` của [2][3] và `results.jsonl` của [1]; thứ tự: (1) mã nhận dạng năm viết tắt, (2) mã loại trùng gold (cùng chunk + cùng ngày + chữ chung ≥ 0,6), (3) giám khảo DeepSeek cho các ca còn lại. Ra `local/derived_verified.json`. Chạy trên 7 ca pending của v7n/v8n: `duplicate_of_gold` 2 (Alemannia `e21` bằng giám khảo; Department_of_Computing bằng mã, nhưng mã cũng ghi nhầm `e6` vì chung cụm "Department of Computing and Control", nên mã trùng bằng chữ chung có thể ghi dư id), `duplicate_in_chain` 1 (Meet_the_Press `e25`), `no_date_stated` 4 (Charles_Lee, Engel, Rush_Holt ×2); 0 mốc mới; 6 lời gọi LLM, 0 ca năm viết tắt.
- **`local/chain_apply.py`** (gộp): áp **quyết định đã duyệt** từ file JSON do người đọc viết (`add_ids` hoặc `drop` kèm `extra`), không tự suy từ nhãn `auto_accept`. Mặc định chạy thử, không ghi gì; `--apply` sao lưu `<page>.jsonl.bak_apply`, ghi nhật ký `local/chain_apply_log.jsonl`, bỏ câu vào `<set>/_dropped.jsonl` (thẻ q của các câu sau trong trang dịch xuống 1), ghi `dataset/eval/timeline_pilot/extras/<page>.json`. `list`/`summary`: thêm id giữ thứ tự thời gian, chặn nếu vượt trần 10/8; `first_last_next`: thêm vào `group_event_ids`, tính lại đáp án theo subtype, **không áp** nếu đáp án đổi hoặc có hòa ngày (báo cần quyết định).
- Chạy thử với `local/chain_decisions_v7n_test.json` (bốn quyết định thật của v7n: Rams:1 thêm `e28`, Sirotkin:1 thêm `e10`, bỏ Cochran:2 và Sam_Selvon:1 kèm hai mục `extras`): đều ra "ÁP" ở chế độ thử, chưa ghi gì; thư mục `extras/` chưa tạo. Chưa áp thật vì bộ chính là v8/v8n (0 ca cần sửa) và v7n chưa cần.

## 12. Chốt về mốc derived và mốc mới trong đáp án (người dùng, 2026-11-09)

- **Derived đã có trong gold và [2] duyệt** (năm lấy từ chính chunk hoặc từ năm viết tắt do mã tính; năm phải suy từ chunk khác thì không cho): thêm id vào đáp án của câu đó, không đổi gold. Khi sinh câu hỏi, mốc `derived_date` vẫn không làm điểm neo và Haiku không dựa vào nó làm đáp án.
- **Derived mới chưa có trong gold:** chỉ ghi `extras` (để tính precision ingest); không vào đáp án; bỏ câu nếu nó nằm trong khoảng chuỗi và thỏa tiêu chí.
- **Mốc ngày rõ cùng câu nhưng chưa có trong gold** (kiểu Cochran DFC, Sam_Selvon Chaconia): bỏ câu, ghi `extras` (hướng b, giữ như cũ).
- **Chưa chốt, không phải việc trước mắt:** giữ câu và thêm id kiểu `extra_<trang>_<n>` / `answer_extra` cho mốc ngày rõ mới; điều kiện nhất quán và lý do hoãn ở `docs/pending/01_QUESTION_PROMPT_V9.md`.
- Việc kéo theo (chưa làm): `local/chain_apply.py` hiện chưa cho `add_ids` với mốc mang cờ; cần cho phép khi quyết định ghi `verified_derived: true` và vẫn chặn mốc `source_inconsistent`. Ba ca `in_gold_not_in_group` mang `derived_date` (Bill_Goldberg:4, Department_of_Computing:1 của v7n, Air_Component_Command:8) chưa được đọc.

