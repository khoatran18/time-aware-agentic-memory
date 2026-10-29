# Kết quả trên tập tune, valid và test_clean (chọn phương pháp, quét tham số, test sạch)

**Ngày:** 2026-10-24. Đây là các số **không dùng bộ `real`** để chọn: cấu hình được chọn trên `tune`, xác nhận trên `valid`, `test_clean` chạy một lần (mục 6). Các số trong [`05_REAL_RESULTS.md`](05_REAL_RESULTS.md) là cận trên (tập đã xem nhiều lần), không so trực tiếp với file này.

## 1. Các tập

| Tập | Số câu | Vai trò | Chỉnh theo? |
|---|---:|---|---|
| `real` | 400 (204 trang) | tập cũ, đã xem nhiều; chỉ là cận trên tham khảo | đã bị chỉnh, không dùng để chọn |
| `tune` | 595 (203 trang) | chọn và chỉnh tham số, chọn ứng viên | có, chỉ ở đây |
| `valid` | 399 | kiểm chứng ứng viên; chọn giữa phương pháp theo quy tắc một sai số chuẩn | không chỉnh tham số |
| `test_clean` | 400 | số cuối, chạy **một lần** với danh sách chốt trước | không |

`tune` gồm 400 câu gốc và 195 câu của `real` có trang không nằm trong `valid` hoặc `test_clean` (bản gốc giữ ở `dataset/eval/tune_base_subset.json`). Ba tập `tune`, `valid`, `test_clean` đôi một không trùng trang. `valid` đã bỏ 1 câu nhãn hỏng (`time_start` = '18'). Cần ba tập vì chọn hai tầng (thử hàng trăm cấu hình trên `tune`, rồi chọn vài ứng viên): `mrr` trên `tune` luôn cao hơn trên tập chưa thấy, `valid` chống tự đánh lừa.

## 2. Bước 1: chạy lại 888 cấu hình cũ trên `tune`, xác nhận 56 cấu hình trên `valid`

888 cấu hình là toàn bộ cấu hình end-to-end đã chạy trên `real` (đã khử trùng). Chạy lại trên `tune`, chọn đa dạng (top 20 `mrr`, top 5 mỗi họ, Plain RAG) rồi chạy trên `valid`. Cấu hình tốt nhất của mỗi họ trên `tune`, đo trên `valid`; Δ là chênh lệch `mrr` ghép cặp theo câu so với nền không cross-encoder (± một sai số chuẩn):

| Họ | `mrr` tune | `mrr` valid | hit@5 | ans_valid@5 | rò rỉ | Δ `mrr` |
|---|---:|---:|---:|---:|---:|---|
| Temporal Retrieval + bge-reranker-v2-m3 | 0.619 | 0.566 | 0.771 | 0.673 | 0 | +0.055 ± 0.014 |
| + MiniLM-L12 | 0.591 | 0.559 | 0.748 | 0.673 | 0 | +0.048 ± 0.009 |
| + MiniLM-L6 | 0.586 | 0.557 | 0.748 | 0.668 | 0 | +0.046 ± 0.010 |
| + bge-reranker-base | 0.560 | 0.524 | 0.748 | 0.675 | 0 | +0.014 ± 0.012 |
| + jina-turbo | 0.556 | 0.520 | 0.730 | 0.675 | 0 | +0.009 ± 0.009 |
| Temporal Retrieval, không cross-encoder | 0.549 | 0.511 | 0.718 | 0.668 | 0 | (nền) |
| Plain RAG + bge-reranker-v2-m3 | 0.527 | 0.437 | 0.670 | 0.531 | 0.87 | −0.074 ± 0.020 |
| Plain RAG dense | 0.422 | 0.332 | 0.569 | 0.458 | 0.95 | −0.179 ± 0.018 |

Nhận xét:

- Thứ hạng giữa các họ giữ nguyên từ `tune` sang `valid`; `mrr` thấp hơn 0.05 đến 0.09 ở mọi họ (một phần do `tune` chứa 195 câu `real`, phần còn lại là mức giảm bình thường khi chọn trên tập chỉnh).
- Cơ chế thời gian là phần đóng góp lớn nhất: Plain RAG rò rỉ 87 đến 95% câu trả lời từ chunk tương lai, kể cả khi thêm cross-encoder; mọi cấu hình Temporal Retrieval rò rỉ 0. Plain RAG + cross-encoder vẫn thua Temporal Retrieval không cross-encoder 0.07 `mrr`.
- Cross-encoder cho thêm +0.05 `mrr` (bge-v2-m3, L12, L6); bge-base và jina không hơn nền một cách đáng tin.
- Ba cross-encoder đầu chênh nhau khoảng 0.01, nhỏ hơn sai số.

## 3. Bước 2: quét tham số ngẫu nhiên trên `tune`

**Quét tham số** là thử nhiều tổ hợp giá trị của các tham số điều khiển cách xếp hạng, rồi giữ tổ hợp cho `mrr` cao nhất trên `tune`. Với mỗi họ cross-encoder (L6, L12, bge-v2-m3) chạy **80 cấu hình**:

- **1 cấu hình xuất phát:** cấu hình tốt nhất của họ đó trong 888 cấu hình cũ (bước 1), chọn trên `tune`. Đây là kết quả "trước khi quét" dùng để so sánh.
- **79 cấu hình ngẫu nhiên:** mỗi cấu hình bốc ngẫu nhiên một giá trị cho từng tham số trong bảng dưới (seed 0, giữ nguyên các cài đặt còn lại của cấu hình xuất phát). Không gian có khoảng 380 nghìn tổ hợp, nên 79 điểm chỉ là mẫu thăm dò.
- Tổng 3 họ × 80 = 240 cấu hình.

Hai tham số `decay_lambda` và `top_n` trước đây chỉ nằm trong file config, nên thêm hai cờ tùy chọn cho `scripts/evaluate.py` (`--decay-lambda`, `--top-n`; mặc định theo config). Mọi cấu hình cũ đều dùng `decay_lambda = 0.5` và `top_n = 50` (giá trị mặc định trong config) nên kết quả cũ không đổi.

| Tham số | Ý nghĩa | Giá trị thử |
|---|---|---|
| `w2` | trọng số điểm thời gian trong `Final = W1·Semantic + W2·Temporal`; `w1 = 1 − w2` | 0.1, 0.2, 0.3, 0.4, 0.5 |
| `decay_lambda` | tốc độ giảm điểm thời gian khi chunk không bao phủ thời điểm hỏi (trường hợp 2): điểm = `exp(−λ · số năm cách)`; mặc định 0.5 (cách 1 năm còn 0.61, 2 năm còn 0.37) | 0.1, 0.25, 0.5, 1, 2 |
| `t_unknown` | điểm thời gian cố định cho chunk không có mốc (`unknown`) | 0.05, 0.1, 0.2, 0.3 |
| `open_decay` | tốc độ giảm điểm của chunk `end_time` chưa rõ (dùng với `end_mode` `decay`/`unknown_decay`) | 0.02, 0.05, 0.1, 0.2 |
| `end_mode` | cách coi `end_time` chưa rõ: `unknown_decay` (chỉ chunk `unknown` giảm dần, `ongoing` giữ 1.0) hoặc `decay` | `unknown_decay`, `decay` |
| `decay_from` | mốc tính khoảng cách của chunk đã hết hạn: đầu (`start`) hay cuối (`end`) khoảng hiệu lực | `start`, `end` |
| `rerank_top` | số ứng viên đầu đưa cho cross-encoder chấm lại | 10, 15, 20, 30, 40 |
| `rerank_mode` (và `rerank_alpha` nếu `mix`) | `replace`: thay điểm cũ bằng điểm cross-encoder; `mix`: trộn, `alpha` là trọng số của điểm cũ | `replace`, `mix` (0.3, 0.5, 0.7) |
| `rerank_norm` | cách chuẩn hóa điểm cross-encoder | `minmax`, `zscore` |
| `top_n` | số ứng viên lấy từ VectorDB trước khi chấm lại thời gian và cross-encoder; mặc định 50 | 50, 100 |
| `time_mode` / `overlap` | `point`: một điểm `t_req`; `range`: khoảng `[t_req, t_end]` với độ chồng lấn `binary` hoặc `coverage` (tỉ lệ phủ) | `point`, `range` + `binary`, `range` + `coverage` |

**Sai số chuẩn** (ở mọi bảng: ± ...) là độ bất định của chênh lệch `mrr` trung bình giữa hai cấu hình, tính ghép cặp theo câu (độ lệch chuẩn của chênh lệch từng câu chia √n). Chênh lệch lớn hơn khoảng 2 sai số chuẩn thì coi là đáng tin; dưới 1 thì không phân biệt được với may rủi.

Cấu hình tốt nhất trên `tune` của mỗi họ (240 cấu hình, 0 lỗi), xác nhận **một lần** trên `valid`:

| Họ | Cấu hình sau quét | `mrr` tune (trước quét = xuất phát) | `mrr` tune (sau quét) | `mrr` valid | hit@5 | ans_valid@5 | Δ valid so với xuất phát | Δ valid so với nền không CE |
|---|---|---:|---:|---:|---:|---:|---|---|
| bge-v2-m3 | `0a1b716ac7` | 0.619 | 0.628 | **0.581** | 0.793 | 0.708 | +0.016 ± 0.011 | +0.071 ± 0.016 |
| L12 | `b73bc37f8c` | 0.591 | 0.592 | 0.564 | 0.778 | 0.662 | +0.005 ± 0.013 | +0.053 ± 0.016 |
| L6 | `a5e602ff4e` | 0.586 | 0.591 | 0.540 | 0.753 | 0.652 | −0.016 ± 0.013 | +0.030 ± 0.016 |

Chênh `mrr` ghép cặp giữa các họ trên `valid`: bge − L12 = +0.018 ± 0.014 (khoảng 1,3 sai số chuẩn); bge − L6 = +0.041 ± 0.015; L12 − L6 = +0.023 ± 0.010.

Tham số của cấu hình bge-v2-m3 tốt nhất (`0a1b716ac7`): `time_mode=range` (`binary`), `w2=0.2`, `end_mode=decay`, `open_decay=0.1`, `decay_from=start`, `rerank_mode=mix` với `alpha=0.3`, `rerank_top=30`, `top_n=100`, `t_unknown=0.1`, `decay_lambda=0.5`.

## 4. Kết luận rút ra

1. **Quét tham số không cho cải thiện đáng tin.** Trên `tune` mức tăng chỉ 0.001 đến 0.009 `mrr` (nhỏ hơn sai số); trên `valid` L6 còn tệ đi 0.016 (quá khớp `tune`), L12 phẳng, bge-v2-m3 tăng 0.016 trong phạm vi sai số. Cấu hình xuất phát đã gần tối ưu và kết quả ổn định theo các tham số thời gian: chất lượng phụ thuộc chủ yếu vào cơ chế (lọc cứng + điểm thời gian) và cross-encoder, không vào việc chỉnh tinh `w2`, `decay`.
2. **Cơ chế thời gian quyết định chất lượng và an toàn.** Plain RAG rò rỉ 87 đến 95%, Temporal Retrieval 0, ở mọi tập; Plain RAG + cross-encoder vẫn kém 0.07 `mrr`.
3. **Chọn cross-encoder.** Quy tắc đặt trước (chỉ dùng `valid`): lấy họ có `mrr` cao nhất, rồi chọn họ đơn giản nhất (L6 < L12 < bge-v2-m3) có Δ ghép cặp nằm trong một sai số chuẩn. bge-v2-m3 cao nhất; L12 thấp hơn 1,3 sai số, nằm ngoài một sai số chuẩn → **bge-v2-m3 (`0a1b716ac7`) là cấu hình chính**. Ranh giới sát, nên `test_clean` báo cả L6, L12 và bge-v2-m3 (đều với cấu hình tốt nhất trên `tune`).
4. **Giới hạn.** Một sai số chuẩn là sai số của chênh lệch ghép cặp (sd/√n), chưa hiệu chỉnh đa so sánh; cross-encoder chạy sau lọc cứng nên không cứu các câu bị lọc cứng loại nhầm; `tune` chứa câu của `real` nên số trên `tune` cao hơn thực tế.

## 5. Danh sách chạy trên `test_clean` (chốt trước, chạy một lần, báo cáo tất cả; kết quả ở mục 6)

Chỉ đo retrieval (hit@1/5, `mrr`, ans_valid@5, rò rỉ) với Δ ghép cặp ± một sai số chuẩn; không dùng cấu hình nào trong 888 cấu hình cũ (chọn theo `real`).

| Nhóm | Cấu hình |
|---|---|
| A. Plain RAG | dense; hybrid; dense + L6; dense + L12; dense + bge-v2-m3 |
| B. Temporal Retrieval | không cross-encoder; + L6 (`a5e602ff4e`); + L12 (`b73bc37f8c`); + bge-v2-m3 (`0a1b716ac7`, cấu hình chính) |
| C. Giá trị của quét | mỗi cross-encoder ở B với tham số xuất phát (trước quét) |
| D. Ablation (cho cả L6, L12, bge-v2-m3, và bản không cross-encoder) | bỏ điểm thời gian (`no_temporal`, `W2 = 0`, vẫn giữ lọc cứng `start ≤ T_req`); `point` ↔ `range`; bỏ `end_mode` (`stored`); bỏ decay khi fallback (`decay_lambda = 0`) |
| E. Đầu-cuối (có gọi LLM) | EM/F1 và số token ngữ cảnh: cấu hình chính so với Plain RAG tốt nhất ở nhóm A |

Cross-encoder chạy sau lọc cứng, nên ablation có cross-encoder và không cross-encoder trả lời hai câu hỏi khác nhau (cơ chế thời gian đóng góp bao nhiêu khi đã có reranker, và khi chưa có).

## 6. Kết quả `test_clean` (400 câu, chạy một lần, 28 cấu hình, 0 lỗi)

Δ là chênh lệch `mrr` ghép cặp theo câu (± một sai số chuẩn) so với Plain RAG dense và so với Temporal Retrieval không cross-encoder. Rò rỉ = tỉ lệ câu có đáp án lấy từ chunk có `start > T_req`.

| Nhóm | Cấu hình | hit@1 | hit@5 | `mrr` | ans_valid@5 | rò rỉ | Δ so với Plain RAG dense | Δ so với Temporal không CE |
|---|---|---:|---:|---:|---:|---:|---|---|
| A | Plain RAG dense | 0.158 | 0.573 | 0.336 | 0.460 | 0.89 | (nền) | −0.181 ± 0.017 |
| A | Plain RAG hybrid | 0.200 | 0.507 | 0.352 | 0.425 | 0.88 | +0.016 ± 0.013 | −0.164 ± 0.019 |
| A | Plain RAG dense + L6 | 0.270 | 0.677 | 0.443 | 0.532 | 0.89 | +0.107 ± 0.016 | −0.073 ± 0.021 |
| A | Plain RAG dense + L12 | 0.282 | 0.685 | 0.452 | 0.530 | 0.90 | +0.117 ± 0.015 | −0.064 ± 0.020 |
| A | Plain RAG dense + bge-v2-m3 | 0.300 | 0.745 | 0.490 | 0.578 | 0.88 | +0.154 ± 0.016 | −0.027 ± 0.021 |
| B | Temporal Retrieval, không CE | 0.352 | 0.725 | 0.516 | 0.657 | 0 | +0.181 ± 0.017 | (nền) |
| B | + L6 (tune sau quét) | 0.405 | 0.767 | 0.558 | 0.677 | 0 | +0.222 ± 0.018 | +0.042 ± 0.014 |
| B | + L12 (tune sau quét) | 0.395 | 0.802 | 0.563 | 0.680 | 0 | +0.227 ± 0.018 | +0.047 ± 0.016 |
| B | **+ bge-v2-m3 (tune sau quét, cấu hình chính)** | **0.468** | **0.828** | **0.620** | 0.695 | 0 | **+0.285 ± 0.018** | **+0.104 ± 0.016** |
| C | + L6 (xuất phát, trước quét) | 0.425 | 0.762 | 0.574 | 0.670 | 0 | +0.238 ± 0.018 | +0.058 ± 0.010 |
| C | + L12 (xuất phát, trước quét) | 0.422 | 0.765 | 0.572 | 0.672 | 0 | +0.237 ± 0.018 | +0.056 ± 0.009 |
| C | + bge-v2-m3 (xuất phát, trước quét) | 0.460 | 0.830 | 0.619 | 0.693 | 0 | +0.283 ± 0.019 | +0.103 ± 0.014 |

Temporal Retrieval + cross-encoder so với Plain RAG + **cùng** cross-encoder (Δ `mrr` ghép cặp): L6 +0.115 ± 0.017; L12 +0.111 ± 0.015; bge-v2-m3 +0.131 ± 0.017.

Chênh giữa các cross-encoder (cấu hình tune sau quét): bge − L12 = +0.057 ± 0.014; bge − L6 = +0.062 ± 0.015; L12 − L6 = +0.005 ± 0.011. Sau quét − xuất phát: L6 −0.016 ± 0.011; L12 −0.009 ± 0.013; bge +0.001 ± 0.011.

Ablation (D), `mrr` (trong ngoặc ở tiêu đề cột: cấu hình đầy đủ cùng họ):

| Bỏ gì | Không CE (0.516) | + L6 (0.558) | + L12 (0.563) | + bge-v2-m3 (0.620) |
|---|---|---|---|---|
| điểm thời gian (`no_temporal`, `W2 = 0`) | 0.398 | 0.486 | 0.482 | 0.537 |
| decay khi fallback (`decay_lambda = 0`) | 0.419 | 0.484 | 0.489 | 0.548 |
| `end_mode` (về `stored`) | 0.506 | 0.556 | 0.556 | 0.618 |
| đổi `point` ↔ `range` | 0.518 | 0.568 | 0.561 | 0.612 |

### Nhận xét

1. **Cơ chế thời gian quyết định.** Plain RAG rò rỉ 88 đến 90% ở mọi biến thể (kể cả cùng cross-encoder); mọi cấu hình Temporal Retrieval rò rỉ 0. Cùng cross-encoder, Temporal Retrieval hơn Plain RAG +0.11 đến +0.13 `mrr`; không cross-encoder đã hơn Plain RAG dense +0.18.
2. **bge-v2-m3 hơn rõ L6 và L12 trên tập sạch** (+0.057 và +0.062, khoảng 4 sai số chuẩn), xác nhận lựa chọn ở `valid` (chênh khi đó chỉ 1,3 sai số). L6 và L12 ngang nhau. hit@1 tăng mạnh nhất: 0.352 → 0.468.
3. **Quét tham số không giúp.** Trên `test_clean` cấu hình sau quét không hơn cấu hình xuất phát (L6 −0.016, L12 −0.009, bge +0.001, đều trong sai số). Giữ kết luận mục 4: chất lượng do cơ chế và cross-encoder quyết định.
4. **Phần nào của điểm thời gian quan trọng.** Bỏ điểm thời gian (`W2 = 0`) giảm 0.08 đến 0.12 `mrr`; bỏ decay khi fallback giảm 0.07 đến 0.10: hai phần này đóng góp chính ngoài lọc cứng. Bỏ `end_mode` (−0.011 không cross-encoder, −0.002 với bge) và đổi `point`/`range` (±0.01) không có tác động đáng kể trên tập này.
5. **Cross-encoder bù một phần cho điểm thời gian.** Khi bỏ điểm thời gian, Temporal Retrieval + bge-v2-m3 vẫn đạt 0.537 (hơn nền không cross-encoder 0.516), nhưng thua cấu hình đầy đủ 0.083.
6. **Giới hạn.** Ablation `no_temporal` vẫn giữ lọc cứng `start ≤ T_req` (hiện không có cờ tắt hẳn lọc cứng); trường hợp không có lọc cứng được đại diện bởi Plain RAG. Cổng đầu-cuối EM/F1: xem mục 7.

## 7. Đáp án sinh ra: EM/F1 trên `test_clean`

Thêm tầng sinh đáp án ngắn (`src/tam/generation/`): mỗi câu nhận 15 chunk đầu của hệ thống truy xuất, LLM (Gemini 3.5 flash-lite, 4 câu mỗi request) trả một cụm từ ngắn hoặc `null`. **EM** (Exact Match) là 1 nếu câu trả lời trùng đáp án vàng sau khi chuẩn hóa (chữ thường, bỏ dấu phụ, bỏ dấu câu và mạo từ), **F1** so theo từ, **contains** là câu trả lời chứa trọn đáp án; từ chối (`null`) tính 0 ở cả ba. Prompt chọn trên `valid` (98 câu, 4 phiên bản, xem [`decisions/03`](../decisions/03_PROMPT_CHANGELOG.md)): không phiên bản nào hơn v1 từ 2 sai số chuẩn nên dùng **v1**. Chạy `test_clean` một lần với v1, 400 câu, 0 lô sai định dạng.

| Hệ thống (top-15 chunk) | EM | F1 | contains | từ chối | EM khi đã trả lời | đáp án có trong 15 chunk | từ chối dù đáp án có trong ngữ cảnh | trả lời dựa chunk tương lai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Plain RAG | 0.422 | 0.501 | 0.470 | 32.0% | 0.621 | 94.0% | 110 | 21/272 |
| Plain RAG + bge-reranker-v2-m3 | 0.407 | 0.479 | 0.435 | 33.5% | 0.613 | 95.3% | 119 | 22/266 |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.448** | **0.513** | 0.472 | 29.2% | 0.633 | 94.3% | 99 | 16/283 |

Δ ghép cặp (± một sai số chuẩn): Temporal − Plain RAG + bge: EM **+0.040 ± 0.020**, F1 +0.034 ± 0.020; Temporal − Plain RAG: EM +0.025 ± 0.023 (không phân biệt được); Plain RAG + bge − Plain RAG: EM −0.015 ± 0.020.

EM theo domain (Temporal / Plain RAG + bge / Plain RAG; mỗi domain 50 câu): business 0.50 / 0.48 / 0.48; career 0.42 / 0.26 / 0.30; media_arts 0.66 / 0.60 / 0.58; military 0.48 / 0.44 / 0.50; person 0.42 / 0.32 / 0.42; place 0.20 / 0.24 / 0.26; politics 0.34 / 0.40 / 0.38; sports 0.56 / 0.52 / 0.46.

Nhận xét:
- **Khoảng cách ở khâu sinh nhỏ hơn nhiều so với ở khâu truy xuất.** `mrr` hơn +0.285 nhưng EM chỉ hơn +0.025 đến +0.040. Lý do chính: với 15 chunk, cả Plain RAG cũng có đáp án trong ngữ cảnh ở 94% câu (Temporal 94,3%), nên LLM vẫn tìm được; lợi thế của truy xuất thời gian sẽ lớn hơn khi ngữ cảnh ít chunk hơn (chưa test).
- **Nút thắt là bước sinh, không phải truy xuất.** Khi đáp án có trong ngữ cảnh, EM chỉ 0.43 đến 0.48; LLM **từ chối** 99 đến 119 câu (khoảng 25 đến 30%) dù đáp án nằm trong 15 chunk, (ví dụ trên `valid`: "after Aug 2004", "between Oct 1911 and Feb 1933", ngày trong chunk không khớp từng chữ với câu hỏi). Nới điều kiện từ chối (v3, v4) chỉ chuyển câu từ "từ chối" sang "trả lời sai" ở valid.
- **Rò rỉ tương lai:** ở Plain RAG khoảng 8% số câu đã trả lời dựa vào chunk có `start_time` sau thời điểm hỏi (21/272 và 22/266), ở Temporal 16/283 (5,7%; chưa phân tích nguyên nhân từng câu). Phần lớn rò rỉ ở khâu truy xuất (88 đến 90% câu có chunk tương lai trong top-5) không chuyển thành câu trả lời dựa chunk tương lai, vì LLM thường chọn đúng chunk theo thời điểm hỏi ghi trong câu.
- **Plain RAG + cross-encoder không hơn Plain RAG** ở EM (−0.015 ± 0.020): cross-encoder đưa chunk đúng lên cao hơn nhưng với 15 chunk thì không còn cần.
- Prompt chọn trên 98 câu valid nên chỉ phân biệt được sai khác lớn; tất cả prompt đều trong sai số.

### Ngữ cảnh top-5 (Gemini 3.1 flash-lite) — phân tích bổ sung

Số 15 chunk ở trên là mặc định của cấu hình truy xuất (`top_k = 15`), không phải lựa chọn có chủ đích; mọi chỉ số truy xuất ở trên lại đo ở top-5. Chạy lại `test_clean` với **5 chunk** mỗi câu, cùng prompt v1, LLM **Gemini 3.1 flash-lite** (hạn mức ngày của 3.5 đã dùng hết). Đây là phân tích **bổ sung chọn sau khi xem kết quả top-15**, và prompt v1 được chọn trên `valid` ở top-15; kiểm lại ở top-5 nằm ở mục "Chọn prompt trên valid ở top-5" bên dưới. Hai bảng khác LLM nên so top-5 với top-15 là lẫn hai yếu tố (số chunk và LLM); phần so cùng LLM (Gemini 3.5) nằm ở mục tiếp theo.

| Hệ thống (top-5 chunk) | EM | F1 | contains | từ chối | EM khi đã trả lời | đáp án có trong 5 chunk | từ chối dù có trong ngữ cảnh | trả lời dựa chunk tương lai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Plain RAG | 0.398 | 0.462 | 0.425 | 36.7% | 0.628 | 68.5% | 46 | 15/253 |
| Plain RAG + bge-reranker-v2-m3 | 0.480 | 0.553 | 0.510 | 24.0% | 0.632 | 83.3% | 45 | 22/304 |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.527** | **0.604** | 0.560 | 19.8% | 0.657 | 89.2% | 51 | 15/321 |

Δ ghép cặp (± một sai số chuẩn): Temporal − Plain RAG: EM **+0.130 ± 0.022**, F1 +0.142 ± 0.022; Temporal − Plain RAG + bge: EM **+0.048 ± 0.018**, F1 +0.051 ± 0.017; Plain RAG + bge − Plain RAG: EM +0.083 ± 0.020.

EM theo domain (Temporal / Plain RAG + bge / Plain RAG): business 0.58 / 0.56 / 0.48; career 0.46 / 0.44 / 0.38; media_arts 0.66 / 0.56 / 0.56; military 0.60 / 0.56 / 0.54; person 0.54 / 0.50 / 0.46; place 0.28 / 0.30 / 0.22; politics 0.40 / 0.46 / 0.30; sports 0.70 / 0.46 / 0.24.

- **Với ngữ cảnh ngắn, khoảng cách lớn hơn rõ:** Temporal hơn Plain RAG +0.130 EM (so với +0.025 ở top-15) và hơn Plain RAG + cross-encoder +0.048. Tỉ lệ câu có đáp án trong ngữ cảnh khác nhau rõ: 89,2% (Temporal), 83,3% (Plain RAG + bge), 68,5% (Plain RAG). Điều này khớp dự đoán: ở top-15 Plain RAG vẫn gom đủ đáp án, ở top-5 thì không.
- **Cross-encoder có ích khi ngữ cảnh ngắn:** Plain RAG + bge hơn Plain RAG +0.083 EM (ở top-15 là −0.015).
- **Ngữ cảnh ngắn không làm EM tụt:** EM của Temporal ở top-5 (0.527, Gemini 3.1) không thấp hơn ở top-15 (0.448, Gemini 3.5), tỉ lệ từ chối cũng giảm (19,8% so với 29,2%). Chưa tách được tác động của LLM và số chunk.
- Tỉ lệ từ chối dù đáp án có trong ngữ cảnh vẫn là 45 đến 51 câu (khoảng 11 đến 13%).
- Theo domain, sports chênh rất lớn (0.70 so với 0.24 của Plain RAG) và politics, place Temporal không hơn (mỗi domain 50 câu, chỉ tham khảo).

### Ngữ cảnh top-5 (Gemini 3.5 flash-lite) — phân tích bổ sung

Cùng thiết lập với phần 3.1 ở trên (5 chunk mỗi câu, prompt v1) nhưng dùng **Gemini 3.5 flash-lite**, nên so được với top-15 (cùng LLM, cùng prompt). Vẫn là phân tích **bổ sung chọn sau khi xem kết quả top-15**.

Prompt: v1 (chọn trên `valid`, xem mục "Chọn prompt trên valid ở top-5" bên dưới).

| Hệ thống (top-5 chunk, Gemini 3.5) | EM | F1 | contains | từ chối | EM khi đã trả lời | đáp án có trong 5 chunk | từ chối dù có trong ngữ cảnh | trả lời dựa chunk tương lai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Plain RAG | 0.360 | 0.414 | 0.385 | 46.0% | 0.667 | 68.5% | 76 | 13/216 |
| Plain RAG + bge-reranker-v2-m3 | 0.432 | 0.494 | 0.458 | 35.0% | 0.665 | 83.3% | 85 | 20/260 |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.500** | **0.564** | 0.530 | 28.5% | 0.699 | 89.2% | 81 | 11/286 |

Δ ghép cặp (± một sai số chuẩn): Temporal − Plain RAG: EM **+0.140 ± 0.023**, F1 +0.151 ± 0.022; Temporal − Plain RAG + bge: EM **+0.068 ± 0.020**, F1 +0.071 ± 0.020; Plain RAG + bge − Plain RAG: EM +0.072 ± 0.021.

EM theo domain (Temporal / Plain RAG + bge / Plain RAG): business 0.54 / 0.52 / 0.48; career 0.42 / 0.36 / 0.24; media_arts 0.70 / 0.60 / 0.52; military 0.60 / 0.54 / 0.48; person 0.50 / 0.42 / 0.36; place 0.24 / 0.26 / 0.24; politics 0.36 / 0.36 / 0.28; sports 0.64 / 0.40 / 0.28.

**Top-5 so với top-15 (cùng Gemini 3.5, cùng prompt v1, ghép cặp theo câu)** (`local/results/answers_test_k5_vs_k15_g35.txt`):

| Hệ thống | Δ EM (top-5 − top-15) | Δ F1 |
|---|---:|---:|
| Temporal Retrieval + bge | +0.052 ± 0.020 | +0.052 ± 0.019 |
| Plain RAG + bge | +0.025 ± 0.020 | +0.014 ± 0.019 |
| Plain RAG | −0.062 ± 0.022 | −0.087 ± 0.022 |

- **Top-5 không làm EM tụt, còn tốt hơn với Temporal:** Temporal tăng +0.052 (khoảng 2,6 sai số chuẩn). Plain RAG + bge không đổi đáng kể. Plain RAG thường tụt −0.062 vì ở top-5 chỉ 68,5% câu còn đáp án trong ngữ cảnh. Vậy khoảng cách Temporal − Plain RAG lớn lên một phần vì Plain RAG kém đi khi bớt chunk, một phần vì Temporal giữ được.
- **Khoảng cách Temporal − Plain RAG + bge** ở top-5 là +0.068 ± 0.020 (3,4 sai số chuẩn), so với +0.040 ± 0.020 ở top-15.
- **So với bảng 3.1:** 3.5 thấp hơn 3.1 ở cả ba hệ thống (EM −0.028 đến −0.048, ghép cặp; Temporal −0.028 ± 0.019, Plain RAG + bge −0.048 ± 0.018, Plain RAG −0.037 ± 0.015). Nên hai LLM không thay thế nhau, nhưng thứ tự ba hệ thống và kết luận chính giống nhau.
- Từ chối vẫn cao (28,5% ở Temporal), trong đó 81 câu từ chối dù đáp án có trong ngữ cảnh: đây vẫn là điểm yếu chính của prompt v1.
- Cột "đáp án có trong 5 chunk" trùng với bảng 3.1 vì cùng chunk, chỉ khác LLM. Trả lời dựa chunk tương lai: Temporal 11/286 (3,8%), Plain RAG + bge 20/260 (7,7%), Plain RAG 13/216 (6,0%).

### Chọn prompt trên valid ở top-5

98 câu chia đều domain (seed 0), 2 hệ thống (Temporal Retrieval + bge và Plain RAG + bge), 4 prompt × 2 hệ thống × 25 request cho mỗi LLM. EM (Temporal / Plain RAG + bge) và Δ EM so với v1 (ghép cặp 196 câu, ± một sai số chuẩn):

| LLM | v1 | v2 | v3 | v4 |
|---|---|---|---|---|
| Gemini 3.1 flash-lite | .480 / .408 | .480 / .398 | .490 / .429 | .541 / .408 |
| | nền | −0.005 ± 0.017 | +0.015 ± 0.015 | **+0.031 ± 0.023** |
| Gemini 3.5 flash-lite | .459 / .388 | .480 / .388 | .469 / .398 | .469 / .378 |
| | nền | +0.010 ± 0.020 | +0.010 ± 0.018 | +0.000 ± 0.022 |
| Gemma 4 26B | .459 / .367 | .459 / .408 | .510 / .378 | .469 / .429 |
| | nền | +0.020 ± 0.018 | +0.031 ± 0.018 | +0.036 ± 0.022 |
| Gemma 4 31B | .490 / .449 | .520 / .469 | .551 / .480 | .531 / .480 |
| | nền | +0.026 ± 0.018 | **+0.046 ± 0.017** | +0.036 ± 0.018 |

(Ở top-15 với Gemini 3.5: v2 +0.010 ± 0.028, v3 +0.000 ± 0.019, v4 +0.036 ± 0.027.) Số thô: `local/results/answers_valid_prompts_k5_{g31,g35,g26b,g31b}.txt`.

- **Quy tắc đặt trước** (chỉ đổi khỏi v1 khi hơn từ 2 sai số chuẩn): chỉ v3 trên Gemma 31B vượt ngưỡng (2,7); v4 sát ngưỡng ở Gemma 31B (2,0). Với Gemini 3.1 và 3.5, tức hai LLM dùng cho test, không prompt nào vượt. Giữ **v1** làm prompt chính.
- **Không nhất quán giữa các LLM:** v4 hơn v1 ở Gemini 3.1 và Gemma nhưng không hơn ở Gemini 3.5 (+0.000 ± 0.022); hiệu hai Δ giữa 3.1 và 3.5 chỉ khoảng 1 sai số chuẩn nên khó nói là khác thật hay chỉ là nhiễu của mẫu 98 câu.
- v3 và v4 từ chối ít hơn nhưng trả lời sai nhiều hơn v1 khoảng 2 đến 6 điểm phần trăm (ví dụ Gemini 3.5, Temporal: sai 16.3% lên 22.4% với v4).

### Test top-5 với prompt v4 (Gemini 3.5) — chạy thêm

Chạy thêm theo yêu cầu, không phải prompt chọn từ `valid` (prompt chính vẫn là v1). Cùng 3 hệ thống, 400 câu, 0 lô lỗi; so ghép cặp với v1 ở bảng 3.5 phía trên.

| Hệ thống (top-5, Gemini 3.5) | EM v4 | F1 v4 | Từ chối | Trả lời sai | Δ EM so với v1 | Δ F1 so với v1 |
|---|---:|---:|---:|---:|---:|---:|
| Plain RAG | 0.385 | 0.453 | 39.3% | 19.5% | +0.025 ± 0.014 | +0.040 ± 0.015 |
| Plain RAG + bge-reranker-v2-m3 | 0.453 | 0.525 | 26.8% | 25.3% | +0.020 ± 0.017 | +0.031 ± 0.016 |
| **Temporal Retrieval + bge-reranker-v2-m3** | **0.512** | **0.597** | 19.3% | 26.0% | +0.013 ± 0.017 | +0.032 ± 0.015 |

Δ giữa các hệ thống với v4: Temporal − Plain RAG EM **+0.128 ± 0.023**, Temporal − Plain RAG + bge EM **+0.060 ± 0.021**; Plain RAG + bge − Plain RAG EM +0.068 ± 0.020 (với v1: +0.140, +0.068, +0.072). Từ chối dù đáp án có trong ngữ cảnh: 51, 56, 57 câu (với v1: 81, 85, 76). Trả lời dựa chunk tương lai: Temporal 15/323, Plain RAG + bge 16/293, Plain RAG 11/243.

v4 tăng nhẹ EM (dưới 2 sai số chuẩn) và F1 (khoảng 2 sai số chuẩn), giảm từ chối 6 đến 9 điểm phần trăm, đổi lại trả lời sai nhiều hơn (Temporal: 18.5% lên 26.0%). Kết luận về khoảng cách giữa các hệ thống không đổi. Số thô: `local/results/answers_test_analysis_k5_g35_v4.txt`, `answers_test_k5_g35_v4_vs_v1.txt`.

### Gemma 4 (valid top-5)

Thử Gemma 4 qua Gemini API để có thêm LLM kiểm tra việc chọn prompt (`google_gemma26` = `gemma-4-26b-a4b-it`, MoE khoảng 4B tham số hoạt động; `google_gemma31` = `gemma-4-31b-it`, dense; profile trong `configs/config.dev.yaml`). Chỉ chạy trên `valid`, không chạy trên test. Kết quả EM ở bảng trên; 31B nhỉnh hơn 26B ở mọi prompt (EM Temporal + bge với v1: 0.490 so với 0.459; với v3: 0.551 so với 0.510).

- **Hạn mức:** 30 request/phút, 16.000 token/phút, 14.400 request/ngày. Giới hạn thật là token/phút: một request 4 câu khoảng 3.050 token (v1) và 3.330 token (v4), nên tối đa khoảng 4 request/phút; 3 request/phút vẫn gặp 429 nhưng cơ chế chờ rồi thử lại vượt qua được (khoảng 8 đến 16 phút mỗi lượt, so với 2 phút của Gemini).
- **JSON theo schema:** cả hai model trả đúng định dạng `AnswerBatch`, 0 lô sai định dạng.
- **Lỗi mạng:** `httpx.RemoteProtocolError` / `ReadError` làm sập tiến trình vì không được xếp vào lỗi tạm thời; đã sửa (`_is_transient` nhận `TransportError`, kèm test).
- **Lỗi riêng của 31B:** một lô 4 câu (Ruud Lubbers, Sarah Bond, Senate of the Kingdom of Italy, Sergio Pérez) luôn trả `500 INTERNAL` khi gộp; chạy riêng từng câu thì qua (4/4), nên v3 trên Temporal + bge của 31B có 4 câu chạy bù bằng 1 câu/request (cờ `--ids-file` của `scripts/generate_answers.py`).

## 8. Tái lập

`local/` là thư mục scratch (gitignore). Các bước: `collect_configs.py` (gom cấu hình), `run_replay.py <tập>` (chạy lại, nhãn = sha1 cấu hình), `select_top.py`, `compare_valid.py`, `random_search.py gen|top`, `compare_search.py`. Cross-encoder chạy qua server GPU từ xa (`TAM_RERANK_REMOTE_URL`, mặc định tắt) cho bge-v2-m3, L12, L6, bge-base; jina chạy CPU cục bộ.
