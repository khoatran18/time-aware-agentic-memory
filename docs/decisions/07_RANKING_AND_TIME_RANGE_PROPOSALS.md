# Quyết định 07: đề xuất nâng thứ hạng sau khi chạy bộ thật (khoảng thời gian của câu hỏi, cách phạt `end`, reranker)

**Ngày:** 2026-10-20 (cập nhật 2026-10-21). **Trạng thái:** đề xuất; trạng thái code, test và đo của từng đề xuất ở hai bảng bên dưới. Các con số "kỳ vọng" trong phần mô tả đề xuất là suy luận, trừ chỗ có ghi "đã đo".

## Trạng thái triển khai (cập nhật 2026-10-20)

| # | Đề xuất | Code | Đã đo | Ghi chú |
|---|---|---|---|---|
| 1 | Khoảng `[qs, qe]` + lọc/chấm chồng lấn | **Đã code phần Profiler** (`query/range_profiler.py`, `query/time_range.py`, prompt `time_extractor_v2.md`, `ProfiledQuery.t_end`, `profile_eval.py --ranges`, 11 test). **Đã code phần retriever dạng tùy chọn** (`retrieval.time_mode: point | range`, `retrieval.overlap: binary | coverage`; `scoring.temporal_score_range`, `filters.to_vector_filter(use_range=...)`, cờ `--time-mode`/`--overlap` của `evaluate.py`; mặc định `point` giữ nguyên hành vi cũ; 8 test mới). Lọc `start <= qe`, điểm chồng lấn (hoặc độ phủ), điểm lùi từ `start` hoặc `end` | **Đã đo** lưới 140 kịch bản mỗi bộ (`eval/05` mục 6.9): `range` so với `point` +0.002 ± 0.014 (giảm số câu bị lọc cứng 78 xuống 68), `coverage` kém `binary`; không vượt sai số. **Profiler khoảng đã chạy xong 400/400 câu** (Gemini 3.1, 0 lỗi; `output/20261020_173521/profiler.jsonl`, `prompt_version` v2); retriever chưa dùng khoảng | Đã đọc tay 37 câu bị lọc: cứu được tối đa 6 câu. `Profiler` cũ giữ nguyên, không bị thay |
| 2 | Dung sai cố định của lọc | **Bỏ** (2026-10-21) | — | — | Bỏ: không có căn cứ chung (chênh `start` − `t_req` ở 37 câu bị lọc cứng có trung vị 4 năm, tùy ý, xem `eval/05` mục 6.14); `range` (đề xuất 1) làm theo độ mịn của câu hỏi và chỉ +0.002 ± 0.014 |
| 3 | Phạt chunk hết hạn từ `end` (`decay_from`) | **Đã code**, dạng tùy chọn, mặc định `start` (`scoring.py`, `retriever.py`, `evaluate.py`, `config.*.yaml`, 3 test) | **Đã đo**: `mrr` +0.007 ở bộ thật (28/28 cặp tăng, nhỏ), +0.013 ở local | Chưa đổi mặc định |
| 4 | Reranker cross-encoder / LLM | **Chưa code** | Chưa | `fastembed` có sẵn `TextCrossEncoder`; đã thử tải `Xenova/ms-marco-MiniLM-L-6-v2` (13 giây, chấm 20 cặp ~0.01 giây). **Việc tiếp theo** |
| 5 | Chỉ số chuỗi đáp án và chỉ số hợp lệ về thời gian | **Đã code** (`evaluation/answer_match.py`, `metrics_temporal.py`, `retrieval_eval.py`, `summarize_runs.py`; 6 test). Metrics: `ans_hit@k`, `ans_valid_hit@k`; `hit@k` theo chunk id giữ nguyên | **Đã đo**: `results_{real,local}.csv` có cột `ans_hit@5`, `ans_valid_hit@5` (`eval/05` mục 6.10) | Khớp theo ranh giới từ (0.810 so với 0.812 ở khớp chuỗi con) |
| 6 | Quét `λ`, `W1/W2` trên D/train | **Chưa code** | Chưa | |
| 7 | Gom chunk cùng trang theo thời gian | **Đã code** dạng tùy chọn (`page_expand` none/time/page, `page_top`, `page_per`; `expansion.py`, `retriever.py`, cờ `--page-expand/--page-top/--page-per`, config dev/prod, chỉ số `ctx_size_p90/max`; 3 test) | **Đã đo** lưới 34 kịch bản mỗi bộ (`eval/05` mục 6.11): lọc thời gian **không tốt hơn** chunk liền kề; kém cả "cùng trang không lọc" (`ctx_hit` 0.719 so với 0.774 ở 3×5) | Kết quả âm; không đổi mặc định. Cần commit |
| 8 | Một chunk nhiều khoảng | **Chưa code** | Chưa | Thêm ở bản này, gắn với `decisions/06` đề xuất 3 Hoãn sang Cơ chế 2 (2026-10-21): đồ thị sự kiện cho mỗi sự việc một `[start, end]` riêng và có con trỏ `Chunk_ID`; làm đề xuất 8 ở VectorDB sẽ trùng việc; tinh chỉnh một thể khi làm Cơ chế 2 |
| 9 | Ingestion: phân biệt **sự kiện và trạng thái** ("chuyển tới X năm 1950" kéo dài tới khi có sự kiện thay thế, `end` không bằng `start`) | **Đã code**: `ingestion_time_v2.md`, `ingestion_time_v3.md`, `TimeExtractor(prompt_version=...)`, cờ `ingest.py --prompt-version` (mặc định `v1`; 1 test). Script chạy song song `local/scripts/warm_ingest_cache.py` nằm ngoài repo | **Đã đo** trên cả bộ thật (kho `tam_chunks_dev_real_v2`, `eval/05` mục 6.13): `ans_valid@5` +0.063 ± 0.042, `hit@5` +0.033 ± 0.036, `mrr` +0.016 ± 0.029 (chưa vượt sai số); 34 câu được thêm, 21 mất | Sai nhỏ: khoảng bị kéo dài và chunk mở đầu người còn sống thành `unknown`. Cần tập valid/test; chưa đổi mặc định |
| 10 | `min_validity`: coi chunk còn hợp lệ ít nhất `start + L` năm (làm mềm `end`) | **Chưa code** | Chưa | Không cần LLM; dự định quét L ∈ {1, 5, 10, ∞} trên tập local/valid; rủi ro dương tính giả |
| 11 | Kế thừa mốc cho chunk không mốc từ chunk có mốc gần nhất cùng mục | **Chưa code** | Chưa | 15/123 câu sai; mốc kế thừa phải đánh dấu là suy ra, điểm thấp hơn mốc thật Mở rộng (2026-10-21): suy luận cả `start`, `end` từ chunk liền kề, không chỉ chunk không mốc; xem bảng tóm tắt |
| 12 | Không mở rộng lọc cứng cho `start` > `t_req` | Không làm | — | Vi phạm bất biến không rò rỉ tương lai; chỉ cứu thêm ~14 câu lệch ≤ 2 năm. Ghi lại để khỏi đề xuất lại |

Đã code ngoài các đề xuất: `scripts/funnel_real.py` (phễu), `scripts/plot_results.py` (thêm `compare_*.svg`, `funnel.svg`), provider Google, `invoke_structured` chịu lỗi giới hạn tốc độ của Google.

### Tóm tắt trạng thái (cập nhật 2026-10-21): Code / Test / Đã đo

Bảng chi tiết ở trên; bảng này chỉ để nhìn nhanh. "Test" là test tự động (`pytest`); prompt thì không có test hành vi LLM, chỉ có test nạp file và lần chạy thật. "Đã đo" nghĩa là đã chạy bộ thật (`eval/05`) với kết quả ghi lại.

| # | Đề xuất | Code | Test | Đã đo | Kết quả một dòng |
|---|---|---|---|---|---|
| 1 | Khoảng `[qs, qe]` | Có (Profiler + retriever tùy chọn) | Có (19 test) | Có (kho v1 và v3, `eval/05` mục 6.15) | `range` so với `point` +0.002 ± 0.014 (v1); tốt nhất +0.003 ± 0.007 ở kho v3 (28 cấu hình): không hơn |
| 2 | Dung sai cố định của lọc | **Bỏ** (2026-10-21) | — | — | Bỏ: không có căn cứ chung (`start` − `t_req` ở 37 câu bị lọc cứng trung vị 4 năm, tùy ý, `eval/05` mục 6.14); `range` (đề xuất 1) làm theo độ mịn của câu hỏi, +0.002 ± 0.014 |
| 3 | Phạt từ `end` (`decay_from`) | Có | Có (3) | Có | +0.006 ± 0.008 |
| 4 | Cross-encoder rerank | **Có** (`rerank.py`, tùy chọn, mặc định tắt) | Có (cả Plain RAG và cache điểm) | **Có** (`eval/05` mục 6.18) | **Cải thiện lớn nhất**: bge-v2-m3 `mrr` 0.478 → 0.566 (+0.088 ± 0.015), `hit@1` 0.338 → 0.415; MiniLM-L12 +0.052 ± 0.012. Plain RAG + cùng cross-encoder cũng tăng, nên phần riêng của Cơ chế 1 là +0.09 đến +0.10 `mrr`, +0.14 đến +0.16 `ans_valid@5`, rò rỉ 0 (so với 66% đến 70%). `ans_valid@5` gần như không đổi (0.70 đến 0.72). Cận trên; chưa quét `w2`, `end_mode`, BM25 |
| 5 | Chỉ số `ans_hit`, `ans_valid_hit` | Có | Có (6) | Có | `ans_valid@5` làm chỉ số chẩn đoán |
| 6 | Quét `λ`, `W1/W2` | Chưa | Chưa | Chưa | Cần tập train/valid |
| 7 | Gom chunk cùng trang theo thời gian | Có (`page_expand`) | Có (3) | Có (mục 6.11) | **Kết quả âm**: lọc thời gian kém "cùng trang không lọc" và kém chunk liền kề |
| 8 | Một chunk nhiều khoảng | Chưa | Chưa | Chưa | Nạp lại kho; làm sau cùng Hoãn sang Cơ chế 2 (2026-10-21): đồ thị sự kiện cho mỗi sự việc một `[start, end]` riêng và có con trỏ `Chunk_ID`; làm đề xuất 8 ở VectorDB sẽ trùng việc; tinh chỉnh một thể khi làm Cơ chế 2 |
| 9 | Ingestion: sự kiện khác trạng thái (prompt v2, v3) | Có (`ingestion_time_v2/v3.md`, `--prompt-version`) | Có (1, chỉ nạp file) | Có (mục 6.13) | `ans_valid@5` +0.063 ± 0.042; `hit@5` +0.033 ± 0.036 và `mrr` +0.016 ± 0.029 chưa vượt sai số |
| 10 | `min_validity`: hiệu lực tối thiểu `start + L` | **Chưa** | **Chưa** | **Chưa** | Không cần LLM; nhắm nhóm chunk "hết hạn" (30 câu sai ở kho v3) Hạ ưu tiên (2026-10-21): L là tham số chọn từ dữ liệu và v3 đã sửa nhãn trạng thái tại gốc |
| 11 | Suy luận thời gian từ chunk liền kề khi chunk thiếu `start`, `end` hoặc chưa rõ trạng thái (không gọi LLM, bước hậu xử lý sau ingestion) | **Có** (`infer_time.py`, `scripts/infer_neighbor_time.py`, `time_inferred`, `inferred_factor`) | Có | **Có** (`eval/05` mục 6.16, 9 collection × 3 hệ số × 3 `end_mode`) | **Không bật**: suy `start` không đổi `hit@5`/`mrr`; suy `end` làm `ans_valid@5` +0.037 ± 0.010 nhưng `mrr` −0.008 ± 0.006. Quy tắc dự kiến ban đầu: Quy tắc dự kiến: `start` thiếu thì lấy mốc `end` (hoặc `start`) của chunk trước có mốc; `end` rỗng hoặc `unknown` thì lấy mốc `start` của chunk sau cùng mạch; `ongoing` không suy (giữ chính sách cần cụm nguyên văn). Mốc suy ra phải đánh dấu (`time_inferred`) và điểm thấp hơn mốc thật. Dựa trên tính chất trang tiểu sử/lịch sử viết theo thứ tự thời gian (xem `eval/05` mục 6.14); giả thuyết, chưa đo. Nhắm: chunk không mốc (4 câu sai ở v3), mốc lệch 1 đến 4 năm (10 câu) |
| 12 | Không nới lọc cứng `start` > `t_req` | Không làm | — | — | Quyết định không làm (vi phạm bất biến không rò rỉ tương lai) |
| 13 | Chặn `end` bị kéo dài quá mức bằng luật nguồn của `end` trong prompt (mốc tử trận, cuối trang không được làm `end` của chunk không nói tới) | **Chưa** | **Chưa** | **Chưa** | Từ v3: 8 câu mất vì khoảng quá dài (Erich Topp `end` 2005, No. 73 Sqn `end` 1969). Cần LLM (prompt v4 + nạp lại). **Đã rút phần tie-break theo `start` gần `t_req`** (2026-10-21): đó là heuristic phụ thuộc thời điểm hỏi, không phải tính chất chung của dữ liệu; chế độ `decay` cũng không tốt hơn `stored` (0.446 so với 0.450); khi nhiều chunk cùng hợp lệ nên phân biệt bằng ngữ nghĩa (đề xuất 4) |
| 14 | Chunk mở đầu về người còn sống bị `unknown` từ năm sinh | **Bỏ** (2026-10-21) | — | — | Bỏ: ban đầu rút từ vài ca mất; đo riêng 165 chunk mở đầu thì `unknown` 36 → 45 và 15 câu có chunk đúng là chunk mở đầu cho `hit@5` 7 → 9 (tốt hơn), `mrr` 0.417 → 0.378: không phải lỗi chung |
| 15 | Nhúng chunk kèm ngữ cảnh lân cận để cải thiện xếp hạng: (a) nối vài câu của chunk trước chỉ khi tính embedding, (b) nhúng cửa sổ hai đoạn, (c) làm mượt vector `v_i' = α·v_i + (1−α)·(v_{i−1} + v_{i+1})/2` từ vector có sẵn trong Qdrant | **Chưa** | **Chưa** | **Chưa** | **Ghi lại, chưa làm** (2026-10-21). Không gọi LLM; (a),(b) tính lại embedding ~4 phút, (c) không cần nhúng lại văn bản. Cơ sở: 52% câu sai ở kho v3 có chunk đúng cách chunk top-5 không quá 2 đoạn (`eval/05` mục 6.14). Khác mở rộng ngữ cảnh cuối chuỗi ở chỗ này đổi cả thứ hạng. Rủi ro: các đoạn kề nhau cạnh tranh nhau nhiều hơn, làm mờ tên riêng và năm; phải áp dụng giống nhau cho Plain RAG khi so sánh; α chọn trên valid |

Ghi chú về đề xuất 2 (nới `start` theo độ mịn; chưa đo riêng, `range` ở đề xuất 1 là cách làm theo độ mịn của câu hỏi): phân tích 37 câu bị lọc cứng ở kho v3: `start` − `t_req` trung vị 4.0 năm; 10 câu trong 1 năm, 13 câu trong 2 năm. Ít nhất 3 câu (Luftflotte, Janet Frame, Nana Okada) là lệch độ mịn thật sự (câu hỏi cả năm hoặc tháng, `t_req` là ngày đầu kỳ, chunk bắt đầu giữa kỳ); các câu còn lại là nhãn lệch năm.


## Bối cảnh

Chạy 142 kịch bản trên bộ thật ([`eval/05`](../eval/05_REAL_RESULTS.md)): cấu hình tốt nhất có `hit@5` 0.687 và `mrr` 0.444. Mất điểm ở hai chỗ (mục 5 và 7 của `eval/05`):

- **21% câu**: chunk đúng vào được ứng viên nhưng xếp sau top-5; 94% trong số đó thì chunk hạng 1 là chunk khác của chính trang đáp án.
- **9.3% câu**: bộ lọc cứng `start <= T_req` loại chunk đúng.

Phân tích 75 câu xếp sau top-5 (dense · stored · `t_unknown` 0.1) và 37 câu bị lọc (xem `eval/05`, mục 5.1 và 7):

| Quan sát | Số liệu |
|---|---|
| Chunk đúng có khoảng `[start, end]` kết thúc trước `t_req` | 66/75 câu; trung vị `t_req − end` = 7.3 năm; 18 câu dưới 1 năm |
| Trong 66 câu đó, `end_status` của chunk đúng | `known` 40, `unknown` 26 (`unknown`: `end` là **giả định** của công thức, cuối năm của `start`, không phải dữ liệu) |
| Trong 18 câu dưới 1 năm: `end` là cuối tháng/quý/năm | 13/18; 14 `known`, 4 `unknown` |
| 37 câu bị lọc: `start` cùng năm với nhãn / trong khoảng nhãn / sau khoảng nhãn | 7 / 9 / 21 |
| Profiler hiện chỉ trích **một điểm** `t_req` | khoảng "from 2018 to 2020" dùng **điểm cuối** (prompt `time_extractor_v1.md`) |

Nguyên nhân khác nhau tùy nhóm và **chưa tách hết**:

1. **Lệch độ mịn**: `t_req` là ngày đầu tháng/năm (câu hỏi "in Apr 1998" thành 1998-04-01) nhưng `end` của chunk là ngày cuối kỳ (1998-03-31); chênh 1 ngày vẫn thành "đã kết thúc".
2. **Chunk đáp án theo nhãn không nói về đúng thời kỳ của câu hỏi**: nhãn của bộ là đoạn *chứa chuỗi đáp án*; đoạn tóm tắt hoặc đoạn "hiện tại" thường chứa đáp án của nhiều thời kỳ (vd Goryachkina hỏi 2012, chunk nói về 2018). Đọc tay 21 đoạn trong nhóm 37 câu bị lọc (`eval/05` mục 7): `start` LLM gán khớp với nội dung có ghi ngày của đoạn, nhưng 6/21 là đoạn nhiều thời kỳ mà thiết kế chỉ cho một khoảng (giới hạn thiết kế, không phải LLM sai), 9/21 nhắc đáp án như chi tiết phụ, 3/21 trùng chuỗi ngẫu nhiên, 3/21 nhãn dữ liệu lệch hoặc tên đã đổi.
3. **`end` do LLM suy ra từ từ khóa sự kiện** ("merged", "transferred", "revived") là phán đoán: Mark Levin (`end` 31/12/2018 vì sáp nhập), Beugró (`end` 31/12/2017 dù chương trình được dựng lại cuối 2017), Veliky Novgorod (`end` 1944-12-31 dù lý do ghi "tồn tại đến 1927"). Một số `end` này có vẻ sai, một số hợp lý; **chưa đọc hết 66 câu nên không đếm được tỉ lệ sai thật**.
4. **Công thức TH2 đo khoảng cách từ `start`, không phải từ `end`** (`scoring.py`: `delta_years(t_req, chunk.start_time)`; design `02` mục 3.2 ghi rõ vậy). Chunk sống lâu và vừa kết thúc trước `t_req` bị phạt nặng như chunk cổ (vd chunk 1727–1944 hỏi tháng 7/1945: Δ = 218 năm, `exp(-0.5·218)` gần 0, dù mới kết thúc 6 tháng).
5. **`t_req` của Profiler thô**: "late 1900s" thành 1999-12-31 (lẽ ra thập niên 1900), khoảng "between Aug 2005 and Sep 2006" thành điểm cuối khoảng.

## Tóm tắt các đề xuất

| # | Ý tưởng | Sửa ở đâu | Vấn đề nhắm tới | Cần LLM |
|---|---|---|---|---|
| 1 | Câu hỏi là **khoảng** `[qs, qe]` (theo độ mịn của câu hỏi); lọc cứng `cs <= qe`; điểm theo chồng lấn | Profiler, lọc, điểm | Câu hỏi chỉ có một điểm trong khi chunk có khoảng; lệch độ mịn (37 câu bị lọc: nhóm A) | Có (Profiler 400 câu) |
| 2 | Dung sai cố định cho bộ lọc | Lọc | Cùng lỗi với 1, nhưng phụ thuộc bộ dữ liệu | Không |
| 3 | Chunk đã kết thúc bị phạt theo thời gian **từ `end`**, không từ `start` | Điểm (TH2) | Chunk sống lâu vừa kết thúc bị phạt như chunk cổ | Không; **đã thử: +0.007 `mrr`, nhỏ** |
| 4 | Reranker cross-encoder / LLM | **Chưa code** | Chưa | `fastembed` có sẵn `TextCrossEncoder`; đã thử tải `Xenova/ms-marco-MiniLM-L-6-v2` (13 giây, chấm 20 cặp ~0.01 giây). **Việc tiếp theo** |
| 5 | Chỉ số chuỗi đáp án và tách 37 câu có chunk đáp án nằm sau thời điểm hỏi | Đánh giá | Chunk đáp án theo nhãn lệch thời kỳ | Không |
| 6 | Quét `λ`, `W1/W2` trên D/train | Tham số | Chưa chốt bằng dữ liệu | Không |
| 7 | Mở rộng ngữ cảnh bằng chunk **cùng trang giao khoảng hỏi** (ngoài chunk liền kề theo chỉ số) | Sau xếp hạng | Đúng trang nhưng nhầm thời kỳ; câu nhiều chunk đúng | Không |
| 8 | Một chunk nhiều khoảng (LLM liệt kê từng sự việc có ngày; lọc theo mốc sớm nhất, chấm theo khoảng tốt nhất) | Ingestion, điểm | Đoạn nhiều thời kỳ chỉ gán một khoảng (khoảng 3–6 trong 37 câu bị lọc) | Có (nạp lại kho khoảng 330 lô) Hoãn sang Cơ chế 2 (2026-10-21): đồ thị sự kiện cho mỗi sự việc một `[start, end]` riêng và có con trỏ `Chunk_ID`; làm đề xuất 8 ở VectorDB sẽ trùng việc; tinh chỉnh một thể khi làm Cơ chế 2 |
| 9 | Ingestion v3: phân biệt **sự kiện và trạng thái** ("chuyển tới X năm 1950" kéo dài tới khi có sự kiện thay thế, `end` không bằng `start`) | **Chưa code** | Chưa | Từ phân tích câu sai (`eval/05` 6.12): chunk đúng hết hạn 51/123 câu; cần LLM + nạp lại kho; gắn với `time_extractor_v3` (hoãn vì quota) |
| 10 | `min_validity`: coi chunk còn hợp lệ ít nhất `start + L` năm (làm mềm `end`) | **Chưa code** | Chưa | Không cần LLM; dự định quét L ∈ {1, 5, 10, ∞} trên tập local/valid; rủi ro dương tính giả |
| 11 | Kế thừa mốc cho chunk không mốc từ chunk có mốc gần nhất cùng mục | **Chưa code** | Chưa | 15/123 câu sai; mốc kế thừa phải đánh dấu là suy ra, điểm thấp hơn mốc thật Mở rộng (2026-10-21): suy luận cả `start`, `end` từ chunk liền kề, không chỉ chunk không mốc; xem bảng tóm tắt |
| 12 | Không mở rộng lọc cứng cho `start` > `t_req` | Không làm | — | Vi phạm bất biến không rò rỉ tương lai; chỉ cứu thêm ~14 câu lệch ≤ 2 năm. Ghi lại để khỏi đề xuất lại |

## Đề xuất

Xếp theo (tác động kỳ vọng) / (công sức); không cái nào cần gọi LLM mới trừ đề xuất 1.

### Đề xuất 1: Profiler trích **khoảng** thời gian và chấm bằng độ chồng lấn

- Hiện tại: `Extraction.t_req` là một điểm ISO; khoảng được rút về điểm cuối. Chunk thì đã có khoảng `[start, end]`.
- Đổi: Profiler trả `t_start`, `t_end` theo **độ mịn của câu hỏi** (chỉ năm: cả năm; tháng và năm: cả tháng; "during the 1990s": 1990-01-01 đến 1999-12-31; một ngày: `t_start = t_end`).
- **Lọc và chấm điểm dùng hai quy tắc khác nhau** (gọi khoảng hỏi là `Q = [qs, qe]`, khoảng chunk là `C = [cs, ce]`):

  | Bước | Quy tắc | Lý do |
  |---|---|---|
  | Lọc cứng | giữ chunk có `cs <= qe` (chunk không bắt đầu **sau khi** khoảng hỏi kết thúc); vẫn loại `invalidated_at` | giữ nguyên tắc không rò rỉ tương lai ở độ mịn của câu hỏi; điểm số chưa nên quyết ở đây |
  | Điểm thời gian, có giao nhau (`cs <= qe` và `ce >= qs`) | `Temporal = 1.0` (bản nhị phân); biến thể: `độ phủ = |C ∩ Q| / |Q|`, tức chunk phủ bao nhiêu phần khoảng hỏi | câu hỏi điểm (`qs = qe`) thì giao nhau là chứa mốc, như TH1 hiện nay |
  | Điểm thời gian, không giao nhau (`ce < qs`) | `Temporal = exp(-λ·năm(qs − ce))`, tính **từ `end`** (xem đề xuất 3) | chunk vừa kết thúc 1 ngày trước khoảng hỏi gần như không bị phạt, nên lệch biên tự hết, không cần dung sai cố định |

  Nên dùng **độ phủ trên `|Q|`**, không dùng Jaccard: Jaccard phạt chunk sống lâu (50 năm) khi hỏi một năm, trong khi chunk đó phủ trọn khoảng hỏi. Quy ước khoảng: chỉ năm thì cả năm; tháng thì cả tháng; "before X" là `(-inf, X]`; "after X" là `[X, T_now]`; "between A and B" là `[A, B]`; "late 1990s" là `[1997-01-01, 1999-12-31]` (do Profiler quyết, dễ sai). `end_status` `ongoing`/`unknown` giữ cách xử lý `end_mode` hiện có để tính `ce`.
- **Có thể đo trước giá trị của đề xuất này bằng đọc tay** (`eval/05` mục 7): trong 37 câu bị lọc, 4 câu là lệch độ mịn năm/tháng và 2 câu là "after X" (6 câu cứu được bằng khoảng); 1 câu nhiễu dữ liệu và 30 câu là đoạn nhiều thời kỳ hoặc nhắc đáp án phụ (không cứu được). Cao nhất là +6 câu (+1.5 điểm `hit@5`) cho nhánh lọc, cộng một phần của các câu lệch biên dưới 1 năm. **Lọc theo "`qe` nằm trong chunk" thì quá chặt**: chunk sự việc một ngày (Nana Okada 22/2/2017, USAFE 15/6/1942) không chứa `qe` (cuối năm/tháng) nên vẫn bị loại; dùng **có giao nhau** (`cs <= qe` và `ce >= qs`).
- **Không phải bỏ lọc cứng**: lọc cứng vẫn còn, chỉ đổi từ `start <= t_req` thành `start <= qe`. Đổi lọc cứng thành phạt điểm sẽ cho chunk thật sự thuộc tương lai lọt vào, đúng nguyên tắc rò rỉ tương lai mà Cơ chế 1 phải chặn (CLAUDE.md; Plain RAG có `leakage_rate` 0.665 vì không lọc). Phần "mềm" chỉ nằm ở điểm cho chunk đã kết thúc trước `qs`.
- **Không có "khoảng 1 năm" cố định**: độ mịn lấy từ chính câu hỏi ("Apr 1998" là cả tháng 4, "1990" là cả năm 1990), nên nó tự co giãn theo bộ dữ liệu: câu hỏi cấp ngày thì khoảng là một ngày. Con số "1 năm" ở đề xuất 2 chỉ là cách làm thô khi chưa có khoảng. Độ mịn cũng có ở phía chunk (nhãn `start` chỉ có năm thì `cs` là cả năm đó); khi so sánh nên coi hai phía là khoảng và dùng phép "có thể giao nhau". Một dung sai `δ` cấu hình được (mặc định 0) chỉ cần nếu một bộ có nhãn thô hơn câu hỏi; chưa có bằng chứng cần.
- Vì sao tốt: **giải quyết nhóm A (7 câu bị lọc) và các trường hợp biên 1 ngày** mà không phải chọn dung sai cố định, và độ mịn lấy từ chính câu hỏi nên không phụ thuộc bộ dữ liệu. Với câu hỏi khoảng (một phần các câu "between X and Y"), nó cũng đúng hơn việc lấy điểm cuối.
- Chi phí: đổi schema `Extraction`/`ProfiledQuery`, prompt `time_extractor_v1.md`, `filters.py`, `scoring.py`; chạy lại Profiler 400 câu (khoảng 400 request Gemini; cache khóa theo prompt nên prompt mới thì gọi lại toàn bộ); thêm test.
- Rủi ro: câu "after X"/"before X" cần quy ước khoảng mở; điểm chồng lấn thay đổi thang của `W2`.

**Kết quả chạy Profiler khoảng trên bộ thật (400 câu, Gemini 3.1, prompt v2, 2026-10-20):**
- `bound`: exact 334, after 35, before 30, none 1 (câu không nêu thời gian); `use_t_now` 1 câu; 0 lỗi.
- Độ rộng khoảng: trung vị 90 ngày; 31 câu một ngày, 143 câu ≤ 31 ngày, 97 câu 32–366 ngày, 129 câu trên 1 năm (tức khoảng 1/3 câu hỏi là khoảng dài).
- So với `t_req` cũ: điểm đầu `qs` giống `t_req` cũ ở 232/400 câu; 168 câu khác nhau, chủ yếu là câu "between X and Y" (cũ lấy điểm cuối, mới lấy điểm đầu của khoảng).
- So với khoảng nhãn thời gian của bộ dữ liệu: `t_req` cũ nằm trong khoảng nhãn ở 390/400 câu; khoảng mới **giao** khoảng nhãn ở 395/400 câu.
- 5 câu không giao khoảng nhãn: 2 câu do Profiler ("late 1900s" bị đọc là 1997–1999, đúng ra là thập niên 1900, Alexander Imich và John Francis Charles; một lỗi mơ hồ của chính cụm từ, nên cần ví dụ cho "1900s" ở prompt `v3`), 3 câu do dữ liệu (Germaine of Foix: câu hỏi không nêu thời gian nhưng nhãn 1526–1527; Thomas Fearnley: "in 1930?" nhãn 1830–1832; Auditorium Building: câu hỏi 1970–1974, nhãn 1975–1976).

**Nói ngắn gọn "độ mịn" và "chỉ lấy điểm X" là gì.** "Độ mịn" là **mức chính xác mà câu hỏi nêu thời gian**: "1990" chỉ chính xác đến năm, "March 1990" đến tháng, "12 May 2019" đến ngày. Hiện Profiler luôn trả **một ngày**: với "in 1990" nó trả 1990-01-01, tức hệ coi như câu hỏi nói về đúng ngày 1/1/1990 và chunk bắt đầu 6/2/1990 là "tương lai", dù cùng năm 1990. Đề xuất 1 chỉ là: **trả cả khoảng mà câu hỏi nêu** ("in 1990" thành 1/1/1990–31/12/1990), nên mọi chunk nằm trong 1990 đều được giữ. Không có phép tính độ mịn phức tạp: Profiler chỉ ghi ngày đầu và ngày cuối của khoảng được nhắc. "Chỉ lấy điểm X" ở câu "after X" nghĩa là Profiler giữ ngày X và **bỏ chữ "after"**, nên không biết câu hỏi mở về phía sau X.

**`t_req` hiện nay so với khoảng `[qs, qe]`** (theo `time_extractor_v1.md`; `t_req` luôn là **ngày đầu** của thời gian được nhắc, riêng khoảng thì lấy ngày đầu của năm/tháng cuối):

| Câu hỏi | `t_req` hiện tại | `[qs, qe]` đề xuất |
|---|---|---|
| "in 1990" | 1990-01-01 | 1990-01-01 đến 1990-12-31 |
| "in March 1990" | 1990-03-01 | 1990-03-01 đến 1990-03-31 |
| "on 12 May 2019" | 2019-05-12 | 2019-05-12 đến 2019-05-12 (`qs = qe`, giống điểm) |
| "from 2018 to 2020" | 2020-01-01 (điểm cuối) | 2018-01-01 đến 2020-12-31 |
| "currently" | T_now | T_now đến T_now |

Câu hỏi nêu thời gian **không đủ rõ** thì Profiler gán như sau (đề xuất, chưa code):

| Câu hỏi | `[qs, qe]` |
|---|---|
| "after X", "since X" | `[X, T_now]` |
| "before X", "until X" | **Mặc định `[X, X]`** (`before_lower="point"`): chunk gần nhất trước X được ưu tiên nhờ điểm lùi về quá khứ, cùng hành vi hiện nay (`hit@5` của nhóm "before" là 0.806). Tùy chọn `before_lower="min"`: `[0001-01-01, X]` (mở cận dưới; kho đã loại mốc trước Công nguyên); chưa đo xem cái nào tốt hơn |
| "as of X" | `[X, X]` |
| "in the 1990s" | `[1990-01-01, 1999-12-31]` |
| "early/late 1990s" | `[1990-01-01, 1993-12-31]` / `[1997-01-01, 1999-12-31]` (Profiler quyết, dễ sai) |
| không nêu thời gian, hoặc "now" | `[T_now, T_now]`, `use_t_now = true` |
| LLM chỉ nêu một mốc, không nêu điểm cuối | **`qe` = ngày cuối của đơn vị thời gian của `qs`**: "2026" thì `[2026-01-01, 2026-12-31]`; "March 2026" thì `[2026-03-01, 2026-03-31]`; một ngày cụ thể thì `qe = qs` |

Cách làm gọn: Profiler vẫn trả mốc dạng ISO **một phần** ("2026", "2026-03", "2026-03-12"; `parse_t_req` hiện đã nhận cả ba dạng), còn **code** (không phải LLM) mở rộng ra `[ngày đầu, ngày cuối]` theo độ dài chuỗi. Như vậy LLM không phải tự tính ngày cuối tháng (hay sai, vd tháng 2 năm nhuận) và độ mịn đọc được từ chính chuỗi. Với khoảng, Profiler trả hai mốc ISO một phần (`t_start`, `t_end`) và code lấy ngày đầu của `t_start`, ngày cuối của `t_end`.

**Chunk không xác định được `start` trong ingestion**: không bỏ hết. LLM trả `no_time` cho 1460/6880 chunk của bộ thật; chạy `ingest.py --keep-undated` (đang dùng) giữ **1358 chunk** có nội dung (có nhãn domain) và chỉ bỏ 102 chunk rỗng (tiêu đề...); các chunk giữ lại **không có `start_time`**, đi qua nhánh `t_unknown` với điểm cố định (`decisions/04`). Không dùng cờ `--keep-undated` thì tất cả bị bỏ. Thêm 41 chunk `invalid_time` (mốc không hợp lệ, vd trước Công nguyên) luôn bị bỏ. Đề xuất 1 không đổi việc này.

Với câu hỏi một thời điểm cụ thể (một ngày) thì `qs = qe = t_req`, hệ hoạt động y như bây giờ. Khác biệt chỉ xuất hiện khi câu hỏi nêu thời gian ở mức thô (năm, tháng, khoảng): hiện chỉ lấy ngày đầu nên chunk bắt đầu "tháng 8/1990" bị lọc khi hỏi "in 1990", còn với khoảng thì chỉ dùng điểm cuối nên bỏ qua phần đầu khoảng.

**"Dung sai cố định"** (đề xuất 2) là một khoảng đệm hằng số cộng vào bộ lọc: giữ chunk nếu `start <= t_req + 365 ngày`. Hằng số này phải chọn tay theo bộ dữ liệu: câu hỏi cấp năm cần ~1 năm nhưng câu hỏi cấp ngày mà vẫn cộng 1 năm thì cho chunk của 11 tháng sau lọt vào (rò rỉ tương lai). Khoảng `[qs, qe]` không có hằng số nào: độ rộng đến từ độ mịn của câu hỏi.

**Dạng câu hỏi của bộ thật** (đếm bằng mẫu chữ trên 400 câu, `hit@5` của cấu hình tốt nhất): "in Month YYYY" 142 câu (0.627); "between/from X to Y" 136 (0.763); "after X" 35 (0.657); "early/late/mid" 33 (0.606); "before X" 31 (0.806); "in YYYY" 20 (0.550); khác 3. Khoảng nhãn thời gian có độ rộng trung vị 2 năm (160 câu ≤ 1 năm, 120 câu 2–5 năm, 120 câu trên 5 năm). Nghĩa là **34% câu hỏi đã là khoảng** mà Profiler hiện rút về một điểm, và câu "after X" (8.8%) có `hit@5` gần mức trung bình (không phải nhóm đặc biệt kém), nên cứu "after" chỉ đáng kể về mặt đúng ngữ nghĩa, ít về số điểm (đọc tay chỉ có 2 câu bị lọc vì "after").

**Quy về ngày**: mọi mốc quy về ngày (`datetime` UTC, độ chính xác ngày); khoảng đóng ở hai đầu, `end` tính hết ngày đó. Năm hoặc tháng chỉ là ngày đầu và ngày cuối kỳ. Đây cũng là cách ingestion đang lưu (`end` 1990-12-31 cho "năm 1990").

**Khi nào "có giao nhau" vẫn chưa đủ** (đề xuất 1 phải đi kèm cách xử lý):

| Tình huống | Vì sao giao nhau không đủ | Cách xử lý |
|---|---|---|
| Khoảng hỏi rất rộng ("during the 1990s", "after 1938") | Hàng chục chunk cùng giao, đều được 1.0, xếp hạng rơi về ngữ nghĩa | Dùng **độ phủ** `|C ∩ Q| / |Q|` thay vì nhị phân; chunk phủ nhiều hơn xếp trên |
| Chunk `ongoing`/`unknown` có khoảng rất dài | Giao nhau với mọi câu hỏi sau `start`, kể cả khi đã lỗi thời | Giữ `end_mode` (`unknown_decay`) làm mềm điểm của `unknown` |
| Chunk nhiều thời kỳ gom thành một khoảng bao (`min start` đến `max end`) | Giao nhau với nhiều thời điểm mà đoạn không thật sự nói tới | Chỉ giải quyết triệt để bằng đề xuất 8 (nhiều khoảng) |
| Câu hỏi sự kiện ("who *became* PM in 1990") so với trạng thái ("who *was* PM") | Chunk trạng thái giao cả năm, chunk sự kiện chỉ giao đúng ngày | Chưa có cách; đây là loại câu hỏi khác, nằm ngoài phạm vi hiện nay |
| Khoảng mở "after X" | Gần như mọi chunk sau X giao | Chấp nhận; điểm quyết định là ngữ nghĩa; có thể thêm ưu tiên gần X |

### Đề xuất 2: dung sai của bộ lọc cứng (đã bỏ, 2026-10-21)

**Đã bỏ:** δ cố định không có căn cứ chung; δ theo độ mịn của câu hỏi chính là đề xuất 1 (`range`, đã đo, hiệu quả nhỏ). Nội dung gốc giữ lại bên dưới.


- `start <= T_req + δ`. **δ phụ thuộc bộ câu hỏi nếu để cố định** (1 năm hợp với câu hỏi cấp năm của TimeQA nhưng quá lỏng với câu hỏi cấp ngày). Nên gắn δ với độ mịn của câu hỏi (tháng: 1 tháng, năm: 1 năm), tức thực chất là đề xuất 1.
- Nếu chỉ thử nhanh: δ cố định 365 ngày; kỳ vọng cứu được nhóm A (7 câu) và một phần 13 câu bị lọc dưới 1 năm; cũng phải chấp nhận nhóm B và C (30 câu) vẫn bị lọc vì chunk đáp án nằm sau thời điểm hỏi. **Nguy cơ**: nới lọc làm mất tính chặn rò rỉ tương lai về mặt nguyên tắc; ghi rõ δ là dung sai độ mịn, không phải cho phép dùng thông tin tương lai.

### Đề xuất 3: phạt chunk đã hết hạn theo khoảng cách từ `end`, không phải từ `start`

**Nói bằng lời.** Mỗi chunk có một khoảng hiệu lực `[start, end]`. Khi câu hỏi (mốc `t_req`) rơi **trong** khoảng đó thì chunk được 1.0 điểm thời gian. Khi chunk **đã hết hạn trước `t_req`** (`end < t_req`, trường hợp TH2 trong design `02`) thì nó vẫn được giữ làm phương án dự phòng nhưng bị trừ điểm, và điểm giảm theo thời gian trôi qua. Câu hỏi là: "thời gian trôi qua" tính **từ lúc nào**? Hiện tại code tính từ **`start`** của chunk (`scoring.py`: `delta_years(t_req, chunk.start_time)`), đề xuất tính từ **`end`**.

**Ví dụ** (λ = 0.5, điểm = `exp(-λ·số năm)`):

| Chunk | `t_req` | Tính từ `start` (hiện tại) | Tính từ `end` (đề xuất) |
|---|---|---|---|
| Veliky Novgorod: 1727 đến 1944-12-31 (đã hết 6 tháng) | 1945-07-01 | Δ = 218 năm, điểm **0.000** (3.6e-48) | Δ = 0.5 năm, điểm **0.78** |
| Chunk 2013 đến 2015 (đã hết 1 năm) | 2016-01-01 | Δ = 3 năm, điểm 0.22 | Δ = 1 năm, điểm 0.61 |
| Chunk 1998-01-01 đến 1998-03-31 (hết 1 ngày), hỏi 1998-04-01 | 1998-04-01 | Δ = 0.25 năm, điểm 0.88 | Δ = 0.003 năm, điểm **1.00** |

Cách tính từ `start` đúng cho văn bản pháp luật ngắn hạn trong ví dụ gốc của design (luật 2018 hiệu lực ngắn, nên `start` và `end` gần nhau) nhưng sai với chunk sống lâu: chunk có hiệu lực 200 năm vừa hết hạn bị coi như "rất cổ". Trong dữ liệu thật phần lớn chunk là một đoạn mô tả một giai đoạn có độ dài rất khác nhau.

**Không liên quan tới `unknown_decay`.** `unknown_decay` xử lý chunk **chưa biết `end`** (`end_status = unknown`): nó phạt theo `start` vì không còn mốc nào khác. Đề xuất 3 chỉ xử lý chunk có `end` **thật** (`known`) mà đã qua. Bảng dưới là các trường hợp của chunk:

  | Trường hợp chunk | Điểm hiện tại | Đề xuất 3 |
  |---|---|---|
  | `ongoing` | 1.0 mãi | không đổi |
  | `unknown`, `end_mode: unknown_decay` | `exp(-d·(t_req − start))` | không đổi |
  | `known`, `t_req <= end` (TH1) | 1.0 | không đổi |
  | `known`, `t_req > end` (TH2, đã hết hạn) | `exp(-λ·(t_req − start))` | **`exp(-λ·(t_req − end))`** |

Trong chế độ `stored` chunk `unknown` bị gán `end` = cuối năm của `start`, nên rơi vào hàng cuối; đó là 26 trong 66 câu đã phân tích. Với `unknown_decay` chúng đi theo hàng thứ hai.

- Vì sao đề xuất: 66/75 câu xếp sau top-5 có chunk đúng đã hết hạn trước `t_req` (mục Bối cảnh), nên cách trừ điểm này ảnh hưởng trực tiếp tới chúng. Hiệu ứng "chunk sống lâu bị phạt như chunk cổ" cũng làm tệ nhóm lệch biên (18 câu dưới 1 năm).
- **Đã code dạng tùy chọn, mặc định không đổi**: `retrieval.decay_from: "start" | "end"` trong `config.*.yaml` (mặc định `start`), tham số `decay_from` của `TemporalRetriever`/`temporal_score`, cờ `--decay-from` của `evaluate.py`; 3 test mới. Muốn bỏ chỉ cần không đặt `end`, không phải sửa logic.
- **Kết quả thử (2026-10-20, 34 kịch bản mỗi bộ, 28 cặp so được với cấu hình `start` cùng tên):**

| Cấu hình | `mrr` bộ thật: `start` → `end` | `hit@5` bộ thật | `mrr` local | `hit@5` local |
|---|---|---|---|---|
| dense · stored · tắt | 0.418 → **0.428** | 0.622 → 0.647 | 0.494 → 0.517 | 0.675 → 0.725 |
| dense · stored · t_unknown 0.1 | 0.441 → **0.450** | 0.679 → 0.702 | 0.542 → 0.549 | 0.800 → 0.825 |
| dense · open · t_unknown 0.1 | 0.430 → **0.436** | 0.647 → 0.657 | 0.525 → 0.527 | 0.725 → 0.750 |
| dense · decay 0.1 · t_unknown 0.1 | 0.438 → **0.446** | 0.684 → 0.697 | 0.544 → 0.550 | 0.800 → 0.825 |
| dense · unknown decay 0.1 · t_unknown 0.1 | 0.444 → **0.452** | 0.687 → 0.699 | 0.580 → 0.586 | 0.825 → 0.850 |
| hybrid · stored · tắt | 0.386 → **0.392** | 0.627 → 0.644 | 0.420 → 0.445 | 0.650 → 0.675 |

  - Tăng ở **28/28 cặp** ở cả hai bộ: `mrr` bộ thật +0.004 đến +0.010 (trung bình +0.007), `hit@5` +0.017; local `mrr` +0.013, `hit@5` +0.026. Cấu hình tốt nhất cũ lên 0.452 (bộ thật) và 0.586 (local); cao nhất mọi cấu hình bộ thật 0.460 (`unknown decay` 0.05, `t_unknown` 0.1).
  - **Mức tăng nhỏ và chưa chắc chắn ở bộ thật**: ghép cặp từng câu cho cấu hình tốt nhất `Δmrr` = +0.009 ± 0.009 (khoảng 95% chạm 0), 15 câu tăng, 14 câu giảm; `hit@5` thêm 9 câu, mất 4. Chỉ khoảng 30 câu đổi thứ hạng. 28 cặp cùng chiều là do cùng dữ liệu nên không độc lập.
  - Kết luận tạm: giả thuyết "phạt từ `start` là nguyên nhân chính của 66 câu" **không đúng**; nó chỉ giải thích một phần nhỏ. Phần lớn chunk đúng ở các câu đó vẫn thua vì thời kỳ của chúng không khớp `t_req` (lỗi của chunk đáp án theo nhãn, mục 5 và 7 của `eval/05`). Cờ vẫn đáng giữ vì chiều tăng nhất quán và rẻ.
  - Dữ liệu: `dataset/eval/results_real_decay_from_end.csv`, `results_local_decay_from_end.csv`.
- Rủi ro: đổi một lựa chọn đã ghi trong design `02` (Δ từ `start`); cần cập nhật design nếu thắng. Có thể làm giảm điểm vài câu vốn đúng nhờ phạt nặng chunk cổ; chỉ đo mới biết.

### Đề xuất 4: reranker học được ở bước cuối (top-20)

- **Hiện chưa có reranker.** "Re-rank" trong Cơ chế 1 chỉ là công thức `Final = W1·Semantic + W2·Temporal` (`Semantic` = điểm RRF min-max về [0, 1], `Temporal` như trên). Không có mô hình nào đọc cặp (câu hỏi, chunk).
- Đề xuất: lấy top-20 theo `Final`, chấm lại bằng reranker, rồi trộn với `Temporal`. Khoảng cách giữa `hit@5` 0.687 và `hit@20` 0.877 là chỗ có dư địa (chưa đo mức cứu được).
- **Cross-encoder chạy cục bộ, miễn phí**, đã có sẵn trong `fastembed` đang dùng (`TextCrossEncoder`):

  | Mô hình | Cỡ | Giấy phép | Ghi chú |
  |---|---|---|---|
  | `Xenova/ms-marco-MiniLM-L-6-v2` | 0.08 GB | Apache-2.0 | nhẹ nhất, thử trước |
  | `Xenova/ms-marco-MiniLM-L-12-v2` | 0.12 GB | Apache-2.0 | |
  | `jinaai/jina-reranker-v1-tiny-en`, `...-turbo-en` | 0.13–0.15 GB | Apache-2.0 | ngữ cảnh 8K |
  | `BAAI/bge-reranker-base` | 1.04 GB | MIT | |
  | `BAAI/bge-reranker-v2-m3` (hoặc `-int8` 0.57 GB) | 2.27 GB | Apache-2.0 | đa ngôn ngữ, mạnh nhất trong danh sách |
  | `jinaai/jina-reranker-v2-base-multilingual` | 1.11 GB | **CC-BY-NC** | chỉ phi thương mại |

- **Điểm yếu cần lường**: cross-encoder không hiểu thời gian; nó sẽ xếp chunk "đúng chủ đề" lên đầu bất kể thời kỳ, đúng lỗi hiện tại (chọn nhầm thời kỳ cùng trang). Cách dùng: (a) chỉ dùng điểm của nó thay cho `Semantic`, giữ `W2·Temporal` để chọn thời kỳ; (b) ghép khoảng thời gian vào văn bản chunk ("[1976–1983] ...") để mô hình có tín hiệu.
- **LLM làm reranker** (Gemini 3.1/3.5 flash-lite): hiểu thời gian tốt hơn, nhưng mỗi câu một lần gọi (khoảng 400 request cho một lượt đánh giá, trên hạn mức 500/ngày mỗi model), chậm, không tái lập được hoàn toàn. Chỉ nên thử sau khi cross-encoder cho thấy dư địa.
- Thứ tự thử: MiniLM-L-6 (nhanh, kiểm tra ý tưởng) thì bge-reranker-v2-m3 (trần của cross-encoder miễn phí), rồi mới tính LLM.

### Đề xuất 5: chấm điểm cho khớp bản chất bài toán (chuỗi đáp án, tách 37 câu có chunk đáp án nằm sau thời điểm hỏi)

**"Chunk đúng" của bộ đánh giá được suy ra như thế nào.** TimeQA cho mỗi câu hỏi **chuỗi đáp án** kèm vị trí ký tự của nó trong trang (`answers[].from/end`). Ta đặt "chunk đúng" = đoạn chứa vị trí đó (`gold_paragraph_indices`), rồi chấm `hit@k`/`mrr` theo việc chunk đúng có nằm trong top-k hay không. Cách này ngầm giả định: đoạn chứa chuỗi đáp án cũng là đoạn nói về **thời kỳ của câu hỏi**.

**"37 câu có chunk đáp án nằm sau thời điểm hỏi"** (trước đây gọi là "lệch nhãn") là các câu giả định đó sai (9.3% của 399 câu có đáp án): chunk đúng theo nhãn có `start` **sau** `t_req`, tức đoạn đó mô tả một thời điểm muộn hơn thời điểm câu hỏi. Ví dụ: hỏi "Goryachkina đạt danh hiệu gì năm 2012", chuỗi đáp án (một danh hiệu) nằm trong đoạn "Historical achievements" nói về 2018. Đáp án đúng, câu hỏi đúng; đoạn đó nhắc "at the age of 13 ... Woman Grandmaster" (13 tuổi = 2012, không ghi năm) và "Grandmaster in early 2018" trong **cùng một chunk**, và ingestion chỉ gán một khoảng (2018). "Chunk đúng" do ta suy ra không nói về thời điểm hỏi. Hệ lọc đoạn này đi là **đúng thiết kế** (không dùng thông tin sau `t_req`), nhưng chỉ số lại tính là hệ trượt. Không phải toàn bộ là lỗi của dữ liệu: đọc tay 21 ca nhóm C cho thấy 6 ca là đoạn nhiều thời kỳ mà thiết kế chỉ gán một khoảng (giới hạn thật của hệ), còn lại là đoạn nhắc đáp án như chi tiết phụ, trùng chuỗi ngẫu nhiên, hoặc nhãn dữ liệu lệch (bảng ở `eval/05` mục 7).

**Ba chỉ số, từ lỏng đến chặt, ở cấu hình tốt nhất và Plain RAG** (đã tính tạm bằng script, chưa nằm trong `evaluate.py`):

| Chỉ số | Hỏi gì | Plain RAG dense | Cơ chế 1 tốt nhất |
|---|---|---|---|
| `hit@5` theo chunk id (đang dùng) | Chunk *được ta gắn nhãn đúng* có trong top-5 không | 0.549 | 0.687 |
| Top-5 có chứa chuỗi đáp án | Văn bản top-5 có chuỗi đáp án không, **bất kể chunk nào, bất kể thời kỳ** | 0.667 | 0.812 |
| Top-5 có chunk **hợp lệ tại `t_req`** chứa chuỗi đáp án | Có chunk top-5 vừa chứa chuỗi đáp án vừa có `[start, end]` bao `t_req` (chặt: chỉ chunk có mốc; có tính chunk không mốc: 0.486 và 0.689) | 0.406 | **0.627** |

**Cách xác định "chứa chuỗi đáp án"** (cài trong script tính tạm): chuẩn hóa cả chuỗi đáp án lẫn văn bản chunk (chữ thường, thay dấu câu bằng khoảng trắng, gộp khoảng trắng liền nhau), rồi kiểm tra **chuỗi đáp án đã chuẩn hóa có là chuỗi con liên tục của văn bản chunk đã chuẩn hóa không**; không so từng ký tự rời, không so gần đúng. Mỗi câu có một danh sách đáp án chấp nhận được (`targets`, 27/400 câu có nhiều hơn một), chỉ cần một đáp án khớp. Ví dụ "Woman Grandmaster ( WGM )" thành "woman grandmaster wgm". Kiểm tra độ nhạy: khớp theo ranh giới từ (đáp án không được dính vào chữ khác) cho 0.810, khớp chuỗi con 0.812, nên khác biệt không đáng kể. Cách làm này giống đo "answer recall" của DPR và các bài truy xuất cho QA mở. Hạn chế: không bắt được cách viết khác của cùng đáp án ("Villa" so với "Aston Villa"), nên có âm tính giả; chuỗi ngắn và chung ("colonel") có dương tính giả.

Khác chỉ số hiện nay ở chỗ nào: chỉ số hiện nay chỉ đúng khi trúng **đúng đoạn ta gắn nhãn**. Hai chỉ số mới hỏi "người đọc (LLM) có đủ chất liệu để trả lời không". Ví dụ đúng: hỏi "Alex McLeish làm huấn luyện viên đội nào tháng 4/2012" (đáp án Aston Villa); đoạn nhãn là #40 (không vào top-5), nhưng đoạn #3 (mốc 2011–2013) có câu "ông từ chức ở Birmingham để làm HLV Aston Villa" và nằm trong top-5, nên LLM trả lời đúng dù chỉ số cũ tính là trượt. Ví dụ sai nên cảnh giác: đáp án "Boeing 747" của câu hỏi về All Nippon Airways xuất hiện trong đoạn nói về công ty hàng hóa NCA ("operator of Boeing 747 freighters") và đoạn đó hợp lệ về thời gian, nhưng không phải đáp án thật. Cả hai đều là xấp xỉ: chỉ số chuỗi đáp án có dương tính giả (chuỗi ngẫu nhiên) và chỉ số hợp lệ phụ thuộc nhãn `[start, end]` của chính ingestion (vòng lặp nhẹ); cần đọc mẫu để tin. Chỉ số thứ ba cho khoảng cách giữa Plain RAG và Cơ chế 1 **+0.22** (0.406 so với 0.627), lớn hơn +0.14 của chỉ số cũ, vì Plain RAG kéo về nhiều chunk có chuỗi đáp án nhưng sai thời kỳ.

**Kiểm chứng: đoạn "chứa chuỗi đáp án" có thật sự là bằng chứng của đáp án không.** Có 31 câu (7.8% của 399) mà `hit@5` theo chunk id là trượt nhưng top-5 có chunk hợp lệ tại `t_req` chứa chuỗi đáp án. Đọc tay 24 câu ngẫu nhiên trong 31 (seed 7), hỏi "đoạn này có nói đáp án đúng cho câu hỏi tại `t_req` không":

| Kết quả | Số câu | Ví dụ |
|---|---|---|
| Đoạn thật sự hỗ trợ đáp án | **16 (67%)** | McLeish làm HLV Aston Villa; Janet Frame nhận Order of New Zealand năm 1990 (đoạn liệt kê giải thưởng có "1990: O.N.Z."); Stauskas học trường Loyola đến 2009 |
| Trùng chuỗi, không phải bằng chứng | 8 (33%) | "Boeing 747" trong đoạn hãng hàng hóa NCA (3 câu của ANA); "Russian" trong "Communist Party of the Russian Federation"; "Taiwan" trong nơi mất của Li Kwoh-ting (câu hỏi về quốc tịch); "Seattle" trong quảng cáo; "FIDE" trong "FIDE rating"; "Germany" trong "East Germany" |

Ước lượng thô từ đó: mức "top-5 thật sự có bằng chứng" nằm khoảng **0.74** (0.687 của chunk id cộng khoảng 20 câu thật sự trúng ở chunk khác, 5%), thấp hơn nhiều so với 0.812; khoảng tin cậy rộng vì chỉ 24 mẫu (16/24 là 67%, khoảng 95% khoảng 47–82%). Ca gần ranh: Guy Aldred "APCF" (đoạn giới thiệu chung, không nói thời điểm 1922); Chicago Red Stars "SeatGeek Stadium" (đoạn nói "Toyota Park, nay là SeatGeek Stadium", đúng chuỗi nhưng khác tên ở 2009). Nghĩa là **chuỗi đáp án có mặt chưa chắc là đáp án cần tìm**; muốn biết chắc cần LLM đọc ngữ cảnh trả lời (EM/F1 thật) hoặc đọc tay.

**Có phải cheat không** (đánh giá khác nhau theo chủ đề, và chỉ số tự dựng):
- **Chỉ số khác nhau theo chủ đề không phải cheat**, miễn là *cùng một chỉ số, cùng giao thức* áp cho mọi hệ được so (Plain RAG và Cơ chế 1), và chọn trước khi xem kết quả. Chỉ số "top-k chứa chuỗi đáp án" là cách đo chuẩn của truy xuất cho QA mở (answer recall của DPR); điều khoản pháp lý sẽ dùng gold là phiên bản điều khoản đã gán nhãn.
- **Chỗ có nguy cơ vòng lặp**: chỉ số thứ ba dùng nhãn `[start, end]` do **chính ingestion của ta** gán để quyết "chunk hợp lệ tại `t_req`". Trong các số ở trên, mình đã dùng cùng bộ nhãn đó để chấm cả Plain RAG, nên không thiên vị riêng một hệ, nhưng vẫn **chấm theo nhãn của hệ mình**: hệ nào đồng ý với nhãn đó sẽ lợi. Vì vậy phải ghi nhãn là chỉ số chẩn đoán, không phải con số chính; muốn con số chính thì dùng nhãn thời gian độc lập (nhãn của bộ dữ liệu hoặc đọc tay) hoặc EM/F1 của một LLM đọc cố định (cùng prompt, cùng model cho mọi hệ).
- **Phương pháp khác nhau theo chủ đề**: không phải cheat nếu tham số (`λ`, `W1/W2`, `end_mode`, `t_unknown`) được chọn trên **tập tinh chỉnh riêng** (D/train, đợt 6), khóa lại rồi mới chấm tập kiểm tra, và baseline cũng được chỉnh công bằng (cùng chunking, cùng `top_k`). Chỗ cần cẩn thận hiện nay: mình đã xem kết quả của 142 kịch bản trên bộ thật; cấu hình để báo cáo nên là cấu hình **chọn từ local trước** (dense, `t_unknown` 0.1, `stored`), không phải cấu hình đứng đầu bộ thật (0.452 chỉ hơn 0.444, nằm trong sai số). Chế độ `oracle` (dùng nhãn thời gian của câu hỏi) luôn ghi rõ riêng, không dùng làm kết quả chính.

**Đề xuất làm hai việc, đều chỉ ở khâu báo cáo, không đổi hệ:**
1. **Thêm chỉ số "top-5 có chứa chuỗi đáp án"** bên cạnh `hit@5` theo chunk id: dù chunk nào, chỉ cần văn bản top-5 chứa chuỗi đáp án (`targets`). Cấu hình tốt nhất: 0.812 thay vì 0.687; Plain RAG 0.667 thay vì 0.549. Là cận trên (chuỗi đáp án có thể nằm trong chunk nói về thời kỳ khác).
2. **Báo cáo thêm trên 362 câu "sạch"** (bỏ 37 câu có chunk đáp án nằm sau thời điểm hỏi): không loại câu khỏi bộ, chỉ thêm một cột. Đã tính:

   | Cấu hình | `hit@5` toàn bộ (399) | `hit@5` bỏ 37 câu (362) | `mrr` toàn bộ | `mrr` bỏ 37 câu |
   |---|---|---|---|---|
   | Plain RAG dense | 0.549 | 0.566 | 0.339 | 0.352 |
   | Cơ chế 1 · dense · stored · tắt | 0.622 | 0.685 | 0.418 | 0.460 |
   | Cơ chế 1 · dense · unknown decay 0.1 · `t_unknown` 0.1 | 0.687 | 0.757 | 0.444 | 0.489 |

   Khoảng cách giữa Cơ chế 1 và Plain RAG rộng hơn trên 362 câu sạch (+0.19 so với +0.14 ở `hit@5`), vì bộ lọc không còn bị phạt vì các nhãn lệch.

- Về lâu dài: dựng nhãn bằng chứng theo thời gian (chunk chứa đáp án **và** có thời kỳ bao `t_req`); cần LLM hoặc đọc tay, ngoài phạm vi hiện tại.

### Đề xuất 6: đợt 6 (đã có trong kế hoạch)

Quét `λ`, `W1/W2` trên mẫu `D/train` (loại 35 câu mượn). Kỳ vọng nhỏ (các cấu hình dense chênh nhau dưới 0.012) nhưng cần có để có con số chốt cho luận văn.

### Đề xuất 7: gom chunk cùng trang theo thời gian, thay cho chunk liền kề theo chỉ số

- **Hiện đã có chunk liền kề** (`--neighbors`, `expansion.py`): với mỗi chunk trong top-K lấy thêm chunk có chỉ số ±`window` cùng tài liệu, vẫn qua bộ lọc cứng, đưa vào `RetrievalResult.neighbors` làm ngữ cảnh. Nó **không đổi xếp hạng** và **không dùng thời gian** (chỉ dùng vị trí đoạn).
- Đo ở bộ thật (`eval/05` mục 6.5): `ctx_hit` tăng +0.09 (0.679 lên 0.772; cứu thêm 37 câu), ngữ cảnh tăng từ 5 lên 8.2 chunk trung bình. Nhưng với **12 câu có nhiều chunk đúng** (`n_multi_gold`), tỉ lệ có đủ mọi chunk đúng trong ngữ cảnh **không đổi** (0.167, tức 2/12): chunk liền kề không gom được các đoạn rải rác trong cùng một trang.
- Đề xuất: **mở rộng theo thời gian**, không theo vị trí. Với mỗi trang trong top-3 trang (theo chunk tốt nhất), lấy thêm tối đa `m` chunk **cùng trang** có khoảng thời gian giao `Q` (cùng cơ chế chồng lấn ở đề xuất 1), xếp theo `Final`. Chunk liền kề theo chỉ số vẫn có thể giữ cho trường hợp đáp án vắt qua đoạn.
- Vì sao hợp lý: lỗi chính là "đúng trang, nhầm thời kỳ" (`eval/05` mục 5); kéo cả trang vào và lọc theo thời gian đi thẳng vào chỗ đó, và không phụ thuộc đoạn nằm cạnh nhau hay không.
- Giới hạn: 12/400 câu multi-gold là mẫu rất nhỏ để đo lợi ích; chi phí là ngữ cảnh dài hơn (token). Liệt kê **mọi** sự việc của một thực thể theo thời gian là việc của Cơ chế 2 (timeline), không nên ôm vào Cơ chế 1.
- Chi phí đo thử (kho thật, Qdrant cục bộ): lấy cả trang bằng `get_chunks` trên 100 id mất **khoảng 2 ms** (p95 3 ms), một trang trung bình 34 chunk (trung vị 25, tối đa 100). Top-5 chỉ có **một trang ở 61% câu, hai trang ở 22%, ba trở lên ở 17%**, nên "top-3 trang" thực tế thường là 1–2 truy vấn. Không embedding, không LLM. Qdrant từ xa sẽ chậm hơn theo độ trễ mạng; payload index chỉ có 4 trường nên truy theo id (`Doc#0` đến `Doc#99`), như `neighbor_ids` đang làm, thay vì lọc theo `page_id`.
- Hai cách mở rộng độc lập, có thể dùng riêng hoặc ghép: (A) chunk liền kề theo chỉ số (đã có, không dùng thời gian); (B) chunk cùng trang giao khoảng hỏi (đề xuất này). Cần so theo `ctx_hit` trên số chunk thêm vào (`ctx_size_mean`), không theo `hit@5`.
- Đã đo ở A (lưới 32 kịch bản mỗi bộ, `eval/05` mục 6.5): không đổi `hit@5` và `mrr` (ở cấu hình tốt nhất vẫn 0.687 và 0.444), chỉ tăng `ctx_hit` từ 0.687 lên 0.769 (cửa sổ 1, 8.2 chunk trong ngữ cảnh) và 0.789 (cửa sổ 2, 10.4 chunk); trên 12 câu nhiều chunk đúng, `ctx_multi_all_hit` 0.167 lên 0.250 chỉ ở cửa sổ 2.
- Chi phí thời gian đo thử của B: `retrieve()` hiện mất khoảng **19 ms**/câu, lấy tối đa 3 trang thêm **3.4 ms** (1.6 trang/câu), tức **+18% của bước truy xuất**; so với cả luồng (Profiler gọi LLM khoảng 1 giây, rồi sinh câu trả lời) thì dưới 0.5%.

### Đề xuất 8: một chunk nhiều khoảng thời gian

- **Vấn đề**: ingestion gán một `[start, end]` cho cả đoạn. Đoạn chứa nhiều sự việc ở nhiều thời điểm (danh sách chức vụ, tiểu sử tóm tắt) chỉ khớp một thời điểm. Từ đọc tay 37 câu bị lọc (`eval/05` mục 7): khoảng 6 câu nhóm C1 và vài câu nhóm B thuộc loại này.
- **Cách làm đề xuất** (không đụng bộ lọc đã index):
  1. Prompt ingestion yêu cầu LLM liệt kê **từng sự việc có ngày** trong chunk: `spans: [{start, end, evidence}]`, mỗi cái kèm câu bằng chứng ngắn (giống `ongoing_evidence` hiện có).
  2. `start_time` đã index (một trường trong 4 trường payload cho phép) lưu **mốc bắt đầu sớm nhất** của mọi khoảng; bộ lọc cứng giữ nguyên `start_time <= qe`, không cần index mới.
  3. Danh sách khoảng đầy đủ nằm trong payload (không index); `Temporal` của chunk = **điểm tốt nhất trong các khoảng** (khoảng nào giao khoảng hỏi thì 1.0), tính bằng Python như bây giờ.
  4. `end_status` tính theo từng khoảng.
  Phương án khác đã cân nhắc: tách chunk theo sự việc (làm đổi embedding và chunk id, nặng hơn); đóng thành khoảng bao `min start` đến `max end` (dễ, nhưng giao nhau sai với nhiều thời điểm, xem bảng "khi nào giao nhau chưa đủ").
- **Kỳ vọng thực tế thấp hơn tưởng**: nhiều ca nhóm C1 **không có ngày cho từng sự việc trong văn bản**: danh sách giám đốc cũ của Office for Foreign Relations chỉ ghi "2014-2018" cho người cuối; Goryachkina chỉ ghi "at the age of 13". Nhiều khoảng không giúp được các ca này (cần suy ra từ tuổi hoặc kiến thức ngoài). Ca có thể được cứu: đoạn có ngày hoặc mốc tương đối rõ cho từng sự việc (vd Senate of Canada Building "ga tàu đến 1966, sau đó cơ quan chính phủ đến 2018", Jiminy Cricket "Cliff Edwards đến những năm 1960"). Ước lượng thô: 3–6 trong 37 câu bị lọc.
- **Chi phí**: đổi schema chunk, prompt ingestion, scoring và test; **nạp lại toàn kho** (khoảng 330 lô LLM, vì prompt đổi nên cache trượt; Gemini 3.5 một ngày đủ); chạy lại Profiler không cần.
- **Rủi ro**: LLM bịa khoảng; output dài hơn nên có thể tăng lỗi định dạng; cần giới hạn số khoảng mỗi chunk (vd 5).

## Thứ tự đề xuất, và vì sao

| Bước | Việc | Cần gọi LLM | Ghi chú |
|---|---|---|---|
| 1 | Đề xuất 3 (`decay_from: end`) và đề xuất 5 (chỉ số chuỗi đáp án, tách 37 câu có chunk đáp án nằm sau thời điểm hỏi) | Không | Rẻ, đo ngay; cho biết phạt từ `start` là lỗi lớn đến đâu và giúp đo công bằng các bước sau |
| 2 | Đề xuất 1 (khoảng + chồng lấn), có đề xuất 3 làm phần "không giao nhau" | Có (Profiler 400 câu) | Thay đổi lớn nhất nhưng đúng gốc; là hướng đã được chọn thay cho dung sai cố định (đề xuất 2) |
| 3 | Đề xuất 7 (gom chunk cùng trang theo thời gian) | Không | Dựa vào cơ chế chồng lấn ở bước 2 |
| 4 | Đề xuất 4 (reranker, MiniLM-L-6 trước, bge-reranker-v2-m3 sau) | Không (cross-encoder) | Đo trên cấu hình đã sửa thời gian, để biết dư địa còn lại |
| 5 | Đề xuất 6 (quét `λ`, `W1/W2` trên D/train) | Không | Cuối cùng, sau khi cấu trúc điểm đã ổn định |
| (bỏ) | Đề xuất 2 (dung sai cố định) | Không | Chỉ dùng nếu bỏ qua đề xuất 1 |

**Lý do của thứ tự** (nguyên tắc: làm việc rẻ và cho nhiều thông tin trước; việc đổi cấu trúc lớn sau khi biết còn thiếu gì; chỉnh tham số cuối cùng):

1. **Bước 1 đầu tiên vì rẻ nhất và quyết định các bước sau.** Đề xuất 3 chỉ là một nhánh trong `scoring.py` và một cờ trong `evaluate.py`, đo được trên cả hai bộ trong vài phút, không gọi LLM. Nó trả lời đúng một câu hỏi: trong 66 câu chunk đúng "đã kết thúc trước `t_req`", bao nhiêu câu hết lỗi chỉ nhờ phạt từ `end`? Nếu nhiều, phần lỗi biên và lỗi `end` hơi sớm đã được xử lý mà chưa cần đổi Profiler. Đề xuất 5 chỉ đổi cách báo cáo nhưng cần có trước để đo công bằng mọi bước còn lại (hiện `hit@k` theo chunk id lệch 12 điểm so với chuỗi đáp án).
2. **Bước 2 (khoảng) làm sau bước 1** vì nó tốn công nhất (đổi schema, prompt, lọc, điểm, chạy lại Profiler 400 câu, mất cache) và phần "không giao nhau" của nó dùng chính công thức của đề xuất 3. Làm sau bước 1 thì biết trước còn bao nhiêu lỗi để nó giải quyết, tránh đổi nhiều thứ cùng lúc rồi không rõ cái nào có tác dụng. Tôi vẫn xếp nó trước reranker vì nó sửa **gốc** (câu hỏi chỉ có một điểm trong khi chunk có khoảng).
3. **Bước 3 (gom chunk cùng trang) sau bước 2** vì nó dùng chung phép chồng lấn.
4. **Reranker ở bước 4, không phải đầu tiên** dù rẻ: nếu đặt trước, nó học trên một công thức thời gian còn lỗi, nên dư địa đo được bị lẫn với lỗi thời gian. Cross-encoder cũng không hiểu thời gian, nên chỉ có nghĩa khi phần chọn thời kỳ đã ổn.
5. **Quét tham số cuối cùng** vì `λ` và `W1/W2` phụ thuộc cấu trúc điểm; quét trước rồi đổi cấu trúc thì phải quét lại.

## Dự định tiếp theo (ghi 2026-10-21, sau lưới cross-encoder đầu tiên)

Lưới cross-encoder đầu tiên chỉ chạy trên MỘT cấu hình thời gian nền (`w1` 0.7, `w2` 0.3, `unknown_decay` 0.05, `decay_from end`, `t_unknown` 0.1, `point`, kho v3, nhóm `final` top-20). Cần làm sau khi lưới hiện tại và lưới Plain RAG + cross-encoder xong:

1. ~~**Bỏ bớt điểm thời gian có được không?**~~ **Đo một phần (chẩn đoán, `eval/05` mục 6.19):** bỏ `Temporal` ở bước cuối làm `mrr` giảm 0.06 đến 0.07 ở cả 3 model; `w2` = 0 giảm 0.067 `mrr`; chưa đo `w2` = 0.5. Dự định gốc: Với cross-encoder tốt nhất, quét `w2` ∈ {0, 0.15, 0.3, 0.5} (`w1 = 1 - w2`). `w2` = 0 nghĩa là chỉ còn lọc cứng + cross-encoder. Nếu bằng `w2` = 0.3 thì điểm `Temporal` thừa.
2. **Cấu hình thời gian kết hợp với cross-encoder:** 3 `end_mode` (`stored`, `unknown_decay` 0.05, `decay` 0.1) × `decay_from` (`start`, `end`).
3. **Nhãn ingest:** kho v1 so với v3 (và mốc suy luận `se_pe_ns`, `e_ns`) khi có cross-encoder, vì lọc cứng và điểm thời gian vẫn phụ thuộc chất lượng nhãn.
4. **Thang điểm:** thử chuẩn hóa điểm cross-encoder khác min-max (softmax, hoặc logit thô) vì chuẩn hóa min-max trên 20 ứng viên khuếch đại chênh lệch nhỏ.
5. **Độ trễ:** đo thời gian rerank cho từng model (L6, L12, bge-base, bge-v2-m3) để chọn model cho agent thật.
6. **Chọn cấu hình trên tập valid/test sạch** (decisions/08) trước khi báo cáo; số hiện tại là cận trên.
7. ~~**BM25 khi có cross-encoder:**~~ **Đã khảo sát** (`eval/05` mục 6.19, chẩn đoán trên bộ thật): BM25, top-30/50 và các thang chuẩn hóa khác không giúp; nhãn v1 kém hơn v3 khi có cross-encoder. Dự định gốc: `sparse_weight` ∈ {0.25, 0.5, 1.0} với cross-encoder tốt nhất, thêm nhóm chấm lại top-30/50. Độ phủ ứng viên top-50: dense 0.900, BM25 0.8675, gộp 0.900, nên dự đoán ít giúp.
8. **Đo đầu-cuối EM/F1** với bộ sinh cố định, so Plain RAG + cross-encoder và Cơ chế 1 + cross-encoder (cần LLM).

## Chưa biết / cần kiểm tra

- Bao nhiêu trong 66 câu có `end` do LLM gán thật sự sai (cần đọc từng chunk). Tôi mới đọc 8 mẫu dưới 1 năm và 6 mẫu rải rác; kết luận "một số sai, một số hợp lý" chưa là tỉ lệ.
- Đề xuất 3 có thể làm giảm điểm một số câu vốn đúng nhờ phạt nặng chunk cũ; chỉ đo mới biết.
- Cross-encoder có xếp nhầm thời kỳ nhiều hơn công thức hiện tại hay không (xem điểm yếu ở đề xuất 4).

## Ghi chú 2026-10-24: thí nghiệm Cơ chế 1 cộng graph

Sau khi Cơ chế 2 có nút theo từng sự kiện (xem [`10`](10_TIMELINE_GRAPH_AND_VECTOR_LINK.md)), thử thêm graph vào Cơ chế 1 ở ba vị trí: trước truy xuất (thu hẹp hoặc nâng điểm theo `chunk_ids` của nút đang hiệu lực ở `T_req`), sau khi lấy top-chunk (tính lại điểm thời gian theo khoảng của nút, tức đề xuất 8 ở trên), và hợp hai nguồn. Cơ chế 1 hiện tại không đổi; so bằng `mrr`, `hit@5`, `ans_valid@5`, `leakage_rate` và số câu "lỗi lọc" trên valid, giữ `test_clean` cho lần chốt cuối.
