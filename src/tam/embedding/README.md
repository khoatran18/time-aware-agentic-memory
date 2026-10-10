# `tam.embedding`: text → vector (dense + sparse)

**Vị trí trong pipeline:** hạ tầng cho **Ingestion** (embed chunk khi `upsert`) và **Retrieval** (embed câu hỏi khi `search`). Không ai gọi trực tiếp: chỉ `stores/vector/qdrant_store.py` dùng, qua ABC `Embedder`.

## Các file

| File | Việc |
|---|---|
| `base.py` | Ba ABC + `SparseVec`. `DenseEmbedder`, `SparseEmbedder`: hợp đồng cho **provider**. `Embedder`: hợp đồng cho **store** |
| `registry.py` | Hai dict `DENSE_PROVIDERS` / `SPARSE_PROVIDERS` (tên → **class**); decorator `@register_dense("tên")`, `@register_sparse("tên")` |
| `factory.py` | `get_embedder(cfg)`, `get_dense`, `get_sparse`; lớp `HybridEmbedder` ghép dense + sparse |
| `providers/__init__.py` | Import từng file provider để decorator chạy (thiếu dòng import thì registry rỗng) |
| `providers/fastembed.py` | `FastEmbedDense` (vd `BAAI/bge-small-en-v1.5`, dim 384), `FastEmbedSparse` (`Qdrant/bm25`); chạy local bằng ONNX |

## Thứ tự vận hành

Quy ước: mỗi khối = một file (đánh số); node = `Class.hàm` hoặc tên hàm; mũi tên có **số thứ tự** và **tên dữ liệu** truyền đi; `↻` = lặp; một node có thể có nhiều mũi tên vào/ra.

```mermaid
flowchart TD
    subgraph B1["1. providers/__init__.py"]
        P0["import fastembed"]
    end
    subgraph B2["2. registry.py"]
        R1["register_dense / register_sparse"]
        R2["_register.deco"]
        R3["DENSE_PROVIDERS, SPARSE_PROVIDERS"]
    end
    subgraph B3["3. providers/fastembed.py"]
        D1["FastEmbedDense.from_profile"]
        D2["FastEmbedDense.__init__"]
        D3["FastEmbedDense.embed, embed_query"]
        S1["FastEmbedSparse.from_profile"]
        S2["FastEmbedSparse.__init__"]
        S3["FastEmbedSparse.embed, embed_query"]
    end
    subgraph B4["4. factory.py"]
        F1["get_embedder"]
        F2["get_dense"]
        F3["get_sparse"]
        F4["_profile"]
        F5["_build"]
        F6["HybridEmbedder.__init__"]
        F7["HybridEmbedder.embed_dense, embed_sparse, embed_dense_query, embed_sparse_query"]
    end
    ST["5. stores.vector: QdrantStore.upsert, search"]

    P0 -->|"1. import file provider"| R1
    R1 -->|"2. tên provider, rồi class"| R2
    R2 -->|"3. ghi CLASS vào dict (chưa tạo đối tượng)"| R3

    F1 -->|"4. cfg"| F2
    F2 -->|"5. role = dense"| F4
    F4 -->|"6. profile dict (provider, model_id)"| F5
    F5 -->|"7. tra provider"| R3
    R3 -->|"8. class FastEmbedDense"| F5
    F5 -->|"9. gọi from_profile(profile)"| D1
    D1 -->|"10. model_id, cache_dir"| D2
    D2 -->|"11. FastEmbedDense (nạp model, có dim)"| F2
    F1 -->|"12. ↻ lặp bước 5-11 với role = sparse"| F3
    F3 -->|"13. dùng lại F4, F5, SPARSE_PROVIDERS, rồi S1, S2"| S1
    S1 --> S2
    F2 -->|"14. DenseEmbedder"| F6
    F3 -->|"15. SparseEmbedder"| F6
    F6 -->|"16. HybridEmbedder (dense_dim)"| ST

    ST -->|"17. ↻ mỗi upsert/search: texts hoặc câu hỏi"| F7
    F7 -->|"18. dense: embed, embed_query"| D3
    F7 -->|"19. sparse: embed, embed_query"| S3
    D3 -->|"20. list vector float"| ST
    S3 -->|"21. list SparseVec"| ST
```

- Bước 1-3 xảy ra **lúc import** (đăng ký class). Bước 4-16 xảy ra **một lần** ở điểm vào (nạp model). Bước 17-21 lặp **mỗi lần** ghi hoặc tìm kiếm.
- `_build` báo lỗi kèm danh sách provider hiện có nếu `provider` chưa đăng ký.

## Pattern

**Registry + Factory + Strategy (ABC).** Cấu hình chọn provider bằng tên, factory không có danh sách provider, nên thêm provider **không sửa factory hay store**.
- Dense và sparse chọn **riêng** vì không phải provider nào cũng có cả hai (OpenAI chỉ có dense; BM25 vẫn chạy local).
- Tài liệu và câu hỏi có hàm embed riêng (`embed` vs `embed_query`) vì một số model xử lý câu hỏi khác tài liệu.
- Hai tầng ABC: store chỉ biết `Embedder`, không biết provider nào đứng sau.

**Thêm provider mới:** viết class kế thừa `DenseEmbedder` (hoặc `SparseEmbedder`) trong `providers/<tên>.py` + `@register_dense("<tên>")`; thêm một dòng import vào `providers/__init__.py`; thêm profile vào `embedding.profiles.dense`; đổi `embedding.dense`. Đổi model dense làm đổi số chiều → `ensure_collection(recreate=True)`.

## Input / Output

| Hàm | Vào | Ra |
|---|---|---|
| `get_embedder(cfg)` | `Config` | `HybridEmbedder` (có `dense_dim`) |
| `embed_dense(texts)` | `list[str]` | `list[list[float]]` (cùng thứ tự) |
| `embed_sparse(texts)` | `list[str]` | `list[SparseVec]` (`indices`, `values`) |
| `embed_*_query(text)` | một câu hỏi | một vector dense / một `SparseVec` |

Chi tiết: `docs/process/02_CORE_COMPONENTS.md` mục 2.
