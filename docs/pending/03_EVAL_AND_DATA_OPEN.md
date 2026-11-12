# Đánh giá và dữ liệu: việc chưa chốt


## CẬP NHẬT 2026-11-12 (sau): bước B mẫu 20 câu bằng OpenCode, lưu câu hỏi v9, việc còn lại (đọc trước)

**1. Đã làm**
- Lưu bộ câu hỏi v9 vào git: `dataset/eval/timeline_pilot/questions_v9/` (553 file `.jsonl` + `README.md`), trùng khớp `local/questions/v9/` lúc 2026-11-12 (1861 câu: tune 639, valid 557, test_clean 665). Không copy `checked.jsonl`, `_*.jsonl`, `.bak*`. Gold, `extras/`, `derived_classify/`, `tools/` vốn đã tracked. Mã (`local/check_questions.py`, `local/chain_*.py`) và prompt (`local/prompts/`) vẫn chỉ ở `local/`.
- Bước B trên mẫu 20 nhóm test_clean (10 trang, seed 7) bằng profile `opencode_deepseek_flash` (model `deepseek-v4.1-flash`, lần gọi đầu tiên của profile này): 26 lần gọi, 0 lỗi. Đã thêm hàm đặt header `x-opencode-session` vào `local/chain_complete.py` và `local/chain_verify.py` (thiếu thì OpenCode trả 400 `MissingSessionID`; `get_llm` không tự đặt, chỉ `scripts/run_agent_search.py` đặt).

**2. Kết quả mẫu**
- [1]: 18/20 nhóm không có ứng viên; Chicago_Stadium:2 có 4, Herbert_Schultze:0 có 2. [2]+[3]: cả 6 bị loại (4 `duplicate_of_gold`, 2 `duplicate_in_chain`). Đọc tay cả 6: đều là báo động giả (Chicago: 4 mốc 1977–1978 trước cửa sổ từ 1979; Schultze: cùng sự kiện, ngày công bố khác ngày hiệu lực). Không câu nào cần bỏ hay thêm id.
- Nhận xét: `in_window` của verifier sai ở 3 ứng viên Chicago (ghi true dù trước 1979), nhưng kết luận vẫn đúng nhờ lọc trùng gold. Mẫu nhỏ, chưa suy ra cho cả bộ.

**3. Thông số đo (nguồn `TAM_LLM_METRICS_FILE`)**
- [1]: 20 lần gọi, 107.152 token vào, 33.656 ra (trung bình khoảng 5.400 vào, 1.700 ra). [2]: 6 lần gọi, 8.631 vào, 3.558 ra. Tổng khoảng $0,04 ngoài giờ cao điểm theo giá OpenCode ($0,15 vào / $0,60 ra mỗi triệu token; gấp đôi 08–11h và 13–17h giờ Việt Nam).
- Một lần gọi chậm nhất 149 giây. Tổng thời gian chạy chưa đo. Output trung bình cao, nghi thinking đang bật (dòng `extra_body` của profile đang là chú thích; chưa kiểm chứng).

**4. Việc còn lại (số theo bộ v9 hiện tại; "nhóm" = 1 request [1])**

| Tập | Tổng | Chưa qua [1] |
|---|---|---|
| test_clean | 149 trang, 452 nhóm | đã chạy xong (4d) |
| valid | 128 trang, 346 nhóm | đã chạy xong (4c) |
| tune v1–v3 | 21 trang, 65 nhóm | 18 trang, 59 nhóm |
| tune cũ (v4–v9) | 144 trang, 408 nhóm | 54 trang, 148 nhóm |
| Cộng | 442 trang, 1271 nhóm | 349 trang, 985 nhóm |

- Request [1]: khoảng 985 (chỉ phần chưa có) hoặc khoảng 1.250 (chạy lại cả tune cũ). Request [2]: 1 mỗi ứng viên, ước 70–300 (chưa kiểm chứng; mẫu này 6/20 nhóm, lần v9_1 cũ khoảng 11/163). Chi phí ước khoảng $1,8 cho [1] ngoài giờ cao điểm cộng dưới $0,5 cho [2] (ước thô).
- "Đã qua" của tune cũ (90 trang) tính theo trang trong `local/chain_check/`; một số lần chạy dùng phiên bản câu hỏi cũ (v5–v8), nên chưa chắc khớp từng câu v9 hiện tại (chưa kiểm chứng).
- `chain_complete` chỉ kiểm `first_last_next`, `list`, `summary`; không kiểm `order_gap` (chuỗi chỉ 2 mốc).
- Các file `local/chain_decisions_v9_valid*_apply.json` là quyết định theo lỗi checker, không phải kết quả [1][2][3]; valid chưa có lần [1][2][3] nào.

**4b. Đã chạy [1][2][3] cho tune còn lại (2026-11-12, `opencode_deepseek_flash`, 20 luồng)**
- 213 nhóm / 75 trang (54 trang tune cũ chưa từng chạy + 21 trang v1–v3), 0 lỗi. [1]: 883.940 token vào, 167.278 ra (khoảng $0,23 ngoài giờ cao điểm). [2]: 14 ứng viên. Kết quả ở `local/chain_check/oc_tune_rest_4/` và `oc_tune_rest_4v/`; cache ở `data/llm_cache/chain/` (cache riêng, `SqliteCache(threadsafe=True)`).
- Đọc tay 10 nhóm có ứng viên: chỉ **Butch_Levy:0 thiếu mốc thật** (câu nguồn ghi cả Northwest AAU 1937 và 1938, gold e2/e3 chỉ ghi phần trung học) → ĐÃ BỎ (v9 còn 1860 câu, tune 638, checker 0 lỗi; bản sao `.bak_edit5`, ghi vào `_dropped.jsonl`). Real_Audiencia_of_Guatemala:0 (e10 tái lập Audiencia 1568, nguồn không nói trụ sở) GIỮ NGUYÊN theo quyết định của người dùng; các ứng viên còn lại là báo động giả.
- Sửa mã (chỉ trong `local/`): `chain_complete.py` và `chain_verify.py` tìm cả `pilot*` (trước đó chết ở trang v1–v3), dùng cache, `chain_complete.py` ghi dần `results.partial.jsonl` và có chế độ `DRY=1` kiểm đầu vào không gọi API; thêm header OpenCode.
- Test_clean: đã chạy xong ở mục 4d.

**4c. Đã chạy [1][2][3] cho valid (2026-11-12, `opencode_deepseek_flash`, 30 luồng)**
- 346 nhóm / 128 trang, 0 lỗi, cả 346 lần gọi nằm trong cache `data/llm_cache/chain/`. [1]: 1.956.836 token vào, 284.048 ra (khoảng $0,46 ngoài giờ cao điểm). [2]: 16 ứng viên. Kết quả: `local/chain_check/oc_valid_1/` ([1]) và `oc_valid_1v/` ([2][3]).
- Người dùng cho phép thêm thẳng mốc thật vào `extras/` hoặc id vào chuỗi câu hỏi. Đọc tay 11 nhóm có ứng viên, chỉ 2 câu cần sửa: **Sergio_P_rez:0** thêm e25 (2012-09-28, xác nhận thay thế Hamilton ở McLaren) vào `gold_event_ids` (nay 8 mốc; mốc đã có trong gold nhưng thiếu trong chuỗi); **Meg_Whitman:4** bỏ câu vì tin Sacramento Bee 2010 (không đi bầu 28 năm) thỏa tiêu chí nhưng không có trong gold, mốc ghi vào `extras/Meg_Whitman.json`. Bản sao `.bak_edit6`.
- Không sửa: Willy_Hernang_mez:3 (dòng "2019 World Cup :" trong nguồn không ghi huy chương nên verifier sai), Igor_Grabar:5 (e4 là `derived_date`), Igor_Grabar:4 (e35 "chỉ huy ủy ban" không phải bổ nhiệm), Francis_H_Case:3 (tiêu chí không gồm biểu quyết hay kết thúc nhiệm kỳ), David_Jolly:0 (năm suy từ câu trước), Lee_Nogan:2 (mùa giải), các ứng viên còn lại trùng chuỗi hoặc gold.
- v9 sau đợt này: 1859 câu (tune 638, valid 556, test_clean 665), checker 0 lỗi.
**4d. Đã chạy [1][2][3] cho test_clean (2026-11-12, `opencode_deepseek_flash`, 30 luồng)**
- 452 nhóm / 149 trang (chạy lại cả 20 nhóm mẫu vì mẫu chưa có cache), 0 lỗi, cả 452 lần gọi nằm trong cache `data/llm_cache/chain/`. [1]: 2.559.911 token vào, 408.520 ra (khoảng $0,63 ngoài giờ cao điểm). [2]: 30 ứng viên (chưa tổng kết chi phí). Kết quả: `local/chain_check/oc_test_1/` ([1]) và `oc_test_1v/` ([2][3]).
- 20 nhóm có ứng viên; đọc tay cả 30 ứng viên bằng `local/chain_review.py` và đọc nguồn: **không câu nào cần sửa, bỏ hay thêm vào `extras/`**. Lý do: ngoài cửa sổ của câu (Chicago_Stadium, Gary_Mills, All_Nippon_Airways là đổi tên chứ không phải lập công ty con), tiêu chí loại trừ (Embassy_of_Canada loại chức quyền, National_Library_of_Serbia loại mốc "listed as director", VP_25 loại việc tái nhập căn cứ cũ), mốc `derived_date` hoặc `source_inconsistent` bị cấm (Inter_Milan, Niigata, 6th_Combined_Arms_Army, Pinchas_Zukerman), mốc ước lượng cùng sự kiện với mốc đã có trong chuỗi (Calcio_Catania e15 với e16, UD_Las_Palmas), hoặc trùng chuỗi (Herbert_Schultze, SBB, VP_29).
- Bốn ứng viên mới chưa có trong gold đều bị loại: Lisa_Marie_Presley:3 và :7, Pierre_Gasly:3, Steve_Sidwell:0 có năm suy ra từ câu trước (cấm `derived_date`), Wheel_of_Fortune:1 là mở rộng nhiệm vụ chứ không phải bắt đầu làm announcer. Steve_Sidwell:0 lưu ý: bản ký hợp đồng một năm với Brighton sau khi Stoke cho ra đi (2016) không có ngày rõ nên không vào đáp án.
- Soát tay mẫu ngẫu nhiên 60 câu test_clean (seed 11, 15 câu mỗi loại): 0 lỗi nội dung (ước tỉ lệ lỗi dưới khoảng 5%, độ tin cậy 95%, chỉ là quy tắc "ba trên n"). Lọc 7 câu có ứng viên `derived_date` chưa vào gold: **bỏ Steve_Sidwell:0 và Pierre_Gasly:3** (đáp án list/summary chắc chắn thiếu một mục có ngày chỉ suy ra), giữ Lisa_Marie_Presley:3 (buổi vinh danh trùng ngày e31), Lisa_Marie_Presley:7, Ludwig_Martens:2, Inter_Milan:0, Pinchas_Zukerman:1 (không đổi đáp án). Bản sao `.bak_edit7`, ghi `_dropped.jsonl`.
- v9 sau soát: 1857 câu (tune 638, valid 556, test_clean 663), checker 0 lỗi.

- Quy định thêm mốc sau [1][2][3] (người dùng chốt 2026-11-12): mốc đã có trong gold, thỏa tiêu chí, không `derived_date`/`source_inconsistent` → thêm id vào `gold_event_ids`; mốc chưa có trong gold → ghi `extras/<Trang>.json` và bỏ câu; ngày suy ra hoặc theo mùa → không thêm. Không sửa gold `rev/`.
- Công cụ mới `local/chain_review.py <repo> <verdicts_dir> [auto|gold|all]` (không gọi API; chạy ngay sau [2], trước khi sửa file câu hỏi vì chỉ số `qi` lệch sau khi bỏ câu): liệt kê ứng viên `duplicate_of_gold` có mốc gold NGOÀI chuỗi và ứng viên `auto_accept` kèm câu hỏi, tiêu chí, chuỗi, trích dẫn. Lý do: verifier gộp "đã có trong gold" với "đã có trong chuỗi" (Sergio_P_rez:0 bị che) và `in_window` của nó không đáng tin.
- Quy định thêm mốc sau [1][2][3] (người dùng chốt 2026-11-12): mốc đã có trong gold, thỏa tiêu chí, không `derived_date`/`source_inconsistent` → thêm id vào `gold_event_ids`; mốc chưa có trong gold → ghi `extras/<Trang>.json` và bỏ câu; ngày suy ra hoặc theo mùa → không thêm. Không sửa gold `rev/`.
- Công cụ mới `local/chain_review.py <repo> <verdicts_dir> [auto|gold|all]` (không gọi API): liệt kê ứng viên `duplicate_of_gold` có mốc gold NGOÀI chuỗi và ứng viên `auto_accept` kèm câu hỏi, tiêu chí, chuỗi, trích dẫn. Lý do: verifier gộp "đã có trong gold" với "đã có trong chuỗi" (Sergio_P_rez:0 bị che) và `in_window` của nó không đáng tin.

**4e. Tổng kết đã làm trong ngày 2026-11-12 (phần sau) và nhận xét**

*Đã làm:*
1. Lưu bộ câu hỏi v9 (1859 câu) vào git ở `dataset/eval/timeline_pilot/questions_v9/`; gold và `extras/` vốn đã tracked.
2. Chạy [1][2][3] bằng `opencode_deepseek_flash` (lần đầu dùng profile này, chạy được sau khi thêm header `x-opencode-session`) cho cả ba tập: mẫu 20 nhóm test_clean, tune 213 nhóm, valid 346 nhóm, test_clean 452 nhóm. Tổng khoảng 1.000 lần gọi [1] và 60 lần gọi [2], không lỗi gọi; tổng chi phí [1] khoảng $1,3 ngoài giờ cao điểm (0,23 + 0,46 + 0,63, cộng mẫu).
3. Áp kết quả: bỏ Butch_Levy:0 và Meg_Whitman:4, thêm e25 vào Sergio_P_rez:0, ghi `extras/Meg_Whitman.json`; Real_Audiencia_of_Guatemala:0 giữ nguyên. Soát tay mẫu 60 câu test_clean (0 lỗi) và bỏ thêm Steve_Sidwell:0, Pierre_Gasly:3 (mục 4d). v9 còn 1857 câu.
4. Sửa `local/chain_complete.py` và `local/chain_verify.py`: tìm cả `pilot*`, dùng cache riêng `data/llm_cache/chain/` (`SqliteCache(threadsafe=True)`), ghi dần `results.partial.jsonl`, chế độ `DRY=1`, header OpenCode. Thêm `local/chain_review.py`.

*Nhận xét:*
- Chất lượng câu hỏi tốt: trên 1.011 nhóm chỉ 4 câu cần thay đổi từ [1][2][3] (Butch_Levy:0, Meg_Whitman:4 bỏ; Sergio_P_rez:0 sửa; test_clean 0), cộng 2 câu test_clean bỏ ở bước soát mẫu vì ngày suy ra (Steve_Sidwell:0, Pierre_Gasly:3), tức khoảng 0,6%. Điều này cho thấy lọc ở bước sinh và soát tay trước đó đã hiệu quả; bước [1][2][3] chủ yếu xác nhận chứ ít sửa.
- Ứng viên thật hiếm và phần lớn do tiêu chí hoặc luật ngày: ngoài cửa sổ, tiêu chí loại trừ, `derived_date`, ngày theo mùa. Gần như mọi báo động giả của [1] đều bị [2][3] hoặc `chain_review.py` lọc đúng.
- Điểm yếu của verifier: gộp "đã có trong gold" với "đã có trong chuỗi" (nhãn `duplicate_of_gold`, che mất Sergio_P_rez:0), `in_window` sai, `auto_accept` sai (Willy_Hernang_mez:3). Phải đọc tay ứng viên.
- Rủi ro còn lại: câu có sự kiện thật nhưng ngày chỉ suy ra (vd Steve_Sidwell:0, Lisa_Marie_Presley:7) được giữ vì luật cấm `derived_date`; đáp án của chúng có thể thiếu một mốc không đo được. "Đã qua [1]" của 90 trang tune cũ là theo trang, một phần dùng phiên bản câu cũ (chưa kiểm chứng từng câu).
- Chi phí OpenCode thấp (khoảng $0,4 mỗi 100 nhóm) và không gặp giới hạn tốc độ ở 30 luồng; hạn mức riêng của `deepseek-v4.1-flash` chưa kiểm chứng (trang `opencode.ai/docs/go` không liệt kê).
- Các lỗi tôi gây ra và đã sửa: không kiểm file tồn tại trước khi chạy (script chết do `pilot*`), để `cache=None` (mất 123 lần gọi, khoảng vài cent), cache SQLite không chia sẻ giữa luồng (cả lượt lỗi trước khi gọi API). Bài học: chạy `DRY=1` và kiểm cache bằng nhiều luồng trước khi chạy thật.

**4f. Soát tay mẫu tune, valid, câu cờ, 5 câu nghi, ước token (2026-11-12, không gọi API)**
- Mẫu tune (seed 5) và valid (seed 7), mỗi tập 8 câu mỗi loại = 32 câu: 0 lỗi nội dung (kiểm số năm `order_gap`, đáp án `first_last_next`, cửa sổ, tiêu chí so với mốc; mở thêm nguồn cho Rainier_Brewing_Company:0 và Chemnitz:5, đều đúng). Mẫu nhỏ: chỉ nói là không thấy lỗi trong mẫu.
- Câu có `flagged_ids` không rỗng: tune 8/638, valid 12/556, test_clean 21/663; toàn `list` hoặc `summary`, chỉ cờ `approximate_date` (13, 17, 37 mốc). Báo điểm riêng nhóm này.
- 5 câu nghi v4–v5: chỉ số cũ đã lệch (Vindobona không còn trang trong v9; The_One_Show và Meet_the_Press chỉ còn đến :2 và :3). Đọc lại cả các trang: The_One_Show, Meet_the_Press, Jerzy_Buzek ổn (Jerzy_Buzek:0 e27 có trích "After losing the parliamentary elections in 2001", chưa kiểm chứng việc cá nhân ông ứng cử). **Sửa Alemannia_Aachen:0:** thêm e10 (1938, "finished atop their division", nằm trong cửa sổ trước thập niên 1990) vào `gold_event_ids` (e2, e10, e17, e19), thêm lời giải thích vào `criterion`, "Three" thành "Four" ở `why_needs_multiple`; bản sao `.bak_edit8`; `check_questions.py v9`: 0 LỖI; đã copy sang `questions_v9/`. Đây là cách đọc "đứng đầu hạng = vô địch hạng", có thể đảo lại nếu bạn không đồng ý.
- Ước token vào nếu đưa **cả trang** cho mỗi câu (ký tự/4, chưa kiểm chứng tokenizer): tune 2,15M, valid 1,97M, test_clean 2,40M. Với giá OpenCode ngoài giờ cao điểm ($0,15 mỗi triệu token vào) khoảng $0,3 đến $0,4 mỗi tập cho một phương án (chưa tính token ra). Vector top-k nhỏ hơn cả trang. Phương án graph chỉ là oracle từ gold: trong `src/tam` chưa thấy mã graph store (chưa kiểm chứng đầy đủ). Chưa chạy gì.

**4g. Kiểm tra chuẩn bị "chạy hệ thống" (2026-11-12, không gọi LLM, chỉ đọc Qdrant cục bộ)**
- Qdrant chạy ở `localhost:6333`, có collection `tam_chunks_dev_tune` (5.898 chunk), `_valid` (4.884), `_test_clean` (5.572). Embedding (fastembed bge-small, bm25) và reranker nằm ở `data/model/`, chạy cục bộ, không cần API. Payload có `start_time`, `end_time`, `time_inferred`, `invalidated_at`; `start_time` rỗng ở 1.033/5.898 (tune), 746/4.884 (valid), 828/5.572 (test_clean). Nghĩa là ingest đã làm xong, không cần ingest lại.
- Văn bản kho khớp `in/<Trang>.txt` của gold: 5.847 / 4.884 / 5.572 chunk khớp thân văn bản, 0 chunk khác (chỉ khác tiền tố tên trang). Tên file trong `in/` đã đổi ký tự (dấu, ngoặc), nên đối chiếu phải theo `chunk_id`, không theo tên file.
- Thiếu chunk trong kho: 82 / 83 / 76 trang thiếu khoảng một chunk (valid còn thiếu cả trang Young_Girl_with_a_Flower_Basket). Ảnh hưởng đến câu hỏi (mốc trong chuỗi hoặc gold có chunk bằng chứng vắng trong kho): tune 1/638 (Fulk_King_of_Jerusalem), valid 11/556 (Master_General_of_the_Ordnance_Sweden 10, Chelyabinsk 1), test_clean 6/663 (Nora_Ephron 1, Air_Staff_Sweden 4, United_States_Air_Forces_in_Europe_Air_Forces_Africa 1). Nên đo riêng hoặc loại 18 câu này khi chấm truy xuất.
- **Chưa có bộ chạy và bộ chấm cho v9.** `generate_answers.py`, `answerer.py`, `answer_v1..v4.md` và `metrics_timeline.score_answer` viết cho câu TimeQA (đáp án đơn) hoặc câu `answer_type`/`gold_answer` của bộ cũ; câu v9 chỉ có `gold_event_ids`, `answer_ids`, `group_event_ids`, không có `gold_answer`. `src/tam` chưa có mã graph store. Cần viết: dựng đáp án chuẩn từ gold theo loại câu, prompt (đầu ra có ngày hoặc id để chấm không cần LLM chấm), phương án lấy ngữ cảnh (vector top-k từ Qdrant, cả trang, chuỗi oracle) và bộ chấm. `scripts/run_agent_search.py` và `score_agent_runs.py` là phần agent search của người dùng, cũng cho câu TimeQA.

**5. Chờ người dùng**
- Chạy hệ thống (vector top-k, cả trang, graph oracle theo `docs/eval/08`) theo thứ tự tune, valid, test_clean; hỏi trước khi gọi API (người dùng 2026-11-12: "ko gọi api" ở lượt này). Chấm riêng câu có `flagged_ids` không rỗng.
- Lọc mốc `date` âm khi đo ingest và kiểm chunk TCN trong kho (chỉ đọc); cách chấm `list` so với `summary`.
- Sau mỗi lần bỏ/sửa câu: copy lại `local/questions/v9/` sang `questions_v9/`.
- Commit (người dùng tự làm): `dataset/eval/timeline_pilot/questions_v9`, `extras/Meg_Whitman.json` và file ghi chú này.

## CẬP NHẬT 2026-11-12: sinh và soát câu hỏi v9 (đọc trước; thay mục "việc kế tiếp" của phần 2026-11-11)

**1. Đã làm**
- **Tune v1–v3 (25 trang, gold viết lại bằng v7):** Session 16 (5 agent Haiku × 5 trang) sinh 96 câu. Checker 0 lỗi. Soát tay rồi bỏ 7 câu (WUPJ Q4 nhãn lẫn; Mike_Bongiorno Q1 text Telegatto trùng; Telekids Q1 đáp án 1 năm; 4 câu `next` có nhóm 2 mốc: Sharp:3, Whitley:6, Regius:5, Toungoo:2), sửa WUPJ Q2 (thêm "Among the dated events…"), sửa tên Nordenskiöld, Nøstmo, Trøndelag, Österdahl (giữ Odqvist vì gold ghi vậy). Còn 89 câu, Klemzig và Telekids rỗng.
- **Test_clean (186 trang, `batchT/rev`):** viết 8 prompt `local/prompts/sinh_cau_hoi_v9_clean_S1..S8.md` (40 agent, mỗi agent 4–5 trang; mục N: không dùng `date` âm, nhãn `other` chỉ gom khi ≥3 mốc cùng nhãn, tên riêng đúng dấu, `why_needs_multiple` có dấu). Người dùng chạy đủ 8 session. 186/186 trang có file câu hỏi, 13 trang rỗng.
- **Sửa hàng loạt sau checker (bản sao `*.jsonl.bak_edit3`):** bỏ 65 câu (10 `first_and_last` nhóm 2 mốc, 2 câu Gary_Mills dùng mốc trùng text làm neo, 53 câu `next/last/first` nhóm 2 mốc); Mbaye_Jacques_Diop:3 đổi "between 1975 and 1982" thành "between the mid-1970s and the early 1980s"; thêm "in any order" cho 41 câu `list`/`summary` có mốc cùng ngày; 6 câu `order_gap` đổi "How many years" thành "How many calendar years".
- **Soát tay (bản sao `*.jsonl.bak_edit4`):** đọc hết 112 câu có mốc cờ nằm trong khoảng chuỗi + 94 cảnh báo sát biên, 74 cặp "chữ trùng cao" nằm cùng một câu, 8 chuỗi hòa đầu/cuối, và các câu phụ thuộc phán đoán. Bỏ thêm 5 câu: U_66:2 (thiếu e16 `derived_date` sau Drumbeat), Inter_Milan:6 (thiếu danh hiệu 1930, 1938: chunk chỉ ghi mốc 1940 là "fifth title"), Myles_Deering:5 (e21 và e22 mâu thuẫn ngày thăng chuẩn tướng), Moeslim_Taher:4 (2 mốc, còn một chức không ngày), Phil_Twyford:1 (mốc 2020 chỉ suy luận).
- **Kiểm các vấn đề gold agent báo:** Guggenberger "thiếu label" là SAI (21 mốc `other` đều có label; toàn batchT 0 mốc `other` thiếu label; ít câu do cờ `derived_date`). Iron Cross e6/e11 là mâu thuẫn thật của chunk, đã bị loại. Berga e8, Many_a_Slip e4: vô hại. National_Library e16/e17 ("listed as director") nên gắn `source_inconsistent`, nhưng không câu nào dùng nên bỏ qua (người dùng quyết không ghi và không sửa).

**2. Kết quả**
- **v9 sau cùng:** 1861 câu, 0 LỖI, 1120 cảnh báo. Test_clean 665 câu / 186 trang, 13 trang rỗng. Loại câu test_clean: `list` ~219, `order_gap` ~214, `first_last_next` ~166, `summary` ~71 (số trước đợt bỏ 5 câu cuối).
- Không câu test_clean nào dùng mốc `date` âm hoặc mốc `derived_date`/`source_inconsistent` làm đáp án.

**3. Nhận xét**
- Câu hỏi ít (3,6 câu/trang) và lệch về `order_gap`/`first_last_next` vì: `track work` bị loại, mốc `derived_date` chặn chuỗi, `undated_mentions` chặn chuỗi, v7 chỉ giữ một mốc cho hoạt động. Đây là cái giá đã chấp nhận (không nới `derived_date`).
- Báo cáo của agent Haiku KHÔNG đáng tin để đếm (agent 9 báo 17 câu, thực 19; agent 20 phân loại sai) và hay tự khẳng định "lỗi gold" mà không kiểm. Chỉ tin số của checker, đánh dấu "chưa kiểm chứng" mọi khẳng định về gold cho đến khi mở file.
- Phần lớn cảnh báo "mốc cờ gần chuỗi chưa khai" là mốc khác loại (kết thúc so với bắt đầu, người khác, giải khác) nên đáp án không đổi; chỉ 3 câu thật sự sai chuỗi đã bỏ.
- Cảnh báo "chữ trùng cao" ở mức cặp (210) phần lớn là sự kiện thật khác nhau cùng mẫu câu (huy chương, nhiệm kỳ, danh hiệu); không có trường hợp đếm đôi trong cùng một câu.

**4. Chưa làm**
- **Bước B (cần DeepSeek, hỏi trước khi gọi):** `chain_complete`, `chain_verify` trên mẫu khoảng 20 câu test_clean với `TAM_LLM_METRICS_FILE`, báo chi phí, rồi mới quyết chạy toàn bộ.
- Soát tay chưa phủ hết 665 câu: chỉ đọc nhóm bị cảnh báo hoặc do agent đánh dấu nghi.
- Câu hỏi tune v4–v6 (các trang cũ): chưa soát lại theo cách này. 815 cảnh báo "mốc cờ gần chuỗi" của cả v9 chưa xem hết ngoài test_clean.
- 5 câu v4–v5 nghi ngờ (The_One_Show:3, Meet_the_Press:4, Alemannia_Aachen:1, Vindobona:2, Jerzy_Buzek:1) vẫn chờ quyết định.
- Lọc mốc `date` âm khi đo ingest với gold, kiểm chunk TCN có vào store với `start_time` dương không (chỉ đọc).
- Chấm điểm `list` so với `summary`, ranh giới với Mechanism 3.

**5. Dự định (theo thứ tự)**
1. Hỏi người dùng rồi chạy bước B trên mẫu 20 câu, báo chi phí.
2. Chạy hệ thống trên test_clean với câu hỏi v9 (cần quyết định chi phí API trước).
3. Chấm riêng các câu có `flagged_ids` không rỗng khi báo điểm.
4. Soát tune v4–v6 và 5 câu nghi ngờ khi còn thời gian.

**6. Trạng thái commit**
- Mọi thay đổi gần đây nằm trong `local/` (gitignored), trừ ghi chú này. Chỉ `docs/pending/03_EVAL_AND_DATA_OPEN.md` thay đổi để commit.

## CẬP NHẬT chiều–tối 2026-11-11 (đọc trước; thay các mục "việc kế tiếp" của phần tổng hợp phía dưới)

**1. Đã làm (kể từ phần tổng hợp phía dưới)**
- Kiểm gold tune v1–v3 mới (25 trang, guide v7) và test_clean (186 trang). Hình thức: `check.py` 0 lỗi cả hai. Nội dung: so mốc cũ với mới, chạy tool gap (`local/gold_gap_sub.py`), tự đọc câu chưa phủ.
- Phát hiện: gold tune v1–v3 mới nhiều mốc "biến mất" (87 mốc cũ), phần lớn do v1–v3 ghi mốc mà v7 cấm (mốc thực thể khác, chuyến tàu/máy bay, thống kê, bài viết/phát biểu của nhân vật, giải truy tặng, mốc mùa giải, ngày kết thúc hoạt động tham gia). Guide: pilot5 = v1 (không có mục KHÔNG ghi, không cờ), pilot10 = v2 và batch2 = v3 (hai bản giống hệt nhau), gold mới = v7.
- Vá tune v1–v3: 24 mốc / 9 trang (Ernst_Hechler +8, Great_Tower_Neuwerk +3, Mike_Bongiorno +3, Regius_Professor_Civil_Law +4, Carl_Ehrensvard +2, Telekids/First_Air_Group/Aero_Union/Toungoo_dynasty +1). Không vá 16 trang còn lại vì đúng theo v7 (WUPJ, Klemzig, Real_Audiencia...). Tool: `local/gold_patch_v1v3.py` (spec `local/gold_patch_v1v3/<Trang>.json`; bản chưa vá ở `regen_v1v3/sub/`, bản vá ở `pilot5|pilot10|batch2/rev/`).
- Test_clean: copy `batchT/sub/` sang `batchT/rev/` cho 136 trang (rev đủ 186); vá 13 mốc / 12 trang (Boris_Nemtsov, Laurette_Onkelinx, VP_29 +2, VP_42, Cutty_Sark, Princess_Victoria_Melita, The_Cycle, UD_Las_Palmas, Jim_Prentice, Guy_Aldred, Cho_Yoon_sun, Nick_Saban). U_101 bỏ e28 (trùng e27). Inter_Milan e50/e51 đổi cờ sang `approximate_date`. Kết luận: phần lớn câu "chưa phủ" của tool gap là mốc v7 cấm hoặc đã có mốc (quote khác), không phải sót.
- Đọc nốt các lớp derived_date chưa ai đọc (`a_far` 15, `a_weakrel` 23, type a chặt 49 đọc lần hai, `b_anchor_prev_chunk` 16 mẫu, `c_exact_*` 49, `c_year_in_quote` 22 mẫu): không thấy phân loại sai; `c_exact_*` và một phần `c_year_in_quote` có cờ thừa (quote đã chứa ngày), không sửa theo quyết định giữ cờ cũ.
- Mục "agent tune có mở gold cũ không": chưa thấy dấu hiệu (văn bản trùng chủ yếu là câu chép sát chunk; không có chú thích riêng của gold cũ xuất hiện lại); không chứng minh phủ định được vì không có log phiên Haiku.
- Viết prompt sinh câu v9 cho 25 trang tune v1–v3: `local/prompts/sinh_cau_hoi_v9_tune_v1v3.md` (1 session, 5 agent × 5 trang). Sửa `local/questions/check_questions.py` (`load_page`) để tìm gold ở cả `batch*` và `pilot*` (trước đó trang `pilot5`/`pilot10` không load được nên chưa từng có câu v9).

**2. Đã kiểm gì, ra gì (tóm tắt)**
- `check.py` (mã): tune 25 trang 0 lỗi; test_clean 186 trang 0 lỗi (kể cả sau mọi lần vá).
- Số liệu: test_clean 186 trang, 6247 mốc sau vá (trước 6236); 52 text trùng trong trang (`dup_text`, tự lọc khi sinh câu); 1 mốc TCN ở 1 trang (phải lọc); derived_date 714, approximate_date 296, source_inconsistent 71.
- Tune v1–v3 mới: 696 mốc trước vá, 720 sau vá.
- Tool gap trên test_clean: 1485 câu có năm chưa phủ; 161 có ngày đầy đủ (53 trang) sau đọc chỉ thêm được 13 mốc.

**3. Chưa làm / còn dở**
- Chờ người dùng chạy session sinh câu v9 cho 25 trang tune (prompt ở trên), rồi tôi chạy `python3 -I local/questions/check_questions.py v9` (ghi đè `checked.jsonl`) và đọc báo cáo agent.
- Viết prompt sinh câu test_clean (v9, không dùng mốc `date` âm, bỏ câu "1/3" của prompt cũ) và chạy bước B ([1] chain_complete, [2] chain_verify, [3] mã) trên test_clean: đo mẫu ~20 câu bằng `TAM_LLM_METRICS_FILE`, báo chi phí, hỏi người dùng trước khi gọi API.
- Chưa quyết (đợi người dùng): sửa hay bỏ 5 câu nghi v4–v5 (The_One_Show:3, Meet_the_Press:4, Alemannia_Aachen:1, Vindobona:2, Jerzy_Buzek:1); lọc mốc TCN khi đo ingest và kiểm chunk TCN có lọt vào kho với `start_time` dương không (chỉ đọc); sửa guide (ngày sinh con, tai nạn máy bay của hãng); cách chấm `list`/`summary` và ranh giới Mechanism 3.
- Chưa đọc/chưa kiểm chứng: câu chỉ có năm của các trang top test_clean chỉ lọc theo mốc đã có, chưa đọc từng câu của mọi trang; gold tune v6 (128 trang) chưa soát; tune v4–v5 (45 trang) gap chưa đọc; baseline 640 warning và 6 quote không tìm thấy của checker; mốc vá của tôi (ví dụ Aero_Union 1987, Toungoo 1740, Telekids 1994-12-31) là phán đoán, người dùng có thể bỏ.
- Chưa commit (người dùng commit): `batchT/rev/` (4 trang mới sửa), `docs/pending/03_EVAL_AND_DATA_OPEN.md`; `local/` bị gitignore.


## Tổng hợp trạng thái cuối ngày 2026-11-11 (đọc phần này trước; chi tiết ở các dòng bên dưới và `docs/eval/10` mục 10.5bb–10.5bk)

**A. Đã làm hôm nay**
- Gold test_clean: đủ 186 trang ở `dataset/eval/timeline_pilot/batchT/sub/` (6236 mốc, `check.py` 0 lỗi). Chỉ session 1–10 (50 trang, 1764 mốc) đã soát và nằm ở `batchT/rev/`.
- Sửa `tools/check.py` (số có dấu phẩy); luật TCN trong `check_questions.py`; bỏ Han_dynasty:2; v9 checker 0 lỗi.
- Phân loại `derived_date` a/b (`docs/process/10_DERIVED_DATE_CLASSIFICATION.md`, mã `local/derived_classify.py`, kết quả `dataset/eval/timeline_pilot/derived_classify/`).
- Mã gợi ý mốc sót `local/gold_gap_sub.py`; đã đọc gap 15 trang đầu bảng của test_clean.
- Đọc gold + 164 câu v4–v5 của tune (10.5bi): đáp án đúng, 5 câu nghi.
- Gen lại gold tune v1–v3 (25 trang) bằng guide v7 rồi **đã thay** (`decisions/14` mục 19; bản cũ ở `old_gold_v1v3/`; thư mục `regen_v1v3`; 23 câu v9 của batch2 gỡ sang `local/questions/v9/_replaced_gold_v3/`).
- Quyết định đã chốt (người dùng): không nới `derived_date`; giữ `extras/` (để tính precision khi ingest); không nới `dup_text` (4 câu cứ bỏ); thay gold tune v1–v3 (`decisions/14` mục 18, 19).

**B. Đang dở**
- Soát gold test_clean: 136 trang (session 11–38) còn ở `sub/`, chưa copy sang `rev/`; mới đọc gap 15 trang đầu bảng (118 trang chưa đọc; 5 trang cuối mới đọc 22 gap đầu).
- Gold tune v1–v3 mới chưa soát nội dung: 65 mốc cũ biến mất (có vẻ sót thật: Great_Tower_Neuwerk 1360/1909/1971, Quelli_che_il_Calcio 1993, Toungoo_dynasty 1740, Regius_Professor 2006-02, Mike_Bongiorno quốc tang 2009, Lev_Polugaevsky 1995); nghi agent mở gold cũ ở Carl_Ehrensvard, August_Maus.
- 25 trang tune v1–v3 chưa có câu v9 (pilot5, pilot10 chưa từng có; 23 câu batch2 đã gỡ). Tune v9 còn khoảng 549 câu.
- Sửa nhỏ gold test_clean đã biết nhưng chưa làm: Friedrich_Guggenberger e11 (cờ nên là `source_inconsistent`), U_101 e27/e28 (trùng), cờ mùa giải Inter_Milan e50/e51.

**C. Chờ quyết (người dùng)**
1. Mức soát 136 trang test_clean: đề xuất không chạy lại Haiku, copy `sub/` sang `rev/` kèm sửa nhỏ, rồi dựa vào bước [1][2][3] sau khi sinh câu hỏi.
2. Có sinh câu v9 mới cho 25 trang tune v1–v3 không.
3. 5 câu nghi v4–v5: sửa lời hoặc bỏ (The_One_Show:3, Meet_the_Press:4, Alemannia_Aachen:1, Vindobona:2, Jerzy_Buzek:1).
4. Loại mốc `date` âm khỏi so sánh ingest-gold; kiểm chunk TCN có lọt vào kho với `start_time` dương không (chỉ đọc).
5. Sửa guide trước khi dùng tiếp (ngày sinh con, tai nạn máy bay của hãng; `CLOUD_STATE.md`).
6. Chấm `list`/`summary` (gộp hay giữ); ranh giới với Cơ chế 3.

**D. Việc kế tiếp (theo thứ tự đề xuất)**
1. Chọn mức soát (C.1), copy `sub/` sang `rev/` cho 136 trang test_clean.
2. Viết prompt sinh câu hỏi test_clean (v9 + dặn không dùng mốc `date` âm, bỏ câu "1/3" của prompt cũ); chạy sinh câu; đếm số câu mỗi trang (trang U-boat có thể ít).
3. Bước B ([1] `chain_complete`, [2] `chain_verify` DeepSeek, [3] mã) cho câu chưa qua + test_clean: đo mẫu 20 câu với `TAM_LLM_METRICS_FILE` và **hỏi người dùng trước khi gọi API**.
4. Soát gold tune v1–v3 mới (65 mốc biến mất) rồi sinh câu cho 25 trang.

**E. Chưa đọc / chưa kiểm chứng (liệt kê để khỏi quên)**
- Gap test_clean: 118 trang chưa đọc; ứng viên mốc sót mới là gợi ý, chưa đối chiếu với mốc quanh.
- Gap tune v4–v5: 45 trang chưa đọc; chưa đối chiếu từng chunk.
- Phân loại derived: chưa đọc `a_far`, `a_weakrel`, `c_*` (235 mốc), `b_anchor_prev_chunk` (50); người đọc thứ hai cho loại a.
- Agent có mở thư mục cấm không (không đọc transcript) ở cả test_clean và regen.
- 640 cảnh báo và 6 quote không thấy trong chunk của `check_questions.py v9` (chưa đối chiếu với trước đó).
- Gold tune v6 (128 trang) chưa soát lại; v1–v3 cũ đã thay.
- Chưa commit: xem lệnh git ở cuối phiên (check.py, `batchT/sub`, docs, `derived_classify`, `regen_v1v3`, `old_gold_v1v3`, `pilot*/rev`, `batch2/rev`).

- **Chấm `list` so với `summary`:** cả hai có đáp án là tập sự kiện gold theo thứ tự thời gian, chỉ khác khung câu hỏi. Cách chấm của hệ thống chưa quyết (`list`: khớp tập, kèm thứ tự?; `summary`: độ bao phủ sự kiện, ai chấm, ngưỡng?). Người dùng (2026-11-09): sẽ xem xét thêm, có thể gộp hai loại sau nếu cần, vì lõi vẫn là danh sách các sự kiện trong chunk.
- **Tỷ lệ theo loại câu** chưa đặt trong docs. Hiện v8+v8n 448 câu: `list` 31%, `first_last_next` 29%, `order_gap` 23%, `summary` 16%. Mục tiêu tham khảo: tune 300, valid 300, test 400 câu, khoảng 8–9 câu mỗi thực thể (hiện khoảng 4,5 mỗi trang).
- **Dữ liệu:** `valid` (167 trang) có gold, cả 167 trang đã sinh câu v9 (582 câu sau khi bỏ câu yếu; trước đó 591 câu: 12 trang ở Session 5–8, 100 trang ở Session 9–12, 55 trang ở Session 13–15; xem `docs/eval/10` mục 10.5ay, 10.5az); `test_clean` (186 trang) chưa có gold; 23 trang gold có tên file mất ký tự có dấu nên không gán tự động vào tune/valid bằng tên.
- **v9 Session 5–8 (2026-11-10, `docs/eval/10` mục 10.5ax), còn chờ quyết:** (a) ~~luật order_gap 1/3~~ đã bỏ hẳn (người dùng, `decisions/14` mục 15.3; prompt chưa sửa dòng đó), đã thêm tay 10 câu `order_gap`; (b) 22 trang 0 câu (mục 10.5ax.2): để trống hoặc làm ở đợt `work` riêng; (c) valid còn 155 trang chưa làm (ước 450 câu, chưa kiểm chứng; mục tiêu tham khảo 300): chọn bao nhiêu trang; (d) 2 cửa sổ chữ tự do còn ở 100 trang trước (Archaeologia_Cambrensis:1, Stefan_He_e:4); (e) chạy [1][2][3] cho 271 câu mới. Đã chốt: bỏ 20 câu, chuẩn hóa cửa sổ, sửa Security:1, thêm luật checker nhóm <3 mốc, không đặt trần câu mỗi trang (xem `decisions/14` mục 15).
- **52 câu `first_last_next` nhóm <3 mốc: ĐÃ BỎ (người dùng chốt 2026-11-11)**; xem `docs/decisions/14` mục 16 và `docs/eval/10` mục 10.5ba. Sao lưu để khôi phục nếu cần: (a) `local/questions/v9/_dropped_weak52.jsonl` (52 câu đầy đủ, mỗi dòng `{page, q, question}`), (b) `local/questions/v9/_dropped.jsonl` (tất cả câu từng bỏ ở v9), (c) `local/questions/v9/<Trang>.jsonl.bak_apply` (file trang trước lần áp đầu), (d) quyết định `local/chain_decisions_v9_weak52_apply.json`, nhật ký `local/chain_apply_log.jsonl`. Thư mục `local/` bị gitignore, nên các bản sao này không nằm trong git. Sau khi bỏ v9 còn 1130 câu (tune 572, valid 558), `first_last_next` 287.
- **Bước B soát gold (chờ, tốn API DeepSeek; ghi 2026-11-11):** chạy [1] `chain_complete.py`, [2] `chain_verify.py`, [3] mã kiểm cho khoảng 800 câu v9 chưa qua ba bước này (281 câu Session 5–8 và 550 câu valid trừ các câu đã bỏ; chưa đếm chính xác). Trước khi chạy cả loạt: chạy mẫu khoảng 20 câu với `TAM_LLM_METRICS_FILE` để đo token và chi phí (chưa ước), rồi hỏi người dùng. Câu nào [2][3] xác nhận thiếu mốc trong chuỗi thì bỏ câu hoặc thêm id bằng `chain_apply.py` (chỉ khi mốc đã có trong gold); không thêm mốc vào gold, không dựng `extras/`. Có thể thử `opencode_deepseek_flash` cho rẻ hơn (chưa kiểm chứng).
- **v9 Session 9–12 (valid, 2026-11-11, `docs/eval/10` mục 10.5ay), còn chờ quyết/áp:** 363 câu trên 100 trang; đã bỏ 8 câu (7 lỗi checker + Southwind:1), chuẩn hóa 8 cửa sổ, sửa Han_dynasty:3, tắt cảnh báo order_gap >1/3 (checker 0 lỗi, v9 994 câu); còn chờ: ~~nới luật `dup_text` để giữ lại 4 câu đã bỏ~~ (ĐÃ CHỐT KHÔNG NỚI, 2026-11-11, `decisions/14` mục 18.4); 13 câu `first`/`next` nhóm <3 mốc (cộng vào 30 câu yếu); 7 trang 0 câu; Session 13–15 (55 trang, 195 câu, 2026-11-11, mục 10.5az): 2 lỗi checker (SV_Darmstadt_98:4, :5), 4 cửa sổ chữ (VFA_94:1, :2), câu nghi Pettus:1–3, Gordon_W_McKay:2, Florida:1–2; đã bỏ/sửa theo xác nhận (v9 còn 1182 câu, checker 0 lỗi); [1][2][3] chưa chạy.
- **Gold nghi thiếu mốc (từ báo cáo Haiku Session 5–8 và 9–12):** danh sách ở `docs/eval/10` mục 10.5ax.7; dùng làm đầu vào cho việc soát gold lần hai (không thêm vào gold theo chỉ dẫn hiện hành).
- **Soát gold:** gold 50 trang mới mới qua một vòng DeepSeek và đọc tay các ca nghi, chưa có người đọc thứ hai. Có 13 mốc thiếu phát hiện (Vologda 8, ACS_Poli 4, Alemannia 1); chưa quyết có đưa vào `extras` hay không.
- **`extras/` (ĐÃ CHỐT GIỮ, người dùng 2026-11-11, `decisions/14` mục 18: để tính precision khi ingest; đề xuất "không cần" trước đó của Claude đã bị bác):** thư mục `dataset/eval/timeline_pilot/extras/` đã tạo ngày 2026-11-10 bằng `chain_apply.py --apply` cho ca đầu tiên (`Vologda.json`, mốc 1936-12 của v9; xem `decisions/14` mục 11). Hai mốc từ v7n (Cochran, Sam_Selvon) vẫn chưa ghi vào `extras/` (v7n chưa áp) và chưa từng qua ingest, nên chưa dùng được cho precision; mốc Vologda cũng chưa qua ingest.
- **Ranh giới với Cơ chế 3:** theo người dùng, Cơ chế 3 gốc xử lý mâu thuẫn khi nạp lại trang với bản mới hơn (ví dụ cùng trang Wikipedia bản mới). Mâu thuẫn trong cùng một trang (`source_inconsistent`) có thuộc Cơ chế 3 hay không thì chưa biết.
- **Lưu ý gold `source_inconsistent`:** gold lưu không đồng nhất (1 mốc cờ không mốc cho phiên bản kia, 2 mốc cùng cờ, 1 mốc cờ cạnh mốc chính); chưa lưu ngày thay thế. 156 mốc trên 73 trang.
- **Bước kiểm/gộp:** `local/chain_derived.py` và `local/chain_apply.py` đã viết và chạy thử; chưa áp thật vì bộ chính (v8, v8n) cần 0 ca.
- Việc cũ: ingest v10, Cơ chế 3, soát độc lập Gemini, `outdated_infos` HoH, ontology.
- **Gold tune dùng guide v1–v6 (ghi 2026-11-11, `docs/eval/10` mục 10.5bb):** 203 trang tune: v1 5, v2 10, v3 10, v4 40, v5 10, v6 128; chỉ valid dùng v7. Sót 2–10% tùy đợt, sai/thừa 2–4% (tự đếm, chưa kiểm chứng độc lập). Rủi ro riêng: 25 trang v1–v3 chưa có quy ước `derived_date`. Chưa làm: soát lại tune, đếm mốc không cờ nghi derived ở v1–v3; chờ bước B.
- **Gold test_clean (ghi 2026-11-11):** **CẬP NHẬT: đủ 186 trang gold ở `batchT/sub/` (xem các dòng session bên dưới, `docs/eval/10` 10.5bc–10.5bg).** Chuẩn bị gồm `batchT/` và prompt `local/prompts/gold_test_clean_v7.md` (38 session, mỗi agent một trang). Chờ người dùng chốt: giữ `GUIDE_v7.md` hay sửa trước, và mức soát (đọc kỹ cả 186 trang hay chỉ trang nghi ngờ).
- **Gold test_clean session 1–10 (ghi 2026-11-11, đã soát; `docs/eval/10` mục 10.5bc):** 50 trang, 1764 mốc trong `batchT/rev/`, `check.py` 0 lỗi sau khi sửa `check.py` cho số có dấu phẩy. Đã sửa trong `rev/`: Cueva_de_las_Manos (thêm 2 mốc TCN), SMS_Cormoran_1909 (cờ e5, quote), `page_id` hai trang. Còn chờ: soát tiếp 40 trang chưa đọc; cờ mùa giải `derived_date`/`approximate_date` không đồng nhất (ví dụ Inter_Milan e50, e51); 28 session còn lại (11–38) chưa chạy; tuân thủ ràng buộc của agent chưa kiểm chứng.
- **Gold test_clean session 11–20 (ghi 2026-11-11, `docs/eval/10` mục 10.5be, chưa soát, còn ở `batchT/sub/`):** 50 trang, 1614 mốc (140 `derived_date`, 43 `approximate_date`, 14 `source_inconsistent`), `check.py` 0 lỗi; cộng 1–10 là 100 trang, 3378 mốc. Chờ quyết: mức soát (chỉ trang nghi ngờ: Ouagadougou, Wellington_Somerset, Pennsylvania_E44, Clarice_Phelps, P_bram, Klamath, Nick_Saban, Louis_Francis_Salzman, Western_Military_District_Sweden, các trang 0 undated, hay đọc kỹ cả 50). Còn session 21–38.
- **Gold test_clean session 21–30 (ghi 2026-11-11, `docs/eval/10` mục 10.5bf, chưa soát, còn ở `batchT/sub/`):** 50 trang, 1355 mốc (260 `derived_date` = 19%, 60 `approximate_date`, 26 `source_inconsistent`), `check.py` 0 lỗi; cộng 1–30 là 150 trang, 4733 mốc. Cờ nhiều ở 6 trang U-boat (U_101 chỉ 13/74 mốc không cờ); đã đọc U_101: cờ đúng guide nhưng năm KHÔNG lấy từ đầu đoạn mà từ chunk khác (đính chính ở 10.5bf và `docs/process/10_DERIVED_DATE_CLASSIFICATION.md`). **Chờ quyết:** có nới luật `derived_date` (ngày-tháng, năm lấy từ câu liền kề) cho câu hỏi test_clean hay chấp nhận ít câu ở trang U-boat; mức soát gold 11–30. Còn session 31–38.
- **Gold test_clean session 31–38 và tổng 186 trang (ghi 2026-11-11, `docs/eval/10` mục 10.5bg):** đã đủ 186 file gold ở `batchT/sub/` (6236 mốc; 714 `derived_date`, 296 `approximate_date`, 71 `source_inconsistent`), `check.py` 0 lỗi. Session 31–38: 1505 mốc, `approximate_date` 137 (UD_Las_Palmas 49, 1_FC_K_ln 32: mùa giải bóng đá). Friedrich_Guggenberger e11 đổi cờ sang `derived_date` (đúng guide là `source_inconsistent`; không ảnh hưởng câu hỏi). **Chờ quyết:** mức soát 136 trang session 11–38 (`rev/` mới có 50 trang); nới `derived_date` (xem dòng session 21–30); sau đó viết prompt sinh câu hỏi test_clean.
- **Phân loại `derived_date` a/b (ghi 2026-11-11, `docs/process/10_DERIVED_DATE_CLASSIFICATION.md`):** mã `local/derived_classify.py`, kết quả `dataset/eval/timeline_pilot/derived_classify/` (kèm bản chụp cờ cũ). Trên test_clean: a chặt 49/713 mốc derived (6,9%); trang U-boat gần như không có loại a vì chunk không chứa năm. **Chưa làm/chưa kiểm chứng:** đọc `a_far`, `a_weakrel` (23), `c_*` (235, kể cả 49 ca `c_exact`: cờ có vẻ thừa), `b_anchor_prev_chunk` (50: có cho neo ở chunk liền trước không), kiểm lại mẫu `b_relative`/`b_no_anchor` tìm ca nhầm; chạy trên tune/valid gold; đo số câu thực sự cứu được; người đọc thứ hai cho loại a; **ĐÃ CHỐT KHÔNG NỚI** (`decisions/14` mục 18); không cần phân loại trên tune/valid.
- **Soát gold test_clean 136 trang (session 11–38) bằng gợi ý tự động (ghi 2026-11-11):** mã `local/gold_gap_sub.py` (chỉ đọc `batchT/sub/`, không sửa; `python3 -I local/gold_gap_sub.py` xếp hạng, `--list <Trang>` in câu): câu chunk có năm mà không quote nào/undated phủ. Kết quả: 1485 câu chưa phủ trên 136 trang (nhiều dương tính giả: thống kê, kết quả mùa giải, đơn vị con theo guide v7), 10 trang 0 gap. Xếp hạng đầu: Nick_Saban 65, Gary_Mills 57, USAFE 57, Boris_Nemtsov 55, P_bram 52, Province_of_Brandenburg 42, Wellington_Somerset 39, St_Bartholomew 38, John_Conyers 36, Loveland_Ohio 32. **Đã đọc gap của 6 trang** (Klamath, Wellington, Ouagadougou, Nick_Saban 24 câu đầu, P_bram 24 câu đầu, Ghaziabad 24 câu đầu): có ca sót thật (Nick_Saban "November 27, 2006 Alabama announced firing of Mike Shula" và "November 7, 1998"; P_bram đường sắt 1875, liên hoan Dvořák 1969, phòng kinh tế 1993; Ghaziabad "founded in 1740" cần kiểm vì câu cắt ở "a.d."); nhiều ca là hợp guide v7 (đơn vị con: trường, ngân hàng, nhà máy trong trang Wellington; danh sách làng/khu của Klamath; thống kê). **Chưa đọc gap** 130 trang còn lại; chưa quyết thêm mốc vào `rev/` hay không (chỉ dẫn hiện hành: không thêm vào gold tune/valid; test_clean chưa chốt).
- **Đã đọc gap 15 trang đầu bảng (2026-11-11, `docs/eval/10` mục 10.5bh):** Nick_Saban, Gary_Mills, USAFE, Boris_Nemtsov, P_bram, Province_of_Brandenburg, Wellington, St_Bartholomew, John_Conyers, Loveland, Wheel_of_Fortune, 1_Hanover_Square, Princess_Victoria_Melita, Lana_Turner, Cutty_Sark (+ Klamath, Ouagadougou, Ghaziabad). Có ứng viên sót thật ở hầu hết trang (3–10/trang), nhiều ca là loại theo guide v7. **Chưa đọc:** 118 trang còn lại; 5 trang cuối danh sách mới đọc 22 gap đầu; chưa đối chiếu ứng viên với mốc quanh. **Chờ quyết:** đề xuất không chạy lại Haiku, copy `sub/`→`rev/` cho 136 trang (kèm sửa nhỏ Guggenberger e11, U_101 e27/e28) rồi dựa vào bước [1][2][3] sau khi sinh câu hỏi; gen lại gold tune v1–v3 (25 trang) bằng v7 (câu hỏi các trang đó phải sinh lại).
- **Gen lại gold tune v1–v3 bằng guide v7 (ĐÃ CHẠY 5 session 2026-11-11, kết quả `docs/eval/10` mục 10.5bj: 25 trang, 696 mốc mới so với 776 cũ, `check.py` 0 lỗi; derived 39 mới so với 17 cũ, approximate 31 so với 1; chưa soát, chưa thay gold tune, cần kiểm nghi agent mở gold cũ ở các trang trùng text như Carl_Ehrensvard 24/34). Phần chuẩn bị ban đầu: 25 trang (pilot5 5, pilot10 10, batch2 10; 11–25 chunk mỗi trang). Thư mục mới `dataset/eval/timeline_pilot/batchR/` (`in/` 25 file chép từ ba batch cũ, `sub/` trống, `GUIDE_v7.md`); gold cũ ở `pilot5/me`, `pilot10/rev`, `batch2/rev` giữ nguyên, không ghi đè. Prompt chung `local/prompts/gold_regen_v1v3_v7.md` (người dùng nói "chạy session N", N=1–5, 5 agent Haiku mỗi session) + danh sách `local/prompts/pages_gold_regen_v1v3.json` (seed 7501). Sau khi chạy: đếm lại từ `batchR/sub/`, `check.py`, so với gold cũ (số mốc, cờ `derived_date`), soát, rồi quyết thay gold tune; thay thì câu hỏi v9 của các trang đó (v3 23 câu; v1, v2 chưa có câu v9) phải sinh lại vì id mốc đổi.
- **ĐÃ THAY gold tune v1–v3 (người dùng 2026-11-11; `decisions/14` mục 19, `docs/eval/10` mục 10.5bk):** gold mới ở `pilot5/rev`, `pilot10/rev`, `batch2/rev`; bản cũ ở `dataset/eval/timeline_pilot/old_gold_v1v3/`; thư mục gen lại là `regen_v1v3`. 23 câu v9 của 10 trang batch2 đã gỡ sang `local/questions/v9/_replaced_gold_v3/`; **25 trang chưa có câu v9, cần sinh câu mới** (pilot5, pilot10 chưa từng có). **Chưa soát:** 65 mốc cũ biến mất (có vẻ sót thật: Great_Tower_Neuwerk 1360/1909/1971, Quelli_che_il_Calcio 1993, Toungoo_dynasty 1740, Regius_Professor 2006-02, Mike_Bongiorno quốc tang 2009, Lev_Polugaevsky 1995) và nghi agent mở gold cũ (Carl_Ehrensvard, August_Maus trùng text).
- **Đọc gold + câu v4–v5 của tune, 50 trang, 164 câu (2026-11-11, `docs/eval/10` mục 10.5bi, chỉ đọc):** đáp án đúng ở các câu đọc, không thấy sai rõ. **Câu nghi chờ quyết (sửa lời hoặc bỏ):** The_One_Show:3 (e48 thông báo rời bị bỏ ngoài chuỗi, đáp án đổi nếu tính), Meet_the_Press:4 (bộ thử HD), Alemannia_Aachen:1 (e10 1938 đứng đầu hạng), Vindobona:2 (biên "mid-1960s" lấy 1964), Jerzy_Buzek:1 (e27 chưa kiểm chứng), Veliky_Novgorod:1 e20 `approximate_date` (hợp luật). **Chưa làm:** đối chiếu từng chunk; đọc gap 45 trang còn lại (472 câu chưa phủ trên 50 trang); 7 trang 0 câu (Ich_bin_ein_Star, The_Dark_Eye, USS_LCS_L_3_102, Minuta_slavy, Pelican_Island, British_Rail_Class_40, U_254) và D__band_ 1 câu trên 85 mốc; ứng viên mốc sót Eliot_Engel (22/12/2010, 19/12/2007), Hanover (1887, 4/1945, 2013, 2010), Veliky_Novgorod (1293). Gold tune v4–v5 chưa gen lại (đề xuất chỉ gen lại v1–v3).
- **Mốc TCN (ghi 2026-11-11, `docs/eval/10` mục 10.5bd, `decisions/14` mục 17):** gold 30 mốc âm trên 13744 (Han_dynasty 27, Cueva 3); chunk nhắc TCN khoảng 48 trên 16740 (0,29%, 11 trang trên 556, regex nhầm vài ca). Đã làm: luật checker, bỏ Han_dynasty:2. Chờ người dùng: (a) loại mốc `date` âm khỏi phần so sánh ingest-gold khi đo precision/recall; (b) kiểm xem chunk TCN có lọt vào kho với `start_time` sai không (chỉ đọc); (c) dặn prompt sinh câu hỏi test_clean không dùng mốc âm khi viết prompt.

## Vá gold tune v1–v3 mới theo v7 (2026-11-11, chiều)

- Gold cũ: pilot5 dùng GUIDE_v1 (không có mục KHÔNG ghi, không cờ, không luật thập kỷ/khoảng thời gian), pilot10 dùng GUIDE_v2 và batch2 dùng GUIDE_v3 (hai bản giống hệt nhau). Gold mới dùng GUIDE_v7. Phần lớn mốc "biến mất" là mốc v1–v3 ghi nhưng v7 cấm: mốc của thực thể khác (chi nhánh, thành phố, con tàu), chuyến đi của tàu/máy bay, thống kê, bài viết của chính nhân vật, giải truy tặng, mốc mùa giải, ngày kết thúc của hoạt động tham gia.
- Chỉ vá mốc v7 cho ghi mà bản mới sót. Công cụ `local/gold_patch_v1v3.py`, spec ở `local/gold_patch_v1v3/<Trang>.json`; bản chưa vá giữ ở `dataset/eval/timeline_pilot/regen_v1v3/sub/`, bản đã vá ở `pilot5|pilot10|batch2/rev/`. Chạy lại tool luôn vá từ bản chưa vá. `check.py` 0 lỗi trên 25 trang.
- Đã vá 24 mốc / 9 trang: Ernst_Hechler +8, Great_Tower_Neuwerk +3, Mike_Bongiorno +3, Regius_Professor_Civil_Law +4, Carl_Ehrensvard +2, Telekids +1, First_Air_Group +1, Aero_Union +1, Toungoo_dynasty +1.
- Không vá (đúng theo v7): World_Union_for_Progressive_Judaism (mốc của các chi nhánh/liên đoàn khác), Klemzig (chuyến tàu), Real_Audiencia (thị trấn/tỉnh khác), Derek_Barton, August_Maus, CS_Aerostar_Bacau, Lev_Polugaevsky, Martin_de_Gurrea, Quelli_che_il_Calcio, Thomas_Fearnley, Butch_Levy, Malvik, Southern_Military_District, John_Henry_Whitley, Frederick_Ralph_Sharp, Seibu_Shinjuku_Line, Great_Tower_Neuwerk 1909/1971.
- Việc còn lại: các mốc vá là phán đoán của tôi (ví dụ 1987 máy bay C-119 ở Aero_Union, 1740 ở Toungoo, 1994-12-31 ở Telekids), người dùng có thể bỏ nếu không đồng ý. Test_clean (136 trang) chưa vá: 161 câu có ngày đầy đủ chưa phủ trên 53 trang (Nick_Saban, Boris_Nemtsov, Wellington_Somerset, Gary_Mills, USAFE...). 25 trang tune v1–v3 vẫn chưa có câu v9.

## Vá gold test_clean theo v7 (2026-11-11, chiều)

- `batchT/rev/` đã đủ 186 trang (136 trang session 11–38 copy từ `sub/`, 50 trang session 1–10 giữ bản đã soát). `check.py` 0 lỗi.
- Đọc 47 trang có từ 2 câu ngày đầy đủ chưa phủ (tool `gold_gap_sub.py`) và thêm bằng `local/gold_patch_v1v3.py` (spec ở `local/gold_patch_v1v3/`, `dir=batchT`, vá từ `batchT/sub/`). Kết luận: phần lớn câu "chưa phủ" là mốc v7 cấm (trận đấu, chuyến tàu/lượt tuần tra, phát biểu của chính nhân vật, việc của người khác, ngày sinh con, giải/vinh danh sau khi mất), gold đã nhất quán với v7; không phải sót.
- Đã thêm 10 mốc / 9 trang: Boris_Nemtsov 2017-06 (xét xử vụ giết), Laurette_Onkelinx 2011-12-06, VP_29 1941-07-03 và 07-07, VP_42 1945-06-01, Cutty_Sark 2008-09-30, Princess_Victoria_Melita 1995-03-07, The_Cycle 2012-08-16, UD_Las_Palmas 2001-12-22, Jim_Prentice 2016-10-28 (tang lễ).
- Sửa nhỏ: U_101 bỏ e28 (trùng e27, cùng quote). Không đổi cờ Guggenberger e11 sang `source_inconsistent` vì `check.py` chỉ miễn quote thiếu năm khi cờ là `derived_date` (cờ đơn); để nguyên. Inter_Milan e50/e51 chưa sửa (chưa nhớ lỗi cụ thể, cần đọc lại).
- Chưa đọc: ~89 trang có dưới 2 câu ngày đầy đủ chưa phủ; câu chỉ có năm của các trang top (Nick_Saban, P_bram...) đọc lướt, không thêm. Mốc vá là phán đoán của tôi, người dùng có thể bỏ.

## Đọc nốt test_clean gold và kiểm tra nghi ngờ gold cũ ở tune (2026-11-11, tối)

- Mục 1 (89 trang còn lại): đọc các câu có ngày đầy đủ hoặc tháng-năm chưa phủ. Thêm 3 mốc: Guy_Aldred 1964-05-04 (hỏa táng), Cho_Yoon_sun 2018-08 (công tố đề nghị án), Nick_Saban 2007-01-01 (gặp Alabama). Còn lại là mốc v7 cấm hoặc mốc của người/thực thể khác. Tổng test_clean đã vá 13 mốc / 12 trang. `check.py` 0 lỗi cả 186 trang.
- Mục 2 (câu chỉ có năm): lọc 270 câu có động từ sự kiện, kiểm tra từng trang bằng cách so với mốc đã có trong gold. Hầu hết đã có mốc (tool gap báo dư vì quote khác). Không thêm mốc nào; Mission_San_Miguel 1833 (đạo luật thế tục hóa) bỏ vì quote chưa khớp, giá trị thấp.
- Mục 3: Inter_Milan e50/e51 đổi cờ `derived_date` thành `approximate_date` (mốc "mùa đầu của Mourinho", năm 2008 là năm bắt đầu mùa, đúng luật mùa giải của v7). Quote vẫn chứa năm 2008, `check.py` qua.
- Mục 4 (lớp derived chưa đọc): đọc đủ 15 `a_far`, 23 `a_weakrel`, 49 type a chặt (đọc lần hai), 16 `b_anchor_prev_chunk`, 49 `c_exact_*`, 22 mẫu `c_year_in_quote`. Không thấy phân loại sai. Kết quả: type a (chặt) và `a_far`/`a_weakrel` đều có năm suy ra hợp lý từ neo cùng chunk; type a chặt không có ca nào sai (đã đối chiếu thêm Vuk_Drašković e18 và Roger_Moore e96 với chunk). Lớp `c_exact_day/month` (49 mốc) thường có cờ `derived_date` thừa vì quote đã chứa ngày đầy đủ; `c_year_in_quote` hỗn hợp (một số đúng là suy ra, ví dụ Inter_Milan 2004→2005, một số cờ thừa, ví dụ Cho_Yoon_sun e5 1991). Không sửa cờ (quyết định giữ cờ cũ); `derived_date` vẫn cấm trong mọi câu hỏi, nên cờ thừa chỉ làm mất ứng viên, không gây sai câu.
- Mục 5 (tune v1–v3, agent có mở gold cũ không): không có bằng chứng. Văn bản trùng giữa gold cũ và mới (Carl_Ehrensvard 25/35, August_Maus 13/38, John_Henry_Whitley 10/21) gần như luôn là câu chép sát chunk: trong mọi trang chỉ có tối đa 4 mốc trùng chứa từ ngoài quote, và Carl chỉ có 2. Không có chú thích riêng của gold cũ ("date as printed", "(1950s)", "as printed"...) nào xuất hiện lại ở gold mới; Ernst_Hechler cũ 60 mốc, mới 37, 0 mốc trùng nguyên văn. Không thể chứng minh phủ định vì không có log của phiên Haiku (người dùng chạy), nên đây là "chưa thấy dấu hiệu".

## Prompt sinh câu v9 cho 25 trang tune v1–v3 (2026-11-11, tối)

- Đã viết `local/prompts/sinh_cau_hoi_v9_tune_v1v3.md` (1 session, 5 agent × 5 trang, Haiku do người dùng chạy). Khối subagent lấy từ `sinh_cau_hoi_v9_valid3.md`, đổi đường dẫn gold thành `DIR/rev/P.json` (DIR = `pilot5`, `pilot10` hoặc `batch2`) và thêm mục N (không dùng mốc `date` âm; guide v7 dùng một mốc cho hoạt động; `label` lạ chỉ gom khi ≥3 mốc).
- Đã sửa `local/questions/check_questions.py` (`load_page`) để tìm gold ở cả `batch*` và `pilot*`; trước đó trang `pilot5`/`pilot10` không load được nên chưa từng có câu v9. Chưa chạy checker; chạy `python3 -I local/questions/check_questions.py v9` sau khi có câu (ghi đè `checked.jsonl`).
- Chờ người dùng chạy session; sau đó chạy checker, đọc báo cáo agent và xử lý id nghi sai.
