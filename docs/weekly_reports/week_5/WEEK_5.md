# Báo cáo tuần 5

Tuần này **chia bộ data thành các tập train, valid, test và test lại các cấu hình của Temporal Retrieval theo đúng vai trò từng tập**. Ở tuần 4, mọi cấu hình đều được chọn ngay trên bộ data 400 câu, nên các con số chỉ là cận trên. Các bước đã làm:
1. Chia bộ data thành ba tập không trùng trang: train (tune), valid và test (test_clean).
2. Chạy lại 888 cấu hình đã thử ở tuần 4 trên tập train, rồi xác nhận các cấu hình tốt trên tập valid.
3. Quét tham số quanh ba cross-encoder (240 cấu hình) trên tập train, xác nhận trên tập valid.
4. Chạy một lần trên tập test với danh sách cấu hình chốt trước, kể cả Plain RAG và các ablation (bỏ từng thành phần).
5. Thêm bước sinh đáp án bằng LLM, chọn prompt trên tập valid, rồi test EM/F1 trên tập test.

**Kết quả trên tập test (400 câu, chạy một lần).** Plain RAG là RAG thuần, chỉ tìm theo độ giống nghĩa, không có cơ chế kiểm soát thời gian:

| Hệ thống | `mrr` | `hit@1` | `hit@5` | `ans_valid@5` | `leakage_rate` |
|---|---|---|---|---|---|
| Plain RAG | 0.336 | 0.158 | 0.573 | 0.460 | 89% |
| Plain RAG + cross-encoder bge-reranker-v2-m3 | 0.490 | 0.300 | 0.745 | 0.578 | 88% |
| Temporal Retrieval, không cross-encoder | 0.516 | 0.352 | 0.725 | 0.657 | 0% |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.620** | **0.468** | **0.828** | **0.695** | **0%** |

Temporal Retrieval + bge-reranker-v2-m3 hơn Plain RAG **+0.285 `mrr`** (± 0.018, một sai số chuẩn), và hơn Plain RAG dùng cùng cross-encoder **+0.131**. `leakage_rate` là tỉ lệ câu hỏi mà top-5 có chunk mang nội dung của tương lai so với thời điểm hỏi (ví dụ hỏi về năm 2010 nhưng top-5 có chunk của năm 2011); kỳ vọng là 0%.

Đây là tập chưa dùng để chọn cấu hình nên con số đáng tin hơn tuần 4 (0.566 trên bộ data 400 câu, là cận trên).

Tài liệu liên quan:
- Kết quả đầy đủ và cách tái lập: [`eval/07`](../../eval/07_TUNE_VALID_RESULTS.md)
- Quyết định chia tập: [`decisions/08`](../../decisions/08_TRAIN_VALID_TEST_SPLIT.md)
- Kết quả trên bộ data 400 câu của tuần 4: [`eval/05`](../../eval/05_REAL_RESULTS.md)

**Quy ước đọc số.** Các chỉ số tính trên từng câu hỏi rồi lấy trung bình:
- `hit@k`: chunk đúng nằm trong top-k kết quả. Ví dụ `hit@5` = 0.83 nghĩa là 83% câu có chunk đúng trong 5 kết quả đầu.
- `mrr`: trung bình của `1/hạng` chunk đúng (hạng 1 được 1.0, hạng 2 được 0.5, ...).
- `ans_valid@5`: top-5 có chunk vừa chứa chuỗi đáp án vừa **hợp lệ về thời gian** tại thời điểm hỏi.
- `leakage_rate`: như trên.
- "Δ" là chênh lệch `mrr` **ghép cặp theo từng câu** giữa hai cấu hình trên cùng một tập; "± x" là **một sai số chuẩn** của chênh lệch đó. Chênh lớn hơn khoảng 2 sai số chuẩn thì coi là đáng tin, dưới 1 sai số chuẩn thì không phân biệt được với may rủi.

---

## 1. Chia bộ data

Bộ data 400 câu của tuần 4 đã được xem kết quả trên hơn 200 cấu hình, nên không còn là tập test sạch. Tuần này chia thêm ba tập mới từ TimeQA, **đôi một không trùng trang** (để mô hình không "học thuộc" nội dung một trang rồi gặp lại ở tập khác):

| Tập | Số câu | Số trang | Dùng để làm gì | Được chỉnh theo kết quả? |
|---|---:|---:|---|---|
| Bộ data 400 câu (tuần 4) | 400 | 204 | tham khảo, cận trên | đã bị chỉnh nhiều |
| Train (tune) | 595 | 203 | chọn và chỉnh tham số, chọn cross-encoder | có, chỉ ở tập này |
| Valid | 399 | — | xác nhận các cấu hình đã chọn; chọn giữa các phương pháp | không chỉnh tham số |
| Test (test_clean) | 400 | — | số cuối của luận văn, chạy **một lần** | không |

- **Train** gồm 400 câu lấy mới và 195 câu của bộ data 400 câu cũ có trang không nằm trong valid hay test (thêm để tập train đủ lớn).
- **Valid** bỏ 1 câu có nhãn thời gian hỏng (`time_start` chỉ có "18"), còn 399 câu.
- Cả ba tập đã nạp kho Qdrant riêng và chạy Profiler (trích thời điểm hỏi từ câu hỏi) đủ số câu, không lỗi.
- Cần ba tập thay vì hai vì ta chọn **hai tầng**: thử hàng trăm cấu hình trên train rồi chọn vài ứng viên. Điểm trên train luôn cao hơn trên tập chưa thấy (ở đây cao hơn khoảng 0.05 đến 0.09 `mrr`), nên valid để kiểm tra việc chọn đó mà không đụng vào test.

---

## 2. Test các cấu hình trên train và valid

### 2.1. Chạy lại 888 cấu hình cũ

Gom toàn bộ cấu hình đã chạy ở tuần 4 (đã bỏ cấu hình trùng): 888 cấu hình, gồm 650 cấu hình Temporal Retrieval không cross-encoder, các cấu hình dùng cross-encoder và 81 cấu hình Plain RAG. Chạy lại cả 888 trên tập train, chọn đa dạng khoảng 50 cấu hình tốt (top theo `mrr` và top từng họ cross-encoder, kể cả Plain RAG) rồi chạy trên valid (56 cấu hình).

**Cross-encoder** là mô hình chấm lại điểm: nhận từng cặp (câu hỏi, chunk) và cho điểm mức khớp, chính xác hơn so sánh embedding riêng lẻ nhưng chậm hơn. Ví dụ với câu "Who coached 1. FC Köln in 2018?", cross-encoder đọc cả câu hỏi lẫn từng chunk trong top-20 rồi xếp lại.

Cấu hình tốt nhất của mỗi họ trên train, đo trên valid (Δ so với Temporal Retrieval không cross-encoder):

| Hệ thống | `mrr` train | `mrr` valid | `hit@5` valid | `ans_valid@5` valid | `leakage_rate` valid | Δ `mrr` valid |
|---|---|---|---|---|---|---|
| Temporal Retrieval + bge-reranker-v2-m3 | 0.619 | **0.566** | 0.771 | 0.673 | 0% | +0.055 ± 0.014 |
| + MiniLM-L12 | 0.591 | 0.559 | 0.748 | 0.673 | 0% | +0.048 ± 0.009 |
| + MiniLM-L6 | 0.586 | 0.557 | 0.748 | 0.668 | 0% | +0.046 ± 0.010 |
| + bge-reranker-base | 0.560 | 0.524 | 0.748 | 0.675 | 0% | +0.014 ± 0.012 |
| + jina-reranker-v1-turbo | 0.556 | 0.520 | 0.730 | 0.675 | 0% | +0.009 ± 0.009 |
| Temporal Retrieval, không cross-encoder | 0.549 | 0.511 | 0.718 | 0.668 | 0% | (nền) |
| Plain RAG + bge-reranker-v2-m3 | 0.527 | 0.437 | 0.670 | 0.531 | 87% | −0.074 ± 0.020 |
| Plain RAG | 0.422 | 0.332 | 0.569 | 0.458 | 95% | −0.179 ± 0.018 |

- Thứ hạng giữa các họ giữ nguyên từ train sang valid; `mrr` thấp hơn khoảng 0.05 đến 0.09 ở mọi họ.
- Ba cross-encoder đầu (bge-reranker-v2-m3, MiniLM-L12, MiniLM-L6) cho thêm khoảng +0.05 `mrr` so với nền; bge-reranker-base và jina không hơn nền một cách đáng tin.
- Plain RAG rò rỉ 87 đến 95% câu trả lời từ chunk tương lai, kể cả khi thêm cross-encoder.

### 2.2. Quét tham số

**Quét tham số** là thử nhiều tổ hợp giá trị của các tham số điều khiển cách xếp hạng, rồi giữ tổ hợp cho `mrr` cao nhất trên train. Với mỗi họ cross-encoder (MiniLM-L6, MiniLM-L12, bge-reranker-v2-m3) chạy 80 cấu hình = 1 **cấu hình xuất phát** (cấu hình tốt nhất của họ đó trong 888 cấu hình cũ, tức kết quả "trước khi quét") và 79 tổ hợp bốc ngẫu nhiên. Tổng 240 cấu hình. Các tham số được quét:

| Tham số | Ý nghĩa | Giá trị thử |
|---|---|---|
| `w2` | trọng số điểm thời gian (`Temporal`) trong `Final = W1·Semantic + W2·Temporal`; `W1 = 1 − W2` | 0.1 đến 0.5 |
| `decay_lambda` | tốc độ giảm điểm thời gian theo số năm cách khi chunk không bao phủ thời điểm hỏi: điểm = `exp(−λ·số năm cách)`; mặc định 0.5 (cách 1 năm còn 0.61, cách 2 năm còn 0.37) | 0.1 đến 2 |
| `t_unknown`, `open_decay`, `end_mode` | cách chấm chunk chưa rõ ngày kết thúc | 4, 4 và 2 giá trị |
| `decay_from` | tính khoảng cách từ đầu hay cuối khoảng hiệu lực của chunk | `start`, `end` |
| `time_mode` | một điểm thời gian (`point`) hay một khoảng (`range`) cho thời điểm hỏi | `point`, `range` |
| `rerank_top`, `rerank_mode`, `rerank_norm` | số ứng viên đưa cho cross-encoder; thay hay trộn điểm cũ; cách chuẩn hóa điểm | 5, 2 và 2 giá trị |
| `top_n` | số ứng viên lấy từ Qdrant trước khi chấm lại; mặc định 50 | 50, 100 |

Cấu hình tốt nhất sau quét trên train, xác nhận trên valid (Δ so với cấu hình xuất phát cùng họ):

| Họ | `mrr` train (trước quét) | `mrr` train (sau quét) | `mrr` valid | Δ `mrr` valid so với trước quét |
|---|---:|---:|---:|---|
| bge-reranker-v2-m3 | 0.619 | 0.628 | **0.581** | +0.016 ± 0.011 |
| MiniLM-L12 | 0.591 | 0.592 | 0.564 | +0.005 ± 0.013 |
| MiniLM-L6 | 0.586 | 0.591 | 0.540 | −0.016 ± 0.013 |

Quét tham số chỉ tăng 0.001 đến 0.009 `mrr` trên train, nhỏ hơn sai số, và trên valid không cải thiện đáng tin (L6 còn tệ đi vì quá khớp train). Vì cấu hình xuất phát đã được chọn từ 888 cấu hình nên đã gần đỉnh, và điểm số phụ thuộc yếu vào từng tham số: lọc cứng thời gian là cố định, còn cross-encoder quyết định phần lớn thứ hạng.

### 2.3. Chọn cấu hình chính

Quy tắc đặt trước, chỉ dùng valid: lấy họ có `mrr` cao nhất, rồi chọn họ **đơn giản nhất** (MiniLM-L6 < MiniLM-L12 < bge-reranker-v2-m3) có chênh lệch ghép cặp nằm trong một sai số chuẩn. bge-reranker-v2-m3 cao nhất, MiniLM-L12 thấp hơn 1,3 sai số chuẩn nên không thay thế được, vậy chọn **Temporal Retrieval + bge-reranker-v2-m3** làm cấu hình chính. Chênh khi đó còn sát, nên tập test vẫn báo cả ba cross-encoder.

---

## 3. Kết quả trên tập test

Chạy một lần 28 cấu hình trên 400 câu của tập test, danh sách chốt trước khi xem kết quả, báo cáo tất cả (0 lỗi):

| Hệ thống | `mrr` | `hit@1` | `hit@5` | `ans_valid@5` | `leakage_rate` | Δ so với Plain RAG | Δ so với Temporal Retrieval không cross-encoder |
|---|---|---|---|---|---|---|---|
| Plain RAG | 0.336 | 0.158 | 0.573 | 0.460 | 89% | (nền) | −0.181 ± 0.017 |
| Plain RAG hybrid (dense + BM25) | 0.352 | 0.200 | 0.507 | 0.425 | 88% | +0.016 ± 0.013 | −0.164 ± 0.019 |
| Plain RAG + MiniLM-L6 | 0.443 | 0.270 | 0.677 | 0.532 | 89% | +0.107 ± 0.016 | −0.073 ± 0.021 |
| Plain RAG + MiniLM-L12 | 0.452 | 0.282 | 0.685 | 0.530 | 90% | +0.117 ± 0.015 | −0.064 ± 0.020 |
| Plain RAG + bge-reranker-v2-m3 | 0.490 | 0.300 | 0.745 | 0.578 | 88% | +0.154 ± 0.016 | −0.027 ± 0.021 |
| Temporal Retrieval, không cross-encoder | 0.516 | 0.352 | 0.725 | 0.657 | 0% | +0.181 ± 0.017 | (nền) |
| Temporal Retrieval + MiniLM-L6 | 0.558 | 0.405 | 0.767 | 0.677 | 0% | +0.222 ± 0.018 | +0.042 ± 0.014 |
| Temporal Retrieval + MiniLM-L12 | 0.563 | 0.395 | 0.802 | 0.680 | 0% | +0.227 ± 0.018 | +0.047 ± 0.016 |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.620** | **0.468** | **0.828** | **0.695** | **0%** | **+0.285 ± 0.018** | **+0.104 ± 0.016** |

Nhận xét:
- **Cơ chế thời gian là đóng góp chính.** Plain RAG rò rỉ 88 đến 90% ở mọi biến thể, kể cả khi thêm cross-encoder; Temporal Retrieval rò rỉ 0%. Không cross-encoder, Temporal Retrieval đã hơn Plain RAG +0.181 `mrr`; cùng cross-encoder thì hơn +0.11 đến +0.13.
- **bge-reranker-v2-m3 hơn rõ hai MiniLM** trên tập sạch: hơn L12 +0.057 ± 0.014 và hơn L6 +0.062 ± 0.015 (khoảng 4 sai số chuẩn). L6 và L12 ngang nhau (+0.005 ± 0.011). Điều này khớp với lựa chọn đã làm trên valid, khi đó chênh mới 1,3 sai số chuẩn.
- **Quét tham số không giúp trên tập test:** so với cấu hình xuất phát, MiniLM-L6 −0.016 ± 0.011, MiniLM-L12 −0.009 ± 0.013, bge-reranker-v2-m3 +0.001 ± 0.011; đều trong sai số.

### Bỏ từng thành phần (ablation)

Mỗi dòng bỏ **một** thành phần khỏi cấu hình đầy đủ, giữ nguyên mọi thứ khác (`mrr` trên tập test):

| Bỏ gì | Không cross-encoder | + MiniLM-L6 | + MiniLM-L12 | + bge-reranker-v2-m3 |
|---|---|---|---|---|
| (cấu hình đầy đủ) | 0.516 | 0.558 | 0.563 | 0.620 |
| điểm thời gian (`W2 = 0`, vẫn giữ lọc cứng `start ≤ T_req`) | 0.398 | 0.486 | 0.482 | 0.537 |
| giảm điểm khi chunk hết hạn (`decay_lambda = 0`) | 0.419 | 0.484 | 0.489 | 0.548 |
| xử lý `end_time` chưa rõ (`end_mode` về `stored`) | 0.506 | 0.556 | 0.556 | 0.618 |
| đổi `point` sang `range` (hoặc ngược lại) | 0.518 | 0.568 | 0.561 | 0.612 |

- Hai thành phần đóng góp nhiều nhất ngoài lọc cứng là **điểm thời gian** (bỏ đi giảm 0.08 đến 0.12 `mrr`) và **giảm điểm khi chunk hết hạn** (giảm 0.07 đến 0.10).
- Xử lý `end_time` chưa rõ và chọn `point`/`range` gần như không tác động trên tập này (chênh dưới 0.01 với cross-encoder).
- Khi bỏ điểm thời gian, Temporal Retrieval + bge-reranker-v2-m3 vẫn đạt 0.537, cao hơn bản không cross-encoder (0.516), nhưng thấp hơn cấu hình đầy đủ 0.083: cross-encoder bù được một phần chứ không thay thế được điểm thời gian.

---

## 4. Đáp án sinh ra: EM/F1

Bước cuối của pipeline: LLM đọc các chunk đã truy xuất rồi trả lời. Đáp án của dataset chỉ là một cụm từ ngắn (ví dụ "Markus Anfang"), nên prompt ép LLM trả đúng cụm từ ngắn nhất lấy từ đoạn văn, hoặc `null` nếu không có đáp án. Các chỉ số:
- **EM (Exact Match):** 1 nếu câu trả lời trùng hoàn toàn với đáp án sau khi chuẩn hóa (chữ thường, bỏ dấu phụ, dấu câu, mạo từ a/an/the), ngược lại 0.
- **F1:** so theo từng từ, ví dụ trả lời "Markus Anfang was the coach" cho đáp án "Markus Anfang" được F1 = 0.67 (EM = 0).
- Từ chối (`null`) tính 0 ở cả hai; tỉ lệ từ chối báo riêng.

**Cách làm.** Mỗi request Gemini 3.5 flash-lite chứa 4 câu độc lập (kèm 15 chunk mỗi câu) và trả về JSON. Chọn prompt trên tập valid (98 câu chia đều theo domain, 4 phiên bản, 2 hệ thống): không phiên bản nào hơn bản đơn giản nhất (v1) từ 2 sai số chuẩn trở lên nên dùng v1. Sau đó chạy một lần trên tập test với 3 hệ thống, 400 câu mỗi hệ thống, 0 lô sai định dạng. Chi tiết: [`eval/07`](../../eval/07_TUNE_VALID_RESULTS.md) mục 7, các phiên bản prompt: [`decisions/03`](../../decisions/03_PROMPT_CHANGELOG.md).

| Hệ thống (top-15 chunk) | EM | F1 | Từ chối | Đáp án có trong 15 chunk |
|---|---|---|---|---|
| Plain RAG | 0.422 | 0.501 | 32.0% | 94.0% |
| Plain RAG + bge-reranker-v2-m3 | 0.407 | 0.479 | 33.5% | 95.3% |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.448** | **0.513** | 29.2% | 94.3% |

Temporal Retrieval + bge-reranker-v2-m3 hơn Plain RAG dùng cùng cross-encoder **+0.040 EM** (± 0.020, hai sai số chuẩn) và hơn Plain RAG +0.025 EM (± 0.023, chưa phân biệt được).

Nhận xét:
- **Khoảng cách về đáp án nhỏ hơn nhiều so với về truy xuất** (`mrr` hơn +0.285, EM chỉ hơn +0.025 đến +0.040). Với 15 chunk, Plain RAG cũng có đáp án trong ngữ cảnh ở 94% câu nên LLM vẫn tìm được; lợi thế của Temporal Retrieval nhiều khả năng lớn hơn khi ngữ cảnh ít chunk hơn (chưa test).
- **Nút thắt là bước sinh đáp án:** khi đáp án có trong ngữ cảnh, EM chỉ khoảng 0.43 đến 0.48, vì LLM từ chối 25 đến 30% câu dù đáp án nằm trong 15 chunk (ngày trong chunk không khớp từng chữ với câu hỏi). Nới điều kiện từ chối ở tập valid chỉ chuyển câu từ "từ chối" sang "trả lời sai".
- Khoảng 6% (Temporal) đến 8% (Plain RAG) câu đã trả lời dựa vào chunk có nội dung sau thời điểm hỏi.
- Theo domain, Temporal Retrieval hơn rõ ở career (0.42 so với 0.26 đến 0.30) và sports; kém hơn ở politics và place (mỗi domain 50 câu nên chỉ để tham khảo).

**Ngữ cảnh ngắn hơn (top-5).** Số 15 chunk là mặc định của cấu hình truy xuất, không phải lựa chọn có chủ đích; các chỉ số truy xuất đều đo ở top-5. Chạy lại tập test với 5 chunk mỗi câu (cùng prompt, dùng Gemini 3.1 flash-lite vì hạn mức của 3.5 đã hết, nên là phân tích bổ sung, không so trực tiếp với bảng trên):

| Hệ thống (top-5 chunk) | EM | F1 | Từ chối | Đáp án có trong 5 chunk |
|---|---|---|---|---|
| Plain RAG | 0.398 | 0.462 | 36.7% | 68.5% |
| Plain RAG + bge-reranker-v2-m3 | 0.480 | 0.553 | 24.0% | 83.3% |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.527** | **0.604** | 19.8% | 89.2% |

Temporal Retrieval + bge-reranker-v2-m3 hơn Plain RAG **+0.130 EM** (± 0.022) và hơn Plain RAG + bge-reranker-v2-m3 +0.048 EM (± 0.018). Khi ngữ cảnh ngắn, Plain RAG không còn gom đủ đáp án (68,5% câu có đáp án trong ngữ cảnh so với 89,2%), nên lợi thế của truy xuất theo thời gian lộ ra rõ hơn so với top-15. Sẽ chạy lại top-5 bằng Gemini 3.5, chọn lại prompt trên tập valid ở top-5.

---

## 5. Hạn chế và việc tiếp theo

- Prompt sinh đáp án chọn trên 98 câu valid nên chỉ phân biệt được khác biệt lớn; LLM từ chối quá nhiều dù đáp án có trong ngữ cảnh. Kết quả EM/F1 chỉ dùng một prompt và một LLM.
- `ans_valid@5` mới khoảng 0.70: khoảng 30% câu chưa có chunk vừa chứa đáp án vừa hợp lệ về thời gian trong top-5.
- Cross-encoder chạy sau lọc cứng thời gian nên không cứu được các câu bị lọc cứng loại nhầm.
- Chỉ test trên TimeQA và câu hỏi tại một thời điểm; chưa test Timeline Summarization hay Conflict Resolution.
- Ablation "bỏ điểm thời gian" vẫn giữ lọc cứng; trường hợp không có lọc cứng được đại diện bởi Plain RAG.
- Việc tiếp theo: test lại EM/F1 với ngữ cảnh ít chunk hơn (top-5), cải thiện prompt để giảm từ chối, rồi chuyển sang các cơ chế còn lại.
