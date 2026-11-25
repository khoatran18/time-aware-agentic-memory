# 16. Thiết kế bản quá khứ mô phỏng cho Cơ chế 3 (2026-11-18)

**Trạng thái (cập nhật 2026-11-25):** đã chạy xong tune, valid và `test_clean` (kết quả ở các mục sau, mục cuối là `test_clean`). Phần thiết kế bên dưới ghi lúc chưa chạy (2026-11-18). Nối tiếp `12` mục 7.

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

## Làm rõ đầu vào của Diff-replace và cơ chế 3 (2026-11-21, đã kiểm mã ingest, chưa cài)

**Ingest thật làm gì** (`dataset/eval/timeline_pilot/outline_trial/pass3_p10b.py`, bản 10b): trích theo **mục** (section) của trang; mỗi mục chia cửa sổ ≤ 8 chunk (`WINDOW = 8`), mỗi cửa sổ một lượt LLM. Đầu vào: tên trang, tên mục, các chunk đánh số; chunk liền trước cửa sổ đưa vào dạng `(context only)` (không trích từ nó). Cần ngữ cảnh vì "later that year", "in March" suy năm từ chunk trước. Sau đó là bước mã cấp trang: lọc, gộp (`merge_keyed`, `merge`, cặp LLM `same`), `node_id`, `FROM_CHUNK`. Một chunk đứng riêng không đủ để trích đúng.

**Diff-replace (sửa):**
- Đầu vào: cửa sổ chứa chunk đổi, **bản mới**; chunk đổi là chunk cần trích, các chunk khác trong cửa sổ đánh dấu `(context only)` (cơ chế có sẵn của prompt 10b). Không có văn bản cũ, không có nút cũ, không có bước LLM quyết định.
- Xóa: chỉ nút có mọi `FROM_CHUNK` nằm trong chunk đổi. Nút có `FROM_CHUNK` tới chunk khác chỉ gỡ cạnh, giữ nút.
- Nút của chunk không đổi giữ nguyên nên không trôi `node_id`. Sau khi thay: chạy lại bước gộp cấp trang và dựng lại chuỗi `TIẾP_THEO`.
- Chi phí: một lượt LLM, vào khoảng một cửa sổ (≤ 8 chunk).

**Cơ chế 3 (làm rõ):** một lượt LLM nhận (a) chunk đổi **bản cũ và bản mới** (cách đổi), (b) các nút cũ trong phạm vi lân cận (dưới), (c) các chunk còn lại của cửa sổ bản mới làm ngữ cảnh. Đề xuất giữ/sửa/đóng `end_time`/vô hiệu/thêm; code kiểm như `12` mục 6. Khác Diff-replace ở chỗ có nút cũ + văn bản cũ làm tham chiếu và có quyết định giữ nút không đổi.

**Phạm vi nút lân cận của cơ chế 3 (ba mức):**
1. Chỉ nút của chunk đổi.
2. **Nút của chunk đổi + nút kề trước và kề sau trong chuỗi `TIẾP_THEO` của cùng `Cell` (đang chọn mức này)**; đủ để chỉnh `end_time` và sửa chuỗi, kèm trần số nút mỗi lượt (đề xuất 20).
3. Cả `Cell`.

Chỉ chuyển sang mức 3 nếu mức 2 bỏ sót nhiều (đo bằng nút lỗi thời còn sót).

## Ghi chú: cơ chế 1 sẽ thử thêm bằng agentic search với vector (2026-11-19, làm sau)

Câu cơ chế 1 (gold chunk trùng chunk sửa) và bộ `mech3` sẽ được thử thêm bằng **agentic search chỉ dùng vector** (agent tự gọi truy xuất vector nhiều lần), ngoài các phương pháp cố định. Chưa thiết kế, chưa chạy.

## Cập nhật 2026-11-20: cấu hình agent và hạ tầng chạy (liên quan so sánh các hệ cơ chế 3)

- Đã có agent kiểu C (text + vector + graph) trong `scripts/run_agent_search.py` (`--kind C`); kết quả trên tune 619 câu cơ chế 2 và cách chạy: `docs/eval/12_V9_TUNE600_RESULTS.md` mục 7. C ngang agent B + graph về exact (0,869 so với 0,864) nhưng tốn thêm khoảng 39% token vào; chưa là điểm trên biên Pareto khi chi phí tính bằng token.
- **Thinking tắt cho mọi lần chạy** (chốt 2026-11-17, nhắc lại 2026-11-20): `deepseek-v4.1-flash` qua OpenCode chỉ cần `thinking: disabled`; `hy4-flash-free` bỏ qua trường đó, cần `reasoning_effort: none`. Mô hình agent giữ `deepseek-v4.1-flash` để so sánh được với các lần chạy cũ (g, h, i).
- **Giới hạn OpenCode** hôm 20/11 khoảng 50 yêu cầu mỗi phút; dùng 20 luồng, chuẩn bị chạy bù khi có `llm_error` (mất kết nối). Chi tiết ở mục 7 của `eval/12`.
- Chưa làm (đã bàn, chờ): module diff và bước cập nhật của cơ chế 3, nạp thử bản cũ vào kho riêng (cần người dùng cho phép), chạy lại g và h trên 619 câu, agent cho cơ chế 1 (text, text + vector) và câu giá trị cần prompt khác `v5`.

## Pilot cơ chế 3: dựng trạng thái graph cũ cho 20 trang tune (2026-11-21, đã chạy)

**Chốt cách chạy:** bốn bước chung cho cả ba hệ: (1) diff chunk, (2) cập nhật nút (khác nhau theo hệ), (3) gộp trùng cấp trang (chạy lại quy tắc, chỉ phán quyết cặp mới bằng LLM), (4) ghi lại graph cả trang. Vector không cần dựng bản cũ: cả ba hệ ghi đè theo `chunk_id` và kết thúc ở bản `real`; chỉ cần nếu cơ chế 3 cập nhật mốc thời gian của chunk (chưa làm).

**Mẫu** (`scripts/m3_select_pilot.py`, seed 20261121, ra `dataset/organized/m3_state/tune/pilot.json`): 20 chỗ sửa trên 20 trang (một chỗ mỗi trang), 5 mỗi loại C/E/F/A, chỉ lấy chỗ sửa có ít nhất một câu cơ chế 2 đích (gold event có bằng chứng ở chunk sửa, cùng năm với sự kiện sửa). Ứng viên: C 11, E 6, F 11, A 10. Câu cơ chế 2 trên 20 trang: **79** (đích 23, cùng chunk 8, cùng trang 48); câu đích theo loại câu: list 11, order_gap 5, summary 4, first_last_next 3. Bộ `mech3` không dùng trong pilot (vector ba hệ giống nhau nên không phân biệt được ba hệ); câu cơ chế 1 trùng chunk sửa chỉ khoảng 3 câu.

**Cách dựng bản cũ** (`scripts/m3_build_old.py`): văn bản trang cũ = trang `real` với chunk sửa thay bằng bản `@past`; chỉ **cửa sổ ingest chứa chunk sửa** (mục, cắt từng khúc 8 chunk từ đầu mục) được trích lại bằng **prompt 10b nguyên bản** (`pass3_p10b_oc.py`, exec bản vá chỉ lọc cửa sổ, file gốc không đổi); các cửa sổ khác dùng lại mốc thô `real`; chạy lại gộp cấp trang (cặp cũ lấy verdict đã lưu theo nội dung; cặp mới gọi `PAIR_PROMPT` của `local/ingest_eval/judge.py`, 25 cặp mỗi lượt). Mô hình `opencode_deepseek_flash`, **thinking tắt**, cache riêng `data/llm_cache/m3_ingest_nothink/`, `m3_pair_nothink/`. Cùng prompt và cùng điều kiện thinking với graph `real` (xem `pending/02` mục "Cache và thinking"), nên trạng thái cũ mô phỏng đúng cách graph thật được dựng.

**Đã chạy:** 20 lượt trích cửa sổ (0 lỗi, 77 giây, trung vị 10,7 giây, 1.188 token ra) + 6 lượt gộp cặp = **26 lượt**. Kiểm trước không LLM: bản cũ của 20 trang chỉ khác `real` ở chunk sửa (20/20); thay mốc cửa sổ bằng chính mốc `real` rồi chạy gộp tái tạo đúng nút `real` ở 20/20 trang. Ra 1.098 nút cũ (`m3_state/tune/old/nodes/`), nạp vào **container Neo4j riêng `tam-neo4j-m3`** (cổng 7688, dữ liệu `data/neo4j_m3`); kho `real` (cổng 7687, 24.522 nút) không đổi. Neo4j bản Community chỉ có một database và ràng buộc duy nhất trên `Page.page`, `Chunk.chunk_id`, `Event.node_id`, nên bản cũ không đặt cạnh `real` được trong cùng database. Log lệnh gọi: `local/m3/llm_calls_old_*.jsonl`.

**Kiểm chất lượng trạng thái cũ** (so token của câu cũ/câu mới với nút trong chunk sửa, thô):
- C: 5/5 trang có nút chứa năm cũ; 2/5 (Josep_Rull, First_Air_Group) còn nút chứa token của năm mới (có thể là sự kiện khác cùng năm, chưa đọc tay).
- E: 5/5 trang không còn nút "đã kết thúc" của bản mới (đúng: bản cũ ghi "còn tiếp diễn").
- F: 4/5 trang có nút chứa giá trị sai (Scariolo, CBSs, Trinity, Hsinchu); Fulk_King_of_Jerusalem: câu cũ và mới không khác từ nào đủ 3 ký tự nên chỉ báo vô hiệu, chưa biết.
- A: nút gần như không đổi nhưng lệch 0 đến 5 nút mỗi trang (nhiễu nền của lần trích lại, cùng prompt và cùng thinking tắt; Michael_Batty 5, các trang khác 0 đến 1). Kết quả ba hệ ở trang loại A nên đọc kèm mức này.
- Ba trang cần đọc tay nếu muốn chắc: Fulk, Josep_Rull, First_Air_Group. Chưa làm.

**Đáp án để chấm** chỉ số trạng thái (nút lỗi thời sót, nút đóng nhầm, nút đổi thừa): đề xuất dùng kết quả trích lại cửa sổ `real` cùng điều kiện (chính là đầu ra Window-replace) thay vì graph `real` lưu sẵn, để không lẫn nhiễu giữa các lần chạy LLM. Chưa chốt.

**Chưa làm:** bộ lọc trang theo tập cho công cụ agent (cờ danh sách trang cho phép, áp cho text và graph) để kho cơ chế 3 tách biệt; ba hệ; prompt cập nhật của cơ chế 3 (cần viết mới, tiếng Anh); các cấu hình cố định (g, h, i...) trên kho cơ chế 3 (chưa đọc `v9_fixed_eval.py` xem nhận được tham số collection/Neo4j chưa).

## Kết quả pilot ba hệ trên tune (2026-11-21, một lần chạy mỗi hệ)

**Phạm vi.** 19 chỗ sửa trên 19 trang (đã bỏ Fulk_King_of_Jerusalem: chunk đổi không có nút nào ở bản cũ vì sự kiện đã nằm ở chunk 0, nên chỗ sửa không tác động lên graph; lý do ghi ở mục `excluded` của `pilot.json`). 76 câu cơ chế 2, trong đó 72 câu nằm trong bộ `v9_graph_tune_subset.json` (4 câu của Carl_August không có trong bộ này), ghi ở `dataset/organized/m3_state/tune/subset.json`. Mã: `scripts/m3_diff.py` (bước 1), `m3_window_replace.py`, `m3_diff_replace.py`, `m3_update_prompt.py` + `m3_llm_update.py` (cơ chế 3), `m3_state_metrics.py`, `m3_agent_by_group.py`. Mọi lượt LLM: `deepseek-v4.1-flash` qua OpenCode, thinking tắt, cache riêng (`m3_ingest_nothink`, `m3_diffrep_nothink`, `m3_pair_nothink`, `m3_update_nothink`, `agent_m3_nothink`).

**Ba hệ.** Bốn bước chung (diff chunk, cập nhật nút, gộp trùng cấp trang, tính lại `node_id` và ghi trang); chỉ bước 2 khác. Mỗi hệ bắt đầu từ cùng trạng thái cũ (`m3_state/tune/old`).
- Window-replace: thay mốc cả cửa sổ 8 chunk bằng mốc trích bản mới. Trong pilot lấy mốc từ ingest `real` đã lưu (cùng prompt, cùng thinking tắt, cùng cửa sổ), kết quả trùng nút `real` 20/20 trang.
- Diff-replace: trích lại chỉ chunk đổi (prompt 10b nguyên bản, 7 chunk kia gắn `(context only)`), bỏ mốc của chunk đổi, giữ mốc các chunk khác.
- Cơ chế 3: một lượt LLM mỗi chỗ sửa, nhận chunk đổi bản cũ và bản mới, chunk khác trong cửa sổ làm context, nút cũ mức 2 (tối đa 20); trả về `edit` / `close` / `invalidate` / `add`; mã kiểm (bằng chứng và quote phải nằm nguyên văn trong bản mới, ngày hợp lệ, số có trong chunk). `close` đặt `end_time`, `invalidate` đặt `invalidated_at`, `add` thêm nút mới. Lần chạy đầu (4 chỗ) loại C bị `edit` thay vì `invalidate` cộng `add`; đã siết prompt (`edit` chỉ cho đổi cách diễn đạt, đổi ngày hay giá trị là `invalidate` cộng `add`; mốc kết thúc có `phase` `end`) rồi chạy đủ 20 chỗ. Bước 3 của cơ chế 3 trong pilot mới chỉ loại trùng theo `node_id`, chưa gộp cặp bằng LLM giữa mốc `add` và nút cũ.

**Chỉ số trạng thái** (`m3_state_metrics.py`, không gọi LLM; so quote và giá trị cũ/mới của chỗ sửa với nút ở chunk đổi). `stale_open`: nút còn mang giá trị cũ mà không bị đóng hay vô hiệu; `new_present`: có nút mang giá trị mới; `lost_other` và `added_other`: nút ngoài chunk đổi bị mất hoặc mới xuất hiện (đổi thừa).

| hệ | còn giá trị cũ (mở) | nút cũ đã đánh dấu | có giá trị mới (/19) | nút mất ngoài chỗ sửa | nút thêm ngoài chỗ sửa |
|---|---|---|---|---|---|
| bản cũ (đối chứng) | 15 | 0 | 3 | 0 | 0 |
| Window-replace | 0 | 0 | 18 | 20 | 19 |
| Diff-replace | 0 | 0 | 18 | 1 | 5 |
| Cơ chế 3 | 1 | 10 | 17 | 0 | 0 |

Ghi chú: cột "nút cũ đã đánh dấu" đếm nút còn mang giá trị cũ nhưng có `invalidated_at` hoặc `end_time` (chỉ số đếm theo giá trị cũ, nên không bằng tổng nút bị đánh dấu); trong kho m3 sau khi nạp cơ chế 3 có 9 nút `invalidated_at` và 2 nút `end_time`. Đổi thừa của Window-replace chủ yếu là nhiễu khi trích lại cả cửa sổ: nút ở 7 chunk không đổi đến từ một lần trích khác với bản cũ (so với bản cũ). Số này cần đọc là "nhiễu khi trích lại cả cửa sổ", không phải lỗi thay thế. Hạn chế của chỉ số: không phân biệt "đánh dấu đúng" với "đánh dấu nhầm", loại A khó đo (quote trùng cả hai câu; tune-139 không thể đo), giá trị cũ F so theo tên.

**Đọc tay các trang nghi vấn.** Fulk: bỏ (xem trên). Josep_Rull và First_Air_Group: các token năm mới còn thấy ở bản cũ là của sự kiện khác (bầu cử, xét xử; Stenfeldt, colonel), không phải nút bị sửa; cả ba hệ xử lý chỗ sửa đúng. Cơ chế 3 để `phase` `point` cho mốc `add` của Josep_Rull, còn graph real và Diff-replace ghi `end`.

**Chi phí cập nhật (bước 2 và gộp cặp, 20 chỗ sửa gồm Fulk; log lệnh gọi không gắn trang nên không tách Fulk ra).** Giá dùng như `scripts/score_agent_runs.py`: vào 0,15, cache 0,003, ra 0,60 USD mỗi triệu token (giờ thấp điểm). Không có token cache nhà cung cấp trong các lượt này (`cached_input_tokens` = 0).

| hệ | lượt LLM | token vào | token ra | USD |
|---|---|---|---|---|
| Window-replace, đo thật (dùng mốc `real` lưu sẵn) | 0 | 0 | 0 | 0 |
| Window-replace, ước lượng nếu chạy lại (cùng 20 cửa sổ, lượt trích cửa sổ bản cũ) | 20 | 51.963 | 23.906 | 0,0221 |
| Diff-replace: trích | 20 | 52.302 | 9.131 | 0,0133 |
| Diff-replace: gộp cặp mới | 8 | 4.483 | 458 | 0,0009 |
| Diff-replace: tổng | 28 | 56.785 | 9.589 | 0,0142 |
| Cơ chế 3 (prompt cuối) | 20 | 50.817 | 2.751 | 0,0093 |
| Cơ chế 3, 4 lượt thử với prompt đầu (phát triển, không tính vào so sánh) | 4 | 10.283 | 545 | 0,0019 |

Log ingest `real` (`llm_calls_ingest_p10b_*.jsonl`) không ghi trang hay cửa sổ nên không đọc riêng được 19 cửa sổ; con số ước lượng của Window-replace lấy từ lượt trích cửa sổ bản cũ (cùng prompt, cùng cửa sổ, 20 lượt đo thật). Cơ chế 3 có ít token ra nhất (khoảng 138 mỗi chỗ sửa so với 1.195 của Window-replace và 457 của Diff-replace) vì chỉ phải nêu quyết định.

**Agent C trên 72 câu** (`--kind C --graph --prompt v5`, thinking tắt, 10 luồng cho Window-replace, 5 luồng cho hai hệ sau; Neo4j m3 cổng 7688 qua `--neo4j-url`; text và graph chỉ thấy 19 trang qua `--pages-file`; graph ẩn nút `invalidated_at` và ghi `(ended ...)` qua `--show-state`). Thư mục output: `20261121_125054` (Window-replace), `20261121_135241` (Diff-replace), `20261121_142450` (cơ chế 3). Không lỗi, không phải chạy lại.

| | Window-replace | Diff-replace | Cơ chế 3 |
|---|---|---|---|
| exact (72 câu) | 0,931 (67) | 0,903 (65) | 0,931 (67) |
| F1 | 0,973 | 0,967 | 0,974 |
| nhóm đích (21) | 19 | 17 | 18 |
| nhóm cùng chunk (6) | 6 | 6 | 6 |
| nhóm cùng trang (45) | 42 | 42 | 43 |
| loại C (24) / E (14) / F (19) / A (15) | 22 / 14 / 18 / 13 | 21 / 13 / 18 / 13 | 23 / 13 / 18 / 13 |
| lượt LLM của agent (tổng, 72 câu) | 230 | 218 | 226 |
| lượt gọi công cụ | 229 | 213 | 225 |
| token vào (trong đó cache nhà cung cấp) | 804.799 (519.424) | 755.068 (390.528) | 775.097 (448.128) |
| token ra | 20.646 | 19.494 | 20.330 |
| USD (72 câu) | 0,0568 | 0,0675 | 0,0626 |

Câu sai chung cả ba hệ: Good_Game_TV_program:0, Lenin_Peak:3, Michael_Batty:4, Real_Madrid_Baloncesto:0. Window-replace sai thêm Stefan_He_e:3; Diff-replace sai thêm First_Air_Group:6 và Marc_Bohan:3; cơ chế 3 sai thêm Marc_Bohan:3. Ghi chú đo: cache LLM cục bộ của agent dùng chung cho cả ba hệ (khóa gồm toàn bộ tin nhắn, kể cả kết quả công cụ), nên câu mà ba hệ trả kết quả công cụ giống nhau được phát lại; số token của các câu phát lại lấy từ lần gọi thật đầu tiên. Số câu phát lại hoàn toàn từ cache cục bộ: 5 (Window-replace), 19 (Diff-replace), 25 (cơ chế 3), nên chênh USD giữa các hệ phần nào phản ánh thứ tự chạy và mức cache nhà cung cấp, không chỉ chất lượng graph.

**Kết luận tạm.** (1) Về độ chính xác của agent, ba hệ gần như bằng nhau (65 đến 67 trên 72, chênh 2 câu); mẫu nhỏ và mỗi hệ một lần chạy nên không đủ kết luận hệ nào hơn. (2) Khác biệt thật nằm ở trạng thái và chi phí cập nhật: Window-replace đổi thừa nhiều nhất (39 nút) và tốn nhiều token ra nhất nếu chạy lại; Diff-replace đổi thừa ít (6 nút) và tốn ít hơn; cơ chế 3 không đổi thừa, ít token ra nhất, và là hệ duy nhất giữ lại nút cũ được đánh dấu vô hiệu hay đã kết thúc. (3) Bộ 72 câu cơ chế 2 và agent C quá dễ để phân biệt các hệ; muốn thấy khác biệt thật cần câu hỏi trực tiếp về trạng thái cũ/mới hoặc các cấu hình cố định g/h/i.

**Chưa làm (đã làm sau, xem mục cuối; g, h, i là agent, cấu hình cố định là f, f′, f″).** Chạy các cấu hình cố định cho ba hệ: cần lọc nút `invalidated_at` trong `TimelineRetriever` (hiện chỉ agent đọc được `--show-state`); `v9_fixed_eval.py` mới thêm biến `NEO4J_URL`. Đọc dấu vết các câu sai khác nhau (Stefan_He_e:3, Marc_Bohan:3, First_Air_Group:6). Bước 3 đầy đủ cho cơ chế 3 (gộp cặp bằng LLM giữa mốc `add` và nút cũ). Phân biệt "đánh dấu đúng" với "đánh dấu nhầm" trong chỉ số trạng thái.

### Mở rộng 40 chỗ sửa mới và đọc tay cơ chế 3 (2026-11-21, 5 luồng, một lần chạy mỗi hệ)

**Đọc tay 19 chỗ pilot (cơ chế 3):** 9 nút `invalidate` đều đúng (nút mang giá trị cũ); 14 mốc `add` đều có `quote` nằm nguyên văn trong bản mới. Lệch: Marc_Bohan (`close` một nút "được mời làm việc" bằng ngày rời hãng 1958), Hasselhoff (đổi CBS thành NBC bằng `edit`, đáng lẽ `invalidate` cộng `add`), MS_GNV_Azzurra (bỏ sót, nút cũ còn `quote` của câu cũ); ba mốc `add` để `phase` `point` thay vì `end`. Bước 3 đầy đủ (`--dedup`: ghép cặp mốc `add` với nút cũ qua cổng, phán quyết bằng prompt gộp cặp, `same` thì bỏ mốc `add` và hợp chunk nguồn): trên 19 chỗ có 1 cặp qua cổng, 0 gộp; trên 40 chỗ mới có 4 lượt gộp cặp (xem số trong bảng).

**Đợt mở rộng** (`M3_STATE_NAME=m3_state_ext`, `scripts/m3_select_pilot.py --any-edit --exclude-state m3_state`, seed 20261122): 40 chỗ sửa trên 40 trang tune khác (10 mỗi loại C/E/F/A); không đòi câu cơ chế 2 đích (chỉ 7 chỗ có), nên **không chạy agent**, chỉ đo trạng thái và chi phí cập nhật. Điều kiện cũ chỉ còn 14 ứng viên nên phải nới. Selftest 40/40; dựng bản cũ 39 lượt trích (1 trúng cache) + 19 lượt gộp cặp.

| hệ (40 chỗ) | còn giá trị cũ (mở) | nút cũ đã đánh dấu | có giá trị mới | nút mất ngoài chỗ sửa | nút thêm ngoài chỗ sửa |
|---|---|---|---|---|---|
| bản cũ | 48 | 0 | 1 | 0 | 0 |
| Window-replace | 1 | 0 | 36 | 42 | 41 |
| Diff-replace | 1 | 0 | 36 | 4 | 5 |
| Cơ chế 3 | 6 | 23 | 33 | 2 | 0 |

Chỉ số trạng thái đo bằng quote và giá trị nên có báo động giả và bỏ sót với cơ chế 3 (U-96 đếm 4 nút trùng năm cũ là sự kiện khác; USS_LCS, Mary_Raine đã `invalidate` và `add` đúng nhưng chỉ số báo không có giá trị mới). Kiểm bằng quy tắc hành động (C: có `invalidate` và `add`; E: có mốc `end` hoặc `close`; F: có `add`; A: không `invalidate`/`close`/`add`): **38/40 đúng**; hai chỗ hỏng là F ở 44_Union_Square và Supreme_Council_of_the_Armed_Forces (đổi tên tổ chức/giá trị trong câu không có nút nào ở bản cũ, LLM trả rỗng). Số `edit` của cơ chế 3: C 1, E 5, A 15.

| chi phí cập nhật, 40 chỗ | lượt LLM | token vào | token ra | USD |
|---|---|---|---|---|
| Window-replace, ước lượng (lượt trích bản cũ cùng cửa sổ) | 39 | 99.325 | 35.751 | 0,0363 |
| Diff-replace (40 trích + 11 gộp cặp) | 51 | 111.232 | 17.170 | 0,0269 |
| Cơ chế 3 (40 cập nhật + 4 gộp cặp) | 44 | 99.219 | 7.259 | 0,0192 |

Thứ tự theo đổi thừa và token ra lặp lại như trên 19 chỗ: Window-replace lớn nhất (83 nút, 35.751 token ra), Diff-replace nhỏ (9 nút, 17.170), cơ chế 3 nhỏ nhất (2 nút, 7.259). Chi phí cơ chế 3 vẫn là cận dưới vì chưa tính phần ngoài mốc `add`.

### Sửa prompt cơ chế 3 hai lần và bỏ `edit` (2026-11-21, chạy lại 59 chỗ = 19 pilot + 40 mới)

Ba bản (kết quả lưu ở `mech3_v1`, `mech3_v2`, `mech3` trong `m3_state` và `m3_state_ext`; kiểm bằng `scripts/m3_action_check.py`, `m3_state_metrics.py`):
- **v1:** prompt đầu. `edit` dùng cho cả đổi giá trị (Hasselhoff: CBS đổi NBC) và đổi nghĩa (E: "đang tiếp diễn" thành "đã kết thúc").
- **v2:** siết `edit` (chỉ khi mọi ngày, số, tên giữ nguyên), thêm "đọc lại bản mới và `add` mọi sự kiện chưa có nút", quy tắc `phase` `end`. Kết quả: F không có nút cũ được xử lý (44_Union_Square, Supreme_Council có `add`) nhưng `edit` sai vẫn còn (E 5, Hasselhoff).
- **v3 (đang dùng):** bỏ hẳn `edit` khỏi schema và mã; diễn đạt lại thì để nguyên nút (không liệt kê); đổi dù một ngày/số/tên là `invalidate` cộng `add`; kết thúc là `close` cộng `add`.

| 59 chỗ | v1 | v2 | v3 |
|---|---|---|---|
| đúng quy tắc hành động (C: `invalidate`+`add`; E: `end` hoặc `close`; F: `add`; A: không đổi) | 56 | 58 | 58 |
| `edit` ở C / E / F | 2 / 5 / 1 | 3 / 5 / 1 | 0 |
| mốc `add` có `phase` `end` / `point` ở C | 2 / 9 | 3 / 8 | 4 / 11 |
| chi phí cập nhật (lượt LLM, token vào, token ra, USD) | 62, 158.729 (gồm gộp cặp) *, 10.070, 0,0299 | 62, 158.729, 10.070, 0,0299 | 64, 146.328, 8.296, 0,0269 |

(* v1 đo ở lượt trước trên 20+40 chỗ: 44 lượt cho 40 chỗ mới, xem bảng chi phí phía trên.) v3 sửa được Hasselhoff (`invalidate` cộng `add` đúng, `phase` `end`), Josep_Rull (`phase` `end`), và E dùng `close` thay vì `edit`. Còn hỏng 1 chỗ: 44_Union_Square (F, đổi tên tổ chức trong câu không có nút nào) trả rỗng.

Chỉ số trạng thái theo loại: C, E, F không tệ hơn v2 (C ở đợt mở rộng: còn giá trị cũ 5 xuống 1, nút đã đánh dấu 10 lên 14). **Loại A "xấu đi" theo chỉ số** (pilot: còn giá trị cũ 1 lên 4, có giá trị mới 3 xuống 0; mở rộng: còn giá trị cũ 0 lên 15, có giá trị mới 10 xuống 0) vì chỉ số so `quote` với câu cũ/mới và nút diễn đạt lại không còn được cập nhật `quote`. Đây là hệ quả của việc bỏ `edit`: nút A vẫn đúng nghĩa nhưng `quote` lệch văn bản mới (agent đọc `text` và chunk nguồn nên không ảnh hưởng). Nếu cần `quote` khớp bản mới thì cập nhật `quote` bằng mã (không qua LLM) khi nút diễn đạt lại.

**Sửa chỉ số loại A (chốt 2026-11-21).** `quote` của nút chỉ dùng để kiểm lúc ingest/cập nhật (chống bịa, bằng chứng của mốc `add`) và làm đầu vào cho prompt gộp cặp; công cụ agent và các cấu hình cố định không đọc `quote`. Bỏ `edit` làm `quote` của nút diễn đạt lại (loại A) còn là câu cũ, vẫn đúng nghĩa. Chỉ số loại A không còn so `quote`: `new_present` = tập (ngày, phase) các nút ở chunk đổi không đổi so với bản cũ; `stale_open` = 0 theo định nghĩa. Số cuối cùng của cơ chế 3 (prompt v3), 59 chỗ sửa:

| hệ | còn giá trị cũ | nút cũ đã đánh dấu | đúng ở chunk đổi (/59) | nút mất ngoài chỗ sửa | nút thêm ngoài chỗ sửa |
|---|---|---|---|---|---|
| Window-replace | 1 | 0 | 53 | 62 | 60 |
| Diff-replace | 1 | 0 | 52 | 5 | 10 |
| Cơ chế 3 | 3 | 41 | 51 | 3 | 0 |

(Diff-replace: mất 1 + 4 = 5, thêm 5 + 5 = 10; cơ chế 3: mất 1 + 2 = 3, thêm 0.) Ba nút còn giá trị cũ của cơ chế 3 ở đợt 40 chỗ cần đọc tay (có thể là báo động giả kiểu U-96).

### Hạ tầng thêm cho thử cơ chế 3 và việc còn lại (2026-11-21)

**Cờ và biến mới (mặc định tắt, hành vi chung không đổi; test hiện có vẫn qua):** `run_agent_search.py`: `--pages-file <file tên trang>` (text và graph chỉ thấy các trang này; lọc theo tên đã chuẩn hóa), `--neo4j-url <bolt>` (trỏ graph khác, ví dụ Neo4j m3 cổng 7688), `--show-state` (công cụ `timeline` ẩn nút có `invalidated_at`, ghi `(ended <ngày>)` cho nút có `end_time`). `v9_fixed_eval.py`: biến môi trường `NEO4J_URL`. `neo4j_store.py`: `upsert_page` lưu thêm `end_time`, `invalidated_at` nếu có; `cell_events` trả thêm hai cột. Các script m3 đọc `M3_STATE_NAME` (mặc định `m3_state`, đợt mở rộng dùng `m3_state_ext`) và `M3_WORKERS`. Một container Neo4j m3 (7688) dùng chung cho cả ba hệ, nạp lần lượt theo trang (không mỗi hệ một container).

**Chưa làm / chưa chốt:**
1. (Đã làm, xem mục cuối) Các cấu hình cố định f, f′, f″ cho ba hệ: lọc nút `invalidated_at`/`end_time` trong `TimelineRetriever` (hiện chỉ công cụ agent có `--show-state`).
2. Đọc tay 3 nút còn giá trị cũ của cơ chế 3 ở đợt 40 chỗ (có thể là báo động giả) và chỗ F hỏng 44_Union_Square (trả rỗng).
3. Chạy cả tune (203 trang): ước khoảng 600 lượt LLM cho ba hệ (trích bản cũ, Diff-replace, cơ chế 3, cộng gộp cặp); cần chọn bộ câu hỏi đo trạng thái trực tiếp, vì agent C trên 72 câu không tách được ba hệ (65 đến 67 trên 72).
4. Cơ chế 3: chi phí 0,0269 USD cho 59 chỗ là cận dưới (gộp cặp giữa mốc `add` và nút cũ chỉ tốn vài lượt; chưa tính trường hợp chunk đổi nhiều câu). Phần `invalidated_at`/`end_time` chưa vào thiết kế docs/design.
5. Chưa commit: `dataset/organized/m3_state/`, `m3_state_ext/`, các script `scripts/m3_*.py`, sửa `run_agent_search.py`, `v9_fixed_eval.py`, `neo4j_store.py`, `graph_tools.py`, `text_corpus.py`, `docs/decisions/16`.


## Cấu hình cố định f, f′, f″ trên pilot, ba container (2026-11-21)

**Nhãn:** g, h, i là agent (A, B, B + graph); cấu hình cố định là a, b, d, f (`graph`), f′ (`graph_tb`), f″ (`graph_tt`) (`docs/eval/12`). Các ghi chú trước đây gọi nhầm "cấu hình cố định g/h/i".

**Hạ tầng.** Ba container Neo4j, mỗi hệ một cái: Window-replace `tam-neo4j-wr` (7689), Diff-replace `tam-neo4j-dr` (7690), cơ chế 3 `tam-neo4j-m3` (7688); `real` (7687) không đụng. Vector dùng chung `tam_chunks_dev_tune` (chỉ tìm trang và chunk vào). Cờ mới, mặc định tắt: `TimelineRetriever(state_filter)` (`STATE_FILTER=1`: bỏ nút `invalidated_at`, thêm `(ended <ngày>)` cho nút có `end_time`), `NODES_FILE=none` (không lọc theo danh sách nút; chấm theo ngày và text nên `node_id` mới không bị phạt), `NEO4J_URL`. Script: `local/m3/run_fixed.sh`, `scripts/m3_fixed_by_group.py`.

**Thiết lập.** 72 câu pilot (bộ câu hỏi Cơ chế 2 trên 19 trang, gold của `real` = đích của cập nhật); thinking tắt, cache `reader_nothink`, 5 luồng; mỗi cấu hình một lần; 164 prompt khác nhau mỗi lần chạy; 0 lỗi.

| Hệ | Lọc | f (`graph`) | f′ (`graph_tb`) | f″ (`graph_tt`) |
|---|---|---|---|---|
| Window-replace | không | 0,597 | 0,653 | 0,639 |
| Window-replace | có | 0,611 | 0,653 | 0,639 |
| Diff-replace | không | 0,597 | 0,639 | 0,667 |
| Diff-replace | có | 0,583 | 0,639 | 0,653 |
| Cơ chế 3 | không | 0,583 | 0,639 | 0,625 |
| Cơ chế 3 | có | 0,611 | 0,694 | 0,639 |

**Đọc kết quả.** Ba hệ lệch nhau 0 đến 0,06 (1 đến 4 câu trên 72), cùng mức với tune 600 của `real` (f′ 0,70, f″ 0,61 đến 0,66). Lọc chỉ có tác dụng với cơ chế 3 (pilot có 11 nút bị đánh dấu: 10 `invalidated`, 1 `end_time`; hai hệ kia 0), nhưng hai hệ kia vẫn lệch 1 câu giữa có/không lọc (nhiễu, chưa kiểm chứng nguyên nhân), nên mức tăng 4 câu của cơ chế 3 ở f′ chưa kết luận được. Theo nhóm câu, nhóm đích (21 câu) 0,48 đến 0,62 ở mọi hệ, thấp hơn nhóm cùng trang (0,60 đến 0,76). Gold `real` là đáp án đúng cho trạng thái sau cập nhật (bản cũ mô phỏng được cập nhật lên đúng bản `real`), nên dùng được; câu đích thấp ở cả Window-replace (tái tạo đúng nút `real`) nghĩa là các câu này vốn khó, không phải do cập nhật hỏng.

**Chưa có:** agent A, B, B + graph (g, h, i) trên ba hệ; chỉ có agent C (xem mục pilot trên).


## Chạy toàn bộ tune, ba hệ (2026-11-21)

> **Đính chính (2026-11-24):** số của agent (e′, agent C) trên mech3 trong mục này đã được chấm lại sau khi sửa luật chấm; dùng bảng ở mục "Kiểm tra cách chấm và đọc tay lỗi" ở cuối file. Số cấu hình cố định không đổi (qid dùng chung ảnh hưởng tối đa ±3 câu ở tune).

**Thiết lập.** 97 chỗ sửa trên tập tune; bản cũ dựng lại từ đầu (`M3_STATE_NAME=m3_state_full`), rồi cập nhật cũ → mới bằng ba hệ (Window-replace, Diff-replace, Cơ chế 3 có `--dedup`). Năm container: `tam-neo4j` 7687 (real = Window-replace, chỉ đọc), `tam-neo4j-old` 7689, `tam-neo4j-dr` 7690, `tam-neo4j-m3` 7688; vector dùng chung `tam_chunks_dev_tune` (chỉ chứa bản real). 3 luồng, thinking tắt (`opencode_deepseek_flash`), cache riêng, 429 chờ 40 s rồi thử lại (tối đa 8). Log đầy đủ: `local/m3/full/` (`manifest.tsv`, `run_full.log`, `RUN_INFO.md`, `<bước>.log`). Câu hỏi: timeline 334 câu (`subset.json`), mech3 160 câu (`subset_mech3.json`). Chỉ đo cấu hình **có đọc graph** (d, f, f′, f″, e′); agent C đầy đủ chỉ để tham chiếu vì vector/text chỉ có bản real nên không đo được graph.

**Trạng thái graph (đọc thẳng Neo4j, không LLM).**

| Hệ | nút cũ còn mở | đã đóng/vô hiệu | nút mới có | mất thừa | thêm thừa |
|---|---|---|---|---|---|
| Bản cũ | 60 | 0 | 24 | 0 | 0 |
| Window-replace | 2 | 0 | 86 | 173 | 189 |
| Diff-replace | 2 | 0 | 83 | 24 | 9 |
| Cơ chế 3 | 3 | 57 | 83 | 12 | 0 |

**Mech3 (160 câu), độ chính xác.** Cột e′ là agent chỉ có `timeline`, `events_of_chunk`, `list_pages` (`--graph-only`, prompt v6). "Có lọc" = ẩn nút `invalidated_at` và ghi "(ended …)" (`STATE_FILTER=1` cho cấu hình cố định; `--show-state` cho agent). Mọi lượt agent của ba hệ cũ/mới chạy **có** `--show-state` (Window-replace và Diff-replace không có nút đánh dấu nên cờ không đổi gì).

| Hệ | d | f | f′ | f″ | e′ |
|---|---|---|---|---|---|
| Bản cũ | 0,388 | 0,388 | 0,325 | 0,300 | 0,419 (67/160) |
| Window-replace | 0,813 | 0,831 | 0,594 | 0,550 | 0,781 (125/160) |
| Diff-replace | 0,800 | 0,788 | 0,581 | 0,506 | 0,775 (124/160) |
| Cơ chế 3, có lọc | 0,800 | 0,769 | 0,556 | 0,494 | 0,769 (123/160) |
| Cơ chế 3, không lọc | 0,588 | 0,544 | 0,438 | 0,419 | 0,588 (94/160) |

(Chấm lại 2026-11-24 bằng luật đã sửa: câu từ chối không tính đúng, qid dùng chung được ghép đúng câu. Số cũ lệch vài câu; xem mục cuối "Kiểm tra cách chấm". Luôn trả "No" đúng 73/160 = 0,456. Agent C tune 156/160 ở cả bốn hệ.)

e′ Cơ chế 3 theo loại, có lọc / không lọc (chấm lại): C 32/15 (trên 38), F 25/13 (trên 33), E 39/38 (trên 45), A 27/28 (trên 44). Lọc chủ yếu cứu loại C và F (giá trị cũ / sai từ đầu); loại A (diễn đạt lại) không đổi.

**Ghi chú về dòng "không lọc".** Dòng "Cơ chế 3, không lọc" ở các bảng chỉ là phép tắt thử (ablation), **bỏ qua khi so sánh ba hệ**: không lọc nghĩa là truy xuất phớt lờ các dấu `end_time`/`invalidated_at` mà chính cơ chế 3 tạo ra, nên sai là hệ quả tất yếu, không phản ánh chất lượng cập nhật. Hai hệ kia gần như không có nút đánh dấu nên bộ lọc không tác dụng với chúng. So sánh chính dùng dòng "có lọc". Giữ lại dòng này chỉ để cho thấy các dấu đánh dấu thật sự được dùng (e′ 0,769 so với 0,588).

**Kết luận.** (1) Cơ chế 3 chỉ ngang Window-replace và Diff-replace khi phía truy xuất đọc `end_time`/`invalidated_at`; không lọc thì kém khoảng 0,1 đến 0,2 ở cả cấu hình cố định lẫn agent. Đánh dấu ở ingest chỉ có giá trị khi truy xuất dùng nó. (2) Không lọc vẫn hơn bản cũ (e′ 0,588 so với 0,419) vì đã thêm nút mới. (3) Window-replace và Diff-replace ngang nhau ở mech3, Cơ chế 3 có lọc kém Window-replace khoảng 0,00 đến 0,06 (f 0,769 so với 0,831; f′ 0,556 so với 0,594; f″ 0,494 so với 0,550); Diff-replace ít đổi thừa hơn rất nhiều (mất/thêm 24/9 so với 173/189) và Cơ chế 3 ít nhất (12/0).

**Timeline cố định (334 câu), exact / F1.**

| Hệ | d | f | f′ | f″ |
|---|---|---|---|---|
| Bản cũ | 0,644/0,799 | 0,641/0,798 | 0,668/0,822 | 0,611/0,778 |
| Window-replace | 0,644/0,802 | 0,665/0,808 | 0,698/0,832 | 0,626/0,789 |
| Diff-replace | 0,650/0,804 | 0,662/0,808 | 0,674/0,825 | 0,623/0,782 |
| Cơ chế 3, không lọc | 0,656/0,804 | 0,650/0,801 | 0,671/0,830 | 0,623/0,784 |
| Cơ chế 3, có lọc | 0,659/0,801 | 0,647/0,793 | 0,674/0,818 | 0,629/0,786 |

Chênh giữa các hệ nhỏ (nhiều nhất 0,03, ở f′); bộ timeline gần như không phân biệt được ba hệ và không đo nhiễu nên không kết luận hơn kém. F1 lấy trung bình trên các hàng có trường `f1` (không tính `order_gap`).

**Agent C đầy đủ (tham chiếu, không đo graph).** Timeline 334 câu exact/F1: bản cũ 0,850/0,939; Window-replace 0,880/0,944; Diff-replace 0,856/0,943; Cơ chế 3 0,853/0,942 (khoảng 10,6 đến 10,8 nghìn token vào mỗi câu). Mech3 160 câu: cả bốn hệ 155/160 (cùng 5 câu sai). Agent gọi `timeline` ở 13/160 câu (8%), 147 câu chỉ dùng vector/text; ở 71 câu loại C/F kết quả công cụ chứa giá trị mới 70 lần kể cả bản cũ. Lượt mech3 của ba hệ sau bản cũ chạy 12 đến 17 giây vì cache agent dùng chung (token không phải số đo thật).

**Lưu ý.** Chênh 155 và 153 ở agent C đã được giải thích (xem mục cuối): lỗi ghép dòng của `m3_agent_tool_usage.py` và luật chấm câu từ chối; số đúng là 156/160 ở cả bốn hệ. `run_meta.json` của các lượt agent cũ không ghi `show_state` (đã thêm trường từ lượt e′ không lọc; cache `agent_m3_graphonly_nostate_nothink`). Lượt e′ không lọc: `output/20261121_220211`.

**Chưa làm.** Chi phí cập nhật ở quy mô 97 chỗ (từ `local/m3/llm_calls_*_m3_state_full.jsonl`); đọc tay các lỗi của Cơ chế 3 (3 nút cũ còn mở, 57 nút đánh dấu, ca đóng nhầm như `tune-049`); e′ cho timeline (chưa chạy, theo quyết định timeline không cần e′); chưa commit.

### e′ trên tập timeline và tổng hợp so sánh (2026-11-23)

**Chạy.** e′ (agent chỉ có công cụ graph, `--graph-only`) trên 334 câu timeline, prompt v5, `--show-state` (có lọc), thinking tắt, 5 luồng, OpenCode `deepseek-v4.1-flash`, cache riêng `data/llm_cache/agent_m3_graphonly_tl_nothink`. Bốn hệ chạy tuần tự (Old 7689, Window-replace 7687, Diff-replace 7690, Cơ chế 3 7688), cả 4 hệ 334/334 câu `answer`, không có `error`/`max`. Script `local/m3/full/run_eprime_tl.sh`, log `run_eprime_tl.log`.

| Hệ | exact | F1 | first_last_next (93) | list (124) | order_gap (84) | summary (33) |
|---|---|---|---|---|---|---|
| Old | 0,769 | 0,890 | 0,849 | 0,710 | 0,833 | 0,606 |
| Window-replace | 0,790 | 0,886 | 0,817 | 0,718 | 0,917 | 0,667 |
| Diff-replace | 0,784 | 0,889 | 0,849 | 0,718 | 0,893 | 0,576 |
| Cơ chế 3 (có lọc) | 0,799 | 0,898 | 0,860 | 0,734 | 0,881 | 0,667 |

Cả bốn hệ chênh nhau trong 0,03 (tối đa khoảng 10 câu trên 334), không có phép đo nhiễu, nên không kết luận hệ nào thắng. Cơ chế 3 không làm hỏng câu timeline dù giữ nút cũ có đánh dấu.

**Cơ chế 3 có thắng không.** Không. Đếm cấu hình có Cơ chế 3 (có lọc) cao nhất theo exact:

| Tập | Cơ chế 3 cao nhất |
|---|---|
| Timeline (d, f, f′, f″, e′) | 3/5 (d, f″, e′; Window-replace thắng f, f′), chênh 0,003 đến 0,013 (1 đến 4 câu) |
| Mech3 (d, f, f′, f″, e′) | 0/5 (Window-replace hoặc Diff-replace luôn ≥; e′ 0,812 so với 0,819) |

Kết luận đúng: Cơ chế 3 **ngang** hai baseline khi truy xuất đọc dấu `end_time`/`invalidated_at`, và **ít đổi graph hơn nhiều** (mất/thêm 12/0 so với 173/189 và 24/9). Lợi thế nằm ở chất lượng graph và giữ lịch sử, không ở điểm QA.

**Về dòng "không lọc".** Chỉ là phép tắt thử, không đưa vào so sánh ba hệ (xem ghi chú ở trên). Các bảng giữ dòng đó cho đầy đủ số liệu.

**Token và thời gian (không dùng để so sánh).** Bốn hệ dùng chung một thư mục cache, nên các hệ chạy sau chủ yếu trúng cache và số token là số phát lại. Lượt gọi thật: Old 417, Cơ chế 3 378, Diff-replace khoảng 170 (975 bước trừ 795 trúng cache); Window-replace chưa đếm được (xem sự cố bên dưới). Tổng token vào/ra gần như bằng nhau (khoảng 2,2 triệu / 71 nghìn mỗi hệ).
- **Thời gian có gồm 429.** SDK tự chờ rồi thử lại trong cùng một lượt gọi nên `e2e_s` và `ttft_s` gồm thời gian chờ. Hệ Old: trung vị `e2e` 2,1 giây nhưng trung bình 18,4 giây, 130 lượt trên 20 giây chiếm 93% tổng thời gian; Cơ chế 3: trung vị 2,4 giây, trung bình 6,1 giây, 62%. Các tổng như "llm_time 15,9 nghìn giây" chủ yếu là chờ 429, không so được giữa các hệ. Dùng trung vị `e2e` của lượt gọi thật (khoảng 2 giây) nếu cần thời gian một lượt. Chưa có trường tách riêng thời gian chờ thử lại.

**Sự cố khi chạy.** (1) Bốn container Neo4j đã dừng sẵn, phải `docker start` lại. (2) Một lượt đầu 10 luồng không dừng hẳn và chạy chồng với lượt 5 luồng khoảng 25 phút, nên có một phần lượt gọi API bị trả hai lần (ước tính tối đa khoảng một lượt Old, dưới 1 USD theo giá 0,15/0,60). (3) Khi dọn tiến trình thừa tôi xóa nhầm thư mục `output/20261123_075510` của lượt Window-replace hợp lệ; kết quả được dựng lại bằng chạy lại từ cache (`output/20261123_081354`, 0 lần gọi API), và token/thời gian của hệ này dựng lại từ log `local/m3/full/eprime_tl_wr.log`.

Thư mục kết quả e′ timeline: Old `20261123_072930`, Window-replace `20261123_081354`, Diff-replace `20261123_110044`, Cơ chế 3 `20261123_110327`. Cache và thinking: xem phần chạy ở trên.

**Việc còn lại.** Chi phí cập nhật 97 chỗ (số lần gọi, token, USD); đọc tay 3 nút còn mở, 57 nút đánh dấu và các ca đóng nhầm (ví dụ `tune-049`); đối chiếu luật chấm agent C (155 so với 153); commit.

### Chi phí (USD) của tune đầy đủ (2026-11-23)

Giá: input 0,15, input đọc từ cache của API (`cached_input_tokens`, số API trả về, không phải cache cục bộ) 0,003, output 0,60 USD mỗi triệu token. Cache của API ở các lượt cập nhật đều bằng 0.

**Cập nhật 97 chỗ sửa từ trạng thái cũ** (log `local/m3/llm_calls_*_tune_m3_state_full.jsonl`). Log chỉ ghi token của lượt **gọi thật**; 29 lượt trúng cache cục bộ (từ pilot) không có token trong log, nên cột "ước đủ 97" nhân số token trung bình mỗi lượt gọi thật với số lượt cần gọi.

| Hệ | Bước | Lượt cần | Gọi thật | Token vào/ra đo được | USD đo được | Token vào/ra ước đủ | USD ước đủ |
|---|---|---|---|---|---|---|---|
| (nền) Dựng bản cũ | trích cửa sổ | 97 | 68 | 180.329 / 84.738 | 0,0779 | 257.300 / 120.900 | 0,111 |
| | gộp cặp | 41 | 27 | (chung log với Diff-replace) | | 25.600 / 2.700 | 0,0055 |
| Window-replace | trích cửa sổ (ước theo cửa sổ bản cũ) | 97 | – | không đo được | – | 257.300 / 120.900 | 0,111 |
| | gộp cặp (ước theo bản cũ) | 41 | – | | | 25.600 / 2.700 | 0,0055 |
| | **tổng** | | | | | | **khoảng 0,117** |
| Diff-replace | trích chunk đổi | 97 | 68 | 181.735 / 27.605 | 0,0438 | 259.300 / 39.400 | 0,0625 |
| | gộp cặp | 44 | 25 | | | 27.500 / 2.900 | 0,0059 |
| | **tổng** | | | | | | **khoảng 0,068** |
| Cơ chế 3 | quyết định (Update) | 97 | 68 | 167.725 / 10.345 | 0,0314 | 239.300 / 14.700 | 0,0447 |
| | gộp cặp | 23 | 20 | 9.857 / 855 | 0,0020 | 11.300 / 1.000 | 0,0023 |
| | **tổng** | | | 177.582 / 11.200 | **0,0334** | 250.600 / 15.700 | **khoảng 0,047** |

- Cơ chế 3 rẻ nhất (ít token ra nhất, khoảng 150 mỗi chỗ sửa so với 1.250 của trích cả cửa sổ và 400 của Diff-replace); Diff-replace giữa; Window-replace đắt nhất (khoảng 2,5 lần Cơ chế 3). Cả ba dưới 0,12 USD cho 97 chỗ sửa.
- **Window-replace không đo trực tiếp được.** Log ingest `real` (`local/ingest_eval/judge_out/llm_calls_ingest_p10b_*.jsonl`) không ghi trang hay cửa sổ (`query_id` là `-`) và là lượt chạy ngày 13 đến 15/11 (thinking có thể bật), nên không tách riêng được cửa sổ bị đổi. Số của Window-replace lấy từ lượt trích đúng các cửa sổ đó ở bản cũ (cùng prompt, cùng cửa sổ, chỉ khác chunk sửa), là ước lượng gần.
- Mỗi bước trích dùng cùng cửa sổ đầu vào (khoảng 2.650 token), khác nhau ở output: nên chênh lệch giữa các hệ gần như hoàn toàn nằm ở token ra.

**Agent e′ trên timeline (334 câu mỗi hệ)**, nếu gọi thật toàn bộ (token phát lại từ cache cục bộ, không phải số đã trả):

| Hệ | Input | trong đó cache API | Output | USD |
|---|---|---|---|---|
| Old | 2.201.943 | 1.240.064 | 71.663 | 0,191 |
| Window-replace | 2.204.360 | 1.292.032 | 71.831 | 0,184 |
| Diff-replace | 2.195.515 | 1.204.352 | 71.473 | 0,195 |
| Cơ chế 3 | 2.181.197 | 1.204.992 | 70.984 | 0,193 |

Bốn hệ chênh nhau dưới 6%, không phân biệt được chi phí hỏi đáp giữa các hệ. Tiền thật đã trả thấp hơn vì chỉ lượt gọi thật bị tính.

### Đọc tay lỗi của Cơ chế 3, tune đầy đủ (2026-11-23)

Đọc 8 ca bị luật `m3_action_check.py` đánh dấu hỏng, 3 nút `stale_open` và vài ca `lost_other`/`new_present=0` (so đoạn sửa, nút LLM thấy, quyết định của LLM; không gọi LLM).

| Nhóm | Ca | Nhận xét |
|---|---|---|
| Luật báo nhầm (Cơ chế 3 làm đúng) | tune-174, 191 (C), 073, 059 (F) | Không có nút cũ nào để vô hiệu (bản cũ không trích sự kiện bị sửa; 174, 191 vẫn `add` đúng mốc mới), hoặc chỗ sửa chỉ đổi tên thực thể không nằm trong nút nào (073: Tower of Antonia → David; 059: Botanical → Hortus) |
| Bỏ sót (không thêm mốc mới) | tune-158 (C), 103 (F), 058 (F, có thể coi là trùng nút `N1`/`N3`) | LLM trả `changes=[]`, `add=[]` dù mốc đích chưa có trong graph cũ (158: "silence ended 1945"; 103: "relegated 1996–97") |
| Sai hành động | tune-045 (E) | Bản cũ "has played for Dons since 1947" → mới "from 1947 to 1948". Đáng ra `close N2` (kết thúc 1948, tiến hóa); LLM `invalidate N2` rồi `add` mốc "1947–1948" (đánh là sai từ đầu, ẩn lịch sử). Đây đúng là nhầm Evolution với Falsehood |
| `stale_open` thật | tune-049 (E) | Đóng nhầm `N3` ("led the team to playoffs in 2016", sự kiện `point`) thay vì `N1` ("Cooper was hired 2014", trạng thái `start` còn mở); `N1` vẫn mở |
| `stale_open` giả | tune-186, 096 (C) | Nút sai đã vô hiệu đúng (`N3` 1984→1987; `N2` 2013→2012); nút bị tính còn mở là nút khác cùng chunk, trùng năm cũ nhưng đúng (Dickerson 1984 rushed; league began 2013) |

Tóm lại trên 97 chỗ sửa: **1 sai hành động** (tune-045), **1 đóng nhầm nút** (tune-049), **2 đến 3 bỏ sót** (158, 103, có thể 058), còn lại đúng hoặc luật báo nhầm. `stale_open` thật là 1 chứ không phải 3. Hai lỗi có hành động sai đều là loại mà một ràng buộc nhẹ (chỉ `close` nút trạng thái `start`/còn mở; quan hệ đơn trị hay đa trị) bắt được; cả hai chỉ chiếm 2/97 nên chưa đủ để nói bắt buộc phải có ontology.

`lost_other` (12 nút): sinh ra ở bước gộp lại cấp trang khi thêm mốc mới (mốc `add` trùng hoặc gộp với nút cũ), không phải xóa chủ động.

**Chất lượng bản cũ.** Bản cũ do LLM trích lại cửa sổ từ văn bản cũ nên bản thân có thiếu và mâu thuẫn, không liên quan hệ cập nhật nào: nhiều sự kiện bị sửa vốn không có nút (191, 103, 158), và có nút mâu thuẫn nhau (tune-016: `N4` "Took ended 1981" cùng `N6` "Took began 1986" và `N16` "Took ended 1995"). Window-replace đổi 173 nút ngoài chỗ sửa vì trích lại cả cửa sổ cho kết quả khác nhau giữa các lần chạy, còn Diff-replace và Cơ chế 3 chỉ đụng nút gần chỗ sửa.

### Có cần ontology cho Cơ chế 3 không (2026-11-23)

**Quyết định: không đưa ontology vào bản làm trong đồ án; ghi thành hướng phát triển.**

Lý do:
1. **Không có bằng chứng cần.** Cơ chế 3 chỉ dùng LLM (không có ontology, không có luật đơn trị/đa trị) mà ngang Window-replace và Diff-replace trên tune 97 chỗ sửa. Trong lần đọc tay, chỉ 2/97 ca có hành động sai mà ràng buộc kiểu ontology bắt được: tune-045 (`invalidate` thay vì `close` một quan hệ đơn trị) và tune-049 (đóng nhầm nút `point` thay vì nút trạng thái còn mở). Cả hai bắt được bằng luật code đơn giản ở bước kiểm quyết định, không cần ontology.
2. **Chỗ duy nhất ontology cần thật chưa có dữ liệu.** Loại câu "khoảng chồng lấn" (decision 11, mục 3.5: cũ `[1500, 1520]`, mới `[1505, 2025]`) cần biết quan hệ đơn trị hay đa trị. Bộ dữ liệu hiện có không có loại câu này; muốn đo phải dựng thêm câu và đáp án.
3. **Chi phí thêm lớn.** Ontology nằm ở tầng ingest, dùng chung Cơ chế 2 và 3 (chuẩn hóa quan hệ, kiểm ràng buộc, gắn số phiên bản ontology vào dữ liệu đã nạp). Thêm sau nghĩa là nạp lại và đo lại cả Cơ chế 2.
4. **Phạm vi đồ án.** Scope cho phép đi sâu 2 trong 3 cơ chế.

**Khi nào mới cần ontology (giả thuyết, chưa kiểm).** Bộ dữ liệu càng rộng và phức tạp thì LLM đơn lẻ và luật code càng khó đủ: nhiều loại quan hệ cùng lúc (đơn trị lẫn đa trị), khoảng thời gian chồng lấn, nhiều miền, nhiều nguồn mâu thuẫn. Khi đó luật viết tay không mở rộng được từng miền, còn ontology khai báo một lần rồi dùng lại. Tune này (Wikipedia, một chỗ sửa mỗi trang, giá trị bị thay trực tiếp) không có các điều kiện đó, nên kết quả hiện tại không phản bác cũng không chứng minh được nhu cầu này.

**Hướng phát triển.** Loại câu "khoảng chồng lấn" kèm ontology nhẹ (`:temporal`, `:exclusiveBy`, Turtle) trên bộ dữ liệu rộng hơn, và luật kiểm đơn giản trong lúc chờ ("chỉ `close` nút trạng thái còn mở"; "bản cũ nói hiện tại, bản mới có mốc kết thúc thì `close`, không `invalidate`").

## Tập valid, ba hệ (2026-11-23 đến 24)

> **Đính chính (2026-11-24):** số e′ và agent C trên mech3 của mục này đã chấm lại; dùng bảng ở mục "Kiểm tra cách chấm và đọc tay lỗi" ở cuối file. Số cấu hình cố định và timeline không đổi.

**Thiết lập (đóng băng theo tune, không chỉnh lại sau khi thấy valid).** 93 chỗ sửa trên 93 trang valid (C 26, E 26, F 26, A 15; chọn bằng `m3_select_pilot.py --set valid --any-edit --per-type 26`, seed 20261121), 323 câu timeline, 147 câu mech3. Các hệ và cấu hình như tune: Old, Window-replace (= `real`), Diff-replace, Cơ chế 3 có `--dedup` (kết quả chính là bản **có lọc**; "không lọc" chỉ là phép tắt thử, bỏ qua khi so sánh); d / f / f′ / f″ cố định, e′ (agent chỉ công cụ graph) và agent C (số tham chiếu). 5 luồng, thinking tắt (`opencode_deepseek_flash`), **mỗi lần chạy một thư mục cache riêng** (`data/llm_cache/valid/<tên>`), nên token và thời gian là số thật. Script `local/m3/valid/run_valid.sh` (37 bước, tất cả xong, không bước nào thất bại); log, `stats.log`, `manifest.tsv` ở `local/m3/valid/`. Đã tách thời gian chờ thử lại 429 khỏi thời gian thật (`retry_wait_s`, `attempts`). Biến `M3_SET=valid` (mặc định `tune`) điều khiển các script.

**Trạng thái graph.** Node cũ còn mở: Old 70, Window-replace 2, Diff-replace 2, Cơ chế 3 4. Mất / thêm thừa: Window-replace 116/91, Diff-replace 15/5, Cơ chế 3 8/0 (66 nút đánh dấu). Cùng chiều với tune.

**Mech3 (147 câu, đúng / tổng):**

| Hệ | d | f | f′ | f″ | e′ |
|---|---|---|---|---|---|
| Old | 55 | 52 | 38 | 31 | 66 |
| Window-replace | 115 | 111 | 75 | 65 | 120 |
| Diff-replace | 112 | 106 | 77 | 72 | 116 |
| Cơ chế 3, có lọc | 113 | 97 | 75 | 68 | 115 |
| Cơ chế 3, không lọc | 79 | 70 | 52 | 49 | 86 |

Agent C (tham chiếu): Old 139, Window-replace 143, Diff-replace 144, Cơ chế 3 144. Luôn trả "No" đúng 65/147 = 0,442. Số e′ và agent C đã chấm lại bằng luật đã sửa (xem mục cuối).

**Timeline (323 câu, exact / F1):**

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---|---|---|---|---|---|
| Old | 0,681/0,798 | 0,718/0,803 | 0,678/0,809 | 0,573/0,736 | 0,762/0,878 | 0,851/0,928 |
| Window-replace | 0,743/0,836 | 0,762/0,825 | 0,734/0,833 | 0,616/0,747 | 0,839/0,924 | 0,858/0,945 |
| Diff-replace | 0,724/0,820 | 0,759/0,825 | 0,715/0,814 | 0,610/0,741 | 0,820/0,914 | 0,864/0,944 |
| Cơ chế 3, có lọc | 0,731/0,819 | 0,749/0,808 | 0,724/0,823 | 0,610/0,743 | 0,817/0,906 | 0,833/0,919 |
| Cơ chế 3, không lọc | 0,712/0,812 | 0,743/0,814 | 0,712/0,811 | 0,604/0,743 | – | – |

(e′ và agent C timeline chỉ chạy bản có lọc.)

**Đọc kết quả.** Cơ chế 3 (có lọc) ngang hai baseline ở hầu hết cấu hình, kém vài điểm chứ không thắng: mech3 kém Window-replace 2 câu ở d, 14 câu ở f (97 so với 111), bằng ở f′, hơn 3 ở f″, kém 5 ở e′ (115 so với 120); timeline kém 0,01 đến 0,02 exact ở d, f, e′. Bản cũ thấp hơn hẳn trên mech3 (55 đến 72 so với 112 đến 127), còn trên timeline chỉ thấp hơn một chút. Không lọc kém bản có lọc khoảng 30 câu ở d và f, 29 ở e′. Kết quả lặp lại kết luận tune: Cơ chế 3 chỉ ngang khi truy xuất đọc dấu `end_time` / `invalidated_at`; mỗi cấu hình chạy một lần, không có phép đo nhiễu.

**Chi phí valid** (lượt gọi thật, giá 0,15 / 0,003 / 0,60 USD mỗi triệu token; cache API là số API trả về): cập nhật khoảng 0,22 USD tổng (trích bản cũ 0,099, Diff-replace 0,062, quyết định Cơ chế 3 0,046, gộp cặp 0,014); bài test khoảng 3,0 USD (21.065 lượt gọi thật: mech3 cố định 0,23, e′ mech3 0,27 + 0,06 không lọc, timeline cố định 0,82, e′ timeline 0,68, agent C mech3 0,18, agent C timeline 0,77). Thời gian LLM gồm chờ 429 (khoảng 60% thời gian agent), thời gian thật tách ở `stats.log`.


## Kiểm tra cách chấm và đọc tay lỗi (2026-11-24)

### Lỗi tìm thấy ở luật chấm mech3 và cách xử lý

| # | Lỗi | Ảnh hưởng | Xử lý |
|---|---|---|---|
| 1 | `m3_mech3_score.match` lấy từ yes/no **đầu tiên xuất hiện bất kỳ đâu** trong câu trả lời. Câu từ chối kiểu "I cannot determine this: **no** page about ... was found" bị đọc thành "No", nên được điểm khi gold là "No" | Phồng điểm của agent (540 trong 2.610 câu trả lời có/không ở valid là câu từ chối; 43 câu bị chấm khác luật gốc). Cấu hình cố định không ảnh hưởng (câu trả lời luôn mở đầu bằng Yes/No) | Câu không mở đầu bằng yes/no mà có cụm từ chối ("cannot determine", "no passage"...) tính sai. Bản cũ của script lưu ở `local/m3/m3_mech3_score.py.bak_2026-11-24` |
| 2 | **qid dùng chung** ở tune: 14 qid ứng với hai câu hỏi khác nhau, `Q[qid]` giữ câu nạp sau, nên 6 dòng của subset tune bị chấm với đáp án của câu khác (valid không có, 0 dòng) | Tune: số cấu hình cố định thấp hơn thực 1 đến 3 câu | Đã sửa: dòng agent chọn câu có nội dung nằm trong `question`; dòng cấu hình cố định ghép theo vị trí (thứ tự dòng đúng bằng thứ tự câu x biến thể, script kiểm trước khi dùng): `getq`, `score` trong `m3_mech3_score.py` |
| 3 | Câu verify_false có gold dạng "No, <giá trị đúng>" nhưng luật chỉ so cực tính (không đòi nêu giá trị) | Trả lời "No" không kèm giá trị đúng vẫn được điểm; **luôn trả "No" đúng 65/147 (0,44) ở valid, 73/160 (0,46) ở tune**, cao hơn điểm của bản cũ ở nhiều cấu hình (Old d 55/147) | Chưa đổi luật chính; thêm số chấm chặt (phải nêu đúng giá trị) ở bảng dưới, thứ hạng các hệ không đổi |
| 4 | Câu giá trị chấm bằng độ phủ từ ≥ 70%, so khớp chuỗi con (số "17" khớp "2017") | Hơi dễ. Kiểm trên C/year: câu đúng nhưng còn chứa giá trị cũ rất hiếm (0 đến 1 trên 16, riêng agent không lọc 4/10) | Giữ, ghi chú |
| 5 | `m3_agent_tool_usage.py` ghép dòng bằng `next(x ... if x["idx"] == idx)`, nên với idx trùng lấy nhầm dòng đầu | Giải thích chênh 155 và 153 ở agent C tune (nay hai script cùng gọi `match` nhưng tool_usage vẫn ghép sai các idx trùng, 152 so với 154) | Dùng `m3_mech3_score.py` làm số chính (156/160) |

**Công thức timeline** (`v9_score.py`: exact = mọi mốc chuẩn khớp ngày tương thích và từ khóa, đúng thứ tự, không thừa; F1 chỉ tính trên dòng có mốc, nên câu `order_gap` không có F1): chạy `v9_score.py . selftest` (không LLM) trên 1.850 câu: đáp án mẫu đúng 100% (kể cả khi đảo thứ tự các mốc cùng ngày), cố ý bỏ một mốc, đảo thứ tự, thêm mốc thừa, sai số đều bị trừ điểm đúng như mong đợi (885/886 ca đảo thứ tự, còn lại 100%). Không thấy lỗi.

### Số mech3 sau khi sửa (số câu đúng)

| Hệ | Tune e′ | Tune agent C | Valid e′ | Valid agent C |
|---|---|---|---|---|
| Old | 67/160 (trước 74) | 156 | 66/147 (trước 72) | 139 (trước 140) |
| Window-replace | 125 (trước 130) | 156 | 120 (trước 127) | 143 (trước 144) |
| Diff-replace | 124 (trước 131) | 156 | 116 (trước 122) | 144 |
| Cơ chế 3, có lọc | 123 (trước 130) | 156 | 115 (trước 125) | 144 |
| Cơ chế 3, không lọc | 94 (trước 99) | – | 86 (trước 93) | – |

Cơ chế 3 có lọc kém Window-replace 2 câu ở tune và 5 câu ở valid trên e′ (trước đây ngang). Cấu hình cố định của valid không đổi; của tune đổi vài câu do ghép đúng qid dùng chung (Old 62/62/52/48, Window-replace 130/133/95/88, Diff-replace 128/126/93/81, Cơ chế 3 có lọc 128/123/89/79, không lọc 94/87/70/67; trước đó thấp hơn 1 đến 3 câu), đã cập nhật ở bảng tune trên.

**Chấm chặt (verify_false phải nêu đúng giá trị), valid, đúng / số đúng theo luật thường:**

| Hệ | d | f | f′ | f″ | e′ | Agent C |
|---|---|---|---|---|---|---|
| Old | 37/55 | 35/52 | 22/38 | 17/31 | 46/66 | – |
| Window-replace | 103/115 | 97/111 | 63/75 | 52/65 | 106/120 | 127/143 |
| Diff-replace | 102/112 | 95/106 | 65/77 | 58/72 | 102/116 | – |
| Cơ chế 3, có lọc | 99/113 | 82/97 | 61/75 | 53/68 | 101/115 | 129/144 |

Điểm tụt 10 đến 18 câu nhưng thứ hạng giữ nguyên: Cơ chế 3 kém Window-replace nhẹ ở d, e′ (4 đến 5 câu), nhiều hơn ở f (15 câu).

> **Đính chính (2026-11-25):** bảng chấm chặt của valid ở trên **không tái lập được**: tôi không còn script đã tạo ra nó. Script mới `local/m3/final_mech3_strict.py` (verify_false phải chứa ≥70% từ của đáp án chuẩn) cho số khác và ít tụt hơn; xem bảng "Chấm chặt" của valid và test_clean ở mục test_clean. Dùng bảng mới.

### Đọc tay lỗi trên valid

**Luật kiểm hành động báo hỏng 8/93 ca:**

| Nhóm | Ca | Nhận xét |
|---|---|---|
| Làm đúng, luật báo nhầm | valid-138, 002, 032 | 138: bản cũ không có nút nào để vô hiệu, LLM vẫn thêm đúng mốc mới; 002 và 032: thêm đúng mốc mới (1864, 1843) nhưng ở dạng `point`/`start` thay vì mốc kết thúc |
| Bỏ sót (không thêm mốc mới) | valid-197 | "1905 → 1904": mốc "mua 40 đầu máy kết thúc" chưa có trong graph cũ, LLM không đổi gì |
| Chi tiết không nằm trong nút | valid-191, 110, 130, 133 (F) | Chỗ sửa đổi tên thực thể trong chi tiết (Philadelphia → Pittsburgh, Italy → France, Los Angeles → Oakland, Tretyakov → Grabar Centre). Nút cũ vốn không chứa chi tiết đó nên LLM trả `changes=[]`, `add=[]` là hợp lý, nhưng graph mới (`real`) có chi tiết trong văn bản nút nên Window-replace trả lời được |

**`close` trên nút `point` (đếm lại 2026-11-24 từ `mech3/raw/*.json` và `old/nodes`):** trên tất cả lệnh `close`, tune 1/10 (tune-049, lỗi thật: đóng nhầm nút `point` "Cooper led the team to the playoffs in 2016", nút trạng thái `start` vẫn mở) và valid 1/13 (valid-009: đóng nút `point` "D8233 moved to the Mangapps Farm Railway" bằng mốc 1993, kèm `add` mốc `end`; chưa đánh giá là lỗi hay chấp nhận được). Tức 2 trường hợp trên 190 chỗ sửa; chưa sửa, chưa chạy lại (nếu sửa thì nên chặn bằng mã kiểm, không đổi prompt).

**Nhận xét chung (tune và valid):**
- Thao tác `edit` (sửa trường của nút) **đã bị bỏ khỏi schema và mã từ prompt v3 (2026-11-21, xem mục "Sửa prompt cơ chế 3 hai lần và bỏ `edit`")**, nên trên 190 chỗ sửa (97 tune + 93 valid) chỉ có `close`, `invalidate`, `add`; số `edit` bằng 0 là do thiết kế, không phải LLM tự tránh. Chỗ sửa loại F (đổi chi tiết, tên) vì vậy thường không để lại dấu vết trong graph: Cơ chế 3 có giá trị mới ở 16/26 chỗ F so với 20/26 của hai baseline (valid), 17/26 so với 22 (tune). Đây là nguồn mất điểm chính.
- Ở valid, trong 20 câu cấu hình f mà Window-replace đúng và Cơ chế 3 sai, 13 câu là loại F (đã đọc 4 câu mẫu: trả lời "UNKNOWN", chi tiết không có trong nút) và 3 câu E/historical.
- **Dấu "(ended <ngày>)" gây nhầm ở câu lịch sử** (valid-004, 025, 002): mô hình thấy nút đã đóng và trả "No" cho câu "Was X married to Y in 1973?" dù nút còn hiệu lực đến 1974, và có câu trả lời mâu thuẫn ("No ... so in 1973 it was still..."). Dấu đánh dấu giúp câu hỏi hiện tại nhưng gây nhiễu câu hỏi quá khứ.
- Với agent e′ (12 câu thua trên valid): 8 câu là loại F (5 verify_false, 3 direct; các câu mẫu đã đọc trả lời "cannot be determined" hoặc nêu sai tên), 3 câu E, 1 câu C; câu mẫu valid-002 hiểu sai mốc thời gian.

**Kết luận sau kiểm tra.** Chỉ lỗi 1 (câu từ chối) làm đổi kết luận: Cơ chế 3 có lọc không còn ngang hẳn Window-replace trên e′ (kém 2 câu ở tune, 5 ở valid); ở cấu hình cố định ngang ở d (128 so với 130 ở tune, 113 so với 115 ở valid), kém ở f (10 câu ở tune, 14 ở valid) và f′, f″ (6 đến 9 câu ở tune, ngang ở valid); luôn cao hơn hẳn bản cũ và bản không lọc. Hai baseline thắng nhẹ ở cấu hình f nhờ graph `real` có chi tiết trong văn bản nút, còn Cơ chế 3 chỉ bổ sung mốc (`add`), không sửa văn bản nút (`edit` đã bỏ từ prompt v3). Mức "luôn trả No" 0,44 đến 0,46 cần được ghi cùng mọi bảng mech3 khi so sánh.

## Tập test_clean, ba hệ (2026-11-24 đến 25)

**Thiết lập (đóng băng theo tune, không chỉnh theo valid hay test).** 98 chỗ sửa trên 98 trang test_clean (C 27, E 27, F 27, A 17; `m3_select_pilot.py --set test_clean --any-edit --per-type 27`; mặc định `--per-type 50` cho C 50, E 34, F 23, A 3 nên chọn 27 để cân bằng như valid), 387 câu timeline, 148 câu mech3. Các hệ, cấu hình và luật chấm như valid: Old, Window-replace (= `real`), Diff-replace, Cơ chế 3 có `--dedup` (kết quả chính là bản **có lọc**), d / f / f′ / f″ cố định, e′ (agent chỉ công cụ graph), agent C (tham chiếu). Script `local/m3/test_clean/run_test.sh` (37 bước, tất cả xong); log, `manifest.tsv`, `stats.log` ở `local/m3/test_clean/`. Thinking tắt (`opencode_deepseek_flash`), mỗi lần chạy một thư mục cache riêng `data/llm_cache/test_clean/<tên>`. Prompt Cơ chế 3 là v3 (không có `edit`, xem mục "Sửa prompt cơ chế 3 hai lần và bỏ `edit`").

**Chạy giữa chừng (ghi để khỏi đọc nhầm).**
- **Số luồng:** 5 luồng đến hết `fixed_tl_dr`, **15 luồng** từ `fixed_tl_m3` (người dùng đổi 2026-11-24 22:00 vì OpenCode chậm). Kết quả (nhiệt độ 0, cache) không đổi, nhưng **thời gian của hai nửa không so được với nhau và không so với tune, valid**.
- **OpenCode giờ cao điểm:** 429 đều đặn khoảng 6 lượt mỗi phút từ 18:55; có lúc mỗi lệnh gọi trung vị 84 giây (token ra chỉ 16 đến 55, không phải 429), `fixed_tl_old` mất 58 phút (valid khoảng 25 phút). Chưa xác nhận nguyên nhân (quá tải máy chủ hay hạn mức theo khóa). 429 không tốn token.
- **Tạm dừng hai lần** theo yêu cầu (giá giờ cao điểm). Ba bước bị cắt giữa chừng và chạy lại (`fixed_mech3_m3`, `agent_go_mech3_dr`, `fixed_tl_m3`): chạy lại trúng cache; thư mục dở `20261124_075739`, `114116`, `201725` được cộng vào chi phí, không xóa.
- **`llm_error` do API (lỗi gọi, hết số lần thử):** 58 dòng agent bị tính sai ở 7 bước (`agent_c_mech3_old` 16, `agent_go_tl_m3` 20, `agent_go_tl_wr` 8, `agent_go_tl_old` 6, `agent_go_tl_dr` 5, `agent_go_mech3_m3_nostate` 2, `agent_go_mech3_m3` 1). Script `run_test.sh` chỉ bắt `error`/`max` nên không phát hiện. Đã chạy lại 7 bước đó (`local/m3/test_clean/rerun_errors.sh`, cùng cache riêng, chỉ dòng lỗi gọi lại API, 110 lệnh gọi, 0,036 USD); `llm_error` về 0. **Số trong mục này dùng thư mục chạy lại** (`rerun_*` trong `manifest.tsv`). Đây là sửa lỗi hạ tầng, không phải đo nhiễu. Trước khi sửa, `agent_c_mech3_old` là 130/148 (nay 146).

**Trạng thái graph (98 chỗ sửa).** Node cũ còn mở: Old 78, Window-replace 2, Diff-replace 2, Cơ chế 3 2. Mất / thêm thừa: Window-replace 144/135, Diff-replace 18/2, Cơ chế 3 8/0 (76 nút đánh dấu). Cùng chiều với tune và valid.

**Mech3 (148 câu, số đúng):**

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---|---|---|---|---|---|
| Old | 53 | 52 | 41 | 36 | 57 | 146 |
| Window-replace | 130 | 128 | 95 | 86 | 119 | 144 |
| Diff-replace | 131 | 125 | 96 | 87 | 122 | 146 |
| Cơ chế 3, có lọc | 129 | 125 | 90 | 87 | 117 | 146 |
| Cơ chế 3, không lọc (tắt thử, bỏ qua khi so) | 81 | 79 | 66 | 62 | 89 | – |

Luôn trả "No" đúng 76/148 = 0,514 (cao hơn valid 0,442 và tune 0,456; chưa kiểm vì sao). Agent C của Old cao (146); agent C có công cụ vector và văn bản nên không chỉ dựa vào graph (chưa kiểm cụ thể từng câu).

**Chấm chặt (verify_false phải nêu giá trị đúng; số đúng chặt / số đúng theo luật thường), script `local/m3/final_mech3_strict.py` (cùng luật cho cả hai tập):**

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---|---|---|---|---|---|
| test_clean, Old | 53/53 | 51/52 | 40/41 | 33/36 | 55/57 | 144/146 |
| Window-replace | 129/130 | 127/128 | 91/95 | 82/86 | 118/119 | 141/144 |
| Diff-replace | 131/131 | 124/125 | 90/96 | 80/87 | 118/122 | 144/146 |
| Cơ chế 3, có lọc | 128/129 | 123/125 | 88/90 | 83/87 | 114/117 | 144/146 |
| valid, Old | 49/55 | 46/52 | 34/38 | 28/31 | 60/66 | 138/139 |
| Window-replace | 111/115 | 105/111 | 70/75 | 60/65 | 116/120 | 140/143 |
| Diff-replace | 110/112 | 103/106 | 71/77 | 66/72 | 111/116 | 142/144 |
| Cơ chế 3, có lọc | 108/113 | 91/97 | 69/75 | 62/68 | 111/115 | 141/144 |

Thứ hạng giữ nguyên khi chấm chặt.

**Timeline (387 câu, exact / F1):**

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---|---|---|---|---|---|
| Old | 0,636/0,796 | 0,674/0,828 | 0,612/0,813 | 0,581/0,759 | 0,775/0,905 | 0,863/0,935 |
| Window-replace | 0,667/0,800 | 0,713/0,838 | 0,659/0,817 | 0,615/0,765 | 0,798/0,911 | 0,884/0,944 |
| Diff-replace | 0,664/0,803 | 0,708/0,838 | 0,654/0,825 | 0,618/0,770 | 0,783/0,893 | 0,871/0,942 |
| Cơ chế 3, có lọc | 0,664/0,798 | 0,705/0,834 | 0,651/0,810 | 0,620/0,770 | 0,786/0,908 | 0,868/0,942 |
| Cơ chế 3, không lọc | 0,649/0,801 | 0,693/0,839 | 0,633/0,805 | 0,602/0,767 | – | – |

(e′ và agent C timeline chỉ chạy bản có lọc.)

**Đọc kết quả.** Cơ chế 3 có lọc **ngang đến kém nhẹ** Window-replace: mech3 kém 1 câu ở d, 3 ở f, 5 ở f′, hơn 1 ở f″, kém 2 ở e′ (117 so với 119); so với Diff-replace kém 2 ở d, ngang ở f, kém 6 ở f′, ngang ở f″, kém 5 ở e′. Timeline kém Window-replace 0,000 đến 0,016 exact (d 0,003, f 0,008, e′ 0,012, agent C 0,016). Luôn hơn hẳn bản cũ và bản không lọc. Cùng chiều tune và valid; không thắng.

**Chi phí test_clean** (lượt gọi thật, giá 0,15 / 0,003 / 0,60 USD mỗi triệu token; cache API là số API trả về; script `local/m3/cost_test.py`):
- **Cập nhật cũ lên mới (98 chỗ sửa):** tổng khoảng 0,224 USD. Trích bản cũ cùng cửa sổ (= Window-replace ước, không có LLM trong thí nghiệm) 0,102 (98 lượt, 255.859 vào, 106.292 ra); gộp cặp bản cũ 0,010; Diff-replace 0,065 (98 lượt, 257.524 vào, 43.387 ra); Cơ chế 3 0,047 (quyết định 0,045 với 98 lượt, 242.016 vào, 14.907 ra; gộp cặp 0,001 với 16 lượt). Cơ chế 3 rẻ nhất (ra ít nhất: 14.907 so với 43.387 và 106.292).
- **Bài test:** khoảng 3,72 USD (mech3 cố định 0,263, e′ mech3 0,357, timeline cố định 0,998, e′ timeline 0,897, agent C mech3 0,196, agent C timeline 1,009; tính cả ba thư mục dở) cộng 0,036 chạy lại `llm_error`, tổng khoảng 3,76 USD. Số lệnh gọi thật: mech3 cố định 2.935, e′ mech3 2.697, timeline cố định 7.641, e′ timeline 4.380, agent C mech3 1.433, agent C timeline 4.992.
- Thời gian: không đưa bảng thời gian giữa các hệ vì nửa đầu 5 luồng, nửa sau 15 luồng, và OpenCode chậm không đều.

### Đọc tay lỗi của Cơ chế 3 trên test_clean

- **Hành động LLM (98 chỗ sửa):** 63 `invalidate`, 15 `close`, 100 `add`, 0 `edit` (đã bỏ từ prompt v3). Loại A: 17/17 không đổi gì (không báo động giả). C: 27/27 có `invalidate` và `add`. F: 27/27 có `invalidate` (31) và `add`. E: 26/27 đạt luật hành động; chỗ hỏng test_clean-050.
- **E dùng `invalidate` thay vì `close` (3/27: test_clean-014, 026, 048).** Cùng kiểu lỗi tune-045. test_clean-048 (Roger Moore, "since 1971" thành "1971 to 1972"): nút "starred ... since 1971" bị `invalidate` (đúng ra `close`), kèm `add` nút mới; ở f, hai câu của chỗ sửa này (hiện nay và 1971) cùng trả "UNKNOWN" vì nút bị lọc.
- **test_clean-050 (Cutty_Sark, E):** câu mới "From February to October 1951 ... temporarily moved", LLM chỉ `add` mốc `start` 1951, không có mốc kết thúc (10/1951), nên không để lại dấu vết kết thúc.
- **`close` trên nút `point`: 0/15** (tune 1/10, valid 1/13), nên không có lỗi tune-049 ở test_clean.
- **Thua Window-replace ở f (4 câu, thắng 1):** E 2 (cả hai của test_clean-048), A 2: test_clean-125 trả "UNKNOWN", test_clean-120-m1 trả "1993-12-13" khi gold "13 December 1993" (luật chấm theo từ không nhận định dạng ngày khác; đáng ghi là lỗi chấm, không phải lỗi graph).
- **Thua Window-replace ở e′ (5 câu: C 4, A 1; thắng 3), đã đọc câu trả lời cả 5:** cả 5 câu Cơ chế 3 trả "không xác định được" (từ chối) trong khi Window-replace trả đúng. Ở test_clean-139 và 166 (C), graph làm đúng: `invalidate` nút giá trị cũ (1970, 1971) và `add` mốc mới (1974-01-15, 1974-12-06, `track` `other`). Câu trả lời lỗi vì agent: ở 139-q2 nó gọi `timeline` với track `naming` nên chỉ thấy 1 sự kiện năm 1987 (mốc mới ở track `other`), ở 139-q1 nó dừng sau `list_pages` và không gọi `timeline`. Track `other` không phải điểm riêng của Cơ chế 3 (nút `add` 13% `other` ở test_clean, 15% tune, 14% valid; nút của bản cũ 37%). Kết luận chỉ cho 139-q1, 139-q2: lỗi chọn track và dừng sớm của agent, không phải lỗi graph. Chưa kiểm vết gọi công cụ của 166-q2 (graph đúng), 093-q1 và 125-q2 (câu từ chối "no page ... available"), nên chưa kết luận cho ba câu này.
- **Khác tune và valid:** không còn mất điểm loại F (f chỉ thua 4 câu, không có F) vì chỗ F của test_clean đều được `invalidate` cộng `add`. Nhận định "F là nguồn mất điểm chính" của tune/valid chưa lặp lại ở test_clean; chưa tìm nguyên nhân (nghi do cách chọn chỗ F, chưa kiểm).
