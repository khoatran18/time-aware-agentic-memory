# Công thức và chỉ số dùng trong báo cáo tuần 4

Tài liệu đi kèm [`WEEK_4.md`](WEEK_4.md): giải thích các công thức tính điểm và các chỉ số, kèm ví dụ tính tay. Bản đầy đủ của thiết kế: [`design/03`](../../design/03_TEMPORAL_RETRIEVAL_DESIGN_V2.md).

---

## 1. Điểm xếp hạng

Mỗi chunk sau khi qua bộ lọc cứng nhận ba điểm, đều nằm trong [0, 1]:

```text
Final = W1·Semantic + W2·Temporal (+ W3·Domain)       W1 = 0.7, W2 = 0.3, W3 = 0 (mặc định)
```

Chunk có `Final` cao nhất đứng hạng 1.

### 1.1. `Semantic`: chunk giống nghĩa câu hỏi đến đâu

Dense và BM25 mỗi bên cho một danh sách xếp hạng riêng. Điểm thô của hai bên khác thang đo (cosine so với BM25) nên không cộng trực tiếp được, mà dùng **thứ hạng**.

**RRF (Reciprocal Rank Fusion)**:

```text
RRF(d) = Σ_i  w_i / (k + rank_i(d))       k = 60, rank bắt đầu từ 1, w_i là trọng số của danh sách i
```

**Min-max** đưa điểm RRF về [0, 1] trên tập top-N đang xét:

```text
Semantic(d) = (RRF(d) − min) / (max − min)
```

Ví dụ với ba chunk (`w_i = 1`):

| Chunk | Hạng dense | Hạng BM25 | RRF | `Semantic` |
|---|---|---|---|---|
| A | 1 | 3 | 1/61 + 1/63 = 0.0323 | 1.00 |
| B | 2 | — | 1/62 = 0.0161 | (0.0161 − 0.0156)/(0.0323 − 0.0156) ≈ 0.03 |
| C | — | 4 | 1/64 = 0.0156 | 0 |

(Chunk chỉ có ở một danh sách vẫn được giữ.) Sau tuần 4, BM25 bị bỏ (trọng số 0), nên `Semantic` chỉ còn là hạng của dense, vẫn qua min-max.

### 1.2. `Temporal`: chunk khớp thời điểm hỏi đến đâu

`T_req` là thời điểm câu hỏi đề cập tới. Mỗi chunk có `[start_time, end_time]` (`end_time` rỗng nghĩa là còn hiệu lực đến nay). Hai trường hợp:

| Trường hợp | Điều kiện | `Temporal` |
|---|---|---|
| **TH1**: khớp thời điểm | `start_time ≤ T_req ≤ end_time` (hoặc `end_time` rỗng) | **1.0** |
| **TH2**: đã hết hạn | `end_time < T_req` | `exp(−λ·Δ)` |

(Chunk có `start_time > T_req` đã bị loại ở bộ lọc cứng, không đến được bước này.)

### 1.3. `Δ`, `λ` và `exp`: vì sao điểm giảm như vậy

- **`Δ` (delta)** là khoảng cách giữa hai mốc **quy ra năm, có phần thập phân** (không làm tròn): số ngày chia 365.25 (code tính từ số giây chia số giây của một năm Julian). Nó đo chunk đã "cũ" bao lâu so với thời điểm hỏi. Ví dụ cách nhau 90 ngày thì `Δ` = 90/365.25 ≈ 0.25 năm; với `λ = 0.5`, `exp(−0.5·0.25)` ≈ 0.88.
- **`λ` (lambda, `decay_lambda`, mặc định 0.5)** là tốc độ giảm điểm: càng lớn thì chunk cũ bị phạt càng nặng.
- **`exp(−λ·Δ)`** là hàm giảm dần theo cấp số nhân. Với `Δ = 0` thì bằng 1.0 (không phạt), `Δ` càng lớn thì càng gần 0 nhưng không bao giờ âm. Mỗi lần `Δ` tăng thêm `ln 2 / λ` năm (1.39 năm khi `λ = 0.5`) thì điểm giảm đi một nửa.

Bảng `exp(−λ·Δ)` theo `Δ`:

| `λ` \ `Δ` (năm) | 1 | 2 | 5 | 10 |
|---|---|---|---|---|
| 0.5 (mặc định) | 0.61 | 0.37 | 0.08 | 0.007 |
| 0.1 | 0.90 | 0.82 | 0.61 | 0.37 |

**Vì sao chunk hết hạn không bị loại mà chỉ bị giảm điểm:** thông tin cũ vẫn đúng với thời điểm của nó, nhiều khi kho chỉ có bản cũ (hỏi luật 2020 nhưng chỉ có bản 2018), và nhãn `end_time` do LLM gán có thể sai. Giảm điểm theo độ cũ giúp chunk gần `T_req` nhất thắng khi không có chunk đúng thời điểm.

### 1.4. `decay_from`: `Δ` tính từ đâu

`decay_from` nằm trong công thức TH2 và chọn mốc để tính `Δ`:

| `decay_from` | `Δ` |
|---|---|
| `start` (bản gốc) | `T_req − start_time` |
| `end` (sau tuần 4) | `T_req − end_time` |

Ví dụ: chunk "A là HLV 1980 đến 1994", hỏi năm 1995, `λ = 0.5`:

| `decay_from` | `Δ` | `Temporal` |
|---|---|---|
| `start` | 15 năm | `exp(−0.5·15)` = 0.0006 |
| `end` | 1 năm | `exp(−0.5·1)` = 0.61 |

Chunk chỉ hết hạn 1 năm nhưng bị phạt như đã cũ 15 năm nếu tính từ `start`; tính từ `end` hợp lý hơn với các sự việc kéo dài.

### 1.5. `end_mode` và `d`: chunk có `end` không chắc chắn

`end_status` có 3 giá trị: `known` (có ngày kết thúc), `ongoing` (còn tiếp diễn, có câu bằng chứng) và `unknown` (không rõ). Với `ongoing` và `unknown`, ta không chắc chunk đã hết hạn nên có thêm tốc độ giảm nhẹ hơn: `d` = `open_decay` (mặc định 0.1). Ký hiệu `Δ = T_req − start_time`.

| `end_mode` | `ongoing` | `unknown` |
|---|---|---|
| `stored` (mặc định) | 1.0 | 1.0 trong năm của `start`, sau đó `exp(−λ·Δ)` |
| `open` | 1.0 | 1.0 |
| `decay` | `exp(−d·Δ)` | `exp(−d·Δ)` |
| `unknown_decay` | 1.0 | `exp(−d·Δ)` |

Ví dụ chunk `unknown` bắt đầu 2010, hỏi 2017 (`Δ = 7`), `d = 0.1`, `λ = 0.5`:

| `end_mode` | `Temporal` của chunk `unknown` |
|---|---|
| `stored` | `exp(−0.5·7)` = 0.03 (phạt nặng, coi như đã hết hạn) |
| `open` | 1.0 |
| `decay` / `unknown_decay` | `exp(−0.1·7)` = 0.50 |

### 1.6. Chunk không mốc: `t_unknown`

Chunk mà nạp kho Qdrant không nhận ra được `start_time` không thể tính `Δ`, nên nhận `Temporal` cố định `t_unknown` (tốt nhất 0.1). Chúng vẫn được giữ lại vì có thể chứa đáp án.

### 1.7. Ví dụ tính `Final` hoàn chỉnh

Hỏi "Ai là HLV của CLB X năm 1995?", `W1 = 0.7`, `W2 = 0.3`, `λ = 0.5`:

| Chunk | Nội dung | `Semantic` | `Temporal` | `Final` |
|---|---|---|---|---|
| A | HLV 1980 đến 1990 (bản cũ, rất giống câu hỏi) | 1.00 | `Δ = 5` → 0.08 | 0.7·1.00 + 0.3·0.08 = **0.72** |
| B | HLV 1991 đến 1998 (đúng thời điểm) | 0.80 | TH1 → 1.00 | 0.7·0.80 + 0.3·1.00 = **0.86** |

B thắng dù giống nghĩa kém hơn A, nhờ `Temporal`.

### 1.8. Cross-encoder chấm lại

Lấy top-20 theo `Final`, cross-encoder cho mỗi chunk một điểm liên quan từ cặp (câu hỏi, chunk), điểm này được chuẩn hóa min-max trong nhóm 20 chunk rồi **thay** `Semantic` (`replace`) hoặc trộn với `Semantic` (`mix`). `Temporal` giữ nguyên và `Final` được tính lại bằng công thức trên.

---

## 2. Chỉ số đánh giá

Mỗi chỉ số tính trên từng câu hỏi rồi lấy trung bình trên bộ 400 câu.

| Chỉ số | Định nghĩa | Ví dụ |
|---|---|---|
| `hit@k` | Câu hỏi được tính 1 nếu chunk đúng (theo id) nằm trong top-k, ngược lại 0 | `hit@5` = 0.72 nghĩa là 72% câu có chunk đúng trong 5 kết quả đầu |
| `mrr` | `1 / hạng` của chunk đúng (0 nếu không có trong danh sách) | 3 câu có hạng 1, 3 và không có: `(1 + 1/3 + 0)/3 = 0.44` |
| `ans_valid@5` | Top-5 có chunk vừa chứa chuỗi đáp án vừa **hợp lệ về thời gian** tại `T_req` (`start ≤ T_req ≤ end`) | Chunk chứa "Big Hit Entertainment" nhưng bắt đầu từ 2014 khi hỏi 2010: chứa đáp án nhưng không hợp lệ |
| `leakage_rate` | Tỉ lệ câu hỏi mà top-5 có chunk với `start_time > T_req` (nội dung của tương lai) | Hỏi năm 2010 mà top-5 có chunk năm 2011; kỳ vọng 0% |
| `ctx_hit` | Chunk đúng có trong ngữ cảnh đưa cho LLM sinh đáp án (top-5 cộng chunk liền kề) | Chunk liền kề ±1: 0.679 lên 0.772 |

`mrr` thưởng việc đưa chunk đúng lên cao hơn `hit@k`: hạng 1 được 1.0, hạng 2 được 0.5, hạng 5 chỉ được 0.2.

### 2.1. "± x" trong báo cáo: so sánh ghép cặp

Khi so hai cấu hình A và B trên cùng 400 câu, tính **chênh lệch từng câu** `δ_i = mrr_B(i) − mrr_A(i)` rồi lấy:

```text
chênh lệch = trung bình(δ_i)           khoảng 95% = ± 1.96 · (độ lệch chuẩn của δ_i) / √400
```

Nếu khoảng này không chạm 0 thì B hơn A một cách đáng tin; nếu chạm 0 thì chênh lệch nằm trong nhiễu, không kết luận được. Trên bộ 400 câu, chênh dưới khoảng 0.013 đến 0.015 `mrr` là không phân biệt được. Cách này chặt hơn so hai số trung bình riêng lẻ, vì loại được độ khó khác nhau của từng câu.

Ví dụ: "`mrr` +0.088 ± 0.015" nghĩa là chênh lệch trung bình 0.088 và khoảng 95% là [0.073; 0.103], hoàn toàn trên 0.
