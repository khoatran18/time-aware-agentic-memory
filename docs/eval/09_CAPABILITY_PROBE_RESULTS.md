# Kết quả bộ kiểm khả năng (thời gian tương đối, mức ngày, không nêu mốc, `end_time` mở) và chọn lại cấu hình

**Ngày:** 2026-11-03. Cách làm từng bước ở [`../process/09_CAPABILITY_PROBE_AND_RESELECTION.md`](../process/09_CAPABILITY_PROBE_AND_RESELECTION.md); lý do làm ở [`../decisions/11_EVOLUTION_FALSEHOOD_ALIGNMENT.md`](../decisions/11_EVOLUTION_FALSEHOOD_ALIGNMENT.md) mục 1.3. Mọi số trong file này là **mrr ghép cặp theo câu ± một sai số chuẩn** nếu không ghi khác; chạy bằng CPU, không gọi LLM ở bước truy xuất.

## 0. Tóm tắt

1. Bộ `real` gần như không có bốn loại câu: **mức ngày, thời gian tương đối, không nêu mốc, `end_time` còn mở**. Mình viết thêm bốn bộ nhỏ (mỗi bộ 100 câu, cùng phân bố) để đo chúng.
2. **Cơ chế thời gian vẫn thắng** ở các bộ mới: rò rỉ 0 ở mọi cấu hình Temporal (Plain RAG rò rỉ khoảng một nửa số câu), và hơn Plain RAG cùng cross-encoder.
3. **Điểm yếu của cấu hình chính:** `end_mode = decay` phạt nặng chunk "đang còn hiệu lực" bắt đầu từ lâu, nên với câu "hiện tại / không nêu mốc" chunk đúng bị đẩy xuống. Hiệu ứng gần như không thấy ở `real` (chênh dưới 0.01) nhưng rõ ở bộ mới (thấp hơn tới 0.25 `mrr` ở nền không cross-encoder, 0.05 đến 0.09 ở nền bge).
4. Chạy lại **1,141 cấu hình** trên bộ tune mới: cách chấm `unknown_decay` (chỉ chunk không rõ trạng thái bị giảm điểm, chunk `ongoing` giữ 1.0) hơn `decay` ở 195/197 cặp tham số giống hệt nhau và **không kém** ở bộ cũ.
5. **Chưa chốt** cấu hình chính mới (A hay X, mục 6) và **chưa chạy `test_clean` lần hai**.

## 1. Các bộ câu hỏi

Mỗi bộ có 100 câu: 31 mức ngày (`day`), 34 thời gian tương đối (`relative`), 18 không nêu mốc (`no_anchor`), 17 `end_time` mở (`open_end`). Viết tay từ chính văn bản các chunk, `t_now` cố định `2026-11-03` (định dạng năm-tháng-ngày) cho câu cần ngày hiện tại.

| Bộ | File | Trang nguồn | Chunk gold | Kho | Độ khớp chữ\* | Profiler đúng ngày |
|---|---|---|---:|---|---:|---:|
| Kiểm bản 1 | `dataset/eval/capability_probe/questions.jsonl` | 37 trang `test_clean` | 42 | `tam_chunks_dev_test_clean` | 0.45 | 92/100 |
| Kiểm bản 2 (viết lại bản 1) | `.../questions_v2.jsonl` | như bản 1 | 42 | như bản 1 | 0.20 | 90/100 |
| Tune mới | `.../tune_questions.jsonl`, `capability_probe_tune_subset.json` | 46 trang `tune` | 52 | `tam_chunks_dev_tune` | 0.17 | 83/100 |
| Valid mới | `.../valid_questions.jsonl`, `capability_probe_valid_subset.json` | 55 trang `valid` | 56 | `tam_chunks_dev_valid` | 0.18 | 82/100 |

\* Tỉ lệ từ khóa (bỏ tên thực thể và con số) của câu hỏi có trong chunk gold; bộ `test_clean` cũ là **0.10**. Bản 1 quá dễ (Plain RAG dense đạt hit@1 0.53 so với 0.16 ở bộ cũ) nên được viết lại thành bản 2; hai bản chung chunk gold nên không độc lập. Các bộ tune mới, valid mới không trùng trang với nhau, với `test_clean` hay với bộ kiểm.

**Profiler:** mọi câu sai ngày đều thuộc loại "N năm trước", Profiler ra đúng **năm** nhưng sai ngày trong năm (ví dụ `2006-01-01` thay vì `2006-11-03`). Các loại còn lại đúng: `day` 31/31, `no_anchor` 18/18 hoặc 17/18, `open_end` 17/17, `relative` kiểu "hiện tại" 100%.

## 2. 28 cấu hình của `test_clean` trên bộ kiểm (bản 1, bản 2)

Danh sách cấu hình đã khai trước ở `decisions/11` mục 1.3 (nhóm A Plain RAG, B Temporal + cross-encoder, C xuất phát, D ablation), chạy một lần, báo tất cả.

| Cấu hình | Bản 1: hit@1 / hit@5 / mrr / rò rỉ | Bản 2: hit@1 / hit@5 / mrr / rò rỉ |
|---|---|---|
| Plain RAG dense | 0.53 / 0.76 / 0.642 / 0.51 | 0.43 / 0.79 / 0.587 / 0.51 |
| Plain RAG dense + bge | 0.61 / 0.99 / 0.753 / 0.49 | 0.65 / 0.94 / 0.772 / 0.51 |
| Temporal không cross-encoder | 0.82 / 0.96 / 0.871 / 0 | 0.69 / 0.94 / 0.794 / 0 |
| **Temporal + bge (cấu hình chính)** | 0.76 / 1.00 / 0.869 / 0 | 0.74 / 0.99 / 0.851 / 0 |

Các cặp đã khai (Δ`mrr` của cấu hình chính so với cấu hình ghi bên trái):

| So với | Bản 1 | Bản 2 |
|---|---|---|
| Plain dense + bge | **+0.115 ± 0.026** | **+0.080 ± 0.025** |
| Temporal không cross-encoder | −0.002 ± 0.026 | +0.058 ± 0.032 |
| bge bỏ điểm thời gian | **+0.083 ± 0.025** | **+0.066 ± 0.024** |
| bge bỏ decay khi fallback | **+0.202 ± 0.027** | **+0.200 ± 0.029** |
| bge bỏ `end_mode` (`stored`) | **−0.055 ± 0.017** | **−0.069 ± 0.022** |
| bge `point` so với `range` | +0.008 ± 0.006 | +0.010 ± 0.007 |

Cấu hình chính **thua** bản bỏ `end_mode` ở cả hai bản, ở nhóm `no_anchor` (hit@1 14/18 so với 18/18 ở bản 2) và `open_end` (11/17 so với 17/17). Trên `test_clean` cũ hai cấu hình này ngang nhau (Δ +0.002 ± 0.006), và gộp 500 câu là −0.009 ± 0.006 (chưa kết luận).

## 3. Vì sao `end_mode = decay` thua

`decay` (`scoring.py`): chunk `ongoing` hoặc `unknown` bị nhân điểm thời gian với `exp(−open_decay · số năm từ start tới t_req)`. Với câu "hiện tại" thì `t_req` là 2026 còn chunk đúng (ví dụ "MIT từ 1994") đã bắt đầu từ lâu, nên hệ số chỉ còn 0.04 (33 năm) hoặc gần 0 khi `start` là ngày sinh (84 năm). Chunk khác cùng trang đứng lên trên; hit@5 giữ nguyên vì chỉ đổi thứ tự trong trang. Ở bản 1 có 11 câu thua trên 6 chunk, bản 2 có 14 câu trên 9 chunk, **cả 11 chunk đều `ongoing`** với `exp(−0.1·Δ)` từ 0.000 đến 0.22.

`decay` được đề xuất ở [`decisions/02`](../decisions/02_END_TIME_ONGOING.md) hướng (a) để chunk `ongoing` quá rộng không thắng mọi chunk. Lúc đo trên bộ local nó không hơn `stored`; nó vào cấu hình chính sau tune. `unknown_decay` (xem `decisions/06`) chỉ giảm điểm chunk `unknown`, giữ `ongoing` ở 1.0.

## 4. Chạy 1,141 cấu hình trên bộ tune mới

Tune cũ đã chạy 888 cấu hình cũ + 240 cấu hình quét = 1,128. Cộng 28 cấu hình `test_clean` (13 cấu hình ablation chưa có ở tune cũ) và bỏ trùng thì hợp là **1,141**, tất cả chạy trên tune mới (0 lỗi).

**Thứ hạng cấu hình có đổi:** Spearman (tương quan thứ hạng) giữa `mrr` tune cũ và tune mới **0.66** (1,125 cấu hình), giữa valid cũ và tune mới 0.68 (69 cấu hình), giữa tune cũ và valid cũ 0.87. Họ cross-encoder không đổi (bge đứng đầu trên bộ gộp, rồi L6, L12; Plain RAG xa nhất); chỗ đổi là các giá trị tham số, nhất là `end_mode`.

**Các cặp cấu hình giống hệt nhau, chỉ khác `end_mode` / `open_decay`** (Δ`mrr` trung bình, số cặp A hơn B):

| A − B | Số cặp | Tune mới (100 câu) | Tune cũ (595 câu) |
|---|---:|---|---|
| `decay` − `stored` | 121 | **−0.248**, 0/121 | −0.004, 24/120 |
| `unknown_decay` − `decay` | 197 | **+0.256**, 195/197 | +0.010, 192/197 |
| `unknown_decay` − `stored` | 215 | −0.002, 25/215 | +0.004, 167/212 |
| `open` − `stored` | 98 | −0.097, 0/98 | −0.018, 0/98 |
| `open` − `decay` | 114 | +0.148, 114/114 | −0.014, 4/114 |

Hiệu ứng lớn nhất ở nền không cross-encoder (`decay` − `stored` −0.254, 0/117); với bge nhỏ hơn (−0.066, chỉ 4 cặp). "Số cặp" là số phép so sánh, một bộ tham số nền có thể ghép với nhiều giá trị `open_decay`.

## 5. Valid (120 cấu hình trên valid mới 100 câu và valid cũ 399 câu)

120 = danh sách ngắn theo tune gộp (top 20 + top 5 mỗi họ, 80 cấu hình) ∪ 56 cấu hình đã chạy valid cũ ∪ 15 cấu hình quét ∪ 28 cấu hình test ∪ cấu hình chính ∪ ứng viên X.

- **Chọn họ (quy tắc cũ):** Temporal + bge-reranker-v2-m3 vẫn cao nhất (0.640 trên 499 câu), L12 kém 0.011 ± 0.011, không đổi họ.
- **X (`2d10bbb571`, bge + `unknown_decay` + bộ tham số chọn lại từ tune gộp) so với cấu hình chính:** valid cũ **−0.003 ± 0.009**, valid mới **+0.051 ± 0.027** (1.9 sai số chuẩn), gộp 499: +0.008 ± 0.009. X đứng hạng 1/120 trên valid gộp, cấu hình chính hạng 6.
- Chỉ có **1 cặp** `unknown_decay` − `decay` trong 120 cấu hình đó (+0.002 ở valid cũ, +0.047 ở valid mới), nên valid xác nhận "không hại" nhiều hơn là xác nhận riêng hiệu ứng `end_mode`.

## 6. Chọn cấu hình chính mới: A, B hay X

X khác cấu hình chính ở nhiều tham số (`rerank_mode` `replace` thay vì `mix`, `decay_from = end`, `rerank_top` 20 và `top_n` 50 thay vì 30 và 100, `w2` 0.3, `decay_lambda` 0.25, `open_decay` 0.05, `t_unknown` 0.2), nên "X so với chính" lẫn nhiều thay đổi. Để tách riêng `end_mode`, tạo hai cấu hình giữ nguyên mọi tham số của cấu hình chính: **A** (`end_mode = unknown_decay`, `open_decay` 0.1) và **B** (như A, `open_decay` 0.05). Kết quả (Δ`mrr` so với cấu hình chính cũ):

| Bộ | Chính (`decay`) mrr | A | B | X |
|---|---:|---|---|---|
| tune cũ (595) | 0.628 | −0.007 ± 0.006 | −0.009 ± 0.006 | −0.001 ± 0.007 |
| tune mới (100) | 0.803 | **+0.093 ± 0.021** | +0.093 ± 0.021 | **+0.073 ± 0.022** |
| valid cũ (399) | 0.578 | **−0.014 ± 0.007** | −0.011 ± 0.008 | −0.003 ± 0.009 |
| valid mới (100) | 0.847 | **+0.065 ± 0.026** | +0.065 ± 0.026 | +0.051 ± 0.027 |
| kiểm bản 1 (100) | 0.869 | +0.055 ± 0.017 | +0.055 ± 0.017 | +0.028 ± 0.020 |
| kiểm bản 2 (100) | 0.851 | +0.069 ± 0.022 | +0.069 ± 0.022 | +0.063 ± 0.021 |

`open_decay` (A so với B) gần như không có tác dụng (khác 0.0017 ± 0.0024), đúng với mã: với `unknown_decay` nó chỉ áp dụng cho chunk `unknown`.

**Quy tắc chọn khai trước khi xem kết quả:** (1) chọn theo `mrr` trên tune gộp (595 + 100 = 695 câu) giữa X, A, B và cấu hình cũ; (2) valid chỉ để phủ quyết: loại nếu thua cấu hình cũ từ 2 sai số chuẩn ở valid cũ, hoặc thua ở valid mới; (3) hòa (chênh dưới 1 sai số chuẩn) thì chọn cấu hình ít thay đổi nhất; (4) cấu hình thắng chạy `test_clean` lần hai, ghi rõ.

Áp dụng: tune gộp X 0.6626, A 0.6603, B 0.6586, chính 0.653 (X − A = +0.0023 ± 0.0055, hòa); không cấu hình nào bị phủ quyết (A suýt bị loại: −1.95 sai số chuẩn ở valid cũ, tức thua chính ở 44 câu, hơn ở 26 câu); hòa nên chọn ít thay đổi nhất, tức **A**. Mặt khác X cân bằng hơn (đứng đầu tune gộp lẫn valid gộp, gần như không mất ở bộ cũ). Hai chọn lựa này **chưa được quyết**.

Số liệu đầy đủ của bốn cấu hình (`hit@1`, `hit@5`, `mrr`, `ans_valid@5`; rò rỉ đều 0):

| Cấu hình | Tune gộp 695: hit@1 / hit@5 / mrr | Valid gộp 499: hit@1 / hit@5 / mrr |
|---|---|---|
| Chính (`decay`) | 0.496 / 0.876 / 0.653 | 0.469 / 0.830 / 0.632 |
| A | 0.514 / 0.866 / 0.660 | 0.471 / 0.842 / 0.634 |
| B | 0.509 / 0.862 / 0.659 | 0.475 / 0.842 / 0.636 |
| X | 0.515 / 0.868 / **0.663** | 0.489 / 0.830 / **0.640** |

## 7. Chỉ số dùng để chọn

- **`mrr`** là chỉ số chọn vì liên tục, ít nhiễu hơn `hit@1`: độ lệch chuẩn theo câu 0.371 so với 0.499; thứ hạng cấu hình lặp lại tốt giữa hai nửa ngẫu nhiên của tune (Spearman 0.95 so với 0.85) và giữa tune với valid (0.94 so với 0.87). Với `hit@5` thì ngang (0.94 giữa tune và valid).
- **`mrr` bị `hit@1` chi phối:** với cấu hình chính trên tune cũ, 74% giá trị `mrr` đến từ chunk gold ở hạng 1, 24.5% từ hạng 2 đến 5, 1.4% từ hạng 6 đến 15, 0 từ chunk không có trong top-15. Tương quan thứ hạng giữa các chỉ số trên 1,125 cấu hình: `mrr` với `hit@1` **0.95**, `mrr` với `hit@5` **0.85**, `hit@1` với `hit@5` **0.71**. Nên chọn theo `mrr` và theo `hit@5` có thể cho kết luận khác (ví dụ A hơn chính ở `hit@1` +0.018 nhưng kém ở `hit@5` −0.010 trên tune gộp).
- **`hit@5` bão hòa ở bộ viết tay** (0.99 đến 1.00 ở nhiều cấu hình, ví dụ valid mới: chính 0.99, A 1.00, X 1.00 trong khi `mrr` 0.847, 0.912, 0.898), nên không phân biệt được cấu hình; ở `real` `hit@5` khoảng 0.83 đến 0.88 vẫn dùng được.
- **`top_k = 15` là đủ:** hạng 6 đến 15 chỉ đóng góp 1.4% của `mrr`, nên hạng sau 15 không có ý nghĩa cho việc chọn cấu hình. `mrr` chỉ tính chunk gold trong danh sách trả về; ngoài top-15 thì bằng 0, không phải `1/20`.
- `leakage_rate = 0` là cổng bắt buộc, không đánh đổi với chỉ số khác. `ans_valid@5` là cận trên (có dương tính giả do trùng chữ), `mrr` và `hit@k` theo một chunk gold là cận dưới; EM/F1 đầu-cuối là kiểm cuối nhưng chưa chạy cho cấu hình mới.

## 8. Hạn chế

- Bốn bộ chỉ 100 câu, đến từ 42 đến 56 chunk gold; các câu cùng sự kiện không độc lập (Niigata, danh sách chủ tịch... dùng chung chunk cho 4 đến 8 câu). Nhãn do tác giả viết nên có thể thiên theo cách hệ đang làm; chưa có người thứ hai đọc.
- Bản 2 được viết lại **sau khi** thấy kết quả bản 1; bản 1 và bản 2 không độc lập.
- Nhóm `day` vẫn khớp chữ cao hơn (0.32 đến 0.45) vì tên tháng không thể bỏ; chỉ 6/31 câu `day` của bộ kiểm thật sự thử độ mịn ngày (có chunk "đối thủ" cách ngày hỏi trong một tháng); 20/31 câu một bộ lọc theo năm cũng đủ.
- Chọn lại cấu hình sau khi thêm loại câu mới là **vòng chọn thứ hai**, nhiều bậc tự do hơn quy trình ban đầu; phải nói rõ khi báo cáo.
- Số tune gộp trộn hai phân phối theo tỉ lệ 6:1 (595 câu `real` với 100 câu viết tay), nên cấu hình tối ưu cho loại câu cũ gần như quyết định; nên báo từng bộ riêng.
- "N năm trước" cho đúng năm nhưng sai ngày (các bộ: 6 đến 8/16, 1/18, 2/20); ảnh hưởng tới truy xuất chưa tách riêng.

## 9. Việc còn lại

1. **Quyết A hay X** (hoặc giữ cấu hình cũ và ghi `end_mode = decay` là hạn chế).
2. Chạy cấu hình đã chọn trên **`test_clean` lần hai** và bộ kiểm; ghi rõ trong báo cáo là vòng hai, sau khi thấy bộ kiểm khả năng. Chưa chạy.
3. Sau khi chốt: cập nhật `configs/*.yaml`, `eval/07` mục 5 và `decisions/11` mục 1.3.
4. Tùy chọn: EM/F1 đầu-cuối cho 2 đến 3 cấu hình đứng đầu; thêm mẫu "N năm trước" ở mức ngày để thử Profiler.
