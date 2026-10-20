# Kế hoạch các đợt test

Mỗi đợt giữ cấu hình tốt nhất của đợt trước làm nền, chỉ đổi một nhóm thứ. Mọi đợt chạy trên **cùng một lần ingestion** để so công bằng; đổi prompt thì chạy lại ingestion và ghi vào [`../decisions/03_PROMPT_CHANGELOG.md`](../decisions/03_PROMPT_CHANGELOG.md). Cách chạy từng script: [`../instruction/01_RUN_PIPELINE.md`](../instruction/01_RUN_PIPELINE.md).

## Tổng quan

| Đợt | Hỏi gì | Biến đổi | Trạng thái |
|---|---|---|---|
| 0 | Pipeline chạy thông, không rò rỉ? | 5 cấu hình ban đầu | Đã chạy lại trên kho mới, xem [`04`](04_TEST_RESULTS.md) |
| 1 | Hệ có hơn plain RAG không, mỗi thành phần đóng góp bao nhiêu? | dense, BM25, hybrid, + lọc thời gian, + điểm thời gian | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 1b | Bỏ hoặc giảm BM25 có tốt hơn không? | `--sparse-weight` 1 / 0.5 / 0.25 / 0 | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 1c | Các thành phần còn lại có giữ nguyên tác dụng trên nền dense không? | Tổ hợp `--sparse-weight 0` với `--end-mode`, `--neighbors`, `--t-unknown`, domain | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 2 | Lỗi nằm ở bước nào? | Không đổi cấu hình; đọc số đo từng bước | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 3 | Cách chấm `end` nào tốt nhất? | `end_mode` A / B / C | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 3b | Mở rộng chunk liền kề cứu được bao nhiêu, tốn bao nhiêu? | `--neighbors` 0 / 1 / 2 | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 3c | Câu cần 2 chunk trở lên có bị đánh giá cao không? | Chỉ số `multi_*` | Đã chạy; bộ local chỉ có 1/40 câu, chưa có ý nghĩa |
| 3d | Tách `ongoing`/`unknown`: chỉ `unknown` giảm dần có tốt hơn không? | `--end-mode unknown_decay --open-decay d` (cạnh `stored`/`open`/`decay`) | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 4 | Có nên giữ chunk không mốc, `T_unknown` bao nhiêu? | `--t-unknown` 0.0 đến 0.7 trên nhiều nền | Đã chạy (đợt 4 và 4b), xem [`04`](04_TEST_RESULTS.md) |
| 5 | Domain cộng điểm có không tệ hơn lọc cứng? | `--facets`, `--w3` | Đã chạy, xem [`04`](04_TEST_RESULTS.md) |
| 6 | Tham số tốt nhất (`λ`, `W1/W2`)? | Quét trên `D/train` | **Chưa code**, để sau |
| 7 | Số đưa vào luận văn | Cấu hình đã chọn, trên bộ thật | Đã chạy lại **toàn bộ 142 kịch bản đợt 0 đến 5** trên bộ thật (400 câu), xem [`05`](05_REAL_RESULTS.md); còn chốt cấu hình sau đợt 6 |

## Chuẩn bị chung (một lần)

1. 9router chạy với combo `basic-gemini-3.5-flash-lite` (một model Gemini; lỗi thì code tự chờ 1 đến 32 giây rồi dừng, chạy lại đúng lệnh cũ).
2. Nạp kho: `python scripts/ingest.py --recreate --keep-undated`. Gọi LLM thật cho 37 trang (cache gần như trống); lần sau đọc từ cache. Ghi lại thư mục `output/<ts>/` của lần nạp: gọi nó là `$E`.
3. Profiler đã có sẵn ở `output/20261019_115213/profiler.jsonl` (gọi là `$P`). Chỉ chạy lại `scripts/profile_eval.py` nếu muốn Profiler chạy bằng combo mới.
4. Kho có chunk không mốc nhưng `t_unknown` mặc định `null`, nên chúng không bao giờ được trả về ở đợt 0 đến 3 và các đợt này vẫn so được với lần 4.

Mỗi lệnh `evaluate.py` ghi `output/<ts>/metrics.json` và `predictions.jsonl`; ghi tên cấu hình và `<ts>` vào bảng kết quả của `eval/04_...` (tạo khi chạy đợt đầu).

## Đợt 0. Chạy thông

```
python scripts/evaluate.py --mode oracle --profiler $P --extractions $E/extractions.jsonl
python scripts/evaluate.py --mode oracle --no-temporal ...
python scripts/evaluate.py --mode e2e    --profiler $P --extractions $E/extractions.jsonl
python scripts/evaluate.py --mode e2e    --no-temporal ...
python scripts/evaluate.py --mode e2e    --facets domain ...
```

Đọc: `leakage_rate` và `invalidated_rate` phải bằng 0 ở mọi cấu hình. Khác 0 là lỗi cần sửa trước khi làm tiếp.

## Đợt 1. Baseline (thang bậc)

| Bậc | Lệnh (thêm `--mode e2e --profiler $P --extractions $E/extractions.jsonl`) |
|---|---|
| a. dense | `--method dense` |
| b. BM25 | `--method bm25` |
| c. hybrid | `--method hybrid` |
| d. hybrid + lọc thời gian | `--no-temporal` |
| e. + điểm thời gian (Cơ chế 1) | (mặc định) |

Đọc: `hit@1/3/5`, `mrr`, `leakage_rate`. Baseline không lọc nên `leakage_rate` > 0 là bình thường và là điều cần chỉ ra. Phân tích: c so d cho thấy lọc cứng đóng góp bao nhiêu; d so e cho thấy điểm thời gian đóng góp bao nhiêu; a hoặc c so e là so với plain RAG. Chênh lệch dưới khoảng 2 câu thì ghi "chưa kết luận" (xem lưu ý cuối).

## Đợt 1b. Bỏ hoặc giảm BM25

Phát hiện ở đợt 1: dense thuần hơn hybrid thuần, nên BM25 có thể đang kéo Cơ chế 1 xuống. Lệnh: như bậc e thêm `--sparse-weight X` với `X` = 1 (RRF thường), 0.5, 0.25, 0 (bỏ BM25; chỉ dense). Thêm `X = 0` với `--no-temporal` để tách phần đóng góp của điểm thời gian trên nền dense.

Đọc: `mrr`, `hit@k`, `mrr_pre` (xếp theo điểm ngữ nghĩa, trước điểm thời gian), `temporal_helped/hurt`. Quy tắc chọn: `X` có `mrr` cao nhất; hòa trong khoảng 1 câu thì chọn `X` nhỏ hơn (đơn giản hơn). Kết quả quyết định nền cho các đợt sau.

## Đợt 1c. Kết hợp trên nền đã chọn

Các đợt 3, 3b, 4, 5 đã chạy trên nền hybrid (`X = 1`). Nếu đợt 1b đổi nền thì chạy lại các thành phần chính trên nền mới (`--sparse-weight 0`) và thử vài tổ hợp: `--end-mode open|decay`, `--neighbors 1`, `--t-unknown 0.3|0.5|0.7`, `--facets boost --w3 0.1`. Đọc như các đợt gốc. Lưu ý chọn lọc: càng thử nhiều tổ hợp trên cùng 40 câu thì cấu hình đứng đầu càng bị ước lượng cao; chỉ coi là cận trên và xác nhận ở đợt 7.

## Đợt 2. Chẩn đoán từng bước

Không cần lệnh riêng: đọc trong `metrics.json` của bậc e (và các bậc khác).

| Số | Nếu thấp hoặc bất thường thì lỗi ở |
|---|---|
| `t_req_abs_error_years_mean`, `t_req_in_label_range` | Profiler trích sai `t_req` |
| `domain_in_gold_chunk` so `domain_given` | Profiler gán domain không khớp nhãn chunk |
| `cand_recall_dense`, `cand_recall_sparse`, `cand_recall_fused` | Chunk đúng không lọt top-N: embedding, BM25 hoặc `top_n` |
| `gold_blocked_by_filter` | Lọc cứng chặn mất chunk đúng: `t_req` sớm hơn `start_time` của chunk, hoặc `start` LLM gán sai |
| `hit@k_pre`, `mrr_pre` so `hit@k`, `mrr` | Điểm thời gian giúp hay hại |
| `temporal_helped` / `temporal_hurt` | Số câu chunk đúng lên hạng / xuống hạng nhờ điểm thời gian |

Kết quả của đợt này quyết định đáng sửa gì trước (ví dụ `cand_recall_fused` thấp thì sửa truy xuất ứng viên, không phải điểm thời gian).

## Đợt 3. Cách chấm `end`

Lệnh: như bậc e, thêm `--end-mode stored` (C, mặc định) / `open` (A) / `decay --open-decay 0.05|0.1|0.2` (B). Cần kho có `end_status` (đã có sau bước chuẩn bị).

Đọc: `mrr`, `hit@1`, `temporal_helped/hurt`. Quy tắc chọn: giữ cách có `mrr` cao nhất; hòa (trong khoảng 1 câu) thì chọn `stored` vì đơn giản nhất. Ghi lại cấu hình thắng, dùng làm nền cho các đợt sau.

### 3b. Chunk liền kề

Lệnh: nền của đợt 3 thêm `--neighbors 0` / `1` / `2`.

Đọc: `hit@5` so `ctx_hit`, `recall@5` so `ctx_recall`, `rescued_by_neighbors`, `ctx_size_mean`. Chi phí ngữ cảnh là `ctx_size_mean` (5 chunk, tối đa 5·(1+2·window)). Chọn `window` nhỏ nhất mà `ctx_hit` ngừng tăng đáng kể.

### 3c. Câu cần nhiều chunk

Không cần lệnh: đọc `n_multi_gold`, `multi_all_hit@k`, `multi_recall@k`, `ctx_multi_all_hit` trong cùng các lần chạy. Bộ local chỉ có 1/40 câu loại này nên đợt này chủ yếu có nghĩa ở bộ thật; ở local chỉ kiểm tra code chạy đúng.

### 3d. Tách `ongoing` và `unknown`

Lệnh: nền đợt 3 (dense) thêm `--end-mode unknown_decay --open-decay d` với `d` = 0.05, 0.1, 0.2, 0.3, mỗi `d` quét `t_unknown` tắt, 0.0 đến 0.7. Ba cách cũ (`stored`, `open`, `decay`) giữ nguyên để so. Đọc: `mrr`, `hit@5`; hạng chunk đáp án của 5 câu lỗi end ([`decisions/06`](../decisions/06_END_UNKNOWN_REMEDIES.md)); so từng câu với `stored` và `decay`. Quy tắc: nếu `mrr` tăng và không câu nào mới hỏng quá 1 thì giữ; không thì ghi "không có lợi" và tính đề xuất 2 của `decisions/06` (LLM ghi loại sự việc).

## Đợt 4. Chunk không mốc

Lệnh: nền của đợt 3 thêm `--t-unknown X`, so với không bật. Dãy `X` = 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7 (0.0 = cận dưới: chunk không mốc chỉ còn điểm ngữ nghĩa). Không thử trên 0.7: `T_unknown` gần 1.0 làm chunk không mốc ngang chunk đúng thời điểm (TH1 = 1.0), trái nguyên tắc, và xu hướng đã giảm khi tăng. **Mọi họ cấu hình đều quét cả dãy** (nền hybrid, dense, BM25 0.25, BM25 0.5; kèm `--end-mode open`, `decay 0.05/0.1/0.2`; riêng `--neighbors 1` chỉ quét trên nền dense vì không đổi thứ hạng), để vẽ đường nhạy cảm; trình bày như đường, không chọn "giá trị tối ưu".

Đọc: `mrr` và `hit@5` (không được tụt so với không bật), `undated_in_results_rate` (chunk không mốc chiếm bao nhiêu kết quả), và chunk đáp án không mốc được cứu hay không (bộ local có 3: `Pskov#0`, `Central_European_University#62`, `Rui_Vitória#2`; xem `predictions.jsonl`). Quy tắc: giữ nhánh này nếu cứu được chunk đáp án mà `mrr` trên các câu có mốc không giảm quá 1 câu; chọn `T_unknown` có `mrr` cao nhất. Nếu không thì tắt và ghi rõ trong `decisions/04`.

## Đợt 5. Domain

| Cấu hình | Lệnh (nền + `--mode e2e`) |
|---|---|
| Không dùng domain | (mặc định) |
| Lọc cứng | `--facets domain` |
| Cộng điểm | `--facets boost --w3 0.05` / `0.1` / `0.2` |

Đọc: `mrr`, `hit@k`, `domain_in_gold_chunk`. Lưu ý Profiler chỉ điền domain cho khoảng 14/40 câu nên `W3` chỉ ảnh hưởng các câu đó; chênh lệch ở local có thể không phân biệt được. Quy tắc: cộng điểm không được kém lọc cứng; chọn `W3` có `mrr` cao nhất, hòa thì `W3` nhỏ hơn. Chọn xong thì sửa `retrieval.w3` trong config.

## Đợt 6 và 7 (để sau)

- Đợt 6: quét `λ`, `W1/W2` (cùng `T_unknown`, `W3`, `end_mode` đã chọn) trên mẫu `D/train`. Cần code lấy mẫu train và dựng bộ con từ train (chưa có).
- Đợt 7: cấu hình đã chọn và baseline (đợt 1) trên bộ thật (8 domain × 50 câu, `dataset/eval/real_subset.json`, **đã dựng**; mượn 35 câu từ `D/train`, xem [`process/06`](../process/06_EVAL_SUBSET.md)), kèm Hit@k, MRR, theo lát thời gian, rò rỉ, chi phí token. Cần Profiler và ingestion cho bộ này (chưa chạy): `profile_eval.py --subset real`, `ingest.py --subset real --recreate --keep-undated` (ghi vào collection `<config>_real`), rồi `evaluate.py --subset real ...`.

## Lưu ý về độ tin cậy

Bộ local có 37 câu có thể trúng nên sai số ±15 điểm phần trăm; một câu đổi chiều là 2.7 điểm. Vì vậy:
- Kết quả đợt 0 đến 5 ở local chỉ cho **hướng** và để bắt lỗi (rò rỉ, chunk bị chặn, câu hỏi Profiler sai), chưa đủ để chốt tham số cuối cùng.
- Nên so từng câu (câu nào đổi từ trượt sang trúng và ngược lại) thay vì chỉ so tỉ lệ; `predictions.jsonl` có đủ dữ liệu, nhưng chưa có script so cặp (chưa code).
- Tham số chốt dựa trên đợt 6 (`D/train`) và đợt 7 (bộ thật), không dựa trên bộ local.
