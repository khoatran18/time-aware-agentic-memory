# Tái hiện các lần đo trên câu timeline v9 (tune, 600 câu)

Tài liệu này ghi **mỗi script làm gì, lệnh nào đã chạy, kết quả nằm ở đâu**, để dựng lại bảng kết quả trong báo cáo. Số liệu và phân tích nằm ở `docs/planning/02_AGENT_SEARCH_BASELINE.md` (mục 11.16 đến 11.19 và mục 14); tài liệu này chỉ lo phần tái hiện. Ghi ngày 2026-11-15.

## 1. Điều kiện cần

| Thành phần | Trạng thái dùng khi đo |
|---|---|
| Qdrant, collection `tam_chunks_dev_tune` | kho vector của split tune, hybrid dense + BM25 (`configs/config.dev.yaml`) |
| Neo4j (`tam-neo4j`) | graph sự kiện của 203 trang tune (`Page`, `Cell`, `Event`, `Chunk`) |
| LLM | profile `opencode_deepseek_flash` (OpenCode Go, DeepSeek V4.1 Flash); khóa trong `.env` (không in ra) |
| Cache LLM cục bộ | `data/llm_cache/agent/` (agent), `data/llm_cache/reader/` (cố định d, f), `data/llm_cache/chunk_eval/` (a, b); gitignore |
| Gold | `dataset/eval/timeline_pilot/*/rev/<Trang>.json` và `questions_v9/<Trang>.jsonl` (trong git) |
| Bộ con câu hỏi | `dataset/eval/v9_graph203_subset.json` (600 câu, 195 trang), `v9_graph53_subset.json` (204 câu, phần 1), `v9_graph203_rest_subset.json` (396 câu, phần 2) |
| **Phụ thuộc ngoài git** | `local/ingest_eval/judge_out/graph_nodes.json` (4,3 MB, do `local/ingest_eval/graph_build.py` sinh; `local/` bị gitignore). Chỉ `v9_fixed_eval.py` cần file này (danh sách nút của từng trang). **Nên sao lưu file này.** |

Mỗi cấu hình chạy **một lần**, mọi lần gọi LLM qua cache (CLAUDE.md). Chạy lại cùng đầu vào trúng cache nên không tốn lần gọi mới.

## 2. Các script

| Script | Việc | Gọi LLM |
|---|---|---|
| `scripts/make_v9_graph_subset.py` | Lấy trang đang có trong graph Neo4j, ghép với `questions_v9`, loại trang thiếu chunk trong kho vector, ghi bộ con câu hỏi (`--out`). Câu hỏi đổi thành `tên trang. câu hỏi` (cột `question_hard`) | không |
| `scripts/run_agent_search.py` | Chạy agent (A: văn bản thô; B: công cụ vector; `--graph` thêm `timeline`, `events_of_chunk`) trên bộ con, tối đa 5 lượt mỗi câu, prompt v5. Ghi `output/<thời điểm>/` (`results.jsonl`, `agent_trace.jsonl`, `agent_calls.jsonl`, `tool_texts.jsonl`, `llm_calls.jsonl`, `run.log`) | có |
| `scripts/v9_eval/v9_score.py` | Bộ chấm câu v9 (exact, precision, recall, F1, order); `selftest` kiểm bộ chấm bằng đáp án oracle và biến dạng cố ý | không |
| `scripts/v9_eval/v9_agent_score.py` | Chấm lại kết quả của `run_agent_search.py` bằng `v9_score.py`; tính độ phủ (cov_tl theo dòng timeline, cov_ch theo chunk), `--detail` | không |
| `scripts/v9_eval/v9_fixed_eval.py` | Phương pháp cố định d (`vec`) và f (`graph`, `graph_tb`, `graph_tt`): truy xuất sự kiện, một lần gọi LLM chọn `selected_ids`, đổi thành `{date, text}`, chấm bằng `v9_score.py`. `DRY=1`: chỉ truy xuất, in trần truy xuất | có (trừ DRY) |
| `scripts/v9_eval/v9_chunk_eval.py` | Phương pháp cố định a (`dense`) và b (`hybrid`): top-k chunk thô (k = 15) đưa cho LLM, một lần gọi, đáp án `{kind, number, events}` như agent. Ghi số đo từng câu (thời gian, token vào/ra/cache). `DRY=1`: chỉ truy xuất, đếm token ước | có (trừ DRY) |

`v9_fixed_eval.py` chứa nguyên văn prompt đọc của `local/ingest_eval/reader.py` (sao ngày 2026-11-15) để tái hiện được dù file đó thay đổi; đổi chữ nào là đổi khóa cache. Bản cũ của bốn script `v9_*` còn ở `local/` (gitignore); bản trong `scripts/v9_eval/` là bản chính.

## 3. Lệnh đã chạy

Chạy từ gốc repo. `S` là thư mục tạm; các lệnh dưới đây là dạng đã dùng.

**Bộ con câu hỏi**
```
python3 scripts/make_v9_graph_subset.py --out $S/all203.json    # 600 câu, 195 trang sau khi loại 8 trang thiếu chunk
# v9_graph53_subset.json = 53 trang đầu (204 câu); v9_graph203_rest_subset.json = 600 trừ 204 (396 câu)
```

**Agent (g, h, i), mỗi phần ba cấu hình**
```
C="--subset dataset/eval/v9_graph53_subset.json --n 300 --prompt v5 --workers 20"       # phần 204 câu, chạy lần lượt
python3 scripts/run_agent_search.py $C --kind B --graph --normalize-page-names           # i: B + graph
python3 scripts/run_agent_search.py $C --kind B                                          # h: B
python3 scripts/run_agent_search.py $C                                                   # g: A

C="--subset dataset/eval/v9_graph203_rest_subset.json --n 500 --prompt v5"               # phần 396 câu, chạy song song
python3 scripts/run_agent_search.py $C --workers 7 --kind B --graph --normalize-page-names
python3 scripts/run_agent_search.py $C --workers 7 --kind B
python3 scripts/run_agent_search.py $C --workers 6
```
Chấm: `python3 -I scripts/v9_eval/v9_agent_score.py . <tên thư mục chạy> [--detail]` (tên thư mục trong `output/`, không kèm `output/`).

**Phương pháp cố định d, f**
```
python3 -I scripts/v9_eval/v9_fixed_eval.py        # VARIANTS mặc định vec,graph,graph_tb,graph_tt; 20 luồng; DRY=1 để chỉ truy xuất
```

**Phương pháp cố định a, b**
```
python3 -I scripts/v9_eval/v9_chunk_eval.py        # VARIANTS mặc định dense,hybrid; K=15; 20 luồng; DRY=1 để chỉ truy xuất
```

## 4. Kết quả nằm ở đâu

`output/` bị gitignore, nên các thư mục dưới đây chỉ có trên máy. Đợt test tổng đã gom bản sao vào `output/agent_v9_tune600/`.

| Cấu hình | Thư mục gốc trong `output/` | Bản gom |
|---|---|---|
| i (B + graph) | `20261115_174811` (204 câu), `20261115_182835` (396 câu) | `agent_v9_tune600/B_graph/` |
| h (B) | `20261115_174955`, `20261115_182837` | `agent_v9_tune600/B/` |
| g (A) | `20261115_175130`, `20261115_182839` | `agent_v9_tune600/A/` |
| d, f (cố định, sự kiện) | `20261115_191028` | `agent_v9_tune600/fixed/vec_graph_600q/` |
| a, b (cố định, chunk thô) | `20261115_211101` (1.194 lần gọi; lần thử 3 câu `20261115_211015` đã nằm trong cache) | `agent_v9_tune600/fixed/dense_hybrid_chunk_600q/` |

Mỗi thư mục có `README.md` mô tả cách đọc. Số đo từng câu: agent trong `results.jsonl` (token vào/ra/cache, `cache_hits`, số lượt, số lần gọi công cụ, `llm_time_s`, `tool_time_s`, `wall_s`, `ttft_s`, `stop_reason`); d, f trong `results.jsonl` (điểm, số nút, độ dài) và `llm_calls.jsonl` (token, thời gian); a, b trong `results.jsonl` (điểm, thời gian truy xuất, chờ LLM, wall, token vào/ra/cache).

## 5. Kết quả a, b (chunk thô, k = 15; `output/20261115_211101`)

| Cấu hình | exact | F1 | phủ chunk gold | token vào TB (cache) | token ra TB | thời gian chờ LLM TB (p50 / p90) | USD |
|---|---|---|---|---|---|---|---|
| a dense | 0,845 | 0,919 | 0,905 | 2.006 (424) | 1.238 | 14,8 s (9,5 / 33,8) | 0,59 |
| b hybrid | 0,868 | 0,930 | 0,930 | 2.072 (489) | 1.269 | 15,1 s (9,1 / 35,6) | 0,60 |

Theo loại (exact, a / b): list 0,738 / 0,794; summary 0,734 / 0,719; first_last_next 0,891 / 0,897; order_gap 0,987 / 1,000. Tổng 1.194 lần gọi (6 trúng cache cục bộ), 2,45 triệu token vào (0,55 triệu cache), 1,50 triệu token ra, khoảng 1,19 USD theo giá Flash, 933 s với 20 luồng, không câu hỏng, không lần thử lại. Truy xuất 0,013 s mỗi câu.

## 6. Chế độ suy luận (thinking)

Mọi kết quả ở mục 4 và 5 chạy với thinking **bật** (mặc định của hồ sơ). Lần chạy thinking **tắt** (mục 11.20 của `02_AGENT_SEARCH_BASELINE.md`): thêm `--no-thinking` cho `run_agent_search.py`, hoặc `THINKING=off` cho `v9_chunk_eval.py` và `v9_fixed_eval.py`; cache riêng nên không trộn với lần bật.

| Cấu hình (thinking tắt) | Thư mục `output/` | Lệnh |
|---|---|---|
| a | `20261115_220403` | `THINKING=off VARIANTS=dense python3 -I scripts/v9_eval/v9_chunk_eval.py` |
| b | `20261115_221607` | `THINKING=off VARIANTS=hybrid WORKERS=12 python3 -I scripts/v9_eval/v9_chunk_eval.py` |
| d, f, f′, f″ | `20261115_223117` (không dùng `20261115_221726`: chạy nhầm thinking bật, toàn trúng cache) | `THINKING=off WORKERS=12 python3 -I scripts/v9_eval/v9_fixed_eval.py` |
| g (agent A) | `20261115_221538` | `python3 scripts/run_agent_search.py --subset dataset/eval/v9_graph203_subset.json --n 1000 --prompt v5 --workers 12 --no-thinking` |
| h (agent B) | `20261115_220350` | cùng lệnh g, thêm `--kind B` (workers 20) |
| i (agent B + graph) | `20261115_221538_2` | cùng lệnh g, thêm `--kind B --graph --normalize-page-names` |

Bảng kết quả đầy đủ cả hai chế độ: `docs/eval/12_V9_TUNE600_RESULTS.md` (và mục 11.20 của `docs/planning/02_AGENT_SEARCH_BASELINE.md`). Số đo từng câu: a, b, d, f trong `results.jsonl` (`retrieval_s`, `llm_s`, `wall_s`, token vào/ra/cache, `local_cache_hit`); g, h, i như mục 4.

## 7. Đo lại các cấu hình dùng graph sau khi ingest lại (2026-11-17, thinking tắt, 619 câu)

**Điều kiện thay đổi so với mục 3 đến 6.**
- Graph Neo4j tune được nạp lại hoàn toàn (ingest thinking tắt; 203 trang, 8.792 sự kiện, `node_id` đổi). Chỉ có một bản graph trong Neo4j; bản cũ chỉ còn ở `local/ingest_eval/judge_out/graph_nodes_before_thinkoff.json` (8.968 nút). `local/ingest_eval/judge_out/graph_nodes.json` (4,2 MB, ngoài git) đã sinh lại cho bản mới; `v9_fixed_eval.py` đọc file này, nên phải sinh lại mỗi khi nạp lại graph.
- Kho vector `tam_chunks_dev_tune` nạp bù 97 chunk không có mốc bằng `local/ingest_eval/vec_fill.py` (chọn kho bằng `COL=...`, không gọi LLM): 5.995 chunk, gắn `domain_features.fill = "undated_dropped"`. Không còn chunk nào mà graph trỏ tới bị thiếu trong Qdrant.
- Profile `opencode_deepseek_flash` trong `configs/config.dev.yaml` nay có sẵn `extra_body: {thinking: {type: "disabled"}}`, nên mọi lần chạy đều tắt thinking dù có truyền cờ hay không. Khóa cache không chứa cờ này, nên cache được tách theo thư mục (`reader_nothink`, `agent_nothink`).
- Bộ con mới `dataset/eval/v9_graph_tune_subset.json` (619 câu, 176 trang có câu; 600 câu cũ và 19 câu mới), dựng bằng `python3 scripts/make_v9_graph_subset.py --out dataset/eval/v9_graph_tune_subset.json`. Bộ cũ `v9_graph203_subset.json` (600 câu) giữ nguyên.

**Lệnh và thư mục kết quả** (30 luồng, chạy song song hai lệnh):

| Cấu hình | Thư mục `output/` | Lệnh |
|---|---|---|
| d, f, f′, f″ | `20261117_115607` (2.476 mục, 311 s) | `THINKING=off WORKERS=30 SUBSET=dataset/eval/v9_graph_tune_subset.json python3 -I scripts/v9_eval/v9_fixed_eval.py` |
| i (agent B + graph) | `20261117_115405` (619 câu) | `python3 scripts/run_agent_search.py --subset dataset/eval/v9_graph_tune_subset.json --n 1000 --prompt v5 --workers 30 --no-thinking --kind B --graph --normalize-page-names` |

Chấm agent: `python3 -I scripts/v9_eval/v9_agent_score.py . 20261117_115405`. d, f, f′, f″ tự chấm khi chạy (bảng trong `run.log` và `results.jsonl`).

**Không đo lại** a, b, g, h (không dùng graph); số của chúng vẫn ở mục 4 đến 6 (600 câu, kho tune chưa có chunk bù). Kết quả và so sánh với lần đo trước: `docs/eval/12_V9_TUNE600_RESULTS.md` mục 4.

## 8. Chạy trên tập valid (2026-11-17, thinking tắt, 554 câu)

**Điều kiện.** Kho vector `tam_chunks_dev_valid` (5.063 chunk, 179 bù); graph Neo4j chứa thêm 167 trang valid (7.490 sự kiện; dựng bằng `local/ingest_eval/graph_build_V.py`, danh sách nút `local/ingest_eval/judge_out/graph_nodes_V.json`, ngoài git, nên sao lưu). Tên trang đã bỏ dấu ở graph và file câu hỏi; bộ con dùng đúng tên đó.

**Thay đổi script.** `v9_fixed_eval.py` và `v9_chunk_eval.py` nhận thêm `COLLECTION` (kho vector) và, riêng `v9_fixed_eval.py`, `NODES_FILE` (danh sách nút); cả hai ghi thêm `run_meta.json` (thinking thực tế của profile, mô hình, kho, bộ câu hỏi, luồng, mã git), `prompts.jsonl` (prompt người dùng + đáp án thô từng cấu hình × câu) và `system_prompt.txt`; chọn cache `reader_nothink` / `chunk_eval_nothink` theo `extra_body` thực tế của profile. `v9_agent_score.py` in số tới 3 chữ số.

**Lệnh** (từ gốc repo, `S=dataset/eval/v9_graph_valid_subset.json`):
```
python3 scripts/make_v9_graph_subset.py --collection tam_chunks_dev_valid --out $S     # 554 câu, 167 trang (các trang bị loại là trang tune)
THINKING=off WORKERS=25 SUBSET=$S COLLECTION=tam_chunks_dev_valid NODES_FILE=local/ingest_eval/judge_out/graph_nodes_V.json python3 -I scripts/v9_eval/v9_fixed_eval.py   # d, f, f′, f″
THINKING=off WORKERS=25 SUBSET=$S COLLECTION=tam_chunks_dev_valid python3 -I scripts/v9_eval/v9_chunk_eval.py                                                          # a, b
C="--subset $S --n 1000 --prompt v5 --workers 10 --no-thinking"
python3 scripts/run_agent_search.py $C --kind B --graph --normalize-page-names     # i
python3 scripts/run_agent_search.py $C --kind B                                    # h
python3 scripts/run_agent_search.py $C                                             # g
```
Agent tự chọn collection theo split của câu hỏi (`data/text_corpus.index.json`). Chấm agent: `python3 -I scripts/v9_eval/v9_agent_score.py . <thư mục>`.

| Cấu hình | Thư mục `output/` |
|---|---|
| a, b | `20261117_173120` (1.108 lần gọi, 161 s) |
| d, f, f′, f″ | `20261117_173237` (2.216 mục, 289 s) |
| g (agent A) | `20261117_171410` |
| h (agent B) | `20261117_171410_3` |
| i (agent B + graph) | `20261117_171410_2` |

Lần đầu của a, b và d, f (`20261117_171516`, `20261117_171636`) chết ở bước ghi `run_meta.json` (đối tượng cấu hình không chuyển được sang JSON), chưa gọi LLM, bỏ. Kết quả và nhận xét: `docs/eval/12_V9_TUNE600_RESULTS.md` mục 5.

## 9. Chạy trên tập test_clean (2026-11-17, thinking tắt, 659 câu, một lần)

**Điều kiện.** Kho vector `tam_chunks_dev_test_clean` (5.682 chunk, 110 bù); graph Neo4j có thêm 186 trang test_clean (8.240 sự kiện; danh sách nút `local/ingest_eval/judge_out/graph_nodes_C.json`, ngoài git, nên sao lưu). Cấu hình giữ nguyên như mục 8, không chỉnh sau khi xem kết quả (tập giữ lại).

**Lệnh** (từ gốc repo, `S=dataset/eval/v9_graph_test_clean_subset.json`):
```
python3 scripts/make_v9_graph_subset.py --collection tam_chunks_dev_test_clean --out $S     # 659 câu, 173 trang
THINKING=off WORKERS=10 SUBSET=$S COLLECTION=tam_chunks_dev_test_clean NODES_FILE=local/ingest_eval/judge_out/graph_nodes_C.json python3 -I scripts/v9_eval/v9_fixed_eval.py   # d, f, f′, f″
THINKING=off WORKERS=10 SUBSET=$S COLLECTION=tam_chunks_dev_test_clean python3 -I scripts/v9_eval/v9_chunk_eval.py                                                          # a, b
C="--subset $S --n 1000 --prompt v5 --workers 10 --no-thinking"
python3 scripts/run_agent_search.py $C --kind B --graph --normalize-page-names     # i
python3 scripts/run_agent_search.py $C --kind B                                    # h
python3 scripts/run_agent_search.py $C                                             # g
```
Năm tiến trình chạy song song, 10 luồng mỗi tiến trình. Kiểm tra trước khi chạy (không gọi LLM): không trùng trang hay mã câu với tune và valid; mọi trang có gold; `DRY=1` cho hai script cố định.

| Cấu hình | Thư mục `output/` | Ghi chú |
|---|---|---|
| a, b | `20261117_175918` | 1.318 mục |
| d, f, f′, f″ | `20261117_180117` | 2.636 mục, 1.100 s với 10 luồng |
| g (agent A) | `20261117_175808_3` | thư mục tên `_3` là agent A trong lần này (thứ tự thư mục không cố định; nhận qua công cụ trong `run.log`: g `tool=grep`, h `tool=vector_search`, i có thêm `tool=timeline`) |
| h (agent B) | `20261117_175808_2` | |
| i (agent B + graph) | `20261117_175808` | |

Kết quả và so với tune, valid: `docs/eval/12_V9_TUNE600_RESULTS.md` mục 6.
