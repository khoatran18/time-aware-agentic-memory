# Bản đồ dữ liệu (ai nằm ở đâu), cập nhật 2026-11-18

Ghi lại vị trí thật của từng loại dữ liệu, trạng thái git, và đề xuất chỗ đúng. Chưa di chuyển file nào (nhiều script còn trỏ đường dẫn cũ).

Ba tập trang: tune 203, valid 167, test_clean 186 (tổng 556). Chia tập: `dataset/eval/real_subset.json` và `data/text_corpus.index.json` (trường `split`); danh sách trang theo tập ở `local/ingest_eval/{tune,valid,test}_pages.txt`.

## 1. Hiện trạng

| Dữ liệu | Vị trí | Git |
|---|---|---|
| Văn bản gốc, toàn bộ TimeQA (4.815 trang) | `dataset/full_dataset/pages.jsonl` | tracked |
| Văn bản 556 trang đã chọn, mỗi trang một `.txt` | `data/text_corpus/` + `data/text_corpus.index.json` | ignored |
| Văn bản đã chia chunk, đầu vào ingest (`=== CHUNK <id> ===`) | `dataset/eval/timeline_pilot/batch*/in/<trang>.txt` (tune: batch2–9, B1–B11, batchN; valid: batchV*; test_clean: batchT) | tracked |
| Gold timeline (mốc vàng) theo trang | `dataset/eval/timeline_pilot/batch*/rev/<trang>.json` (+ `sub/`) | tracked |
| Nhãn thời gian chunk (cho vector) | payload Qdrant: `docker/qdrant/qdrant_data` (collection `tam_chunks_dev_tune`, `_valid`, `_test_clean`); kết quả LLM trong cache `data/llm_cache/` (`cache.sqlite`) và `output/<ngày_giờ>/extractions.jsonl` | ignored |
| Mốc ingest cho graph (prompt 10b) | `dataset/eval/timeline_pilot/outline_trial/out_p10b_ds_T` (tune 203), `_VN` (valid 167), `_TC` (test_clean 186); thử nghiệm: 80 thư mục `out_p*` khác | **untracked, không ignore** |
| LLM trả lời lần ingest (cache) | `data/llm_cache/ingest_nothink/` (thinking tắt); `ingest/` là thinking mặc định | ignored |
| Verdict so cặp (thô) | `local/ingest_eval/judge_out/graph_missing_{T,V,C}.json`; cache `data/llm_cache/judge_nothink/`; log gọi `llm_calls_graphmissing_*.jsonl` | ignored |
| Nút graph sau verdict, gộp, chặn (trước khi nạp) | `local/ingest_eval/judge_out/graph_nodes{,_V,_C}.json` | ignored |
| Graph Neo4j (Page, Event, Cell, Chunk) | `docker/neo4j/neo4j_data` (và `data/neo4j`) | ignored |
| Mã dựng graph | `local/ingest_eval/graph_build{,_T,_V,_C}.py`, `run_valid.sh`, `run_clean.sh`; thư viện: `src/tam/ingestion/events/{nodes,post}.py`, `src/tam/stores/graph` | `src` tracked, `local` ignored |
| Prompt ingest 10b | `dataset/eval/timeline_pilot/outline_trial/pass3_p10b.py`, `pass3_p10b_oc.py` | tracked / untracked |
| Câu hỏi Cơ chế 1 (case + đáp án) | `dataset/eval/{tune,valid,test_clean,real}_subset.json` (+ `*_cases.csv`); probe: `dataset/eval/capability_probe/` | tracked |
| Câu hỏi Cơ chế 2 (v9, timeline) | `dataset/eval/timeline_pilot/questions_v9/<trang>.jsonl` (553 file, 1.861 câu: tune 639, valid 557, test_clean 665); `extras/`, `derived_classify/` | tracked (bản làm việc ở `local/questions/v9/`) |
| Danh sách câu v9 dùng cho graph | `dataset/eval/v9_graph*_subset.json` | tracked |
| Kết quả chạy hỏi đáp | `dataset/eval/results_*.csv`, `local/results/`, cache `data/llm_cache/{reader,agent,chain,...}` | tracked / ignored |
| Model embedding, reranker | `data/model/` | ignored |

## 2. Vấn đề

1. **Mốc ingest 10b của cả ba tập (`out_p10b_ds_T/VN/TC`) nằm trong `dataset/` nhưng chưa vào git và không bị ignore**, lẫn với 80 thư mục thử nghiệm.
2. **Nút graph sau verdict chỉ có ở `local/` (ignored)** và Neo4j; dựng lại được từ ingest + cache `judge_nothink`, nhưng không có bản chính thức nào.
3. **Hai bản Neo4j** (`data/neo4j` và `docker/neo4j/neo4j_data`) khiến khó biết bản nào đang chạy; `docker-compose.yml` mount `docker/neo4j/neo4j_data`.
4. Nhãn thời gian cho vector không có bản xuất ra file; chỉ có trong Qdrant và cache.
5. Mã dựng graph nằm ở `local/ingest_eval/`, không được git theo dõi.
6. Cache `ingest/` và `ingest_nothink/`, `judge/` và `judge_nothink/` khác thinking, không được trộn khi so số liệu (xem CLAUDE.md).

## 3. Bản gom `dataset/organized/` (2026-11-18, chỉ copy, thư mục cũ giữ nguyên)

Tạo bằng `scripts/organize_data.py` (chạy lại được, ghi đè; xuất vector cần Qdrant chạy, `--no-vector` để bỏ). Mỗi nhóm chia theo ba tập `tune`, `valid`, `test_clean`; danh sách trang ở `pages_<tập>.txt` (203 / 167 / 186).

```
dataset/organized/                         (~55 MB)
  source/<tập>/text/                       văn bản gốc .txt
  source/<tập>/chunks/                     văn bản đã chia chunk (đầu vào ingest, "=== CHUNK <id> ===")
  vector/<tập>/chunks.jsonl                payload Qdrant mỗi chunk (nhãn thời gian), không có vector: 5.995 / 5.063 / 5.682 dòng
  timeline_gold/<tập>/<trang>.json         gold timeline (mốc vàng), độc lập với graph; đủ 203 / 167 / 186 trang; _derived_classify/ là phân loại ngày suy ra
  graph/<tập>/ingest_10b/<trang>.json      mốc ingest prompt 10b (thinking tắt)
  graph/<tập>/verdicts/<trang>.json        các cặp qua cổng: id, i, j, verdict (null = chưa có), nội dung hai mốc
  graph/<tập>/nodes/<trang>.json           nút graph sau verdict, gộp, chặn
  questions/mech1/<tập>/                   subset .json + cases .csv; mỗi case có `targets` (đáp án), thời gian, gold_chunk_ids
  questions/mech2/<tập>/<trang>.jsonl   câu v9; đã thêm `gold_events` (đáp án: id, date, text, track, phase) nối từ gold
  questions/mech1/_real/, _probe/          bộ real 400 câu; bộ kiểm khả năng (day, relative, no_anchor, open_end) và tune_base_subset
  questions/mech2/_subsets/, _extras/   v9_*graph*_subset.json; câu/mốc bổ sung của 5 trang
```

Số liệu cặp so (verdict): tune 2.993 cặp, thiếu 567; valid 1.787, thiếu 69; test_clean 1.910, thiếu 127.

Ghi chú tên: 3 trang tune có gold và câu v9 dưới tên cũ (pilot5/pilot10) khác tên trang trong batchN: `Regius_Professor_Civil_Law`, `Carl_Ehrensvard`, `Southern_Military_District` thành `Regius_Professor_of_Civil_Law_Oxford`, `Carl_August_Ehrensv_rd_1858_1944`, `Southern_Military_District_Milo_S`. Bản gom đổi tên file và trường `page` về tên sau (tên cũ ở `page_orig`). Số câu v9: tune 637, valid 554, test_clean 659 (1.850).

Chưa gom (vẫn ở chỗ cũ): 80 thư mục thử nghiệm `outline_trial/out_p*`, mã dựng graph ở `local/ingest_eval/`, `capability_probe/`, kết quả chạy, cache LLM, dữ liệu Neo4j và Qdrant thật. Script và tài liệu cũ vẫn trỏ đường dẫn cũ.

## Bản quá khứ mô phỏng cho Cơ chế 3 (thêm 2026-11-18)

`dataset/organized/past/<tập>/` (tune, valid, test_clean; chưa nạp kho nào): `edits.jsonl` (nhãn 200 chỗ sửa: C/E/F/A mỗi loại 50; `edits_v*.jsonl`, `edits_prev.jsonl` là bản lưu các lượt chạy), `chunks/<trang>.txt` (chunk bản cũ, id `<id>@past`), `metrics*.json`. Tune còn `questions_pilot*.jsonl` (câu hỏi thử và bản đã kiểm bằng LLM trả lời). `past/tune_prev2/` và `past/pilot_prev/` là bản cũ, không dùng. Sinh bằng `scripts/make_past.py` (`--redo`, `--swap`, `--accept`, `--from-current`), câu hỏi bằng `scripts/make_past_questions.py`, kiểm câu hỏi bằng `scripts/validate_past_questions.py`. **Câu hỏi Cơ chế 3 để chấm: `dataset/organized/questions/mech3/<tập>/questions.jsonl`** (tune 332, valid 309, test_clean 319 câu; bản cuối copy từ `past/<tập>/questions_vN.clean.jsonl`, N chỉ là số lần gộp, xem `dataset/organized/README.md`). Chi tiết và kết quả: `docs/decisions/16_MECH3_PAST_VERSION_DESIGN.md`. Cache LLM: `data/llm_cache/pastgen_hy4-flash-free/` (sinh bản cũ), `pastq_hy4-flash-free/` (câu hỏi), `pastv_hy4-flash-free/` (kiểm); thư mục `*_test/` là thử nghiệm.
