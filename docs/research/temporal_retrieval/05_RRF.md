# Phân tích bài báo: Reciprocal Rank Fusion (RRF)

## 1. Thông tin chung & Tài nguyên
- **Tiêu đề:** Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods
- **Tác giả:** G. V. Cormack, C. L. A. Clarke (University of Waterloo), S. Büttcher (Google)
- **Công bố:** SIGIR '09, Boston, 19–23/7/2009 (bài ngắn 2 trang, tr. 758–759)
- **DOI:** [10.1145/1571941.1572114](https://doi.org/10.1145/1571941.1572114)
- **PDF (bản tác giả):** [cormacksigir09-rrf.pdf](http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- **Mã nguồn:** Không có (công thức đủ đơn giản để tự cài, xem mục 5).
- **Dataset:** Các tập TREC (Robust 2004, TREC 3/5/9) và LETOR 3.

> Khác với các bài 01–04, đây **không phải bài về thời gian**. Nó là kỹ thuật gộp kết quả nhiều bộ truy xuất, được đồ án dùng để gộp nhánh Dense và BM25 của Hybrid Search (xem `docs/design/02_TEMPORAL_RETRIEVAL_DESIGN.md`, Bước 4a).

## 2. Vấn đề giải quyết
Có nhiều hệ thống truy xuất (ở đồ án: Dense và BM25), mỗi hệ thống trả về một danh sách xếp hạng riêng. Cần gộp thành một danh sách tốt hơn từng danh sách đơn lẻ.

Khó khăn khi gộp theo **điểm**: điểm của mỗi hệ thống có thang đo tùy ý (cosine nằm trong khoảng nhỏ, BM25 không giới hạn trên), nên không cộng trực tiếp được. Bài báo cần một phương pháp **không giám sát** (không cần dữ liệu huấn luyện) và chỉ dùng **thứ hạng**.

## 3. Cơ chế cốt lõi

### 3.1. Công thức
Với tập tài liệu `D` và tập các danh sách xếp hạng `R`, mỗi danh sách `r` là một hoán vị của `1..|D|`:

```
RRFscore(d ∈ D) = Σ_{r ∈ R}  1 / (k + r(d))
```

- `r(d)`: hạng của tài liệu `d` trong danh sách `r` (hạng 1 là tốt nhất).
- `k`: hằng số, bài báo cố định **k = 60**.
- Tài liệu được sắp xếp theo `RRFscore` giảm dần.

Trực giác của tác giả: tài liệu hạng cao thì quan trọng hơn, nhưng tài liệu hạng thấp **không biến mất nhanh** như khi dùng hàm mũ. Hằng số `k` giảm ảnh hưởng của các hạng rất cao do một hệ thống "ngoại lai" gây ra.

### 3.2. Về giá trị k = 60
Trích từ bài báo: `k = 60` được cố định trong một **pilot investigation** và không đổi trong các bước kiểm chứng sau. Đây là lựa chọn thực nghiệm, không có suy dẫn lý thuyết.

Bảng 1 của bài (30 cấu hình Wumpus Search trên TREC topic 351–400) cho thấy MAP theo `k`:

| k | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 | 500 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| MAP | .2072 | .2123 | .2134 | .2139 | .2138 | .2144 | .2145 | .2146 | .2147 | .2145 | .2142 | .2098 |

Nhận xét từ bài và từ bảng:
- Tác giả nói `k = 60` là **gần tối ưu nhưng lựa chọn này không quan trọng** (*near-optimal, but the choice was not critical*).
- MAP phẳng trong khoảng `k = 20–100` (chênh dưới 0.002). Chỉ khi `k = 0` hoặc `k = 500` mới giảm rõ.
- Đỉnh thực tế là `k = 80` (.2147), nhưng chênh với `k = 60` không đáng kể.

### 3.3. So sánh với phương pháp khác trong bài
- **Condorcet Fuse:** gộp bằng bỏ phiếu đa số trên từng cặp tài liệu. Bài cho rằng RRF thắng vì giữ được sự đa dạng giữa các danh sách: một hoặc hai hệ thống xếp một tài liệu rất cao có thể đẩy nó lên đáng kể, trong khi ở Condorcet một đa số yếu có thể lấn át các hệ thống mạnh hơn.
- **CombMNZ:** cộng các điểm gốc chưa chuẩn hóa nhân với số danh sách có chứa tài liệu. Kết quả có phương sai cao hơn RRF.
- **Learning-to-rank** (ListNet, RankSVM, AdaRank…): có giám sát. Trên LETOR 3, RRF tốt hơn tất cả.
- Ưu điểm nêu trong bài: RRF **không cần thuật toán bỏ phiếu đặc biệt hay thông tin toàn cục**; có thể tính tuần tự từng hệ thống và cộng dồn, không phải giữ tất cả danh sách trong bộ nhớ.

## 4. Kết quả
Trên pilot và các tập TREC, RRF hơn Condorcet, CombMNZ và hệ thống đơn lẻ tốt nhất khoảng **4–5%** trung bình (kiểm định sign test, các chênh lệch có ý nghĩa thống kê).

**MAP trên các tập TREC (Bảng 2):**

| Collection | RRF | Best individual | Condorcet | CombMNZ |
| :--- | :--- | :--- | :--- | :--- |
| TREC Robust 2004 | **.3686** | .3586 | .3652 | .3575 |
| TREC 3 | .4350 | .4226 | .4256 | **.4381** |
| TREC 5 | **.3394** | .3165 | .3213 | .3237 |
| TREC 9 | **.2830** | .3519 (.2801) | .2750 | .2671 |

Ghi chú: ở TREC 9, hệ thống đơn lẻ tốt nhất (.3519) dùng người trong vòng lặp (*human-in-the-loop*); hệ thống tự động tốt nhất đạt .2801 và RRF vẫn hơn nó. Ở TREC 3, CombMNZ nhỉnh hơn RRF.

**LETOR 3 (Bảng 3, 583.850 cặp query–document):** RRF đạt MAP 0.6051, hơn Condorcet (0.5917) và hơn các phương pháp learning-to-rank (ListNet 0.5846, RankBoost 0.5622…) với p < .003. CombMNZ nhỉnh hơn RRF một chút (0.6107) nhưng chênh lệch không có ý nghĩa thống kê (p ≈ .2).

## 5. Áp dụng vào đồ án

### 5.1. Dùng ở đâu
Cơ chế 1 (Temporal Retrieval) chạy Hybrid Search với hai danh sách độc lập là Dense và BM25. RRF gộp hai danh sách này thành `Semantic_Score` (sau đó min-max về [0, 1] trước khi trộn với `Temporal_Score`). Không cần train gì thêm, phù hợp phạm vi đồ án.

Cài đặt nhanh:

```python
def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """rankings: mỗi phần tử là danh sách chunk_id đã xếp hạng (hạng 1 đứng đầu)."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores
```

Chunk chỉ có ở một danh sách vẫn được giữ và chỉ nhận một số hạng. Vì thế tập gộp có tối đa `20 + 20 = 40` chunk nếu mỗi nhánh lấy Top-20, thường ít hơn do trùng.

### 5.2. Điều cần ghi chú trong báo cáo
- **`k = 60` là mặc định thực nghiệm, không phải giá trị tối ưu.** Bài gốc nói rõ lựa chọn này không quan trọng (MAP phẳng với `k` từ 20 đến 100). Khi viết thesis, nên trình bày là "dùng mặc định theo Cormack et al. (2009)", và có thể chạy thử vài giá trị `k` như một ablation nhỏ.
- **Bối cảnh bài báo khác đồ án:** bài đánh giá trên tìm kiếm ad hoc (TREC) và learning-to-rank, không phải truy xuất theo thời gian hay RAG. Kết quả 4–5% **không** tự động chuyển sang đồ án; cần đo lại trên dataset của đồ án nếu muốn khẳng định lợi ích.
- **Điểm RRF rất nhỏ** (tối đa `2/(k+1) ≈ 0.0328` với 2 nhánh), nên không dùng trực tiếp với `W1`, `W2`; cần chuẩn hóa về [0, 1] (xem mục 5.3).

### 5.3. Đề xuất (chưa sửa `docs/design/`)
- Trích dẫn Cormack et al. (2009) tại Bước 4a của `02_TEMPORAL_RETRIEVAL_DESIGN.md` làm nguồn cho RRF và `k = 60`.
- Một hướng có thể thử như ablation: coi `Temporal_Score` là **danh sách xếp hạng thứ ba** rồi gộp 3 nhánh bằng RRF, thay vì tính `Final_Score = W1·Semantic + W2·Temporal`. Ưu điểm là bỏ được việc chỉnh `W1`, `W2` và `λ` ảnh hưởng gián tiếp. Nhược điểm là RRF chỉ dùng thứ hạng nên mất thông tin về mức chênh lệch điểm thời gian (TH1 đạt 1.0 so với TH2 giảm dần theo `λ`); đây là nhận xét của tôi, bài báo không bàn tới.
- Min-max trên Top-N làm điểm phụ thuộc vào từng câu hỏi (chunk cuối luôn nhận 0). Đây là lựa chọn thiết kế của đồ án, không thuộc bài báo; nên ghi rõ như vậy.

## 6. Hạn chế của bài báo
- Chỉ 2 trang, đánh giá bằng MAP; các thước đo khác (P@k, R-precision, NDCG) tác giả nói cho kết quả tương đương nhưng không trình bày số liệu.
- Không có phân tích lý thuyết cho `k = 60` hay cho công thức; trực giác của tác giả chưa được chứng minh.
- Dữ liệu 2009, chưa kiểm tra với truy xuất Dense bằng embedding hiện đại.
