# Nhật ký triển khai 02: Schemas, embedding và Qdrant store

Tiếp nối [`01_BASE_SETUP_CONFIG_LOGGING.md`](01_BASE_SETUP_CONFIG_LOGGING.md). Kế hoạch: [`../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md`](../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md) mục 5, bước 1. **Chưa có** scoring/fusion/filters, LLM, profiler.

---

## 1. Đã làm được

| Hạng mục | File | Ghi chú |
|---|---|---|
| Đóng gói | `pyproject.toml`, `requirements-dev.txt` | `pip install -e .`; pytest `pythonpath=src`, marker `qdrant` |
| Schemas | `src/tam/schemas/{chunk,query,result}.py` | pydantic, không logic |
| Embedding | `src/tam/embeddings/{base,registry,factory}.py`, `providers/fastembed.py` | ABC + registry + factory theo provider, dense và sparse tách riêng |
| Vector store | `src/tam/stores/vector/{base,qdrant_store}.py` | Protocol + Qdrant |
| Test | `tests/test_config.py`, `test_schemas.py`, `test_qdrant_store.py` | 19 test xanh |

## 2. Quyết định thiết kế

- **Datetime luôn UTC.** `Chunk`/`ProfiledQuery` coi datetime không múi giờ là UTC. Mốc trước 1970 (năm 1850) đã kiểm chứng đi vòng qua Qdrant (payload + range filter) đúng.
- **`Chunk` kiểm tra `end_time >= start_time`.** `invalidated_at` và `end_time` mặc định `None`.
- **Qdrant point id = `uuid5(chunk_id)`** vì Qdrant chỉ nhận UUID/int; `chunk_id` gốc nằm trong payload (không index). Upsert hai lần cùng chunk không tạo bản sao.
- **Payload ghi cả khóa `None`** (`model_dump(mode="json")`) để `IsNullCondition(invalidated_at)` khớp.
- **Đúng 4 payload index:** `start_time`, `invalidated_at` (DATETIME), `domain_features.domain`, `domain_features.country` (KEYWORD). Test so khớp bằng `payload_index_fields()`.
- **Store trả về hai danh sách xếp hạng riêng** (`BranchHits.dense`, `.sparse`), mỗi nhánh đã áp hard filter. RRF (k=60) và min-max sẽ nằm ở `retrieval/temporal/fusion.py`, không dùng fusion của Qdrant, để tự kiểm soát và giải thích được.
- **`VectorFilter`** (t_req, exclude_invalidated, facets) là kiểu trung lập nằm ở `base.py`; chỉ `qdrant_store.build_filter` dịch sang cú pháp Qdrant. `exclude_invalidated=False` dành cho trường hợp cần câu trả lời lịch sử có cảnh báo.
- BM25 dùng `Modifier.IDF` ở sparse vector config (bắt buộc để `Qdrant/bm25` có IDF).

### Embedding: ABC + factory

Cấu hình giống `llm`: `embedding.profiles` định nghĩa các profile chia hai nhóm `dense` và `sparse` (tên → `provider`, `model_id`, tùy chọn `cache_dir`), còn `embedding.dense` và `embedding.sparse` chỉ ghi **tên profile** đang dùng. Đổi model = đổi một dòng tên. Dense và sparse chọn riêng vì OpenAI chỉ có dense, BM25 vẫn chạy local.

```yaml
embedding:
  profiles:
    dense:
      bge_small_en: {provider: "fastembed", model_id: "BAAI/bge-small-en-v1.5"}
    sparse:
      bm25: {provider: "fastembed", model_id: "Qdrant/bm25"}
  dense: "bge_small_en"
  sparse: "bm25"
```

```python
embedder = get_embedder(cfg)          # HybridEmbedder, đưa thẳng vào QdrantStore
```

- `base.py`: ba ABC. `DenseEmbedder`/`SparseEmbedder` là hợp đồng cho provider (kế thừa tường minh, thiếu hàm thì lỗi ngay khi tạo); `Embedder` là hợp đồng cho store.
- `registry.py`: hai dict `DENSE_PROVIDERS`/`SPARSE_PROVIDERS` (tên provider → class) và decorator `@register_dense("tên")` / `@register_sparse("tên")` dán lên class.
- `factory.py`: `get_embedder` lấy profile theo tên, tra registry theo `provider`, gọi `Class.from_profile(profile)`, rồi ghép bằng `HybridEmbedder`. Không có danh sách provider trong factory.
- **Thêm provider mới** (ví dụ OpenAI): viết class kế thừa `DenseEmbedder` trong `providers/openai.py` và dán `@register_dense("openai")`; thêm một dòng import vào `providers/__init__.py` (import là lúc decorator chạy); thêm profile vào `embedding.profiles.dense`; đổi `embedding.dense` sang tên profile mới. Không sửa `factory.py` hay `QdrantStore`. Đổi model dense làm đổi số chiều nên phải tạo lại collection (`ensure_collection(recreate=True)`).

## 3. Đã kiểm chứng

Chạy trên Qdrant thật (docker, v1.19.2) với embedder giả tất định (không tải model):

- chỉ có đúng 4 payload index;
- hard filter loại chunk tương lai (`start_time > t_req`) và chunk `invalidated_at != NULL` ở **cả hai nhánh**;
- `exclude_invalidated=False` trả lại chunk bị vô hiệu;
- facet `country` thu hẹp đúng; mốc năm 1850 đi vòng đúng.

`FastEmbedEmbedder` đã chạy thật với `BAAI/bge-small-en-v1.5` (dim 384) và `Qdrant/bm25`. Test Qdrant tự bỏ qua (skip) nếu không có Qdrant ở `localhost:6333`.

**Chưa kiểm chứng:** hybrid search với embedding thật trên dữ liệu TimeQA; hiệu năng.

## 4. Việc tiếp theo

1. `retrieval/temporal/`: `scoring.py`, `fusion.py`, `filters.py` + test với fixture `tests/fixtures/laws_2015_2018_2021.json` (hỏi 2020 → bản 2018).
2. `llm/` factory + `query/profiler.py`.
3. Ingestion TimeQA bộ local.
