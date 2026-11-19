# 16. Thiết kế bản quá khứ mô phỏng cho Cơ chế 3 (2026-11-18)

**Trạng thái:** thiết kế và bản thử 10 chỗ sửa; chưa chạy cả loạt, chưa nạp vào kho nào. Nối tiếp `12` mục 7.

## Nguyên tắc

- `real` = bản mới nhất ("tương lai"); bản quá khứ = `real` bị sửa **một câu** trong một số chunk. Mỗi chỗ sửa: đưa chunk (câu mục tiêu đánh dấu) cho LLM, LLM chỉ trả lại câu đã viết lại; code ghép vào chunk. Chunk khác trong trang và câu khác trong chunk giữ nguyên (vừa là đối chứng "không đổi", vừa giống thực tế: sửa nhỏ giữ ~98% chunk).
- Không sửa mọi chunk của một trang: cần chunk không đổi để đo đóng nhầm (False-invalidation) và vì chi phí/nhãn. Mốc thật: sửa nhỏ trên Wikipedia chỉ đổi khoảng 1 chunk trong 74 (`09`).
- **Đã chốt cho tune (2026-11-18, người dùng):** đổi **một nửa số trang** (101 trong 203), mỗi trang **2 chunk khác nhau** (mỗi chunk một câu, hai loại khác nhau), tổng khoảng 200 chỗ sửa (~3,4% trong 5.995 chunk). Một nửa số chỗ sửa nằm trên chunk là bằng chứng (gold) của câu hỏi có sẵn (Cơ chế 1 `gold_chunk_ids`, Cơ chế 2 evidence của mốc vàng), nửa còn lại ở chunk khác. Ghi chú: câu "10–20%" trong `12` mục 7.2 là phần nội dung **trong một chunk**, không phải tỉ lệ số chunk.
- Tỉ lệ loại: C : E : F : A = 3 : 3 : 2 : 2 (~61 / 60 / 40 / 40), E bị giới hạn bởi số ứng viên (338 câu trên 119 trang).
- Nhãn do code sinh, đáp án tính bằng code. Câu mục tiêu lấy từ mốc ingest 10b có `quote` nằm trọn trong một câu trọn của chunk (câu đầu chỉ khi chunk mở mục; câu cuối chỉ khi kết thúc bằng dấu chấm).

## Danh mục chỗ sửa

| Loại | Sửa | Làm bằng | Kiểm bằng code | Đáp án |
|---|---|---|---|---|
| C. Mốc lệch | đổi một năm trong câu (±1–4) | code | năm cũ còn đúng một lần | `real` đúng; bản cũ sai mốc |
| E. Tiến hóa | viết lại thành "còn đang tiếp diễn", bỏ ngày kết thúc | LLM | từ khóa kết thúc và năm kết thúc không còn | bản cũ đúng đến thời điểm đó; `real` đóng |
| F. Sai từ đầu | đổi một giá trị (tên, nơi chốn, tổ chức) | LLM | giá trị cũ vắng, giá trị mới có, giá trị mới không có trong câu gốc | `real` đúng; bản cũ không được trả như sự thật |
| A. Đối chứng | diễn đạt lại không đổi ý | LLM | tập năm giữ nguyên, tên riêng không mất | không được đóng/vô hiệu |
| J. Bản mới bỏ sự kiện | giữ câu mà `real` bỏ | chưa làm (cần câu thật) | | vắng mặt không phải bác bỏ |

Số lượng cho tune: ~201 chỗ sửa, LLM cho ~140 chỗ (E, F, A), 20 luồng song song.

## Định danh và kho

- `chunk_id` bản quá khứ = `<id của real>@past` (ví dụ `/wiki/X#12@past`); `real` giữ nguyên id nên gold chunk và câu hỏi hiện có không đổi. Qdrant dùng id suy ra từ `chunk_id`, nên hai bản là hai điểm khác nhau.
- Collection Qdrant riêng cho nạp thử: `tam_chunks_dev_past_<tập>` (bản cũ), kho nạp thử Cơ chế 3 `tam_chunks_dev_m3_<tập>`. **Không nạp bản cũ vào `tam_chunks_dev_{tune,valid,test_clean}`** (ghi đè theo `chunk_id`/trang).
- Neo4j: `upsert_page` xóa cả trang trước khi ghi, nên bản cũ và `real` không được nạp bằng đường đó. Dùng khóa trang riêng (`<trang>@past`) hoặc cơ sở dữ liệu riêng cho thử nghiệm Cơ chế 3.
- Cache LLM riêng: `data/llm_cache/pastgen_<model>/`; mỗi lần chạy ghi model và thinking.

## Định dạng nhãn (`edits.jsonl`)

`edit_id, type, page, chunk_id, chunk_id_past, on_gold_chunk, sentence_real, sentence_past, event{date,text,track,phase,kind,quote}, real_value, past_value, checks_failed, model`.
`real_value` = giá trị đúng ở bản `real`, `past_value` = giá trị ở bản cũ (loại C, F; null với E, A). Bản thử (`past/pilot_prev`) dùng tên cũ `old_value`/`new_value` không nhất quán, đã sửa ở bản chạy tune.

## Bản thử 2026-11-18 (10 chỗ, `dataset/organized/past/pilot/`)

Model `hy4-flash-free` qua OpenCode (7 lần gọi; còn lại 3 chỗ loại C bằng code). Thinking: profile gửi `thinking: disabled`, chưa kiểm chứng model có nhận. Đạt kiểm 9/10.
- C 3/3 đạt; F 2/2 đạt; A 2/2 đạt (diễn đạt lại giữ năm và tên); E 2/3 đạt.
- Loại: tune-003 (First_Things, E): bản viết lại vẫn còn từ khóa kết thúc, bị kiểm bắt.
- Chất lượng cần xem: tune-009 (Milton_Friedman, E) viết "was still teaching at ... after teaching there for 30 years", gượng nhưng đạt kiểm; kiểm bằng code chưa bắt được lỗi văn phong/logic.

## Quyết định chờ

1. (Đã làm) Đổi tên trường nhãn (`past_value`, `real_value`).
2. Có đưa bước đọc tay mẫu nhỏ (cỡ 10–20 chỗ) để kiểm chất lượng loại E vào quy trình không.
3. Model sinh bản cũ chính thức (`hy4-flash-free` đến khoảng 30/11, dự phòng Gemini flash-lite) và kiểm chứng thinking.
4. Tên kho Neo4j cho thử nghiệm Cơ chế 3.

## Kết quả chạy tune (2026-11-18, `hy4-flash-free`, 20 luồng)

201 chỗ sửa trên 102 trang (100 chỗ trên gold chunk của câu có sẵn); đạt kiểm code 185/201. Đầu ra: `dataset/organized/past/tune/{edits.jsonl, chunks/}`; log `local/make_past_tune.log`; cache `data/llm_cache/pastgen_hy4-flash-free/`. Không có lỗi LLM, không thấy 429. Thinking: chưa kiểm chứng model có nhận `thinking: disabled`.

| Loại | Đạt / Tổng |
|---|---|
| C (đổi năm, code) | 61 / 61 |
| F (đổi giá trị) | 40 / 40 |
| A (đối chứng) | 40 / 40 |
| E (còn tiếp diễn) | 44 / 60 |

### Vì sao 16 chỗ E không đạt (đã đọc từng câu)

1. **Kiểm báo nhầm (phần lớn):** luật cũ loại năm của mốc rồi kiểm "năm cuối còn lại", thường là năm không liên quan (tune-010 giữ 2006, tune-088 giữ 1165) nên loại cả câu viết đúng (tune-010, 024, 048, 098, 114, 193).
2. **Chọn câu E sai:** chọn bằng từ khóa `retired|replaced|resigned`, nên lấy cả câu không có mốc kết thúc để bỏ (tune-156 `unchanged`; tune-173, 142, 090, 116 là mốc điểm/bắt đầu).
3. **LLM sai thật (2–3 chỗ):** tune-130 viết quá tay, tune-074 giữ "until 1996".

### Kiểm cũ còn bỏ lọt (phát hiện khi viết lại luật kiểm, chạy offline, không tốn LLM)

- **LLM bịa năm mới**: tune-092 ("formed in 1986"), tune-108, tune-191 ("Since 2006, Sirks has held the post"). Đây là lỗi nặng: bản cũ chứa thông tin không có trong `real`.
- Vài chỗ đạt kiểm nhưng câu cụt hoặc mất logic (tune-175, tune-004 "amid controversy" giữ lại sau khi bỏ "resigned"). Luật kiểm mới cũng báo nhầm vài chỗ (tune-138, 185). Cả hai luật chỉ là heuristic.
- Loại C, F, A đạt hết; chưa đọc tay F và A kỹ.

### Việc cần làm tiếp (theo thứ tự, chưa làm)

1. Siết chọn câu E: chỉ mốc `phase = end`, năm kết thúc đứng ngay sau `until|to|death in|…`.
2. Sửa kiểm bằng code: cấm số/năm mới không có trong câu gốc; kiểm đúng năm kết thúc của mốc đó; cấm số từ khóa kết thúc tăng. Chạy lại kiểm trên 201 chỗ có sẵn (không tốn LLM) và báo số chỗ còn hỏng trước khi gọi lại LLM.
3. Prompt E: "không thêm năm hoặc tên mới; bỏ các mệnh đề chỉ có nghĩa sau khi kết thúc".
4. Kiểm chất lượng: đọc tay mẫu ~30 chỗ E và F (rẻ, tin hơn), hoặc thêm một lượt LLM kiểm câu (~140 lần gọi).
5. Chạy lại chỉ các chỗ hỏng (~30 lần gọi, dùng `cache_salt` hoặc prompt mới vì khóa cache không đổi khi prompt giống).
6. Sau đó: nạp bản cũ vào kho riêng, sinh câu hỏi cho từng chỗ sửa, bốn hệ so sánh (xem trên).

## Lượt siết loại E và chạy lại (2026-11-18, `hy4-flash-free`, `--redo`)

Sửa `scripts/make_past.py`: chọn E chỉ khi mốc `phase=end` và năm kết thúc đứng ngay sau `until|to|through|death in|…` (một lần); kiểm E mới: năm kết thúc phải mất, số từ khóa kết thúc không tăng, cấm số mới (`new_number`), không mất năm khác (`other_year_lost`), không rút câu quá nửa (`over_edit`); prompt E cấm thêm năm/tên, yêu cầu bỏ mệnh đề chỉ có nghĩa sau khi kết thúc. Chế độ `--redo [--no-llm]` kiểm lại `edits_v1.jsonl` (bản cũ giữ nguyên) và chỉ gọi lại chỗ E hỏng.
- Kiểm offline luật mới trên 60 E cũ: 43 hỏng, trong đó 40 là câu không phải câu kết thúc (`not_end_sentence`): chọn E cũ quá rộng.
- Chạy lại: 18 lần gọi (chỗ giữ được câu + chỗ thay bằng ứng viên E khác trên cùng trang), thinking `disabled` gửi đi (chưa kiểm chứng), 20 luồng, cache hit 0 / miss 18, 60 s. Chỉ số: `past/tune/metrics_redo.json`, log `local/make_past_tune_redo.log`.
- Kết quả: đạt kiểm 173/201; E 32/60 (C 61/61, F 40/40, A 40/40). 25 chỗ E không còn ứng viên hợp lệ trên trang (`no_valid_E_candidate`); 3 chỗ LLM làm hỏng thật (tune-004, 022, 114: bỏ mất năm khác hoặc cụt câu). Đọc tay các E làm lại thấy tự nhiên và không thêm sự thật mới.
- Hệ quả: số E tune thực tế chỉ ~32 (không phải 60). Muốn tăng E cần mở rộng nguồn ứng viên (trang khác, hoặc cho phép E trên trang chưa được chọn) hoặc chấp nhận E ít.

## Bộ tune đều 50 mỗi loại (2026-11-18, `hy4-flash-free`, 20 luồng)

Tỉ lệ đổi thành C:E:F:A = 1:1:1:1 (50 mỗi loại, 200 chỗ, 100 trang, 100 chỗ trên gold chunk). `make_past.py` chọn E trước (tối đa 1 E mỗi trang, từ 224 câu E hợp lệ ở 115 trang), rồi C/F/A lấp chỗ, mỗi trang tối đa 2 chunk khác nhau. Bản trước giữ ở `past/tune_prev2/`.
- 150 lần gọi LLM (cache hit 14, miss 136), 290 s, thinking `disabled` gửi đi (chưa kiểm chứng). Chỉ số: `past/tune/metrics.json`; log `local/make_past_tune_v3.log`.
- Đạt kiểm 187/200: C 50/50, E 42/50, F 47/50, A 48/50. Lỗi: other_year_lost 5, over_edit 4, llm_fail 3 (JSON thiếu trường `sentence`), end_still_present 2, value_swap 2, facts_changed 1.

### Đọc tay 13 chỗ hỏng và sửa (2026-11-18)

Nguyên nhân (đã đọc từng câu), phần lớn là lỗi của code kiểm/tách câu, ít là của LLM:
1. **Tách câu sai ở viết tắt** (`B.S .`, `c .`, `IV .`): câu cụt, LLM viết lại thêm tiền tố, khi ghép bị lặp (tune-052, 119, 183). Sửa: `sentences()` không tách sau viết tắt; `frag_ok` loại câu mở bằng chữ thường hoặc ngoặc không cân.
2. **Kiểm báo nhầm**: `other_year_lost` khi mất năm *sau* mốc kết thúc là hợp lý (cắt phần sau, hợp với bản cũ) nên chỉ báo khi mất năm ≤ năm kết thúc; `value_swap` báo khi giá trị cũ còn xuất hiện ở chỗ khác (tune-081, 114) đổi thành so số lần xuất hiện; `facts_changed` bỏ sót tên đầu câu (tune-129) đổi thành kiểm sự có mặt; bỏ kiểm từ khóa `resigned` ở câu không liên quan (tune-022). Thêm `length_grew`.
3. **LLM sai thật**: giữ `until 1996` / `until 1999` (tune-021, 038); JSON thiếu trường `sentence` (tune-014, 058, 062). Chạy lại bằng prompt retry (cache key mới), lần cuối kèm gợi ý "năm kết thúc cần bỏ".
- Chạy lại: 10 + 5 lần gọi (prompt retry), cache miss hết, không 429. Kết quả: **198/200** (C 50, E 49, F 49, A 50). Còn hỏng: tune-038 (bỏ cả các nhà xuất bản sau 1999, `over_edit`, có thể chấp nhận nếu nới ngưỡng) và tune-058 (LLM luôn trả JSON thiếu `sentence`). Hai chỗ này không có chunk `@past`.
- Chưa đọc tay hết E/F đã đạt; mẫu 26 chỗ đạt vừa đọc: tự nhiên, trừ F tune-192 (`Luftwaffe` → `Kriegsmarine ( air force )`: giá trị sai nhưng còn lại chú thích cũ).
- Bản lưu: `past/tune/edits_v4.jsonl` (trước lượt này), `past/tune_prev2/` (bộ 201 cũ).

## Kiểm prompt/model hy4-flash-free trước khi sinh valid, test_clean (2026-11-18)

Chưa nạp kho riêng, chưa sinh bản quá khứ cho valid và test_clean. Chỉ kiểm trên tune (không dùng DeepSeek). Kết quả:
1. **Thinking:** `thinking: disabled` (profile) bị hy4 **bỏ qua**: cùng 108 reasoning token khi tắt/không đặt/bật; `chat_template_kwargs`, `thinking.budget_tokens` cũng không tác dụng. Chỉ `reasoning_effort: none` tắt được (reasoning 0). Đã sửa ghi chú: mọi lần chạy trước (cache `pastgen_hy4-flash-free`) là **thinking BẬT**.
2. **Tắt thinking làm chất lượng giảm:** 36 chỗ (12 E, 12 F, 12 A đầu danh sách tune), cùng prompt: tắt thinking đạt kiểm 29/36 (1 JSON hỏng); bật thinking 35/36 (0 JSON hỏng), nhưng chậm hơn (trung bình 19,8 s so với 6,1 s/lần). Giữ thinking bật.
3. **Lỗi JSON (~7% mỗi lượt thử, cuối cùng ~2%) do hy4 bọc kết quả trong `{"properties": {...}}`** (giống schema trong lời nhắc vì profile `structured_output: false`). Sửa trong `make_past.py` (validator mở `properties`, không đổi prompt nên cache cũ vẫn dùng được). Thử lại 36 chỗ: 0 cảnh báo JSON.
4. Lời nhắc có ví dụ định dạng (thay vì schema) làm tệ đi: model trả lại câu gốc nhiều (23/36 đạt), không dùng.
5. Còn lỗi cần chú ý: E `over_edit` khi câu có nhiều mệnh đề sau mốc kết thúc (tune-007), `end_still_present` ở câu có hai mốc "until" (cần chạy lại bằng prompt retry kèm năm cần bỏ).
- Cache thử: `data/llm_cache/pastgen_hy4-flash-free_think_test/` và `..._nothink_test/` (không dùng cho bộ chính).

## Bộ valid (2026-11-18, `hy4-flash-free`, thinking BẬT, 30 luồng)

`python scripts/make_past.py --split valid --n 200 --workers 30`: 200 chỗ sửa (C/E/F/A mỗi loại 50), 101 trang, 105 chỗ trên gold chunk. Đầu ra `dataset/organized/past/valid/{edits.jsonl, chunks/, metrics*.json}`; log `local/make_past_valid.log`, `local/make_past_valid_redo.log`.
- Lượt đầu: 150 lần gọi (hit 0 / miss 150), 142 s, 1 lỗi tạm thời tự thử lại; đạt kiểm 192/200 (E 43, F 49). Lỗi: `end_still_present` 6, `over_edit` 1, `length_grew` 1.
- Nguyên nhân đọc tay: (a) câu có nhiều mốc kết thúc, LLM bỏ **mốc khác** với mốc của nhãn (valid-004, 025, 028, 029): lỗi thật, sửa bằng prompt retry kèm "năm cần bỏ"; (b) kiểm báo nhầm với mốc tháng (`From January to July 1982` giữ lại 1982 là đạt, valid-036): kiểm theo tháng-năm; (c) tách câu sai sau chữ cái viết tắt đơn (`A . F .`) làm câu F cụt (valid-056); và câu F nuốt cả một tiêu đề ghép vào câu (valid-117: mất "Later life and attempted political comeback ."), thêm kiểm `length_shrunk` (F rút >4 từ, A <60%).
- Chạy lại (`--redo --swap valid-039,valid-056,valid-117`): 7 lần gọi, **199/200** (E 49, F 50, A 50, C 50). Còn lại valid-039 (E, `over_edit`, không còn ứng viên E thay thế): không có chunk `@past`.
- Đã đọc tay phần khác biệt của cả E, F, A: F đổi giá trị hợp lý; E cắt các mệnh đề sau mốc kết thúc (hợp bản cũ), 4 chỗ chạy lại cắt khá nhiều (valid-004, 025, 028, 029) nhưng nhất quán; A giữ nguyên sự thật (kiểm 078, 079, 085, 147). Điểm yếu nhỏ: A/F trên câu dạng mục danh sách (`- 2010 : ...`, valid-122, 168) được thêm "In"/"and", vô nghĩa nhưng không sai sự thật; cân nhắc loại câu dạng danh sách khỏi A/F.
- Kiểm tách chunk: 199 chunk `@past`, mỗi chunk khác `real` đúng một câu, 0 lỗi ghép. Luật kiểm mới chạy lại trên tune không làm xuất hiện lỗi mới.

## Bộ test_clean (2026-11-18, `hy4-flash-free`, thinking BẬT, 30 luồng)

`python scripts/make_past.py --split test_clean --n 200 --workers 30`: 200 chỗ (mỗi loại 50), 106 trang, 103 chỗ trên gold chunk. Đầu ra `dataset/organized/past/test_clean/`; log `local/make_past_test_clean*.log`.
- Lượt đầu: 150 lần gọi (hit 0), 81,5 s, không lỗi JSON; đạt kiểm 189/200 (E 41, F 48). Lỗi: `over_edit` 5, `end_still_present` 4, `value_swap` 2, `other_year_lost` 1, `unchanged` 1, `length_grew` 1.
- Nguyên nhân (đã đọc từng câu): (a) câu nhiều mốc kết thúc, LLM bỏ nhầm mốc khác (006, 009, 021, 050), chạy lại bằng prompt retry kèm năm cần bỏ; (b) F trên câu cụt: viết tắt `Rev .` làm tách câu sai (197) và câu mất tên tàu (131), thêm các viết tắt `rev, hon, gov, sen, rep, capt, cdr, adm, maj, sgt, cpl, esq, vol, dept, ft, bros...` vào ABBR và thay chỗ (`--swap`); (c) `over_edit` (008, 024, 027, 035, 039): LLM bỏ cả mệnh đề sau mốc kết thúc, chạy lại được 3/5, còn 008 và 035 đọc tay thấy đúng (chỉ cắt phần sau mốc), miễn lỗi bằng `--accept` (ghi `accepted_by_hand`).
- Chạy lại: 11 lần gọi (miss 11), **200/200** (C/E/F/A 50 mỗi loại; 2 chỗ E miễn tay).
- Đọc tay phần khác biệt cả E, F, A: không thấy sự thật mới hay lỗi ghép (0 lỗi ghép). Điểm yếu nhỏ: A trên mục danh sách (test_clean-171 thêm "transferred").
- Tổng ba tập bản quá khứ: tune 200/200, valid 199/200, test_clean 200/200 (cơ sở cho Cơ chế 3 chưa nạp kho nào).

### Bù E cho valid (2026-11-18)

valid-039 (E) hỏng và không còn câu E hợp lệ nào chưa dùng ở trang còn chỗ (86 câu E chưa dùng đều nằm trên trang đã đủ 2 chỗ). Thay bằng một câu E ở trang `Affari_tuoi` (trang này thành 3 chỗ sửa, ngoại lệ so với quy tắc ≤2 chunk/trang; chunk khác nhau, không trùng). 1 lần gọi (`--redo --from-current --swap valid-039`, đã thêm cờ `--from-current`; fallback cho phép vượt `per_page` khi hết chỗ). valid: **200/200** (E 50), 101 trang, 104 chỗ trên gold chunk, 0 lỗi ghép.

## Câu hỏi riêng cho các chỗ sửa: thử trên tune (2026-11-18)

`scripts/make_past_questions.py` (chưa chạy cả tập): mỗi chỗ sửa 2–3 câu do LLM viết (hy4-flash-free, thinking BẬT, cache `data/llm_cache/pastq_hy4-flash-free/`), đáp án bám nhãn, code kiểm lộ đáp án/thiếu giá trị nhãn/phân cực/tự thân.
- E: `current` (còn không? → không, kết thúc <tháng năm>), `historical` (năm trước kết thúc, còn không? → có; năm tính bằng code), `when`. F: `direct` (đáp án = `real_value`), `verify_false` (khẳng định giá trị sai → không, là `real_value`). C: `year`, `verify_false`. A: `direct`, `direct2` (đối chứng, không đổi).
- Thử 20 chỗ sửa cân bằng (5 mỗi loại): 45 câu, 0 lỗi LLM, 45/45 đạt kiểm code (20 lần gọi, 16–22 s). Lần đầu định dạng ngày thô (`2009-01`) nên đổi thành `January 2009` (chạy lại 20 lần gọi). Đọc tay: E và C/verify_false tự nhiên; vài câu F `direct` còn vụng (tune-078, tune-115: hỏi vòng).
- Đã tách `questions_pilot.jsonl` (+ `.metrics.json`) trong `dataset/organized/past/tune/`.

### Chỉnh và đánh giá chất lượng câu hỏi (2026-11-18)

Chỉnh `make_past_questions.py`: (1) prompt yêu cầu câu ngắn, giọng tự nhiên (<25 từ), kiểm `form` ≤30 từ; (2) thêm kiểm `no_entity` (câu hỏi phải nêu thực thể từ trang/câu), `current_word` (câu E `current` phải có still/currently/now...), A: đáp án phải nằm trong cả bản `real` lẫn bản cũ (`answer_not_in_real/past`); (3) mỗi câu có trường `expect`: chunk còn hiệu lực sau khi nạp real (`valid_now`), chunk lỗi thời (`stale_now` = `@past`), `past_also_valid` (E historical và A: bản cũ cũng đúng; F/C: không). Thử 40 chỗ sửa (10 mỗi loại): 90 câu, 90/90 đạt kiểm, 0 lỗi LLM, 40 lần gọi, 39 s.
- **Phân biệt được bản cũ và real (kiểm bằng code):** với 100% câu E `current/when`, F `direct`, C `year`, đáp án đúng không có trong câu bản cũ; với F/C `verify_false`, giá trị sai có trong câu bản cũ. Hệ trả lời từ chunk `@past` sẽ sai ở đúng các câu này, nên câu hỏi phân biệt được hệ không xử lý trạng thái.
- **Chất lượng đọc tay (hy4, thinking bật):** E, C, A tự nhiên và đúng nhãn. F `direct` còn khoảng 20% vụng hoặc mơ hồ (tune-059 "medical garden", tune-103 "what was the club called? → Poli", tune-115 dài dòng); lỗi nhỏ do token hóa nguồn ("NBCs" thay vì "NBC"). Không thấy câu lộ đáp án hay trái nhãn.
- **Chưa có / việc cần làm:** câu kiểm "đóng nhầm" trên chunk không đổi cùng trang bị sửa (dùng lại câu Cơ chế 1/2 có gold chunk không bị sửa làm đối chứng); câu hỏi chưa đo thứ tự thời gian giữa nhiều lần sửa (chỉ có hai phiên bản).

### Kiểm độc lập câu hỏi bằng LLM trả lời (2026-11-18, hy4, 40 chỗ sửa tune, 90 câu)

`scripts/validate_past_questions.py`: mỗi chỗ sửa 3 lần gọi (kèm chunk `real` / kèm chunk `@past` / không kèm chunk), đáp án so gold bằng code (120 lần gọi, thinking BẬT, cache `data/llm_cache/pastv_hy4-flash-free/`). Kết quả `questions_pilot.validated.jsonl` + `.metrics.json`: **giữ 54/90 (60%)**.
- `real_wrong` 4/90: câu rõ ràng nhưng sai hoặc mơ hồ (tune-059 giá trị F quá chung "Botanical garden"; tune-148 "NBCs" lỗi token hóa; tune-137-q2, tune-158-q1 mơ hồ). Tức ~95% câu hỏi trả lời đúng được từ chunk `real`.
- `closed_leak` 22/90 (24%): hy4 trả lời đúng **không cần chunk** (kiến thức Wikipedia sẵn có): C `year` 6/10, F `direct` 7/10, A 5/20, E `when` 4/10. Câu này không đo bộ nhớ, loại.
- `past_not_as_expected` 11/90, **gần hết ở E `current`/`when`** (9/11): với chunk bản cũ mô hình vẫn trả lời "No" (hoặc đúng năm kết thúc), không bị đánh lừa. Nguyên nhân nằm ở **dữ liệu E, không ở câu hỏi**: kiểm trên 3 tập, ~65–68% câu E bản cũ (tune 34/50, valid 34/50, test_clean 32/50) không có dấu hiệu "còn tiếp diễn" (chỉ bỏ năm kết thúc: "from 1814", vẫn quá khứ, không khẳng định còn đang diễn ra); và ~16–20% (tune 10, valid 8, test_clean 9) năm kết thúc vẫn còn ở chỗ khác trong chunk cũ.
- Việc cần làm: (1) sinh lại E để câu bản cũ khẳng định rõ "còn tiếp diễn" (hiện tại/`since`/`still`) và năm kết thúc không còn ở chỗ khác trong chunk (kiểm ở mức chunk); (2) lọc `closed_leak`; (3) F: lọc giá trị chung/token hóa.

## Cập nhật 2026-11-19: sinh lại E (prompt "còn tiếp diễn") và ổn định bước câu hỏi

- **E mới:** prompt bắt câu bản cũ nêu rõ còn tiếp diễn (thì hiện tại/"since"/"remains"), báo năm kết thúc ngay lần gọi đầu; kiểm mức chunk (`e_chunk_bad`: năm kết thúc không còn ở bất kỳ câu nào trong chunk, câu mới không còn dấu hiệu thì quá khứ nếu thiếu từ tiếp diễn); ứng viên E loại chunk còn năm kết thúc ở câu khác. `make_past.py --redo --from-current --regen-e` (cache `pastgen_e2_<model>`). Cả ba tập 200/200; nhận tay tune-001, valid-046 (`over_edit`), test_clean-038. Bản trước: `edits_v6_preE2.jsonl`. valid: 7 trang có 3 chỗ sửa (ngoại lệ so với ngưỡng 2).
- **Câu hỏi E (tune, 50 chỗ, 150 câu):** current giữ 37/50 (bản E cũ: 3/10), historical 50/50 sau khi cho phép UNKNOWN (bản cũ chỉ còn "đang…", không còn năm), when giữ 25/50 vì 24/50 `closed_leak` nên **bỏ `when` khỏi bộ chấm**.
- **Validator:** `match` bỏ qua "s" cuối (token hóa "NBCs"); E/historical chấp nhận UNKNOWN với chunk cũ; tạo `<in>.final.jsonl` = câu qua kiểm, không `E/when`; thống kê số chỗ sửa còn ≥1 câu.
- **Nguồn loại chính:** `closed_leak` (kiến thức Wikipedia sẵn có) ~20–25% câu; mức sinh không tránh được, bước lọc bằng LLM trả lời là cơ chế ổn định (không sửa prompt).

### Bộ câu hỏi tune hoàn chỉnh (2026-11-19, đã làm xong trên tune; valid/test_clean chưa sinh)

Đường ống một tập: `make_past_questions.py` (LLM sinh + code kiểm) → `validate_past_questions.py` (hy4 trả lời với real / `@past` / không chunk; loại `real_wrong`, `past_not_as_expected`, `closed_leak`, bỏ E/when) → viết tay bù cho chỗ sửa thiếu câu (cùng đường kiểm) → `build_clean_questions.py` gộp các đợt → `audit_questions.py` (hy4 kiểm mơ hồ: câu đứng một mình, không kèm trang) → `<prefix>.clean.jsonl`.

- **Tune, bộ sạch `questions_v7.clean.jsonl`: 332 câu**, mọi loại 50/50 chỗ sửa có câu: E 87, C 71, F 66, A 108. Từ 450 câu sinh (E 150 + C/F 100 + A 200 lần đầu) + A 200 (4 câu/chỗ) + 51 câu viết tay (7 đợt).
- **Viết tay:** bù cho chỗ không còn câu sau lọc. A: hỏi câu khác trong cùng chunk (`scope: same_chunk_other_sentence`) hoặc chunk khác của cùng trang (`same_page_other_chunk`, `evidence_chunk`); validator dùng đúng chunk đó. C/F phải hỏi đúng giá trị bị đổi nên giữ nguyên câu sửa, thêm bối cảnh (tên giải/đơn vị) cho đỡ mơ hồ; F tune-081 dùng dạng so sánh "Was it Kerry, rather than Gorton…".
- **Rò rỉ kiến thức sẵn (`closed_leak`)** ~30% câu không có chunk mà hy4 vẫn trả đúng: đó là kiến thức Wikipedia của mô hình, không phải lỗi; câu loại đi, không sửa được bằng prompt. Câu có/không (`E/current`, `F/C verify_false`) không áp kiểm này (đoán "No" 50%); phân biệt dựa vào chunk cũ trả "Yes".
- **Mơ hồ:** E/current luôn mang "still/now" nên chỉ đòi tự đứng được (hệ thống truyền T_now); 19 câu khác bị loại (thiếu tên riêng, đáp án là danh sách).
- **Sửa code kiểm:** `match` coi số ngắn (52, 17) là từ phải khớp (trước đó "Intermediate School 52/131" khớp nhầm). Kiểm lại toàn bộ bằng cache (0 lần gọi mới).
- **Chi phí tune:** ~1.150 lần gọi hy4 (sinh 270, kiểm 800+, mơ hồ ~230, viết tay kiểm ~130); E sinh lại 150 lần cho 3 tập.
- **Hạn chế:** chỉ kiểm rò rỉ với hy4 (mô hình khác có thể biết nhiều hơn); câu A mức trang (không phải chunk bị sửa) ở tune-072/116/169; chỉ số trạng thái của chunk (còn hiệu lực/đã đóng/đánh dấu sai) đo thẳng trên kho, không phụ thuộc câu hỏi.

## Bộ câu hỏi valid và test_clean (2026-11-19, hy4-flash-free, thinking bật)

Cùng quy trình với tune: sinh câu (`make_past_questions.py`) → LLM trả lời kiểm real/past/closed (`validate_past_questions.py`) → viết tay bù chỗ sửa còn thiếu (đợt `questions_manual*`, A dùng câu khác hoặc chunk khác cùng trang) → gộp (`build_clean_questions.py`) → kiểm mơ hồ (`audit_questions.py`). Chạy thử 20 chỗ trước khi chạy cả tập (cả hai tập cùng mức giữ ~55–60% như tune). Dữ liệu quá khứ của hai tập được kiểm lại bằng code trước khi sinh (ghép chunk, năm kết thúc, từ chỉ tiếp diễn): 0 lỗi.

| Tập | Sinh | Qua kiểm code | Giữ sau LLM-trả-lời | Bù tay (giữ) | Bộ sạch (file) | C | E | F | A | Chỗ sửa có câu |
|---|---|---|---|---|---|---|---|---|---|---|
| valid | 550 | 520 | 286 | 51 | **309** (`questions_v3.clean.jsonl`) | 78 | 83 | 66 | 82 | 200/200 |
| test_clean | 550 | 526 | 287 | 69+16+7 | **319** (`questions_v5.clean.jsonl`) | 80 | 91 | 68 | 80 | 200/200 |

- Hao hụt chủ yếu do `closed_leak` (hy4 trả lời được khi không có chunk): valid 199, test_clean 213 trên 550 câu.
- test_clean-064 (F): chỗ sửa cũ (Drašković/Bulatović) không có câu đạt (câu thẳng `closed_leak`, câu `verify_false` bị chunk cũ tự mâu thuẫn). Đã thay bằng chỗ F khác cùng trang (`--redo --from-current --swap test_clean-064`; cờ `--swap` nay đưa edit vào danh sách làm lại dù đang đạt kiểm; test_clean-038 giữ nguyên câu cũ, chunk dựng lại, 0 lỗi ghép). Câu hỏi của 064 sinh lại. Bản trước lưu `edits_v8_pre064swap.jsonl`, `pre064/`. test_clean: bộ sạch **319** câu (`questions_v5.clean.jsonl`; C 80, E 91, F 68, A 80), **200/200** chỗ sửa có câu.
- Hạn chế giống tune: kiểm rò rỉ chỉ với hy4; câu có/không (E current/historical, verify_false) không kiểm rò rỉ; một số câu A bù tay ở mức trang (`scope: same_page_other_chunk`).

## Kế hoạch so sánh các hệ (2026-11-19, bàn xong, chi tiết làm rõ sau, chưa cài, chưa chạy)

**Phạm vi chốt:** người dùng hỏi về thế giới theo thời gian (hiện tại, tại một mốc, timeline); kho phải đúng sau mỗi lần cập nhật. Câu về lịch sử của tài liệu ("trước đây trang ghi gì", "đã sửa gì") không đưa vào đánh giá chính (người dùng cuối hầu như không hỏi; `12` coi là ngoại lệ nhỏ). Dữ liệu mô phỏng cũng không có ca giữ bản cũ có ích, vì `real` là bản đầy đủ nên đã chứa lịch sử.

**Ba hệ so sánh** (thêm hệ nào chắc thua thì bỏ: "không cập nhật" và Keep-all bị loại):

| Hệ | Cách cập nhật | Chi phí LLM | Rủi ro / khác biệt |
|---|---|---|---|
| Replace-all | Xóa nút cả trang, nạp lại cả trang | Cao nhất (cả trang) | Mốc tham chiếu về độ sạch; nạp mức trang có bước gộp nút toàn trang |
| Diff-replace | Diff chunk; xóa nút có `FROM_CHUNK` là chunk đổi; trích xuất lại chỉ chunk đó bằng prompt ingest thường; không có bước LLM quyết định | Thấp (chỉ chunk đổi) | Không thấy nút cũ: dễ lệch ở nút gộp nhiều chunk, nút lân cận; trích xuất lại có biến động |
| Cơ chế 3 | Diff chunk; **một lượt LLM nhận văn bản chunk mới + các nút cũ của cả đoạn đổi (mở rộng sang nút cùng `Cell`)**, đề xuất giữ/sửa mốc/đóng `end_time`/vô hiệu/thêm; code kiểm tra trích dẫn, mốc, chuỗi (`12` mục 6) | Gần Diff-replace, hơn một chút token vào/ra | Nút cũ làm tham chiếu (có thể tốt hơn), nhưng LLM có thể bị neo vào nút cũ (giữ nút lỗi thời); nút mới do prompt cập nhật sinh nên có thể khác prompt ingest `10b` |

**Cách so:** biểu đồ Pareto, trục độ chính xác và chi phí (lượt gọi, token), cùng phương pháp truy xuất ở cả ba hệ (`vec`, `graph`, `graph_tb`, `graph_tt`, và agent của cơ chế 2). Tách theo loại sửa C/E/F/A. Thêm chỉ số trạng thái: nút lỗi thời còn sót, nút bị đóng/vô hiệu nhầm, nút bị đổi dù không cần.

**Bộ câu hỏi:**
- Chính: câu cơ chế 2 trên các trang bị sửa (~190 trang/tập); tách riêng nhóm câu hỏi đúng sự kiện bị sửa (tune 56, valid 67, test_clean 63).
- Phụ: bộ `mech3` (chỉ phân biệt hệ giữ nhiều bản với nhóm ghi đè, vì vector của cả ba hệ đều ghi đè nên giống nhau); câu cơ chế 1 trùng gold chunk với chunk sửa (tune 30, valid 24, test_clean 24), dùng làm kiểm hồi quy.
- Độ phủ kiểm offline (200 chỗ sửa/tập): chunk sửa là bằng chứng của ≥1 sự kiện timeline 184/177/177; câu cơ chế 2 hỏi đúng sự kiện nằm trên câu sửa 56/67/63. Không cần sinh thêm câu graph-level.

**Việc chưa chốt:** phạm vi mở rộng nút lân cận của cơ chế 3; Plain (nạp lại từng chunk không dọn) không còn là hệ riêng; nạp thử ~20 chỗ sửa vào kho riêng để đo tỉ lệ chỗ sửa "hiệu lực" (bản cũ có sinh nút khớp câu bị sửa) cần người dùng cho phép nạp kho.

## Ghi chú: cơ chế 1 sẽ thử thêm bằng agentic search với vector (2026-11-19, làm sau)

Câu cơ chế 1 (gold chunk trùng chunk sửa) và bộ `mech3` sẽ được thử thêm bằng **agentic search chỉ dùng vector** (agent tự gọi truy xuất vector nhiều lần), ngoài các phương pháp cố định. Chưa thiết kế, chưa chạy.
