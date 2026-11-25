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
- Mỗi cấu hình một lần: thời gian LLM nhiễu theo giờ cao điểm (giá x2, 429); số lượt và token ổn định hơn. Không chạy lặp để đo nhiễu.
- Số Cơ chế 1 ở `eval/07` mục 6 và 7 (tháng 10) đo trước khi nạp bù chunk không mốc; không so thẳng với số mới.
- Prompt hai bước nạp và Profiler đã chỉnh trên `real` và `local` (tập đã xem nhiều), không phải `tune` (`eval/01` mục 11).

## 6. Quy tắc làm việc

- Không xóa `output/`; dừng tiến trình bằng PID; 429: chờ 40 giây, thử lại tối đa 8 lần; kiểm `llm_error` sau mỗi bước (script `run_test.sh` cũ chỉ bắt `error` và `max`).
- Mọi con số trong báo cáo phải đọc lại từ docs hoặc đếm lại từ dữ liệu.
- Người dùng tự commit, nhiều lô nhỏ, một dòng tiếng Anh `feat:`/`docs:`, không Co-Authored-By.

## 7. Việc còn lại trước khi chạy

1. Chốt prompt agent (`--prompt`).
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
- [ ] Chốt prompt agent (`--prompt`), giữ cho A1 đến A5: **tune `agent_m1`** (mục 10).
- [ ] Tune `answer_m1` cho 10 pipeline (mục 10).
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
- Cả hai viết từ tài liệu và prompt cũ, **chưa dựa trên phân tích lỗi của DeepSeek, chưa chạy lần nào**.

**Quy trình tune (chưa chạy):**
1. Tập cố định: `dataset/eval/tune50_subset.json` (50 câu đầu của mẫu `tune100`, seed 1, lấy từ `tune_base`, chứa 10 câu của lần thử) để sửa; `tune50b_subset.json` (50 câu còn lại, không giao) chỉ chạy một lần khi chốt. Không dùng `valid`, `test_clean`.
2. Hệ đại diện: pipeline P1 (dense) và P6 (Temporal); agent A2 (vector) và A4 (vector + `temporal_search`). Truy xuất không gọi LLM.
3. Vòng 1: chạy `m1` trên `tune50`, phân loại lỗi (từ chối dù có đáp án trong ngữ cảnh, sai mốc, dài dòng làm EM thấp, hết lượt, ít dùng công cụ). Vòng sau: sửa theo nhóm lỗi nhiều nhất, lưu bản cũ vào `archive/` (`answer_m1_v1.md`...). Khoảng 3 phiên bản mỗi loại.
4. Chốt: chạy bản tốt nhất và bản `m1` đầu trên `tune50b`, so ghép cặp; chỉ đổi khi hơn 2 sai số chuẩn (với 50 câu sai số chuẩn của Δ cỡ 0,05 đến 0,07, chưa đo). Chọn một prompt chung cho 10 pipeline và một cho 5 agent, rồi mới chạy `test_clean`.
5. Chi phí ước (giá thường, từ lần thử 5 câu, chưa đo lại): vòng 1 khoảng 0,5 đến 1 USD; giá DeepSeek giờ cao tải gấp đôi. Mỗi lần chạy lớn hỏi người dùng trước.

**Chưa kiểm:** `ingest_m2` (bản `p10b`) có đúng là bản nạp graph của cả ba tập không; `pair_m2` lấy từ `local/` (ngoài git) nên không so được với bản gốc trong git.
