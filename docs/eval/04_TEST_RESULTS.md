# Kết quả các đợt test (bộ local)

Kế hoạch và lệnh chạy: [`03_TEST_ROUNDS.md`](03_TEST_ROUNDS.md). Mọi số dưới đây từ **một lần ingestion** và **một lần Profiler**, 40 câu mức `hard`, ngày chạy 2026-10-19.

| Thứ | Giá trị |
|---|---|
| LLM | combo 9router `basic-gemini-3.5-flash-lite` (combo `basic-gemini-3.1-flash-lite` bị Gemini trả 503 "high demand" nên đổi) |
| Ingestion | `output/20261019_222626/`, `ingest.py --recreate --keep-undated`: 37 trang, 1275 chunk, nạp 1259 (**309 chunk không mốc**), bỏ 14 `no_time` và 2 `invalid_time`, 0 lỗi LLM. 61 lần gọi LLM |
| Profiler | `output/20261019_222137/profiler.jsonl`, 40/40 câu thành công |
| Qdrant | collection `tam_chunks_dev`, 1259 điểm |

**Không so được với [`02`](02_RETRIEVAL_LOCAL.md):** kho khác (1259 chunk so với 954 vì giờ giữ chunk không mốc), model khác (Gemini 3.5 so với `basic-llm`), và 40 câu đều có chunk đáp án trong kho (trước là 37). Số ở đây chỉ so với nhau.

**Sai số:** 40 câu; một câu đổi chiều là 2.5 điểm phần trăm, sai số khoảng ±15 điểm. Chênh dưới khoảng 2 câu thì ghi "chưa kết luận".

## Bảng xếp hạng (theo `mrr`, càng cao càng tốt)

Tất cả chạy ở chế độ **e2e** (Profiler trích `t_req` từ câu hỏi), trừ dòng tham chiếu. Chênh dưới khoảng 0.05 `mrr` là chưa phân biệt được.

| Hạng | Phương pháp | `hit@1` | `hit@5` | `mrr` | `leakage_rate` | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | Cơ chế 1 + nhánh chunk không mốc (`t_unknown` 0.3 đến 0.7) | 0.325 | 0.675 | 0.452 | 0 | So từng câu chỉ ròng +1 câu (3 lên, 2 xuống): chưa kết luận |
| 2 | Cơ chế 1 (lọc thời gian + điểm thời gian, `end_mode: stored`) | 0.275 | 0.650 | 0.420 | 0 | Cấu hình nền |
| 2 | Cơ chế 1 + **lọc cứng domain** | 0.275 | 0.650 | 0.420 | 0 | Giống hệt hạng 2 trên (chỉ 13/40 câu có domain) |
| 2 | Cơ chế 1 + cộng điểm domain (`W3` 0.05, 0.1, 0.2) | 0.275 | 0.650 | 0.420 | 0 | Giống hệt |
| 5 | Cơ chế 1 với `end_mode: open` | 0.250 | 0.675 | 0.418 | 0 | Hòa với hạng 2 |
| 6 | Cơ chế 1 với `end_mode: decay` (0.05 / 0.1 / 0.2) | 0.225 | 0.650 đến 0.700 | 0.408 / 0.402 / 0.390 | 0 | Hơi kém |
| 7 | Dense thuần (plain RAG) | 0.225 | 0.500 | 0.340 | **0.675** | Rò rỉ tương lai |
| 8 | Hybrid + lọc thời gian, không điểm thời gian | 0.175 | 0.575 | 0.323 | 0 | |
| 9 | Hybrid thuần | 0.100 | 0.475 | 0.245 | **0.725** | Rò rỉ tương lai |
| 10 | BM25 thuần | 0.125 | 0.250 | 0.179 | **0.725** | Rò rỉ tương lai |
| (tham chiếu) | Oracle (`t_req` lấy từ nhãn, không qua Profiler) | 0.300 | 0.700 | 0.458 | 0 | Mức trần của Cơ chế 1; không phải một phương pháp |

**Đọc nhanh:** Cơ chế 1 hơn plain RAG (dense) 0.080 `mrr` và 0.15 `hit@5` (+6 câu), lại không rò rỉ. Phần đóng góp lớn nhất là điểm thời gian (hạng 8 lên hạng 2: 0.323 → 0.420). Các biến thể nhỏ hơn (cách chấm `end`, domain) chưa phân biệt được trên 40 câu.

## Cách đọc các cột (dùng chung cho mọi đợt)

Mỗi câu hỏi có một hoặc vài **chunk đáp án** (gold). Hệ trả về 5 chunk xếp hạng (top 5).

| Cột | Nghĩa | Ví dụ |
|---|---|---|
| `hit@k` | Tỉ lệ câu có chunk đáp án nằm trong top k | `hit@5` = 0.650: 26/40 câu có chunk đáp án trong 5 chunk đầu |
| `mrr` | Trung bình của 1 chia cho hạng của chunk đáp án đầu tiên (hạng 1 được 1.0, hạng 2 được 0.5, hạng 5 được 0.2, không có trong top 5 được 0). Thưởng nhiều hơn khi đáp án nằm cao | Đáp án ở hạng 1 trong mọi câu thì `mrr` = 1 |
| `recall@k` | Với câu có nhiều chunk đáp án: tỉ lệ chunk đáp án tìm được trong top k | Câu có 2 đáp án, tìm được 1: recall = 0.5 |
| `leakage_rate` | Tỉ lệ câu có ít nhất một chunk top 5 có `start_time` **sau** thời điểm hỏi `t_req` (hệ "nhìn thấy tương lai") | Hỏi về năm 1968 mà kết quả có đoạn nói sự việc năm 1990. Phải bằng 0 |
| `invalidated_rate` | Tỉ lệ câu có chunk bị đánh dấu `invalidated_at` (thông tin sai từ đầu: tin giả, đính chính). Phải bằng 0 | Bộ local ít khi có loại này nên 0 chưa chứng minh nhiều |
| `forbidden_rate` | Tỉ lệ câu có chunk nằm trong danh sách "tuyệt đối không được xuất hiện" của câu | Bộ local không dùng, luôn 0 |

**Hai chế độ chạy:**
- **e2e** (end to end): Profiler (LLM) đọc câu hỏi và tự trích thời điểm cần hỏi `t_req`. Đây là hệ thật.
- **oracle**: dùng luôn `t_req` lấy từ nhãn của dataset, bỏ qua Profiler. Cho biết trần nếu bước trích thời gian hoàn hảo. Chênh giữa oracle và e2e là phần mất do Profiler.

**Hai thứ cùng gọi "lọc cứng" (hay nhầm):**
- **Lọc cứng thời gian** (`start_time <= t_req`): luôn bật trong mọi cấu hình của Cơ chế 1, loại chunk bắt đầu sau thời điểm hỏi. Đây là thứ giúp `leakage_rate` bằng 0.
- **Lọc cứng domain** (`--facets domain`): chỉ giữ chunk có domain trùng domain Profiler trích từ câu hỏi. Chỉ dùng ở đợt 5 (và một dòng ở đợt 0).

## Đợt 0. Chạy thông

**Làm gì:** kiểm tra pipeline chạy hết từ đầu đến cuối và không rò rỉ tương lai. Chưa phải đợt để so phương pháp nào hơn.

**Cơ chế:** 5 cấu hình đầu tiên của dự án. Mỗi cấu hình khác nhau ở một chỗ:
- `oracle` và `e2e`: xem mục trên.
- `--no-temporal`: đặt `W1 = 1`, `W2 = 0`, tức **bỏ điểm thời gian**, chỉ xếp theo độ giống nội dung. Lọc cứng thời gian vẫn bật, nên vẫn không rò rỉ.
- `--facets domain`: thêm lọc cứng domain.

| Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `leakage_rate` | `invalidated_rate` | Thư mục |
|---|---|---|---|---|---|---|---|
| oracle | 0.300 | 0.575 | 0.700 | 0.458 | 0 | 0 | `224156_2` |
| oracle `--no-temporal` | 0.200 | 0.450 | 0.625 | 0.353 | 0 | 0 | `224156_4` |
| e2e | 0.275 | 0.525 | 0.650 | 0.420 | 0 | 0 | `224156` |
| e2e `--no-temporal` | 0.175 | 0.425 | 0.575 | 0.323 | 0 | 0 | `224156_3` |
| e2e `--facets domain` | 0.275 | 0.525 | 0.650 | 0.420 | 0 | 0 | `224200` |

(Thư mục là `output/20261019_22xxxx`; cột `hit@3` là tỉ lệ câu có đáp án trong 3 chunk đầu.)

**Kết luận:** pass. Rò rỉ và chunk vô hiệu bằng 0 ở mọi cấu hình. Oracle hơn e2e 0.038 `mrr` (khoảng 1.5 câu): phần mất do Profiler là nhỏ. `--no-temporal` kém hơn rõ (0.323 so 0.420), cho thấy điểm thời gian có tác dụng. Dòng cuối (lọc cứng domain) trùng với `e2e`: xem đợt 5.

## Đợt 1. Baseline (so với RAG thường)

**Làm gì:** trả lời "hệ có hơn plain RAG không, và nhờ thành phần nào". Chạy một chuỗi từ RAG đơn giản nhất, thêm dần từng thành phần của Cơ chế 1; hiệu giữa hai bậc liền nhau là đóng góp của thành phần vừa thêm.

**Cơ chế từng bậc** (tất cả lấy 5 chunk từ cùng kho Qdrant):
- a. **dense**: tìm theo vector ngữ nghĩa (embedding).
- b. **BM25**: tìm theo từ khóa.
- c. **hybrid**: gộp dense và BM25 bằng RRF (xếp hạng lại theo thứ hạng của hai danh sách), không lọc thời gian.
- d. **hybrid + lọc thời gian**: như c nhưng loại chunk có `start_time > t_req` và chunk bị vô hiệu.
- e. **+ điểm thời gian (Cơ chế 1)**: như d, rồi xếp lại bằng `Final = 0.7·Semantic + 0.3·Temporal`. `Temporal` = 1.0 nếu `t_req` nằm trong `[start, end]` của chunk (TH1); nếu chunk đã hết hiệu lực trước `t_req` thì `exp(-0.5·Δ)` với Δ là số năm từ `start` của chunk đến `t_req` (TH2), chunk càng xa thì điểm càng thấp.

Bậc a, b, c là baseline: không lọc thời gian nên `leakage_rate` > 0 là bình thường và là điều cần chỉ ra.

| Bậc | Cấu hình | `hit@1` | `hit@3` | `hit@5` | `mrr` | `leakage_rate` | Thư mục |
|---|---|---|---|---|---|---|---|
| a | dense | 0.225 | 0.450 | 0.500 | 0.340 | **0.675** | `224200_2` |
| b | BM25 | 0.125 | 0.250 | 0.250 | 0.179 | **0.725** | `224200_3` |
| c | hybrid (không lọc) | 0.100 | 0.375 | 0.475 | 0.245 | **0.725** | `224200_4` |
| d | hybrid + lọc thời gian | 0.175 | 0.425 | 0.575 | 0.323 | 0 | `224156_3` |
| e | + điểm thời gian (Cơ chế 1) | 0.275 | 0.525 | 0.650 | 0.420 | 0 | `224156` |

- **Lọc thời gian (c → d):** `mrr` 0.245 → 0.323, `leakage` 0.725 → 0. Đóng góp chính là loại rò rỉ: baseline không lọc có 67 đến 73% câu có chunk sau `t_req` trong top 5.
- **Điểm thời gian (d → e):** `mrr` 0.323 → 0.420, `hit@1` 0.175 → 0.275 (+4 câu). Đóng góp rõ nhất của Cơ chế 1.
- **So plain RAG:** e so với a (dense) hơn 0.080 `mrr` và 0.15 `hit@5` (+6 câu), và không rò rỉ. So với hybrid (c) hơn 0.175 `mrr`.
- **Bất ngờ:** dense (a) tốt hơn hybrid (c): BM25 yếu (`mrr` 0.179) nên kéo RRF xuống. Bậc d, e vẫn dùng hybrid. Đáng thử đổi `top_n`, trọng số RRF hoặc bỏ BM25 (ngoài kế hoạch, ghi nhận để sau).

## Đợt 2. Chẩn đoán từng bước

**Làm gì:** không chạy cấu hình mới. Đọc các số đo từng bước trong `metrics.json` của bậc e để biết **lỗi nằm ở bước nào**: Profiler, tìm ứng viên, lọc cứng hay chấm điểm.

**Cơ chế:** một câu hỏi đi qua 4 bước; mỗi bước có thể làm mất chunk đáp án:

1. **Profiler** trích `t_req`, `domain` từ câu hỏi.
2. **Tìm ứng viên**: dense và BM25 mỗi bên lấy 50 chunk (`top_n`), gộp bằng RRF.
3. **Lọc cứng thời gian**: loại chunk `start_time > t_req`.
4. **Chấm điểm**: `Final = 0.7·Semantic + 0.3·Temporal`, lấy top 5.

| Bước | Cột | Nghĩa | Giá trị |
|---|---|---|---|
| 1. Profiler | `t_req_in_label_range` | `t_req` Profiler trích có nằm trong khoảng thời gian nhãn của câu hỏi không | 38/40 |
| | `t_req_abs_error_years_mean` | Sai số trung bình (năm) giữa `t_req` và giữa khoảng nhãn | 3.66 |
| | `domain_given` / `domain_in_gold_chunk` | Số câu Profiler điền domain / số câu domain đó trùng domain của chunk đáp án | 13 / 13 |
| 2. Ứng viên | `cand_recall_dense` / `sparse` / `fused` | Tỉ lệ câu có chunk đáp án trong 50 ứng viên của dense / BM25 / sau gộp RRF | 0.875 / 0.825 / 0.875 |
| 3. Lọc cứng | `gold_blocked_by_filter` | Số câu chunk đáp án bị lọc cứng thời gian loại mất (vì `start_time` của nó sau `t_req`, do `t_req` hoặc `start` sai) | 5 |
| 4. Chấm điểm | `hit@5_pre`, `mrr_pre` | `hit@5` và `mrr` nếu chỉ xếp theo điểm ngữ nghĩa, **chưa** cộng điểm thời gian | 0.575 / 0.380 |
| | `hit@5`, `mrr` | Sau khi cộng điểm thời gian | 0.650 / 0.420 |
| | `temporal_helped` / `hurt` / `same` | Số câu chunk đáp án lên hạng / xuống hạng / không đổi nhờ điểm thời gian | 15 / 7 / 13 |

**Đọc:**
- Profiler tốt: `t_req` đúng ở 38/40 câu, domain đúng 13/13.
- Tìm ứng viên mất 12.5% câu (chunk đáp án không lọt 50 ứng viên), là trần của bước này.
- **Lọc cứng chặn mất 5/40 chunk đáp án**: lỗi lớn nhất sau bước tìm ứng viên. Cần xem 5 câu này: `start_time` LLM gán sai hay `t_req` sai.
- Điểm thời gian giúp 15 câu, hại 7: ròng +8 câu lên hạng.

## Đợt 3. Cách chấm điểm `end`

**Làm gì:** chọn cách xử lý chunk mà LLM không biết chắc **khi nào sự việc kết thúc**.

**Cơ chế:** mỗi chunk có `end_status` ∈ {`known` (biết ngày kết thúc), `ongoing` (LLM khẳng định còn tiếp diễn), `unknown` (không biết)}. Với `known` thì không bàn. Với `ongoing` / `unknown` có 3 cách chấm cho điểm thời gian (`--end-mode`):
- **C `stored` (mặc định)**: `ongoing` thì coi còn hiệu lực mãi (điểm 1.0 với mọi `t_req` sau `start`); `unknown` thì coi như kết thúc cuối kỳ của `start` (ví dụ `start` = 1990 thì hết hiệu lực cuối 1990; `t_req` sau đó được điểm TH2 giảm dần).
- **A `open`**: cả `ongoing` lẫn `unknown` đều coi còn hiệu lực mãi (điểm 1.0).
- **B `decay`**: `ongoing` / `unknown` điểm giảm dần `exp(-d·Δ)` với Δ là số năm từ `start` đến `t_req`, để chunk bắt đầu gần `t_req` nhất thắng. `d` là `open_decay` (thử 0.05, 0.1, 0.2).

| `end_mode` | `hit@1` | `hit@3` | `hit@5` | `mrr` | `temporal_helped / hurt` | Thư mục |
|---|---|---|---|---|---|---|
| `stored` (C) | 0.275 | 0.525 | 0.650 | **0.420** | 15 / 7 | `224156` |
| `open` (A) | 0.250 | 0.575 | 0.675 | 0.418 | 16 / 4 | `224227_4` |
| `decay` 0.05 (B) | 0.225 | 0.525 | 0.700 | 0.408 | 17 / 8 | `224227_3` |
| `decay` 0.1 (B) | 0.225 | 0.500 | 0.700 | 0.402 | 17 / 7 | `224227_2` |
| `decay` 0.2 (B) | 0.225 | 0.500 | 0.650 | 0.390 | 15 / 8 | `224227` |

**Quyết định: giữ `stored`** (`mrr` cao nhất; hòa với `open` trong 1 câu thì chọn cái đơn giản). Chênh giữa các cách chỉ 0.002 đến 0.030 `mrr` (dưới 1 câu): **chưa kết luận được cách nào hơn**. Không cách nào thắng ở mọi chỉ số: `open` có `hurt` thấp nhất (4) và `hit@5` cao hơn `stored`; `decay` có `hit@5` cao nhất (0.700) nhưng `hit@1` thấp nhất. Chọn lại trên bộ lớn hơn.

### 3b. Chunk liền kề

**Làm gì:** chunk đáp án đôi khi nằm cạnh chunk tìm được (cùng trang, số thứ tự kề). Thử kèm thêm chunk liền kề vào ngữ cảnh đưa cho LLM trả lời.

**Cơ chế:** chunk tìm được `Trang#i` thì lấy thêm `Trang#i-1 ... i+n` và `Trang#i+1 ... i+n` (`n` = `--neighbors`, gọi là window). Chunk liền kề vẫn phải qua lọc cứng thời gian, nhưng không chấm điểm và **không đổi thứ hạng top 5**: chúng chỉ nằm thêm trong "ngữ cảnh".

| Cột | Nghĩa |
|---|---|
| `hit@5` | Như trên, chỉ tính 5 chunk xếp hạng (không đổi theo `neighbors`) |
| `ctx_hit` | Tỉ lệ câu có chunk đáp án trong **ngữ cảnh** (5 chunk + chunk liền kề) |
| `ctx_recall` | Như `recall@k` nhưng tính trên ngữ cảnh |
| `rescued_by_neighbors` | Số câu mà chunk đáp án **không** nằm trong top 5 nhưng nằm trong chunk liền kề |
| `ctx_size_mean` | Số chunk trung bình trong ngữ cảnh: chi phí token (5 khi không mở rộng) |

| `neighbors` | `hit@5` | `ctx_hit` | `ctx_recall` | `rescued_by_neighbors` | `ctx_size_mean` | `mrr` |
|---|---|---|---|---|---|---|
| 0 | 0.650 | 0.650 | 0.650 | 0 | 5.0 | 0.420 |
| 1 | 0.650 | **0.725** | 0.725 | **3** | 7.9 | 0.420 |
| 2 | 0.650 | 0.725 | 0.725 | 3 | 10.1 | 0.420 |

**Quyết định: window = 1.** Cứu thêm 3 câu (`ctx_hit` 0.650 → 0.725) với chi phí 7.9 chunk thay vì 5 (+58% ngữ cảnh). Window 2 không cứu thêm câu nào, chỉ tốn thêm. 3 câu là ít nên chưa chặt, nhưng chiều hướng rõ vì window 2 không thêm gì.

### 3c. Câu cần nhiều chunk

**Làm gì:** có câu cần ghép 2 chunk trở lên mới trả lời được; đo riêng nhóm này vì `hit@k` thường (chỉ cần 1 chunk) sẽ đánh giá cao.

**Cơ chế và cột:** `n_multi_gold` = số câu có ≥ 2 chunk đáp án. `multi_all_hit@k` = tỉ lệ câu loại này tìm đủ **mọi** chunk đáp án trong top k (khắt khe hơn `hit@k`). `multi_recall@k` = tỉ lệ chunk đáp án tìm được. `ctx_multi_all_hit` = như `multi_all_hit` nhưng tính trên ngữ cảnh (có chunk liền kề).

**Kết quả:** `n_multi_gold` = 1 (chỉ 1 câu), `multi_all_hit@5` = 1.0 và `ctx_multi_all_hit` = 1.0 ở mọi cấu hình. Chỉ xác nhận code chạy đúng; chưa có ý nghĩa thống kê (bộ thật mới có).

## Đợt 4. Chunk không mốc

**Làm gì:** nhiều chunk (ở đây 309/1259) không có năm hay mốc thời gian nào, vì đoạn văn mô tả sự việc ổn định ("Pskov là thành phố ở Tây Bắc Nga"). Trước đây bị bỏ; đợt này giữ chúng lại và thử cho chúng cơ hội được trả về.

**Cơ chế:** chunk không mốc có `start_time` rỗng nên lọc cứng thời gian loại hết chúng. Bật `--t-unknown X` thì thêm **nhánh thứ ba** tìm riêng chunk không mốc (dense và BM25), gộp với kết quả chính. Chunk không mốc không có TH1 hay TH2, nên cho điểm thời gian cố định `T_unknown = X`:

`Final = 0.7·Semantic + 0.3·X`

(Chunk có mốc đúng lúc được 1.0; chunk hết hiệu lực xa được gần 0. `X` càng cao thì chunk không mốc càng dễ thắng.) Nền: `stored`, `neighbors` 0.

| Cột | Nghĩa |
|---|---|
| `undated_in_results_rate` | Tỉ lệ câu có ít nhất một chunk không mốc trong top 5 |
| `temporal_helped / hurt` | Như đợt 2 |

| `t_unknown` | `hit@1` | `hit@5` | `mrr` | `undated_in_results_rate` | helped / hurt | Thư mục |
|---|---|---|---|---|---|---|
| tắt | 0.275 | 0.650 | 0.420 | 0 | 15 / 7 | `224156` |
| 0.3 | 0.325 | 0.675 | 0.452 | 0.525 | 18 / 9 | `224241_4` |
| 0.5 | 0.325 | 0.675 | 0.452 | 0.600 | 18 / 9 | `224241` |
| 0.7 | 0.325 | 0.675 | 0.452 | 0.700 | 18 / 9 | `224245_2` |

So từng câu (tắt so với 0.5): thứ hạng đổi ở 30/40 câu, nhưng chunk đáp án đổi hạng ở chỉ 5 câu: **3 lên, 2 xuống**.
- Lên: `Pskov#P17#3` (đáp án không mốc được cứu, 0 → 1.0), `Air_Armament_Center#P1448#1` (0.5 → 1.0), `Central_European_University#P1075#1` (0 → 0.25).
- Xuống: `Central_European_University#P1075#0` (0.2 → 0), `Vista_House#P1435#0` (0.5 → 0.2); cả hai có chunk không mốc chen vào top 5.

**Kết luận:** nhánh cứu được chunk đáp án không mốc (Pskov) và `mrr` tăng 0.032, nhưng ròng chỉ +1 câu (3 lên, 2 xuống): **chưa kết luận**. Giữ làm tùy chọn, mặc định vẫn tắt. Quy tắc ở `03` ("cứu được chunk đáp án và `mrr` trên câu có mốc không giảm quá 1 câu") xét đúng thì 2 câu xuống đã chạm ngưỡng 1 câu, nên chưa đủ chắc để bật mặc định (chưa tách riêng nhóm câu có mốc). `t_unknown` 0.3, 0.5, 0.7 cho **kết quả giống hệt** (cùng `hit`/`mrr`; chỉ `undated_in_results_rate` tăng 0.525 → 0.700): không phân biệt được ở local. Nếu bật, chọn 0.3 (ít chunk không mốc chen kết quả nhất, cùng `mrr`). Cần đo lại trên bộ thật, nơi chunk đáp án không mốc nhiều hơn 3.

## Đợt 5. Domain

**Làm gì:** câu hỏi đôi khi nêu rõ lĩnh vực ("trong thể thao..."), Profiler điền `domain`. Thử dùng nó theo hai cách và so với không dùng.

**Cơ chế:**
- **Không dùng** (mặc định): bỏ qua domain.
- **Lọc cứng** `--facets domain`: chỉ giữ chunk có domain trùng domain của câu hỏi. Nguy cơ: Profiler hoặc LLM gán domain sai thì chunk đúng bị loại hẳn.
- **Cộng điểm** `--facets boost --w3 X`: không loại gì; thêm `W3·Domain_Match` vào điểm (`Domain_Match` = 1 nếu chunk có ít nhất một nhãn domain trùng domain câu hỏi, ngược lại 0; mỗi chunk có tối đa 3 nhãn). Domain sai thì chỉ mất một ít điểm, không mất chunk.

| Cột | Nghĩa |
|---|---|
| `W3` | Trọng số điểm domain (0.05, 0.1, 0.2) |
| `domain_given` | Số câu Profiler điền domain (13/40) |
| `domain_in_gold_chunk` | Trong số đó, bao nhiêu câu domain trùng domain của chunk đáp án (13/13) |

| Cấu hình | `hit@1` | `hit@5` | `mrr` | Thư mục |
|---|---|---|---|---|
| không dùng domain | 0.275 | 0.650 | 0.420 | `224156` |
| lọc cứng `--facets domain` | 0.275 | 0.650 | 0.420 | `224200` |
| cộng điểm `W3` = 0.05 | 0.275 | 0.650 | 0.420 | `224245` |
| `W3` = 0.1 | 0.275 | 0.650 | 0.420 | `224246` |
| `W3` = 0.2 | 0.275 | 0.650 | 0.420 | `224247` |

So từng câu với "không dùng": thứ hạng đổi ở 2 đến 5 câu nhưng chunk đáp án không đổi hạng ở câu nào (các thay đổi nằm ở hạng 4 đến 5). **Không phân biệt được**: Profiler chỉ điền domain cho 13/40 câu (đúng cả 13), nên có tối đa 13 câu bị ảnh hưởng. Cộng điểm không tệ hơn lọc cứng (đúng quy tắc) nhưng cũng không hơn không dùng. Không đổi `retrieval.w3` (giữ 0.0). Cần xem lại trên bộ thật (8 domain, 50 câu mỗi domain), nơi domain sai có thể làm lọc cứng chặn mất chunk đúng.

## Cấu hình đề xuất sau local (chưa phải kết luận cuối)

`end_mode: stored`, `neighbor_window: 1`, `w3: 0.0`, `t_unknown: null` (tùy chọn 0.3 nếu muốn thử nhánh chunk không mốc), `decay_lambda: 0.5`, `w1/w2: 0.7/0.3` (chưa quét: đợt 6). Cần xử lý trước đợt 6: 5 câu chunk đáp án bị lọc cứng chặn (đợt 2), và `hybrid` kém `dense` (đợt 1).

## Cách tái hiện

Lệnh từng cấu hình: [`03`](03_TEST_ROUNDS.md). Mỗi thư mục `output/<ts>/` có `metrics.json` (kèm `config`) và `predictions.jsonl`. Các lần chạy dùng `$E = output/20261019_222626`, `$P = output/20261019_222137/profiler.jsonl`.
