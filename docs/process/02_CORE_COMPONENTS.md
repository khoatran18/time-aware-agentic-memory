# Nhật ký triển khai 02: Các thành phần lõi (schemas, embedding, Qdrant store, LLM)

Tiếp nối [`01_BASE_SETUP_CONFIG_LOGGING.md`](01_BASE_SETUP_CONFIG_LOGGING.md). Kế hoạch: [`../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md`](../planning/01_TEMPORAL_RETRIEVAL_IMPLEMENTATION.md) mục 5, bước 1. **Chưa có** scoring/fusion/filters, profiler.

---

## 1. Đã làm được

| Hạng mục | File | Ghi chú |
|---|---|---|
| Đóng gói | `pyproject.toml`, `requirements-dev.txt` | `pip install -e .`; pytest `pythonpath=src`, marker `qdrant` |
| Schemas | `src/tam/schemas/{chunk,query,result}.py` | pydantic, không logic |
| Embedding | `src/tam/embedding/{base,registry,factory}.py`, `providers/fastembed.py` | ABC + registry + factory theo provider, dense và sparse tách riêng |
| Vector store | `src/tam/stores/vector/{base,qdrant_store}.py` | Protocol + Qdrant |
| LLM | `src/tam/llm/{registry,factory}.py`, `providers/{anthropic,openai,ollama}.py` | registry + factory theo profile và role |
| Cấu hình | `configs/config.*.yaml`, `.example.env`, `.env` | thêm `embedding.profiles`, profile LLM `9router`, biến `NINE_ROUTER_*`; sửa `.example.env` (dòng `ANTHROPIC_API_KEY=t` có ký tự thừa) |
| Dependency | `requirements.txt`, `pyproject.toml` | bật `qdrant-client`, `fastembed`, `langchain-core`, `langchain-anthropic`, `langchain-openai`, `langchain-ollama` |
| Test | `tests/test_config.py`, `test_schemas.py`, `test_qdrant_store.py`, `test_embedding_factory.py`, `test_llm_factory.py` | 37 test xanh (6 test Qdrant cần server chạy, nếu không sẽ skip); ruff sạch với rule mặc định đã bật |

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
- **Đăng ký ≠ tạo đối tượng.** `@register_dense("tên")` chạy lúc file provider được import: chỉ ghi **class** vào dict, chưa có đối tượng, `__init__` chưa chạy, model chưa nạp. Model chỉ được nạp khi `get_embedder` gọi `Class.from_profile(profile)`. Vì vậy `providers/__init__.py` phải import từng file provider; thiếu dòng import thì dict rỗng và factory báo "provider chưa hỗ trợ".
- **Thêm provider mới** (ví dụ OpenAI): viết class kế thừa `DenseEmbedder` trong `providers/openai.py` và dán `@register_dense("openai")`; thêm một dòng import vào `providers/__init__.py` (import là lúc decorator chạy); thêm profile vào `embedding.profiles.dense`; đổi `embedding.dense` sang tên profile mới. Không sửa `factory.py` hay `QdrantStore`. Đổi model dense làm đổi số chiều nên phải tạo lại collection (`ensure_collection(recreate=True)`).

### LLM: registry + factory theo profile và role

Config có sẵn từ process 01: `llm.profiles` (tên → `provider`, `model_id`, `api_key`, `temperature`, `base_url`) và `llm.roles` (chỗ dùng → tên profile).

```python
llm = get_llm(cfg, "claude_haiku")          # theo tên profile
llm = get_llm_for_role(cfg, "generation")   # tra roles -> profile -> chat model
```

- `registry.py`: dict `LLM_PROVIDERS` (tên provider → **hàm** `build(profile)`) và decorator `@register_llm("tên")`. Khác embedding ở chỗ đăng ký hàm chứ không phải class, vì không cần lớp riêng: kết quả hàm đã là `BaseChatModel` của langchain-core, nên `with_structured_output`, `bind_tools` dùng được bất kể provider.
- `providers/{anthropic,openai,ollama}.py`: mỗi file một hàm `build` dán `@register_llm`. `providers/_common.py` có `require` (thiếu hoặc rỗng thì báo lỗi) và `model_id` (từ chối giá trị mẫu `<điền model id>`).
- `factory.py`: tra profile theo tên, tra registry theo `provider`, gọi hàm build. Mọi lỗi cấu hình đều có tiền tố `llm.profiles.<tên>`; lỗi chỉ báo khi profile **thực sự được dùng**, nên chỉ có key của một provider vẫn chạy được.
- **Thêm provider mới:** viết `providers/<tên>.py` với hàm `build` dán `@register_llm("<tên>")`, thêm một dòng import vào `providers/__init__.py`, thêm profile vào yaml.
- **9router** (proxy tương thích OpenAI) dùng lại provider `openai` với `base_url`, không cần code mới. Profile `9router` có trong `llm.profiles` của dev và prod, `model_id` đang để mẫu (`<điền ...>`) nên dùng sớm sẽ báo `model_id chưa điền`; chưa gán cho role nào. URL mặc định `http://localhost:20128/v1` và tên model/combo chưa kiểm chứng, cần đối chiếu dashboard 9router.
- **Đọc nội dung trả lời bằng `message.text`, không dùng `message.content`:** `.content` có thể là `str` hoặc danh sách khối (Claude khi có tool call/thinking), còn `.text` luôn là `str` đã ghép. Mọi model đều có `invoke`, `ainvoke`, `with_structured_output`, `bind_tools`; việc structured output/tool calling chạy được hay không còn tùy model phía sau (nhất là qua router), cần thử khi làm profiler.
- **Tiêm phụ thuộc:** `profiler`, `generation`, `time_extraction` nhận LLM qua tham số; chỉ chỗ lắp ráp (`pipeline/builder.py`, `scripts/*`) gọi `get_llm_for_role`. Hàm nhận `cfg` tường minh, không đọc config toàn cục.
- **Chưa làm:** log mỗi lệnh gọi LLM (role, profile, độ trễ, số token) theo kế hoạch §4.3; sẽ bọc bằng callback khi có chỗ gọi LLM thật. Chưa gọi API thật nào (không cần key để chạy test).

### Lưu ý khi dùng

- **Chưa có chỗ nào trong code ứng dụng gọi `get_embedder`, `get_llm`, `QdrantStore.from_config`**; hiện chỉ test và script thử gọi. Điểm vào (`scripts/ingest.py` hoặc `pipeline/builder.py`) sẽ làm: `load_config()` → `get_embedder(cfg)` → `QdrantStore.from_config(cfg, embedder)` → `get_llm_for_role(cfg, ...)`.
- **Cache model fastembed** mặc định nằm ở thư mục tạm của hệ thống nên có thể phải tải lại sau khi khởi động máy. Đặt `cache_dir` (vd `data/models`) trong profile để cố định; mẫu đã có sẵn dạng comment trong yaml.
- **Tốc độ embedding** (đo trên máy 16 luồng CPU, chunk ~200 từ): nạp model ~1 giây khi đã có cache; dense ~30 chunk/giây; BM25 gần như tức thì; một câu hỏi ~3 ms. Lần đầu cần mạng để tải model (~20 giây).
- **Embedding qua 9router** (endpoint `/v1/embeddings`, theo mô tả cộng đồng, chưa kiểm chứng) chỉ có dense, không có BM25. Chưa viết provider; chỉ nên cân nhắc nếu recall ở bộ local thấp. Cần lưu ý: tốn quota, dữ liệu gửi ra ngoài, baseline phải dùng cùng embedding, và router fallback đổi model sẽ làm vector cũ/mới không so sánh được.
- **Chất lượng embedding hiện tại** (`bge-small-en`, tiếng Anh, giới hạn ~512 token) chưa được đo; quyết định nâng cấp dựa trên recall@N ở bộ local sau khi có ingestion. Dữ liệu tiếng Việt cần model đa ngữ.
- **`docker/`** (dữ liệu volume của Qdrant/Neo4j) chưa bị `.gitignore`, có nguy cơ commit nhầm.
- **Quy ước code:** mọi hàm/class trong `src/` có docstring một dòng; chỗ khó hiểu (lời gọi Qdrant, registry) có thêm comment giải thích bước.

## 3. Đã kiểm chứng

Chạy trên Qdrant thật (docker, v1.19.2) với embedder giả tất định (không tải model):

- chỉ có đúng 4 payload index;
- hard filter loại chunk tương lai (`start_time > t_req`) và chunk `invalidated_at != NULL` ở **cả hai nhánh**;
- `exclude_invalidated=False` trả lại chunk bị vô hiệu;
- facet `country` thu hẹp đúng; mốc năm 1850 đi vòng đúng.

`get_embedder` đã chạy thật với `BAAI/bge-small-en-v1.5` (dim 384) và `Qdrant/bm25`. Test Qdrant tự bỏ qua (skip) nếu không có Qdrant ở `localhost:6333`.

**LLM:** test dùng provider giả (`FakeListChatModel`) cho logic factory; ba provider thật được tạo thành công với key giả (không gọi mạng). Với config dev thật: thiếu key báo `llm.profiles.claude_sonnet: thiếu 'api_key' (đặt ANTHROPIC_API_KEY trong .env)`, có key thì ra `ChatAnthropic`.

**Chưa kiểm chứng:** gọi LLM thật qua API; hybrid search với embedding thật trên dữ liệu TimeQA; hiệu năng.

## 4. Việc tiếp theo

1. `retrieval/temporal/`: `scoring.py`, `fusion.py`, `filters.py` + test với fixture `tests/fixtures/laws_2015_2018_2021.json` (hỏi 2020 → bản 2018).
2. `query/profiler.py` (Time Extractor, dùng `get_llm_for_role(cfg, "time_extractor")`).
3. Ingestion TimeQA bộ local.
