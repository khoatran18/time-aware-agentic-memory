# Cơ chế 1: đo đầu-cuối bằng DeepSeek, so pipeline cố định với phương pháp agent (kế hoạch, ghi 2026-11-25)

**Trạng thái (2026-11-25):** B0 và B1 đã làm xong (mục 3); chưa chạy LLM nào. Bộ đo thời gian và cờ `--temporal-search` đã viết, chưa commit.

## 1. Đã chốt (người dùng)

- Cơ chế 1 **không dùng graph**; phần cần thêm là **phương pháp agent** (công cụ vector, text, và `temporal_search`; không có công cụ graph).
- Bộ đo: TimeQA `test_clean`, 400 câu (`dataset/eval/test_clean_subset.json`), mỗi cấu hình **một lần**, thinking tắt, cache riêng cho mỗi lần chạy.
- LLM sinh đáp án và agent: `opencode_deepseek_flash` (`deepseek-v4.1-flash`). Lý do: số cũ ở `eval/07` mục 7 dùng Gemini (top-15: 3.5; top-5: 3.1), agent dùng DeepSeek; khác LLM thì không tách được chênh lệch phương pháp với chênh lệch mô hình.
- Pipeline cố định lấy **top-5** chunk.
- **Ablation không đưa vào phép so** (bỏ điểm thời gian, `point`↔`range`, bỏ `end_mode`, bỏ decay); chỉ giữ số truy xuất đã đo ở `eval/07` mục 6.
- Đo **thời gian tách từng khâu** cho mỗi câu, và **token vào/ra/cache** cùng USD.
- Hỏi người dùng trước khi chạy loạt LLM lớn (ước số lần gọi và chi phí).
- Nạp kho (Gemini 3.5 flash-lite) **không** nạp lại; cả pipeline lẫn agent đọc cùng kho hiện tại. Ghi vào phần hạn chế.

## 2. Cấu hình cần đo

**Pipeline cố định, top-5, sinh đáp án bằng DeepSeek (10 cấu hình):**

| # | Cấu hình | Ghi chú |
|---|---|---|
| P1 | Plain RAG dense | `fac1ea4f53`; cũng là "Plain RAG" ở `eval/07` mục 7 |
| P2 | Plain RAG hybrid | `ff745f4228` |
| P3 | Plain dense + L6 | `1aede0eb77` |
| P4 | Plain dense + L12 | `4b996b0129` |
| P5 | Plain dense + bge-v2-m3 | `d78ac378fa`; "Plain RAG + bge" ở `eval/07` mục 7; cross-encoder nặng (chưa có số đo độ trễ) |
| P6 | Temporal, không cross-encoder | `6e55ff0d59` (`mrr` 0.516 khớp `eval/07`) |
| P7 | Temporal + L6 | `a5e602ff4e` (`mrr` 0.558) |
| P8 | Temporal + L12 | `b73bc37f8c` (`mrr` 0.563) |
| P9 | Temporal + bge-v2-m3 | `0a1b716ac7` (cấu hình chính cũ, `mrr` 0.620; "Temporal + bge" ở `eval/07` mục 7) |
| P10 | Temporal X | `2d10bbb571` (cấu hình chính hiện tại; tham số ở `scripts/run_agent_search.py` hằng `X_SETTINGS`); chưa nằm trong 28 cấu hình `test_clean` tháng 10 |

**Agent (5 cấu hình; `scripts/run_agent_search.py`):**

| # | Cấu hình | Công cụ | Cờ |
|---|---|---|---|
| A1 | Agent A | `list_pages`, `grep`, `read_page` | `--kind A` |
| A2 | Agent B | `vector_search`, `read_chunk` | `--kind B` |
| A3 | Agent C | A1 + A2 (không graph) | `--kind C` |
| A4 | Agent B + `temporal_search` | A2 + công cụ bọc nguyên Cơ chế 1 (cấu hình X) | cờ mới, cần nối |
| A5 | Agent C + `temporal_search` | A3 + công cụ trên | cờ mới, cần nối |
| (tùy chọn) | Agent B ẩn mốc | A2 với `--hide-time` | chỉ để chẩn đoán (agent dựa metadata hay văn bản) |

Đã có sẵn trong mã: `VectorTools.temporal_search` (`src/tam/tools/vector_tools.py`), nhưng `run_agent_search.py` đang truyền `retriever=None` nên công cụ chưa được bật.

## 3. Các bước

**B0. Kiểm điều kiện (không gọi LLM) — XONG 2026-11-25.**
- **Plain RAG ở `eval/07` mục 7 là dense** (`plain_dense` = `fac1ea4f53`; "Plain RAG + bge" = `d78ac378fa`; "Temporal + bge" = `0a1b716ac7`), theo `local/scripts/run_answers_test_k.sh`. Plan trước ghi "hybrid" là sai; P2 hybrid là cấu hình thêm.
- **Kho dựng bằng prompt `ingestion_time` v3** cho cả ba tập: `extractions.jsonl` ghi `prompt_version = v3` ở `output/20261021_230913` (test_clean, 5.681 dòng), `20261021_224334`/`230615` (valid, 5.062), `20261024_100929` (tune, 5.995). Lần chạy `real` tháng 10 đầu dùng prompt không ghi phiên bản (v1).
- **`eval/07` mục 6 chạy ở chế độ `e2e`, không phải oracle** (`local/scripts/run_replay.py` gọi `evaluate.py --mode e2e --profiler ... --extractions ...`; `metrics.json` ghi `mode: e2e`). Tức truy xuất dùng `t_req` do Profiler (Gemini 3.1, `output/20261024_143251/profiler.jsonl`) trích từ câu hỏi, và `top_k` của các lần chạy này là 15 hoặc 20 (sẽ ghi đè bằng `--top-k 5`). **Plan trước ghi "oracle" là sai**; sửa mục 5 bên dưới.
- **Cross-encoder bge/L12/L6 các lần chạy cũ chạy trên server GPU từ xa** (`TAM_RERANK_REMOTE_URL`, `local/results/rerank_remote.url`; điểm fp16, khóa cache `remote:<model>`), kèm cache điểm `data/model/reranker/score_cache.sqlite`. Với đo thời gian phải quyết: chạy cục bộ CPU (không cache điểm) hay GPU từ xa; ghi rõ lựa chọn vào kết quả. Chạy thử B1 cục bộ: `temporal_search` X mất 4,1 giây lần đầu (nạp model) và 2,2 giây lần sau trên CPU.
- Profile `opencode_deepseek_flash` đã có `extra_body.thinking.disabled` trong config; ghi vào log "thinking tắt".

**B1. Nối `temporal_search` vào agent — XONG 2026-11-25.** `scripts/run_agent_search.py` có cờ `--temporal-search` (kiểu B hoặc C): dựng `TemporalRetriever` cấu hình X (`X_SETTINGS`, cross-encoder `BAAI/bge-reranker-v2-m3-int8`, `rerank_score_cache` để trống để thời gian là thời gian chấm thật, `top_k` = trần `--k-cap`). `src/tam/tools/vector_tools.py` ghi log `temporal_search timings_ms=...` theo `query_id`. Đã thử không gọi LLM trên Qdrant thật: công cụ có mặt (`vector_search`, `temporal_search`, `read_chunk`); câu "trainer của 1. FC Köln" trả đúng chunk gold `#26` ở hạng 1. 307 test pass. Chưa chạy agent nào.

**B2. Chạy lại truy xuất trên kho hiện tại (không gọi LLM).** Kho nay có thêm chunk nạp bù không mốc (`test_clean` +110), nên không dùng lại `predictions.jsonl` của tháng 10. Chạy cho 10 cấu hình P1 đến P10 theo đúng cách `eval/07` mục 6 đã chạy (`--mode e2e --profiler output/20261024_143251/profiler.jsonl --extractions output/20261021_230913/extractions.jsonl`, qua `local/scripts/run_replay.py` với `REPLAY_CONFIGS` trỏ tới file cấu hình mới, hoặc gọi thẳng `scripts/evaluate.py`), đổi `--top-k 5`. Profiler đã chạy sẵn nên không gọi LLM. Mỗi dòng `predictions.jsonl` có `timings_ms` (embed, search, fuse_score, rerank, neighbors, total) nhờ bộ đo mới.

**B3. Sinh đáp án bằng DeepSeek, 10 cấu hình × 400 câu = 4.000 lần gọi.**
`scripts/generate_answers.py --profile opencode_deepseek_flash --batch 1 --top-k 5 --prompt v1 --rpm <cao> --workers 15 --cache-dir data/llm_cache/mech1_ds/<cấu hình> --label <cấu hình>`.
`--batch 1` bắt buộc để token và thời gian là của một câu; `--rpm` đặt cao vì mặc định 12 là hạn mức Gemini. Mỗi dòng `answers.jsonl` có `llm_wall_s`, `retrieval_ms`, và `llm_calls.jsonl` nối được theo `query_id`. Chi phí chưa ước lượng; tính từ số token ngữ cảnh top-5 trước khi hỏi.

**B4. Chạy agent A1 đến A5 trên 400 câu.** `scripts/run_agent_search.py --subset dataset/eval/test_clean_subset.json --collection tam_chunks_dev_test_clean --n 400 --no-thinking --workers 15 --cache-dir data/llm_cache/mech1_agent/<tên> [--kind ...]`. Prompt agent (`--prompt`) **chưa chốt** (các lần cũ dùng P2 hoặc P3, `planning/02` mục 11.11); chọn trước, giữ nguyên cho cả năm cấu hình. Ước tính theo `planning/02` mục 11.11: khoảng 0,02 đến 0,03 USD mỗi 20 câu ở kiểu B, nên khoảng 0,5 USD mỗi cấu hình 400 câu (số suy ra từ lần chạy cũ, chưa đo lại).

**B5. Chấm.** Cùng một bộ chấm cho cả hai nhóm: EM, F1, `contains`, từ chối (`src/tam/generation/scoring.py`). Với agent lấy dòng `Answer:` (`score_agent_runs.py`); thống nhất cách chuẩn hóa để không lệch giữa hai nhóm. Δ ghép cặp theo câu ± một sai số chuẩn.

**B6. Đo độ trễ riêng của cross-encoder.** L6, L12, bge: một luồng, máy rảnh (không chạy ingest, không chạy LLM nhiều luồng, Docker nhẹ), bỏ vài lần đầu (nạp model), báo p50 và p90 trên 400 câu; ghi CPU hay GPU, số luồng. Ước tính thời gian pipeline = truy xuất đo riêng + thời gian LLM (`e2e_net_s`, không tính chờ sau 429).

**B7. Tổng hợp.** Bảng một dòng mỗi cấu hình; ghi vào `docs/eval/` (file mới) và nối từ `decisions/README.md`.

## 4. Metric

1. **Chất lượng đáp án:** EM, F1, `contains`; tỉ lệ từ chối; "từ chối dù đã thấy đáp án" (`saw_answer_text` với agent).
2. **Rò rỉ tương lai:** tỉ lệ câu dựa vào chunk có `start_time > T_req`. Pipeline Cơ chế 1 chặn cứng; agent đo từ vết gọi công cụ.
3. **Hành vi agent:** có dùng `temporal_search`, `start_before` không; số lượt.
4. **Chi phí (báo riêng, không trộn vào điểm):** token vào/ra/cache, USD (0.15 / 0.003 / 0.60 USD mỗi triệu token vào / cache / ra), số lượt LLM, chi phí mỗi câu đúng.
5. **Thời gian mỗi câu, tách khâu:** embed, tìm, fuse/score, rerank, neighbors, LLM, tổng (pipeline); LLM, công cụ theo loại, tổng (agent). Hit@k và MRR chỉ cho pipeline, để đối chiếu phụ.

## 5. Hạn chế phải ghi khi báo cáo

- Pipeline dùng `T_req` do **Profiler** (Gemini 3.1 flash-lite) trích, chế độ `e2e`; agent tự trích `T_req` từ câu hỏi bằng DeepSeek. Hai bên có Profiler khác nhau; chưa có `T_req` thật của người hỏi để đo độ đúng (nhãn chỉ là khoảng hiệu lực của sự việc).
- Nhãn `time_start`/`time_end` là khoảng hiệu lực của sự việc đáp án, không phải mốc người hỏi nêu, càng không phải mốc của chunk (`dataset/full_dataset/README.md`).
- Kho nạp bằng Gemini 3.5 flash-lite; mốc chunk chỉ đo gián tiếp (`eval/01` mục 11: TH1 60,2%, TH2 26,8%, lọc cứng loại đáp án 7,2%, không mốc 5,8%).
- Chấm `contains` và EM là khớp chuỗi, sai khi đúng ý mà khác chữ.
- Nhãn của bộ dữ liệu có chỗ mơ hồ hoặc lệch (mục 11): EM thấp hơn mức hệ đúng ý thật; báo cả EM, F1 và `contains`, nêu rõ giới hạn khi so với số của bài khác.
- Mỗi cấu hình một lần: thời gian LLM nhiễu theo giờ cao điểm (giá x2, 429); số lượt và token ổn định hơn. Không chạy lặp để đo nhiễu.
- Số Cơ chế 1 ở `eval/07` mục 6 và 7 (tháng 10) đo trước khi nạp bù chunk không mốc; không so thẳng với số mới.
- Prompt hai bước nạp và Profiler đã chỉnh trên `real` và `local` (tập đã xem nhiều), không phải `tune` (`eval/01` mục 11).

## 6. Quy tắc làm việc

- Không xóa `output/`; dừng tiến trình bằng PID; 429: chờ 40 giây, thử lại tối đa 8 lần; kiểm `llm_error` sau mỗi bước (script `run_test.sh` cũ chỉ bắt `error` và `max`).
- Mọi con số trong báo cáo phải đọc lại từ docs hoặc đếm lại từ dữ liệu.
- Người dùng tự commit, nhiều lô nhỏ, một dòng tiếng Anh `feat:`/`docs:`, không Co-Authored-By.

## 7. Việc còn lại trước khi chạy

1. ~~Chốt prompt agent~~ đã xong: `m1_v4` (mục 13). Còn chốt định nghĩa A4, A5 (chế độ `temporal_search`, mục 13) và đồng bộ P6 đến P9 theo X.
2. Chọn nơi chạy cross-encoder cho phép đo thời gian (CPU cục bộ hay GPU từ xa).
3. B2 (không gọi LLM), rồi ước lượng số lần gọi và USD cho B3, B4 và hỏi người dùng.

## 8. Checklist (cập nhật 2026-11-25)

**Đã làm**
- [x] Chốt hướng: Cơ chế 1 không graph, thêm phương pháp agent; ablation không đưa vào phép so (`decisions/12`, mục 1 file này).
- [x] Bộ đo thời gian: `RetrievalTrace.timings_ms`, `BranchHits.embed_ms` (embed, search, fuse_score, rerank, neighbors, total) ở `TemporalRetriever`, `PlainRetriever`, `QdrantStore.search`, ghi vào `predictions.jsonl`.
- [x] `scripts/generate_answers.py`: `--cache-dir`, `llm_wall_s`, `retrieval_ms`, `query_context` (nối `llm_calls.jsonl`); mới kiểm cú pháp, chưa chạy.
- [x] B0: Plain RAG = dense; kho dựng bằng prompt v3; `eval/07` mục 6 chạy e2e; cross-encoder cũ chạy server GPU.
- [x] B1: `--temporal-search` (cấu hình X) trong `run_agent_search.py`; thử không gọi LLM đạt.
- [x] Docs: `eval/01` mục 11 (kho hiện tại, mốc so với `t_req`, cách chỉnh prompt), `eval/07` mục 6 (ghi chú trước nạp bù), `planning/02` mục 11.10 (lỗi thời), `decisions/README.md`, `decisions/10`, `12`, `16`.
- [x] Phát hiện: 386 chunk "thiếu" đã nạp bù 2026-11-17 (97 + 179 + 110); chunk không mốc ở `test_clean` là 16,5%.

**Cần làm**
- [x] Tune `agent_m1` và `answer_m1` trên `tune`, chốt `m1_v4` cho cả hai (mục 13); A1 đến A4 đã chạy trên 200 câu `tune` (mục 13).
- [ ] Chốt A4, A5 (`--temporal-mode`: `legacy` đã đo, `point`, `range`, `choice`) và đồng bộ P6 đến P9 theo X (`range`, `decay_from end`): hỏi người dùng.
- [ ] Thêm `judge_correct` (LLM giám khảo) cho TimeQA và nhóm câu giá trị của M3 (mục 11), kiểm bằng duyệt tay 50 câu.
- [ ] Đo `valid` rồi `test_clean` (không dùng hai tập này để chỉnh gì).
- [ ] Chốt nơi chạy cross-encoder khi đo thời gian (CPU cục bộ hay GPU từ xa). Lần thử 10 câu `tune` chạy CPU cục bộ, tắt cache điểm (`evaluate.py --no-score-cache`): rerank trung bình L6 khoảng 0,4 s, L12 0,6 s, bge 2,1 đến 2,9 s mỗi câu.
- [ ] B2: chạy lại truy xuất 10 cấu hình (e2e, `--top-k 5`) trên kho hiện tại, không gọi LLM; cần file cấu hình mới cho X và 9 cấu hình còn lại.
- [ ] Ước lượng số lần gọi và USD cho B3 (4.000 lần) và B4 (A1 đến A5), hỏi người dùng duyệt.
- [ ] B3: sinh đáp án bằng DeepSeek (`--batch 1`, thinking tắt, cache riêng).
- [ ] B4: chạy agent A1 đến A5 trên 400 câu.
- [ ] B5: chấm chung (EM, F1, `contains`, từ chối, rò rỉ tương lai); B6: đo độ trễ L6, L12, bge; B7: tổng hợp ra file `docs/eval/` mới.
- [ ] Sửa `eval/01` mục 7 (ghi chú các chỉ số "đúng năm nhãn", "phủ", "giao" chỉ là gián tiếp); ghi chú vào `planning/02` mục 11.10 nếu cần thêm.
- [ ] Kiểm vết agent của 166-q2, 093-q1, 125-q2 (Cơ chế 3, e′); viết tổng hợp ba tập cho luận văn.

## 9. Sao lưu trước khi restart Docker (2026-11-25)

Sao lưu **ngoài repo**, tại `~/backups_tam/2026-11-25/` (tức `/home/tmkhoa-1812/backups_tam/2026-11-25/`, khoảng 2,9 GB). Chép khi các container Qdrant và Neo4j đã dừng (để dữ liệu nhất quán), sau đó khởi động lại; `diff -rq` với Qdrant không lệch.

| Thư mục sao lưu | Nguồn gốc | Chứa gì |
|---|---|---|
| `qdrant_data/` | `docker/qdrant/qdrant_data` | mọi collection Qdrant (có `tam_chunks_dev_{tune,valid,test_clean}`) |
| `neo4j/`, `neo4j_m3/`, `neo4j_old/`, `neo4j_dr/` | `data/neo4j`, `data/neo4j_m3`, `data/neo4j_old`, `data/neo4j_dr` | `/data` của `tam-neo4j` (7687), `-m3` (7688), `-old` (7689), `-dr` (7690) |
| `judge_out/` | `local/ingest_eval/judge_out` | `graph_nodes*.json` (danh sách nút để dựng lại graph), log LLM; ngoài git |
| `llm_cache/` | `data/llm_cache` | cache LLM (ingest, agent, chấm...) |
| `extractions/<thư mục output>/` | `output/<thư mục>/*.jsonl` | `extractions.jsonl` (ingest tune `20261024_100929`, test_clean `20261021_230913`, valid `20261021_224334`, `20261021_230615`) và `profiler.jsonl` (tune `20261024_101330`, test_clean `20261024_143251`) |

**Lưu ý khi restart/dựng lại Docker**
- Dữ liệu Qdrant và Neo4j nằm ở thư mục máy chủ (bind mount) nên restart hay xóa container không làm mất. Không chạy `docker compose down -v` hay `docker volume prune` (volume `pgdata` của dự án Postgres khác nằm trong đó).
- `docker-compose.yml` trỏ Neo4j tới `./docker/neo4j/neo4j_data`, khác `data/neo4j` mà container hiện chạy: dựng lại bằng file này sẽ ra graph rỗng. Phải mount đúng `data/neo4j*`.
- Khôi phục: dừng container, chép thư mục tương ứng từ bản sao lưu về nguồn, khởi động lại. Chưa thử khôi phục thực tế.
- Nạp lại từ JSON (khi mất cả dữ liệu): chunk từ `dataset/full_dataset/pages.jsonl`, mốc từ `extractions.jsonl` (`scripts/ingest.py --recreate`, trúng cache `data/llm_cache/ingest*` nếu khóa còn khớp, chưa kiểm), 386 chunk không mốc bằng `local/ingest_eval/vec_fill.py`; graph bằng `local/ingest_eval/graph_build{,_V,_C}.py` từ `judge_out/graph_nodes*.json`. Chưa thử nạp lại thực tế.

## 10. Prompt Cơ chế 1 và kế hoạch tune (2026-11-25)

**Việc đã làm ngày 2026-11-25 (sau mục 8):**
- Thử 10 câu `tune` (`dataset/eval/tune10_subset.json`): truy xuất P1–P10 (top-5, e2e, `--no-score-cache`) chạy sạch; trả lời pipeline (DeepSeek, prompt cũ `answer_v1`, 5 câu, 50 lần gọi) sạch; agent A1–A5 (prompt cũ `agent_v3`, 5 câu) sạch: không `llm_error`, không lỗi công cụ, mọi câu dừng bằng `answer`; mỗi cấu hình agent khoảng 0,004 đến 0,006 USD (giá thường). Đây chỉ là kiểm lỗi, không phải kết quả.
- Đã bắt đầu rồi dừng (bằng PID) lần chạy 100 câu (`tune100`): truy xuất P1–P10 và agent A1–A5 với `agent_v3`; chưa lấy kết quả nào. `output/` giữ nguyên các thư mục chạy dở; cache `data/llm_cache/ds_agent_tune100_*_v3` giữ các lượt đã gọi.
- Thêm cờ `scripts/evaluate.py --no-score-cache` (tắt `rerank_score_cache` để đo thời gian rerank thật; `temporal_search` của agent đã tắt từ trước).
- Sao lưu dữ liệu Docker ra ngoài repo (mục 9).
- **Gom và đổi tên prompt** (chi tiết `src/tam/llm/prompts/README.md`): tên dạng `<vai trò>_<cơ chế>.md`, bản cũ vào `archive/`, lệnh cũ (`--prompt v5`, `--prompt-version v3`) vẫn chạy nhờ `ALIASES`. Các prompt nằm trong script đã tách ra file giống hệt nguyên văn (`ingest_m2`, `pair_m2`, `answer_m2`, `answer_m3`, `update_m3`); `answer_m2_chunk` vào `archive/` (chỉ là đối chứng). Tài liệu cũ khác (`process/04`, `05`, `07`, README của `query/`, `ingestion/`) còn nhắc tên cũ `ingestion_time_v1`, `time_extractor_v1`: đã ánh xạ ở `prompts/README.md`, chưa sửa từng chỗ.

**Prompt của Cơ chế 1 là riêng, viết mới (chốt 2026-11-25):** các prompt cũ `agent_v1..v4` là agent đối chứng (`planning/02`, không thuộc cơ chế nào) và `answer_v1..v4` viết, chọn cho Gemini; không dùng làm mốc so của Cơ chế 1.
- `answer_m1.md`: **sửa từ `archive/answer_v4.md`** (ghi khoảng hiệu lực chunk trong ngoặc, ba ví dụ giữ nguyên), thêm quy tắc "trạng thái giữ nguyên đến khi đoạn nói nó đổi" và tách "không đoán, không dùng kiến thức ngoài".
- `agent_m1.md`: **viết lại**, mượn ý từ `agent_v3`, `agent_v4` (nêu giá trị kèm mốc, mốc phủ một phần thì vẫn đưa giá trị, dừng khi hết thông tin mới); thêm "trả lời đúng mốc hỏi", `Answer:` là cụm ngắn nhất, bỏ dòng `Type:`. Không nêu tên công cụ nào.
- Hai bản này là `m1_v1` (nháp đầu); bản chốt là `m1_v4` (mục 13).

**Quy trình tune (đã chạy, kết quả mục 13; quy trình thực tế rộng hơn kế hoạch: thêm `tune100` và `tune100c`):**
1. Tập cố định: `dataset/eval/tune50_subset.json` (50 câu đầu của mẫu `tune100`, seed 1, lấy từ `tune_base`, chứa 10 câu của lần thử) để sửa; `tune50b_subset.json` (50 câu còn lại, không giao) chỉ chạy một lần khi chốt. Không dùng `valid`, `test_clean`.
2. Hệ đại diện: pipeline P1 (dense) và P6 (Temporal); agent A2 (vector) và A4 (vector + `temporal_search`). Truy xuất không gọi LLM.
3. Vòng 1: chạy `m1` trên `tune50`, phân loại lỗi (từ chối dù có đáp án trong ngữ cảnh, sai mốc, dài dòng làm EM thấp, hết lượt, ít dùng công cụ). Vòng sau: sửa theo nhóm lỗi nhiều nhất, lưu bản cũ vào `archive/` (`answer_m1_v1.md`...). Khoảng 3 phiên bản mỗi loại.
4. Chốt: chạy bản tốt nhất và bản `m1` đầu trên `tune50b`, so ghép cặp; chỉ đổi khi hơn 2 sai số chuẩn (với 50 câu sai số chuẩn của Δ cỡ 0,05 đến 0,07, chưa đo). Chọn một prompt chung cho 10 pipeline và một cho 5 agent, rồi mới chạy `test_clean`.
5. Chi phí ước (giá thường, từ lần thử 5 câu, chưa đo lại): vòng 1 khoảng 0,5 đến 1 USD; giá DeepSeek giờ cao tải gấp đôi. Mỗi lần chạy lớn hỏi người dùng trước.

**Chưa kiểm:** `ingest_m2` (bản `p10b`) có đúng là bản nạp graph của cả ba tập không; `pair_m2` lấy từ `local/` (ngoài git) nên không so được với bản gốc trong git.

## 11. Giới hạn của nhãn bộ dữ liệu (ghi 2026-11-25, từ lần tune prompt trên 200 câu)

Một phần câu "sai" ở mọi hệ không do hệ mà do nhãn. Đây là đặc điểm của bộ TimeQA, không phải lỗi riêng của hệ. Số liệu thực đếm được: tỉ lệ câu có nhiều hơn một đáp án vàng là 8,1% ở `tune` (48/595), 6,5% ở `valid` (26/399), 5,2% ở `test_clean` (21/400); trên `tune100`, 22 câu trong 100 cả bốn hệ P1, P6, A2, A4 (`m1_v4`) đều sai EM. **Chưa đo tỉ lệ nhãn mơ hồ trên cả tập** (mới đọc khoảng 25 câu agent sai và đối chiếu 22 câu cả bốn hệ cùng sai; chưa duyệt tay một mẫu có hệ thống).

**Các kiểu lệch nhãn, kèm ví dụ thật (câu hỏi rút gọn, "gold" là đáp án vàng):**

| Kiểu | Ví dụ | Hệ trả lời | Vấn đề |
|---|---|---|---|
| Đáp án cụ thể hơn hoặc tổng quát hơn nhãn | "What was end point of the Vindobona train between May 1972 and Aug 1983?" gold `Vienna` | `Wien Mitte` (A2), `Villach` (P6) | Đoạn nêu "In 1975, Wien Mitte station became the terminus"; `Wien Mitte` là ga cụ thể trong Vienna, đúng ý mà EM sai. |
| Cùng thực thể, viết khác | "…enjoyed which entity… (Andrew Mellon Building)" gold `Andrew Mellon`; "What was the MS Costa Allegra named in Aug 1990?" gold `Panalexandra` | `Andrew W. Mellon`; `Alexandra` | Đoạn có cả hai dạng; hệ chọn một dạng khác nhãn. |
| Gold nhiều giá trị, hệ chỉ nêu một (hoặc ngược lại) | "Spain's Martín de Gurrea y Aragón had which name of nobility…" gold `Duke of Villahermosa`, `Count of Ribagorza`; "…Line 15 terminus in Mar 2011?" gold `Wangjing West`, `Houshayu` | `Duke of Villahermosa`; `Wangjing West and Houshayu` | EM chỉ khớp khi đưa đúng một giá trị trong gold; liệt kê cả hai thì EM sai, `contains` đúng. |
| Cùng mốc có hai đáp án thật | "Talk im Turm was presented by whom in 1990?" gold `Heidi Schüller` | `Florian Fischer-Fabian` | Chunk ghi hai người cùng dẫn năm 1990 ("Florian Fischer-Fabian (1990) - Heidi Schüller (1990)"); gold chỉ nhận một. |
| Câu hỏi mơ hồ về loại thực thể | "The administrative center of what region was found in Vologda between…" gold `Vologda Governorate` / `Vologda Urban Okrug` / `Vologodsky District` tùy câu | `Vologda Oblast` ở cả bốn hệ | Cùng một thực thể trả lời khác nhau theo mốc, có câu chỉ một chunk không mốc nêu `Vologodsky District`. |
| Gold không phải một cụm đáp án | "What title did Fulk the Younger hold before Jun 1109?" gold `Fulk V became count of Anjou upon his fathers death in 1109` | `Count of Anjou` (P6) hoặc từ chối (A2) | Gold là cả câu; không hệ nào khớp được bằng EM. |
| Gold lệch loại câu hỏi | "Which military branch did Charles Lee (general) belong to before Feb 1755?" gold `Lee`; "Mary Raine was known by which family name in late 1900s?" gold `Thomas` | `British Army`; `Raine` | Nhãn không trả lời đúng câu hỏi hoặc mốc hỏi mơ hồ ("late 1900s"). |
| Chuẩn hóa ký tự | "Journal de 20 heures was presented by whom between Mar 1976 and Apr 1976?" gold `Patrick Poivre dArvor` | `Patrick Poivre d'Arvor` | Văn bản gốc đã bỏ dấu nháy; hệ khôi phục dấu nháy nên EM sai. |

**Hệ quả:**
- EM thấp hơn mức hệ thực sự đúng ý; ước tính thô trần thực tế của EM trên `tune100` là khoảng 0,78 (đúng ít nhất ở một trong bốn hệ), không phải 1,0. Đây là cận dưới của trần thật, chưa phải số đo chính xác.
- So sánh giữa các hệ cùng bộ câu vẫn công bằng (cùng nhãn), và so ghép cặp theo câu loại bỏ phần lớn tác động này.
- Khi báo cáo, in cả EM, F1, `contains`; khi so với số của bài khác, nêu rõ giới hạn nhãn và dùng cùng hàm chấm.
- Muốn có tỉ lệ chắc: duyệt tay một mẫu (đề xuất 50 câu mọi hệ đều sai trên `tune`), phân loại "nhãn mơ hồ", "đáp án khác vẫn đúng", "sai thật" và ghi tỉ lệ vào đây. Việc này không tốn lần gọi LLM.

### M2 và M3: có cần LLM giám khảo không (ghi 2026-11-25)

Đọc từ mã chấm hiện có; chưa so luật với giám khảo hay duyệt tay trên M2, M3.

| Bộ câu hỏi | Chấm bằng | Cách tính điểm | Cần LLM giám khảo? |
|---|---|---|---|
| M2 timeline v9 (`first_last_next`, `order_gap`, `list`, `summary`) | `scripts/v9_eval/v9_score.py`, không gọi LLM | Đáp án là danh sách mốc `{date, text}`; ghép mốc dự đoán với mốc chuẩn theo **ngày** (một bên chỉ có năm thì cần trùng năm), nhiều mốc cùng ngày thì chọn theo độ trùng từ khóa của `text`; tính precision, recall, F1, thứ tự, `exact` (đủ, không thừa, đúng thứ tự); `order_gap` là số năm, đúng khi bằng nhau | Không cần: khớp theo ngày nên ít lệch chữ. Điểm yếu nhỏ: ghép theo từ khóa khi nhiều mốc cùng ngày |
| M3 câu có/không (E current, E historical, F verify_false, C verify_false; khoảng 190 câu mỗi tập) | `scripts/m3_mech3_score.py` (dựa `validate_past_questions.match`), không gọi LLM | So cực tính yes/no ở đầu câu trả lời; câu từ chối ("cannot determine", "no passage...") tính sai | Không cần. Điểm yếu: không đòi nêu giá trị đúng ở `verify_false`; luôn trả "No" đúng 0,44 đến 0,51 tùy tập (valid 65/147, test_clean 76/148), nên phải báo cùng mốc này (`decisions/16`, chấm chặt đã có bảng) |
| M3 câu giá trị (A direct, direct2..4, F direct, C year; khoảng 130 câu mỗi tập) và E when | cùng `match` | Giá trị: phủ ≥70% từ của gold (so khớp chuỗi con, số "17" khớp "2017"); E when: đúng nếu năm kết thúc nằm trong câu trả lời | **Nên thêm giám khảo cho nhóm này**: khớp 70% từ bỏ lỡ cách viết khác (ví dụ `1993-12-13` so với `13 December 1993` bị tính sai, đã ghi ở `decisions/16`) và có thể chấp nhận câu chứa đáp án sai kèm đáp án đúng |

Kết luận: M2 và phần lớn M3 đủ bao quát bằng luật; chỉ nhóm câu giá trị của M3 (khoảng 40% số câu mech3) nên có LLM giám khảo bổ sung, dùng chung khung `judge_correct` đề xuất cho TimeQA, và kiểm giám khảo bằng duyệt tay một mẫu trước khi tin. Chưa làm.

## 12. Câu hỏi riêng của Cơ chế 3 (`mech3`): điểm theo phần trăm (ghi 2026-11-25)

Nguồn: `docs/decisions/16_MECH3_PAST_VERSION_DESIGN.md` (số câu đúng chia tổng số câu `mech3` của tập; luật chấm ở mục 11, phần "M2 và M3"). Không chạy lại. Tune dùng số đã sửa (qid dùng chung, luật từ chối). Cột: d, f, f′, f″ = bốn cấu hình truy xuất cố định (`decisions/16`); e′ = agent chỉ có công cụ graph; agent C = agent có văn bản, vector và graph. Dòng "luôn trả No" là mốc không cần hiểu gì (đúng khi gold là "No"). Cơ chế 3 = bản có lọc.

### tune (160 câu; luôn trả "No": 46%)

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---:|---:|---:|---:|---:|---:|
| Old | 39% | 39% | 32% | 30% | 42% | 98% |
| Window-replace | 81% | 83% | 59% | 55% | 78% | 98% |
| Diff-replace | 80% | 79% | 58% | 51% | 78% | 98% |
| Cơ chế 3 | 80% | 77% | 56% | 49% | 77% | 98% |

### valid (147 câu; luôn trả "No": 44%)

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---:|---:|---:|---:|---:|---:|
| Old | 37% | 35% | 26% | 21% | 45% | 95% |
| Window-replace | 78% | 76% | 51% | 44% | 82% | 97% |
| Diff-replace | 76% | 72% | 52% | 49% | 79% | 98% |
| Cơ chế 3 | 77% | 66% | 51% | 46% | 78% | 98% |

### test_clean (148 câu; luôn trả "No": 51%)

| Hệ | d | f | f′ | f″ | e′ | agent C |
|---|---:|---:|---:|---:|---:|---:|
| Old | 36% | 35% | 28% | 24% | 39% | 99% |
| Window-replace | 88% | 86% | 64% | 58% | 80% | 97% |
| Diff-replace | 89% | 84% | 65% | 59% | 82% | 99% |
| Cơ chế 3 | 87% | 84% | 61% | 59% | 79% | 99% |

**Đọc nhanh (test_clean):**
- Cấu hình cố định d và f: Cơ chế 3 (87%, 84%) ngang Window-replace (88%, 86%) và Diff-replace (89%, 84%), hơn Old (36%, 35%) khoảng 50 điểm. Old thấp hơn cả mốc "luôn trả No" (51%).
- f′ và f″ (58 đến 65%) chỉ nhỉnh hơn mốc "luôn trả No", nên ít đáng tin để so các hệ cập nhật.
- e′ (agent chỉ graph): Cơ chế 3 79%, Window-replace 80%, Diff-replace 82%, Old 39%.
- Agent C đạt 97 đến 99% ở cả bốn hệ, kể cả Old: không phân biệt được các hệ (agent đọc được văn bản và vector, không phụ thuộc graph).
- Theo tập: valid, test_clean Cơ chế 3 kém Window-replace 1 đến 5 điểm phần trăm (f ở valid kém 10 điểm); tune cũng cùng chiều.

## 13. Kết quả tune prompt và thí nghiệm công cụ thời gian (2026-11-25)

DeepSeek flash, thinking tắt, top-5, cache riêng mỗi lần chạy. Chỉ dùng tập `tune`: `tune50`, `tune50b`, `tune100` (= hai tập trước), `tune100c` (100 câu mới từ `tune`, không trùng `tune100`; 27 trang trùng). Hệ đại diện P1, P6, A2, A4; sai số chuẩn ghép cặp trên 100 câu khoảng 0,03, trên 200 câu khoảng 0,015 đến 0,02. Không dùng `valid`, `test_clean`.

**Các bản prompt (`archive/*_m1_v1..v6`):** v1 nháp đầu; v2 đối chiếu mốc và chỉ từ chối khi không đoạn nào nêu giá trị; v3 đáp án chỉ là tên thực thể (liệt kê hai đáp án nếu cùng đúng); **v4 = v3 với đúng một đáp án (chốt)**; v5 = v4 + quy tắc mốc + chép ký tự; v6 = v4 + chép ký tự.

**EM trên 100 câu `tune100`:**

| Hệ | v1 | v3 | v4 |
|---|---|---|---|
| P1 | 0,44 | 0,47 | 0,47 |
| P6 | 0,58 | 0,62 | 0,64 |
| A2 | 0,56 | 0,62 | **0,69** |
| A4 | 0,56 | 0,61 | **0,68** |

**Kiểm trên câu mới `tune100c` (EM, v1 → v4; chênh ghép cặp):** P1 0,38 → 0,39 (+0,01); P6 0,52 → 0,54 (+0,02); A2 0,53 → 0,61 (+0,08, z +2,2); A4 0,47 → 0,55 (+0,08, z +2,2). Mức tăng của agent giữ được (nhỏ hơn trên `tune100`); pipeline gần như không đổi.

**v4, v5, v6 trên 200 câu (EM):** P1 0,430 / 0,425 / 0,430; P6 0,590 / 0,615 / 0,605; A2 0,650 / 0,635 / 0,655; A4 0,615 / 0,630 / 0,630. Chênh v5 − v4 và v6 − v4 đều dưới 1,5 sai số chuẩn: dừng tune, giữ v4. Quy tắc mốc của v5 làm agent từ chối thêm; quy tắc chép ký tự của v6 sửa vài câu viết khác nhưng không đo được.

**Lỗi còn lại (v4):** khoảng 22 câu trong 100 mọi hệ đều sai, chủ yếu do nhãn mơ hồ hoặc lệch (mục 11). Agent thấy đoạn chứa đáp án vàng ở 192 đến 196/200 câu nhưng vẫn chốt sai hoặc từ chối ở khoảng 57 câu mỗi hệ; chỉ khoảng 4 câu tìm không ra. P1 từ chối 28%, phần lớn vì truy xuất không lấy đúng chunk (hit@5 khoảng 0,54).

**A1 đến A4 trên 200 câu (`m1_v4`):**

| Hệ | EM | F1 | contains | Từ chối | Lượt/câu |
|---|---|---|---|---|---|
| A1 (grep, `read_page`) | 0,595 | 0,671 | 0,655 | 0,12 | 3,54 |
| A2 (vector) | **0,650** | 0,719 | 0,695 | 0,07 | 2,63 |
| A3 (A1 + A2, không graph) | 0,610 | 0,681 | 0,670 | 0,10 | 3,10 |
| A4 (vector + `temporal_search` bản `legacy`) | 0,615 | 0,691 | 0,670 | 0,08 | 2,54 |

Chênh EM so với A2: A1 −0,055 (z −2,2), A3 −0,040 (z −1,8), A4 −0,035 (z −1,8). Thêm grep không giúp. A5 chưa chạy. Thời gian trong các lần này không dùng được (CPU quá tải khi chạy song song, load 74/16 nhân; xem "Đo độ trễ riêng" ở B5).

**`temporal_search` cho agent: point, range, choice (200 câu, `m1_v4`).** Bản `legacy` chỉ nhận một `t_req` do agent tự điền và hiểu ngày thiếu là **cuối** năm hoặc tháng; agent không biết `t_req` là đầu khoảng như Profiler, và thường chọn điểm giữa khoảng. Thêm cờ `--temporal-mode` (`vector_tools.py`: `parse_start_date`, ba mô tả công cụ):

| Biến thể | Mô tả cho agent | EM | F1 | Chênh EM so với A2 | Chênh so với `legacy` |
|---|---|---|---|---|---|
| A2 | (không có công cụ thời gian) | 0,650 | 0,719 | — | — |
| A4 `legacy` | một `t_req` (cuối kỳ), retriever range | 0,615 | 0,691 | −0,035 (z −1,8) | — |
| A4p `point` | `t_req` = đầu khoảng, retriever point | 0,640 | 0,713 | −0,010 (z −0,6) | +0,025 (z +1,4) |
| A4r `range` | `t_start`, `t_end` | 0,625 | 0,697 | −0,025 (z −1,4) | +0,010 |
| A4c `choice` | `t_req` + `t_end` tùy chọn, agent tự quyết | 0,635 | 0,710 | −0,015 (z −0,8) | +0,020 |

Không biến thể nào hơn A2. Báo cho agent biết `t_req` là đầu khoảng (point) thu hẹp khoảng cách còn −0,010; tất cả đều trong 2 sai số chuẩn nên không phân biệt được với nhiễu.

**Pipeline point so với range (200 câu, DeepSeek trả lời, EM; truy xuất trên `tune100` / `tune100c`: hit@5):**
- P6: point 0,590, range 0,605 (+0,015, z +1,1). hit@5: point 0,83 / 0,69, range 0,82 / 0,71.
- P10 (X): point 0,645, range 0,640 (−0,005, z −0,4). hit@5: point 0,86 / 0,77, range 0,87 / 0,80.
- Hai chế độ không phân biệt được (khớp `eval/09`: bge point so với range +0,008 ± 0,006 `mrr`).

**Không đồng bộ giữa P6 đến P10 và cấu hình chính:** P10 (X) là cấu hình chính đã chốt (`eval/07` mục 9: `range`, `decay_from end`). P6 đến P9 là các mức đợt tháng 10 mang tham số tối ưu riêng của họ (P6 `point`; P7 và P9 `decay_from start`). Đề xuất (chờ người dùng): bảng chính cho P6 đến P9 đồng bộ theo X (`range`, `end`), bảng đối chiếu giữ số tháng 10.

**Sự cố khi chạy song song (ghi để lần sau tránh):** 12 tiến trình cùng khởi động gửi khoảng 190 lần gọi mỗi phút và gặp 134 lần 429 trong 4 phút đầu (sau đó không còn). Mỗi tiến trình nạp cross-encoder bge và dùng hết số nhân, nên load lên 74 trên 16 nhân; hậu quả: `temporal_search` chậm (2 đến 6 giây), năm lượt kẹt đúng một yêu cầu HTTP khoảng 17 phút (dừng bằng PID và chạy lại cùng cache), một lượt lỗi Qdrant 408. Từ lần sau: tổng khoảng 20 luồng và giới hạn luồng cho cross-encoder (`OMP_NUM_THREADS`).

**Việc tiếp theo (chờ người dùng):**
1. Chốt A4, A5: tôi đề xuất bản `point` (đầu khoảng, báo trong mô tả công cụ), hoặc bỏ `temporal_search` khỏi tập so nếu muốn đơn giản; ghi kết quả "không hơn A2" như một phát hiện.
2. Đồng bộ P6 đến P9 theo X (3 cấu hình phụ P6, P7, P9, khoảng 1.200 lần gọi trên `test_clean`).
3. Đo `valid` rồi `test_clean`; đo độ trễ riêng một tiến trình.
4. `judge_correct` cho TimeQA và nhóm câu giá trị của M3 (mục 11).


## 14. Tổng hợp các cấu hình đã đo và chưa đo, giải thích A2 so với A4 (2026-11-25, đọc lại từ `output/`)

Mọi số: `tune` 200 câu (`tune100` + `tune100c`), `m1_v4`, DeepSeek flash, thinking tắt, top-5, EM.

**Pipeline (cấu hình trích từ `test_configs.json` và `probe_tune_configs_rest.json`).**

| # | `time_mode` | `decay_from` | `end_mode` | Cross-encoder | Đã đo e2e trên `tune`? |
|---|---|---|---|---|---|
| P1 | không có | không | không | không | có, EM 0,430 |
| P2 | không có | không | không | không (hybrid) | chưa |
| P3, P4, P5 | không có | không | không | L6 / L12 / bge (replace) | chưa |
| P6 | **point** | end | unknown_decay | không | point 0,590; range 0,605 |
| P7 | range | **start** | unknown_decay | L6 (mix) | chưa |
| P8 | range | end | unknown_decay | L12 (replace) | chưa |
| P9 | range | **start** | decay | bge (mix) | chưa |
| P10 (X) | range | end | unknown_decay | bge (replace) | range 0,640; point 0,645 |

Ghi chú: P6 đến P9 mang tham số tối ưu riêng của đợt tháng 10 nên không đồng bộ với X; đề xuất đồng bộ (`range`, `end`) vẫn chờ người dùng. Point so range ở P6 (+0,015, z +1,1) và P10 (−0,005, z −0,4) đều không phân biệt được.

**Agent (kind B: `vector_search`, `read_chunk`; A4 thêm `temporal_search`).**

| Hệ | Điền | Ngày thiếu là | Retriever | EM | So với A2 |
|---|---|---|---|---|---|
| A1 (grep, `read_page`) | – | – | – | 0,595 | −0,055 |
| A2 | – | – | – | **0,650** | – |
| A3 (A1+A2) | – | – | – | 0,610 | −0,040 |
| A4 `legacy` | `t_req` | cuối kỳ | range | 0,615 | −0,035 |
| A4 `point` | `t_req` = đầu khoảng | đầu kỳ | point | 0,640 | −0,010 |
| A4 `range` | `t_start`, `t_end` | đầu / cuối kỳ | range | 0,625 | −0,025 |
| A4 `choice` | `t_req` + `t_end` tùy chọn | đầu / cuối kỳ | range nếu có `t_end`, point nếu không | 0,635 | −0,015 |
| A5 | – | – | – | chưa chạy | – |

**Vì sao A2 không thua A4 một cách có ý nghĩa.** A2 và A4 point khác nhau ở 10/200 câu (A2 thắng 6, A4 thắng 4). Năm câu chỉ khác cách viết đáp án (Wangjing West and Houshayu; Ava (Inwa); CVG-82 dạng chữ; "Fellow of the Royal Society"; "GMMCH (...)"): A2 thắng 3, A4 thắng 2. Năm câu thật sự khác: A2 thắng 3 (Sarah Danzig, Novgorod, Frans Hals: A4 chỉ tìm một hoặc hai lần theo mốc đã điền, top-5 không chứa đáp án, nên chốt "cannot be determined" hoặc sai; A2 tìm lại bằng từ khóa cụ thể), A4 thắng 2 (Atlanta Dream, Mary Raine). Cả hai thấy đoạn vàng ở 196/200 câu (`gold_listed` 191 so với 187), nên truy xuất không phải điểm nghẽn. A2 hầu như không dùng `start_before` (0 trên 249 và 253 lượt gọi ở hai lần chạy v4 đã kiểm); prompt `agent_m1` không nhắc tới nó. Đây là suy luận từ 10 vết, chưa có thí nghiệm riêng.

**Chưa đo:** P2, P3, P4, P5, P7, P8, P9, A5 trên `tune`; mọi cấu hình trên `valid` và `test_clean`; độ trễ chính thức.

**Chốt (2026-11-25, người dùng):** `decay_from end` là mặc định trong `configs/config.dev.yaml` và `config.prod.yaml` (trước là `start`). Mặc định tham số hàm trong `scoring.py`, `retriever.py`, `evaluate.py` vẫn `start` (các bảng tháng 10 và P7, P9 dùng `start` khi ghi rõ trong cấu hình). Khi đồng bộ bảng chính, P6 đến P9 chạy `decay_from end` cùng `range`.

## 15. Chốt cấu hình thời gian (người dùng, 2026-11-25)

**Mọi thành phần có thời gian dùng `time_mode = range` và `decay_from = end`** (cấu hình X). Lý do: point và range không phân biệt được trên 200 câu `tune` (pipeline P6 +0,015 z +1,1; P10 −0,005 z −0,4; agent A4 point 0,640, range 0,625, choice 0,635, đều không hơn A2), nên chọn theo nguyên tắc: `range` chấm chồng lấn cả khoảng, phù hợp câu hỏi "between A and B", và X đã dùng range.

Đã sửa: `configs/config.dev.yaml` và `config.prod.yaml` (`time_mode: range`, `decay_from: end`); `scripts/run_agent_search.py` (`--temporal-mode` mặc định `range`). Mặc định tham số hàm trong `scoring.py`, `retriever.py`, `evaluate.py` giữ `start` và `point` để tái tạo được bảng tháng 10 (cấu hình ghi rõ trong tham số).

**Phải chạy P6 đến P9 theo X (`range`, `end`)** làm bảng chính: số P6 `point` và P7, P9 `start` ở trên chỉ là đối chiếu. A4 và A5 dùng bản `range` (`t_start`, `t_end`); các bản `legacy`, `point`, `choice` ghi làm đối chiếu.

**Trạng thái trên `tune` (200 câu, `m1_v4`), chỉ tính cấu hình `range` + `end`:**

| Hệ | Cấu hình | Đã đo | EM |
|---|---|---|---|
| P1 | dense | có | 0,430 |
| P2 | hybrid | chưa | – |
| P3 | dense + L6 | chưa | – |
| P4 | dense + L12 | chưa | – |
| P5 | dense + bge | chưa | – |
| P6 | Temporal, không CE (range, end) | có | 0,605 |
| P7 | Temporal + L6 (range, end) | chưa | – |
| P8 | Temporal + L12 (range, end) | chưa | – |
| P9 | Temporal + bge mix (range, end) | chưa | – |
| P10 (X) | Temporal + bge replace (range, end) | có | 0,640 |
| A1 | grep, `read_page` | có | 0,595 |
| A2 | `vector_search`, `read_chunk` | có | 0,650 |
| A3 | A1 + A2 | có | 0,610 |
| A4 | A2 + `temporal_search` (range) | có | 0,625 |
| A5 | A3 + `temporal_search` (range) | chưa | – |

Chưa có: `judge_correct`, độ trễ chính thức, `valid`, `test_clean`.

## 16. LLM judge `judge_correct` (thiết kế và thử, 2026-11-26)

**Model:** GLM-5.3 qua OpenCode Go (`opencode_glm_5_3`; khác họ DeepSeek). Gọi thử 2026-11-25: cần header `x-opencode-session` (như DeepSeek), trả `usage` đầy đủ; `reasoning_tokens` = 0 trên các lần thử (thinking tắt nhận được, mới thử vài prompt). Mỗi cặp (câu hỏi, đáp án) một lần gọi; cache riêng `data/llm_cache/judge_*`; `scripts/judge_answers.py` ghi `judgments.jsonl` kèm `llm_calls.jsonl`.

**Đầu vào:** câu hỏi (có mốc), danh sách đáp án vàng, các đoạn văn hệ có khi trả lời (pipeline: top-5; agent: các chunk thấy trong vết công cụ, tối đa 20), số thứ tự các đoạn hệ đã trích, đáp án hệ (dòng `Answer:`). Không đưa tên hệ.

**Đầu ra (schema `Judgment`):** `reason` (đặt đầu để suy luận trước), `verdict` (correct, partial, wrong, refusal), `match_type`, `matches_gold` (chỉ so với nhãn vàng, không phụ thuộc nhãn đúng hay sai), `gold_in_passages` (context recall), `relevant_passages` (danh sách số đoạn liên quan; context precision = độ dài / số đoạn), `grounded` (trung thực: một đoạn nêu đáp án, bất kể mốc; khác `verdict`, vốn xét đúng mốc), `hallucinated` (chỉ true khi tên, số, ngày của đáp án không xuất hiện trong đoạn nào; mã tính thêm `answer_in_passages` bằng so khớp chuỗi để đối chiếu), `answer_relevant`, `completeness`, `refusal_quality` (not_refusal, justified, borderline, unjustified), `citation_support`, `label_issue` (none, multi_gold, ambiguous, gold_not_an_answer, time_mismatch).

**Báo cáo:** điểm "nghiêm" = `matches_gold` (khớp nhãn, kể cả viết khác); điểm "rộng" = `verdict` correct (cộng `alternate_valid` mà judge thấy đoạn văn đỡ); luôn báo `label_issue` riêng và loại `gold_not_an_answer` khỏi điểm chính; từ chối báo theo `refusal_quality`.

**Phạm vi chấm:** câu EM sai và không từ chối (khoảng 55 đến 60 câu mỗi hệ trên `tune`), cộng mẫu 50 câu EM-đúng và 50 câu duyệt tay để kiểm; câu từ chối thì chấm `refusal_quality`. Khoảng 950 lần gọi cho 15 hệ trên 200 câu `tune`.

**Thử (6 vòng prompt, `archive/judge_m1_v1..v4.md` và bản hiện tại, 37 câu: 25 pipeline P6 range + 14 agent A2):** 37/37 parse được (sau khi cấm dấu nháy kép trong `reason` và cho thử 3 lần). Giữa hai bản cuối chỉ 3/37 câu đổi trường phụ, không đổi `verdict`. Những gì judge làm được: phân biệt viết khác ("Royal Swedish Academy of Sciences" so với "Swedish Academy of Sciences") với sai thật (Liga I so với Liga II; tên cũ SeaRiver Mediterranean); phát hiện nhãn lệch mốc (Atlanta Dream Dec 2017 ở McCamish Pavilion, Telekids 1991 là Irene Moors, Milan Line 3) và nhãn không phải đáp án (Diane Downs, Charles Lee, Fulk). Từ chối: 5 câu, 1 justified, 1 borderline, 3 unjustified (agent hoặc pipeline từ chối dù có đoạn nêu đáp án, khớp mục 13). `hallucinated` = false ở cả 37 (đáp án của hệ hầu như đều có trong đoạn văn).

**Chưa làm:** duyệt tay 50 câu để đo mức đồng ý giữa judge và người; chưa chạy judge trên các hệ; GLM-5.3 khác họ DeepSeek nhưng chưa có đo độ lệch; nhiễu của GLM giữa các lần gọi không đo (quy tắc không đo nhiễu); câu Sukandar ("represented" thay cho "won") vẫn bị gắn `unjustified` dù định nghĩa `borderline` đã nêu trường hợp này.

**Kiểm 50 câu (25 pipeline P10 range, 25 agent A2; tune100c; prompt chính):** đọc tay từng câu, so với EM, và kiểm các trường bằng so khớp chuỗi. Khớp EM: 10/10 câu EM-đúng đều `correct`, 12/12 câu sai hẳn đều `wrong`, 6/6 từ chối đúng; judge sửa thêm 13 câu viết khác và 9 câu nhãn lệch mốc (`alternate_valid`); bất đồng rõ với người đọc: 0; mơ hồ: khoảng 6. `gold_in_passages`: 47/50 trùng với so khớp chuỗi (1 câu khác nhờ suy luận nghĩa, 2 câu cùng không có). `grounded` và `hallucinated`: 41/44 trùng chuỗi, 3 câu khác là đáp án ghép hai phần ("X and Y") mà từng phần có trong đoạn văn; 0/44 bịa trong mẫu thật; thử độ nhạy bằng 6 đáp án bịa cố ý: 6/6 gắn `hallucinated` đúng. `citation_support`: tách khỏi `verdict` (11 câu sai vẫn `true` vì đoạn được trích có nêu đáp án nhưng cho mốc khác). Lỗi nhận thấy: `refusal_quality` gắn `unjustified` khi lý do ghi không đoạn nào nêu mốc (Veliky Novgorod); `label_issue` bỏ sót `ambiguous` (Fort Tilden, Milan Line 3); một câu (Monir Shahroudy, Cornell so với Tehran, Mar 1945) đổi `wrong` thành `correct` sau khi sửa trường `grounded`.

## 17. Quy tắc chạy đợt đo còn lại (người dùng chốt, 2026-11-26)

**Việc cần đo trên `tune` (200 câu = `tune100` + `tune100c`, `m1_v4`, top-5), chỉ cấu hình `time_mode = range`, `decay_from = end`:** pipeline P2, P3, P4, P5, P7, P8, P9 và agent A5 (`--kind C --temporal-search --temporal-mode range`); rồi chạy judge cho cả 15 hệ (P1 đến P10, A1 đến A5; A4 bản range). Không đụng `valid`, `test_clean`.

**Mô hình:** trả lời và agent dùng DeepSeek flash (`opencode_deepseek_flash`); judge dùng GLM-5.3 (`opencode_glm_5_3`, prompt `judge_m1.md`). Tất cả tắt thinking; cache riêng cho mỗi lần chạy (`data/llm_cache/<việc>_<biến thể>/`).

**Song song, không chờ hết bước này mới sang bước sau:** truy xuất, trả lời của pipeline, agent và judge chạy theo dây chuyền: cấu hình nào truy xuất xong thì gọi LLM trả lời ngay, trả lời xong thì chấm ngay; agent chạy cùng lúc với truy xuất.

**Tài nguyên:** CPU chỉ dùng tối đa 50% (8 trên 16 nhân): ghim bằng `taskset -c 0-7`, `OMP_NUM_THREADS` không quá 2 mỗi tiến trình, tối đa 4 tiến trình nặng CPU (truy xuất bge, agent có `temporal_search`); load trung bình không vượt khoảng 8. LLM: 20 luồng DeepSeek và 20 luồng GLM-5.3 (hai nhà cung cấp, tính riêng). Gặp 429 thì theo dõi bằng `llm_calls.jsonl`; nếu lặp lại thì giảm số luồng (dừng đúng PID, chạy lại cùng cache, ít luồng hơn); quy tắc cũ: chờ 40 giây, thử lại tối đa 8 lần.

**Ghi nhận:** mỗi lần chạy có log (`run.log`), cache, `llm_calls.jsonl` (token vào/ra/cache, thời gian, lỗi), `answers.jsonl` hoặc `results.jsonl` với thời gian truy xuất và LLM tách riêng; judge ghi `judgments.jsonl` kèm `llm_calls.jsonl`. Thời gian các lần chạy song song không dùng làm độ trễ chính thức.

**Tự giám sát:** đặt hẹn giờ 20 phút một lần (kiểm tiến trình còn sống, tiến độ, 429, lỗi, load CPU, có bị treo một yêu cầu quá 5 phút không; nghẽn thì sửa bằng cách dừng đúng PID và chạy lại cùng cache); chỉ tắt hẹn giờ khi đo xong và chấm xong tất cả.

**Kiểm tay judge:** `docs/eval/13_JUDGE_M1_CHECK_50.md` (50 câu, tôi kiểm: 35 đồng ý, 14 mơ hồ, 1 không đồng ý). Mức đồng ý với người chưa đo.

**Đã dừng giữa chừng ngày 2026-11-25 (chạy khi chưa được phép):** `output/20261125_2352*`, `20261125_2353*` là các lần truy xuất P2, P3, P4, P5, P7, P8 trên `tune100` (xong) và các lần trả lời, A5 dở dang; cache `data/llm_cache/ds_rest_*` dùng lại được. Không xóa.

## 18. Kế hoạch sau đợt đo 15 hệ (2026-11-26)

Đợt đo Cơ chế 1 trên `tune` 200 câu (15 hệ, range + `decay_from end`, DeepSeek flash trả lời, GLM-5.3 judge) đã xong. **Kết quả, cách tính, giải thích nhãn và đầu ra judge: `docs/eval/14_M1_TUNE_15_SYSTEMS.md`.** Mục này chỉ giữ việc còn lại:

1. **A1 (và A3) chưa chấm đúng bằng judge:** judge chỉ lấy passage từ kết quả `vector_search`/`temporal_search`; kết quả `grep`/`read_page` không có định dạng chunk nên A1 nhận 0 đoạn, A3 chỉ thấy phần vector. Việc: sửa `agent_passages` (đọc cả kết quả `grep` và `read_page`), chấm lại A1, A3 (~400 lần gọi GLM); cần người dùng đồng ý trước khi chạy.
2. **Mức đồng ý judge và người:** duyệt tay mẫu 50 câu mới (50 câu cũ đã dùng để chỉnh prompt).
3. **Token, thời gian, USD:** đo chính thức một tiến trình trên máy rảnh; chưa chốt CPU hay GPU; cần đơn giá để tính USD.
4. **`valid`, `test_clean`:** chỉ khi được bảo; thứ tự `valid` rồi `test_clean`.
5. Cập nhật tài liệu cũ: `process/04`, `05`, `07`, `eval/01` mục 7.

**Cập nhật chiều 2026-11-26:** đã đo nốt 395 câu `tune` còn lại (tổng 595, judge GLM đủ 595 câu), A1, A3 và A5 đã chấm lại sau khi sửa trích passage (mục 1 ở trên xong). Kết quả, chi phí, thời gian chia CPU/GPU, quy tắc giá OpenCode: `docs/eval/14_M1_TUNE_15_SYSTEMS.md` mục 7. Còn: mục 2 đến 5 ở trên. Khi chạy `valid`: DeepSeek tạm dừng ở khung giá ×2 (thứ 2 đến thứ 6, 08:00–11:00 và 13:00–17:00 giờ Việt Nam); GLM giá cố định; hạn mức tuần đã dùng 51%.

**Cập nhật 2026-11-28:** judge tune xong đủ 595 câu cho 15 hệ (A1, A3, A5 đã chấm lại). Chốt cho `valid`: đủ 15 hệ, DeepSeek qua OpenCode, judge GLM-5.3 qua Surplus (`surplus_glm_5_3`, ghim `dashscope-cn`, thinking tắt bằng `reasoning_effort: none`), cache local riêng, GPU Kaggle do người dùng đưa link. Chi tiết và số đo Surplus: `docs/eval/14_M1_TUNE_15_SYSTEMS.md` mục 7.8, 7.9.

**`valid` đã đo xong (2026-11-28, 02:19–06:12):** đủ 15 hệ trên 399 câu (pipeline 397 câu trả lời). Strict cao nhất: A4 0,679, A2 0,677, A5 0,672, P10 0,652, P9 0,647; thấp nhất P2 0,438, P1 0,476. EM không giảm so với `tune` nhưng judge strict giảm 0,01–0,07 và `hit@5` giảm 0,06–0,11; chưa tách được phần do judge (Surplus so với OpenCode) và phần do tập. DeepSeek 10.104 lần gọi (1,87 USD niêm yết, 429 thử lại 1.457 lần), GLM judge 5.995 lần gọi (giá thật ~0,02 USD; giá Surplus tính theo micro-USD). Kết quả, so cặp, token/cache/thời gian, sự cố (404 sàn giảm giá, hai agent treo): `docs/eval/15_M1_VALID_15_SYSTEMS.md`.

**`test_clean` đã đo xong (2026-11-28, 12:30–16:31, một lần, cấu hình đã khóa):** đủ 15 hệ trên 400 câu. Strict cao nhất: A4 0,695, A2/A3/A5 0,690, A1 0,677, P9 0,657, P10 0,655; thấp nhất P2 0,432, P1 0,482. Thứ tự các nhóm và EM giữ như `tune`, `valid` (EM chênh −0,04 đến +0,04 so với `tune`), chưa thấy overfit; strict gần `valid` (cùng judge Surplus) và thấp hơn `tune`. So cặp strict: P6−P1 +0,142 (z 6,25); P10−P6 +0,030 (z 1,81); A2−P10 +0,035 (z 1,84); A4−P10 +0,040 (z 2,15); `temporal_search` không giúp thêm. DeepSeek 9.990 lần gọi (1,87 USD niêm yết, 1.436 lần thử lại do 429, cache 57,3%), GLM judge 6.011 lần gọi (cache 57,8%, giá thật ~0,02 USD). Sự cố: hai agent treo (A5, A4 phần 4) dừng đúng PID và chạy lại từ cache; 11 lần 404 sàn giảm giá ở một việc judge; thử ghim Z.ai cho judge bị 404 (sàn 94%, offer tốt nhất 80%). Chi tiết: `docs/eval/16_M1_TEST_CLEAN_15_SYSTEMS.md`. Việc còn lại: judge–người, độ trễ chính thức trên máy rảnh, tách phần judge giữa hai nền tảng.
