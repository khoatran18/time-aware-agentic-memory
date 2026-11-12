# Cấu trúc thư mục hiện tại

Ảnh chụp những gì **đã có trong repo** (không phải cấu trúc đích). Cấu trúc đích và kế hoạch: [`../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md`](../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md) mục 3. Cập nhật file này mỗi khi thêm module mới. Cập nhật lần cuối: 2026-10-09.

```
time-aware-agentic-memory/
├── configs/
│   ├── config.dev.yaml          # Môi trường dev (chọn bằng APP_ENV)
│   └── config.prod.yaml
├── src/tam/                     # Package chính; `tam` = Time-Aware Memory
│   ├── config/
│   │   ├── loader.py            #   .env + yaml + ${VAR} -> Config
│   │   └── logging.py           #   setup_logging(), thư mục output theo lần chạy
│   ├── schemas/                 #   Hình dạng dữ liệu (pydantic, không logic)
│   │   ├── chunk.py             #     Chunk
│   │   ├── query.py             #     ProfiledQuery
│   │   └── result.py            #     ScoredChunk, RetrievalResult
│   ├── embedding/               #   Text -> vector (dense + sparse)
│   │   ├── base.py              #     ABC: DenseEmbedder, SparseEmbedder, Embedder
│   │   ├── registry.py          #     Tên provider -> class, decorator @register_dense/@register_sparse
│   │   ├── factory.py           #     get_embedder(cfg), HybridEmbedder
│   │   └── providers/
│   │       └── fastembed.py     #     FastEmbedDense, FastEmbedSparse
│   ├── llm/                     #   Tạo chat model theo profile và role
│   │   ├── registry.py          #     Tên provider -> hàm build, decorator @register_llm
│   │   ├── factory.py           #     get_llm(cfg, name), get_llm_for_role(cfg, role)
│   │   └── providers/
│   │       ├── _common.py       #     Hàm kiểm tra dùng chung (require, model_id)
│   │       ├── anthropic.py
│   │       ├── openai.py
│   │       └── ollama.py
│   ├── retrieval/
│   │   ├── base.py              #     ABC Retriever (hợp đồng chung 3 cơ chế)
│   │   └── temporal/            #     Cơ chế 1, thuần Python, không import langchain
│   │       ├── scoring.py       #       Temporal_Score (TH1/TH2), Final_Score
│   │       ├── fusion.py        #       RRF + min-max -> Semantic_Score
│   │       ├── filters.py       #       ProfiledQuery -> VectorFilter, passes_hard_filter
│   │       └── retriever.py     #       TemporalRetriever
│   └── stores/
│       └── vector/
│           ├── base.py          #     ABC VectorStore, VectorFilter, SearchHit, BranchHits
│           └── qdrant_store.py  #     QdrantStore (collection dense + BM25, 4 payload index)
├── tests/                       # Pytest; test Qdrant đánh dấu `qdrant`, tự skip nếu không có server
│   ├── conftest.py
│   ├── test_config.py, test_schemas.py
│   ├── test_embedding_factory.py, test_llm_factory.py
│   ├── test_qdrant_store.py
│   ├── test_scoring.py, test_fusion.py, test_filters.py, test_temporal_retriever.py
│   └── fixtures/temporal_corpus.json   # 15 chunk, 5 lĩnh vực, 11 case; FakeVectorStore trong conftest.py
├── docs/
│   ├── scope/                   # Phạm vi đồ án
│   ├── design/                  # Thiết kế hệ thống (đóng góp của đồ án)
│   ├── planning/                # Kế hoạch triển khai
│   ├── process/                 # Nhật ký triển khai (thư mục này)
│   ├── research/, dataset/      # Ghi chú nghiên cứu, dataset
│   └── weekly_reports/
├── dataset/full_dataset/        # Dữ liệu TimeQA enriched (xem EVAL_PLAN.md)
├── docker-compose.yml           # Qdrant (Neo4j để dành cho CC2/3)
├── docker/                      # Dữ liệu volume của container (qdrant_data, neo4j); chưa bị gitignore
├── pyproject.toml               # `pip install -e .`, cấu hình pytest/ruff
├── requirements.txt, requirements-dev.txt
├── .example.env                 # Mẫu biến bí mật; `.env` thật bị gitignore
└── (gitignore) .env, .venv/, output/, data/, local/
```

## Quy tắc phụ thuộc đang áp dụng

```
config  <-  embedding, llm, stores
schemas <-  stores
embedding  <-  stores/vector/qdrant_store   (store chỉ biết ABC `Embedder`, không biết provider nào)
```

`embedding/` và `llm/` giống nhau về cách tổ chức (base → registry → factory → providers, chọn bằng `profiles` trong yaml). Khác nhau: embedding đăng ký **class** vì phải tự định nghĩa ABC; llm đăng ký **hàm** và không có `base.py` vì giao diện đã có sẵn (`BaseChatModel` của langchain-core), các module khác dùng thẳng kiểu đó.

## Chưa có (theo kế hoạch)

`query/profiler.py`, `ingestion/`, `generation/`, `pipeline/`, `agents/`, `tools/`, `baselines/`, `evaluation/`, `scripts/`.

## Bổ sung 2026-11-12: agent search (chưa gộp vào cây ở trên)

Cây ở trên là ảnh chụp 2026-10-09 và đã cũ: thiếu `evaluation/`, `ingestion/`, `generation/`, `query/`, `scripts/` và nhiều test đã có sau đó. Phần dưới chỉ ghi các thư mục và file **mới thêm** cho agent search ([`../planning/02_AGENT_SEARCH_BASELINE.md`](../planning/02_AGENT_SEARCH_BASELINE.md)); chưa dựng lại cả cây.

```
time-aware-agentic-memory/
├── src/tam/
│   ├── tools/                       #   Công cụ cho agent (mới)
│   │   ├── base.py                  #     AgentTool, ToolResult, ToolError
│   │   ├── text_corpus.py           #     Kho text thuần + list_pages, grep, read_page; build_corpus (dựng kho)
│   │   ├── text_tools.py            #     Bộ công cụ kiểu A (mô tả và schema cho LLM)
│   │   └── vector_tools.py          #     Bộ công cụ kiểu B: vector_search, temporal_search, read_chunk
│   ├── agents/                      #   Orchestration (mới; vòng lặp tối giản, không LangGraph)
│   │   └── loop.py                  #     AgentLoop: gọi LLM (streaming), chạy công cụ, trần bước và token; ghi agent_trace.jsonl và agent_calls.jsonl (prompt, câu trả lời, TTFT/TPOT/token) vào thư mục lần chạy
│   └── llm/prompts/                 #   Prompt của agent (A và B dùng chung)
│       ├── agent_v1.md              #     P0: trung tính (đối chứng)
│       ├── agent_v2.md              #     P1: P0 + diễn giải thời điểm, căn cứ, không đoán, không lan man (125 từ)
│       ├── agent_v3.md              #     P2: P1 + khoảng bị cắt ngang nêu từng giá trị + đầu ra Answer/Basis/Type (178 từ)
│       └── agent_v4.md              #     P3: P2 + nới quy tắc căn cứ (ứng viên có căn cứ một phần mốc thì đưa ra, đánh dấu inferred) (219 từ)
├── scripts/build_text_corpus.py     # Dựng data/text_corpus từ pages.jsonl và 3 bộ con (không gọi LLM)
├── scripts/run_agent_search.py      # Chạy agent kiểu A (mặc định) hoặc B (--kind B, kho Qdrant) trên bộ con câu hỏi (GỌI LLM): --prompt, --pick, --workers, --max-steps (mặc định 5), --no-budget-notice, --no-cache, --repeat-id
├── scripts/score_agent_runs.py      # Chấm lại các lần chạy agent đã có (KHÔNG gọi LLM): chấm theo dòng Answer, chia nhóm lỗi (thấy mà không chốt / tìm không ra), ước USD
├── tests/
│   ├── test_text_corpus.py          #   17 test: dựng kho, grep, read_page, list_pages
│   ├── test_vector_tools.py         #   11 test: công cụ B trên kho giả
│   └── test_agent_loop.py           #   27 test: vòng lặp với LLM giả có kịch bản (ScriptedChatModel), báo lượt và ép trả lời, các phiên bản prompt, cache lượt gọi
├── data/                            # gitignore; sinh lại được
│   ├── llm_cache/agent/cache.sqlite #   Cache từng lượt LLM của agent (riêng, tách khỏi data/llm_cache/cache.sqlite của pipeline)
│   ├── text_corpus/                 #   556 file <tên trang>.txt (kho của agent A)
│   └── text_corpus.index.json       #   {page_id: {file, split}}; ngoài thư mục corpus để agent không thấy tên tập
└── docs/planning/02_AGENT_SEARCH_BASELINE.md   # Kế hoạch agent search (đề xuất, chưa chốt)
```

Khác: `src/tam/llm/metrics.py` thêm `stream_collect`; `src/tam/llm/providers/openai.py` thêm khóa profile `stream_usage`; `configs/config.dev.yaml` thêm role `agent`.

Quy tắc phụ thuộc giữ như `00_OVERALL_PLAN.md` mục 3: `retrieval/*` vẫn thuần Python; `tools/` bọc `retrieval/` và `stores/` (B) hoặc kho text (A), không import langchain; chỉ `agents/loop.py` dùng `langchain_core` (tin nhắn, `bind_tools`).

