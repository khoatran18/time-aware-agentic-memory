# 11. Chỗ chưa khớp giữa 09 và 10 về Evolution và Falsehood

**Ngày:** 2026-11-02. **Trạng thái:** đề xuất, chưa chốt; chưa sửa `09` và `10` (chỉ thêm một dòng link ở mục "Liên quan" của mỗi file). Phát hiện khi đọc lại hai file để lập kế hoạch đánh giá Cơ chế 3 (`docs/research/benchmarks_for_comparison/03_EVALUATION_PLAN_BY_MECHANISM.md`).

## Bối cảnh

Bất biến của đồ án (`design/01`, `CLAUDE.md`): **Evolution ≠ Falsehood.**
- Evolution: trạng thái từng đúng rồi đổi. Đóng bằng `end_time`, vẫn trả lời được câu hỏi về quá khứ.
- Falsehood: thông tin sai từ đầu. Đặt `invalidated_at`, bị lọc cứng khỏi Cơ chế 1, câu hỏi lịch sử có cảnh báo.

`09` quyết cách xử lý chunk khi trang Wikipedia đổi; `10` quyết cách cập nhật nút graph khi chunk đổi. Hai file nối với nhau (10 nhận đầu ra của 09) nhưng ở mức tách Evolution khỏi Falsehood thì chưa khớp.

## Ba chỗ lệch

### Lệch 1: `invalidated_at` bị dùng cho mọi chunk bị thay (09)

- `design/01`: `invalidated_at` nghĩa là "sai từ gốc".
- `09`, bảng "Các trường hợp chunk khi cập nhật" (15 trường hợp) và đoạn ngay sau bảng: chunk "không còn thuộc bản hiện tại của trang" đều bị `invalidated_at` kèm lý do `factual_change`, `recut`, `removed`.
- Lý do `09` ghi: truy xuất lọc cứng `invalidated_at IS NULL` trong Qdrant (trường đã có payload index), còn `end_time` chỉ giảm điểm nên không loại được chunk đã bị thay. `09` tự thừa nhận ngữ nghĩa lệch so với `design/01`.
- **Hậu quả:** chunk Evolution đã bị thay cũng bị loại khỏi truy xuất, kể cả khi hỏi về quá khứ. Trên Wikipedia điều này ít lộ ra, vì lịch sử nằm ngay trong nội dung bài và chunk mới vẫn chứa giá trị cũ (`09`, mục "Điều chỉnh về bản chất của thay đổi"). Nghĩa là chỉ số **Historical retention** có thể trông tốt nhờ đặc điểm dữ liệu chứ không nhờ cơ chế, và sẽ vỡ ở nguồn không có đặc điểm đó.
- Trong cùng `09`, phần "Thiết kế tổng quát cho nguồn không có lịch sử" (luồng có nhánh LLM phân loại) lại tách đúng: Evolution là `end_time` + `SUPERSEDES`, Falsehood là `invalidated_at` + `CORRECTS`. Luồng chính (bước 4 và 5) cũng có bước phân loại. Vậy `09` đang có hai cách nói.

### Lệch 2: `10` không nhận nhãn phân loại của 09 và không tạo cạnh `SUPERSEDES` / `CORRECTS`

- `09`, mục "Lưu trữ và Graph": cạnh `SUPERSEDES` / `CORRECTS` do phân loại ở bước 4 tạo ra.
- `10`, mục "Cập nhật khi đoạn đổi": đầu vào chỉ là "chunk cũ bị `invalidated_at`" và các cửa sổ mới; diff chỉ là gợi ý; **không nhận lý do** (`factual_change` / `recut` / `removed`) hay nhãn tiến hóa/đính chính. Cạnh duy nhất được nhắc là `TIẾP_THEO` (dựng lại, không lưu cố định).
- Hành động trên nút chỉ có `keep` / `modify` / `delete`:
  - `modify` sửa tại chỗ (giữ `node_id`), nên **ghi đè** giá trị cũ. Với đính chính (ví dụ 1569 sửa thành 1599) thì giá trị sai biến mất, không còn bản ghi, không có cạnh `CORRECTS`.
  - `delete` chỉ "đánh `status` bị xóa". Không phân biệt: đóng `end_time` (Evolution), vô hiệu (Falsehood), hay đoạn chỉ bị lược khỏi bài.
  - Giá trị của `status` ngoài "bị xóa" chưa được định nghĩa.

### Lệch 3: cách diễn đạt và tên trường (nhỏ)

- `09`, mục "Lưu trữ và Graph": "xóa các nút có `pointer_chunk_id` trỏ tới chunk bị thay, trích lại bộ ba cho chunk mới". Đó gần giống phương án đối chứng (ablation) của `10`, trong khi mặc định của `10` là `keep` / `modify` / `delete` với nút cũ đưa vào LLM. `09` có câu trỏ sang `10` cho chi tiết, nên có thể coi `10` là chuẩn, nhưng câu tóm tắt trong `09` dễ gây hiểu nhầm.
- Tên trường: `09` (và `design/01`) dùng `pointer_chunk_id` / `Chunk_ID` (một id); `10` dùng `chunk_ids` (danh sách, vì một sự kiện có thể vắt hai chunk).
- `09` có đoạn nói phân biệt tiến hóa với đính chính ở mức phiên bản "gần như không còn ý nghĩa" với Wikipedia, trong khi luồng chính vẫn có bước phân loại. Hai ý này không mâu thuẫn nếu hiểu bước phân loại chạy trên cặp (câu cũ, câu mới), nhưng nên ghi rõ.

## Hướng sửa đề xuất

Không sửa ngay; chốt hướng rồi mới đổi `09` và `10`.

**A. Bảng ánh xạ từ nhãn phân loại sang chunk, nút và cạnh** (mỗi cặp câu cũ/mới thuộc đúng một nhãn):

| Nhãn (bước 4 của `09`) | Chunk cũ | Nút cũ | Cạnh |
|---|---|---|---|
| Sửa văn phong | Thay bằng chunk mới kế thừa nhãn thời gian; chunk cũ không còn hiện hành (không phải sai) | `keep` | Không |
| Thông tin mới (thêm) | Giữ | Thêm nút mới | Không |
| **Tiến hóa** | Không còn hiện hành, **vẫn trả lời được câu hỏi quá khứ**; đóng `end_time` | Đóng `end_time`, thêm nút mới | `SUPERSEDES` |
| **Đính chính** | `invalidated_at` | Giữ bản ghi nhưng đánh vô hiệu (không ghi đè), thêm nút đúng | `CORRECTS` |
| Đoạn bị xóa | **Chưa quyết** (xem dưới) | Chưa quyết | Không |

**B. Tách "không còn hiện hành" khỏi "sai"** ở lớp lọc. Hai lựa chọn:
- Lựa chọn 1: giữ `invalidated_at` chỉ cho Falsehood; thêm trường `superseded_by` (hoặc cờ `is_current`) để loại chunk Evolution khỏi truy vấn "hiện tại" mà vẫn giữ cho truy vấn lịch sử. **Cái giá:** `CLAUDE.md` giới hạn payload index ở 4 trường (`start_time`, `invalidated_at`, `domain_features.domain`, `domain_features.country`); thêm trường lọc cứng nghĩa là mở rộng danh sách này và cần ghi lý do.
- Lựa chọn 2: giữ nguyên như `09` hiện nay (một trường, nhiều lý do), chấp nhận Historical retention chỉ cứu được nhờ nội dung bài. Ghi rõ đây là giới hạn và **không** tuyên bố cơ chế bảo toàn lịch sử trên dữ liệu Wikipedia.

Mình nghiêng về lựa chọn 1 vì nó là cái duy nhất khớp bất biến; lựa chọn 2 rẻ hơn nhưng làm chỉ số Historical retention mất ý nghĩa.

**C. Sửa `10`:** thêm vào bước 2 nhãn phân loại và lý do từ `09`; thêm hành động cho nút `close` (đóng `end_time`, Evolution) và `invalidate` (Falsehood, giữ bản ghi, tạo `CORRECTS`); chỉ dùng `modify` cho sửa văn phong hoặc sửa không đổi nghĩa; định nghĩa tập giá trị của `status`.

**D. Câu hỏi chưa quyết: đoạn bị xóa khỏi bài (`removed`).** Bị lược không có nghĩa là sai. Cần chọn: giữ chunk cho truy vấn lịch sử (đóng `end_time` bằng ngày bản mới), hay loại hẳn. Gợi ý: đóng `end_time`, không `invalidated_at`, trừ khi có nhãn đính chính.

## Việc cần kiểm thêm

1. **Historical retention thực sự phụ thuộc bao nhiêu vào nội dung bài.** Đo trên bộ S0/S1: trả lời câu hỏi quá khứ (loại 2) khi chỉ có chunk mới (cố tình loại chunk cũ khỏi kho) và khi có cả chunk cũ. Chênh lệch chính là phần lịch sử mà cơ chế giữ được.
2. **Tỉ lệ đính chính thật** trong dữ liệu (chưa đo; mẫu 40 ở `eval/06` cho khoảng 10–15% ứng viên theo comment).
3. Kiểm lại sau khi chốt: bảng 15 trường hợp của `09` cần thêm cột "nhãn" để khớp bảng ánh xạ ở mục A.

## Việc cần làm với dữ liệu của ba cơ chế

Ghi 2026-11-02, theo quyết định: **Cơ chế 1: dữ liệu chính là `real` (TimeQA) cộng mẫu sinh thêm; Cơ chế 2: không dùng bộ `timeline_gold` sinh từ script (xem mục 2.0), bộ thay thế chưa chọn; Cơ chế 3: dùng HoH trước rồi sinh thêm.** Chi tiết bộ dữ liệu, đối thủ cài lại và chỉ số ở [`03_EVALUATION_PLAN_BY_MECHANISM.md`](../research/benchmarks_for_comparison/03_EVALUATION_PLAN_BY_MECHANISM.md). Cột "Phụ thuộc" cho biết việc nào phải xong trước.

### Nguồn gốc các bộ dùng làm bộ chính

| Bộ | Từ đâu | Có phải bộ công bố không |
|---|---|---|
| `real` (1,394 câu; tune 595 / valid 399 / test 400) | Lấy từ **TimeQA** (Chen và cộng sự, NeurIPS 2021, [arXiv 2108.06314](https://arxiv.org/abs/2108.06314), BSD-3), bản đã ghép thêm thông tin trang ở `dataset/full_dataset/` | Có, chọn tập con của bộ công bố |
| `timeline_gold` (1,241 câu, 1,019 reliable) | **Tự dựng bằng mã** (`python scripts/build_timeline_gold.py --subset real`, module `tam.evaluation.timeline_gold`) từ chú thích câu hỏi `hard` của TimeQA, gộp theo ô (trang, quan hệ); không gọi LLM | **Không**, không có bài báo; chỉ nguồn chú thích là TimeQA. Mô tả ở `eval/08`. **Quyết 2026-11-02: không dùng làm bộ chính, lý do ở mục 2.0** |
| S0/S1 (bộ Cơ chế 3 tự dựng) | Sẽ dựng từ lịch sử Wikidata + bản Wikipedia cũ/mới của các trang TimeQA | Không; chưa dựng |

### Cơ chế 1 (Temporal Retrieval)

| # | Việc | Phụ thuộc |
|---|---|---|
| 1.1 | Phân tích 71 câu `ans_valid@5 = 0` và sửa nhãn "± 95%" (việc mở từ trước) | Không |
| 1.2 | Chốt chính sách khi câu hỏi không nêu mốc (ưu tiên mới nhất hay hỏi lại) | Không |
| 1.3 | Sinh mẫu ~100 câu: thời gian tương đối (~30, cố định `T_now`), mức ngày (~30), không nêu mốc (~20), `end_time` còn mở (~20). Báo riêng, không trộn vào số chính | 1.2 |
| 1.4 | Xin quyền Hugging Face cho TempRAGEval, tải `test.csv`, thu hẹp kho 33.1M chunk, gán `start_time` | Bạn xin quyền |
| 1.5 | Cài đủ logic MRAG (hai cấu hình), TA-RAG; DyG-RAG nếu đã dựng cho Cơ chế 2 | Chốt cách tách MC/TC cho MRAG trên `real` |
| 1.6 | Ablation: chỉ lọc cứng, chỉ xếp lại, không bge, bỏ nửa đời | Không |
| 1.7 | Thí nghiệm "Cơ chế 1 + graph" (ba cách ghép ở `10`) | Có graph (2.3 hoặc 2.4) |
| 1.8 | Chạy bộ ngoài đúng một lần sau khi khóa cấu hình | 1.4 |

### Cơ chế 2 (Timeline Summarization)

| # | Việc | Phụ thuộc |
|---|---|---|
| 2.0 | **Quyết 2026-11-02: không dùng bộ sinh từ `scripts/build_timeline_gold.py`** (`dataset/eval/timeline_gold_real.json`, `timeline_questions_real.jsonl`). Chọn bộ thay thế (xem bên dưới bảng) | Bạn quyết bộ thay thế |
| 2.1 | **Tạm dừng** (dựa trên bộ cũ). Phần làm tay theo `eval/08`: thời lượng (~30 sự kiện), khoảng trống (~30 ô), precision (~100 nút), câu ghép hai ô (vài câu), kiểm oracle (~40 ô) | Không |
| 2.2 | **Tạm dừng** đến khi có bộ thay thế; ý tưởng giữ nguyên (graph oracle so với vector top-k). Chạy bước go/no-go: graph oracle so với vector top-k (k = 3, 5, 10, thích nghi), chunk đáp án và cả trang, trên `tune`/`valid` (không dùng `test_clean`); thêm prompt cho nhóm câu cấu trúc vào sổ prompt (`decisions/03`) | Không |
| 2.3 | **Tạm dừng.** Nếu oracle hơn vector ở ít nhất một loại có ý nghĩa: trích sự kiện bằng LLM ~20 ô rồi toàn bộ (tầng 1) | 2.2 |
| 2.4 | Cài đủ logic DyG-RAG, TG-RAG | Không |
| 2.5 | Bộ ngoài: ECT-QA (tách 261 câu unanswerable, cố định `T_now` cho 201 câu thời gian tương đối); TLQA nếu làm (lấy trang Wikipedia của 5,711 thực thể); ADQAB sau cùng | Không |
| 2.6 | **Tạm dừng.** Chốt trên `test_clean` một lần | 2.2, 2.3 |

Lưu ý (áp dụng cho bộ cũ, chỉ để biết): `test_clean` chiếm 55% số câu của `timeline_gold` (677/1,241), valid chỉ có 31 ô (150 câu reliable), nên chọn phương pháp ở valid khó đạt ngưỡng 2 sai số chuẩn; báo rõ.

#### 2.0. Vì sao không dùng bộ sinh từ script, và còn lại gì

Quyết ngày 2026-11-02. Bộ cũ gồm `dataset/eval/timeline_gold_real.json` và `timeline_questions_real.jsonl` (1,241 câu, 1,019 reliable), dựng bằng `scripts/build_timeline_gold.py` / `tam.evaluation.timeline_gold`, mô tả ở `eval/08`. Lý do:

1. **`gold_chunk_ids` sai (lỗi mã).** `src/tam/evaluation/timeline_gold.py` dòng 64 gọi `gold_paragraph_indices(spans, [ans["from"]], [ans["end"]])`. `ans["from"]` và `ans["end"]` là vị trí *trong đoạn* (ví dụ 30 đến 43), còn hàm cần vị trí *trong toàn trang* (ví dụ 10968 đến 10981, trường `row["from"]` / `row["end"]` mà mã gold của Cơ chế 1 ở `splits.py` và `subset.py` đang dùng). Đo trên 800 đáp án của bộ `real` (2026-11-02): đoạn tìm ra chứa chuỗi đáp án ở **191/800 (23.9%)** theo cách của script, **793/800 (99.1%)** theo cách của Cơ chế 1. Ví dụ ô (1. FC Köln, head coach): TimeQA ghi đáp án Anfang ở đoạn 26, bộ cũ ghi `#0`. Hệ quả: số token "chunk đáp án" và `event_coverage` ở tầng 2 sai. Các số ở `eval/08` ("graph nhỏ hơn chunk đáp án ở 95 đến 100% câu", độ phủ vector top-k 0.62 / 0.77 / 0.90) **không dùng làm bằng chứng**. Đáp án chuẩn, giá trị, thứ tự và mốc của graph oracle không bị ảnh hưởng vì lấy từ `targets` / `time_start` / `time_end`.
2. **Gold không đầy đủ.** Chỉ có sự kiện mà TimeQA từng đặt câu hỏi; 22.5% ô thủng (`q_index` không liên tục), 222 câu không `reliable`; precision của dòng thời gian không đo được tự động. Ô chỉ có một sự kiện thì không sinh câu (13 ô).
3. **Câu hỏi theo mẫu cố định, không phải tóm tắt.** Đầu ra là đáp án có cấu trúc (danh sách, số, một giá trị); kiểm được độ phủ sự kiện, thứ tự, số lượng, không kiểm được chất lượng viết tóm tắt.
4. **Không có bài báo** đứng sau bộ này; nguồn duy nhất là chú thích của TimeQA.

Xử lý: giữ nguyên mã và dữ liệu trong repo (không xóa, không sửa), chỉ **không dùng** làm bộ chính hay trích số liệu từ nó. Ý tưởng đo ba tầng và cổng go/no-go (graph oracle so với vector top-k) ở `eval/08` và `10` vẫn giữ, chỉ đổi bộ dữ liệu.

**Bộ thay thế cho Cơ chế 2: chưa chọn.** Các phương án:
- (a) **ECT-QA** làm bộ chính: có sẵn kho, câu hỏi, đáp án, `evidence_list`; mốc theo quý; miền tài chính; cần tách 261 câu unanswerable và cố định `T_now` cho 201 câu thời gian tương đối.
- (b) **TLQA**: gần bài toán nhất (liệt kê chức vụ/đội kèm khoảng năm), nhưng phải lấy trang Wikipedia của 5,711 thực thể để dựng kho; gold chỉ là infobox, ~51% tên khớp nguyên văn với evidence.
- (c) **Dựng bộ mới trên trang TimeQA bằng cách khác** (ví dụ gold từ Wikidata + kiểm tay, hoặc LLM trích rồi kiểm tay), tốn công hơn nhưng cùng miền với bộ chính.
- (d) Kết hợp (a) hoặc (b) làm bộ ngoài và (c) làm bộ chính.

Sau khi chọn: cập nhật mục 0 và mục 2.1 của `03_EVALUATION_PLAN_BY_MECHANISM.md` (hiện vẫn ghi `timeline_gold` là bộ chính của Cơ chế 2) và bỏ dấu "Tạm dừng" ở 2.1, 2.2, 2.3, 2.6.

### Cơ chế 3 (Conflict Resolution)

| # | Việc | Phụ thuộc |
|---|---|---|
| 3.1 | **Chốt decision 11** (các mục A đến D ở trên): `invalidated_at` nghĩa là gì, bộ lọc đặt ở đâu, đoạn bị xóa xử lý ra sao | Bạn quyết |
| 3.2 | Kiểm HoH: đọc tay ~40 dòng `outdated_infos` xem lẫn đính chính bao nhiêu; tải mẫu ~1,000 câu (cố định seed), dựng kho từ `document` / `evidence`, `start_time = last_modified_time` | Không |
| 3.3 | Dựng S0/S1 từ Wikidata: ~150 cặp (ưu tiên P54, P39, P108, P488) và các loại câu 1, 2, 3, 5, 6 (~680 câu): hiện tại, lịch sử, chuyển tiếp, đối chứng không đổi, thăng tiến | Chốt chính sách ở 1.2 nếu liên quan |
| 3.4 | Dựng Falsehood (loại 4): **thật** (lọc tay trong 961 ứng viên của 204 trang đã crawl, kỳ vọng vài chục câu) và **tổng hợp có nhãn** (~100 câu: lấy chunk đúng, thay bằng giá trị có thật nhưng ở thời điểm khác của cùng quan hệ, thêm nhiễu văn phong và đoạn mới để diff không quá lộ, kiểm closed-book). Báo riêng, không trộn vào số chính | 3.1, 3.3 |
| 3.5 | (Đề xuất, chưa chốt) Thêm loại câu thứ 7 "khoảng chồng lấn" (cũ [1500, 1520], mới [1505, 2025]); cần ontology khai báo quan hệ đơn trị hay đa trị | 3.1 |
| 3.6 | Baseline: Plain RAG, Replace-all, Keep-all-snapshots; đối thủ cài đủ logic: khung LongMemEval, VersionRAG; (đề xuất) Zep/Graphiti và Mem0 làm baseline "một trục" / "ghi đè" | Không |
| 3.7 | Bộ ngoài: FactConsolidation (cả 8 ngữ cảnh), LongMemEval `knowledge-update` (78 câu), VersionQA, Conflicts (Freshness 62 + No conflict 161) | Không |
| 3.8 | Ablation diff: có diff và không diff (so hash chunk hoặc LLM so cặp theo nghĩa), cùng S0 và S1 cho mọi baseline; chỉ dùng diff lúc nạp | 3.3 |
| 3.9 | Đo Historical retention khi cố tình loại chunk cũ khỏi kho (xem "Việc cần kiểm thêm" mục 1) | 3.3 |

### Việc chung

| # | Việc | Ghi chú |
|---|---|---|
| C.1 | Chốt chuyển DyG-RAG sang Cơ chế 2 trong `01` và `02` của `benchmarks_for_comparison` (hiện xếp Cơ chế 1) | Bạn quyết |
| C.2 | Mọi bộ dựng phải cố định seed; `test_clean` chạy một lần; bộ ngoài không dùng để tune | Quy tắc đã chốt |
| C.3 | Chi phí LLM: nút thắt là hạn mức (Gemini ~500 request/ngày, Gemma 30 RPM / 16K token mỗi phút), nên chạy nền nhiều ngày; DyG-RAG và TG-RAG nặng nhất | Ước lượng ở `02` mục chi phí, chưa đo |
| C.4 | Nhãn gán cho bộ tự dựng phải lấy từ Wikidata hoặc đọc tay, không từ chính đầu ra của hệ đang đo; edit comment chỉ dùng chọn ứng viên, không dùng làm nhãn duy nhất | Tránh đánh giá vòng tròn |

## Liên quan

- [`09_CONFLICT_RESOLUTION_SCOPE.md`](09_CONFLICT_RESOLUTION_SCOPE.md): bảng các trường hợp chunk, luồng chính, mục "Lưu trữ và Graph".
- [`10_TIMELINE_GRAPH_AND_VECTOR_LINK.md`](10_TIMELINE_GRAPH_AND_VECTOR_LINK.md): mục "Cập nhật khi đoạn đổi".
- [`../research/benchmarks_for_comparison/03_EVALUATION_PLAN_BY_MECHANISM.md`](../research/benchmarks_for_comparison/03_EVALUATION_PLAN_BY_MECHANISM.md): kế hoạch đánh giá, mục 3.5 (các bài đã đọc xử lý Falsehood ra sao).
- Bất biến gốc: `docs/design/01_INITIAL_BASE_DESIGN.md`, `CLAUDE.md` (mục Invariants).
