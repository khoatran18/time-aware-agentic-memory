# Tổng kết: bộ dữ liệu và bài báo để so sánh, theo từng cơ chế

> Ghi 2026-10-31, sau khi tìm khoảng 40 bài/bộ dữ liệu và **tải thử** những bộ chính. Tiêu chí giữ lại: dữ liệu công khai tải được, tiếng Anh, quy mô vừa, chạy lại được. Bộ nào không đạt đã bị xóa khỏi folder, lý do nằm trong cột "Vì sao loại" của từng bảng.
>
> Kết luận chung: **bộ dữ liệu phù hợp thì có cho cả ba cơ chế. Bài báo để đặt số cạnh số thì chưa có**, vì điều kiện thí nghiệm khác nhau chứ không phải vì chỉ số khác nhau (chỉ số thì mình tự tính thêm được, xem mục 4).

## 1. Cơ chế 1: Temporal Retrieval (hỏi tại một mốc)

**Bộ dùng được (theo thứ tự ưu tiên):**
1. **Bộ `real`** (TimeQA, tune/valid/test_clean): bộ chính; đo `hit@k`, `mrr`, `leakage_rate`, EM/F1.
2. **TempRAGEval** (TimeQA + SituatedQA): phụ; có gold chunk nên đo được `hit@k`; phải thu hẹp kho. **Chưa kiểm được dữ liệu**: gated, cần xin quyền Hugging Face.
3. **DyG-RAG / TimeQA** (2,613 câu): phụ; có đáp án nên tự chấm EM/F1 hoặc `contains`, không có `hit@k`.
4. **TEMPO**: phụ, kiểm tổng quát hóa sang miền khác (1,730 câu, nDCG@10 và Recall@100 tính được); đã kiểm tải được, tài liệu không có mốc thời gian.
5. **ChroniclingAmericaQA** (`Bhawna/ChroniclingAmericaQA`, MIT): rất yếu; chỉ dùng 1,272 câu có năm để kiểm "không lọt tương lai" trên văn bản OCR.

Cột "Bài đó đo gì" là chỉ số **bài báo dùng**, không phải giới hạn của bộ dữ liệu: bộ nào có đáp án chuẩn thì mình tự chấm EM/F1 được.

| Bộ / bài | Dữ liệu là gì | Phương pháp của bài (dễ hiểu) | Bài đó đo gì | So số của họ với mình được không, vì sao | Trạng thái | Ghi chú đã kiểm | Vì sao loại (nếu loại) |
|---|---|---|---|---|---|---|---|
| Bộ `real` của đồ án (TimeQA) | Câu hỏi kiểu "Ai là chủ tịch X năm 1995?" trên trang Wikipedia, mỗi câu có đoạn văn đúng (gold chunk) và mốc thời gian. **1,394 câu** (tune 595 / valid 399 / test 400); **có văn bản**: trang Wikipedia đã nạp (203 + 167 + 186 trang), có gold chunk. | Của đồ án: lọc cứng theo thời gian rồi xếp lại có trọng số thời gian, thêm bge-reranker. Không huấn luyện. | `hit@k`, `mrr`, `leakage_rate`, EM/F1 | Đây là bộ của mình, không cần so. | **Chính** | Có gold chunk, có baseline Plain và Plain+bge. |  |
| **TempRAGEval** | Lấy câu hỏi TimeQA/SituatedQA rồi cố ý đổi mốc thời gian hoặc cách hỏi ("trước", "mới nhất"...) để thử xem hệ thống có lấy đúng đoạn theo mốc không. **1,000 câu** (TimeQA 500 + SituatedQA 500); `test.csv` chỉ có câu hỏi và gold evidence (khoảng 470 KB); **văn bản nằm ở kho Wikipedia 12/2021 (33.1M chunk)** tải riêng từ ATLAS, dung lượng chưa rõ. | MRAG (không huấn luyện): LLM tách câu hỏi thành phần nội dung và phần ràng buộc thời gian; lấy đoạn bằng retriever có sẵn; LLM tóm tắt từng đoạn thành một câu; mỗi câu được chấm điểm ngữ nghĩa × điểm thời gian (hàm đường cong theo mốc trong câu); chọn đoạn có câu điểm cao nhất. Sơ đồ ở file `02`. | `ER@k` (đoạn đúng có trong top-k), `AR@k` (đáp án có trong top-k), EM, F1 | **Một phần.** Có bảng từ BM25 đến reranker mạnh với ER@k/AR@k, mình tính lại được. Nhưng kho gốc 33.1M chunk, mình phải thu hẹp nên số tuyệt đối cao giả; chỉ so khoảng cách giữa các hệ cùng kho, nên chạy lại BM25 và reranker trên đúng tập thu hẹp. Chưa kiểm vì dataset gated. | Giữ, phụ | Gold chunk do người gán. **Chưa kiểm được dữ liệu:** dataset gated, tải thử trả 401; bạn cần xin quyền trên Hugging Face (file `test.csv` khoảng 470 KB). | Kho đầy đủ 33.1M chunk nên phải thu hẹp; khi thu hẹp số tuyệt đối cao giả, chỉ so khoảng cách giữa các hệ. |
| **DyG-RAG / TimeQA** | Biến văn bản thành đồ thị các sự kiện có thời gian rồi tìm trên đồ thị, thử trên TimeQA. **2,613 câu** TimeQA; **có văn bản**: 3,159 bài Wikipedia, khoảng 1.82M token (ước lượng khoảng 8 MB chữ, chưa tải). | Dùng LLM (Qwen2.5-14B) dựng đồ thị sự kiện có thời gian từ văn bản rồi truy xuất trên đồ thị đó. Không huấn luyện. | Accuracy và Recall mức token (công thức chưa rõ) | **Không trực tiếp.** Accuracy/Recall mức token chưa rõ công thức nên không quy ra EM/F1; LLM và embedding (BGE-M3) khác mình; không có `hit@k`. Chỉ có ý nghĩa nếu mình dựng lại DyG-RAG chạy cùng điều kiện (mục 4). | Giữ, phụ | Cùng nguồn TimeQA, 2,613 câu. | Không có `hit@k`; công thức Accuracy chưa rõ, nên số của họ khó quy đổi. |
| **TEMPO** | Câu hỏi dài lấy từ Stack Exchange, cần tìm tài liệu bao quát nhiều giai đoạn (ví dụ "X thay đổi thế nào từ 2010 đến nay"). **1,730 câu**; **có văn bản**: 1,654,055 đoạn (`id` + `content`), 13 miền; **khoảng 2.4 GB** (tổng file gốc trên Hugging Face). | Bài **không đề xuất hệ thống mới**; họ làm bộ dữ liệu rồi lấy 12 retriever đã có (BM25, BGE, E5, ReasonIR...) chạy thử để xem cái nào tìm đúng tài liệu. Thử thêm việc nhờ LLM tách câu hỏi thành các bước nhỏ rồi tìm từng bước. Các retriever này chỉ so độ giống nghĩa giữa câu hỏi và tài liệu, **không dùng ngày tháng** để lọc hay chấm. | nDCG@10 (chính); TC@k, TR@k (phủ giai đoạn, LLM chấm) | **Một phần.** nDCG@10 tính lại được, họ có mã `temporal_metrics.py`. Nhưng retriever của họ chỉ so độ giống nghĩa, không dùng ngày; còn kho của họ không có trường ngày nên hệ của mình (cần `start_time` để lọc) không chạy được thế mạnh chính; các chỉ số TC/TR cần LLM judge. Phải chạy lại BM25/dense trên cùng dữ liệu rồi so khoảng cách. | Giữ, phụ | **Đã kiểm 2026-10-31:** CC-BY-4.0, tải được. 1,730 câu, 1,654,055 đoạn tài liệu chia 13 miền Stack Exchange (lớn nhất `history` 356K, nhỏ nhất `quant` 29K, `law` 43K). Có `gold_ids`, `gold_answers`, `negative_ids` nên tính được `hit@k`/nDCG. Tài liệu chỉ có `id` và `content`, không có cột thời gian. | Hạn chế: mỗi tài liệu chỉ có `id` và `content`, **không có trường ngày** (như `start_time`) nên bộ lọc cứng không có gì để lọc; câu hỏi có nói về thời gian trong chữ nhưng không có `T_req` rõ. Vì vậy không đo được rò rỉ tương lai. |
| **ChroniclingAmericaQA** | Câu hỏi trên báo cổ Mỹ 1800 đến 1920 (OCR), đáp án nằm trong bài báo. Bài TempRetriever dùng để thử bộ truy xuất có biết thời gian. Test **24,084 câu** (train 439,302, dev 24,111); **có văn bản**: đoạn báo (`context`, `raw_ocr`); dung lượng chưa ghi. | TempRetriever: huấn luyện (fine-tune) bộ truy xuất BERT hai nhánh, nhúng thêm thông tin thời gian vào vector (55 epoch). | Top-k accuracy, nDCG@k, MAP@k; EM, Recall, Contains khi cho LLM đọc | **Không.** Mã nguồn repo trống, không tái dựng được tập con 1,268 câu, chỉ số Top-k tính theo "chứa chuỗi đáp án". Phải tự chạy baseline trên cùng kho. | Giữ, rất yếu | Test 24,084 câu; chỉ 1,272 (5.3%) có năm; xem mục 5. | Hạn chế: 95% câu không có mốc `T_req`; OCR nhiễu; không có cặp cùng thực thể khác thời điểm. |
| TIDE | Đo truy xuất khi văn bản trộn Bangla và English, hai hệ lịch. | Chưa ghi. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Dữ liệu không phải tiếng Anh. |
| TimelyRAG | Chỉnh trọng số thời gian theo từng câu hỏi (α động), thử trên dữ liệu tiếng Hàn. | Chỉnh trọng số thời gian theo từng câu hỏi (α động) khi xếp hạng. | (chưa ghi) | Đã loại nên không xét. | **Loại** | Ý hay (α động, chỉ-lọc-cứng có thể tụt điểm), xem mục 4. | Dữ liệu tiếng Hàn và do LLM sinh. |
| TMRL | Huấn luyện bộ truy xuất hiểu thời gian trong câu hỏi (TimeQA). | Huấn luyện bộ truy xuất hiểu thời gian. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Không tải được dữ liệu đã xử lý; Hugging Face trả 401. |
| TPOUR | Huấn luyện bộ truy xuất theo thứ tự thời gian. | Huấn luyện bộ truy xuất theo thứ tự thời gian. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Repo chỉ có file train mẫu, bộ truy xuất không phát hành. |
| TANGO | Chỉ mục tìm kiếm nhanh có lọc theo thời gian. | Chỉ mục tìm kiếm gần đúng (ANN) có lọc theo thời gian. | Tốc độ truy vấn ANN | Đã loại nên không xét. | **Loại** |  | Dữ liệu là embedding có timestamp giả lập; không có đáp án, không có câu hỏi kèm mốc. |
| Freshness (Temporal RAG) | Thử cập nhật kho tài liệu mới có giúp RAG trả lời đúng không. | Cập nhật kho tài liệu để RAG trả lời được thông tin mới. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Dữ liệu phải tự sinh hoặc tự gọi API; chỉ 2 đến 5 truy vấn mỗi thử nghiệm. |
| Time-sensitive RAG (CIKM 2024) | Lọc tài liệu theo độ nhạy thời gian của câu hỏi. | Chưa đọc được thân bài. | (chưa đọc) | Đã loại nên không xét. | **Loại** |  | Không có bản arXiv, không đọc được thân bài; dữ liệu chưa xác nhận công khai. |

### Cần làm gì để dùng các bộ này (Cơ chế 1)

| Bộ | Dùng được ngay? | Việc cần làm để dùng | Chạy lại phương pháp của họ được không | Ontology (gói cần viết) |
|---|---|---|---|---|
| Bộ `real` | Có | Đã sẵn. | Của mình. | Gói nhỏ cho quan hệ Wikidata của TimeQA (chức vụ, đội...). |
| **TempRAGEval** | Chưa: gated | Xin quyền Hugging Face, tải `test.csv`. Kho 33.1M chunk quá lớn: chỉ giữ các trang chứa gold evidence của 1,000 câu, thêm trang nhiễu từ top-k BM25 và trang cùng thực thể ở thời điểm khác. Gán `start_time` cho chunk như bộ `real`. | Được: repo MRAG công khai (`temp_eval.py`, `reader.py`) nhưng README không có lệnh đánh giá, phải đọc mã. | Giống TimeQA, thêm địa lý (SituatedQA). |
| **DyG-RAG / TimeQA** | Gần: cần tải | Tải 3,159 bài Wikipedia từ repo; gán mốc như bộ `real`. | Được về mặt mã (`reproduce/`), nhưng dựng đồ thị cho khoảng 1.82M token gọi LLM rất nhiều, chỉ nên chạy mẫu nhỏ. README không có phần đánh giá. | Không cần: DyG-RAG tự dựng đồ thị sự kiện. |
| **TEMPO** | Có | Tải 1-2 miền nhỏ (`quant` 29K, `law` 43K đoạn). Tài liệu không có trường ngày nên chỉ đo được xếp hạng theo nghĩa; muốn lọc cứng thì phải nhờ LLM đọc từng đoạn để trích ngày (tốn LLM, nhân với 29K đến 43K đoạn). | Được: repo `tempo-bench/Tempo` (MIT) có `run.py` và `temporal_metrics.py`; chỉ số TC/TR cần LLM judge. | Không hợp (hỏi đáp mở Stack Exchange). |
| **ChroniclingAmericaQA** | Có | Tải `test.json`, lọc 1,272 câu có năm; `publication_date` có sẵn làm `start_time`. | Không: TempRetriever phải huấn luyện lại (fine-tune) bộ truy xuất và repo trống. Chỉ tự chạy baseline. Thêm nữa 95% câu hỏi không có `T_req` nên cơ chế của mình không có gì để lọc. | Không hợp. |

## 2. Cơ chế 2: Timeline Summarization (diễn biến theo thời gian)

**Bộ dùng được:**
1. **`timeline_gold`** tự dựng từ TimeQA: **bạn phải tự dựng**, theo `docs/eval/08_TIMELINE_EVAL_DESIGN.md`. Chưa có bộ ngoài nào dùng thẳng được ngay.
2. **TLQA** (`elixir-research-group/TLQA`, nhánh `master`): có sẵn câu hỏi và đáp án, thiếu kho văn bản (phải lấy trang Wikipedia). Gần bài toán nhất.
3. **ECT-QA** (`hanjiale/Temporal-GraphRAG`): có sẵn cả câu hỏi lẫn kho (9.9 MB) và `evidence_list`; có đáp án nên tự chấm EM/F1 được; cần lọc câu unanswerable.
4. **TDBench** (`ssoy0701/tdbench`): 2,854 câu sinh từ bảng có khoảng thời gian (đáp án đúng chắc chắn); thiếu kho văn bản, phải viết mỗi dòng bảng thành câu; hợp làm Cơ chế 2 qua các bảng chuỗi chức vụ (`dyknow_leaders` 448 dòng).
5. **ADQAB** (`kwunhang/TA-RAG`, CC BY-NC-SA): có sẵn câu hỏi trắc nghiệm và kho 127 MB, chấm accuracy đơn giản; không có gold chunk nên không đo được `hit@k`.

| Bộ / bài | Dữ liệu là gì | Phương pháp của bài (dễ hiểu) | Bài đó đo gì | So số của họ với mình được không, vì sao | Trạng thái | Ghi chú đã kiểm | Vì sao loại (nếu loại) |
|---|---|---|---|---|---|---|---|
| `timeline_gold` tự dựng từ TimeQA | Từ chú thích TimeQA, dựng câu "liệt kê/đếm/đầu tiên/cuối cùng/kế tiếp" về diễn biến một thực thể. **1,241 câu** (1,019 câu "reliable") dựng từ chú thích TimeQA; **có văn bản**: trang Wikipedia của TimeQA. | Của đồ án: Vector DB tìm nút vào, đồ thị duyệt theo thời gian, trả bộ ba gọn. Không huấn luyện. | `metrics_timeline` của đồ án (F1 tập, thứ tự...) | Đây là bộ của mình. | **Chính (tự dựng)** | Theo `docs/eval/08_TIMELINE_EVAL_DESIGN.md`. |  |
| **TLQA** | Hỏi "liệt kê tất cả các chức vụ/đội bóng của một người", đáp án là danh sách kèm năm bắt đầu và kết thúc. **1,655 câu** (train 1,158 / test 497) + biến thể TS 423 và TM 460 (chỉ test); đáp án là danh sách (thực thể: khoảng năm), trung bình 8.6 đáp án/câu. **Văn bản không kèm trong repo**: gold là infobox; kho đầy đủ là 4.5M bài Wikipedia (tháng 4/2024) trên Google Drive, dung lượng chưa rõ. | Chỉ là benchmark: cho LLM nhỏ (Mistral 7B, GPT-4o-mini) trả lời bằng few-shot/CoT, có hoặc không kèm BM25/dense top-3 trên Wikipedia 4.5M bài. Không graph, không huấn luyện. | Precision/Recall/F1 trên danh sách; Temporal Overlap, Temporal Jaccard (độ phủ năm); MRR, Recall@k cho truy xuất | **Một phần.** F1 và Temporal Overlap tính lại được trên đáp án chuẩn. Nhưng số của họ dùng BM25 top-3 trên 4.5M bài và LLM nhỏ khác mình, thời gian chỉ ở mức năm. Chạy lại baseline BM25 của họ cùng LLM với mình thì so khoảng cách được. | Giữ, phụ (gần nhất) | Test 497 câu (251 chính trị, 246 đội bóng), median 8 đáp án/câu; có baseline GPT-4o-mini. | Hạn chế: gold chỉ là infobox; chỉ khoảng 51% tên đáp án khớp nguyên văn trong evidence; không kèm kho văn bản. |
| **ECT-QA** | Câu hỏi về các cuộc họp báo cáo thu nhập công ty qua nhiều quý ("doanh thu thay đổi thế nào từ Q1 đến Q4"). **1,005 câu cụ thể** (656 base + 349 new, trong đó 261 unanswerable) + 100 câu trừu tượng; **có văn bản**: 480 transcript của 24 công ty, khoảng 1.58M token, kho **9.9 MB** (nén; chỉ là kho, không phải số câu hỏi). | TG-RAG: dùng LLM (Gemini-2.5-flash-lite) dựng đồ thị thời gian hai tầng (bi-level) từ văn bản rồi truy xuất trên đó. Không huấn luyện. | Tỉ lệ Correct/Refusal/Incorrect do LLM chấm; ROUGE-L; token F1; win rate cho câu trừu tượng | **Khó.** Họ chấm bằng LLM judge với prompt riêng; chỉ mục dựng bằng Gemini-2.5-flash-lite. Có sẵn kho và gold evidence nên chạy lại NaiveRAG/GraphRAG... cùng điều kiện được, nhưng không đặt số tuyệt đối cạnh số của họ. Mình có thể chấm EM/F1 thay. | Giữ, phụ | Kho 9.9 MB, có `evidence_list`, `num_hops`. Có đáp án nên tự chấm EM/F1 được. | Hạn chế: nhiều câu unanswerable; miền tài chính (chỉ là miền, không phải lý do loại). |
| **ADQAB (TA-RAG)** | Trắc nghiệm về giá cổ phiếu qua các thời điểm, kho tin tài chính. **525 câu** trắc nghiệm (7 loại × 75); **có văn bản**: 27,037 bài (23,737 tin thật + 3,300 tin tổng hợp) = 77,965 chunk, file `C_final.jsonl` **127 MB**; không có gold chunk. | TA-RAG (không huấn luyện): lúc nạp, LLM nhỏ trích khoảng thời gian của từng chunk; lúc hỏi, LLM tách câu hỏi thành nội dung và khoảng thời gian, lọc các chunk có khoảng giao với khoảng hỏi, rồi xếp theo độ giống. Đã sửa: bài **không có** bước tóm tắt dòng thời gian bằng LLM như mình ghi nhầm trước đây. Sơ đồ ở file `02`. | Accuracy (5 lần chạy), tại top-k 5/10/20/50 | **Khó nhưng khả thi.** Accuracy trắc nghiệm tính lại được và có bảng BM25/Naive RAG theo k = 5 đến 50. Nhưng họ dùng LLaMA-3.3-70B, chunk 2048 token, và đáp án đến từ đồ thị giá chứ không từ văn bản tin. Chạy lại Naive RAG và BM25 cùng LLM rồi so khoảng cách. | Giữ, phụ | 525 câu, kho 127 MB. | Hạn chế: không có gold chunk nên không đo `hit@k`. |
| **TDBench** | Từ các bảng có khoảng thời gian (ví dụ "nước X, chức vụ Y, người Z, từ ngày A đến ngày B"), sinh câu hỏi bằng SQL nên đáp án chắc chắn đúng. Có cả câu không có đáp án và câu hỏi nối hai bảng. **2,854 câu** sinh sẵn; **không có văn bản**, chỉ có bảng (10 file CSV, 54 đến 539 dòng); cả repo 13 MB. | Công cụ sinh câu hỏi từ bảng thời gian bằng SQL (LLM chỉ diễn đạt), rồi hỏi LLM không kèm tài liệu. Không đề xuất phương pháp truy xuất. | Answer accuracy, Time accuracy (câu trả lời đúng cả mốc thời gian), AT | **Không.** Bài đo LLM trả lời không có tài liệu nên không có số RAG nào để đặt cạnh. Mình chỉ dùng dữ liệu, tự chạy baseline. | Giữ, phụ (**khôi phục**) | **Đã kiểm 2026-10-31** (`github.com/ssoy0701/tdbench`): 2,854 câu có sẵn trong `qa_pairs/` (now 962, basic_unique 655, basic_multiple 570, basic_none 535 không có đáp án, join 132) kèm `correct_rows` và `incorrect_rows` (các dòng có sai mốc); 10 bảng CSV nhỏ (54 đến 539 dòng) nằm ở `dataset/crafted/`; mỗi câu có 3 cách diễn đạt. | Hạn chế: **không có kho văn bản**, mỗi dòng bảng phải tự viết thành câu (`start_time`/`end_time` lấy thẳng từ cột Start/End nên rất sạch); câu hỏi kiểu "đúng 4 tháng trước ngày..." (13 quan hệ Allen) ngoài phạm vi Cơ chế 1; bài chỉ có 2,854 trên 9,231 câu trong paper. Lý do loại trước đây (đo LLM đóng sách) là mục đích bài, không phải dữ liệu. |
| Diachronic RAG | Thực chất là bài TA-RAG/ADQAB. | Trùng TA-RAG. |  | Đã loại nên không xét. | **Loại** |  | Trùng, đã gộp. |

Chưa có bài nào là "đối thủ cùng bài toán" dùng được ngay. DyG-RAG là đối thủ thật nhất (đồ thị sự kiện), nhưng muốn so phải tự dựng lại (xem mục 4).

### Cần làm gì để dùng các bộ này (Cơ chế 2)

| Bộ | Dùng được ngay? | Việc cần làm để dùng | Chạy lại phương pháp của họ được không | Ontology (gói cần viết) |
|---|---|---|---|---|
| `timeline_gold` | Đã dựng | Theo `docs/eval/08_TIMELINE_EVAL_DESIGN.md`. | Của mình. | Gói TimeQA như Cơ chế 1. |
| **TLQA** | Gần: cần dựng kho | Tải JSON từ GitHub. Lấy trang Wikipedia của 5,711 thực thể (API gom 50 tên mỗi yêu cầu, khoảng 115 yêu cầu, ước lượng vài phút đến 1-2 giờ, chưa đo). Nên dùng bản mapping trên Google Drive của họ vì trang hiện tại khác bản dump 4/2024. Gán `start_time`/`end_time` từ năm. | Được cho baseline: repo có `evaluation/evaluateResults.py` và mã BM25 top-3. Không có phương pháp graph để chạy lại. | **Dễ nhất:** chỉ 2 quan hệ Wikidata (P54 đội, P39 chức vụ) kèm khoảng năm. |
| **ECT-QA** | Có | Tải repo `hanjiale/Temporal-GraphRAG` (kho 9.9 MB nén). Mốc là quý. Cố định `T_now` cho 201 câu relative-time; tách 261 câu unanswerable ra riêng. | Được: mã TG-RAG công khai; dựng chỉ mục 1.58M token tốn LLM mức trung bình đến cao. Họ index bằng Gemini-2.5-flash-lite. | Gói nhỏ: công ty, chỉ số tài chính, quý. |
| **ADQAB** | Có | Tải `C_final.jsonl` (127 MB, Git LFS) và `dqabench_MCQA.json`; chunk sẵn. Kiểm cột ngày của bài trước. Không có gold chunk nên không đo `hit@k`. Tự mô phỏng thì cần giá cổ phiếu, câu hỏi sinh theo mẫu, đáp án gây nhiễu, kho tin tổng hợp; tự ra đề tự chấm nên không khuyến khích. | Được về mã (`kwunhang/TA-RAG`), nhưng họ dùng LLaMA-3.3-70B và trích mốc bằng LLM cho 27K bài; nếu dùng ngày đăng thì là biến thể khác. | Gói nhỏ: cổ phiếu, xu hướng giá. |
| **TDBench** | Gần: cần viết kho | Mỗi dòng bảng viết thành câu bằng mẫu; `Start`/`End` lấy thẳng từ cột. Câu hỏi 2,854 dùng sẵn. | Không có phương pháp truy xuất; `run_qa.py` chỉ hỏi LLM không kèm tài liệu. | Gần như sẵn: bảng có cột kiểu và phụ thuộc hàm thời gian. |

## 3. Cơ chế 3: Conflict Resolution (chỉ xung đột thời gian)

**Bộ dùng được (theo thứ tự ưu tiên):**
1. **HoH** (`russwest404/HoH-QAs`): chính; 111,972 dòng, có đáp án mới, đáp án cũ kèm ngày, `last_modified_time`.
2. **FactConsolidation** (`ai-hyz/MemoryAgentBench`, split `Conflict_Resolution`): chính; fact sau đè fact trước, ngữ cảnh 6K đến 262K token.
3. **LongMemEval** (`xiaowu0162/longmemeval-cleaned`, MIT, phần `knowledge-update`, 78 câu): chính; hội thoại; đã kiểm tải được.
4. **VersionQA** (`danielhuwiler/versionrag`): phụ; 100 câu, 34 tài liệu release notes.
5. **Conflicts (Google, Cattan)**: phụ; chỉ lấy Freshness (62) và No conflict (161).

| Bộ / bài | Dữ liệu là gì | Phương pháp của bài (dễ hiểu) | Bài đó đo gì | So số của họ với mình được không, vì sao | Trạng thái | Ghi chú đã kiểm | Vì sao loại (nếu loại) |
|---|---|---|---|---|---|---|---|
| **HoH** | Wikipedia đã sửa thông tin. Hỏi lại câu cũ, xem hệ thống trả giá trị mới hay còn trả giá trị cũ (lỗi thời). **111,972 dòng** (tập đánh giá chính thức 10,000); **có văn bản**: cột `document`, `evidence` (1 câu); khoảng **28 MB**. | Chủ yếu benchmark: chạy RAG trên máy tìm kiếm giả lập (BM25 + giảm dần theo thời gian), bge, và hai retriever có biết thời gian (MRAG, TempRALM). Dữ liệu dựng bằng so sánh từng token và một mô hình nhỏ (Qwen2.5-0.5B) được huấn luyện để lọc. | LLM chấm mỗi câu: Perfect (+1) / Missing (0) / Harmful (-1); top-k hit rate tách đoạn đúng (R) và đoạn lỗi thời (O) | **Một phần.** Hit rate đoạn mới/cũ tính lại được, Perfect/Harmful cần LLM judge (họ dùng Llama-3.1-70B). Retriever, LLM, judge đều khác mình nên chạy lại baseline cùng điều kiện; kho chỉ gồm câu evidence nên dễ hơn thực tế. | **Chính** | 111,972 dòng; mỗi dòng có đáp án mới, đáp án cũ kèm ngày (`outdated_infos`), `last_modified_time`. Có đáp án nên tự chấm EM/F1 được. | Hạn chế: kho chỉ là các câu evidence (dễ hơn thực tế); chủ yếu hỏi giá trị hiện tại. |
| **FactConsolidation** | Một danh sách fact đánh số, fact sau sửa fact trước (ví dụ "thủ đô của X là A" rồi "thủ đô của X là B"). Hỏi lại, phải trả theo fact mới nhất. 2 biến thể (SH, MH) × **100 câu**, mỗi biến thể 4 mức dài (6K, 32K, 64K, 262K token) = 8 ngữ cảnh; **có văn bản**: danh sách fact đánh số; dung lượng chưa đo. | Chỉ là benchmark: chạy khoảng 10 loại hệ thống (ngữ cảnh dài, BM25, embedding RAG, HippoRAG-v2 dùng graph, Mem0, Cognee...), prompt dặn ưu tiên fact mới. | SubEM: câu trả lời có chứa đáp án chuẩn không | **Dễ nhất trong nhóm.** Có bảng nhiều hệ thống, chỉ số SubEM đơn giản, tự tính. Nhưng họ dùng GPT-4o, OpenAI embedding, chunk 512; số multi-hop sát sàn; mình thêm `start_time` giả là điều kiện khác. Chạy lại BM25 hoặc RAG cùng LLM rồi so. | **Chính** | 10 hệ thống có số (có Mem0). | Hạn chế: không có mốc thời gian thật, chỉ có thứ tự số. |
| **LongMemEval** (`knowledge-update`) | Hội thoại dài giữa người dùng và trợ lý qua nhiều phiên; về sau người dùng đổi thông tin ("trước ở Hawaii, giờ chuyển Paris"). Hỏi lại thông tin hiện tại. **500 câu** (`knowledge-update` 78, `temporal-reasoning` 133); **có văn bản**: hội thoại nhiều phiên; bản `oracle` **15 MB**, `s` 277 MB, `m` 2.7 GB. | Benchmark kèm khung 3 bước (lập chỉ mục, truy xuất, đọc) với: tách phiên thành từng lượt, mở rộng khóa bằng fact trích ra, mở rộng truy vấn theo thời gian. Không huấn luyện. | Accuracy do LLM chấm (GPT-4o) theo loại câu; Recall@k, nDCG@k khi hệ thống lộ kết quả truy xuất | **Một phần.** Chấm bằng GPT-4o judge nên phải dùng cùng judge. Số Zep/Mem0 do bên thứ ba tự báo, khác LLM và phiên bản file. Chỉ so được nếu mình chạy lại baseline của họ; benchmark còn tính đúng cả khi trả lẫn giá trị cũ. | **Chính** | **Đã kiểm 2026-10-31:** tải được `longmemeval_oracle.json` (15 MB), 500 câu, trong đó `knowledge-update` 78 câu (mỗi câu 2 phiên bằng chứng ở bản oracle) và `temporal-reasoning` 133; có `haystack_dates`, `question_date`, `answer_session_ids`. Bản `s` 277 MB, bản `m` 2.7 GB. | Hạn chế: là hội thoại, không phải Wikipedia; người chấm cho đúng cả khi trả luôn thông tin cũ, nên không phạt "không bỏ giá trị cũ". |
| **VersionQA** | Hỏi về tài liệu phần mềm qua các phiên bản ("phiên bản 3 đổi gì so với 2?"). **100 câu**; **có văn bản**: 34 tài liệu release notes; nhỏ, dung lượng chưa đo. | VersionRAG: đồ thị phân cấp 5 mức (Neo4j) kết hợp vector (Milvus), phát hiện thay đổi giữa các phiên bản bằng so sánh từng dòng, định tuyến câu hỏi theo loại. Không huấn luyện. | Accuracy do LLM chấm (GPT-4.1), theo 3 nhóm Content, Version Listing, Change | **Khó.** GPT-4.1 chấm; bộ dùng số hiệu phiên bản chứ không phải thời gian thật; chỉ 100 câu nên chỉ nói được xu hướng. Có số Naive RAG và GraphRAG nhiều LLM, nên chạy lại Naive RAG cùng LLM với mình để so. | Giữ, phụ | 100 câu, 34 tài liệu release notes. | Nhỏ; miền phần mềm; phiên bản không phải thời gian thật; không có gold chunk. |
| **Conflicts (Google, Cattan)** | Câu hỏi mà các kết quả tìm kiếm bất đồng nhau; có 5 loại bất đồng. Chỉ lấy loại "thông tin mới hơn" và "không xung đột". **458 câu** (dùng Freshness 62 + No conflict 161); **có văn bản**: mỗi câu kèm top-10 kết quả Google với toàn văn trang (suy ra khoảng 4,200 tài liệu); dung lượng chưa đo. | Benchmark kèm thử 4 cách prompt trên LLM: prompt thường, đoán loại xung đột rồi trả lời theo loại, đưa bảng phân loại vào prompt, và biết sẵn nhãn (oracle). Không huấn luyện. | Accuracy đoán loại xung đột; factual grounding; Answer Recall; hành vi mong đợi (LLM chấm) | **Rất hạn chế.** Chỉ 2 trong 5 loại liên quan, chưa có số riêng cho Freshness, chấm bằng LLM judge. Chỉ dùng được số vanilla và oracle làm mốc tham khảo. | Giữ, phụ | Freshness (62), No conflict (161, đối chứng "không đóng nhầm"). | Chỉ 2 trong 5 loại liên quan. |
| ConflictBank | Bộ lớn về xung đột kiến thức trong LLM. | Benchmark: cho LLM trả lời trắc nghiệm khi bằng chứng (do LLaMA-3-70B sinh) mâu thuẫn. | Chỉ số riêng của bài | Đã loại nên không xét. | **Loại** |  | Dữ liệu tổng hợp, mốc tương lai bịa. |
| FRESCO | Kiểm re-ranker có chọn đoạn mới nhất không. | Kiểm re-ranker có chọn đoạn mới nhất không. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Không có dữ liệu sẵn (phải tự sinh), CC-BY-NC. |
| EvoWiki | Câu hỏi về kiến thức Wikipedia thay đổi theo thời gian. | Chưa ghi. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Dữ liệu ở MEGA, repo "Coming soon". |
| RECON | Đối chiếu xung đột trong bộ nhớ. | Chưa ghi. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Chưa công khai (repo ẩn danh). |
| CONFACT | Xác minh claim bằng nguồn có uy tín khác nhau. | Chưa ghi. | Yes/no về claim | Đã loại nên không xét. | **Loại** | Bộ duy nhất có nhãn uy tín nguồn thật (MBFC). | Ngoài phạm vi (xung đột nguồn); lệch lớp 80% "No". |
| ConfRAG | Web thật, nhiều nguồn bất đồng. | Chưa ghi. | Gom cụm quan điểm | Đã loại nên không xét. | **Loại** | `trust_score` 1 đến 10 mỗi trang. | Ngoài phạm vi; 74% trang chấm 8; tài liệu dài, tốn token. |
| Multi-Source Memory Benchmark | Nhiều nguồn tổng hợp theo thời gian. | Chưa ghi. | Đáp án là khoảng số | Đã loại nên không xét. | **Loại** |  | Ngoài phạm vi; là bài đếm 30 ngày, không phải ghi đè. |
| RAMDocs, CAGB | Tài liệu sai/đúng trộn lẫn. | Chưa ghi. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Ngoài phạm vi (misinformation tổng hợp, credibility tự động 3 mức). |
| RAGuard, WikiContradict, NatConfQA | Mâu thuẫn giữa các tài liệu. | Chưa ghi. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Không có thời gian lẫn nhãn uy tín nguồn. |
| RA-RAG | Trọng số theo độ tin cậy nguồn. | Trọng số theo độ tin cậy nguồn. | (chưa ghi) | Đã loại nên không xét. | **Loại** |  | Nguồn giả lập; README không có link dữ liệu. |

### Cần làm gì để dùng các bộ này (Cơ chế 3)

| Bộ | Dùng được ngay? | Việc cần làm để dùng | Chạy lại phương pháp của họ được không | Ontology (gói cần viết) |
|---|---|---|---|---|
| **HoH** | Có | Tải file 28 MB; dựng kho từ `document`/`evidence`; `start_time` = `last_modified_time`; đáp án cũ nằm trong `outdated_infos` (chunk cũ có `end_time`). | Được: repo công khai nhưng README không có lệnh đánh giá; judge của họ là Llama-3.1-70B. | Khó: Wikipedia mở, 5 lĩnh vực, không có sơ đồ cố định; để LLM trích quan hệ. |
| **FactConsolidation** | Có | Tải split `Conflict_Resolution` (8 dòng); tách ngữ cảnh thành fact đánh số; gán ngày giả từ số thứ tự. | Được: MemoryAgentBench có baseline BM25, embedding RAG, HippoRAG-v2, Mem0... | Vừa: quan hệ Wikidata kiểu "head of government"; fact sau ghi đè fact trước ứng với `SUPERSEDES`. |
| **LongMemEval** | Có | Tải bản `oracle` (15 MB) trước, rồi bản `s` (277 MB). Ngày mỗi phiên làm `start_time`. | Được: repo có mã chấm bằng GPT-4o (tốn tiền judge). Bản gốc có tách phiên và mở rộng truy vấn theo thời gian, cài lại được. | Vừa: gói "bộ nhớ cá nhân" (thuộc tính người dùng). |
| **VersionQA** | Có | Tải 34 tài liệu release notes và `evaluation_set.csv`. Phiên bản chưa phải thời gian thật: lấy ngày phát hành tra ngoài hoặc dùng thứ tự phiên bản. | Nặng: VersionRAG cần Neo4j + Milvus + LLM lớn. Baseline Naive RAG chạy lại nhẹ. | Vừa: phần mềm, phiên bản, tính năng. |
| **Conflicts (Cattan)** | Có | Tải `conflicts.jsonl`; lọc 223 câu (Freshness 62 + No conflict 161). Mốc lấy từ trường `date` (chưa kiểm có đủ không). | Không: repo đã archive, chỉ có dữ liệu. | Không cần. |

## 4. Vì sao chưa có bài để đặt số cạnh số, và chỉ số đo thêm được gì

**Nguyên tắc:** phương pháp của họ khác mình (graph, fine-tune, prompt...) **không phải** lý do để không so. So một cách tiếp cận với cách tiếp cận khác trên cùng bài toán chính là mục đích của so sánh. Cái cản là **điều kiện thí nghiệm không giống nhau**. Muốn đặt số cạnh số thì phải cùng dữ liệu, cùng LLM đọc, cùng cách chấm; số công bố hầu như không thỏa ba điều này.

**Các vấn đề cụ thể** (xếp theo mức nghiêm trọng):

| # | Vấn đề | Vì sao làm số không so được | Bộ / bài bị ảnh hưởng |
|---|---|---|---|
| 1 | **Kho tài liệu khác** (kích thước, độ nhiễu, cách chia chunk) | Kho càng lớn thì càng khó; mình phải thu hẹp kho nên số tuyệt đối cao giả. Chunk khác nhau làm cùng `k` chứa lượng chữ khác nhau. | TempRAGEval (33.1M chunk), TLQA (Wikipedia 4.5M bài), ADQAB (chunk 2048 token), FactConsolidation (chunk 512), HoH (kho chỉ là câu evidence, dễ hơn thực tế) |
| 2 | **LLM đọc khác** | Cùng retriever mà LLM khác thì EM/F1 khác nhiều, không biết chênh do phương pháp hay do LLM. | Gần như mọi bài: Qwen2.5-14B (DyG-RAG), LLaMA-3.3-70B (TA-RAG), GPT-4o (FactConsolidation, LongMemEval), Mistral 7B (TLQA), Gemini-2.5-flash-lite (ECT-QA); mình dùng Gemini 3.5/Gemma |
| 3 | **Embedding và reranker khác** | Đổi embedding hoặc reranker đã làm `hit@k` đổi lớn (mình thấy: Plain 0.336 lên Plain+bge 0.490). | Mọi bài có truy xuất |
| 4 | **Cách chấm khác** | LLM judge phụ thuộc model chấm và prompt chấm; EM/F1 phụ thuộc cách chuẩn hóa chuỗi; công thức một số chỉ số không công bố. | LongMemEval (GPT-4o judge), HoH (Llama-3.1-70B judge), VersionQA (GPT-4.1 judge), ECT-QA (judge riêng), DyG-RAG (Accuracy token-overlap chưa rõ công thức), Conflicts |
| 5 | **Tập con câu hỏi không tái dựng được** | Không biết đúng những câu nào họ dùng. | ChroniclingAmericaQA (1,268 trong 24,084, không có script), DyG-RAG (không rõ split) |
| 6 | **Không có mã hoặc dữ liệu để chạy lại** | Không chạy lại được baseline hay phương pháp của họ để kiểm pipeline. | TempRetriever (repo trống), TMRL, TPOUR, EvoWiki, RECON; TempRAGEval gated |
| 7 | **Bài không có số cho tình huống của mình** | Mục đích bài khác nên không có số RAG nào để đặt cạnh. | TDBench (đo LLM không kèm tài liệu) |
| 8 | **Thiếu thông tin thời gian trong dữ liệu** | Hệ của mình lọc cứng bằng cách so `start_time` của từng chunk với `T_req` của câu hỏi. Nếu chunk không có trường ngày, hoặc câu hỏi không nêu thời điểm nào để so, thì bộ lọc không có gì để làm: không dùng được thế mạnh chính và không đo được rò rỉ tương lai. | TEMPO, ChroniclingAmericaQA, FactConsolidation (chỉ có thứ tự số), VersionQA (số hiệu phiên bản) |
| 9 | **Bộ nhỏ, nhiễu thống kê** | Một câu lệch nhiều điểm phần trăm, chỉ nói được xu hướng. | VersionQA (100 câu), Conflicts (62 và 161 câu) |
| 10 | **Không bài nào đo `leakage_rate`** | Đó là điểm khác của đồ án, nên không có số của họ để đặt cạnh. | Tất cả |
| 11 | **Số công bố là tự báo cáo** | Chưa ai độc lập kiểm, một số chỗ bản HTML và PDF lệch nhau (ví dụ TEMPO). | Gần như mọi bài |

**Hai cách so hợp lệ** (thay cho việc chép số của họ). Ví dụ số giả định: bài họ công bố BM25 = 40, phương pháp của họ = 50; pipeline của mình BM25 = 41, hệ của mình = 55.
1. **Chạy lại phương pháp của họ trên máy mình.** Cùng dữ liệu, cùng LLM, cùng cách chấm với hệ của mình, rồi đặt hai số cạnh nhau. Sạch nhất, nhưng phải chạy được mã của họ (tốn công và LLM).
2. **Neo bằng baseline chung.** Không chạy phương pháp của họ; chỉ chạy BM25 hoặc Naive RAG ở cả hai phía. Nếu BM25 của mình (41) gần số họ công bố (40) thì pipeline hai bên tương đương, khi đó so **mức hơn baseline**: họ +10, mình +14. Rẻ hơn, nhưng yếu hơn vì ta giả định phương pháp của họ cũng cho +10 trên máy mình.

**Chỉ số của họ, đồ án tự đo thêm được:**

| Chỉ số của họ | Tự tính được? |
|---|---|
| ER@k | Có, trùng `hit@k` trên gold chunk |
| AR@k, Top-k accuracy | Có: "top-k chứa chuỗi đáp án", gần `ans_valid@k` và `contains` |
| EM, F1 | Có, đã đo |
| nDCG@10, Recall@100 | Có, nếu có nhãn liên quan; chỉ là hàm trên danh sách xếp hạng |
| Accuracy token-overlap (DyG-RAG) | Chưa chắc: phải đọc `reproduce/` của họ |
| LLM judge (ECT-QA) | Cần đúng prompt và model chấm của họ |

**Cách đặt cạnh số của họ:** chạy lại baseline của chính bài họ (BM25 hoặc DPR) trên đúng dữ liệu và giao thức của bạn. Nếu số khớp số họ công bố thì pipeline tương đương, và số của bạn đặt cạnh số phương pháp của họ có ý nghĩa hơn. Nếu lệch nhiều thì chỉ so khoảng cách giữa các hệ.

**Dựng lại phương pháp của họ có tốn không** (ước lượng, chưa đo):
- Cài lại ý tưởng đơn giản (rerank decay `α·cos + (1−α)·0.5^(age/h)`, lọc theo khoảng thời gian, chỉ-lọc-cứng, α động theo truy vấn): nửa ngày đến 2 ngày mỗi ý, không cần LLM thêm. **Đáng làm.**
- DyG-RAG nguyên bản: vài ngày, chi phí LLM trung bình đến cao; chỉ nên chạy trên mẫu nhỏ ở Cơ chế 2.
- Fine-tune retriever: không đáng.

## 5. ChroniclingAmericaQA có hợp lý cho Cơ chế 1 không?

**Không hợp làm bộ chính. Đề xuất "tốt nhất" ở lượt trước của mình là sai.** Mình tải test và đếm:

- **24,084 câu** test (không phải 1,268; con số 1,268 trong bài TempRetriever là tập con, cách lọc **chưa rõ**).
- **Chỉ 1,272 câu (5.3%) có năm** trong câu hỏi, 878 câu có tên tháng, 297 câu có cụm thời gian tương đối. Khoảng **95% câu không có mốc `T_req`**, ví dụ "How many lots did Thomas Peirce have?". Với các câu này Cơ chế 1 không có gì để lọc.
- Trong 1,272 câu có năm, **73% năm trong câu cách ngày đăng báo không quá 1 năm.** Nghĩa là câu hỏi gần như hỏi về chính sự kiện trong bài, `T_req` ≈ ngày đăng. Không có cặp "cùng thực thể, trạng thái khác theo thời gian" nên không kiểm được "phiên bản nào đang hiệu lực tại T".
- Một số câu lệch thời gian lớn (ví dụ báo năm 1901 nhưng hỏi năm 1861). Văn bản là OCR báo cổ 1800 đến 1920, lẫn nhiễu nặng.
- Giả thuyết **chưa kiểm:** tập con 1,268 câu của TempRetriever có thể chính là nhóm câu có năm (1,272 gần 1,268).

**Kết luận:** nếu dùng, chỉ lấy 1,272 câu có năm và coi như bộ phụ kiểm tra "không lọt tương lai" trên văn bản OCR, không đo được Case 1/Case 2. Bộ chính cho Cơ chế 1 vẫn là bộ `real` (TimeQA), phụ là TempRAGEval thu hẹp.

## 6. Giải thích thuật ngữ hay gặp trong bảng

- **Mức token (token-level):** token ở đây là đơn vị chữ, gần như là từ, không phải chi phí gọi LLM. Recall = tỉ lệ từ của đáp án chuẩn có trong câu trả lời; precision = tỉ lệ từ của câu trả lời nằm trong đáp án chuẩn; F1 là trung bình của hai cái. Ví dụ đáp án "Michel Temer", trả lời "Michel Temer, 2016": recall 100%, precision 2/3.
- **LLM judge:** dùng một LLM làm giám khảo. Đưa cho nó câu hỏi, đáp án chuẩn và câu trả lời của hệ thống, nó trả "đúng/sai" hoặc chia mức (HoH: Perfect/Missing/Harmful; LongMemEval: yes/no). Kết quả phụ thuộc model chấm và prompt chấm, tốn tiền, có nhiễu.
- **Không có mốc thời gian thật (FactConsolidation):** dữ liệu chỉ có số thứ tự fact (`[12]`, `[847]`, số lớn là mới hơn), không có ngày. Đo được "fact sau đè fact trước", nhưng không đo được lọc theo `T_req`, decay theo năm hay câu hỏi lịch sử.
- **Closed-book (TDBench):** hỏi LLM không kèm tài liệu để xem nó tự nhớ gì; không phải RAG.
- **Gold chunk:** đoạn văn đúng do người gán, dùng để tính `hit@k`. Bộ nào không có (ADQAB, TDBench) thì không đo được chỉ số truy xuất.
- **Ontology nhẹ của đồ án:** một lõi dùng chung cộng một gói riêng cho từng bộ dữ liệu (xem `docs/research/knowledge_representation_and_integration/16_Ontology_and_Ingestion_Decisions.md`).

## 7. Các hệ thống mà bài benchmark đã chạy, và biết chúng từ đâu

Chuyển từ file `02` sang đây 2026-11-01 vì các bài này chỉ là benchmark, không có phương pháp riêng.

- **Các bài benchmark** (HoH, TLQA, TEMPO, FactConsolidation, Conflicts) **lấy các phương pháp có sẵn trong các bài đã công bố trước đó** (trích dẫn bài gốc) rồi chạy trên dữ liệu của họ. Một số thành phần **họ tự dựng hoặc tự thiết kế** chứ không phải có sẵn.
- **Họ biết các phương pháp đó nhờ đọc tài liệu và trích dẫn** (bài gốc, hoặc mã và thư viện công khai). Mình đọc bản HTML của HoH, FactConsolidation, TLQA (2026-11-01): các bài đều **trích bài gốc**, nhưng **không nêu họ dùng mã chính thức hay tự cài lại** ở các phần mình đọc (FactConsolidation mình mới đọc khoảng 100K trên 176K ký tự). Nên cột "Xem ở đâu" bên dưới là **nơi bạn có thể xem phương pháp gốc**, không phải bằng chứng họ dùng đúng bản đó.

| Bài benchmark | Hệ thống hay phương pháp | Nguồn gốc theo chính bài | Xem ở đâu |
|---|---|---|---|
| **HoH** ([repo](https://github.com/0russwest0/HoH)) | Máy tìm kiếm BM25 cộng giảm dần Gaussian (HoH-SearchEngine) | **Do HoH tự dựng** trên Elasticsearch, hàm giảm dần Gaussian là phần họ thêm; BM25 trích Robertson và cộng sự (2009) | Mã HoH (công thức giảm dần đọc trong mã) |
| | bge-base-en-v1.5, bge-m3, bge-reranker-v2-m3 | Trích Chen (2024), Xiao (2024), gọi là mô hình embedding và reranker tiên tiến | Hugging Face, tìm theo tên |
| | MRAG, TempRALM | Trích như "giải pháp truy xuất thời gian có sẵn"; không nêu dùng mã chính thức hay cài lại | Mục 1.1 và [repo MRAG](https://github.com/siyue-zhang/MRAG); TempRALM: [arXiv 2401.13222](https://arxiv.org/abs/2401.13222) (chưa kiểm có mã) |
| **TLQA** ([repo](https://github.com/elixir-research-group/TLQA)) | Few-shot, kNN few-shot, few-shot CoT, Auto-CoT; BM25, all-MiniLM-v2, multi-qa-mpnet | **Bài không ghi nguồn hay cách cài** (chỉ nêu tên trong bảng); đây là các kỹ thuật phổ biến | Mã và kết quả trong repo TLQA; [Auto-CoT](https://github.com/amazon-science/auto-cot) |
| **FactConsolidation** ([repo MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench)) | BM25 | Trích Robertson và Walker (1994) | [rank_bm25](https://github.com/dorianbrown/rank_bm25) |
| | Contriever | Trích Izacard (2021) | [Repo Contriever](https://github.com/facebookresearch/contriever) |
| | NV-Embed-v2 | Phần mình đọc không thấy nhắc | [Hugging Face](https://huggingface.co/nvidia/NV-Embed-v2) |
| | HippoRAG-v2 | Trích Gutiérrez (2025) | [Repo HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) |
| | RAPTOR, GraphRAG | Có trong bảng đầy đủ; phần mình đọc không nêu nguồn | [RAPTOR](https://github.com/parthsarthi03/raptor), [GraphRAG](https://github.com/microsoft/graphrag) |
| | Cognee | Trích Markovic (2025); bài nhắc "chi phí API" cho Cognee và Mem0 | [Repo Cognee](https://github.com/topoteretes/cognee) |
| | Self-RAG | Trích Asai (2023) | [Repo Self-RAG](https://github.com/AkariAsai/self-rag) |
| | MemGPT (nay là Letta) | Trích Packer (2023) | [Repo Letta](https://github.com/letta-ai/letta) |
| | Mem0 | Trích Chhikara (2025) | [Repo Mem0](https://github.com/mem0ai/mem0) |
| | Long-context (GPT-4o, Gemini-2.0-Flash, Claude-3.7-Sonnet...) | Trích thông báo của nhà cung cấp mô hình; backbone mặc định của các hệ RAG là GPT-4o-mini | Gọi API, đưa cả ngữ cảnh dài vào prompt |
| **TEMPO** ([repo](https://github.com/tempo-bench/Tempo)) | 12 retriever (BM25, BGE, Contriever, Instructor-L, SBERT, E5, GritLM, Qwen, SFR, DiVeR, Rader, ReasonIR) | **Chưa kiểm lại** (ghi chú cũ nói repo có `retrievers.py`) | Repo TEMPO, hoặc tải mô hình trên Hugging Face |
| **Conflicts (Cattan)** | Ba cách prompt: prompt thường, đoán loại xung đột rồi trả lời ("pipeline"), đưa bảng phân loại vào prompt ("taxonomy-aware"), và biết sẵn nhãn ("oracle") | **Do chính tác giả thiết kế** (đây là phần đề xuất của bài, không phải phương pháp có sẵn) | Chỉ có trong phụ lục bài [arXiv 2506.08500](https://arxiv.org/abs/2506.08500); [repo dữ liệu](https://github.com/google-research-datasets/rag_conflicts) không có prompt |

## 8. Ontology trong các bài benchmark

Chuyển từ file `02` sang đây 2026-11-01 vì TLQA và Conflicts là bài benchmark. Không bài nào dùng ontology theo nghĩa đầy đủ (OWL, RDF, Turtle); đây là phần gần nhất, kèm cách triển khai ontology nhẹ của đồ án nếu muốn dùng.

| Bài | Có gì gần với ontology | Mức độ | Nếu triển khai ontology cho bài này: chứa gì |
|---|---|---|---|
| **TLQA** | Dùng đúng hai thuộc tính Wikidata (P54 thành viên đội, P39 chức vụ) làm khuôn câu hỏi | Mượn từ vựng Wikidata | Lớp `Person`, `Team`, `Position`; quan hệ `memberOf` (P54), `positionHeld` (P39), mỗi quan hệ có `start` và `end` (năm); ô (thực thể, quan hệ) tạo thành dòng thời gian |
| **Conflicts (Cattan)** | Bảng phân loại 5 loại quan hệ giữa các nguồn (taxonomy) gắn với hành vi mong đợi | Taxonomy, không phải ontology | Lớp `Claim`, `Source`; quan hệ `contradicts`, `supersedes` (loại "thông tin mới hơn"), `agreesWith`; thuộc tính `statedAt`; loại xung đột là thuộc tính của cặp claim, mỗi loại kèm quy tắc trả lời |

Bảng ontology của các bài có phương pháp riêng (VersionRAG, TG-RAG...) nằm ở file `02_REPRODUCIBLE_METHODS.md`.
