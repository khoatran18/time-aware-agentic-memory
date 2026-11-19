# Phân tích bài báo: AT2QA - Let the Agent Search (2603.01853)

## 1. Thông tin chung & Tài nguyên (Links)
- **Tiêu đề:** Let the Agent Search: Autonomous Exploration Beats Rigid Workflows in Temporal Question Answering
- **Tác giả:** Xufei Lv, Jiahui Yang, Haoyuan Sun, Xialin Su, Zhiliang Tian, Yifu Gao, Linbo Qiao, Houde Liu
- **Mã arXiv:** [2603.01853](https://arxiv.org/abs/2603.01853) (đã kiểm tra: tiêu đề và tác giả khớp bài trên trang lacuna)
- **Nguồn đọc thêm:** [lacuna.tiptreesystems.com](https://lacuna.tiptreesystems.com/work/let-the-agent-search-autonomous-exploration-beats-rigid-workflows-in-temporal/wrk_ae17459474e7e876b3c19aeb206f8d7a)
- **Mã nguồn (GitHub):** https://github.com/AT2QA-Official-Code/AT2QA-Official-Code (link do trang arXiv cung cấp; chưa kiểm tra nội dung repo)
- **Datasets (đều dựng trên Temporal KG kiểu ICEWS):**
  - MultiTQ: ~500K QA (theo bài), test 54,584; loại Single/Multiple, Entity/Time.
  - Timeline-CronQuestion: 41,720 QA, test 8,344; Simple/Medium/Complex.
  - Timeline-ICEWS-Actor: 89,372 QA, test 17,874; Simple/Medium/Complex.
  - Link tải dataset: chưa rõ (không đọc được trong bài).

## 2. Vấn đề giải quyết (Problem Statement)
Các hệ thống Temporal KGQA (TKGQA) dùng LLM thường (a) chạy theo **workflow cố định** (phân rã câu hỏi, truy xuất, trả lời theo thứ tự định sẵn) nên khi một bước sai thì không tự sửa được, hoặc (b) phải **post-training** (RL, fine-tune) tốn kém. Bài báo cho rằng chỉ cần để LLM có sẵn tự chọn hành động kế tiếp là đã chạy tốt, ngay cả zero-shot.

> **Ví dụ (minh họa của ghi chú, không phải ví dụ trong bài):** "Sau khi A gặp B lần đầu thì A gặp ai tiếp theo?" Workflow cố định truy xuất một lần với cửa sổ thời gian đoán sai thì kết quả rỗng và hết đường. Agent tự phát hiện rỗng, nới cửa sổ thời gian, tìm lại.

## 3. Cơ chế cốt lõi (Core Mechanisms)

```mermaid
flowchart TD
    Q[Câu hỏi] --> T[LLM: Thought]
    T --> A["Action: Search(q, C)\nC = c_time, c_entity, c_rel"]
    A --> F[Lọc cứng theo C\n(conjunctive filter)]
    F --> R[Dense retrieval\ncosine, top-m, tối đa 10 fact]
    R --> S{Sắp xếp}
    S -->|relevance| O[Observation]
    S -->|time-based| O
    O --> T
    T -->|token kết thúc hoặc T_max=20| ANS[Câu trả lời]
    T -.->|tự sửa: nới cửa sổ thời gian, đổi entity/relation| A
    LOG[(Audit trail:\nthink, action, observation)] -.-> T
```

### 3.1. Một Search tool tổng quát với ràng buộc có cấu trúc
- Tham số: chuỗi truy vấn `q` và `C = {c_time, c_entity, c_rel}`.
  - `c_time`: cửa sổ thời gian đóng [τ_start, τ_end].
  - `c_entity`: giới hạn thực thể (head/tail).
  - `c_rel`: khớp chính xác relation.
- Thứ tự: **lọc cứng trước** (conjunctive filter), sau đó dense retrieval xếp hạng `s(f,q) = cos(enc(f), enc(q))`.
- Hai chế độ sort: theo relevance, hoặc theo thời gian (lấy top-m rồi sắp xếp lại theo trục thời gian).

### 3.2. Vòng lặp agent tự khám phá
- Mỗi bước: `thought` rồi `a_t = Search(q_t, C_t)`; dừng khi có token kết thúc hoặc đạt `T_max`.
- Tự sửa lỗi = đổi ràng buộc (vd nới cửa sổ thời gian) chứ không cần module riêng.

### 3.3. Experience mining (training-free, kiểu GRPO)
1. Lấy mẫu G trace cho mỗi câu hỏi trong mini-batch.
2. Reward nhị phân (exact match), chỉ giữ trace đúng.
3. LLM xếp hạng trace theo giá trị hướng dẫn và chưng cất thành các "advantage experience".
4. Mỗi ứng viên được kiểm bằng mức tăng trên validation; giữ top **K = 3** làm thư viện few-shot.
- Bài không nêu giá trị N, G (chưa rõ).

### 3.4. Audit trail
Log từng think, action, observation thành chuỗi bằng chứng kiểm tra được. Bài không báo cáo chỉ số định lượng cho audit.

### Cấu hình triển khai (đọc trực tiếp)
- LLM: DeepSeek-V3.2, decoding mặc định của server (temperature 1.0).
- Embedding: GLM-Embedding-3 (256 chiều), tính offline; brute-force cosine trên tập đã lọc, tối đa 10 fact mỗi lần gọi.
- T_max = 20, K = 3.
- Chi phí: AT2QA dưới 150 USD trên MultiTQ, dưới 50 USD trên TimelineKGQA; training-free GRPO dưới 7 USD mỗi dataset.

## 4. Kết quả chính (Hits@1 = exact match)

**MultiTQ (Overall / Multiple / Single / Entity / Time):**

| Method | Overall | Multiple | Single | Entity | Time |
|---|---|---|---|---|---|
| AT2QA | 0.887 | 0.751 | 0.942 | 0.864 | 0.945 |
| Temp-R1 | 0.780 | 0.550 | 0.888 | 0.714 | 0.969 |
| PoK | 0.779 | 0.409 | 0.929 | 0.696 | 0.962 |
| RTQA | 0.765 | 0.424 | 0.902 | 0.692 | 0.942 |
| MemoTime | 0.730 | 0.459 | 0.829 | 0.677 | 0.846 |

Hơn SOTA trước +10.7 Overall và +20.1 ở Multiple.

**TimelineKGQA (Overall):** CronQuestion 0.754 (Temp-R1 0.705, +4.9); ICEWS-Actor 0.754 (Temp-R1 0.642, +11.2). Câu Complex: AT2QA 0.803 / 0.768; baseline RAG 0.009 / 0.011.

**Ablation (MultiTQ, Table 3):**

| Cấu hình | Hits@1 |
|---|---|
| LLM only, không search | 0.100 |
| RTQA (workflow cứng) + base tool | 0.762 |
| RTQA + advanced tool | 0.767 |
| Tự chủ, zero-shot, base tool | 0.791 |
| + giới hạn thời gian (time limit) | 0.817 |
| + time-aware sorting | 0.814 |
| + entity filter | 0.795 |
| + relation filter | 0.799 |
| Tự chủ, zero-shot, advanced tool | 0.844 |
| + demonstrations (training-free GRPO) | 0.887 |

Bài quy: autonomy cho +7.7 so với RTQA cùng tool; demonstrations cho +4.3. Trong các ràng buộc, `time limit` là thành phần đơn lẻ tăng nhiều nhất (0.791 lên 0.817).

**Ngân sách vòng lặp:** đã vượt SOTA trước ở T_max = 8; tốt nhất quanh 19 vòng, sau đó giảm dần lợi ích.
**Độ sâu top-k (700 câu):** top-10 0.898, top-15 0.898, top-20 0.904, top-30 0.906 (dùng top-10).
**Backbone zero-shot (advanced tool):** DeepSeek V3.2 0.844; DeepSeek-R1 0.842; Qwen3-Max 0.793; Kimi-2.5 0.789; tất cả vượt SOTA 0.780.
**Embedding (500 câu):** text-embedding-3-large 0.883, 3-small 0.892, gemini-embedding-001 0.889, Baidu-Embedding-V1 0.877 (chênh lệch nhỏ).
**Tự sửa lỗi (Appendix B):** với câu Complex nhiều đích và hơn 3 vòng, khoảng 32% ca thành công chỉ tìm thấy Gold Fact sau mốc 50% quỹ đạo.
**Phân tích lỗi (Appendix C):** trên CronQuestion nhiều "lỗi" là đáp án đúng nhưng bị phạt do single-gold EM (Simple 371/406 = 91.4%; Medium 226/1,012 = 23.0%).

**Hạn chế (bài tự nêu):** độ trễ và chi phí cao hơn RAG một lượt (tối đa 20 vòng); có thể lặp vòng khi câu hỏi mơ hồ hoặc nhiều distractor; nhạy với decoding randomness và tiêu chí dừng; không báo cáo số bước trung bình và token mỗi câu; một số ablation chạy trên subset.

## 5. Áp dụng vào đồ án

### Liên hệ đồ án
Lưu ý phạm vi: AT2QA chạy trên **Temporal KG dạng fact** (sự kiện ICEWS), không phải văn bản Wikipedia/luật. Kết luận cần chuyển đổi, không áp trực tiếp.

1. **Agent tự đọc docs rồi tự quyết định.** Kết quả "tự chủ > workflow cứng" (0.791 so với 0.762 cùng tool; 0.844 so với 0.767) ủng hộ việc để agent của đồ án tự đọc tài liệu truy xuất về, tự đánh giá đủ chưa và tự truy vấn lại, thay vì Routing Agent chốt một cơ chế rồi chạy một lượt. Tương ứng Layer 2 (Routing Agent) trong `docs/design/01_INITIAL_BASE_DESIGN.md`: có thể coi route là gợi ý đầu tiên, agent vẫn được đổi tool giữa chừng.
2. **Chọn tool search vector/graph.** Bài chỉ có **một** tool tổng quát với tham số ràng buộc, không có tool vector và graph riêng. Với đồ án: tool vector (Cơ chế 1, VectorDB, hybrid dense + BM25) và tool graph (Cơ chế 2/3, GraphDB, Evolution edge) có thể tách thành hai tool, nhưng nên giữ chung giao diện tham số (`query`, cửa sổ thời gian, lọc entity/domain) để agent dễ học. Phần "graph" của bài (relation filter `c_rel`) tăng không nhiều (0.795 và 0.799 so với 0.791 base), nên đừng kỳ vọng nhiều từ filter relation đơn lẻ; điều này chỉ là quan sát trên benchmark của bài.
3. **Cửa sổ thời gian `T_req`.** `c_time` là cửa sổ [τ_start, τ_end] áp dụng như hard filter trước dense retrieval, tương tự hard filter `start_time <= T_req` trong Cơ chế 1. Khác biệt cần chú ý: (a) bài cho agent **tự đặt và nới** cửa sổ qua các vòng; đồ án nên cho tool nhận `T_start/T_end` (hoặc `T_req` điểm) và để agent nới khi kết quả rỗng, nhưng **vẫn giữ chặn no-future-leakage** ở tầng tool, không để agent tự bỏ; (b) `T_req` tương đối vẫn do server clock `T_now` đổi ra tuyệt đối trước khi agent gọi tool; (c) trong số ràng buộc, time limit đóng góp lớn nhất (+2.6 điểm trong Table 3), phù hợp việc ưu tiên time filter trong thiết kế.
4. **Time-aware sorting.** Chế độ sort theo thời gian (top-m rồi sắp xếp chronological) gần với Cơ chế 2 (timeline) hơn là Cơ chế 1; trong bài nó không tăng thêm so với time limit (0.814 so với 0.817), nên có thể tùy chọn.
5. **Thư viện few-shot từ trace thành công.** Experience mining (K = 3, reward EM, chi phí dưới 7 USD/dataset) là cách rẻ để cải thiện prompt agent mà không fine-tune, +4.3 điểm trong bài. Có thể áp dụng cho bộ câu hỏi eval của đồ án; cần tuân quy tắc cache LLM của repo (mọi lần gọi qua `SqliteCache`, chỉ chạy một lần mỗi cấu hình).
6. **Audit trail.** Log thought/action/observation khớp với nhu cầu giải thích trong Layer 4 (Time-CoT) và có thể dùng làm bằng chứng cho báo cáo; đồ án nên lưu cả `Chunk_ID` được trả về mỗi bước.
7. **Ngân sách và rủi ro.** Đặt `T_max` (bài: 20, đã vượt SOTA từ 8), có tiêu chí dừng để tránh lặp; báo cáo thêm số bước và token mỗi câu (bài không báo cáo), vì đồ án đã có tiêu chí token efficiency.
8. **Lưu ý đánh giá.** Single-gold EM phạt đáp án đúng khác dạng (Appendix C); khi chấm bộ eval của đồ án nên cân nhắc chấm bằng LLM hoặc nhiều gold.

### Điểm chưa phù hợp / cần thận trọng
- Chưa có xử lý **Evolution vs Falsehood** (`end_time` vs `invalidated_at`) hay conflict nguồn trong bài; AT2QA không giải quyết Cơ chế 3.
- Dữ liệu là fact có cấu trúc sẵn, không có bước ingestion từ văn bản (structural chunking, content hashing).
- Hệ thống đánh giá bằng Hits@1; số liệu của bài không so sánh trực tiếp được với EM/F1 của đồ án.
