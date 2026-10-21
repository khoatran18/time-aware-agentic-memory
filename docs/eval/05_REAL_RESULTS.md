# Kết quả bộ thật (400 câu)

Chạy lại **toàn bộ 142 kịch bản đã chạy ở bộ local** (cùng cấu hình, lấy từ `metrics.json` của từng dòng trong `dataset/eval/results_local.csv`) trên bộ thật 400 câu. Quy ước tên cấu hình xem đầu [`04_TEST_RESULTS.md`](04_TEST_RESULTS.md). Danh sách câu: [`real_subset_cases.csv`](../../dataset/eval/real_subset_cases.csv); câu bị loại và lý do: [`real_subset_dropped.csv`](../../dataset/eval/real_subset_dropped.csv); cách dựng bộ và việc thay 1 câu: [`process/06`](../process/06_EVAL_SUBSET.md).

## 1. Tóm tắt

1. **Cơ chế 1 hơn Plain RAG rõ ràng**: `mrr` 0.339 (Plain RAG dense) lên 0.444 (+0.104 ± 0.036 khi ghép cặp từng câu), và `leakage_rate` từ 0.665 xuống 0. Kết luận của local được giữ.
2. **Điểm tuyệt đối thấp hơn local nhiều**: `mrr` cao nhất 0.452 và `hit@5` cao nhất 0.692 (local: 0.581 và 0.825). Phần lớn do local nhỏ (40 câu, sai số lớn) và dễ hơn; trung bình `mrr` của 140 cấu hình giảm từ 0.482 xuống 0.412.
3. **Thứ hạng các cấu hình chuyển từ local sang bộ thật gần như nguyên vẹn**: tương quan hạng Spearman 0.961 (`mrr`) và 0.806 (`hit@5`). Cấu hình tốt nhất ở local đứng hạng 7/140 ở bộ thật, `mrr` kém cấu hình số 1 chỉ 0.006, nằm trong sai số.
4. **Đúng chiều ở cả hai bộ, nhưng nhỏ hơn ở bộ thật**: bỏ BM25 (+0.03), bật nhánh chunk không mốc (+0.02). **Không còn đúng**: `unknown_decay` hơn `stored` (+0.003 ± 0.010, không phân biệt được).
5. **Mất điểm chủ yếu do xếp hạng trong cùng một trang**, không phải do tìm trượt trang: 21% câu có chunk đúng trong ứng viên nhưng xếp sau top-5, và 94% trong số đó có kết quả hạng 1 là chunk khác của **chính trang đáp án** (thời kỳ khác). 88% các câu này có chunk đúng với khoảng `[start, end]` đã kết thúc trước `t_req`. 9.3% câu bị bộ lọc cứng loại mất chunk đúng, phần lớn do chunk đáp án theo nhãn nói về thời kỳ sau câu hỏi (chunk đáp án theo nhãn nằm sau thời điểm hỏi; đọc tay 21 ca nhóm C cho thấy phần lớn không phải ingestion gán sai `start`, xem mục 7). Chấm theo chuỗi đáp án trong top-5 cho 0.81 thay vì 0.69.

## 2. Thiết lập

| Mục | Giá trị |
|---|---|
| Bộ câu hỏi | `dataset/eval/real_subset.json`: 400 câu (8 domain × 50), 204 trang, 35 câu mượn từ D/train; 399 câu có chunk đáp án trong kho (`n_answerable`) |
| Kho | Qdrant `tam_chunks_dev_real`, 6737 điểm (nạp bằng `--keep-undated`) |
| LLM nạp kho | Gemini 3.5 flash-lite gọi thẳng API Google (có structured output); `output/20261020_143820/extractions.jsonl` |
| LLM Profiler | Gemini 3.1 flash-lite gọi thẳng; `output/20261020_144033/profiler.jsonl`, 400/400 câu, 0 lỗi |
| Chế độ | `e2e` (Profiler lấy `t_req` từ câu hỏi), mức `hard`, `top_k` 5, `top_n` 50 |
| Chạy | `local/run_real_eval.py` (không gọi LLM), 142 lần, 0 lỗi, rồi thêm lưới chunk liền kề 32 lần (`local/run_neighbors.py`); gom bằng `scripts/summarize_runs.py`, vẽ bằng `scripts/plot_results.py`, phễu bằng `scripts/funnel_real.py` |
| Dữ liệu | [`results_real.csv`](../../dataset/eval/results_real.csv) (132 nhóm xếp hạng + 38 nhóm có chunk liền kề), [`results_compare.csv`](../../dataset/eval/results_compare.csv) (local và real cạnh nhau, 170 dòng), [`real_funnel.csv`](../../dataset/eval/real_funnel.csv) |

Khác biệt với local khi so sánh: nạp kho và Profiler của hai bộ không cùng model (local: 3.5 qua 9router cho cả hai; real: 3.5 nạp kho, 3.1 Profiler). Cỡ mẫu: `mrr` có sai số chuẩn khoảng 0.07 ở 40 câu, khoảng 0.02 ở 400 câu, nên chênh lệch dưới ~0.04 ở local không phân biệt được, còn ở bộ thật chỉ khoảng 0.04 là cần thiết (ghép cặp: 0.01–0.04, xem mục 6).

## 3. Giá trị cao nhất của `mrr` và `hit@k`

Trong các cấu hình `e2e` (140 cấu hình; không tính 2 cấu hình `oracle`):

| Chỉ số | Cao nhất ở local | Cấu hình ở local | Cao nhất ở bộ thật | Cấu hình ở bộ thật |
|---|---|---|---|---|
| `mrr` | 0.581 | 1 cấu hình, vd tìm kiếm dense · end unknown decay 0.2 · t_unknown 0.1 | 0.452 | 1 cấu hình, vd tìm kiếm dense · end unknown decay 0.05 · t_unknown 0.0 |
| `hit@1` | 0.425 | 8 cấu hình, vd tìm kiếm dense · end unknown decay 0.2 · t_unknown 0.1 | 0.311 | 4 cấu hình, vd tìm kiếm dense · end unknown decay 0.05 · t_unknown 0.1 |
| `hit@3` | 0.750 | 6 cấu hình, vd tìm kiếm dense · end unknown decay 0.1 · t_unknown 0.4 | 0.571 | 4 cấu hình, vd tìm kiếm dense · end unknown decay 0.05 · t_unknown 0.1 |
| `hit@5` | 0.825 | 6 cấu hình, vd tìm kiếm dense · end unknown decay 0.2 · t_unknown 0.1 | 0.692 | 2 cấu hình, vd tìm kiếm dense · end unknown decay 0.2 · t_unknown 0.1 |

Dòng "vd" là một đại diện; nhiều cấu hình đồng hạng ở `hit@k` vì `hit@k` chỉ nhận giá trị rời rạc (1/40 = 0.025 ở local, 1/399 ở bộ thật). Các cấu hình đứng đầu đều là nền dense, `unknown_decay` và `t_unknown` thấp. Ngoại lệ duy nhất: `hit@3` ở bộ thật có thêm một cấu hình BM25 0.25 đồng hạng; không có cấu hình hybrid hay Plain RAG nào đứng đầu ở chỉ số nào.

Các giá trị `mrr` cao nhất tuyệt đối vẫn thấp (0.45) và `hit@5` chỉ 0.69. Vì sao: xem mục 5.

## 4. Cấu hình tốt nhất ở local có tốt nhất ở bộ thật không?

**Không phải số 1, nhưng nằm trong nhóm đầu và chênh lệch nằm trong sai số.**

| Chỉ số so khớp | Giá trị |
|---|---|
| Tương quan hạng Spearman `mrr`, local so với real (140 cấu hình) | **0.961** |
| Tương quan hạng Spearman `hit@5` | 0.806 |
| `mrr` trung bình của 140 cấu hình | local 0.482, real 0.412 (giảm 0.070) |
| Cấu hình tốt nhất ở local (dense · unknown decay 0.2 · `t_unknown` 0.1, `mrr` 0.581) | ở bộ thật `mrr` 0.446, hạng **7/140**; cấu hình số 1 ở bộ thật là 0.452 |
| 6 cấu hình đứng đầu ở local | hạng ở bộ thật lần lượt 7, 10, 11, 16, 3, 4 (đều trong top 12%) |

![`mrr` local so với bộ thật](figures_real/compare_mrr.svg)

![`hit@5` local so với bộ thật](figures_real/compare_hit5.svg)

Mỗi điểm là một cấu hình; đường nét đứt là y = x. Mọi điểm nằm dưới đường chéo (bộ thật thấp hơn local) và các cụm giữ nguyên thứ tự trên trục: Plain RAG và "chỉ lọc" thấp nhất, rồi hybrid, rồi BM25 một phần, rồi dense. Thứ tự giữa các cấu hình dense gần nhau (0.43–0.45) thì lộn xộn, đúng như dự đoán vì chênh lệch của chúng nhỏ hơn sai số.

Kết luận thực hành: **chọn họ cấu hình** (dense, bật `t_unknown`) bằng local là đúng; **chọn tham số tinh** (`d` của `unknown_decay`, giá trị `t_unknown` trong 0.0–0.3) bằng 40 câu thì không đáng tin, vì các cấu hình đó chênh nhau 0.00–0.01 ở bộ thật.

## 5. Vì sao `mrr` và `hit@5` vẫn thấp: phễu từng câu

Mỗi câu có chunk đáp án (399 câu) rơi vào đúng một nhóm:

![Phễu: chunk đúng rơi ở đâu](figures_real/funnel.svg)

| Nhóm | Dense · stored · `t_unknown` 0.1 | Dense · unknown decay 0.1 · `t_unknown` 0.1 | Plain RAG dense |
|---|---|---|---|
| Trúng top-5 (`hit@5`) | 271 (67.9%) | 274 (68.7%) | 219 (54.9%) |
| Không vào 50 ứng viên | 3 | 3 | 10 |
| Bị lọc cứng: chunk đúng không có mốc | 0 (nhánh `t_unknown` cứu) | 0 | không lọc |
| Bị lọc cứng: `start` của chunk đúng **sau** `t_req` | **37 (9.3%)** | **37 (9.3%)** | không lọc |
| Vào ứng viên nhưng xếp sau top-5 | **88 (22.1%)** | **85 (21.3%)** | **170 (42.6%)** |

Ba nguyên nhân, theo mức ảnh hưởng:

1. **Xếp hạng trong cùng một trang (21–22% câu, nguyên nhân lớn nhất).** Trang TimeQA dài, nhiều chunk cùng nói về một thực thể ở các thời kỳ khác nhau, nên chunk đúng và chunk gần-đúng giống nhau về ngữ nghĩa và chỉ khác nhau ở mốc thời gian. Ở cấu hình tốt nhất, trong 85 câu trượt này có 80 câu (94%) có kết quả hạng 1 nằm trên chính trang đáp án, và 65 câu (76%) có cả 5 kết quả đều thuộc trang đó; trung vị hạng của chunk đúng trong danh sách 50 là 2. Plain RAG cũng vậy (176/180 câu, 98%). Nghĩa là hệ **tìm đúng trang nhưng chọn nhầm thời kỳ**; việc của điểm thời gian là chọn đúng thời kỳ, và nó chỉ cứu được một phần (`temporal_helped` 136, `temporal_hurt` 89 câu).
2. **Bộ lọc cứng loại nhầm chunk đúng (9.3% câu).** Xem mục 7. Đây là trần cứng: không cấu hình nào giữ bộ lọc `start_time <= T_req` có thể vượt `hit@5` = (399 − 37) / 399 = **90.7%** (và 81.5% nếu tắt nhánh chunk không mốc, vì thêm 37 chunk không mốc nữa bị loại).
3. **Không vào danh sách ứng viên (≤ 0.8% ở Cơ chế 1, 2.5% ở Plain RAG)**: không đáng kể; truy xuất dense lấy được chunk đúng trong top 50 ở 97.5% câu khi không lọc (Plain RAG).

### 5.1 Vì sao chunk đúng bị xếp sau top-5

Phân tích 75 câu trượt top-5 mà chunk đúng vẫn qua bộ lọc (dense · stored · `t_unknown` 0.1), so điểm thời gian của chunk đúng và chunk hạng 1 (theo nhãn `start`/`end` lúc nạp kho):

| Chunk đúng | Chunk hạng 1 | Số câu |
|---|---|---|
| **đã kết thúc trước `t_req`** (điểm thời gian giảm dần) | khớp `t_req` (điểm 1.0) | 55 |
| đã kết thúc trước `t_req` | không mốc / cũng đã kết thúc | 11 |
| khớp `t_req` (điểm 1.0) | khớp (1.0) hoặc loại khác | 9 |

- **66/75 câu (88%): chunk đúng có khoảng `[start, end]` kết thúc trước `t_req`.** Khoảng cách `t_req − end` có trung vị 7.3 năm: 18 câu dưới 1 năm (sát biên, vd chunk "đầu 1998" gán `end` 31/3/1998, câu hỏi tháng 4/1998), 9 câu 1–3 năm, 39 câu trên 3 năm. Điểm thời gian phạt nó nên chunk khớp `t_req` hơn nhưng sai nội dung vượt lên.
- Chỉ **9 câu** là hòa thật sự về thời gian, tức xếp hạng hoàn toàn do điểm ngữ nghĩa.
- Chunk đúng nằm ở hạng 6–10 (33 câu), 11–20 (33 câu), trên 20 (9 câu): kéo top-k lên 10 là đủ cứu một nửa.
- Nguyên nhân lớn nhất là chunk đáp án theo nhãn của TimeQA là **đoạn có chứa chuỗi đáp án**, không bảo đảm đoạn đó nói về đúng thời kỳ của câu hỏi (xem mục 7), nên dù ingestion gán mốc đúng cho chính đoạn đó, nó vẫn lệch với `t_req`. Phần còn lại là `t_req` của Profiler quá thô (vd "late 1900s" thành 1999-12-31, câu hỏi khoảng "between Aug 2005 and Sep 2006" thành điểm cuối khoảng).

**Hit@k theo độ sâu** (cùng cấu hình tốt nhất, dùng hạng cuối cùng của chunk đúng trong 50 ứng viên):

| k | 1 | 3 | 5 | 10 | 15 | 20 | 30 | 50 |
|---|---|---|---|---|---|---|---|---|
| Cơ chế 1 (dense · unknown decay 0.1 · `t_unknown` 0.1) | 0.296 | 0.569 | 0.687 | 0.789 | 0.855 | 0.877 | 0.895 | 0.900 |
| Plain RAG dense | 0.226 | 0.424 | 0.549 | 0.762 | 0.862 | 0.895 | 0.937 | 0.975 |

Cơ chế 1 hơn rõ ở k nhỏ (≤ 10), nhưng **từ k ≥ 15 Plain RAG bằng và vượt** vì bộ lọc cứng đã loại mất 9.3% chunk đúng; trần của Cơ chế 1 là 0.900 trong khi Plain RAG đạt 0.975 ở k = 50. Top-20 đã gần bão hòa (0.877).

**Nếu chấm bằng chuỗi đáp án thay vì chunk id.** Tỉ lệ câu có chuỗi đáp án (`targets`) xuất hiện trong văn bản của top-5:

| Cấu hình | `hit@5` theo chunk id | Top-5 có chứa chuỗi đáp án |
|---|---|---|
| Plain RAG dense | 0.549 | 0.667 |
| Cơ chế 1 · hybrid · stored · tắt | 0.627 | 0.734 |
| Cơ chế 1 · dense · stored · tắt | 0.622 | 0.752 |
| Cơ chế 1 · dense · stored · `t_unknown` 0.1 | 0.679 | 0.805 |
| Cơ chế 1 · dense · unknown decay 0.1 · `t_unknown` 0.1 | 0.687 | 0.812 |

Chỉ số thứ ba (top-5 có chunk vừa chứa chuỗi đáp án vừa có `[start, end]` bao `t_req`, chỉ tính chunk có mốc): Plain RAG **0.406**, Cơ chế 1 tốt nhất **0.627** (+0.22, so với +0.14 của `hit@5` theo chunk id); tính cả chunk không mốc: 0.486 và 0.689. Định nghĩa, ví dụ đúng và sai, và hạn chế ở [`decisions/07`](../decisions/07_RANKING_AND_TIME_RANGE_PROPOSALS.md) đề xuất 5.

Chênh 12 điểm cho thấy nhiều câu "trượt" thật ra có chunk khác chứa đúng đáp án trong top-5. Đây là cận trên (chuỗi đáp án có thể xuất hiện trong chunk nói về thời kỳ khác); thứ hạng giữa các cấu hình không đổi.

`hit@1` thấp (0.31) vì đa số câu hỏi TimeQA có nhiều chunk "gần-đúng" cùng trang; `ctx_hit` (có chunk đúng trong ngữ cảnh gửi LLM) bằng `hit@5` khi không lấy thêm chunk liền kề (mục 6.5).

## 6. Từng nhóm kịch bản trên bộ thật

Mỗi bảng có cột local để thấy chiều thay đổi. Tên cấu hình theo quy ước ở `04`; toàn bộ 132 nhóm xếp hạng ở phụ lục.

### 6.1 Baseline và "chỉ lọc thời gian" (đợt 1)

| Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `hit@5` local | `mrr` local |
|---|---|---|---|---|---|---|
| Plain RAG · dense | 0.226 | 0.424 | 0.549 | **0.339** | 0.500 | 0.340 |
| Plain RAG · hybrid | 0.226 | 0.388 | 0.509 | **0.322** | 0.475 | 0.245 |
| Plain RAG · BM25 | 0.178 | 0.338 | 0.424 | **0.267** | 0.250 | 0.179 |
| Chỉ lọc thời gian · dense | 0.268 | 0.494 | 0.607 | **0.389** | 0.600 | 0.428 |
| Chỉ lọc thời gian · hybrid | 0.226 | 0.444 | 0.554 | **0.350** | 0.575 | 0.323 |

- Plain RAG dense (0.339) tốt hơn hẳn Plain RAG hybrid (0.322) và BM25 (0.267): kết hợp BM25 vào RRF không giúp trên bộ này.
- "Chỉ lọc thời gian" (bỏ điểm thời gian, chỉ giữ bộ lọc `start <= T_req`) đã nâng `mrr` từ 0.339 lên 0.389 (dense) và 0.322 lên 0.350 (hybrid): **bộ lọc cứng một mình đóng góp phần lớn lợi ích**. Điểm thời gian (`W2` = 0.3) cộng thêm 0.03 nữa (0.389 lên 0.418).

### 6.2 Trọng số BM25 và các thành phần trên nền dense (đợt 1b, 1c)

| Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `hit@5` local | `mrr` local |
|---|---|---|---|---|---|---|
| hybrid · stored · tắt | 0.241 | 0.509 | 0.627 | **0.386** | 0.650 | 0.420 |
| hybrid · stored · `t_unknown` 0.1 | 0.251 | 0.526 | 0.649 | **0.401** | 0.675 | 0.459 |
| BM25 0.5 · stored · tắt | 0.261 | 0.539 | 0.649 | **0.406** | 0.725 | 0.474 |
| BM25 0.25 · stored · tắt | 0.268 | 0.554 | 0.659 | **0.418** | 0.725 | 0.507 |
| BM25 0.25 · stored · `t_unknown` 0.1 | 0.283 | 0.561 | 0.682 | **0.434** | 0.725 | 0.522 |
| dense · stored · tắt | 0.288 | 0.534 | 0.622 | **0.418** | 0.675 | 0.494 |
| dense · stored · `t_unknown` 0.1 | 0.298 | 0.564 | 0.679 | **0.441** | 0.800 | 0.542 |

- Thứ tự `mrr` khi `t_unknown` tắt: dense (0.418) ≈ BM25 0.25 (0.418) > BM25 0.5 (0.406) > hybrid (0.386); khi `t_unknown` 0.1: dense 0.441 > BM25 0.25 0.434 > hybrid 0.401. Giảm BM25 đều có lợi, bỏ hẳn tốt nhất hoặc ngang bằng; ghép cặp dense so với hybrid: hơn 74 câu, kém 50, +0.032 ± 0.025.
- Bật `t_unknown` 0.1 cải thiện mọi nền (dense +0.023, hybrid +0.015, BM25 0.25 +0.016); ghép cặp dense: hơn 39, kém 19, +0.023 ± 0.016.

### 6.3 Cách chấm `end` (đợt 3, 3d)

| Cách chấm `end` (nền dense) | `t_unknown` | `hit@1` | `hit@3` | `hit@5` | `mrr` | `hit@5` local | `mrr` local |
|---|---|---|---|---|---|---|---|
| stored | tắt | 0.288 | 0.534 | 0.622 | **0.418** | 0.675 | 0.494 |
| stored | 0.1 | 0.298 | 0.564 | 0.679 | **0.441** | 0.800 | 0.542 |
| open | tắt | 0.286 | 0.536 | 0.607 | **0.413** | 0.700 | 0.519 |
| open | 0.1 | 0.293 | 0.561 | 0.647 | **0.430** | 0.725 | 0.525 |
| decay 0.1 | tắt | 0.273 | 0.531 | 0.634 | **0.411** | 0.700 | 0.471 |
| decay 0.1 | 0.1 | 0.293 | 0.556 | 0.684 | **0.438** | 0.800 | 0.544 |
| unknown decay 0.05 | tắt | 0.286 | 0.544 | 0.632 | **0.421** | 0.725 | 0.524 |
| unknown decay 0.05 | 0.1 | 0.311 | 0.571 | 0.679 | **0.451** | 0.800 | 0.575 |
| unknown decay 0.1 | tắt | 0.286 | 0.549 | 0.632 | **0.420** | 0.725 | 0.525 |
| unknown decay 0.1 | 0.1 | 0.296 | 0.569 | 0.687 | **0.444** | 0.825 | 0.580 |
| unknown decay 0.2 | tắt | 0.291 | 0.541 | 0.639 | **0.425** | 0.725 | 0.519 |
| unknown decay 0.2 | 0.1 | 0.301 | 0.571 | 0.692 | **0.446** | 0.825 | 0.581 |
| unknown decay 0.3 | tắt | 0.288 | 0.529 | 0.632 | **0.420** | 0.700 | 0.500 |
| unknown decay 0.3 | 0.1 | 0.301 | 0.566 | 0.689 | **0.444** | 0.825 | 0.554 |

- Thứ tự `mrr` giữ nguyên như local: unknown decay ≥ stored > decay > open, nhưng các giá trị cách nhau 0.002–0.015.
- `open` (coi mọi chunk đang kéo dài, điểm 1.0) kém rõ rệt nhất ở `hit@5` (0.647 so với 0.679 của stored khi `t_unknown` 0.1).
- `unknown_decay` so với `stored` (cùng `t_unknown` 0.1): hơn 19 câu, kém 17, **+0.003 ± 0.010**, tức không có lợi thế. Ở local nó cao nhất, nhưng đó là cận trên của hơn 140 cấu hình trên 40 câu.

Lưới `mrr` của `unknown_decay` theo `d` và `t_unknown` (nền dense, bộ thật):

| `d` (unknown decay) \ `t_unknown` | tắt | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.7 |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.421 | 0.452 | 0.451 | 0.451 | 0.448 | 0.447 | 0.440 | 0.424 |
| 0.1 | 0.420 | 0.443 | 0.444 | 0.443 | 0.442 | 0.437 | 0.429 | 0.418 |
| 0.2 | 0.425 | 0.446 | 0.446 | 0.443 | 0.441 | 0.437 | 0.429 | 0.418 |
| 0.3 | 0.420 | 0.446 | 0.444 | 0.441 | 0.440 | 0.437 | 0.426 | 0.416 |

![Bảng màu mrr theo t_unknown](figures_real/t_unknown_grid.svg)

Khi bật `t_unknown` từ 0.0 đến 0.3, mọi ô nằm trong 0.440–0.452 (chênh 0.012, dưới sai số); `d` = 0.05 nhỉnh hơn một chút nhưng không đáng tin. Không có "cao nguyên" nào tách hẳn khỏi phần còn lại; lưới giảm khi `t_unknown` ≥ 0.5.

### 6.4 Nhánh chunk không mốc `t_unknown` (đợt 4, 4b)

| `t_unknown` (dense · stored) | `hit@5` | `mrr` | `hit@5` local | `mrr` local | `undated_in_results_rate` |
|---|---|---|---|---|---|
| tắt | 0.622 | **0.418** | 0.675 | 0.494 | 0.000 |
| 0.0 | 0.684 | **0.442** | 0.800 | 0.531 | 0.340 |
| 0.1 | 0.679 | **0.441** | 0.800 | 0.542 | 0.403 |
| 0.2 | 0.677 | **0.440** | 0.800 | 0.541 | 0.455 |
| 0.3 | 0.669 | **0.438** | 0.775 | 0.536 | 0.502 |
| 0.4 | 0.644 | **0.432** | 0.775 | 0.534 | 0.562 |
| 0.5 | 0.634 | **0.425** | 0.775 | 0.510 | 0.590 |
| 0.7 | 0.624 | **0.413** | 0.725 | 0.492 | 0.672 |

![mrr theo t_unknown](figures_real/t_unknown_curve.svg)

- `t_unknown` 0.0 đến 0.2 là đỉnh (0.440–0.442 so với 0.418 khi tắt); từ 0.4 trở lên giảm dần và xuống dưới mức tắt ở 0.7 (0.413). Lợi ích chủ yếu đến từ việc **đưa chunk không mốc vào danh sách ứng viên**, không phải từ giá trị điểm cụ thể.
- `undated_in_results_rate` (tỉ lệ câu có chunk không mốc trong top-5) tăng theo `t_unknown`; tăng từ 0.34 ở 0.0 lên 0.67 ở 0.7; ở 0.1 là 0.40, nghĩa là chunk không mốc xuất hiện trong top-5 của khoảng 40% số câu, và vẫn có lợi ròng.

### 6.5 Chunk liền kề (đợt 3b)

| Cấu hình | `hit@5` | `ctx_hit` (ngữ cảnh) | `mrr` | `ctx_hit` local |
|---|---|---|---|---|
| dense · stored · `t_unknown` 0.1, không lấy thêm | 0.679 | **0.679** | 0.441 | 0.800 |
| cùng cấu hình, lấy thêm 1 chunk liền kề | 0.679 | **0.772** | 0.441 | 0.850 |
| dense · stored · tắt, không lấy thêm | 0.622 | **0.622** | 0.418 | 0.675 |
| cùng cấu hình, lấy thêm 1 chunk liền kề | 0.622 | **0.697** | 0.418 | 0.750 |
| hybrid · stored · tắt, không lấy thêm | 0.627 | **0.627** | 0.386 | 0.650 |
| cùng cấu hình, lấy thêm 1 | 0.627 | **0.707** | 0.386 | 0.725 |
| cùng cấu hình, lấy thêm 2 | 0.627 | **0.737** | 0.386 | 0.725 |


**Lưới 32 kịch bản có chunk liền kề (ở mỗi bộ):** nền {dense, hybrid} × cách chấm `end` {stored, open, decay 0.1, unknown decay 0.1} × `t_unknown` {tắt, 0.1} × cửa sổ {1, 2}; thêm vào CSV (38 nhóm ở phụ lục B).

| Bộ | Cửa sổ | `ctx_hit` − `hit@5` (TB 32 lần) | Chunk trong ngữ cảnh (TB) | Câu được cứu thêm (TB) |
|---|---|---|---|---|
| Bộ thật | 1 | +0.082 | 8.4 (so với 5) | 33 |
| Bộ thật | 2 | +0.115 | 10.7 | 46 |
| Local | 1 và 2 | +0.055 | 7.9 / 9.9 | 2 |

Ở cấu hình tốt nhất (dense · unknown decay 0.1 · `t_unknown` 0.1): `hit@5` 0.687 và `mrr` 0.444 **không đổi** với mọi cửa sổ; `ctx_hit` 0.687 lên **0.769** (cửa sổ 1, 8.2 chunk) và **0.789** (cửa sổ 2, 10.4 chunk). Câu nhiều chunk đúng (`ctx_multi_all_hit`) từ 0.167 lên 0.167 (cửa sổ 1) và 0.250 (cửa sổ 2) trên 12 câu. Ở local lợi ích nhỏ vì kho nhỏ (chỉ cứu 2 câu).

Lấy thêm chunk liền kề **không đổi `hit@5` và `mrr`** (xếp hạng không đổi), chỉ tăng `ctx_hit` (chunk đúng có trong ngữ cảnh đưa vào LLM): +0.09 ở dense · `t_unknown` 0.1 (0.679 lên 0.772). Lấy 2 chunk mỗi phía thêm +0.03 so với 1 chunk ở hybrid. Đây là cách tăng độ phủ ngữ cảnh mà không động đến xếp hạng; chi phí là gửi thêm 1–2 chunk mỗi kết quả.

### 6.6 Domain: cộng điểm hay lọc cứng (đợt 5)

| Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `hit@5` local | `mrr` local |
|---|---|---|---|---|---|---|
| tìm kiếm dense · end stored · cộng điểm domain W3 0.1 · tắt | 0.291 | 0.541 | 0.632 | **0.422** | 0.675 | 0.494 |
| tìm kiếm hybrid · end stored · cộng điểm domain W3 0.2 · tắt | 0.241 | 0.514 | 0.629 | **0.388** | 0.650 | 0.420 |
| tìm kiếm hybrid · end stored · cộng điểm domain W3 0.05 · tắt | 0.241 | 0.511 | 0.627 | **0.388** | 0.650 | 0.420 |
| tìm kiếm hybrid · end stored · cộng điểm domain W3 0.1 · tắt | 0.241 | 0.514 | 0.627 | **0.388** | 0.650 | 0.420 |
| tìm kiếm hybrid · end stored · lọc cứng domain · tắt | 0.243 | 0.501 | 0.609 | **0.381** | 0.650 | 0.420 |


Không có cấu hình domain nào hơn mức nền: cộng điểm W3 0.1 cho nền dense cho 0.422 (nền: 0.418), còn lọc cứng domain làm giảm (0.381 so với 0.386 của hybrid). `domain_given` chỉ có 140/400 câu (Profiler chỉ trích domain khi câu hỏi nêu rõ), nên thành phần này ít có chỗ tác động. Giữ quyết định domain là điểm cộng mềm ([`decisions/01`](../decisions/01_DOMAIN_AS_SOFT_BOOST.md)), không có lý do bật mặc định.

### 6.7 Oracle (đợt 2): dùng `t_req` từ nhãn thay Profiler

| Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `hit@5` local | `mrr` local |
|---|---|---|---|---|---|---|
| Oracle (t_req từ nhãn) · tìm kiếm hybrid · end stored · tắt | 0.253 | 0.536 | 0.639 | **0.398** | 0.700 | 0.458 |
| Oracle (t_req từ nhãn) · Chỉ lọc thời gian (bỏ điểm thời gian) · tìm kiếm hybrid | 0.236 | 0.454 | 0.554 | **0.357** | 0.625 | 0.353 |

`mrr` của oracle hybrid (0.398) chỉ hơn e2e hybrid cùng cấu hình (0.386) 0.012: **Profiler không phải nút thắt**. `t_req` của Profiler nằm trong khoảng nhãn thời gian ở 391/400 câu (97.8%), sai lệch tuyệt đối trung bình 4.5 năm so với mốc nhãn (vì nhãn là khoảng, không phải điểm).

### 6.8 Thử `decay_from: end` (phạt chunk đã hết hạn theo khoảng cách từ `end`)

Tùy chọn mới `retrieval.decay_from` (mặc định `start`, không đổi hành vi); xem [`decisions/07`](../decisions/07_RANKING_AND_TIME_RANGE_PROPOSALS.md) đề xuất 3. 34 kịch bản mỗi bộ, dữ liệu ở `dataset/eval/results_real_decay_from_end.csv` và `results_local_decay_from_end.csv`:

| Cấu hình | `mrr` bộ thật: `start` → `end` | `hit@5` bộ thật | `mrr` local | `hit@5` local |
|---|---|---|---|---|
| dense · stored · tắt | 0.418 → **0.428** | 0.622 → 0.647 | 0.494 → 0.517 | 0.675 → 0.725 |
| dense · stored · t_unknown 0.1 | 0.441 → **0.450** | 0.679 → 0.702 | 0.542 → 0.549 | 0.800 → 0.825 |
| dense · open · t_unknown 0.1 | 0.430 → **0.436** | 0.647 → 0.657 | 0.525 → 0.527 | 0.725 → 0.750 |
| dense · decay 0.1 · t_unknown 0.1 | 0.438 → **0.446** | 0.684 → 0.697 | 0.544 → 0.550 | 0.800 → 0.825 |
| dense · unknown decay 0.1 · t_unknown 0.1 | 0.444 → **0.452** | 0.687 → 0.699 | 0.580 → 0.586 | 0.825 → 0.850 |
| hybrid · stored · tắt | 0.386 → **0.392** | 0.627 → 0.644 | 0.420 → 0.445 | 0.650 → 0.675 |

`mrr` tăng ở 28/28 cặp so được (bộ thật +0.004 đến +0.010, trung bình +0.007; local +0.013). Ghép cặp từng câu ở cấu hình tốt nhất: +0.009 ± 0.009, 15 câu tăng và 14 giảm: mức tăng nhỏ, khoảng 95% chạm 0. Lợi ích có nhưng không phải nguyên nhân chính của các câu xếp sau top-5.

### 6.9 Chế độ khoảng và Profiler khoảng (decisions/07 đề xuất 1)

Lưới 140 kịch bản mỗi bộ dùng Profiler khoảng (prompt v2): nền {dense, hybrid} × cách chấm `end` {stored, open, decay 0.1, unknown decay 0.05/0.1/0.2} × `t_unknown` {tắt, 0.1}, cộng quét `t_unknown` cho hai cấu hình dense; mỗi cấu hình chạy 5 biến thể `(time_mode, overlap, decay_from)`. Biến thể gốc để so là `(point, binary, start)` với Profiler v2 (một điểm `qs`, phạt từ `start`), nên tách được tác dụng của Profiler khỏi tác dụng của retriever. Dữ liệu: [`results_real_range.csv`](../../dataset/eval/results_real_range.csv), [`results_local_range.csv`](../../dataset/eval/results_local_range.csv).

**Chênh trung bình so với biến thể gốc** (24 cấu hình mỗi biến thể):

| Biến thể | `mrr` bộ thật | `hit@5` | `ans_valid@5` | `mrr` local | số cấu hình `mrr` tăng/giảm (thật) |
|---|---|---|---|---|---|
| `point, binary, end` | +0.0047 | +0.012 | −0.001 | +0.016 | 23/0 |
| `range, binary, end` | +0.0052 | +0.017 | +0.008 | +0.013 | 21/3 |
| `range, binary, start` | +0.0006 | +0.005 | +0.009 | −0.004 | 14/7 |
| `range, coverage, end` | −0.0013 | +0.007 | −0.011 | +0.017 | 7/14 |

**Cấu hình dense · unknown decay 0.1 · `t_unknown` 0.1 (bộ thật, 399 câu)**

| Biến thể | `mrr` | `hit@5` | `ans_valid@5` | số câu bị lọc cứng chặn |
|---|---|---|---|---|
| gốc cũ (Profiler v1, một điểm, phạt từ `start`) | 0.444 | 0.687 | 0.627 | 74 |
| `point, binary, start` (Profiler v2) | 0.448 | 0.677 | 0.637 | 78 |
| `point, binary, end` | 0.454 | 0.692 | 0.637 | 78 |
| `range, binary, start` | 0.449 | 0.679 | 0.644 | 68 |
| **`range, binary, end`** | **0.456** | **0.699** | 0.644 | **68** |
| `range, coverage, end` | 0.449 | 0.684 | 0.627 | 68 |

Cao nhất mọi cấu hình: `mrr` **0.464** (dense, unknown decay 0.05, `t_unknown` 0.1, `range, binary, end`; `hit@5` 0.699), so với 0.452 trước đây.

**So sánh ghép cặp từng câu** (bộ thật, cấu hình trên, khoảng 95%):

| So sánh | `Δmrr` | `hit@5` thêm / mất |
|---|---|---|
| Profiler v2 (một điểm) so với v1 | +0.005 ± 0.015 | +10 / −14 |
| `range` so với `point` (cùng Profiler v2, phạt từ `end`) | +0.002 ± 0.014 | +8 / −5 |
| `range` so với `point` (phạt từ `start`) | +0.001 ± 0.014 | +8 / −7 |
| `decay_from end` so với `start` (một điểm) | +0.006 ± 0.008 | +9 / −3 |
| `coverage` so với `binary` (range, `end`) | −0.006 ± 0.012 | +3 / −9 |
| Tốt nhất mới (`range, binary, end`) so với gốc cũ | +0.012 ± 0.018 | +21 / −16 |

**Nhận định**
1. **Chế độ khoảng** giảm số câu bị lọc cứng từ 78 xuống 68 (cứu 10 chunk đúng), nhưng `mrr` gần như không đổi (+0.002 ± 0.014): không cải thiện đáng kể so với `point` cùng Profiler.
2. **Phạt từ `end`** vẫn là phần cho lợi ích nhất quán nhỏ (+0.005 đến +0.006; 23/24 cấu hình tăng), nhưng khoảng 95% của riêng nó chạm 0.
3. **Độ phủ (`coverage`) không tốt hơn nhị phân**: `mrr` thấp hơn 0.006 ở bộ thật và `ans_valid@5` thấp hơn; không nên dùng làm mặc định. Đã chạy thêm `range, coverage, start` (24 cấu hình mỗi bộ, 2026-10-20): so với `range, binary, start` thì `mrr` bộ thật −0.005 (tăng 4, giảm 20), local +0.004 (tăng 13, giảm 10); so với `range, binary, end` thì −0.010 (thật) và −0.013 (local). Không biến thể độ phủ nào hơn nhị phân.
4. **Số câu bị lọc cứng chặn** (`gold_blocked_by_filter`, đo bằng bộ lọc chặt) là 78 ở `point` và 68 ở `range`; trong đó 37 là chunk **không có mốc** (chỉ bị chặn khi `t_unknown` tắt) và còn lại là chunk có `start` sau cận trên của thời gian hỏi: 41 ở `point`, 31 ở `range`. Tức `range` cứu được 10 chunk, còn 31 chunk có `start` sau cả `qe` (đoạn nói về thời kỳ muộn hơn câu hỏi, xem mục 7).
5. **Profiler v2** (một điểm = đầu khoảng) cho ra `mrr` ngang v1 (+0.005 ± 0.015): đổi từ điểm cuối khoảng sang điểm đầu không làm tệ.
6. Cả bốn thay đổi cộng lại cho +0.012 ± 0.018 so với cấu hình gốc: cùng chiều tăng ở cả hai bộ nhưng **không vượt sai số ở 400 câu**; không nên coi là cải thiện đã được xác nhận. Chênh lệch này nhỏ hơn mức phát hiện được (khoảng 0.013) của một tập 400 câu (`decisions/08`).

### 6.10 Mỗi bản cập nhật đổi chỉ số thế nào (tổng hợp)

Tích lũy từng thay đổi, cùng nền dense và `t_unknown` 0.1 (trừ bước 0–2). Bước 1 đến 3 dùng Profiler v1 (`t_req` là điểm cuối khoảng); từ bước 4 dùng Profiler khoảng v2. Số liệu từ `results_{real,local}.csv` và `results_{real,local}_range.csv`; mọi biến thể trong bảng là một lần chạy, nên khác biệt dưới khoảng 0.013 (bộ thật, 400 câu) không phân biệt được.

**Bộ thật (399 câu có đáp án)**

| Bước | `hit@1` | `hit@5` | `mrr` (Δ so với bước trước) | `ans@5` | `ans_valid@5` |
|---|---|---|---|---|---|
| 0. Plain RAG dense (baseline, không lọc thời gian) | 0.226 | 0.549 | **0.339** | 0.664 | 0.409 |
| 1. Cơ chế 1: hybrid, `stored`, chunk không mốc tắt (cấu hình đầu tiên) | 0.241 | 0.627 | **0.386** | 0.739 | 0.624 |
| 2. + bỏ BM25 (dense) | 0.288 | 0.622 | **0.418** (+0.032) | 0.757 | 0.644 |
| 3. + bật `t_unknown` 0.1 | 0.298 | 0.679 | **0.441** (+0.023) | 0.810 | 0.637 |
| 4. + Profiler khoảng v2 (một điểm `qs`) | 0.303 | 0.679 | **0.445** (+0.004) | 0.805 | 0.639 |
| 5. + `decay_from: end` | 0.303 | 0.699 | **0.451** (+0.006) | 0.822 | 0.639 |
| 6. + chế độ khoảng `range` | 0.306 | 0.697 | **0.452** (+0.001) | 0.810 | 0.644 |
| 7. đổi sang `unknown_decay` 0.05 (từ bước 5, một điểm) | 0.326 | 0.692 | **0.463** (+0.012) | 0.822 | 0.632 |
| 8. + chế độ khoảng `range` | 0.323 | 0.699 | **0.464** (+0.002) | 0.820 | 0.642 |

**Bộ local (40 câu)**

| Bước | `hit@1` | `hit@5` | `mrr` (Δ so với bước trước) | `ans@5` | `ans_valid@5` |
|---|---|---|---|---|---|
| 0. Plain RAG dense (baseline, không lọc thời gian) | 0.225 | 0.500 | **0.340** | 0.600 | 0.475 |
| 1. Cơ chế 1: hybrid, `stored`, chunk không mốc tắt (cấu hình đầu tiên) | 0.275 | 0.650 | **0.420** | 0.750 | 0.675 |
| 2. + bỏ BM25 (dense) | 0.350 | 0.675 | **0.494** (+0.073) | 0.750 | 0.725 |
| 3. + bật `t_unknown` 0.1 | 0.375 | 0.800 | **0.542** (+0.049) | 0.850 | 0.725 |
| 4. + Profiler khoảng v2 (một điểm `qs`) | 0.400 | 0.800 | **0.555** (+0.012) | 0.875 | 0.775 |
| 5. + `decay_from: end` | 0.400 | 0.825 | **0.568** (+0.013) | 0.900 | 0.775 |
| 6. + chế độ khoảng `range` | 0.400 | 0.825 | **0.563** (-0.004) | 0.900 | 0.775 |
| 7. đổi sang `unknown_decay` 0.05 (từ bước 5, một điểm) | 0.475 | 0.825 | **0.610** (+0.042) | 0.900 | 0.775 |
| 8. + chế độ khoảng `range` | 0.475 | 0.825 | **0.606** (-0.004) | 0.900 | 0.775 |

Đọc bảng:
- Phần lớn mức tăng đến từ **lọc thời gian và bỏ BM25** (bước 0 đến 3: `mrr` +0.102 ở bộ thật, +0.202 ở local); đây là các thay đổi có ý nghĩa thống kê.
- Các cập nhật sau (Profiler khoảng, `decay_from end`, `range`) mỗi cái chỉ +0.000 đến +0.006 ở bộ thật; riêng `decay_from end` nhất quán nhất. `range` gần như không đổi `mrr` (+0.001 và −0.005 ở local).
- `unknown_decay` 0.05 thêm +0.012 (bộ thật) và +0.042 (local) so với `stored`; chưa kiểm tra ghép cặp, và do chọn trong hơn 140 cấu hình nên là cận trên.
- `ans_valid@5` (đúng thời kỳ theo nhãn của ingestion) ít đổi ở các bước sau (0.63 đến 0.64), tức các cập nhật chủ yếu xếp lại thứ hạng chứ không đưa thêm chunk đúng thời kỳ vào top-5.

### 6.11 Mở rộng ngữ cảnh cùng trang (decisions/07 đề xuất 7)

Cấu hình nền (dense, `unknown_decay` 0.05, `t_unknown` 0.1, `decay_from end`, point, Profiler v2): `hit@5` = `mrr` không đổi (0.692 / 0.463) vì chunk thêm không đổi thứ hạng; chỉ `ctx_hit` (top-5 + chunk thêm) và kích thước ngữ cảnh đổi. Lưới 34 kịch bản mỗi bộ (`local/run_page_expand.py`, không gọi LLM; code: `page_expand` = `none | time | page`, `page_top`, `page_per`; chunk cùng trang lấy theo id `#0..#99`, sắp theo gần chunk của top-5; `page` = chỉ hard filter (đối chứng), `time` = thêm điều kiện còn hợp lệ tại `qs`).

| Cách | Chunk trong ngữ cảnh (trung bình / p90 / max) | `ctx_hit` | `multi_all` | Câu được cứu |
|---|---|---|---|---|
| nền (top-5) | 5.0 / 5 / 5 | 0.692 | 0.167 | 0 |
| liền kề ±1 | 8.2 / 11 / 15 | 0.749 | 0.333 | 23 |
| liền kề ±2 | 10.4 / 15 / 22 | 0.774 | 0.333 | 33 |
| liền kề ±3 | 12.1 / 19 / 29 | 0.797 | 0.333 | 42 |
| liền kề ±5 | 14.6 / 25 / 41 | 0.820 | 0.417 | 51 |
| cùng trang, **không** lọc thời gian, 3 trang × 2 | 7.7 / 9 / 11 | 0.737 | 0.250 | 18 |
| cùng trang, không lọc thời gian, 3 trang × 5 | 11.0 / 15 / 20 | 0.774 | 0.333 | 33 |
| cùng trang, **có** lọc thời gian, 3 trang × 2 | 6.5 / 8 / 11 | 0.714 | 0.167 | 9 |
| cùng trang, có lọc thời gian, 3 trang × 5 | 7.5 / 10 / 17 | 0.719 | 0.167 | 11 |

Kết luận: **lọc theo thời gian không tốt hơn** chunk liền kề theo chỉ số và kém cả "cùng trang, không lọc". Ngân sách ngữ cảnh nhỏ (trung bình 5.9 đến 7.5 chunk) nhưng trần thấp (`ctx_hit` ≤ 0.737 ở range). Lý do (suy luận, nối với mục 6.12): chunk đáp án còn sót ngoài top-5 phần lớn có nhãn thời gian không khớp `qs`, nên bị chính bộ lọc loại; liền kề thắng nhờ tính liên tục của văn bản, không cần nhãn đúng. Bộ local (40 câu) cùng xu hướng nhưng chênh lệch tối đa 3 câu nên không dùng để kết luận. Lưới đầy đủ: `local/pageexp_{real,local}.tsv`.

### 6.12 Phân tích câu sai của cấu hình nền (bộ thật)

123/399 câu sai (`hit@5` = 0.692). Mỗi câu một nhóm nguyên nhân; chi tiết từng câu: `dataset/eval/failures_real.csv`; script `local/failure_analysis.py`.

| Nguyên nhân | Số câu | % |
|---|---|---|
| Chunk đúng bị lọc cứng: `start` sau `t_req` (nhãn ở tương lai) | 41 | 33% |
| Chunk đúng đã hết hạn (`end` < `t_req`), xếp sau top-5 (6–10: 13; 11–20: 14; 21–50: 6) | 33 | 27% |
| Điểm thời gian đẩy chunk đúng ra khỏi top-5 (trước đó đã trong top-5) | 21 | 17% |
| Chunk đúng không mốc (điểm `t_unknown` 0.1 thấp), xếp sau top-5 | 15 | 12% |
| Chunk đúng hợp lệ về thời gian nhưng xếp sau top-5 (lỗi ngữ nghĩa thuần) | 10 | 8% |
| Không vào ứng viên (dense top-50) | 3 | 2% |

- Trạng thái nhãn của chunk đúng tại `t_req`: **tương lai 41, hết hạn 51, không mốc 20, hợp lệ 11**. Tức **92/123 (75%) nhãn thời gian chunk đúng không khớp thời điểm hỏi**: lỗi nằm ở nhãn lúc ingestion, không phải ở xếp hạng. Lỗi do Profiler chỉ 3/123 (`t_req` ngoài khoảng nhãn).
- Trong 51 chunk hết hạn: `end_status` `known` 32, `unknown` 19 (với `unknown`, `end` chỉ là cuối năm của `start`; điểm thời gian còn 0.00–0.98, trung vị khoảng 0.17). Trong 41 chunk tương lai: `known` 30, `unknown` 11. Khoảng cách `t_req` − `end` có trung vị 11.2 năm (10/51 câu ≤ 1 năm); `start` − `t_req` trung vị 4.0 năm (13/41 câu ≤ 1 năm).
- Cả 123 câu đều có ít nhất một chunk top-5 cùng trang với chunk đúng: trang đúng, chọn nhầm đoạn.
- Góc nhìn người đọc: 52 câu top-5 vẫn chứa chuỗi đáp án (`ans_hit@5`), 37 câu còn hợp lệ thời gian. Ngữ cảnh cứu được: liền kề ±5 cứu 51, cùng trang 3×5 không lọc 33, có lọc 11; **71 câu không ngữ cảnh nào cứu được**.
- Đọc tay 12 mẫu: (1) sự kiện bị gán như trạng thái đã kết thúc ("Sam Selvon chuyển tới London năm 1950" gán `start=end=1950`; hỏi tháng 1/1975 thì đáp án vẫn London); (2) chunk nhắc mốc đời sau ("Nik Stauskas học trung học", chunk nhắc mùa 2012, hỏi 2008); (3) đoạn không có mốc thật; (4) nhãn dữ liệu lệch (vd "current director" gán 2014). Từ đó sinh đề xuất 9–12 ở `decisions/07`.
- Trần ước lượng nếu sửa hoàn hảo nhãn sự kiện/trạng thái và chunk không mốc: `hit@5` khoảng 0.85 (suy luận từ bảng, chưa đo).

### 6.13 Kho nạp lại bằng prompt ingestion v3 (decisions/07 đề xuất 9)

Nạp lại cả bộ thật (204 trang, 6880 chunk, `google_35`, 330 lô) bằng `ingestion_time_v3.md` vào collection riêng `tam_chunks_dev_real_v2` (6752 điểm; kho v1 6737). Extractions: `output/20261021_174115/extractions.jsonl`. Cùng Profiler v2 (point), dense, `t_unknown` 0.1; lưới 14 cấu hình `end_mode` × `decay_from` (`local/run_v3_eval.py`, không gọi LLM). Prompt v1, v2, v3 và ba lần thử nhỏ: `decisions/03`.

**Nhãn toàn bộ 6880 chunk (v1 → v3):** `known` 3974 → 4596, `unknown` 1238 → 924, `ongoing` 167 → 172, không mốc 1501 → 1188, `invalid_time` 41 → 29. Giống hệt v1 ở 3735 chunk (54%).

**Truy xuất, cấu hình nền (`unknown_decay` 0.05, `decay_from end`), v1 → v3, ghép cặp 399 câu:**

| Chỉ số | v1 | v3 | Chênh lệch ghép cặp |
|---|---|---|---|
| `hit@1` | 0.326 | 0.338 | |
| `hit@5` | 0.692 | 0.723 | +0.033 ± 0.036 (cứu 34, hỏng 21) |
| `mrr` | 0.463 | 0.478 | +0.016 ± 0.029 (tăng 69, giảm 71) |
| `ans_valid@5` | 0.632 | 0.693 | **+0.063 ± 0.042** |
| chunk đúng bị lọc cứng | 78 | 57 | |

Cấu hình `stored` (mặc định) cũng tăng: 0.450 → 0.474 `mrr`. Tốt nhất trong 14 cấu hình trên kho v3 vẫn là `unknown_decay` 0.05 với `decay_from end` (0.478). **Chỉ `ans_valid@5` vượt sai số**; `hit@5` và `mrr` chưa. Prompt v3 được sửa sau khi đã đọc 123 câu sai của bộ này, nên các con số là cận trên; cần tập valid/test.

**34 câu được thêm / 21 mất ở `hit@5` (trạng thái nhãn chunk đúng tại `t_req`, v1 → v3):**

| Nhóm | Số câu | Giải thích |
|---|---|---|
| Được thêm: không mốc → hợp lệ | 12 | Chunk v1 để trống nay có khoảng bao `t_req` (Leahy 1917–1921; New Orleans Baby Cakes 1993–2019) |
| Được thêm: hết hạn → hợp lệ | 7 | Sửa đúng lỗi nhắm tới: trạng thái không bị chốt ở năm bắt đầu (Sam Selvon `1950–1994`, Allsång `1935–2020`) |
| Được thêm: tương lai → hợp lệ | 5 | `start` lùi về sớm hơn (Wheel of Fortune 1975, Goryachkina 1998) |
| Được thêm: hết hạn → hết hạn | 7 | Đổi `known` thành `unknown` nên điểm giảm chậm từ `start` thay vì giảm nhanh từ `end` (Zhansaya) |
| Mất: hợp lệ → hợp lệ | 5 | Khoảng bị kéo quá dài (Erich Topp `end` 2005, mốc tử trận), nhiều chunk cùng được 1.0 nên mất khả năng phân biệt |
| Mất: hết hạn → hợp lệ | 3 | Cùng nguyên nhân (No. 73 Squadron `end` 1969 cho nhiều chunk) |
| Mất: hợp lệ → hết hạn / tương lai / không mốc | 6 | Nhãn chunk đúng xấu đi: Helen Clark (chunk mở đầu) `1950–2017` thành `1950` unknown, John Francis Charles (chunk sự nghiệp) `1877–1894` thành `1877` unknown. Chỉ một phần là chunk mở đầu: đo riêng 15 câu có chunk đúng là chunk mở đầu cho `hit@5` 7 → 9 và `mrr` 0.417 → 0.378, nên **chưa đủ bằng chứng** để coi chunk mở đầu là lỗi chung |
| Mất: hết hạn → hết hạn | 5 | `unknown` thành `known` nên điểm giảm nhanh từ `end` hơn (Pierre Gasly, Jimmy Lai) |

Nhận xét: v3 sửa được loại lỗi nhắm tới (trạng thái bị chốt sớm, chunk không mốc) nhưng cái giá là (a) khoảng quá dài làm điểm thời gian mất tính phân biệt (8 câu), (b) một số chunk bị đổi sang `unknown` (6 câu, không riêng chunk mở đầu).

**Câu sai còn lại ở kho v3: 111/400 (`hit@5` 0.722);** chi tiết `dataset/eval/failures_real_v3.csv`; 90 câu sai cả ở v1, 21 câu mới sai.

| Nguyên nhân | Số câu | % |
|---|---|---|
| Bị lọc cứng: `start` sau `t_req` | 37 | 33% |
| Xếp sau top-5; chunk đúng đã hết hạn | 30 | 27% |
| Xếp sau top-5; chunk đúng hợp lệ về thời gian (lỗi ngữ nghĩa) | 21 | 19% |
| Điểm thời gian đẩy chunk đúng ra khỏi top-5 | 16 | 14% |
| Chunk đúng không mốc xếp sau top-5 | 4 | 4% |
| Không vào ứng viên | 3 | 3% |

### 6.14 Tính chất của dữ liệu: chunk đúng thường liền kề vùng đã truy xuất, và mốc viết trong chunk không phải mốc của sự việc

Phân tích 111 câu sai của kho v3 (cấu hình nền; `dataset/eval/failures_real_v3.csv`, các số liệu dưới đây tính trên 111 câu đó, không phải trên cả 400 câu).

**(a) Hệ thống tìm đúng trang và gần đúng vùng, chunk đúng nằm sát.** Chỉ 1/111 câu sai có chunk đúng ở trang khác. Khoảng cách chỉ số giữa chunk đúng và chunk top-5 gần nhất cùng trang:

| Khoảng cách chỉ số | ≤ 1 | ≤ 2 | ≤ 3 | ≤ 5 | ≤ 10 |
|---|---|---|---|---|---|
| Số câu (trên 111) | 33 | 58 | 73 | 83 | 94 |

Tức 52% câu sai có chunk đúng cách chunk top-5 không quá 2 đoạn, 75% trong 5 đoạn. Khớp với mục 6.11: chunk liền kề ±5 cứu được 51/123 câu sai ở kho cũ (hơn nhiều so với "cùng trang có lọc thời gian"). Mình gọi đây là tính chất của dữ liệu và cách dựng bộ đánh giá (gán chunk đáp án theo vị trí chuỗi đáp án trong trang), không phải nhiễu ngẫu nhiên: nội dung liên quan nằm ở các đoạn kề nhau của cùng một trang, còn mốc thời gian được viết trong từng đoạn thì không luôn khớp với thời điểm của sự việc trả lời câu hỏi. Chưa kiểm chứng cách bộ dữ liệu gốc gán đáp án.

**(b) Khoảng cách nhãn 2, 3, 4 năm không phải lệch độ mịn.** Trong 37 câu bị lọc cứng, 10 câu có `start` của chunk đúng cách `t_req` 1 đến 5 năm. Nguyên nhân chung: chunk nói về một sự việc sớm hơn mọi ngày được viết trong chunk, nên `start` (ngày viết sớm nhất) muộn hơn sự việc thật. Độ lớn của khoảng cách tùy ý (1.6 đến 4.0 năm), nên không dung sai cố định nào đúng. Ví dụ:

| Câu hỏi | Chunk đúng (nhãn) | Vì sao lệch |
|---|---|---|
| Chồng trước 9/1973 của Nora Ephron | `1976 → 2012` | Chunk liệt kê ba cuộc hôn nhân; cuộc đầu ("Dan Greenburg") không ghi năm, nên mốc sớm nhất là 1976 |
| Nik Stauskas học trường nào, 1/2008 | `2012` | Chunk nhắc các trường trung học, chỉ ghi mùa 2012 |
| Tommy Flowers, 6/1948 | `1950 → 1964` | Chunk về Colossus thời chiến, ngày đầu tiên được viết là 1950 |
| Rio Grande K-28, 2/1942 | `1944` | Chunk nói việc mua trong chiến tranh (không ngày) rồi rút khỏi dịch vụ 1944 |

**(c) Vì sao chunk đúng bị tụt hạng ngoài top-5 (71 câu chunk đúng đã vào ứng viên nhưng xếp sau top-5).** Hai lực:
- *Ngữ nghĩa:* hạng ngữ nghĩa (trước điểm thời gian) của chunk đúng có trung vị 9; chỉ 16 câu nằm trong top-5, 25 câu hạng 6–10, 30 câu hạng > 10. Câu hỏi ("ai là chồng của X") giống nhiều đoạn của trang hơn là đoạn chứa tên người chồng.
- *Điểm thời gian không phân biệt được:* top-5 của các câu này chứa trung bình 3.0 chunk hợp lệ tại `t_req`; 31/71 câu có ít nhất 4 chunk hợp lệ, tức nhiều chunk cùng được 1.0 và thứ hạng do ngữ nghĩa quyết. 16 câu thì điểm thời gian đẩy chunk đúng (đã ở top-5 theo ngữ nghĩa) ra ngoài vì chunk đúng hết hạn hoặc `unknown` bị giảm điểm.

Hệ quả cho thiết kế: mở rộng ngữ cảnh bằng chunk liền kề theo chỉ số (không lọc thời gian) có lợi ở bước sinh câu trả lời; lọc theo thời gian lúc truy xuất đã làm hết phần việc của nó.

### 6.15 Chế độ khoảng (`range`) đo lại trên kho v3

Cùng kho v3 (`tam_chunks_dev_real_v2`) và Profiler khoảng v2. Lưới 28 cấu hình: 7 kiểu `end_mode` (`stored`, `open`, `decay`, `unknown_decay` 0.02/0.05/0.1/0.2) × `decay_from` (`start`, `end`) × `overlap` (`binary`, `coverage`) (`local/run_v3_range.py`, không gọi LLM). Chênh lệch ghép cặp so với cấu hình nền `point` (`unknown_decay` 0.05, `decay_from end`, `mrr` 0.478):

| Cấu hình `range` (đứng đầu) | `mrr` | Δ `mrr` | Δ `hit@5` | Δ `ans_valid@5` |
|---|---|---|---|---|
| `stored` · `end` · `coverage` | 0.481 | +0.003 ± 0.007 | −0.003 ± 0.013 | +0.000 ± 0.008 |
| `unknown_decay` 0.05 · `end` · `coverage` | 0.481 | +0.003 ± 0.007 | +0.003 ± 0.010 | −0.005 ± 0.008 |
| `unknown_decay` 0.05 · `end` · `binary` | 0.480 | +0.002 ± 0.007 | +0.005 ± 0.009 | +0.010 ± 0.007 |

Không cấu hình `range` nào hơn `point` vượt sai số (tốt nhất +0.003 ± 0.007); `decay_from end` vẫn tốt hơn `start` (khoảng +0.01) và `open`/`decay` vẫn kém rõ (−0.02 đến −0.05). **Kết luận cũ ở mục 6.9 vẫn đúng ở nhãn v3:** `range` không đáng giá, giữ làm tùy chọn mặc định tắt.

### 6.16 Mốc thời gian suy từ chunk liền kề (decisions/07 đề xuất 11)

Hậu xử lý không gọi LLM (`src/tam/ingestion/infer_time.py`, `scripts/infer_neighbor_time.py`): sao chép vector từ kho v3 sang 9 collection mới (`tam_chunks_dev_real_inf_*`), chỉ đổi nhãn thời gian và thêm `time_inferred`. `ongoing` không suy. Quy tắc:

| Tên | Quy tắc | Số chunk được suy |
|---|---|---|
| `s_pe` | chunk không mốc lấy `end` (nếu `known`, không thì `start`) của chunk dated gần nhất đứng trước | 938 `start` |
| `s_ps` | như trên nhưng lấy `start` của chunk trước | 938 |
| `s_pc` | lấy `end` của chunk trước nếu khoảng của nó ≤ 10 năm, không thì `start` | 938 |
| `e_ns` | chunk `unknown` lấy `end` = `start` của chunk dated kế tiếp và muộn hơn | 816 `end` |
| `e_ns10`, `e_ns5` | như `e_ns` nhưng bỏ nếu cách xa hơn 10/5 năm | 482 / 392 |
| `se_pe_ns`, `se_pc_ns10`, `se_ps_ns10` | kết hợp | 938 + 816 / 938 + 482 / 938 + 482 |

Lưới: 9 collection × hệ số giảm điểm thời gian của chunk có mốc suy luận (`inferred_factor` 1.0/0.8/0.5) × 3 `end_mode` (`unknown_decay` 0.05, `stored`, `decay` 0.1) = 84 lượt (`local/run_inferred.py`). Nền: kho v3 cùng `end_mode`. Ghép cặp, `unknown_decay` 0.05:

| Collection | Δ `mrr` | Δ `hit@5` | Δ `ans_valid@5` |
|---|---|---|---|
| `s_pe` (suy `start`) | −0.005 ± 0.004 | +0.000 ± 0.009 | +0.007 ± 0.004 |
| `e_ns` (suy `end`) | −0.008 ± 0.006 | −0.005 ± 0.008 | **+0.037 ± 0.010** |
| `e_ns5` | +0.002 ± 0.002 | +0.000 ± 0.004 | +0.007 ± 0.004 |
| `se_pe_ns` (cả hai) | −0.014 ± 0.007 | −0.013 ± 0.011 | **+0.043 ± 0.011** |

Nhận xét:
- Suy `start` không cải thiện `hit@5` hay `mrr` (chỉ 4 câu sai do chunk không mốc); suy `end` không giới hạn khoảng cách làm `ans_valid@5` tăng đáng kể (+0.037 đến +0.043) nhưng `mrr` và `hit@5` không tăng, hơi giảm.
- `ans_valid@5` tăng có thể chỉ vì khoảng hiệu lực bị kéo dài nên nhiều chunk "hợp lệ" hơn theo nhãn, không vì chunk đúng lên hạng (giải thích, chưa kiểm chứng riêng).
- Hệ số 0.8 hoặc 0.5 chỉ bù phần mất `mrr` về gần nền, không vượt nền. Giới hạn khoảng cách (`e_ns5`) cho kết quả trung tính.
- **Kết luận: không bật.** Giữ ở dạng tùy chọn tắt (`inferred_factor` 1.0 mặc định, collection riêng).

### 6.17 Plain RAG và chunk liền kề cùng kích thước ngữ cảnh

`PlainRetriever` nhận `neighbor_window` (lấy cả chunk tương lai vì không lọc thời gian) và `evaluate.py --top-k`. Lưới (`local/run_plain_neighbors.py`): Plain dense/hybrid và Cơ chế 1 (cấu hình nền), `w` 0 đến 3, `top-k` 5 đến 20, trên kho v1 và v3. `ctx_hit` = chunk đúng có trong ngữ cảnh (top-k cộng chunk liền kề). Kho v3, không cross-encoder:

| Số chunk (xấp xỉ) | Cơ chế 1 `ctx_hit` | Plain dense `ctx_hit` | `leakage_rate` Plain |
|---|---|---|---|
| 5 (top-5) | 0.723 | 0.547 | 0.700 |
| 8 | 0.800 (top-8) | 0.695 (top-8) | 0.825 |
| 10 | 0.828 (top-10) | 0.765 (top-10) | 0.845 |
| 15 | 0.860 (top-15) | 0.863 (top-15) | 0.920 |
| 20 | 0.882 (top-20) | 0.900 (top-20) | 0.940 |
| chunk liền kề ±1 | 0.765 (8.4 chunk) | 0.720 (10.9 chunk) | 0.700 |
| ±3 | 0.838 (12.5) | 0.855 (17.9) | 0.700 |

Cơ chế 1 hơn rõ khi ngữ cảnh nhỏ (5 đến 12 chunk); từ khoảng 15 chunk hai bên bằng nhau và Plain RAG nhỉnh hơn ở 20 chunk. Plain RAG rò rỉ tương lai ở 70% đến 94% câu (Cơ chế 1 là 0). **`ctx_hit` không phải thước đo công bằng cho cơ chế thời gian ở ngữ cảnh lớn** (cả hai cùng chứa chunk đúng, nhưng Plain còn chứa nhiều chunk sai thời điểm); phép đo cuối nên là EM/F1 đầu-cuối ở cùng ngân sách token. Mở rộng ngữ cảnh là kỹ thuật chung, áp dụng cho cả Plain RAG, không tính vào đóng góp của cơ chế thời gian.

### 6.18 Cross-encoder rerank (decisions/07 đề xuất 4)

Tính năng tùy chọn, mặc định tắt: `src/tam/retrieval/temporal/rerank.py` (`CrossEncoderReranker` bọc `fastembed.TextCrossEncoder`, cache điểm sqlite chỉ để chạy thí nghiệm nhanh), tham số `rerank*` trong `TemporalRetriever`, `PlainRetriever` và `retrieval` của config; cờ `evaluate.py --rerank <model> --rerank-top --rerank-mode --rerank-alpha --rerank-pool --rerank-time`.

**Luồng:** dense top-50 (đã lọc cứng thời gian) → `Final = W1·Semantic + W2·Temporal` → lấy `rerank_top` chunk đầu (nhóm `final`, hoặc `semantic`) → cross-encoder chấm lại cặp (câu hỏi, chữ của chunk) → `replace` (Semantic mới = min-max điểm cross-encoder) hoặc `mix` (α·Semantic cũ + (1−α)·min-max) → tính lại `Final` với `Temporal` cũ → top-5. Ứng viên ngoài nhóm giữ nguyên, xếp sau. `leakage_rate` vẫn 0.

**Lưới** (`local/run_rerank.py`, `run_rerank_bge.py`): 5 model × cấu hình (đầy đủ cho 3 model nhỏ: `replace`/`mix` 0.3/0.5/0.7 × nhóm × top 10/20/30 × có/không ghép khoảng thời gian vào văn bản; 5 cấu hình đại diện cho 2 model lớn) trên kho v3, cấu hình thời gian nền. Chọn model và cấu hình theo cùng bộ 400 câu nên **là cận trên**. Ghép cặp, so nền (`hit@1` 0.338, `hit@5` 0.723, `mrr` 0.478, `ans_valid@5` 0.693):

| Model | Cấu hình tốt nhất | `hit@1` | `hit@5` | `mrr` (Δ) | `ans_valid@5` | Độ trễ (20 chunk) |
|---|---|---|---|---|---|---|
| bge-reranker-v2-m3 (int8) | `replace`, top-20, ghép thời gian | 0.415 | 0.795 | **0.566 (+0.088 ± 0.015)** | 0.710 | ~980 ms |
| MiniLM-L12 | `mix` 0.3, top-20 | 0.375 | 0.785 | 0.530 (+0.052 ± 0.012) | 0.713 | ~160 ms |
| MiniLM-L6 | `replace`, top-20, ghép thời gian | 0.360 | 0.795 | 0.524 (+0.046 ± 0.015) | 0.710 | ~70 ms |
| bge-reranker-base | `replace`, top-20, ghép thời gian | 0.338 | 0.782 | 0.508 (+0.030 ± 0.016) | 0.700 | ~770 ms |
| jina-reranker-v1-turbo-en | `mix` 0.7, top-20, ghép thời gian | 0.343 | 0.765 | 0.502 (+0.024 ± 0.009) | 0.710 | ~120 ms |

Độ trễ đo trên CPU laptop khi máy rảnh (20 chunk dài khoảng 300 ký tự, 1 câu hỏi); chưa đo trên GPU hoặc dưới tải.

- Cả bốn model tốt nhất tăng `mrr` và `hit@5` vượt sai số; bge-v2-m3 tăng chủ yếu ở thứ hạng đầu (`hit@1` 0.338 → 0.415) chứ `hit@5` ngang MiniLM (~0.79). Kích cỡ model không quyết định riêng: bge-reranker-base yếu hơn MiniLM.
- Nhóm `final` top-20 ổn định nhất; nhóm `semantic` top-10 kém rõ (`ans_valid@5` giảm 0.03 đến 0.05, kéo lên chunk đúng nội dung nhưng hết hạn). Ghép khoảng thời gian vào văn bản gần như không đổi `mrr`. `replace` và `mix` 0.3 ngang nhau trong sai số.
- **`ans_valid@5` gần như không đổi giữa các model (0.70 đến 0.72):** cross-encoder đọc nội dung, không biết thời gian; điểm yếu còn lại là nhãn thời gian lệch.
- Chưa đo: đổi `w1`/`w2`, bỏ `Temporal`, các `end_mode` khác, nhãn v1, BM25 (`sparse_weight` > 0) khi có cross-encoder; ghi ở `decisions/07` mục "Dự định tiếp theo".

**Đối chứng công bằng: Plain RAG + cùng cross-encoder** (`local/run_plain_rerank.py`, `run_plain_bge.py`; `replace`, top-20; Plain xếp theo vector, không lọc, không `Temporal`). Cơ chế 1 + cross-encoder so với Plain + cross-encoder (ngữ cảnh 5 chunk):

| Cặp (cross-encoder) | Plain `hit@5` / `mrr` / `ans_valid@5` / rò rỉ | Cơ chế 1 `hit@5` / `mrr` / `ans_valid@5` / rò rỉ |
|---|---|---|
| Không | 0.547 / 0.330 / 0.443 / 0.700 | 0.723 / 0.478 / 0.693 / 0 |
| MiniLM-L12 | 0.688 / 0.425 / 0.545 / 0.665 | 0.800 / 0.528 / 0.705 / 0 |
| bge-v2-m3 | 0.735 / 0.471 / 0.573 / 0.695 | 0.787 / 0.560 / 0.710 / 0 |

Cross-encoder nâng cả Plain RAG (một phần mức tăng không thuộc về cơ chế thời gian). Phần riêng của Cơ chế 1 khi cả hai có cross-encoder: L12 +0.10 `mrr`, +0.11 `hit@5`, +0.16 `ans_valid@5`; bge-v2-m3 +0.09 `mrr`, +0.05 `hit@5`, +0.14 `ans_valid@5`. **`hit@5` của Plain + bge-v2-m3 (0.735) ngang Cơ chế 1 không cross-encoder (0.723)**, nên với model mạnh, khoảng cách `hit@5` thu hẹp; ưu thế của Cơ chế 1 còn lại chủ yếu ở thứ hạng đầu, `ans_valid@5` và không rò rỉ.

**Cùng kích thước ngữ cảnh (`ctx_hit`):**

| Chunk | L12: Cơ chế 1 / Plain | bge-v2-m3: Cơ chế 1 / Plain |
|---|---|---|
| 5 | 0.800 / 0.688 | 0.787 / 0.735 |
| 8 (top-8) | 0.840 / 0.797 | 0.840 / 0.815 |
| 10 (top-10) | 0.863 / 0.848 | 0.868 / 0.860 |
| 12 | 0.873 / 0.873 | 0.868 / 0.890 |
| 15 | 0.880 / 0.890 | 0.875 / 0.897 |

Khoảng cách thu hẹp khi ngữ cảnh lớn và đảo chiều từ khoảng 12 chunk. **Chunk liền kề ±1 cộng thêm** `ctx_hit` +0.038 (L12: 0.800 → 0.8375, 7.9 chunk), ±2 +0.058, ±3 +0.068 (11.2 chunk).

**Giới hạn:** (a) số trên bộ thật là cận trên; (b) các lượt đối chứng Plain dùng đúng cấu hình cross-encoder của Cơ chế 1 (có thể không tối ưu cho Plain); (c) `ctx_hit` bỏ qua việc Plain chứa nhiều chunk sai thời điểm, cần EM/F1 đầu-cuối.

### 6.19 Khảo sát cross-encoder: BM25, nhóm chấm lại lớn hơn, nhãn v1, thang chuẩn hóa (chẩn đoán)

**Chỉ để chẩn đoán trên bộ thật 400 câu (đã dùng để chọn cấu hình), không dùng chọn cấu hình cuối.** 3 model (MiniLM-L6, MiniLM-L12, bge-v2-m3 int8) với cấu hình nền của khảo sát: `replace`, nhóm `final`, top-20, ghép khoảng thời gian vào văn bản (`local/run_remaining.py`, 30 lượt). Chênh lệch ghép cặp theo câu so với nền của chính model đó (`mrr` nền: L6 0.524, L12 0.529, bge-v2-m3 0.566):

| Thay đổi | L6 Δ `mrr` | L12 Δ `mrr` | bge-v2-m3 Δ `mrr` | Kết luận |
|---|---|---|---|---|
| BM25 `sparse_weight` 0.25 / 0.5 / 1.0 | −0.003 / −0.010 / −0.006 | −0.001 / −0.005 / −0.005 | −0.005 / −0.009 / −0.003 | Không giúp, hơi hại; giữ dense |
| Nhóm chấm lại top-30 / top-50 | −0.003 / −0.001 | 0.000 / 0.000 | −0.002 / −0.001 | Không giúp; top-20 đủ |
| Nhãn ingestion v1 (thay v3) | **−0.038 ± 0.013** | **−0.031 ± 0.012** | **−0.031 ± 0.013** | Lợi ích của prompt v3 vẫn còn khi có cross-encoder (`ans_valid@5` −0.07) |
| Chuẩn hóa `sigmoid` | −0.008 | −0.016 | −0.001 | Không hơn min-max |
| Chuẩn hóa `zscore` | −0.005 | −0.011 | −0.009 | Không hơn min-max |
| Chuẩn hóa `softmax` | −0.032 | −0.032 | −0.052 | Kém rõ (quá nhọn, `hit@5` −0.06 đến −0.07) |

Các chênh lệch của BM25, top-30/50, `sigmoid`, `zscore` đều nằm trong khoảng sai số (±0.003 đến 0.008). Hai chênh lệch vượt sai số: nhãn v1 kém và `softmax` kém. Kết luận cho cấu hình cross-encoder: **dense (không BM25), nhóm `final` top-20, chuẩn hóa min-max** vẫn là lựa chọn đơn giản nhất. `leakage_rate` vẫn 0.

**Quét `w2` và `end_mode` với bge-v2-m3 (dở dang, chẩn đoán).** Lưới 28 lượt bị dừng ở 12 lượt (`local/w2end_real.tsv`): `w2` ∈ {0, 0.15, 0.3} × `end_mode` ∈ {`unknown_decay` 0.05, `stored`, `unknown_decay` 0.1, `decay` 0.1}, `decay_from end`, cấu hình rerank tốt nhất (`replace`, `final`, top-20, ghép thời gian). `w2` quyết định cả bước chọn nhóm lẫn bước cuối (`w1` = 1 − `w2`):

| `w2` | `mrr` (bốn `end_mode`) | `ans_valid@5` |
|---|---|---|
| 0 (không thời gian) | 0.499 (cả bốn bằng nhau vì không dùng `Temporal`) | 0.642 |
| 0.15 | 0.544 đến 0.550 | 0.690 đến 0.695 |
| 0.3 (hiện tại) | 0.556 đến 0.566 | 0.705 đến 0.715 |

`mrr` tăng đều theo `w2` đến 0.3 và `end_mode` không phân biệt được trong sai số (`unknown_decay` 0.05 cao nhất 0.566, `stored`/`decay` 0.556). Chưa đo `w2` > 0.3 (0.5 chưa chạy) nên chưa biết đỉnh; giá trị cuối cần chọn trên valid, không chọn trên bộ này.

**Bỏ `Temporal` ở bước xếp cuối (`--rerank-no-temporal`, chẩn đoán).** Sau khi cross-encoder chấm, nhóm top-20 xếp chỉ theo điểm cross-encoder (không cộng `Temporal` lần hai). 12 lượt (`local/run_notemporal.py`): 3 model × nhóm (`final`, `semantic`) × ghép thời gian vào văn bản (có, không), `replace`, top-20; so với cấu hình có `Temporal` lần hai (nền của khảo sát trên):

| Model | Nền (có `Temporal`) `mrr` / `ans_valid@5` | Bỏ `Temporal`, nhóm `final` | Bỏ `Temporal`, nhóm `semantic` |
|---|---|---|---|
| MiniLM-L6 | 0.524 / 0.710 | 0.459 / 0.618 (Δ`mrr` −0.066 ± 0.016) | 0.455 / 0.610 (−0.069 ± 0.016) |
| MiniLM-L12 | 0.529 / 0.708 | 0.467 / 0.625 (−0.062 ± 0.015) | 0.462 / 0.623 (−0.067 ± 0.015) |
| bge-v2-m3 | 0.566 / 0.710 | 0.503 / 0.652 (−0.062 ± 0.014) | 0.503 / 0.655 (−0.063 ± 0.014) |

- Bỏ `Temporal` ở bước cuối làm `mrr` giảm 0.06 đến 0.07 và `ans_valid@5` giảm 0.06 đến 0.09 ở cả ba model, vượt sai số xa (4 đến 5 lần). Cross-encoder đọc nội dung nên không thay được điểm thời gian.
- Chọn nhóm `final` hay `semantic` gần như không khác nhau khi bỏ `Temporal` bước cuối (chênh 0.00 đến 0.005): thời gian ở bước chọn nhóm không đủ cứu khi bước cuối không còn thời gian. Ghép khoảng thời gian vào văn bản cũng không bù được (`hit@5` còn giảm thêm ở bge-v2-m3).
- Kết luận: giữ `Temporal` ở bước xếp cuối (cấu hình hiện tại). Trùng hướng với lưới `w2` dở dang (bge-v2-m3, `w2` = 0 → `mrr` 0.499).

## 7. "Bị lọc nhầm" nghĩa là gì, và bộ có còn đủ 400 câu không

- **Bộ vẫn đủ 400 câu**, trong đó 399 câu có chunk đáp án trong kho (1 câu có chunk đáp án bị bỏ lúc nạp kho). Không câu nào bị loại khỏi mẫu đánh giá vì lọc nhầm; 37 câu chỉ là các câu hệ **không thể trả đúng** khi còn dùng bộ lọc cứng.
- Bộ lọc cứng của Cơ chế 1 giữ chunk có `start_time <= T_req` (không rò rỉ tương lai). "Lọc nhầm" là trường hợp chunk đúng (theo nhãn đáp án) có `start` (do LLM gán lúc nạp kho) **lớn hơn** `t_req` (do Profiler trích từ câu hỏi), nên bị loại trước khi chấm điểm. Hệ không có cơ hội xếp nó dù điểm ngữ nghĩa cao đến đâu.
- Quy mô: **37/399 = 9.3%** câu. Khoảng cách `start` − `t_req` có trung vị 3.1 năm: 13 câu dưới 1 năm, 9 câu từ 1 đến 5 năm, 15 câu trên 5 năm. Ở local con số này chỉ cỡ 2 câu.
- Cùng bộ lọc, **37 câu nữa** có chunk đúng không có `start` (LLM không tìm được mốc trong chunk). Nếu tắt nhánh `t_unknown` thì các chunk đó bị loại (`gold_blocked_by_filter` = 74 = 37 + 37); bật `t_unknown` thì chúng được giữ lại và chỉ còn lỗi xếp hạng.
- **Phân loại 37 câu** theo khoảng nhãn thời gian của câu hỏi (`time_start`–`time_end` trong dữ liệu) so với `start` của chunk đúng:

| Nhóm | Số câu | Ý nghĩa | Ví dụ |
|---|---|---|---|
| A. `start` cùng năm với nhãn, chỉ muộn hơn `t_req` vài tháng | 7 | `t_req` Profiler lấy đầu tháng/năm, chunk bắt đầu giữa năm: lệch độ mịn | Janet Frame 1990: `t_req` 1/1/1990, chunk "6 February 1990" |
| B. `start` trong khoảng nhãn nhưng sau `t_req` | 9 | Câu hỏi hỏi sớm hơn đoạn mô tả | 2AM: hỏi 6/2013, chunk nói về 4/2014 |
| C. `start` **sau cả khoảng nhãn** | 21 | Đoạn có chứa chuỗi đáp án nói về thời kỳ sau thời điểm câu hỏi | Goryachkina: hỏi danh hiệu năm 2012, chunk "Historical achievements" nói về 2018 |

- **Đọc tay 21 đoạn ở nhóm C** (đọc quanh chuỗi đáp án, phân loại thô; vài ca có thể thuộc hai nhóm). Trong cả 21 ca, `start` LLM gán khớp với nội dung có ghi ngày rõ của đoạn; điều không khớp là **đoạn mà ta coi là "chunk đúng"** (đoạn chứa chuỗi đáp án) không nói về thời điểm của câu hỏi:

  | Nhóm | Số ca | Mô tả | Ví dụ |
  |---|---|---|---|
  | C1. Đoạn liệt kê hoặc tổng hợp nhiều thời kỳ; ingestion chỉ gán **một** khoảng cho cả đoạn | 6 | Đây là **giới hạn thiết kế "một chunk một khoảng"**, không phải LLM đọc sai | 4 câu của Office for Foreign Relations (danh sách giám đốc cũ, mốc 2014); Goryachkina: "at the age of 13 ... Woman Grandmaster" (13 tuổi = 2012, không có chữ "2012") cùng "Grandmaster in early 2018" trong một đoạn, chỉ gán 2018; Stauskas (tổng kết "high school years") |
  | C2. Đoạn nói về sự việc ở thời điểm khác, nhắc đáp án như chi tiết phụ | 9 | Sự việc của câu hỏi vẫn đúng nhưng được kể trong đoạn khác thời kỳ | 2AM: hợp đồng với Big Hit "hết hạn tháng 4" (2014); Nora Ephron: hôn nhân 1976–80 nhắc trong đoạn về tiểu thuyết 1983; Mancini: "returned 2014" trong khi hỏi 2007 |
  | C3. Đáp án là từ chung, trùng ngẫu nhiên | 3 | Chuỗi đáp án xuất hiện nhưng không phải là sự việc được hỏi | Keith Emerson: "Emerson, Lake and Palmer" trong đoạn lễ tang 2016; Schörner: "colonel" trong "OKW colonel Meyer-Detring"; Goryachkina: "FIDE" trong "FIDE rating" |
  | C4. Nhãn thời gian của dữ liệu lệch, hoặc đáp án là tên hiện tại | 3 | Không do ingestion hay Profiler | Stommel: nhãn 1961, đoạn ghi 1962; Chicago Red Stars: "SeatGeek Stadium" là tên mới của sân nhưng câu hỏi hỏi 2009; Inter Milan: Simoni bị sa thải 1998 trong khi nhãn là 1983 |

  **Đọc tay 16 đoạn nhóm A và B** (cùng cách đọc, phân loại thô):

  | Nhóm | Số ca | Nguyên nhân | Ví dụ | Đề xuất 1 (khoảng) có cứu không |
  |---|---|---|---|---|
  | A1. Câu hỏi nêu năm/tháng, chunk bắt đầu giữa kỳ đó; `t_req` chỉ là ngày đầu kỳ | 4 | Lệch độ mịn của `t_req` (Profiler) | Janet Frame "in 1990" (chunk 6/2/1990); Luftflotte 5 "in Apr 1940" (12/4/1940); Nana Okada "in 2017" (22/2/2017); USAFE "in Jun 1942" (15/6/1942) | **Có** (`qe` là cuối kỳ) |
  | A2. Câu hỏi "after X" | 2 | Profiler lấy điểm X, bỏ phần mở sau X | Esteban Ocon "after Feb 2016"; Pelican "after Nov 1938" | **Có** (khoảng mở `[X, T_now]`) |
  | A3. Câu hỏi nêu tháng nhưng dữ liệu chỉ có nhãn cấp năm | 1 | Nhiễu dữ liệu: Garnidelia hỏi "Mar 2017", nhãn 2017–2018, sự việc xảy ra 4/2017 | | Không |
  | B. Đoạn nói về thời điểm khác hoặc nhiều thời kỳ, nhắc đáp án như chi tiết phụ | 9 | Giống nhóm C2/C1: 2AM, Central European University, Charles Holden, Jiminy Cricket, GNV Azzurra, Nora Ephron, Nakhimov, Senate of Canada Building, The Dark Eye | | Không |

  Tức là trong 37 câu bị lọc, **khoảng 6 câu (16%) cứu được bằng khoảng thời gian của câu hỏi**; 31 câu còn lại do đoạn nhiều thời kỳ (giới hạn "một chunk một khoảng") hoặc nhiễu dữ liệu. Phân loại là đọc tay, chưa có kiểm tra độc lập.
- Hệ quả cho đánh giá: 9.3% là trần do cách chấm theo chunk id. Một phần là hạn chế thiết kế thật (C1, một chunk một khoảng: `decisions/06` đề xuất 3, và đề xuất 7 của `decisions/07`), phần còn lại là nhiễu của bộ dữ liệu; chấm theo chuỗi đáp án (mục 5.1) thoát khỏi lệch này một phần.

## 8. Kiểm tra thống kê (ghép cặp, 400 câu, khoảng 95%)

| So sánh | Hơn / kém | Δ`mrr` |
|---|---|---|
| Cơ chế 1 (dense, stored, tắt) so với Plain RAG dense | 143 / 79 | **+0.078 ± 0.042** |
| Cơ chế 1 (dense, unknown decay 0.1, `t_unknown` 0.1) so với Plain RAG dense | 143 / 56 | **+0.104 ± 0.036** |
| Dense so với hybrid (stored, tắt) | 74 / 50 | **+0.032 ± 0.025** |
| `t_unknown` 0.1 so với tắt (dense, stored) | 39 / 19 | **+0.023 ± 0.016** |
| `unknown_decay` 0.1 so với `stored` (dense, `t_unknown` 0.1) | 19 / 17 | +0.003 ± 0.010 (không phân biệt được) |

## 9. Việc còn lại

0. (cập nhật 2026-10-21) Cross-encoder (mục 6.18) là cải thiện lớn nhất hiện có; việc tiếp theo là quét `w1`/`w2` và `end_mode` với cross-encoder, BM25, chọn cấu hình trên tập valid sạch, đo độ trễ dưới tải và EM/F1 đầu-cuối. Xem `decisions/07` mục "Dự định tiếp theo".
1. Phân loại 37 câu `start` sau `t_req` (nhãn tháng, chunk nhiều sự việc, mốc đăng) để biết cần sửa ingestion hay chấp nhận; đây là trần 9.3% của mọi cấu hình.
2. Hạng đầu `mrr` ở bộ thật chỉ hơn cấu hình mặc định hiện tại khoảng 0.01–0.02, nên **chọn mặc định theo độ đơn giản**: dense + `t_unknown` 0.1 + `end_mode: stored`. Chưa đổi `config.*.yaml`; chờ bạn chốt (cùng quyết định đổi tên `t_unknown`).
3. Quét `decay_lambda`, `W1`/`W2` bằng D/train (đợt 6), loại 35 câu mượn khỏi mẫu tinh chỉnh. Hiện λ = 0.5, `W1`/`W2` = 0.7/0.3 là giá trị cố định chưa được tinh chỉnh.
4. Cải thiện chọn thời kỳ trong cùng một trang (nguyên nhân lớn nhất, mục 5): hướng của `decisions/06` đề xuất 2–3 (LLM ghi loại sự việc, một chunk nhiều khoảng) và Cơ chế 2. Các đề xuất nâng hạng sau bộ thật (khoảng thời gian của câu hỏi + chồng lấn, phạt `end` theo khoảng cách từ `end`, reranker, chỉ số chuỗi đáp án) ghi ở [`decisions/07`](../decisions/07_RANKING_AND_TIME_RANGE_PROPOSALS.md).

## Phụ lục A. Bảng xếp hạng đầy đủ 132 nhóm cấu hình (theo `mrr`)

Các dòng chỉ khác `t_unknown` mà kết quả y hệt được gộp. Hạng bằng nhau khi `mrr` bằng nhau (3 chữ số). Hai cột `ans@5` và `ans_valid@5` là chỉ số theo chuỗi đáp án (`decisions/07` đề xuất 5); thư mục là lần chạy lại ngày 2026-10-20 (có thêm các cột này, `hit@k` và `mrr` giống hệt lần chạy đầu).

![Xếp hạng toàn bộ](figures_real/ranking.svg)

| Hạng | Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `ans@5` | `ans_valid@5` | `ctx_hit` | `leakage_rate` | Thư mục |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.0 | 0.308 | 0.569 | 0.682 | **0.452** | 0.820 | 0.637 | 0.682 | 0.000 | 20261020_173227 |
| 2 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.1 | 0.311 | 0.571 | 0.679 | **0.451** | 0.815 | 0.632 | 0.679 | 0.000 | 20261020_173227_3 |
| 2 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.2 | 0.311 | 0.566 | 0.679 | **0.451** | 0.812 | 0.629 | 0.679 | 0.000 | 20261020_173227_2 |
| 4 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.3 | 0.311 | 0.566 | 0.667 | **0.448** | 0.799 | 0.622 | 0.667 | 0.000 | 20261020_173227_4 |
| 5 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.4 | 0.311 | 0.564 | 0.664 | **0.447** | 0.797 | 0.622 | 0.664 | 0.000 | 20261020_173302 |
| 6 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.1 | 0.301 | 0.571 | 0.692 | **0.446** | 0.820 | 0.637 | 0.692 | 0.000 | 20261020_173303 |
| 6 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.0 | 0.298 | 0.564 | 0.692 | **0.446** | 0.827 | 0.639 | 0.692 | 0.000 | 20261020_173303_2 |
| 6 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.0 | 0.298 | 0.571 | 0.689 | **0.446** | 0.827 | 0.639 | 0.689 | 0.000 | 20261020_173303_3 |
| 9 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.1 | 0.301 | 0.566 | 0.689 | **0.444** | 0.817 | 0.637 | 0.689 | 0.000 | 20261020_173336 |
| 9 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.1 | 0.296 | 0.569 | 0.687 | **0.444** | 0.817 | 0.634 | 0.687 | 0.000 | 20261020_173337 |
| 11 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.2 | 0.296 | 0.564 | 0.687 | **0.443** | 0.817 | 0.632 | 0.687 | 0.000 | 20261020_173337_2 |
| 11 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.0 | 0.293 | 0.566 | 0.684 | **0.443** | 0.822 | 0.637 | 0.684 | 0.000 | 20261020_173337_3 |
| 11 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.2 | 0.301 | 0.559 | 0.682 | **0.443** | 0.810 | 0.634 | 0.682 | 0.000 | 20261020_173410 |
| 14 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.0 | 0.296 | 0.561 | 0.684 | **0.442** | 0.820 | 0.639 | 0.684 | 0.000 | 20261020_173411 |
| 14 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.3 | 0.298 | 0.559 | 0.679 | **0.442** | 0.807 | 0.624 | 0.679 | 0.000 | 20261020_173411_2 |
| 16 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.1 | 0.298 | 0.564 | 0.679 | **0.441** | 0.810 | 0.637 | 0.679 | 0.000 | 20261020_173411_3 |
| 16 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.2 | 0.301 | 0.554 | 0.677 | **0.441** | 0.805 | 0.634 | 0.677 | 0.000 | 20261020_173445 |
| 16 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.3 | 0.303 | 0.554 | 0.674 | **0.441** | 0.802 | 0.627 | 0.674 | 0.000 | 20261020_173445_2 |
| 19 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.2 | 0.298 | 0.554 | 0.677 | **0.440** | 0.805 | 0.634 | 0.677 | 0.000 | 20261020_173445_4 |
| 19 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.3 | 0.303 | 0.551 | 0.669 | **0.440** | 0.797 | 0.627 | 0.669 | 0.000 | 20261020_173445_3 |
| 19 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.5 | 0.301 | 0.561 | 0.659 | **0.440** | 0.789 | 0.617 | 0.659 | 0.000 | 20261020_173519 |
| 22 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.0 | 0.293 | 0.556 | 0.687 | **0.439** | 0.822 | 0.629 | 0.687 | 0.000 | 20261020_173519_3 |
| 23 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.2 | 0.296 | 0.554 | 0.687 | **0.438** | 0.812 | 0.624 | 0.687 | 0.000 | 20261020_173519_2 |
| 23 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.1 | 0.293 | 0.556 | 0.684 | **0.438** | 0.812 | 0.627 | 0.684 | 0.000 | 20261020_173520 |
| 23 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.3 | 0.301 | 0.549 | 0.669 | **0.438** | 0.794 | 0.627 | 0.669 | 0.000 | 20261020_173553 |
| 26 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.4 | 0.298 | 0.551 | 0.667 | **0.437** | 0.799 | 0.622 | 0.667 | 0.000 | 20261020_173554 |
| 26 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.4 | 0.303 | 0.549 | 0.657 | **0.437** | 0.792 | 0.627 | 0.657 | 0.000 | 20261020_173554_3 |
| 26 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.4 | 0.303 | 0.546 | 0.654 | **0.437** | 0.789 | 0.627 | 0.654 | 0.000 | 20261020_173554_2 |
| 29 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.0 | 0.283 | 0.571 | 0.687 | **0.436** | 0.807 | 0.642 | 0.687 | 0.000 | 20261020_173625 |
| 30 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.1 | 0.283 | 0.561 | 0.682 | **0.434** | 0.799 | 0.642 | 0.682 | 0.000 | 20261020_173628 |
| 31 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.3 | 0.291 | 0.544 | 0.679 | **0.433** | 0.810 | 0.619 | 0.679 | 0.000 | 20261020_173629_2 |
| 32 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.2 | 0.278 | 0.556 | 0.684 | **0.432** | 0.794 | 0.642 | 0.684 | 0.000 | 20261020_173629 |
| 32 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.2 | 0.293 | 0.556 | 0.654 | **0.432** | 0.774 | 0.596 | 0.654 | 0.000 | 20261020_173659 |
| 32 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.4 | 0.301 | 0.541 | 0.644 | **0.432** | 0.782 | 0.627 | 0.644 | 0.000 | 20261020_173702 |
| 35 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.3 | 0.293 | 0.559 | 0.649 | **0.430** | 0.769 | 0.591 | 0.649 | 0.000 | 20261020_173703 |
| 35 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.1 | 0.293 | 0.561 | 0.647 | **0.430** | 0.772 | 0.596 | 0.647 | 0.000 | 20261020_173703_2 |
| 35 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.0 | 0.291 | 0.566 | 0.644 | **0.430** | 0.769 | 0.599 | 0.644 | 0.000 | 20261020_173732 |
| 38 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.5 | 0.291 | 0.546 | 0.652 | **0.429** | 0.784 | 0.617 | 0.652 | 0.000 | 20261020_173735 |
| 38 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.4 | 0.293 | 0.559 | 0.644 | **0.429** | 0.767 | 0.591 | 0.644 | 0.000 | 20261020_173737 |
| 38 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.5 | 0.293 | 0.546 | 0.644 | **0.429** | 0.777 | 0.619 | 0.644 | 0.000 | 20261020_173737_2 |
| 41 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.3 | 0.276 | 0.556 | 0.679 | **0.427** | 0.787 | 0.639 | 0.679 | 0.000 | 20261020_173808 |
| 41 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.0 | 0.276 | 0.564 | 0.677 | **0.427** | 0.794 | 0.639 | 0.677 | 0.000 | 20261020_173811 |
| 43 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.4 | 0.288 | 0.539 | 0.664 | **0.426** | 0.799 | 0.617 | 0.664 | 0.000 | 20261020_173813 |
| 43 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.5 | 0.291 | 0.539 | 0.644 | **0.426** | 0.774 | 0.619 | 0.644 | 0.000 | 20261020_173813_2 |
| 43 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.5 | 0.288 | 0.554 | 0.639 | **0.426** | 0.762 | 0.586 | 0.639 | 0.000 | 20261020_173843 |
| 46 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc tắt | 0.291 | 0.541 | 0.639 | **0.425** | 0.767 | 0.644 | 0.639 | 0.000 | 20261020_173846 |
| 46 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.5 | 0.293 | 0.539 | 0.634 | **0.425** | 0.769 | 0.622 | 0.634 | 0.000 | 20261020_173847 |
| 48 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc t_unknown 0.7 | 0.286 | 0.541 | 0.647 | **0.424** | 0.784 | 0.614 | 0.647 | 0.000 | 20261020_173848 |
| 49 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.1 | 0.276 | 0.551 | 0.667 | **0.423** | 0.782 | 0.637 | 0.667 | 0.000 | 20261020_173907 |
| 50 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.2 | 0.278 | 0.546 | 0.662 | **0.422** | 0.777 | 0.637 | 0.662 | 0.000 | 20261020_173917 |
| 50 | Cơ chế 1 · tìm kiếm dense · end stored · cộng điểm domain W3 0.1 · chunk không mốc tắt | 0.291 | 0.541 | 0.632 | **0.422** | 0.764 | 0.644 | 0.632 | 0.000 | 20261020_173923 |
| 52 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.2 | 0.276 | 0.544 | 0.669 | **0.421** | 0.779 | 0.599 | 0.669 | 0.000 | 20261020_173924 |
| 52 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.0 | 0.278 | 0.544 | 0.664 | **0.421** | 0.784 | 0.604 | 0.664 | 0.000 | 20261020_173946 |
| 52 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.1 | 0.281 | 0.541 | 0.662 | **0.421** | 0.782 | 0.602 | 0.662 | 0.000 | 20261020_173946_2 |
| 52 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.4 | 0.276 | 0.554 | 0.662 | **0.421** | 0.777 | 0.639 | 0.662 | 0.000 | 20261020_173955 |
| 52 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.05 · chunk không mốc tắt | 0.286 | 0.544 | 0.632 | **0.421** | 0.762 | 0.642 | 0.632 | 0.000 | 20261020_174001 |
| 57 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.3 | 0.276 | 0.541 | 0.672 | **0.420** | 0.782 | 0.596 | 0.672 | 0.000 | 20261020_174020 |
| 57 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.4 | 0.276 | 0.546 | 0.669 | **0.420** | 0.782 | 0.596 | 0.669 | 0.000 | 20261020_174021 |
| 57 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc tắt | 0.286 | 0.549 | 0.632 | **0.420** | 0.764 | 0.644 | 0.632 | 0.000 | 20261020_174022 |
| 57 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc tắt | 0.288 | 0.529 | 0.632 | **0.420** | 0.764 | 0.644 | 0.632 | 0.000 | 20261020_174029 |
| 61 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.5 | 0.276 | 0.541 | 0.669 | **0.419** | 0.779 | 0.596 | 0.669 | 0.000 | 20261020_174042 |
| 61 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.5 | 0.276 | 0.544 | 0.657 | **0.419** | 0.772 | 0.639 | 0.657 | 0.000 | 20261020_174051 |
| 63 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc tắt | 0.268 | 0.554 | 0.659 | **0.418** | 0.774 | 0.652 | 0.659 | 0.000 | 20261020_174054 |
| 63 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc t_unknown 0.7 | 0.278 | 0.541 | 0.639 | **0.418** | 0.762 | 0.584 | 0.639 | 0.000 | 20261020_174056 |
| 63 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · chunk không mốc t_unknown 0.7 | 0.283 | 0.536 | 0.637 | **0.418** | 0.774 | 0.614 | 0.637 | 0.000 | 20261020_174115 |
| 63 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.2 · chunk không mốc t_unknown 0.7 | 0.286 | 0.526 | 0.632 | **0.418** | 0.767 | 0.617 | 0.632 | 0.000 | 20261020_174116 |
| 63 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc tắt | 0.288 | 0.534 | 0.622 | **0.418** | 0.757 | 0.644 | 0.622 | 0.000 | 20261020_174124 |
| 68 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.3 | 0.273 | 0.541 | 0.662 | **0.417** | 0.764 | 0.634 | 0.662 | 0.000 | 20261020_174131 |
| 69 | Cơ chế 1 · tìm kiếm dense · end unknown decay 0.3 · chunk không mốc t_unknown 0.7 | 0.283 | 0.524 | 0.632 | **0.416** | 0.767 | 0.619 | 0.632 | 0.000 | 20261020_174145 |
| 70 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.5 | 0.278 | 0.531 | 0.649 | **0.415** | 0.789 | 0.612 | 0.649 | 0.000 | 20261020_174150 |
| 71 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.4 | 0.273 | 0.534 | 0.649 | **0.413** | 0.762 | 0.632 | 0.649 | 0.000 | 20261020_174151 |
| 71 | Cơ chế 1 · tìm kiếm dense · end stored · chunk không mốc t_unknown 0.7 | 0.281 | 0.521 | 0.624 | **0.413** | 0.759 | 0.619 | 0.624 | 0.000 | 20261020_174204 |
| 71 | Cơ chế 1 · tìm kiếm dense · end open · chunk không mốc tắt | 0.286 | 0.536 | 0.607 | **0.413** | 0.734 | 0.604 | 0.607 | 0.000 | 20261020_174219 |
| 74 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc t_unknown 0.7 | 0.271 | 0.536 | 0.657 | **0.412** | 0.762 | 0.581 | 0.657 | 0.000 | 20261020_174224 |
| 75 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.5 | 0.273 | 0.531 | 0.647 | **0.411** | 0.759 | 0.632 | 0.647 | 0.000 | 20261020_174225 |
| 75 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc tắt | 0.273 | 0.531 | 0.634 | **0.411** | 0.764 | 0.637 | 0.634 | 0.000 | 20261020_174238 |
| 77 | Cơ chế 1 · tìm kiếm BM25 0.25 · end open · chunk không mốc tắt | 0.278 | 0.514 | 0.637 | **0.409** | 0.749 | 0.609 | 0.637 | 0.000 | 20261020_174239 |
| 78 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc tắt | 0.261 | 0.539 | 0.649 | **0.406** | 0.764 | 0.639 | 0.649 | 0.000 | 20261020_174259 |
| 78 | Cơ chế 1 · tìm kiếm dense · end decay 0.1 · chunk không mốc t_unknown 0.7 | 0.273 | 0.511 | 0.637 | **0.406** | 0.779 | 0.609 | 0.637 | 0.000 | 20261020_174300 |
| 80 | Cơ chế 1 · tìm kiếm BM25 0.25 · end stored · chunk không mốc t_unknown 0.7 | 0.263 | 0.536 | 0.639 | **0.405** | 0.752 | 0.627 | 0.639 | 0.000 | 20261020_174300_2 |
| 81 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.0 | 0.251 | 0.529 | 0.657 | **0.404** | 0.767 | 0.622 | 0.657 | 0.000 | 20261020_174300_3 |
| 82 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.0 | 0.248 | 0.526 | 0.662 | **0.403** | 0.774 | 0.607 | 0.662 | 0.000 | 20261020_174321 |
| 82 | Cơ chế 1 · tìm kiếm BM25 0.5 · end stored · chunk không mốc t_unknown 0.7 | 0.266 | 0.521 | 0.632 | **0.403** | 0.744 | 0.619 | 0.632 | 0.000 | 20261020_174335 |
| 84 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.1 | 0.251 | 0.519 | 0.654 | **0.402** | 0.772 | 0.604 | 0.654 | 0.000 | 20261020_174336 |
| 85 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.1 | 0.251 | 0.526 | 0.649 | **0.401** | 0.757 | 0.622 | 0.649 | 0.000 | 20261020_174337 |
| 86 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.2 | 0.253 | 0.524 | 0.642 | **0.400** | 0.752 | 0.622 | 0.642 | 0.000 | 20261020_174357 |
| 86 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.2 | 0.253 | 0.519 | 0.639 | **0.400** | 0.762 | 0.602 | 0.639 | 0.000 | 20261020_174411 |
| 88 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.3 | 0.253 | 0.514 | 0.639 | **0.398** | 0.764 | 0.602 | 0.639 | 0.000 | 20261020_174413 |
| 88 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.4 | 0.256 | 0.504 | 0.637 | **0.398** | 0.754 | 0.602 | 0.637 | 0.000 | 20261020_174413_2 |
| 90 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.0 | 0.246 | 0.521 | 0.649 | **0.396** | 0.759 | 0.602 | 0.649 | 0.000 | 20261020_174433 |
| 90 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.0 | 0.248 | 0.519 | 0.647 | **0.396** | 0.757 | 0.602 | 0.647 | 0.000 | 20261020_174446 |
| 90 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.1 | 0.248 | 0.514 | 0.644 | **0.396** | 0.757 | 0.602 | 0.644 | 0.000 | 20261020_174448 |
| 93 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.1 | 0.251 | 0.514 | 0.639 | **0.395** | 0.757 | 0.599 | 0.639 | 0.000 | 20261020_174448_2 |
| 94 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.3 | 0.248 | 0.514 | 0.637 | **0.394** | 0.744 | 0.619 | 0.637 | 0.000 | 20261020_174509 |
| 94 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.5 | 0.253 | 0.506 | 0.632 | **0.394** | 0.749 | 0.602 | 0.632 | 0.000 | 20261020_174523 |
| 94 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.2 | 0.253 | 0.511 | 0.629 | **0.394** | 0.747 | 0.596 | 0.629 | 0.000 | 20261020_174525 |
| 97 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.3 | 0.253 | 0.499 | 0.629 | **0.393** | 0.744 | 0.594 | 0.629 | 0.000 | 20261020_174526 |
| 98 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.2 | 0.251 | 0.506 | 0.632 | **0.392** | 0.747 | 0.599 | 0.632 | 0.000 | 20261020_174544 |
| 98 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.4 | 0.253 | 0.499 | 0.627 | **0.392** | 0.742 | 0.594 | 0.627 | 0.000 | 20261020_174557 |
| 100 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.4 | 0.248 | 0.511 | 0.629 | **0.391** | 0.737 | 0.619 | 0.629 | 0.000 | 20261020_174600 |
| 101 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.5 | 0.248 | 0.509 | 0.629 | **0.390** | 0.737 | 0.619 | 0.629 | 0.000 | 20261020_174600_2 |
| 102 | Chỉ lọc thời gian (bỏ điểm thời gian) · tìm kiếm dense | 0.268 | 0.494 | 0.607 | **0.389** | 0.722 | 0.534 | 0.607 | 0.000 | 20261020_174619 |
| 103 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.5 | 0.248 | 0.494 | 0.637 | **0.388** | 0.739 | 0.574 | 0.637 | 0.000 | 20261020_174633 |
| 103 | Cơ chế 1 · tìm kiếm hybrid · end stored · cộng điểm domain W3 0.2 · chunk không mốc tắt | 0.241 | 0.514 | 0.629 | **0.388** | 0.742 | 0.624 | 0.629 | 0.000 | 20261020_174636 |
| 103 | Cơ chế 1 · tìm kiếm hybrid · end stored · cộng điểm domain W3 0.05 · chunk không mốc tắt | 0.241 | 0.511 | 0.627 | **0.388** | 0.742 | 0.624 | 0.627 | 0.000 | 20261020_174637 |
| 103 | Cơ chế 1 · tìm kiếm hybrid · end stored · cộng điểm domain W3 0.1 · chunk không mốc tắt | 0.241 | 0.514 | 0.627 | **0.388** | 0.742 | 0.624 | 0.627 | 0.000 | 20261020_174639 |
| 107 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.2 | 0.248 | 0.501 | 0.627 | **0.387** | 0.742 | 0.579 | 0.627 | 0.000 | 20261020_174658 |
| 107 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.3 | 0.248 | 0.501 | 0.624 | **0.387** | 0.742 | 0.596 | 0.624 | 0.000 | 20261020_174658_2 |
| 107 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.5 | 0.246 | 0.499 | 0.622 | **0.387** | 0.734 | 0.594 | 0.622 | 0.000 | 20261020_174701 |
| 110 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.1 | 0.246 | 0.499 | 0.629 | **0.386** | 0.742 | 0.579 | 0.629 | 0.000 | 20261020_174710 |
| 110 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.4 | 0.248 | 0.494 | 0.629 | **0.386** | 0.734 | 0.574 | 0.629 | 0.000 | 20261020_174734 |
| 110 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.3 | 0.248 | 0.501 | 0.627 | **0.386** | 0.734 | 0.574 | 0.627 | 0.000 | 20261020_174734_2 |
| 110 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc tắt | 0.241 | 0.509 | 0.627 | **0.386** | 0.739 | 0.624 | 0.627 | 0.000 | 20261020_174736 |
| 110 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.7 | 0.248 | 0.504 | 0.622 | **0.386** | 0.724 | 0.564 | 0.622 | 0.000 | 20261020_174745 |
| 115 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.4 | 0.248 | 0.496 | 0.622 | **0.385** | 0.737 | 0.594 | 0.622 | 0.000 | 20261020_174757 |
| 115 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc t_unknown 0.7 | 0.248 | 0.496 | 0.617 | **0.385** | 0.739 | 0.589 | 0.617 | 0.000 | 20261020_174809 |
| 117 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc t_unknown 0.0 | 0.243 | 0.496 | 0.629 | **0.384** | 0.742 | 0.579 | 0.629 | 0.000 | 20261020_174810 |
| 118 | Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc t_unknown 0.7 | 0.243 | 0.506 | 0.612 | **0.383** | 0.727 | 0.604 | 0.612 | 0.000 | 20261020_174820 |
| 119 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.05 · chunk không mốc tắt | 0.241 | 0.501 | 0.612 | **0.381** | 0.729 | 0.609 | 0.612 | 0.000 | 20261020_174832 |
| 119 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.5 | 0.246 | 0.491 | 0.612 | **0.381** | 0.727 | 0.594 | 0.612 | 0.000 | 20261020_174845 |
| 119 | Cơ chế 1 · tìm kiếm hybrid · end stored · lọc cứng domain · chunk không mốc tắt | 0.243 | 0.501 | 0.609 | **0.381** | 0.717 | 0.614 | 0.609 | 0.000 | 20261020_174845_2 |
| 122 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc tắt | 0.238 | 0.499 | 0.607 | **0.379** | 0.719 | 0.607 | 0.607 | 0.000 | 20261020_174853 |
| 123 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · chunk không mốc t_unknown 0.7 | 0.243 | 0.484 | 0.607 | **0.378** | 0.719 | 0.576 | 0.607 | 0.000 | 20261020_174855 |
| 124 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc tắt | 0.236 | 0.496 | 0.609 | **0.376** | 0.724 | 0.602 | 0.609 | 0.000 | 20261020_174907 |
| 125 | Cơ chế 1 · tìm kiếm hybrid · end decay 0.2 · chunk không mốc t_unknown 0.7 | 0.243 | 0.479 | 0.596 | **0.374** | 0.717 | 0.579 | 0.596 | 0.000 | 20261020_174914 |
| 126 | Cơ chế 1 · tìm kiếm hybrid · end open · chunk không mốc tắt | 0.231 | 0.474 | 0.589 | **0.364** | 0.704 | 0.581 | 0.589 | 0.000 | 20261020_174921 |
| 127 | Chỉ lọc thời gian (bỏ điểm thời gian) · tìm kiếm hybrid | 0.226 | 0.444 | 0.554 | **0.350** | 0.679 | 0.496 | 0.554 | 0.000 | 20261020_174928 |
| 128 | Plain RAG · dense | 0.226 | 0.424 | 0.549 | **0.339** | 0.664 | 0.409 | 0.549 | 0.665 | 20261020_174930 |
| 129 | Plain RAG · hybrid | 0.226 | 0.388 | 0.509 | **0.322** | 0.624 | 0.373 | 0.509 | 0.680 | 20261020_174942 |
| 130 | Plain RAG · BM25 | 0.178 | 0.338 | 0.424 | **0.267** | 0.539 | 0.313 | 0.424 | 0.675 | 20261020_174948 |
| — | Oracle (t_req từ nhãn) · Cơ chế 1 · tìm kiếm hybrid · end stored · chunk không mốc tắt | 0.253 | 0.536 | 0.639 | **0.398** | 0.764 | 0.612 | 0.639 | 0.000 | 20261020_174948_2 |
| — | Oracle (t_req từ nhãn) · Chỉ lọc thời gian (bỏ điểm thời gian) · tìm kiếm hybrid | 0.236 | 0.454 | 0.554 | **0.357** | 0.682 | 0.466 | 0.554 | 0.000 | 20261020_174951 |

## Phụ lục B. Cấu hình có chunk liền kề (38 nhóm, xếp riêng vì không đổi thứ hạng)

| Cấu hình | `hit@5` | `ctx_hit` | `mrr` | Thư mục |
|---|---|---|---|---|
| Cơ chế 1 · tìm kiếm dense · end decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.684 | **0.797** | 0.438 | 20261020_175047 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.679 | **0.794** | 0.441 | 20261020_175038 |
| Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.687 | **0.789** | 0.444 | 20261020_175007 |
| Cơ chế 1 · tìm kiếm hybrid · end stored · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.649 | **0.777** | 0.401 | 20261020_175259 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.2 | 0.677 | **0.774** | 0.440 | 20261020_175045 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.679 | **0.772** | 0.441 | 20261020_175010 |
| Cơ chế 1 · tìm kiếm hybrid · end unknown decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.644 | **0.772** | 0.401 | 20261020_175308 |
| Cơ chế 1 · tìm kiếm dense · end open · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.647 | **0.769** | 0.430 | 20261020_175124 |
| Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.687 | **0.769** | 0.444 | 20261020_175002 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.0 | 0.684 | **0.767** | 0.442 | 20261020_175008 |
| Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.644 | **0.767** | 0.396 | 20261020_175335 |
| Cơ chế 1 · tìm kiếm dense · end decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.684 | **0.764** | 0.438 | 20261020_175045_2 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.3 | 0.669 | **0.764** | 0.438 | 20261020_175115 |
| Cơ chế 1 · tìm kiếm hybrid · end open · lấy thêm 2 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.629 | **0.754** | 0.386 | 20261020_175345 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.4 | 0.644 | **0.752** | 0.432 | 20261020_175122 |
| Cơ chế 1 · tìm kiếm dense · end open · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.647 | **0.747** | 0.430 | 20261020_175122_2 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.5 | 0.634 | **0.744** | 0.425 | 20261020_175152 |
| Cơ chế 1 · tìm kiếm hybrid · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.649 | **0.744** | 0.401 | 20261020_175251 |
| Cơ chế 1 · tìm kiếm hybrid · end stored · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.627 | **0.737** | 0.386 | 20261020_175412 |
| Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.607 | **0.732** | 0.379 | 20261020_175440 |
| Cơ chế 1 · tìm kiếm hybrid · end unknown decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.617 | **0.732** | 0.383 | 20261020_175424 |
| Cơ chế 1 · tìm kiếm dense · end decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.634 | **0.729** | 0.411 | 20261020_175245 |
| Cơ chế 1 · tìm kiếm hybrid · end unknown decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.644 | **0.729** | 0.401 | 20261020_175307 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.7 | 0.624 | **0.727** | 0.413 | 20261020_175222_2 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.622 | **0.727** | 0.418 | 20261020_175222 |
| Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.632 | **0.727** | 0.420 | 20261020_175159 |
| Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.644 | **0.727** | 0.396 | 20261020_175327 |
| Cơ chế 1 · tìm kiếm dense · end open · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.607 | **0.717** | 0.413 | 20261020_175228 |
| Cơ chế 1 · tìm kiếm hybrid · end open · lấy thêm 1 chunk liền kề · chunk không mốc t_unknown 0.1 | 0.629 | **0.714** | 0.386 | 20261020_175344 |
| Cơ chế 1 · tìm kiếm hybrid · end open · lấy thêm 2 chunk liền kề · chunk không mốc tắt | 0.589 | **0.712** | 0.364 | 20261020_175450 |
| Cơ chế 1 · tìm kiếm hybrid · end stored · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.627 | **0.707** | 0.386 | 20261020_175404 |
| Cơ chế 1 · tìm kiếm dense · end unknown decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.632 | **0.699** | 0.420 | 20261020_175158 |
| Cơ chế 1 · tìm kiếm dense · end decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.634 | **0.697** | 0.411 | 20261020_175244 |
| Cơ chế 1 · tìm kiếm dense · end open · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.607 | **0.697** | 0.413 | 20261020_175222_3 |
| Cơ chế 1 · tìm kiếm dense · end stored · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.622 | **0.697** | 0.418 | 20261020_175159_2 |
| Cơ chế 1 · tìm kiếm hybrid · end unknown decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.617 | **0.692** | 0.383 | 20261020_175423 |
| Cơ chế 1 · tìm kiếm hybrid · end decay 0.1 · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.607 | **0.679** | 0.379 | 20261020_175431 |
| Cơ chế 1 · tìm kiếm hybrid · end open · lấy thêm 1 chunk liền kề · chunk không mốc tắt | 0.589 | **0.674** | 0.364 | 20261020_175449 |

## Phụ lục C. So sánh từng cấu hình local và bộ thật

[`results_compare.csv`](../../dataset/eval/results_compare.csv): 170 dòng, cột `mrr`/`hit@1`/`hit@3`/`hit@5` ở hai bộ, `delta_mrr` và thư mục `output/` của từng lần chạy.
