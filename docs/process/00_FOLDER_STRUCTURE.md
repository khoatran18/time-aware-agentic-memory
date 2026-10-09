# Cấu trúc thư mục hiện tại

Ảnh chụp những gì **đã có trong repo** (không phải cấu trúc đích). Cấu trúc đích và kế hoạch: [`../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md`](../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md) mục 3. Cập nhật file này mỗi khi thêm module mới. Cập nhật lần cuối: 2026-10-09.

```
time-aware-agentic-memory/
├── configs/
│   ├── config.dev.yaml          # môi trường dev (chọn bằng APP_ENV)
│   └── config.prod.yaml
├── src/tam/                     # package chính; `tam` = Time-Aware Memory
│   ├── config/
│   │   ├── loader.py            #   .env + yaml + ${VAR} -> Config
│   │   └── logging.py           #   setup_logging(), thư mục output theo lần chạy
│   ├── schemas/                 #   hình dạng dữ liệu (pydantic, không logic)
│   │   ├── chunk.py             #     Chunk
│   │   ├── query.py             #     ProfiledQuery
│   │   └── result.py            #     ScoredChunk, RetrievalResult
│   ├── embedding/               #   text -> vector (dense + sparse)
│   │   ├── base.py              #     ABC: DenseEmbedder, SparseEmbedder, Embedder
│   │   ├── registry.py          #     tên provider -> class, decorator @register_dense/@register_sparse
│   │   ├── factory.py           #     get_embedder(cfg), HybridEmbedder
│   │   └── providers/
│   │       └── fastembed.py     #     FastEmbedDense, FastEmbedSparse
│   ├── llm/                     #   tạo chat model theo profile và role
│   │   ├── registry.py          #     tên provider -> hàm build, decorator @register_llm
│   │   ├── factory.py           #     get_llm(cfg, name), get_llm_for_role(cfg, role)
│   │   └── providers/
│   │       ├── _common.py       #     hàm kiểm tra dùng chung (require, model_id)
│   │       ├── anthropic.py
│   │       ├── openai.py
│   │       └── ollama.py
│   └── stores/
│       └── vector/
│           ├── base.py          #     Protocol VectorStore, VectorFilter, SearchHit, BranchHits
│           └── qdrant_store.py  #     QdrantStore (collection dense + BM25, 4 payload index)
├── tests/                       # pytest; test Qdrant đánh dấu `qdrant`, tự skip nếu không có server
│   ├── conftest.py
│   ├── test_config.py, test_schemas.py
│   ├── test_embedding_factory.py, test_llm_factory.py
│   └── test_qdrant_store.py
├── docs/
│   ├── scope/                   # phạm vi đồ án
│   ├── design/                  # thiết kế hệ thống (đóng góp của đồ án)
│   ├── planning/                # kế hoạch triển khai
│   ├── process/                 # nhật ký triển khai (thư mục này)
│   ├── research/, dataset/      # ghi chú nghiên cứu, dataset
│   └── weekly_reports/
├── dataset/full_dataset/        # dữ liệu TimeQA enriched (xem EVAL_PLAN.md)
├── docker-compose.yml           # Qdrant (Neo4j để dành cho CC2/3)
├── docker/                      # dữ liệu volume của container (qdrant_data, neo4j); chưa bị gitignore
├── pyproject.toml               # `pip install -e .`, cấu hình pytest/ruff
├── requirements.txt, requirements-dev.txt
├── .example.env                 # mẫu biến bí mật; `.env` thật bị gitignore
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

`retrieval/temporal/` (scoring, fusion, filters), `query/profiler.py`, `ingestion/`, `generation/`, `pipeline/`, `agents/`, `tools/`, `baselines/`, `evaluation/`, `scripts/`.
