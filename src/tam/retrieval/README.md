# `tam.retrieval`: truy xuất time-aware

**Vị trí trong pipeline:** Tầng 3 (Retrieval). Nhận `ProfiledQuery` từ Query Processing, trả `RetrievalResult` cho Generation. Hiện có Cơ chế 1 (`temporal/`); `timeline/` (CC2) và `conflict/` (CC3) sẽ thêm cạnh bên. **Thuần Python, không import langchain/langgraph**: dễ test, dễ giải thích; store được tiêm qua constructor.

## Các file

| File | Việc |
|---|---|
| `base.py` | ABC `Retriever`: `mechanism` + `retrieve(ProfiledQuery) -> RetrievalResult`. Hợp đồng chung của 3 cơ chế |
| `temporal/filters.py` | `to_vector_filter(query)` (kiểm tra facet ∈ `FACET_KEYS` = `{domain, country}`), `passes_hard_filter(chunk, flt)` (kiểm lại bằng Python) |
| `temporal/fusion.py` | `rrf` (k=60), `normalize_minmax`, `fuse(hits, k, top_n)` → `Semantic_Score` ∈ [0,1] |
| `temporal/scoring.py` | `is_exact_match`, `delta_years`, `temporal_score` (TH1/TH2), `final_score` |
| `temporal/retriever.py` | `TemporalRetriever(Retriever)`: ghép các bước trên; `from_config(cfg, store)` |

`filters`, `fusion`, `scoring` là hàm thuần, **không gọi nhau**; chỉ `retriever.py` gọi cả ba nên test riêng từng cái được.

## Thứ tự vận hành (`TemporalRetriever.retrieve`)

Quy ước: mỗi khối = một file (đánh số); node = `Class.hàm` hoặc tên hàm; mũi tên có **số thứ tự** và **tên dữ liệu** truyền đi; `↻` = lặp; một node có thể có nhiều mũi tên vào/ra.

```mermaid
flowchart TD
    IN["ProfiledQuery"]
    subgraph B1["1. temporal/retriever.py"]
        T1["TemporalRetriever.retrieve"]
        T2["_guard"]
        T3["TemporalRetriever._score"]
    end
    subgraph B2["2. temporal/filters.py"]
        F1["to_vector_filter"]
        F2["passes_hard_filter"]
    end
    ST["3. stores.vector: QdrantStore.search"]
    subgraph B4["4. temporal/fusion.py"]
        U1["fuse"]
        U2["rrf"]
        U3["normalize_minmax"]
    end
    subgraph B5["5. temporal/scoring.py"]
        S1["temporal_score"]
        S2["is_exact_match"]
        S3["delta_years"]
        S4["final_score"]
    end
    OUT["RetrievalResult"]

    IN -->|"1. ProfiledQuery"| T1
    T1 -->|"2. query"| F1
    F1 -->|"3. VectorFilter"| T1
    T1 -->|"4. semantic_query, flt, top_n"| ST
    ST -->|"5. BranchHits (dense, sparse)"| T1
    T1 -->|"6. hits, flt"| T2
    T2 -->|"7. ↻ mỗi hit: chunk, flt"| F2
    F2 -->|"8. bool"| T2
    T2 -->|"9. BranchHits đã loại hit vi phạm"| T1
    T1 -->|"10. hits, rrf_k, top_n"| U1
    U1 -->|"11. 2 danh sách chunk_id"| U2
    U2 -->|"12. dict chunk_id: điểm RRF"| U1
    U1 -->|"13. điểm RRF của top_n"| U3
    U3 -->|"14. điểm trong [0,1]"| U1
    U1 -->|"15. list (Chunk, semantic_score)"| T1
    T1 -->|"16. ↻ mỗi chunk"| T3
    T3 -->|"17. chunk, t_req, lambda"| S1
    S1 -->|"18. chunk, t_req"| S2
    S2 -->|"19. TH1 hay không"| S1
    S1 -->|"20. chỉ khi TH2: t_req, start_time"| S3
    S3 -->|"21. delta_years"| S1
    S1 -->|"22. temporal_score"| T3
    T3 -->|"23. semantic, temporal, w1, w2"| S4
    S4 -->|"24. final_score"| T3
    T3 -->|"25. ScoredChunk"| T1
    T1 -->|"26. chỉ để log: đếm TH1 (gọi is_exact_match lại)"| S2
    T1 -->|"27. sort, cắt top_k"| OUT
```

- Bước 4: hard filter chạy **trong DB** trước khi xếp hạng. Bước 6-9 (`_guard`) là chốt chặn: với Qdrant thật không nên loại gì, nếu có thì ghi cảnh báo.
- Bước 17-22: TH1 (`end_time` rỗng hoặc `>= t_req`) trả 1.0 ngay; TH2 mới gọi `delta_years` và tính `exp(-λ·Δyears)`. Chunk có `start_time > t_req` ném `ValueError`.
- Bước 27: sắp theo `final_score` giảm dần; hòa thì `temporal_score` giảm dần, rồi `chunk_id`.
- `filters`, `fusion`, `scoring` không gọi nhau; chỉ `retriever.py` gọi cả ba.

## Pattern

- **Strategy qua ABC `Retriever`:** `tools/`, `pipeline/`, `evaluation/` về sau chỉ phụ thuộc hợp đồng này, không phụ thuộc `TemporalRetriever`.
- **Dependency injection:** `TemporalRetriever(store, w1, w2, decay_lambda, rrf_k, top_n, top_k)`; `from_config` đọc khối `retrieval` của yaml (`w1=0.7, w2=0.3, λ=0.5, rrf_k=60, top_n=50, top_k=5` là mặc định). Ràng buộc: `1 <= top_k <= top_n`.
- **Defense in depth** cho bất biến: hard filter ở DB + `_guard` ở Python + `ValueError` trong `scoring`.
- **Rủi ro đã biết:** min-max nhạy với hòa nghĩa (kho giả 7/11 case, Qdrant thật 11/11); ứng viên thay thế để ablation sau. Xem `docs/process/03_TEMPORAL_RETRIEVAL_CORE.md` mục 3.

## Input / Output

| | Vào | Ra |
|---|---|---|
| `TemporalRetriever.retrieve` | `ProfiledQuery(semantic_query, t_req, filters)` | `RetrievalResult(mechanism="temporal", chunks=list[ScoredChunk])` tối đa `top_k`, mỗi chunk có đủ 3 điểm |
| `fuse` | `BranchHits`, `k`, `top_n` | `list[(Chunk, semantic_score)]` giảm dần |
| `temporal_score` | `Chunk`, `t_req`, `λ` | float ∈ (0, 1] |

Thiết kế thuật toán: `docs/design/02_TEMPORAL_RETRIEVAL_DESIGN.md`.
