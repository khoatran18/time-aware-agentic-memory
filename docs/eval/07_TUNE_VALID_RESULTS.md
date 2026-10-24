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

Thêm hai cờ tùy chọn cho `scripts/evaluate.py` (`--decay-lambda`, `--top-n`, mặc định theo config; mọi cấu hình cũ đều dùng 0.5 và 50 nên kết quả cũ không đổi). Mỗi họ (L6, L12, bge-v2-m3) chạy 80 cấu hình = cấu hình xuất phát (tốt nhất trên `tune` ở bước 1) và 79 điểm ngẫu nhiên (seed 0) trong không gian:

| Tham số | Giá trị thử |
|---|---|
| `w2` (`w1 = 1 − w2`) | 0.1, 0.2, 0.3, 0.4, 0.5 |
| `decay_lambda` | 0.1, 0.25, 0.5, 1, 2 |
| `t_unknown` | 0.05, 0.1, 0.2, 0.3 |
| `open_decay` | 0.02, 0.05, 0.1, 0.2 |
| `end_mode` | `unknown_decay`, `decay` |
| `decay_from` | `start`, `end` |
| `rerank_top` | 10, 15, 20, 30, 40 |
| `rerank_mode` (và `rerank_alpha` nếu `mix`) | `replace`, `mix` (0.3, 0.5, 0.7) |
| `rerank_norm` | `minmax`, `zscore` |
| `top_n` | 50, 100 |
| `time_mode` / `overlap` | `point`, `range` + `binary`, `range` + `coverage` |

Cấu hình tốt nhất trên `tune` của mỗi họ (240 cấu hình, 0 lỗi), xác nhận **một lần** trên `valid`:

| Họ | Cấu hình | `mrr` tune (xuất phát) | `mrr` tune (sau quét) | `mrr` valid | hit@5 | ans_valid@5 | Δ valid so với xuất phát | Δ valid so với nền không CE |
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
6. **Giới hạn.** Ablation `no_temporal` vẫn giữ lọc cứng `start ≤ T_req` (hiện không có cờ tắt hẳn lọc cứng); trường hợp không có lọc cứng được đại diện bởi Plain RAG. Cổng đầu-cuối EM/F1 chưa làm (chưa có tầng sinh câu trả lời).

## 7. Tái lập

`local/` là thư mục scratch (gitignore). Các bước: `collect_configs.py` (gom cấu hình), `run_replay.py <tập>` (chạy lại, nhãn = sha1 cấu hình), `select_top.py`, `compare_valid.py`, `random_search.py gen|top`, `compare_search.py`. Cross-encoder chạy qua server GPU từ xa (`TAM_RERANK_REMOTE_URL`, mặc định tắt) cho bge-v2-m3, L12, L6, bge-base; jina chạy CPU cục bộ.
