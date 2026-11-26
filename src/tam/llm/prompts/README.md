# Prompt LLM của đồ án

Tên file theo dạng `<vai trò>_<cơ chế>.md`, không có số phiên bản: file ở thư mục này là **bản đang dùng**. Bản cũ nằm trong `archive/` và vẫn chạy được: `prompt_path` (`tam/llm/prompt_files.py`) tìm ở đây trước, rồi `archive/`; bảng `ALIASES` ánh xạ tên cũ (`agent_v5`, `ingestion_time_v3`, `time_extractor_v2`...) sang file đang dùng, nên `--prompt v5` hay `--prompt-version v3` vẫn chạy. Prompt đổi nội dung thì chép bản cũ sang `archive/` kèm hậu tố phiên bản (vd `agent_m1_v1.md`) và ghi dòng vào "Lịch sử" ở cuối.

Khóa cache LLM gồm nội dung prompt, không gồm tên file. Các prompt tách từ script (đánh dấu ★) đã kiểm giống hệt nguyên văn trước khi tách, nên không đổi khóa cache.

## Đang dùng

| File | Việc | Cơ chế | Dùng ở | Ghi chú |
|---|---|---|---|---|
| `ingest_m1.md` | nạp kho vector: gán `start`, `end`, `domain` cho từng chunk | 1 | `scripts/ingest.py --prompt-version v3` | = bản v3 (`ingestion_time_v3`); kho tune, valid, test_clean dựng bằng bản này; `extractions.jsonl` ghi `prompt_version = v3` |
| `profiler_m1.md` | Profiler: câu hỏi → khoảng thời gian `t_req`/`t_end`, bộ lọc | 1 | `query/range_profiler.py` (`PROMPT_VERSION = "v2"`) | = bản v2 (`time_extractor_v2`); `profiler.jsonl` ghi `prompt_version = v2` |
| `answer_m1.md` | trả lời của pipeline P1–P10 (top-5 chunk) | 1 | `generate_answers.py --prompt m1` | **= `archive/answer_m1_v4.md`** (chốt 2026-11-25 sau tune trên 200 câu; `docs/planning/03` mục 13) |
| `agent_m1.md` | agent A1–A5 | 1 | `run_agent_search.py --prompt m1` | **= `archive/agent_m1_v4.md`** (chốt 2026-11-25); không nêu tên công cụ (5 cấu hình dùng chung) |
| `judge_m1.md` | LLM judge chấm câu trả lời Cơ chế 1 (pipeline và agent): `verdict`, `matches_gold`, bịa, trung thực, từ chối đúng lúc, trích dẫn, lý do | 1 | `scripts/judge_answers.py --prompt judge_m1` (profile `opencode_glm_5_3`) | **bản đang dùng = `judge_m1.md` (= `archive/judge_m1_v5.md` + trường `grounded` thay `supported_by_passages`)**; v1 đến v6 trong `archive/judge_m1_v1..v6.md` (v6 thêm quy tắc 12 và 13, kém ổn định hơn, không dùng) (thử trên 37 câu, chưa duyệt tay; `docs/planning/03` mục 16) |
| `ingest_m2.md` ★ | nạp graph: trích sự kiện có ngày theo từng mục của trang | 2 | `dataset/eval/timeline_pilot/outline_trial/pass3_p10b_oc.py` | bản `p10b` (log `out_p10b_*`); chưa kiểm bản nào dùng cho từng tập |
| `pair_m2.md` ★ | gộp cặp sự kiện: `same` / `different` | 2, 3 | `local/ingest_eval/judge.py`, `graph_build{,_T,_V,_C}.py`, `scripts/m3_build_old.py` | Cơ chế 3 dùng lại khi dựng trạng thái cũ |
| `answer_m2.md` ★ | trả lời phương pháp cố định (không agent) trên timeline: LLM chọn `selected_ids` | 2 | `scripts/v9_eval/v9_fixed_eval.py` | đầu vào là timeline đã trích; cấu hình `vec` (nút của chunk top-k, không đi dọc ô) và `graph*` (chunk → nút → đi dọc ô) dùng cùng prompt này, chỉ khác cách truy xuất. Cả hai đều đọc nút từ Neo4j |
| `agent_m2.md` | agent timeline, đầu ra JSON `{kind, number, events, evidence}` | 2 | `run_agent_search.py --prompt m2` | = `agent_v5` cũ |
| `update_m3.md` ★ | hệ "LLM quyết định": cập nhật graph khi một chunk bị sửa (`keep`/`close`/`invalidate`/`add`) | 3 | `scripts/m3_update_prompt.py` | |
| `answer_m3.md` ★ | trả lời phương pháp cố định cho câu hỏi Cơ chế 3, đọc dòng "(ended …)" | 3 | `scripts/m3_fixed_mech3.py` | có chỗ `{t_now}` |
| `agent_m3.md` | agent chỉ có công cụ graph (`timeline`, `events_of_chunk`, `list_pages`) | 3 | `run_agent_search.py --graph-only --prompt m3` | = `agent_v6` cũ |

Window-replace và Diff-replace (Cơ chế 3) không gọi LLM nên không có prompt.

## File đang dùng ↔ file trong `archive/`

| File đang dùng | Quan hệ với `archive/` |
|---|---|
| `ingest_m1.md` | là `ingestion_time_v3.md` đổi tên; bản trước ở `archive/ingestion_time_v1.md`, `ingestion_time_v2.md` |
| `profiler_m1.md` | là `time_extractor_v2.md` đổi tên; bản trước ở `archive/time_extractor_v1.md` (một điểm) |
| `answer_m1.md` | **sửa từ `archive/answer_v4.md`** (cùng cách ghi khoảng hiệu lực trong ngoặc, cùng 3 ví dụ); thêm quy tắc "một trạng thái giữ nguyên đến khi đoạn nói nó đổi" (rule 3), tách "không đoán, không dùng kiến thức ngoài" ra rule 4. Các bản gốc `answer_v1`..`v3` cũng ở `archive/`. Các bản tune: `archive/answer_m1_v1.md` (nháp đầu) đến `answer_m1_v6.md`; bản đang dùng = v4 (v3 + 'đúng một đáp án'). Xem Lịch sử |
| `agent_m1.md` | **viết lại**, không phải bản sao. Mượn ý từ `archive/agent_v3.md`, `agent_v4.md` (nêu giá trị kèm mốc, mốc phủ một phần thì vẫn đưa giá trị, dừng khi hết thông tin mới); khác: thêm "trả lời đúng mốc hỏi", bỏ dòng `Type:`, `Answer:` là cụm ngắn nhất (chấm EM/F1). Các bản tune: `archive/agent_m1_v1.md` đến `agent_m1_v6.md`; bản đang dùng = v4 |
| `agent_m2.md`, `agent_m3.md` | là `agent_v5.md`, `agent_v6.md` đổi tên (không còn bản cũ ở `archive/`) |
| `ingest_m2.md`, `pair_m2.md`, `answer_m2.md`, `answer_m3.md`, `update_m3.md` | tách nguyên văn từ hằng trong script, không có bản trong `archive/` |

## `archive/` (bản cũ, giữ để tái lập)

| File | Là gì |
|---|---|
| `agent_v1.md` | P0, agent đối chứng trung tính (`planning/02`) |
| `agent_v2.md`, `agent_v3.md`, `agent_v4.md` | P1 đến P3, agent đối chứng trên TimeQA, kiểu A và B (`planning/02` mục 11) |
| `answer_v1.md` | trả lời pipeline, chọn trên `valid` cho Gemini; cho phép từ chối |
| `answer_v2.md` | v1 + khoảng hiệu lực của chunk |
| `answer_v3.md`, `answer_v4.md` | v1, v2 nới điều kiện từ chối (`eval/07`) |
| `ingestion_time_v1.md`, `ingestion_time_v2.md` | bản cũ của prompt nạp (v1 là mặc định của `ingest.py` nếu không đặt `--prompt-version`) |
| `time_extractor_v1.md` | Profiler một điểm (`query/profiler.py`) |
| `answer_m2_chunk.md` ★ | **đối chứng của Cơ chế 2**: trả lời bộ v9 từ top-k chunk thô (cấu hình `a` dense, `b` hybrid), không có timeline đã trích và không dùng graph; LLM tự viết sự kiện, đầu ra JSON `{kind, number, events}` (`scripts/v9_eval/v9_chunk_eval.py`). Chỉ để so với `answer_m2.md`, không phải đường chính. Tách nguyên văn từ hằng `SYSTEM` của script |

## Không phải thành phần hệ thống (không tách)

| Nơi | Là gì | Dùng để làm gì |
|---|---|---|
| `local/ingest_eval/judge.py` (`EV_PROMPT`) | kiểm các sự kiện ingest không khớp timeline gold: `duplicate`, `in_scope_missing`, `out_of_scope`, `unsupported` | **đo chất lượng nạp graph** (độ chính xác), không chạy lúc vận hành |
| `local/ingest_eval/reader.py` (`SYSTEM`) | LLM đọc timeline gold hoặc timeline ingest và chọn mốc trả lời câu v9 | đo **tác động của chất lượng nạp lên câu trả lời** |
| `scripts/make_past.py` (`PROMPTS`) | sinh bản quá khứ của chunk | tạo dữ liệu thử Cơ chế 3 |
| `local/prompts/*.md` (40 file) | sinh và rà soát bộ câu hỏi, rà gold | dựng bộ dữ liệu đánh giá |

## Lịch sử

- 2026-11-25: lưu bản nháp đầu của `answer_m1`, `agent_m1` vào `archive/answer_m1_v1.md`, `archive/agent_m1_v1.md` (chạy được bằng `--prompt m1_v1`); các bản sửa khi tune là `m1_v2`, `m1_v3`; chốt bản nào thì chép vào `answer_m1.md`/`agent_m1.md`.
- 2026-11-25: đổi sang dạng `<vai trò>_<cơ chế>.md` (`ingestion_time_v3` → `ingest_m1`, `time_extractor_v2` → `profiler_m1`, `agent_v5` → `agent_m2`, `agent_v6` → `agent_m3`; bản cũ vào `archive/`); thêm `agent_m1`, `answer_m1` (bản nháp, viết cho DeepSeek, chưa chạy); tách ra file `ingest_m2`, `pair_m2`, `answer_m2`, `answer_m3`, `update_m3` và `archive/answer_m2_chunk` (đối chứng, không phải đường chính), giống hệt nguyên văn.
- Quy ước tune Cơ chế 1 (chốt 2026-11-25): chỉ trên tập `tune` (`tune50` để sửa, `tune50b` để chốt), không dùng `valid` hay `test_clean`.
- 2026-11-25 (tune `answer_m1`, `agent_m1`, chi tiết `docs/planning/03` mục 13): các bản trong `archive/` (chạy bằng `--prompt m1_v1`..`m1_v6`): v1 = nháp đầu; v2 = đối chiếu mốc với khoảng hiệu lực, chỉ từ chối khi không đoạn nào nêu giá trị (không tăng); v3 = đáp án chỉ là tên thực thể, không danh hiệu hay chú thích, hai đáp án đều đúng thì liệt kê; **v4 = v3 nhưng đúng MỘT đáp án (đang dùng)**; v5 = v4 + không dùng đoạn có mốc bắt đầu sau thời điểm hỏi + chép từng ký tự (quy tắc mốc làm agent từ chối thêm); v6 = v4 + chép từng ký tự (ngang v4, chênh dưới 1 sai số chuẩn). v1 đến v4 chạy trên `tune50` và `tune100`, v4 đến v6 thêm `tune100c` (câu mới, chưa dùng để chọn). Chốt v4 theo luật chỉ đổi khi hơn 2 sai số chuẩn.
- 2026-11-26: thêm `judge_m1.md` (judge GLM-5.3, một lần gọi cho mỗi cặp câu hỏi - đáp án); các bản trong `archive/judge_m1_v1..v4.md`. v1 = verdict, match_type, lý do; v2 = kiểm mốc dù khớp nhãn; v3 = thêm trung thực, bịa, từ chối đúng lúc, trích dẫn; v4 = `matches_gold` tách khỏi `verdict`, `relevant_passages`, `borderline`; bản hiện tại thêm quy tắc JSON hợp lệ, đúng và đủ tách nhau, cấp độ khác là sai, nhãn không phải đáp án.
