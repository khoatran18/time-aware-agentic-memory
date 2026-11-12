# Agent search làm đối chứng (đề xuất, chưa chốt)

Ghi ngày 2026-11-11. Tài liệu này là **đề xuất**: chưa có mã, chưa chạy gì. Nguồn ý tưởng: ghi chú cá nhân về agentic search (Mistral 2026-08-20, bài "Is Grep All You Need"), chưa phải tài liệu chính thức của đồ án. Các tuyên bố về hiệu quả của agentic search trong các nguồn đó chưa được kiểm chứng trên dữ liệu của đồ án.

## 1. Mục đích

Thêm một nhóm phương pháp mới vào bảng so sánh của phần nghiên cứu (`00_OVERALL_PLAN.md` mục 1.1): **agent tự tìm**, bên cạnh vector (k cố định, thích nghi), graph và "cả trang". Mục tiêu không phải chứng minh hướng nào hơn, mà là **giải thích được vì sao hơn hoặc kém** (nguyên nhân lỗi, chi phí).

## 2. Hai kiểu agent

Cả hai dùng **cùng một vòng lặp agent**, cùng mô hình, cùng system prompt, cùng trần số bước và token. **Biến duy nhất là bộ công cụ.** Agent tự làm mọi việc còn lại: đọc câu hỏi, đổi `T_now` thành `T_req` (system prompt có `T_now`), viết truy vấn, chọn công cụ, quyết định dừng.

| Kiểu | Công cụ | Kho | Câu hỏi nó trả lời |
|---|---|---|---|
| **A. Raw text** | `list_pages`, `grep(pattern, page?)`, `read_page(page, offset?)`; có thể thêm `bm25(query)` | Trang Wikipedia dạng text thuần, không chunk, không embed | Không cần index và graph thì được tới đâu, tốn bao nhiêu? |
| **B. Kho đã xây** | `vector_search` (xem dưới), tùy chọn `temporal_search` (bọc nguyên pipeline Cơ chế 1), `read_chunk(chunk_id)`, `timeline_lookup(page, track)` (khi graph có), các công cụ tính (khoảng cách, đếm, kế nhiệm) | VectorDB (Qdrant) và GraphDB | Agent dùng index và graph tốt hơn pipeline cố định không? |

**Quyết định (người dùng, 2026-11-11): B cung cấp đủ chức năng của pipeline dưới dạng tham số công cụ; có dùng hay không và dùng thế nào là do LLM quyết định.** Công cụ không áp bộ lọc mặc định.

`vector_search(query, mode, k, offset, start_before, include_invalidated)`:
- Agent chỉ đưa văn bản; việc embed câu hỏi và so sánh nằm trong công cụ.
- `mode`: `dense`, `bm25`, `hybrid`. `k`: số kết quả trả về, agent tự chọn, có trần cứng (đề xuất bằng `top_n` hiện có, 50; chưa chốt); `offset` để lấy trang tiếp.
- `start_before`, `include_invalidated`: bộ lọc **tùy chọn, mặc định không áp**; agent muốn lọc theo `T_req` thì tự truyền. Không có `start_after`: `VectorFilter` hiện chỉ có cận trên và `end_time` cố ý không được index; metadata đã trả kèm nên agent tự lọc cận dưới.
- Kết quả trả kèm metadata (`start_time`, `end_time`, `end_status`, `invalidated_at`, `chunk_id`).
- Cài đặt: gọi thẳng tầng dưới (`VectorStore.search` với `VectorFilter`, `fuse`, cắt `[offset : offset+k]`), không bọc retriever. Không lọc = `VectorFilter(apply_time=False, exclude_invalidated=False)`, như `PlainRetriever`.

`temporal_search(query, t_req, k)`: nguyên pipeline Cơ chế 1 (lọc cứng, RRF, `W1·Sem + W2·Temp`) như một công cụ riêng, để agent chọn giữa tìm thô và tìm có chấm thời gian. Bọc `TemporalRetriever` một lần với cấu hình chính cố định, dựng với `top_k` bằng trần rồi cắt xuống `k` của agent (tương đương, vì `top_k` chỉ cắt sau khi đã xếp hạng).

`read_chunk(chunk_id, neighbors=0..n)`: `get_chunks` và `neighbor_ids`. Thay cho tham số `neighbors` cố định: agent mở rộng khi cần.

**Rerank (cross-encoder) không để agent chọn.** Nó kéo thêm model (fastembed) và là cải thiện lớn nhất đã đo ở pipeline cố định (`docs/instruction/02`). Nếu dùng, là cờ bật hoặc tắt trong cấu hình harness, để kết quả còn giải thích được.

**Mô tả công cụ và system prompt phải trung tính** (không dặn "nhớ lọc theo ngày"), và được coi là phần cố định của harness; nếu không, thiết kế đã bị nhúng vào agent và phép so mất ý nghĩa.

Hệ quả:
- Các lựa chọn của agent trở thành **đại lượng quan sát được** từ vết: `k` chọn bao nhiêu, có truyền bộ lọc không, dùng `vector_search` hay `temporal_search`. Đối chiếu với `k` và cấu hình đã tune cho pipeline cố định.
- "Không rò rỉ tương lai" không còn là bảo đảm của công cụ mà là **đại lượng đo** từ vết (agent đọc chunk có `start_time > T_req` bao nhiêu lần, và bao nhiêu lần chunk đó vào đáp án). Đặt cạnh `leakage_rate` 0% của pipeline cố định.
- Sai số `start`/`end` do LLM gán lúc ingest (không tránh được) chỉ còn tác động gián tiếp: agent có thể tin metadata sai.
- A cũng không có bảo đảm cứng (trang chứa cả sự kiện sau `T_req`), nên A và B nhất quán ở điểm này.

## 3. Biến thể đối chứng (để cô lập nguyên nhân)

| Biến thể | So với | Cô lập được |
|---|---|---|
| B có metadata thời gian / B ẩn metadata thời gian | nhau | agent dựa vào metadata hay vào văn bản |
| B với mốc LLM gán / B với mốc oracle (từ gold) | nhau | cái giá của sai số gán mốc ở ingest |
| B có công cụ tính / không có | nhau | lợi thế của phép tính bằng code (decisions/10) |
| A đọc cả trang / A cắt trang theo `T_req` | nhau | tác động của việc thấy tương lai |
| A, B, pipeline cố định, vector top-k, "cả trang" | nhau | agent so với pipeline cố định (Profiler và Router do agent tự làm) |

Chưa chốt biến thể nào thật sự chạy; mỗi biến thể là một lần chạy tốn API.

## 4. Vết và phân loại lỗi

Mỗi câu hỏi, mỗi biến thể ghi một vết (JSONL): các lượt gọi công cụ (tên, tham số, các `chunk_id` hoặc vị trí trả về), các chunk agent đã đọc, đáp án và bằng chứng nêu ra, số lượt LLM, token vào và ra, độ trễ. Mỗi câu sai được gán vào đúng một nhóm:

| Nhóm | Điều kiện |
|---|---|
| Không tìm thấy | chunk hoặc sự kiện gold chưa từng xuất hiện trong kết quả công cụ |
| Tìm thấy nhưng không dùng | có trong kết quả công cụ nhưng không có trong đáp án |
| Hiểu sai thời gian | dùng sự kiện ngoài khung `T_req`, hoặc loại sự kiện đúng khung |
| Suy luận sai | đủ bằng chứng nhưng sai thứ tự, khoảng cách, số đếm |
| Cạn ngân sách | chạm trần bước hoặc token trước khi dừng |

Cách chấm đáp án cuối không bàn ở đây (đã có `score_answer` trong `src/tam/evaluation/metrics_timeline.py`, người dùng sẽ quyết sau).

## 5. Chi phí là một trục riêng

Mỗi phương pháp báo cáo cặp (độ đúng, chi phí), không gộp thành một điểm: số lượt LLM, token vào và ra, số lần gọi công cụ, độ trễ, tiền. Agent có thể đúng hơn nhưng đắt hơn; đó là kết quả hợp lệ. Cần tính **điểm hòa vốn**: số truy vấn để chi phí trích của graph rẻ hơn chi phí mỗi truy vấn của agent. Cần trần bước và token để một lần lặp vô ích không làm lệch chi phí trung bình. Agent không tất định nên cần chạy lặp vài lần trên tập con để biết độ nhiễu.

## 6. Hiện trạng mã (đã đọc 2026-11-11)

| Cần | Hiện có | Còn thiếu |
|---|---|---|
| Gọi LLM, chọn nhà cung cấp | `tam.llm` (`get_llm_for_role`); `BaseChatModel` của langchain nên dùng được `bind_tools` | role `agent` trong `configs/*.yaml` |
| Đo token, độ trễ mỗi lượt | `tam/llm/metrics.py` ghi `llm_calls.jsonl` theo `query_id`, kể cả token trúng cache | gắn vết công cụ vào cùng `query_id` |
| Chunk và metadata | `tam.schemas.Chunk` (`chunk_id`, `doc_id`, `start_time`, `end_time`, `end_status`, `invalidated_at`) | |
| Vector search | `VectorStore.search(query_text, flt, top_n)` (embed, dense và BM25, `VectorFilter` đặt được mỗi lần gọi), `fuse`, `get_chunks`, `neighbor_ids`, `Reranker.score` (đã đọc 2026-11-11) | `TemporalRetriever` và `PlainRetriever` cố định `top_k`, `top_n`, `neighbor_window`, `reranker` ở constructor và `retrieve()` chỉ nhận `ProfiledQuery`, nên **không bọc trực tiếp** cho `vector_search`; gọi tầng dưới (mục 2). `temporal_search` bọc được một lần |
| Chấm và độ phủ | `event_coverage`, `score_answer` | đối chiếu `chunk_ids` trong vết với gold |
| Graph, `tools/`, `agents/` | **Chưa có** (kế hoạch ở `00_OVERALL_PLAN.md` mục 3 nhưng thư mục chưa tạo) | toàn bộ phần B có graph |
| Kho text cho A | chưa kiểm | tìm nguồn trang text trong `dataset/full_dataset/` |

## 7. MCP hay hàm Python

Mặc định: **hàm Python thường** trong `src/tam/tools/`, đủ cho thí nghiệm và dễ tái lập. MCP chỉ cần nếu muốn dùng harness ngoài (ví dụ Claude Code) làm agent, hoặc nếu phần chatbot sau này phơi công cụ ra ngoài; khi đó là lớp bọc mỏng quanh cùng các hàm. Chưa chốt; xem `docs/research/knowledge_representation_and_integration/05_MCP_and_Agent_Tooling.md` và `12_...` (chưa đọc kỹ khi viết file này).

## 8. Việc cần làm

**Người dùng dặn 2026-11-12: chưa ingest. Hóa ra không cần ingest vì kho vector cho 556 trang đã có (mục 1 bên dưới).**

1. ~~Dựng kho B~~ **Không cần ingest (đính chính 2026-11-12):** Qdrant đang chạy (`localhost:6333`) và đã có đủ kho cho 556 trang: `tam_chunks_dev_tune` (5.898 điểm, 203 trang), `tam_chunks_dev_valid` (4.884, 166 trang), `tam_chunks_dev_test_clean` (5.572, 186 trang). Gộp 16.354 chunk, 555/556 trang của kho text (đối chiếu `chunk_id` với `data/text_corpus.index.json`; thiếu 1 trang). Kho text có 16.740 đoạn, nên kho vector ít hơn 386 chunk (nguyên nhân chưa kiểm chứng; có thể chunk không gán được mốc, `chunk_id` trùng, hoặc 1 trang thiếu). Ghi chú cũ "kho chỉ có 204 trang" chỉ đúng với bộ `real` (`eval/05`). Việc còn lại: viết kiểu B trong `run_agent_search.py` trỏ vào ba collection này (chọn collection theo split của câu hỏi), và xác định 386 chunk thiếu.
2. ~~Viết `scripts/run_agent_search.py`~~ **Đã xong** (kiểu A; kiểu B đã nối và chạy 40 câu P2/P3, mục 11.10 và 11.11). Có `--prompt`, `--no-budget-notice`, `--pick`, `--workers`, `--max-steps` (mặc định 5).
3. ~~Chạy thử 1 câu rồi 20 câu~~ **Đã xong** (mục 10.2, 11.2 đến 11.4). Chạy cả loạt lớn hơn thì hỏi người dùng trước.
4. Chốt trần `k` (đề xuất 50), trần token (200k, đề xuất, chưa có căn cứ đo), biến thể nào thật sự chạy (mục 3), MCP hay hàm Python (mặc định hàm Python). **Đã chốt (người dùng, 2026-11-12): tối đa 5 lần gọi LLM mỗi câu** (trước đó là 10; xem 11.1, 11.5).
5. Công cụ graph (`timeline_lookup`, công cụ tính) khi Cơ chế 2 có đồ thị.
6. Phân loại lỗi (mục 4) từ log: đối chiếu `chunk_ids` trong `agent_trace.jsonl` với chunk gold bằng `event_coverage`; tổng hợp p50/p90/p99 TTFT, E2E, token, chi phí, điểm hòa vốn (mục 5).
7. Phát triển trên tune; `test_clean` chỉ chạy một lần khi chốt.
8. **Việc mới ghi 2026-11-12 (chưa làm):**
   - ~~Sửa `saw_gold_chunk` thành kiểm chuỗi~~ **Đã xong 2026-11-12 (mục 11.8):** kiểm chuỗi đáp án trong **văn bản** công cụ trả về (không phải danh sách `chunk_ids`), và ghi thêm lượt đầu tiên thấy đáp án (mục 11.5).
   - Viết script chấm theo mục 13 (so khớp thô, LLM judge khác mô hình đang đánh giá, kiểm tay một mẫu, gán nguyên nhân lỗi).
   - Lặp mỗi biến thể (P0 trần 5, P2, P3) 3 lần trên 20 câu để đo dao động giữa các lần chạy, rồi mới so (mục 11.4); sau đó mở rộng 60 đến 100 câu cho biến thể thắng.
   - Quyết định chọn P2 hay P3 làm mặc định; chạy P0 với trần 5 và báo lượt (`budget_notice`) để tách ảnh hưởng của cơ chế dừng khỏi prompt.
   - Còn lại như cũ: dựng kho B (hỏi trước), mốc chung với pipeline qua `Answerer` (mục 12), công cụ graph.

## 9. Rủi ro

- Trang TimeQA ngắn (trung vị 1.213 từ theo ghi chú), nên "cả trang" và A có thể mạnh về độ phủ; lợi thế của graph khi đó chủ yếu ở token, phép tính và chi phí cập nhật, cần số liệu riêng cho các điểm này.
- Kết quả agent phụ thuộc mạnh vào mô hình và harness (nguồn ngoài báo chênh khoảng 10 điểm chỉ do đổi harness); phải cố định cả hai khi so sánh.

## 10. Đã làm (2026-11-12, không gọi LLM)

| Phần | File | Ghi chú |
|---|---|---|
| Kho text cho A | `scripts/build_text_corpus.py` → `data/text_corpus/` (556 file, 7.5 MB, gitignore) | đúng 556 trang của tune, valid và test_clean (203 + 167 + 186, không giao nhau); mỗi đoạn `[#i]` + đúng văn bản chunk của ingestion nên khớp `chunk_id`; không có nhãn thời gian; bảng ánh xạ ở `data/text_corpus.index.json` (ngoài thư mục corpus) |
| Công cụ A | `src/tam/tools/text_corpus.py`, `text_tools.py` | `list_pages`, `grep` (regex, phân trang), `read_page` (cắt ở ranh giới đoạn); trần cứng số kết quả và ký tự |
| Công cụ B | `src/tam/tools/vector_tools.py` | `vector_search`, `temporal_search`, `read_chunk`, đúng đặc tả mục 2; `show_time=False` là biến thể ẩn metadata; trên kho giả |
| Hợp đồng công cụ | `src/tam/tools/base.py` | `AgentTool` (schema OpenAI function từ pydantic), `ToolResult`, `ToolError` |
| Vòng lặp agent | `src/tam/agents/loop.py`, prompt `src/tam/llm/prompts/agent_v1.md` | `bind_tools`, trần `max_steps` và `max_total_tokens`, lỗi công cụ trả lại cho agent, lỗi LLM thành `stop_reason`; vết JSONL (`llm`, `tool`, `end`); không LangGraph; prompt trung tính (có test canh) |
| Test | `tests/test_text_corpus.py` (17), `test_vector_tools.py` (11), `test_agent_loop.py` (9, nay 15; mục 10.1) | LLM giả có kịch bản; toàn bộ 266 test (trừ `qdrant`) qua |

**Chưa kiểm:** chưa có lần chạy nào với LLM thật nên chưa biết `bind_tools` với dạng schema này chạy đúng ở từng nhà cung cấp (Anthropic, OpenAI, Gemini); `TemporalRetriever` chỉ thử trên kho giả, chưa trên Qdrant thật; `grep` chưa có timeout cho regex bùng nổ (chỉ chặn độ dài pattern 200 ký tự); ngân sách token tính theo `usage_metadata` nên bằng 0 nếu nhà cung cấp không trả; vòng lặp gọi tuần tự các lời gọi công cụ song song.

### 10.1. Ghi log và đo (2026-11-12, không gọi LLM)

| Phần | Nơi | Ghi chú |
|---|---|---|
| Log từng lần gọi LLM: prompt, câu trả lời, số đo | `agent_calls.jsonl` (thư mục lần chạy `get_run_dir()` sau `setup_logging()`, hoặc `calls_path`) | mỗi lần gọi một dòng: toàn bộ tin nhắn đã gửi, câu trả lời (chữ, lời gọi công cụ, chuỗi suy luận nếu có), model, số đo, lỗi nếu có. `log_prompts="delta"` chỉ ghi tin nhắn mới (prompt đầy đủ dựng lại được; mỗi lượt lặp lại cả lịch sử nên `full` phình theo bình phương số lượt: chưa đo cỡ file thật); `"off"` tắt |
| Vết nhẹ | `agent_trace.jsonl` | `llm` (token vào/ra/cache, TTFT, TPOT, tokens/s, E2E, số lời gọi công cụ), `tool` (tên, tham số, chunk lộ ra, lỗi, số ký tự, thời gian), `end` (lý do dừng, tổng token, thời gian LLM, thời gian công cụ, wall, đáp án) |
| Số đo | `tam/llm/metrics.py::stream_collect` | TTFT = t(chunk đầu ra đầu tiên) - t_gửi (lượt chỉ gọi công cụ cũng tính, kể cả chuỗi suy luận); TPOT = (t_cuối - t_đầu) / (token ra - 1); tokens/s; E2E; token vào, ra, cache (`input_token_details.cache_read`); `tokens_exact` nói số token ra lấy từ `usage` hay đếm chunk. `measure_stream` tái dùng cùng hàm |
| `logger` | `tam.config.logging` | mỗi lượt LLM, mỗi lời gọi công cụ và lúc kết thúc ghi một dòng INFO kèm `query_id`; `llm_calls.jsonl` (callback) vẫn ghi E2E, token, lỗi 429 mỗi lần gọi thật và nối được qua `query_id` |
| Tổng hợp mỗi câu | `AgentRun` | `llm_time_s`, `tool_time_s`, `wall_s`, `ttft_s` (từng lượt), token vào/ra/cache; tách thời gian LLM với công cụ như `local/ai_projects_review/05` mục 0 |
| Role `agent` | `configs/config.dev.yaml` `llm.roles.agent: opencode_deepseek_flash` | không đổi `config.prod.yaml` (profile ở đó chỉ có Claude) |
| `stream_usage` | profile `openai`, đặt `true` cho `opencode_deepseek_flash` | langchain-openai mặc định **tắt** `usage` khi streaming với `base_url` tùy chỉnh (đã kiểm: `_should_stream_usage()` là False), khi đó token vào/ra rỗng và trần token không có tác dụng |
| Test | `tests/test_agent_loop.py` (15 test), `test_llm_factory.py` (thêm 1) | LLM giả streaming nhiều chunk thử TTFT/TPOT, tool call ghép từ chunk, log prompt đầy đủ và delta, lỗi LLM có prompt, đường dẫn mặc định từ thư mục lần chạy |

**Đã kiểm không cần mạng:** role `agent` dựng được `ChatOpenAI` (`deepseek-v4.1-flash`, `base_url` OpenCode, có callback `LlmMetrics`); `bind_tools` nhận ba schema công cụ; payload yêu cầu có `tools` và `stream_options.include_usage`.

**Chưa kiểm chứng (cần một lần gọi thật):** OpenCode có chuyển tiếp `tools` và `stream_options` cho DeepSeek không (lỗi thì đặt `stream_usage: false` và chạy `stream=False`, khi đó mất TTFT và TPOT); DeepSeek bật thinking mặc định và API của nó đòi gửi lại `reasoning_content` ở các lượt gọi công cụ, trong khi `ChatOpenAI` không gửi lại trường này (nguy cơ lỗi hoặc giảm chất lượng; cách xử lý: tắt thinking bằng `extra_body` như profile `deepseek_flash`, chưa thử); TTFT qua proxy gồm cả hàng đợi và mạng; kích thước `agent_calls.jsonl` ở chế độ `full`.

### 10.2. Lần chạy thử với LLM thật (2026-11-12): kiểu A, 20 câu

Cấu hình: role `agent` = `opencode_deepseek_flash` (OpenCode Go), kho text 556 trang, 20 câu ngẫu nhiên (seed 1) của `dataset/eval/tune_base_subset.json` (`question_hard`), `T_now` = 2026-11-03, trần cũ 12 lượt LLM mỗi câu (đã đổi thành 10, xem mục 8), tuần tự, streaming. Log: `output/20261112_115710/` (`results.jsonl`, `agent_trace.jsonl`, `agent_calls.jsonl` 1,2 MB cho 20 câu, `llm_calls.jsonl`). Một câu thử trước đó ở `output/20261112_115609/` (lần đầu lỗi 400 `MissingSessionID`, xem dưới).

| Chỉ số | Giá trị |
|---|---|
| Trả lời / chạm trần bước | 17 / 3 (câu 12, 16, 19: 12 lượt, 18 đến 21 lần gọi công cụ, không có đáp án) |
| Chứa đáp án chuẩn (so khớp thô `contains`) | 16/20; câu 3 trả đúng ("Senegal, Dakar") nhưng bị chấm trượt vì đáp án chuẩn viết `Dakar , Senegal`, nên thực tế khoảng 17/20 (chưa đọc kỹ từng câu) |
| Thấy chunk gold ít nhất một lần | 20/20: lỗi không phải do không tìm thấy mà do dò quá nhiều bước |
| Số lượt LLM mỗi câu | p50 4, p90 12, max 12 (tổng 120); câu 18 trả lời đúng ở lượt 11 nên với trần 10 sẽ chạm trần: tổng 4 câu |
| Lời gọi công cụ | 150: `grep` 85, `read_page` 37, `list_pages` 28; 4 lần lỗi tham số |
| Token vào / ra | tổng 408.102 / 36.712; mỗi câu p50 8.765 / 463, p90 53.717 / 5.300, max 73.834 / 12.763 |
| Token vào trúng cache | 312.576 / 408.102 (77%) |
| Thời gian mỗi câu | p50 31,8 giây, p90 122,3, max 202; tổng 1.055 giây; LLM 1.048 giây, công cụ 6 giây (99% là chờ LLM) |
| TTFT mỗi lượt | p50 5,62 giây, p90 15,80 giây (n = 120); gồm lớp proxy OpenCode, có thể gồm suy luận ẩn của model |

**Điều đã kiểm chứng:** OpenCode nhận `tools` và `stream_options.include_usage` (có token vào/ra/cache khi streaming); tool-calling nhiều lượt chạy không lỗi dù không gửi lại chuỗi suy luận; log đủ prompt, câu trả lời, số đo.

**Phải sửa mới chạy được:** OpenCode Go đòi header `x-opencode-session` (mã phiên ổn định mỗi cuộc hội thoại) và khuyến nghị User-Agent riêng; thiếu thì 400 `MissingSessionID`. Đã thêm `default_headers` và `session_header` vào profile và `request_headers` vào `AgentLoop`.

**Lưu ý khi đọc số:** TPOT và tokens/s của profile này không đáng tin (token suy luận ẩn tính vào `output_tokens` nhưng không stream ra, nên chia token cho khoảng thời gian chỉ có phần văn bản hiện ra); TTFT, E2E, token vào/ra dùng được. Mẫu 20 câu, một seed, một mô hình, một lần chạy: chỉ để kiểm tra hệ thống chạy được và ước cỡ chi phí, không phải kết quả so sánh. Ba câu chạm trần dùng nhiều token nhất (57k, 74k, 53k token vào), nên phần lớn chi phí đến từ nhóm câu agent dò mãi không dừng.

**Chi phí 20 câu (tính theo bảng giá, 2026-11-12):** token vào không trúng cache 95.526 (= 408.102 - 312.576), token vào trúng cache 312.576, token ra 36.712 (`input_tokens` đã gồm phần trúng cache; token ra gồm cả suy luận ẩn nếu API tính). Giá DeepSeek V4.1 Flash theo `api-docs.deepseek.com/quick_start/pricing` và theo bảng Go của OpenCode (hai nơi trùng nhau): giờ thấp điểm vào 0,15, cache 0,003, ra 0,60 USD mỗi 1M token; giờ cao điểm gấp đôi (01:00-04:00 và 06:00-10:00 UTC, thứ Hai đến thứ Sáu). Lần chạy diễn ra khoảng 04:57-05:15 UTC thứ Năm nên thuộc giờ thấp điểm: 0,0143 (vào, miss) + 0,0009 (cache) + 0,0220 (ra) = **khoảng 0,037 USD, tức khoảng 0,0019 USD mỗi câu**; nếu rơi vào giờ cao điểm thì khoảng 0,075 USD. Ba câu chạm trần chiếm 45% token vào và 65% token ra. Với gói OpenCode Go (thuê bao tháng) khoản này trừ vào hạn mức, không thu tiền theo token; chưa ghi lại trường `opencode.allowance` mà mỗi phản hồi báo.

## 11. Dừng sớm và hướng dẫn suy luận (đề xuất 2026-11-12, chưa làm)

**Hiện trạng:** chỉ có hai cơ chế dừng cứng là trần số lượt (`max_steps`, nay 10) và trần token; ngoài ra là mô hình tự quyết dừng. Không có phát hiện lặp, không báo số lượt còn lại, không ép trả lời ở lượt cuối (chạm trần thì `answer = None`).

**Quan sát (20 câu, mục 10.2):** 3 câu chạm trần (12, 16, 19) không lặp y hệt lời gọi nào mà liên tục đổi cách tìm để thấy bằng chứng khớp **đúng mốc ngày** của câu hỏi (ví dụ `August 1905|June 1963`, `April 1734`, `Apr 2005`), kể cả thử trang không tồn tại hoặc trang không liên quan; chunk gold đã được thấy ở cả 3 câu. Trang chỉ nêu năm hoặc giai đoạn nên "xác nhận đúng ngày" không bao giờ xuất hiện. Câu trả lời đúng khác thường vẫn hedge ("trang không nêu tháng, nhưng...").

**Cơ chế dừng có thể thêm** (áp như nhau cho A và B):

| Cơ chế | Tác dụng | Cái giá |
|---|---|---|
| Báo số lượt còn lại mỗi lượt | agent tự biết lúc nào phải chốt | thêm một dòng vào tin nhắn |
| Lượt cuối ép trả lời, không cho gọi công cụ | không mất đáp án khi chạm trần; phân biệt "có bằng chứng mà không dám trả lời" với "không biết" | phép đo kém thuần hơn |
| Phát hiện gọi lặp, lan sang trang không liên quan | cắt lãng phí | phải định nghĩa "không liên quan", dễ nhúng thiết kế |

**Hướng dẫn suy luận (đề xuất, người dùng hỏi 2026-11-12):** cho agent biết rằng bằng chứng thời gian trong văn bản thường chỉ ở mức năm hoặc giai đoạn, nên không cần khớp đúng ngày; được suy từ chunk khác khi cần (một trạng thái đúng cho tới khi có chỗ nêu thay đổi; đoạn không ghi mốc thường thuộc giai đoạn của đoạn có mốc gần nhất trước nó); nếu phải suy thì nói rõ. Đây là quy tắc mà cơ chế time-aware của đồ án đã mã hóa (`end_time` mở, TH2 lùi về quá khứ gần nhất, suy mốc từ chunk liền kề `decisions/07` đề xuất 11, kết quả trung tính ở ingest), nên đặt nó vào prompt là một **biến của thí nghiệm**, không phải chi tiết harness:

| Biến thể prompt | Nội dung |
|---|---|
| P0 (hiện có, `agent_v1.md`) | trung tính |
| P1 | chỉ về việc dừng: báo số lượt còn lại, trả lời bằng bằng chứng tốt nhất hiện có (có thể kèm lượt cuối ép trả lời) |
| P2 | P1 cộng hướng dẫn suy luận thời gian ở trên |

Chạy A và B dưới cùng một biến thể; báo cáo từng biến thể riêng, vì mức "cần giúp bao nhiêu" là kết quả. **Rủi ro:** nhãn TimeQA là chunk chứa chuỗi đáp án, không phải khoảng thời gian chính xác (`eval/05` mục 7), nên P2 có thể tăng điểm nhờ khớp quy ước nhãn chứ không nhờ suy luận đúng. Vì vậy chỉ phát triển P1, P2 trên tune, xác nhận trên valid, rồi đóng băng trước khi chạy test_clean; và để agent ghi rõ câu trả lời có phải suy ra không, để đối chiếu.

### 11.1. Yêu cầu bổ sung của người dùng cho P1/P2 (2026-11-12, chưa làm)

Hai ràng buộc, áp cho mọi biến thể có hướng dẫn suy luận:

1. **Suy luận phải có căn cứ, không đoán.** Agent chỉ được suy ra đáp án khi dẫn được đoạn văn làm căn cứ (số chunk `[#i]` hoặc `page_id#i`, kèm câu trích). Quy tắc suy luận hợp lệ chỉ gồm: (a) một sự kiện nêu năm hoặc tháng thì coi là đúng cho cả năm hoặc tháng đó; (b) một trạng thái đúng cho tới khi có đoạn nêu thay đổi; (c) ghép hai đoạn (mốc trước và mốc sau) để kẹp thời điểm hỏi. Nếu không dẫn được căn cứ thì trả lời "không xác định được từ tài liệu" kèm điều đã thấy, không nêu đáp án đoán.
2. **Không lan man, không gọi công cụ quá nhiều.** Dừng tìm khi đã có đủ sự kiện bao quanh mốc hỏi; không đi tìm đoạn nêu đúng ngày hỏi; không tìm lại điều đã đọc; hai lần tìm liên tiếp không thêm sự kiện mới thì chốt đáp án. Cơ chế vòng lặp đi kèm (không phải prompt): báo số lượt còn lại và ép trả lời ở lượt cuối (mục 11 bảng cơ chế dừng). Ép trả lời ở lượt cuối vẫn phải theo ràng buộc 1 (không căn cứ thì trả "không xác định").

**Nháp P1 (tiếng Anh, chưa vào `src/tam/llm/prompts/`):**

```
Pages rarely state the exact date a question asks about. Do not search for a passage that mentions that exact date. Treat a fact stated for a year or a month as holding for that whole year or month, and treat a state as holding until a passage says it changed. You may combine passages (an earlier and a later one) to place the asked date between them.
Every answer must rest on passages you actually read: give the passage ids and a short quote. If you cannot ground an answer this way, say it cannot be determined from the collection and state what you found; never guess.
Be economical: stop searching once you have the facts around the asked date. Do not re-read what you already read. If two searches in a row add no new fact, answer with what you have.
```

**Trần lượt (người dùng chốt 2026-11-12): tối đa 5 lần gọi LLM mỗi câu** (mặc định của `scripts/run_agent_search.py --max-steps`). Cơ sở từ 20 câu cũ (`output/20261112_115710`): chunk gold đã tới tay LLM ở lượt 2 (15/20 câu), lượt 3 (4 câu), lượt 4 (1 câu, câu 12); nên 5 lượt đủ để tìm, miễn là agent không đi đòi khớp đúng ngày. Với trần cũ, chỉ 12/20 câu xong trong 5 lượt; 8 câu còn lại phải dựa vào cơ chế ép trả lời ở lượt 5 (mục 11) cộng quy tắc suy luận của P1. Rủi ro: câu 12 chỉ còn 1 lượt sau khi thấy chunk. Nếu chạy 5 lượt mà số câu "không xác định" tăng nhiều trong khi chunk gold đã thấy thì xem lại trần, đừng kết luận agent kém.

**Prompt P1 rút gọn (125 từ thay vì 196, vẫn đủ ý):** gộp ý "trả lời từ văn bản đã đọc" và "nếu không có thì nói không biết" vào ràng buộc căn cứ, bỏ ví dụ thừa; ràng buộc 1 và 2 giữ nguyên.

**Hệ quả cho cách chấm:** câu trả lời có `căn cứ` được kiểm tra riêng: đáp án đúng mà không dẫn được căn cứ (hoặc căn cứ không chứa đáp án) tính là đúng do may, báo riêng. Đo thêm "tỉ lệ trả lời đúng trong số câu dám trả lời" và "tỉ lệ từ chối khi có chunk gold" để thấy ràng buộc 1 có làm agent quá rụt rè không.

**Cần theo dõi:** ràng buộc 1 và 2 kéo ngược nhau với số lượt (ít lượt thì ít căn cứ); so P1 với P0 bằng log: số câu đòi đúng ngày giảm, số lượt trung bình giảm, mà đúng-có-căn-cứ không giảm.

### 11.2. Đã làm và lần chạy thử đầu với P1 (2026-11-12)

**Mã:** `src/tam/llm/prompts/agent_v2.md` (P1 rút gọn, 125 từ; `agent_v1.md` giữ nguyên làm P0); `AgentLoop(budget_notice=True)`: sau mỗi lượt công cụ gắn dòng "còn N lượt" vào kết quả công cụ cuối, lượt cuối **không gắn công cụ** và dòng báo bảo trả lời ngay theo ràng buộc căn cứ; lượt cuối trả rỗng thì `answer=None`, `stop_reason=max_steps`. `scripts/run_agent_search.py` thêm `--prompt` (mặc định v2), `--no-budget-notice`, `--pick` (số thứ tự 1-based trong mẫu `--n/--seed`), `--max-steps` mặc định 5. 279 test qua.

**Chạy thử (`output/20261112_130332`, kiểu A, 5 câu khó của mẫu seed 1: 12, 15, 16, 18, 19; trần 5; P1 cộng báo lượt):** 5/5 có trả lời, không câu nào chạm trần (trước: 12, 16, 19 chạm trần 12 lượt). Tự chấm: 18 đúng có căn cứ (4 lượt, trước 11); 19 đúng có căn cứ (5 lượt); 16 đúng một phần có căn cứ (nêu 2. Bundesliga rồi lên Bundesliga ngày 16/4/2006, gold là Bundesliga); 12 và 15 từ chối "không xác định" (câu 12 nêu LCC là gần nhất rồi tự hạ vì một đoạn ghi 1965; câu 15 thấy Manchester từ 1966 và Reading 10 năm nhưng không có mốc 8/1968). Tổng 22 lượt, token vào 49.547 (không có số cache ở lượt cuối), ra 8.513, 189 giây. **Chưa kiểm chứng:** chỉ 5 câu chọn từ nhóm khó nên không so được tỉ lệ với 20 câu cũ; cần chạy cả 20 câu cùng seed và đối chiếu P0 cùng trần 5.

**Quan sát:** lượt cuối bị ép trả lời (không công cụ) tốn nhiều token suy luận ẩn và TTFT rất cao ở câu 19 (4.353 token ra, TTFT 49 giây). Ràng buộc căn cứ làm 2/5 câu từ chối dù chunk gold đã thấy: đúng ý ("không đoán") nhưng cần theo dõi tỉ lệ từ chối khi có chunk gold.

### 11.3. Biến thể P2, P3 và lần chạy song song 5 câu (2026-11-12)

**Mã:** `agent_v3.md` (P2 = P1 + "khoảng hỏi bị cắt ngang thì nêu từng giá trị kèm giai đoạn" + đầu ra ba dòng `Answer/Basis/Type`, 178 từ); `agent_v4.md` (P3 = P2 + "có đoạn nêu giá trị cho chủ thể nhưng mốc chỉ phủ một phần thì đưa giá trị đó, đánh dấu inferred", 219 từ); mô tả `grep` ghi rõ chỉ trả đoạn trích, muốn đọc trọn thì dùng `read_page`; `scripts/run_agent_search.py --workers N` chạy N câu song song. 280 test qua.

**Kết quả** (cùng 5 câu khó seed 1, trần 5, kiểu A; tôi tự chấm; `output/20261112_134127` = P2, `output/20261112_134308` = P3; P1 ở `output/20261112_130332`):

| Câu (gold) | P1 | P2 | P3 |
|---|---|---|---|
| 12 (London County Council) | từ chối | đúng, inferred | một phần (County of London, không nêu Council) |
| 15 (University of Manchester) | từ chối | đúng, inferred (kẹp bằng mốc 1979 của chuyển sang UWIST) | **sai**: University of Reading, suy luận "trong khoảng 10 năm ở Reading" nhưng 1979 trừ 10 năm là 1969 nên không phủ 8/1968 |
| 16 (Bundesliga) | một phần | một phần có đủ hai giai đoạn | như P2 |
| 18 (Santa Cruise) | đúng | đúng | đúng |
| 19 (Grand Duchy of Tuscany) | đúng | một phần ("cannot be determined" nhưng nêu Tuscany và Papal States) | đúng (cùng Papal States) |

Thời gian thực cả loạt 5 câu song song: P2 97,7 giây (câu 19 sinh 7.184 token ra), P3 35,4 giây. Token vào/ra: P2 52.142/11.172, P3 51.198/7.455. **Chưa kiểm chứng:** 5 câu, một lần chạy mỗi biến thể, nên chênh một hai câu có thể là ngẫu nhiên giữa các lần chạy; không kết luận hơn kém P2 với P3.

**Quan sát:** (1) P3 biến từ chối thành trả lời, nhưng được 1 câu (19) và mất 1 câu (15) vì suy luận không có căn cứ đủ; đây đúng là rủi ro đã nêu ở mục 11.1; (2) nhãn `Type` hầu như luôn là `inferred`, hiếm khi `stated`, nên chưa phân biệt được đúng-có-căn-cứ với đúng-do-suy; (3) cả hai biến thể dẫn căn cứ bằng chunk id và trích dẫn, kiểm chứng được tay.

### 11.4. Chạy đủ 20 câu, trần 5 lượt, P2 và P3 (2026-11-12)

Cùng mẫu 20 câu seed 1 như lần P0 (`output/20261112_115710`, trần 12). Kiểu A, `--workers 5`, `--max-steps 5`. P2 = `output/20261112_134606`, P3 = `output/20261112_134848`. Tôi tự chấm: đúng = 1, một phần = 0,5, sai hoặc từ chối = 0.

| | P0 (trần 12) | P2 (trần 5) | P3 (trần 5) |
|---|---|---|---|
| Có trả lời | 17/20 | 20/20 | 20/20 |
| Điểm tự chấm | 16 đến 17 (câu 7, 18 đúng nhưng rào đón; 15 từ chối) | 17,5 | 19,0 |
| Từ chối | 1 (câu 15) + 3 chạm trần | 1 (câu 15) | 0 |
| Tổng lượt LLM / lượt công cụ | khoảng 110 / 150 | 75 / 64 | 73 / 62 |
| Token vào / ra | 408.102 / 36.712 | 154.247 / 15.802 | 150.925 / 11.598 |
| Nhãn Type | | stated 5, inferred 14, cannot 1 | stated 7, inferred 13 |

Ghi chú chấm: cả hai nêu thêm thông tin thừa đúng sự thật ở câu 2, 5, 19 (vẫn tính đúng). P2 mất điểm ở câu 1 (nêu cả Kellyanne Conway cạnh DeStefano: 0,5), câu 13 (trả "S/R Mediterranean" chứ không phải SeaRiver Mediterranean ở khoảng hỏi: 0,5), câu 15 (từ chối). P3 mất ở câu 12 (nêu County of London, không nêu Council: 0,5). Câu 16 cả hai nêu đủ hai giai đoạn (0,5 vì gold chỉ có Bundesliga).

**Điều quan trọng nhất:** cùng prompt P3, câu 15 trả **University of Reading (sai)** ở lần chạy 5 câu và **University of Manchester (đúng)** ở lần chạy 20 câu; còn P2 đúng ở lần 5 câu và từ chối ở lần 20 câu. Nên chênh 1,5 điểm giữa P2 và P3 nằm trong dao động giữa các lần chạy; không kết luận hơn kém từ một lần chạy 20 câu. Cần lặp nhiều lần hoặc tăng số câu.

**Chắc chắn hơn (không phụ thuộc dao động):** so với P0, hai biến thể mới đều xong cả 20 câu trong 5 lượt (P0 phải đến 12 lượt mới xong 17 câu), giảm khoảng 62% token vào và 57% đến 68% token ra. Mức đúng không thấp hơn P0.

### 11.5. Vì sao agent thấy đáp án mà không chốt; chunk gold tới tay lúc nào (2026-11-12)

Từ log lần chạy 20 câu đầu (`output/20261112_115710`, P0, trần 12):

- **Chunk gold tới tay LLM sớm:** theo danh sách `chunk_ids` của công cụ, LLM đọc được chunk gold ở lượt 2 với 15/20 câu, lượt 3 với 4 câu, lượt 4 với 1 câu (câu 12). Nhưng 6 câu còn tiêu từ 6 lượt trở lên **sau** khi đã thấy chunk (câu 1, 12, 15, 16, 18, 19); phần lớn lượt LLM đi vào việc tìm thêm bằng chứng khớp ngày.
- **Danh sách `chunk_ids` lạc quan:** `grep` chỉ trả **đoạn trích ngắn** quanh lần khớp đầu của mỗi chunk, không trả cả chunk. Câu 19: chunk gold `#8` nằm trong danh sách ở lượt 1 nhưng đoạn trích bị cắt trước chữ "Grand Duchy of Tuscany"; chuỗi đáp án chỉ hiện ở tin nhắn công cụ thứ 9. Đối chiếu bằng cách tìm chuỗi đáp án trong nội dung các tin nhắn công cụ của `agent_calls.jsonl`: câu 12 thấy ở tin nhắn thứ 4, câu 16 ở thứ 1, câu 19 ở thứ 9. Sửa: mô tả `grep` nay ghi rõ chỉ là đoạn trích, muốn đọc trọn dùng `read_page`; cột `saw_gold_chunk` cần đổi cách tính (mục 8, việc mới).
- **Nguyên nhân không chốt (suy từ lời gọi công cụ; chuỗi suy luận ẩn của mô hình trống trong log nên chưa kiểm chứng):** agent đi tìm đoạn khớp đúng ngày: câu 16 gọi `grep` các chuỗi `Apr(il)? 2005`, `Sep(tember)? 2006`, rồi liệt kê trang theo tên giải đấu, rồi sang trang khác (1. FC Köln, Dieter Hecking); câu 12 gọi `1905.*1963`, `August 1905|June 1963`, `Brigade[\s\S]{0,300}1963`, `municipalit`; câu 19 gọi `April 1734`, `June 1815`, `1734.{0,200}1815`. Prompt cũ không nói khi nào đủ để dừng, nên không có điểm dừng nào; không thấy đoạn nêu đúng ngày được hiểu là "chưa tìm xong" chứ không phải "trang không ghi ngày này".
- **Riêng câu 16** khoảng hỏi (4/2005 đến 9/2006) cắt ngang lúc lên hạng, nên không có một đáp án duy nhất; gold chỉ ghi Bundesliga. Câu hỏi tự nó mơ hồ, không chỉ do agent.
- **Sau P1 đến P3:** vẫn còn tìm theo **năm** (`1734|1815`, `1968`, `1905|1963`), nhưng hết tìm tháng và ngày (trừ lượt 1 câu 15); câu 16 và 18 không tìm ngày nào. Tìm theo năm là cách tìm đúng đoạn nói về năm đó nên không coi là lỗi.
- **Prompt thêm vào dài hơn bao nhiêu:** P0 53 từ; P1 125 từ; P2 178 từ; P3 219 từ (khoảng 2,4 đến 4,1 lần P0). Lượt đầu 967 token (phần lớn là schema công cụ, khoảng 850; prompt hệ thống khoảng 75; câu hỏi khoảng 25); P3 thêm khoảng 190 token, được cache từ lượt 2 nên chi phí thêm không đáng kể.
- **Trần lượt:** với P0, trong 17 câu có trả lời p50 là 4 lượt, p90 khoảng 9; xong trong trần 8 được 15/20, trần 10 được 16/20, trần 12 vẫn 16/20. Người dùng chốt trần 5 (2026-11-12); P2 và P3 xong 20/20 trong 5 lượt (mục 11.4).
- **Khi dùng trần 5, nhớ ép trả lời ở lượt cuối** (`budget_notice`), nếu không câu nào chưa chốt ở lượt 5 sẽ ra `answer=None` và lẫn lỗi suy luận với lỗi hết lượt. Lượt cuối tắt công cụ nên mô hình suy luận ẩn nhiều: câu 19 ở P2 sinh 7.184 token ra, TTFT 49 giây.

### 11.6. Cache từng lần gọi LLM của agent (2026-11-12)

**Trước đó** các lần gọi của agent chỉ được ghi **log** (`agent_calls.jsonl`, `agent_trace.jsonl`, `llm_calls.jsonl`, `run.log` trong `output/<ts>/`), không có cache nào; cache phản hồi LLM cũ (`data/llm_cache/cache.sqlite`, khoảng 5.900 mục Gemini/Gemma) chỉ do `invoke_structured` ghi cho ingestion, profiler và answerer. Chạy lại cùng câu hỏi là gọi API lại từ đầu.

**Nay:** `AgentLoop(cache=...)`; `scripts/run_agent_search.py` mặc định bật, lưu ở **file riêng** `data/llm_cache/agent/cache.sqlite` (tách khỏi cache của pipeline; `data/` gitignore).
- Khóa = (model, `cache_salt`, có gắn công cụ hay không + schema công cụ, toàn bộ tin nhắn đến lượt đó). Đổi prompt, model, danh sách công cụ hoặc câu hỏi thì tự trượt cache. Lượt cuối bị ép trả lời (không công cụ) có khóa riêng.
- Chỉ lượt gọi **thành công và không rỗng** mới được ghi; lỗi LLM không ghi.
- **Trúng cache:** không gọi API; số đo (token vào/ra/cache, TTFT, E2E) lấy nguyên từ lần gọi thật để chạy lại ra đúng bảng cũ; đánh dấu `cache_hit` ở `agent_trace.jsonl` và `agent_calls.jsonl`, và `cache_hits` trong `results.jsonl`. Muốn thống kê độ trễ thật thì lọc bỏ các lượt `cache_hit=true`, hoặc đọc `llm_calls.jsonl` (chỉ có lần gọi thật).
- Tùy chọn: `--no-cache`, `--cache-dir`, `--refresh-cache` (ghi đè mục đã có), `--repeat-id N`.
- **Lặp để đo dao động phải đổi `--repeat-id`** (khóa có salt này): cùng số thì tái dùng kết quả, khác số thì gọi mới; nếu quên, lần lặp trả đúng kết quả lần đầu và phép đo dao động vô nghĩa.
- `SqliteCache` có thêm `threadsafe=True` (một kết nối dùng chung, khóa `RLock`) vì `--workers N` chạy nhiều luồng.
- Đã kiểm trên API thật: câu 18 với P2, lần 1 gọi 4 lượt (19,8 giây), lần 2 trúng cache 4/4, 0 giây, không có `llm_calls.jsonl` (không có lần gọi thật), đáp án và token trùng. Các lần chạy trước khi có cache (mục 11.2 đến 11.4) **không** nằm trong cache, chạy lại sẽ gọi API.
- 285 test qua (thêm 5 test: phát lại không gọi LLM, đổi salt/model/prompt thì trượt, không ghi lỗi hoặc rỗng, refresh, nhiều luồng).

### 11.7. Chạy P2 và P3 trên 20 câu khác (2026-11-12, người dùng yêu cầu)

Mục đích: xem P2 (`--prompt v3`) và P3 (`--prompt v4`) có giữ kết quả trên mẫu mới không, và còn vấn đề gì. Cấu hình: role `agent` = `opencode_deepseek_flash`, trần 5 lượt, báo lượt, 10 luồng song song (`--workers 10`), cache riêng, `--repeat-id 0`. Mẫu: `--n 20 --seed 2` trên `tune_base_subset.json` (400 câu); đã kiểm 20 câu này **không giao** với mẫu seed 1. Kết quả ghi bên dưới sau khi chạy.

**Kết quả (mẫu seed 2, 20 câu, trần 5, 10 luồng mỗi bộ; P2 `output/20261112_173317`, P3 `output/20261112_173317_2`).** Cả hai chạy xong trong khoảng 50 giây thực, không lỗi, không bị giới hạn tốc độ; 0 lượt từ cache.

| | P2 (v3) | P3 (v4) |
|---|---|---|
| trả lời / chạm trần | 20/20 / 0 | 20/20 / 0 |
| so khớp thô `contains` | 18 | 18 |
| tôi chấm tay (đúng 1, sai 0, bỏ qua 3 câu gold đáng ngờ) | 16 | 16,5 đến 17 |
| lượt LLM | 74 | 73 |
| token vào / ra | 179.892 / 13.369 | 175.981 / 13.432 |
| TTFT p50 / p90 (s) | 3,51 / 6,57 | 3,51 / 5,41 |

**Vấn đề thấy được:**
1. P2 và P3 gần như ngang nhau (khác đúng một câu, câu 10: P2 từ chối "cannot be determined" dù đã tìm ra Florence và Papal States, P3 trả lời). Giống mẫu seed 1: chênh trong vùng dao động; chưa chốt.
2. **Câu 20** (Metro Line 2, gold Gorgonzola), cả hai từ chối. Trang có "1968 tới Gorgonzola", "1972 nhập vào Metro", "1985 kéo dài tới Gessate", tức là suy ra được Gorgonzola cho 1975 bằng ghép các đoạn. Agent đòi một đoạn nói thẳng năm 1975 (chuỗi Gorgonzola đã hiện trong văn bản công cụ từ lượt 2, xem 11.8). Đây vẫn là lỗi "đòi đúng mốc" còn sót, và khoảng cách giữa "từ chối" và "ứng viên có căn cứ" là chỗ P3 chỉ sửa một phần.
3. **`contains` thô chấm lạc quan:** P2 câu 10 từ chối nhưng vẫn tính trúng vì câu trả lời nhắc tên đáp án trong phần Basis; câu 18 trúng vì nhắc "colonial forces" ở phần giải thích dù kết luận khác. Cần script chấm có LLM judge (mục 13).
4. **Gold đáng ngờ:** câu 8 (gold "he stepped back from political life" cho câu hỏi về đảng) và câu 18 (gold là chức vụ từ 1894, hỏi "trước Apr 1894", cả hai bộ trả lời chỉ huy tiểu đoàn Lauenburg, khớp văn bản). Cần soát tay trước khi tính điểm chính thức.
5. Câu 14 (rector of physics) tốn 29.000 token vào qua 5 lượt (7 lần gọi công cụ), gấp 5 lần câu thường (khoảng 6.000).

### 11.8. Sửa `saw_gold_chunk` thành kiểm văn bản công cụ (2026-11-12, không gọi LLM)

- `AgentRun.tool_texts` lưu (lượt, văn bản công cụ đưa cho agent); `AgentRun.first_step_showing(targets)` trả lượt LLM đầu tiên mà văn bản đó chứa trọn một đáp án (theo từ, sau chuẩn hóa như `contains`), None nếu chưa lần nào. Lượt n nghĩa là lời gọi công cụ ở lượt n trả về đáp án, agent nhìn thấy từ lượt n+1.
- `results.jsonl` đổi trường: `gold_chunk_listed` (chỉ số cũ, theo `chunk_ids`, lạc quan), `saw_gold_text`, `gold_text_step` (mới). Trường `saw_gold_chunk` bỏ. Bản tóm tắt in thêm p50/p90 của lượt đầu tiên thấy đáp án. Thêm 1 test (27 test file loop; tổng 286 qua, 4 xfail).
- **Tính lại offline cho 4 lần chạy đã có** (đọc `agent_calls.jsonl`, tin nhắn `tool` trong prompt cuối của mỗi câu; không gọi API). Chuỗi đáp án có trong văn bản công cụ ở: P2 seed 1 20/20, P3 seed 1 20/20, P2 seed 2 19/20, P3 seed 2 19/20. Lượt đầu tiên: seed 1 chủ yếu lượt 1 đến 2 (P2: 10 câu lượt 1, 8 lượt 2, 2 lượt 3; P3: 12, 7, và 1 câu lượt 4). Seed 2: lượt 1 đến 2 gần hết, ngoại lệ câu 14 (lượt 4) và câu 4, câu 2 của P2 (lượt 3). Tức đáp án thường tới tay agent sớm, nên lỗi chủ yếu nằm ở bước kết luận chứ không phải tìm.
- Câu duy nhất không bao giờ hiện chuỗi đáp án: câu 8 seed 2 (gold "he stepped back from political life", xem 11.7), cho thấy gold đó không khớp văn bản.
- **Đính chính 11.7 mục 2:** câu 20 seed 2 (Metro Line 2, Gorgonzola): chuỗi "Gorgonzola" **đã hiện** trong văn bản công cụ từ lượt 2 (đoạn [#3] đọc đủ, có "opened in 1968 from Cimiano up to Gorgonzola"), nhưng agent vẫn từ chối vì cho rằng không có đoạn nào nói thẳng năm 1975. Đây là "thấy mà không chốt", không phải lỗi tìm kiếm hay cắt đoạn trích.
- Giới hạn còn lại: khớp chuỗi chỉ chứng minh đáp án có trong văn bản, không chứng minh nó đúng cho mốc thời gian hỏi (một chuỗi như "Royal Navy" có thể xuất hiện cho giai đoạn khác).

### 11.9. Chấm offline bằng `scripts/score_agent_runs.py` (2026-11-12, không gọi LLM)

Script đọc `results.jsonl` + `agent_calls.jsonl` của các lần chạy đã có. Chấm theo **dòng `Answer:`** (không tính phần Basis, vì Basis hay nhắc lại đáp án nên `contains` thô chấm lạc quan), rồi chia nhóm: `correct`, `refused_seen` / `refused` (từ chối khi đáp án đã / chưa hiện trong văn bản công cụ), `wrong_seen` (sai dù đã thấy: thấy mà không chốt), `wrong_not_seen`, `no_answer`. Vẫn là so khớp chuỗi, chưa phải LLM judge. Giá: DeepSeek V4.1 Flash giờ thấp điểm.

| lần chạy | prompt, mẫu | đúng (dòng Answer) | `contains` thô | nhóm lỗi | lượt/câu | token vào (cache) / ra | USD |
|---|---|---|---|---|---|---|---|
| `20261112_134606` | P2, seed 1 | 18/20 | 20 | refused_seen 1 (q15), wrong_seen 1 (q13) | 3,75 | 154.247 (59%) / 15.802 | 0,019 |
| `20261112_134848` | P3, seed 1 | 19/20 | 19 | wrong_seen 1 (q12) | 3,65 | 150.925 (61%) / 11.598 | 0,016 |
| `20261112_173317` | P2, seed 2 | 18/20 | 18 | refused_seen 1 (q20), wrong_not_seen 1 (q8) | 3,70 | 179.892 (55%) / 13.369 | 0,020 |
| `20261112_173317_2` | P3, seed 2 | 17/20 | 18 | refused_seen 1 (q20), wrong_seen 1 (q18), wrong_not_seen 1 (q8) | 3,65 | 175.981 (52%) / 13.432 | 0,021 |

- **Gộp 40 câu: P2 = 36, P3 = 36.** Không phân biệt được P2 với P3 (kết luận cũ giữ nguyên). Điểm tay trước đó (P2 17,5, P3 19,0 ở seed 1) cao hơn vì tôi cho 0,5 điểm câu một phần và tính khoan dung hơn; số ở bảng này là số cứng, dùng để so.
- **Phân bố lỗi:** 7 câu sai trên 80 lượt chấm thì 5 câu là "thấy mà không chốt" (đáp án đã hiện trong văn bản công cụ): từ chối khi lẽ ra ghép được (q15 seed 1 P2, q20 seed 2 cả hai), hoặc chốt giá trị khác (q12, q13, q18). Chỉ câu 8 seed 2 là gold không khớp văn bản. Vậy chỗ cần cải thiện là bước kết luận, không phải công cụ tìm.
- **Chấm khớp chuỗi sai hai chiều, cần judge:** (a) false negative: câu 13 seed 1 P2 trả "S/R Mediterranean" cho gold "SeaRiver Mediterranean" (khác tên viết tắt, cùng ý); câu 12 seed 1 P3 "County of London" cho gold "London County Council" (khác thật hay cùng ý còn phải kiểm); (b) false positive: câu 18 seed 2 P2 được tính đúng vì dòng Answer nhắc "colonial forces in German East Africa" như sự kiện sau mốc, trong khi kết luận chính là tiểu đoàn Lauenburg (giống P3 bị tính sai). Nên số đúng của P2 seed 2 có thể là 17, tức P2 = 35.
- **Chi phí:** khoảng 0,016 đến 0,021 USD cho 20 câu (khoảng 0,001 USD/câu), 3,65 đến 3,75 lượt LLM mỗi câu, tỉ lệ cache token vào 52 đến 61% (thấp hơn P0 trần 12 là 77% vì ít lượt hơn nên ít được dùng lại tiền tố). Gói OpenCode Go tính thuê bao nên đây chỉ là chi phí quy đổi.
- Lệnh: `python3 scripts/score_agent_runs.py <tên thư mục output> ... [--detail]`.

### 11.10. 386 chunk thiếu trong kho vector và kiểu B trong `run_agent_search.py` (2026-11-12, không gọi LLM)

**386 chunk có trong kho text (A) nhưng không có trong Qdrant (B).** Đối chiếu `chunk_id` của 16.740 đoạn kho text với 16.354 điểm của ba collection; kho vector không có chunk nào ngoài kho text. Lý do bị loại lúc ingest, tra trong `output/*/extractions.jsonl` (384/386 chunk có dòng): `no_time` 274, `invalid_time` 89, `llm_error` 21; 2 chunk còn lại không có dòng (nhiều khả năng bị bỏ vì hash trùng; 3 chunk thiếu có văn bản trùng hệt chunk khác). Chunk thiếu thường ngắn (trung vị 152 ký tự, so với 418 ký tự của mọi chunk), kiểu "External links", "Ancient ... civilization". Trải trên 242 trang; trang `Young_Girl_with_a_Flower_Basket` mất toàn bộ (đó là 1 trang thiếu trong 556).
- **Ảnh hưởng tới phép so:** B không thể trả 386 chunk này, A đọc được. Trên các bộ câu hỏi đã có, chỉ **2 câu của `valid_subset`** (399 câu) có chunk gold nằm ngoài kho vector; `tune_base`, `test_clean`, `tune`, `real` và các `capability_probe` đều 0. Nên sai lệch do thiếu chunk nhỏ, nhưng phải ghi khi báo kết quả valid.

**Kiểu B đã nối vào `scripts/run_agent_search.py`:** `--kind B` dùng `vector_search` (dense, bm25, hybrid; `k`, `offset`, `start_before`, `include_invalidated`) và `read_chunk` (kèm chunk liền kề) của `src/tam/tools/vector_tools.py`; chưa có `temporal_search`. Collection tự lấy là `tam_chunks_dev_<split>` theo `data/text_corpus.index.json` (tune, valid hoặc test_clean; mỗi lần chạy một split, hoặc truyền `--collection`). Embed cục bộ bằng fastembed (`bge_small_en`, BM25), không gọi API; chỉ vòng lặp agent gọi LLM. Cờ thêm: `--k-cap` (mặc định 50), `--hide-time` (ẩn khoảng hiệu lực để xem agent dựa vào metadata hay văn bản). System prompt và vòng lặp giữ nguyên với kiểu A. Cache khóa theo cả lược đồ công cụ nên không lẫn với kiểu A.
- Đã thử không gọi LLM trên Qdrant thật (câu 19 seed 1 của `tune_base`): ba chế độ chạy được, `read_chunk` kèm chunk liền kề chạy được; với nguyên câu hỏi làm truy vấn, chunk gold không nằm trong top 5 ở cả dense, bm25 và hybrid. Chưa chạy agent kiểu B nào (cần hỏi người dùng).

### 11.11. Kiểu B lần đầu, P2 và P3, 40 câu (2026-11-12)

Cấu hình: `--kind B`, role `agent` = `opencode_deepseek_flash`, trần 5 lượt, báo lượt, 10 luồng, mỗi cấu hình một lần (0 lượt từ cache), collection `tam_chunks_dev_tune`, công cụ `vector_search` + `read_chunk` (không có `temporal_search`, khoảng hiệu lực hiển thị). Chấm bằng `scripts/score_agent_runs.py` (dòng Answer, khớp chuỗi thô). Mọi lượt trả lời đủ, không chạm trần, không lỗi.

| lần chạy | prompt, mẫu | đúng | lỗi | lượt/câu | token vào (cache) / ra | USD |
|---|---|---|---|---|---|---|
| `20261112_204902` | B P2 seed 1 | 19/20 | q3 (format) | 3,30 | 183.147 (48%) / 22.166 | 0,028 |
| `20261112_205035` | B P3 seed 1 | 17/20 | q3 (format), q5, q13 (format) | 2,90 | 148.521 (44%) / 15.152 | 0,022 |
| `20261112_205148` | B P2 seed 2 | 18/20 | q8 (gold), q18 | 3,40 | 189.178 (48%) / 23.688 | 0,029 |
| `20261112_205253` | B P3 seed 2 | 17/20 | q8, q18, q20 (từ chối) | 3,25 | 196.034 (41%) / 22.360 | 0,031 |

**So với kiểu A (cùng 40 câu, cùng prompt, mục 11.9):** P2: A 36, B 37; P3: A 36, B 34 trên 40. Chênh nằm trong sai số chấm khớp chuỗi (câu 3 "Senegal (Dakar)" so với gold "Dakar , Senegal" và câu 13 "S/R Mediterranean" là sai định dạng, không sai nội dung; nếu tính là đúng thì B P2 = 38, B P3 = 36). Chưa thấy bên nào hơn về độ đúng; kiểu B tốn hơn: token ra 15.152 đến 23.688 (A: 11.598 đến 15.802), USD 0,022 đến 0,031 mỗi 20 câu (A: 0,016 đến 0,021), tỉ lệ cache token vào thấp hơn (41 đến 48% so với 52 đến 61%). Số lượt LLM xấp xỉ (B 58 đến 68, A 73 đến 75).

**Agent dùng công cụ thế nào (từ `agent_trace.jsonl`, gộp 4 lần chạy, 200 lời gọi `vector_search`):**
- Chọn `mode=hybrid` trong khoảng 90% lời gọi (bm25 20, dense 1); **hầu như không dùng bộ lọc thời gian**: `start_before` chỉ 6 lần trên 200 lời gọi; `include_invalidated=false` 0 lần.
- Đặt `k` lớn hơn mặc định 5 ở phần lớn lời gọi (167/200), tức tự mở rộng số kết quả thay vì lọc.
- `read_chunk` 52 lần (mở chunk gần, hoặc đọc cả đoạn).
- Chuỗi đáp án hiện ngay lượt 1 gần như mọi câu (p50 = 1, p90 1 đến 2): tìm không phải điểm yếu.
- Các lỗi giống kiểu A: q18 (gold đáng ngờ), q20 (từ chối dù thấy), q8 (gold lạ); riêng B P3 seed 1 câu 5 sai ("Oblt.z.S. Horst Willner" thay "Wilhelm Peters", nhầm người chỉ huy theo giai đoạn).

**Hạn chế:** mỗi cấu hình một lần, chưa có `temporal_search`, kho vector thiếu 386 chunk (mục 11.10; không ảnh hưởng 40 câu này vì 0 gold nằm ngoài kho), chấm bằng khớp chuỗi thô, và chưa có mốc "pipeline cố định" cùng LLM để so (mục 12).

### 11.12. Mốc pipeline cố định cùng LLM trên 40 câu (2026-11-12)

Mục đích: trả lời "agent có hơn pipeline cố định không" ở mức đáp án cuối (mục 12). **Cùng 40 câu** (seed 1 và seed 2 của `tune_base`, đã dùng cho A và B), **cùng LLM** `opencode_deepseek_flash`, mỗi cấu hình một lần.
- Truy xuất (không gọi LLM, embed cục bộ): `scripts/evaluate.py --subset tune_base --collection tam_chunks_dev_tune --mode oracle --top-k 15`, hai phương pháp: `temporal` (Cơ chế 1 với `T_req` lấy từ gold, tức cận trên của pipeline vì không qua Query Profiler; `output/20261112_211128`) và `hybrid` (RAG thường, không lọc, không chấm thời gian; `output/20261112_211134`). Trên cả 400 câu: temporal Hit@1 0,345, Hit@5 0,74; hybrid Hit@1 0,2775, Hit@5 0,70.
- Sinh đáp án: `scripts/generate_answers.py --prompt v1 --top-k 15 --batch 1 --ids-file <40 id> --profile opencode_deepseek_flash`, 1 câu mỗi request, `Answerer` v1 (cho phép từ chối). Sửa script: thêm `--collection`, và đặt header `x-opencode-session` (thiếu thì 400 `MissingSessionID`). Cache dùng chung `data/llm_cache/cache.sqlite` (khóa gồm prompt và đầu vào).

| hệ thống (40 câu) | `contains` | EM | F1 | từ chối | trả lời sai | token vào / ra (40 câu) |
|---|---|---|---|---|---|---|
| pipeline temporal (oracle `T_req`), top 15 (`output/20261112_211220`) | 25/40 (62,5%) | 0,575 | 0,657 | 17,5% | 20% | 99.427 / 25.141 |
| pipeline hybrid, không lọc, top 15 (`output/20261112_211335`) | 30/40 (75%) | 0,725 | 0,807 | 5% | 20% | 92.628 / 39.075 |
| agent A, P2 / P3 (mục 11.9) | 36/40 / 36/40 chấm theo dòng Answer | | | | | P2 334.139 / 29.171; P3 326.906 / 25.030 |
| agent B, P2 / P3 (mục 11.11) | 37/40 / 34/40 | | | | | P2 372.325 / 45.854; P3 344.555 / 37.512 |

- **Trên 40 câu này agent hơn pipeline cố định:** 34 đến 37/40 (85 đến 93%) so với 25 và 30/40. Phần lớn chênh lệch của temporal đến từ **từ chối** (17,5% so với 5% của hybrid, khoảng 0 ở agent): bộ lọc cứng `start_time <= T_req` đẩy ra khỏi top 15 chunk cần để suy luận, và `Answerer` v1 từ chối khi ngữ cảnh không nêu thẳng mốc.
- **Chi phí ngược lại:** pipeline dùng ít token vào hơn (khoảng 93.000 đến 99.000 so với 327.000 đến 372.000 cho 40 câu) nhưng token ra cao do mô hình suy luận ẩn. Số liệu pipeline có 80 lượt gọi cho 40 câu (khoảng 2 lượt mỗi câu, nguyên nhân chưa kiểm chứng, có thể do bước structured output thử lại), nên số token có thể gấp đôi so với ước lượng 1 lượt.
- **Hạn chế khi so:** (a) pipeline chấm bằng `contains` toàn câu trả lời, agent chấm theo dòng Answer; câu trả lời của pipeline ngắn nên chênh không đáng kể; (b) `T_req` oracle làm pipeline có lợi thế (đã trừ Query Profiler); (c) chưa tune prompt `Answerer` cho DeepSeek; prompt agent đã được chỉnh nhiều lần trên chính mẫu seed 1, còn `Answerer` chạy v1 nguyên bản; (d) 40 câu, một lần chạy, chưa có valid hay test_clean; (e) các câu hỏi nêu tên thực thể nên agent dễ tìm đúng trang (mục 11.9 và lời bàn trong phiên).


## 12. Agent tìm đáp án, không tìm chunk; so với pipeline (ghi 2026-11-12)

Agent trả một **câu trả lời**, nên được chấm ở mức đáp án (EM, F1); chunk chỉ là thứ nó đọc để có cơ sở. Pipeline Cơ chế 1 trả danh sách chunk và được chấm ở mức chunk (Hit@k, MRR). Hai con số **không so trực tiếp được**; mốc chung là đáp án cuối: đưa top-k của pipeline cho cùng một LLM sinh đáp án (đã có `Answerer`, `src/tam/generation/answerer.py`) rồi so với đáp án của agent. Đã làm lần đầu trên 40 câu ở mục 11.12.

`scripts/run_agent_search.py` ghi `contains_target` (câu trả lời có chứa chuỗi đáp án) là chỉ số chính và `saw_gold_text` / `gold_text_step` (chuỗi đáp án đã hiện trong văn bản công cụ chưa, ở lượt nào) chỉ để chẩn đoán; `gold_chunk_listed` là chỉ số cũ theo danh sách chunk (lạc quan). Nhãn "chunk đúng" của TimeQA là đoạn **chứa chuỗi đáp án**, không bảo đảm đoạn đó nói về đúng thời kỳ của câu hỏi (`eval/05` mục 7; ví dụ hỏi 2012, chunk gold nói về 2018), nên `saw_gold_chunk` cao không có nghĩa agent đã có bằng chứng đúng thời điểm, và agent có thể trả đúng từ một đoạn khác của trang. `contains_target` là so khớp thô (câu 3 của lần chạy 20 câu trả đúng nhưng bị chấm trượt vì đáp án chuẩn viết `Dakar , Senegal`); cách chấm sẽ làm sau theo người dùng.

## 13. Cách tính điểm đề xuất (ghi 2026-11-12, chưa làm)

Ba tầng riêng, không gộp thành một con số, để giải thích được **vì sao** một cách hơn cách khác:

1. **Đúng/sai (chất lượng đáp án):** 3 mức: đúng 1, đúng một phần 0,5 (nhiều giá trị mà nêu thiếu, hoặc nêu đúng nhưng không chốt), sai hoặc không trả lời 0. Chạy `contains` thô làm sàn, rồi LLM judge nhận gold và câu trả lời (dùng mô hình **khác** mô hình đang đánh giá để tránh thiên vị), và kiểm tay trên một mẫu nhỏ để biết judge lệch bao nhiêu. Báo riêng: tỉ lệ không trả lời, tỉ lệ từ chối sai (có đoạn gold trong tay mà vẫn từ chối), tỉ lệ sai tự tin (trả lời `inferred` mà sai). Với câu có nhiều giá trị đúng trong khoảng hỏi (câu 5, 16), gold chỉ có một giá trị; cần quyết định chấm theo gold hay theo thực tế (mặc định: đúng nếu chứa gold và thông tin thừa đúng sự thật).
2. **Chất lượng bằng chứng:** đoạn chứa đáp án có trong văn bản công cụ trả về không (`saw_answer_text`, theo mục 11.5), lượt đầu tiên thấy; câu đúng mà không thấy đoạn gold tính là đúng do may; nhãn `Type` (stated, inferred, cannot be determined) so với đúng sai thực; kiểm tay rằng căn cứ trích dẫn có chứa điều agent nói. Gán nguyên nhân cho câu sai theo từng bước: không tìm thấy đoạn, thấy đoạn nhưng suy luận sai, đòi khớp đúng ngày, hết lượt.
3. **Chi phí (trục riêng, không trộn vào điểm):** số lượt LLM, token vào/ra/cache, thời gian mỗi câu (p50, p90), chi phí theo giá niêm yết, và chi phí trên mỗi câu đúng.

**So công bằng với pipeline:** cho cùng một LLM sinh đáp án từ top-k chunk của pipeline (`Answerer`) rồi chấm bằng thang tầng 1; Hit@k và MRR của pipeline là số phụ để đối chiếu với tầng 2. **Cỡ mẫu:** 20 câu chỉ là chạy thử (lệch một câu là 5 điểm phần trăm; cùng prompt P3, câu 15 ra đúng một lần và sai một lần); mỗi biến thể cần lặp nhiều lần cùng seed để biết dao động, rồi mở rộng lên 60 đến 100 câu cho biến thể thắng.
