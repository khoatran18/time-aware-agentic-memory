# Báo cáo tuần 5

Tuần này **chia bộ data thành các tập train, valid, test và test lại các cấu hình của Temporal Retrieval theo đúng vai trò từng tập**. Các bước đã làm:
1. Chia bộ data thành ba tập không trùng trang: train (tune), valid và test (test_clean).
2. Chạy 888 cấu hình đã thử trước đó trên tập train, rồi xác nhận các cấu hình tốt trên tập valid.
3. Quét tham số quanh ba cross-encoder (240 cấu hình) trên tập train, xác nhận trên tập valid.
4. Chạy một lần trên tập test với danh sách cấu hình chốt trước, kể cả Plain RAG.
5. Thêm bước sinh đáp án bằng LLM, chọn prompt trên tập valid, rồi test EM/F1 trên tập test.

**Kết quả trên tập test (400 câu, chạy một lần).** Plain RAG là RAG thuần, chỉ tìm theo độ giống nghĩa, không có cơ chế kiểm soát thời gian:

| Hệ thống | `mrr` | `hit@1` | `hit@5` | `ans_valid@5` | `leakage_rate` |
|---|---|---|---|---|---|
| Plain RAG | 0.336 | 0.158 | 0.573 | 0.460 | 89% |
| Plain RAG + cross-encoder bge-reranker-v2-m3 | 0.490 | 0.300 | 0.745 | 0.578 | 88% |
| Temporal Retrieval, không cross-encoder | 0.516 | 0.352 | 0.725 | 0.657 | 0% |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.620** | **0.468** | **0.828** | **0.695** | **0%** |

Temporal Retrieval + bge-reranker-v2-m3 hơn Plain RAG **+0.285 `mrr`** (± 0.018, một sai số chuẩn), và hơn Plain RAG dùng cùng cross-encoder **+0.131**. `leakage_rate` là tỉ lệ câu hỏi mà top-5 có chunk mang nội dung của tương lai so với thời điểm hỏi (ví dụ hỏi về năm 2010 nhưng top-5 có chunk của năm 2011); kỳ vọng là 0%.

Đây là tập chưa dùng để chọn cấu hình nên con số đáng tin.

**Quy ước đọc số.** Các chỉ số tính trên từng câu hỏi rồi lấy trung bình:
- `hit@k`: chunk đúng nằm trong top-k kết quả. Ví dụ `hit@5` = 0.83 nghĩa là 83% câu có chunk đúng trong 5 kết quả đầu.
- `mrr`: trung bình của `1/hạng` chunk đúng (hạng 1 được 1.0, hạng 2 được 0.5, ...).
- `ans_valid@5`: top-5 có chunk vừa chứa chuỗi đáp án vừa **hợp lệ về thời gian** tại thời điểm hỏi.
- `leakage_rate`: như trên.
- "Δ" là chênh lệch `mrr` **ghép cặp theo từng câu** giữa hai cấu hình trên cùng một tập; "± x" là **một sai số chuẩn** của chênh lệch đó. Chênh lớn hơn khoảng 2 sai số chuẩn thì coi là đáng tin, dưới 1 sai số chuẩn thì không phân biệt được với may rủi.

---

## 1. Chia bộ data

Bộ data chia thành ba tập từ TimeQA, **đôi một không trùng trang** (để mô hình không "học thuộc" nội dung một trang rồi gặp lại ở tập khác):

| Tập | Số câu | Số trang | Dùng để làm gì | Được chỉnh theo kết quả? |
|---|---:|---:|---|---|
| Train (tune) | 595 | 203 | chọn và chỉnh tham số, chọn cross-encoder | có, chỉ ở tập này |
| Valid | 399 | 167 | xác nhận các cấu hình đã chọn; chọn giữa các phương pháp | không chỉnh tham số |
| Test (test_clean) | 400 | 186 | số cuối của luận văn, chạy **một lần** | không |

Chia ba tập để tách ba việc: chọn cấu hình (train), kiểm tra việc chọn đó (valid) và báo số cuối (test). Nếu dùng cùng một tập cho cả chọn lẫn báo cáo thì con số cuối bị thổi phồng.

---

## 2. Test các cấu hình trên train và valid

### 2.1. Chạy lại 888 cấu hình cũ

**Cơ chế thời gian của Temporal Retrieval** gồm hai phần. (1) **Lọc cứng:** chỉ giữ chunk có `start_time` không sau thời điểm hỏi, để không dùng thông tin của tương lai. (2) **Điểm thời gian:** `Final = W1·Semantic + W2·Temporal`, trong đó `Temporal = 1.0` nếu chunk còn hiệu lực tại thời điểm hỏi, và nếu chunk đã hết hạn thì giảm dần `exp(−λ·số năm cách)`. Quy trình mỗi câu hỏi: lấy `top_n` ứng viên từ Qdrant (đã qua lọc cứng), chấm `Final`, cross-encoder chấm lại một số ứng viên đầu, rồi trả 5 chunk đầu (top-5).

**888 cấu hình** là toàn bộ các lần chạy trước khi chia tập (đã bỏ cấu hình trùng), không phải một lưới đầy đủ. Mỗi cấu hình là một tổ hợp của:
- **Phương pháp:** Temporal Retrieval hoặc Plain RAG (dense, hybrid dense + BM25, BM25).
- **Cross-encoder:** không có, MiniLM-L6, MiniLM-L12, bge-reranker-v2-m3, jina-reranker-v1-turbo, bge-reranker-base.
- **Cách chấm điểm thời gian:** `time_mode`, `end_mode`, `open_decay`, `decay_from`, `t_unknown`, `w2` (giải thích dưới bảng).
- **Cách đưa cho cross-encoder:** `rerank_top`, `rerank_mode`.
- **Mở rộng ngữ cảnh:** thêm chunk lân cận hoặc cả trang.

Ý nghĩa các tham số chính:

| Tham số | Giá trị | Ý nghĩa |
|---|---|---|
| `time_mode` | `point` | dùng **một mốc** thời điểm hỏi (`t_req`) do Profiler trích từ câu hỏi; chunk được điểm 1.0 nếu còn hiệu lực tại mốc đó |
| | `range` | dùng **cả khoảng** nêu trong câu hỏi (ví dụ "between Sep 2003 and Nov 2004"); chunk có khoảng hiệu lực giao với khoảng hỏi thì được điểm, `binary` = 1.0, `coverage` = tỉ lệ khoảng hỏi mà chunk phủ (ví dụ chunk còn hiệu lực đến tháng 3/2004 chỉ phủ khoảng một nửa khoảng hỏi nên được khoảng 0.5) |
| `end_mode` | `stored` | chunk chưa rõ ngày kết thúc dùng đúng `end_time` đã lưu: `ongoing` (đang còn hiệu lực) được 1.0 mãi, `unknown` (không rõ) coi như hết hạn cuối kỳ của `start` |
| | `open` | `ongoing` và `unknown` đều coi là còn hiệu lực mãi, điểm 1.0 |
| | `decay` | `ongoing` và `unknown` đều giảm nhẹ theo số năm từ `start` đến thời điểm hỏi: `exp(−open_decay·số năm)` |
| | `unknown_decay` | chỉ `unknown` giảm như `decay`; `ongoing` giữ 1.0 |
| `top_n` | 50, 100 | số ứng viên mỗi nhánh (dense, BM25) lấy từ Qdrant sau lọc cứng; sau đó gộp, chấm `Final`, chấm lại bằng cross-encoder và chỉ trả top-5 cuối cùng |
| `rerank_top` | 10 đến 50 | số ứng viên đầu bảng được đưa cho cross-encoder chấm lại |
| `rerank_mode` | `replace` | **thay**: bỏ điểm `Semantic` cũ (điểm xếp hạng ngữ nghĩa lấy từ Qdrant), dùng điểm cross-encoder làm `Semantic` mới: `Semantic_mới = CE` (CE đã chuẩn hóa về [0, 1] bằng min-max) |
| | `mix` | **trộn**: `Semantic_mới = alpha·Semantic_cũ + (1 − alpha)·CE`; ví dụ `alpha` = 0.3 thì 30% điểm cũ, 70% điểm cross-encoder |

Sau khi có `Semantic_mới`, điểm cuối được tính lại: `Final = W1·Semantic_mới + W2·Temporal`.

**Từ train lên valid.** Chạy cả 888 cấu hình trên tập train, xếp theo `mrr`. Không lấy thẳng 50 cấu hình đầu vì chúng phần lớn là biến thể gần giống nhau (khác nhau một tham số nhỏ), nên chọn đa dạng:

| Nhóm | Số cấu hình | Vì sao |
|---|---|---|
| `mrr` cao nhất trong cả 888 | 20 | các cấu hình mạnh nhất tổng thể |
| 5 `mrr` cao nhất của mỗi họ Temporal Retrieval (không cross-encoder, MiniLM-L6, MiniLM-L12, bge-reranker-v2-m3, bge-reranker-base, jina-reranker-v1-turbo) | 5 mỗi họ | so sánh các cross-encoder, kể cả họ không lọt top chung |
| 3 Plain RAG không cross-encoder và 3 Plain RAG có cross-encoder, mỗi nhóm lấy `mrr` cao nhất | 6 | đối chứng, để biết Temporal Retrieval hơn bao nhiêu |

Bỏ trùng còn **51 cấu hình**. "Cao nhất" ở đây luôn là `mrr` trên tập train (trung bình `1/hạng` của chunk đúng, tính trên 595 câu).

**Cross-encoder** là mô hình chấm lại điểm: nhận từng cặp (câu hỏi, chunk) và cho điểm mức khớp, chính xác hơn so sánh embedding riêng lẻ nhưng chậm hơn. Ví dụ với câu "Who coached 1. FC Köln in 2018?", cross-encoder đọc cả câu hỏi lẫn từng chunk trong top-20 rồi xếp lại.

Cấu hình tốt nhất của mỗi họ trên train, đo trên valid (Δ so với Temporal Retrieval không cross-encoder):

| Hệ thống | `mrr` train | `mrr` valid | `hit@5` valid | `ans_valid@5` valid | `leakage_rate` valid | Δ `mrr` valid |
|---|---|---|---|---|---|---|
| Temporal Retrieval + bge-reranker-v2-m3 | 0.619 | **0.566** | 0.771 | 0.673 | 0% | +0.055 ± 0.014 |
| + MiniLM-L12 | 0.591 | 0.559 | 0.748 | 0.673 | 0% | +0.048 ± 0.009 |
| + MiniLM-L6 | 0.586 | 0.557 | 0.748 | 0.668 | 0% | +0.046 ± 0.010 |
| + bge-reranker-base | 0.560 | 0.524 | 0.748 | 0.675 | 0% | +0.014 ± 0.012 |
| + jina-reranker-v1-turbo | 0.556 | 0.520 | 0.730 | 0.675 | 0% | +0.009 ± 0.009 |
| Temporal Retrieval, không cross-encoder | 0.549 | 0.511 | 0.718 | 0.668 | 0% | (Baseline) |
| Plain RAG + bge-reranker-v2-m3 | 0.527 | 0.437 | 0.670 | 0.531 | 87% | −0.074 ± 0.020 |
| Plain RAG | 0.422 | 0.332 | 0.569 | 0.458 | 95% | −0.179 ± 0.018 |

- Ba cross-encoder đầu (bge-reranker-v2-m3, MiniLM-L12, MiniLM-L6) cho thêm khoảng +0.05 `mrr` so với Baseline; bge-reranker-base và jina không hơn Baseline một cách đáng tin.
- Plain RAG rò rỉ 87 đến 95% câu trả lời từ chunk tương lai, kể cả khi thêm cross-encoder.

### 2.2. Quét tham số

Quét ngẫu nhiên cho từng họ cross-encoder (MiniLM-L6, MiniLM-L12, bge-reranker-v2-m3): chạy 80 cấu hình trên tập train (1 cấu hình tốt nhất trong 888 cấu hình, cộng 79 cấu hình bốc ngẫu nhiên giá trị các tham số dưới đây), tổng 3 × 80 = 240 cấu hình, rồi giữ cấu hình có `mrr` train cao nhất của mỗi họ.

| Tham số | Ý nghĩa | Giá trị quét |
|---|---|---|
| `w2` | trọng số điểm thời gian trong `Final = W1·Semantic + W2·Temporal`, `W1 = 1 − W2` | 0.1, 0.2, 0.3, 0.4, 0.5 |
| `decay_lambda` | tốc độ giảm điểm theo số năm cách: `exp(−λ·số năm)` | 0.1, 0.25, 0.5, 1, 2 |
| `t_unknown` | điểm của chunk không có mốc thời gian | 0.05, 0.1, 0.2, 0.3 |
| `end_mode` | cách chấm chunk chưa rõ ngày kết thúc | `unknown_decay`, `decay` |
| `open_decay` | tốc độ giảm điểm của chunk đó | 0.02, 0.05, 0.1, 0.2 |
| `decay_from` | tính khoảng cách từ đầu hay cuối khoảng hiệu lực của chunk | `start`, `end` |
| `time_mode` | cách hiểu thời điểm hỏi | `point`; `range` giao nhau `binary`; `range` theo độ phủ `coverage` |
| `top_n` | số ứng viên lấy từ Qdrant | 50, 100 |
| `rerank_top` | số ứng viên đưa cho cross-encoder | 10, 15, 20, 30, 40 |
| `rerank_mode` | `replace`: dùng điểm cross-encoder thay hẳn điểm `Semantic` cũ; `mix`: trộn hai điểm (công thức ở mục 2.1) | `replace`, `mix` |
| `rerank_alpha` (khi `mix`) | trọng số điểm Semantic cũ; điểm cross-encoder có trọng số `1 − alpha` | 0.3, 0.5, 0.7 |
| `rerank_norm` | cách chuẩn hóa điểm | `minmax`, `zscore` |

Bộ tham số tốt nhất của mỗi họ (theo `mrr` train):

| Tham số | MiniLM-L6 | MiniLM-L12 | bge-reranker-v2-m3 |
|---|---|---|---|
| `w2` | 0.3 | 0.2 | 0.2 |
| `decay_lambda` | 0.1 | 1 | 0.5 |
| `t_unknown` | 0.05 | 0.05 | 0.1 |
| `end_mode` | `unknown_decay` | `unknown_decay` | `decay` |
| `open_decay` | 0.02 | 0.05 | 0.1 |
| `decay_from` | `start` | `end` | `start` |
| `time_mode` | `range`, `coverage` | `range`, `coverage` | `range`, `binary` |
| `top_n` | 50 | 100 | 100 |
| `rerank_top` | 10 | 15 | 30 |
| `rerank_mode` | `mix` (`rerank_alpha` 0.3) | `replace` | `mix` (`rerank_alpha` 0.3) |
| `rerank_norm` | `minmax` | `minmax` | `minmax` |
| `mrr` train | 0.591 | 0.592 | 0.628 |
| `mrr` valid | 0.540 | 0.564 | **0.581** |

---

## 3. Kết quả trên tập test

**Từ valid lên test.** Danh sách 12 cấu hình được chốt trước khi xem kết quả test, chạy một lần trên 400 câu, báo cáo tất cả (0 lỗi):

| Nhóm | Cấu hình | Vì sao |
|---|---|---|
| Plain RAG (5) | dense; hybrid (dense + BM25); dense + MiniLM-L6; dense + MiniLM-L12; dense + bge-reranker-v2-m3 | đối chứng: RAG thuần; thêm cross-encoder để thấy lợi thế của Temporal Retrieval không chỉ do cross-encoder |
| Temporal Retrieval (4) | không cross-encoder; + MiniLM-L6; + MiniLM-L12; + bge-reranker-v2-m3 (tham số sau quét, mục 2.2) | cấu hình chính là bản + bge-reranker-v2-m3 (`mrr` valid cao nhất trong ba bộ); giữ cả hai MiniLM vì chênh với bge trên valid còn sát; bản không cross-encoder để tách đóng góp của cơ chế thời gian |
| Temporal Retrieval, tham số xuất phát (3) | + MiniLM-L6; + MiniLM-L12; + bge-reranker-v2-m3 (trước quét) | xem quét tham số có giúp trên tập test không |

| Hệ thống | `mrr` | `hit@1` | `hit@5` | `ans_valid@5` | `leakage_rate` | Δ so với Plain RAG | Δ so với Temporal Retrieval không cross-encoder |
|---|---|---|---|---|---|---|---|
| Plain RAG | 0.336 | 0.158 | 0.573 | 0.460 | 89% | (Baseline) | −0.181 ± 0.017 |
| Plain RAG hybrid (dense + BM25) | 0.352 | 0.200 | 0.507 | 0.425 | 88% | +0.016 ± 0.013 | −0.164 ± 0.019 |
| Plain RAG + MiniLM-L6 | 0.443 | 0.270 | 0.677 | 0.532 | 89% | +0.107 ± 0.016 | −0.073 ± 0.021 |
| Plain RAG + MiniLM-L12 | 0.452 | 0.282 | 0.685 | 0.530 | 90% | +0.117 ± 0.015 | −0.064 ± 0.020 |
| Plain RAG + bge-reranker-v2-m3 | 0.490 | 0.300 | 0.745 | 0.578 | 88% | +0.154 ± 0.016 | −0.027 ± 0.021 |
| Temporal Retrieval, không cross-encoder | 0.516 | 0.352 | 0.725 | 0.657 | 0% | +0.181 ± 0.017 | (Baseline) |
| Temporal Retrieval + MiniLM-L6 | 0.558 | 0.405 | 0.767 | 0.677 | 0% | +0.222 ± 0.018 | +0.042 ± 0.014 |
| Temporal Retrieval + MiniLM-L12 | 0.563 | 0.395 | 0.802 | 0.680 | 0% | +0.227 ± 0.018 | +0.047 ± 0.016 |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.620** | **0.468** | **0.828** | **0.695** | **0%** | **+0.285 ± 0.018** | **+0.104 ± 0.016** |

Nhận xét:
- **Cơ chế thời gian là đóng góp chính.** Plain RAG rò rỉ 88 đến 90% ở mọi biến thể, kể cả khi thêm cross-encoder; Temporal Retrieval rò rỉ 0%. Không cross-encoder, Temporal Retrieval đã hơn Plain RAG +0.181 `mrr`; cùng cross-encoder thì hơn +0.11 đến +0.13.
- **bge-reranker-v2-m3 hơn rõ hai MiniLM** trên tập sạch: hơn L12 +0.057 ± 0.014 và hơn L6 +0.062 ± 0.015 (khoảng 4 sai số chuẩn). L6 và L12 ngang nhau (+0.005 ± 0.011). Điều này khớp với lựa chọn đã làm trên valid, khi đó chênh mới 1,3 sai số chuẩn.
- **Quét tham số không giúp trên tập test:** so với cấu hình xuất phát, MiniLM-L6 −0.016 ± 0.011, MiniLM-L12 −0.009 ± 0.013, bge-reranker-v2-m3 +0.001 ± 0.011; đều trong sai số.

---

## 4. Đáp án sinh ra: EM/F1

Bước cuối của pipeline: LLM đọc các chunk đã truy xuất rồi trả lời. Đáp án của dataset chỉ là một cụm từ ngắn (ví dụ "Markus Anfang"), nên prompt ép LLM trả đúng cụm từ ngắn nhất lấy từ đoạn văn, hoặc `null` nếu không có đáp án. Các chỉ số:
- **EM (Exact Match):** 1 nếu câu trả lời trùng hoàn toàn với đáp án sau khi chuẩn hóa (chữ thường, bỏ dấu phụ, dấu câu, mạo từ a/an/the), ngược lại 0.
- **F1:** so theo từng từ, ví dụ trả lời "Markus Anfang was the coach" cho đáp án "Markus Anfang" được F1 = 0.67 (EM = 0).
- Từ chối (`null`) tính 0 ở cả hai; tỉ lệ từ chối báo riêng.

**Cách làm.** Mỗi request chứa 4 câu độc lập, mỗi câu kèm 5 chunk (cùng top-5 với các chỉ số truy xuất), LLM trả về JSON. Bốn phiên bản prompt, chi tiết ở [`decisions/03`](../../decisions/03_PROMPT_CHANGELOG.md):

| Prompt | Nội dung |
|---|---|
| v1 | chỉ đưa văn bản chunk. Từ chối (`null`) khi các đoạn không nêu đáp án đúng cho thời điểm hỏi; không đoán, không trả lời cho thời điểm gần đó |
| v2 | v1 + khoảng thời gian `(start – end)` của từng chunk |
| v3 | v1 nhưng **nới điều kiện từ chối**: chỉ từ chối khi không đoạn nào nói về điều câu hỏi hỏi. Nếu có đoạn nêu đáp án với khoảng thời gian chồng lấn hoặc gần nhất thời điểm hỏi (kể cả khi đoạn ghi mốc lỏng hơn câu hỏi: chỉ ghi năm thay vì tháng, khoảng mở, không có ngày) và không đoạn nào mâu thuẫn thì vẫn trả lời |
| v4 | v2 + nới điều kiện từ chối như v3 |

### 4.1. Chọn prompt trên tập valid

Mẫu 100 câu chia đều theo domain, top-5, chạy trên hai hệ thống: Temporal Retrieval + bge-reranker-v2-m3 và Plain RAG + bge-reranker-v2-m3. Mỗi LLM có hai cột EM (một cột mỗi hệ thống) và cột **Δ EM**: chênh lệch EM của prompt so với v1, tính từng câu rồi lấy trung bình, gộp cả hai hệ thống, kèm một sai số chuẩn. Ví dụ Δ EM = +0.031 nghĩa là prompt đó trả lời đúng nhiều hơn v1 trung bình 3,1% số câu.

| Prompt | 3.1: EM Temporal | 3.1: EM Plain RAG + bge | 3.1: Δ EM | 3.5: EM Temporal | 3.5: EM Plain RAG + bge | 3.5: Δ EM |
|---|---|---|---|---|---|---|
| v1 | 0.480 | 0.408 | Baseline | 0.459 | 0.388 | Baseline |
| v2 | 0.480 | 0.398 | −0.005 ± 0.017 | 0.480 | 0.388 | +0.010 ± 0.020 |
| v3 | 0.490 | 0.429 | +0.015 ± 0.015 | 0.469 | 0.398 | +0.010 ± 0.018 |
| v4 | 0.541 | 0.408 | **+0.031 ± 0.023** | 0.469 | 0.378 | +0.000 ± 0.022 |

(3.1 là Gemini 3.1 flash-lite, 3.5 là Gemini 3.5 flash-lite.)

### 4.2. Kết quả trên tập test (Gemini 3.5, top-5, 400 câu)

| Hệ thống | EM v1 | EM v4 | F1 v1 | F1 v4 | Từ chối v1 | Từ chối v4 |
|---|---|---|---|---|---|---|
| Plain RAG | 0.360 | 0.385 | 0.414 | 0.453 | 46.0% | 39.3% |
| Plain RAG + bge-reranker-v2-m3 | 0.432 | 0.453 | 0.494 | 0.525 | 35.0% | 26.8% |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.500** | **0.512** | **0.564** | **0.597** | 28.5% | 19.3% |

Temporal Retrieval hơn Plain RAG và Plain RAG + bge ở cả hai prompt:

| Prompt | Temporal − Plain RAG (EM) | Temporal − Plain RAG + bge (EM) |
|---|---|---|
| v1 | +0.140 ± 0.023 | +0.068 ± 0.020 |
| v4 | +0.128 ± 0.023 | +0.060 ± 0.021 |

v4 so với v1 (ghép cặp): EM tăng +0.013 đến +0.025 (± 0.014 đến 0.017, chưa phân biệt được), F1 tăng +0.031 đến +0.040 (khoảng 2 sai số chuẩn). v4 từ chối ít hơn nhưng trả lời sai nhiều hơn (Temporal: 18.5% lên 26.0%).

Nhận xét:
- **Kết luận chính không phụ thuộc prompt:** Temporal Retrieval hơn Plain RAG khoảng +0.13 EM và hơn Plain RAG + bge khoảng +0.06 EM.
- **Ngữ cảnh ngắn làm lộ lợi thế của truy xuất theo thời gian:** chỉ 68,5% câu của Plain RAG còn đáp án trong 5 chunk, so với 89,2% của Temporal Retrieval; khi đáp án không có trong ngữ cảnh, EM gần bằng 0.
- **Cross-encoder cũng có ích:** Plain RAG + bge hơn Plain RAG +0.07 EM.
- **Nút thắt là bước sinh đáp án:** với v1, 76 đến 85 câu (khoảng 20%) bị từ chối dù đáp án có trong ngữ cảnh; v4 giảm xuống 51 đến 57 câu.
- Khoảng 4% (Temporal) đến 8% (Plain RAG + bge) câu trả lời dựa vào chunk có nội dung sau thời điểm hỏi.

---

## 5. Hạn chế và việc tiếp theo

- Prompt sinh đáp án chọn trên mẫu 100 câu valid nên chỉ phân biệt được khác biệt lớn; LLM từ chối quá nhiều dù đáp án có trong ngữ cảnh. Kết quả test EM/F1 chỉ dùng một LLM (Gemini 3.5).
- `ans_valid@5` mới khoảng 0.70: khoảng 30% câu chưa có chunk vừa chứa đáp án vừa hợp lệ về thời gian trong top-5.
- Cross-encoder chạy sau lọc cứng thời gian nên không cứu được các câu bị lọc cứng loại nhầm.
- Chỉ test trên TimeQA và câu hỏi tại một thời điểm; chưa test Timeline Summarization hay Conflict Resolution.
- Việc tiếp theo: cải thiện prompt để giảm từ chối mà không tăng trả lời sai, rồi chuyển sang các cơ chế còn lại.
