# Benchmark để so sánh hệ thống Time-Aware Agentic Memory

> Thư mục này trả lời một câu hỏi: **chạy hệ thống của đồ án trên bộ dữ liệu công khai nào để so sánh với các bài đã công bố**, cho từng cơ chế. Mỗi file là một bài báo cùng bộ dữ liệu của nó: nguồn, quy mô, chỉ số đo, baseline có số, ưu nhược, cách ánh xạ vào hệ thống của đồ án. Cách chọn: ưu tiên tiếng Anh, quy mô vừa phải (loại bộ quá lớn như ComplexTempQA 100 triệu câu), có baseline với số công bố, và phản ánh đúng cơ chế.
>
> Ghi ngày 2026-10-30. Cơ chế 1 = Temporal Retrieval (câu hỏi tại một mốc), Cơ chế 2 = Timeline Summarization (diễn biến theo thời gian), Cơ chế 3 = Conflict Resolution (thông tin mới đè thông tin cũ, hoặc tin sai).

## Bảng tổng hợp

### Cơ chế 1: Temporal Retrieval

| File | Bộ dữ liệu | Quy mô | Chỉ số | Có số baseline | Dữ liệu tải được? |
|---|---|---|---|---|---|
| [`01_DyG_RAG_TimeQA`](temporal_retrieval/01_DyG_RAG_TimeQA.md) | TimeQA (hard), TempReason (L2), ComplexTR | 2,613 / 5,397 / 312 câu | Accuracy, Recall theo trùng token | Có (9 hệ thống) | Repo có thư mục `datasets/`; **chưa xác nhận** đúng bộ con trong bài |
| [`02_MRAG_TempRAGEval`](temporal_retrieval/02_MRAG_TempRAGEval.md) | TempRAGEval (TimeQA + SituatedQA, có chunk gold) | 1,000 câu; corpus Wikipedia 33.1 triệu chunk | AR@k, ER@k, EM, F1 | Có | Hugging Face `siyue/TempRAGEval` (gated, CSV); giấy phép mâu thuẫn giữa các nguồn |
| [`03_TEMPO`](temporal_retrieval/03_TEMPO.md) | TEMPO (13 domain, truy xuất cần suy luận) | 1,730 câu, corpus 1.65 triệu tài liệu | NDCG@10, Temporal Coverage@k | Có (12 hệ thống, tốt nhất 32.0 NDCG@10) | Hugging Face `tempo26/Tempo`; giấy phép dữ liệu chưa rõ |
| [`04_TempRetriever`](temporal_retrieval/04_TempRetriever.md) | ChroniclingAmericaQA (báo Mỹ cũ, OCR, có `publication_date`) | Tập con test 1,268 câu; 151,485 passage | Top-k accuracy (chứa chuỗi đáp án), EM/Recall/Contains | Có (VanillaDPR, DateAsTag, TS-Retriever...; không có BM25) | Hugging Face `Bhawna/ChroniclingAmericaQA`, MIT. Repo phương pháp trống |

### Cơ chế 2: Timeline Summarization

| File | Bộ dữ liệu | Quy mô | Chỉ số | Có số baseline | Dữ liệu tải được? |
|---|---|---|---|---|---|
| [`01_TG_RAG_ECT_QA`](timeline_summarization/01_TG_RAG_ECT_QA.md) | ECT-QA (transcript báo cáo thu nhập), có kiểm thử cập nhật tăng dần | 1,005 câu cụ thể + 100 câu trừu tượng; 480 tài liệu | Correct/Refusal/Incorrect (LLM chấm), win rate | Có | Repo `hanjiale/Temporal-GraphRAG` (theo bài); giấy phép chưa rõ |
| [`02_TA_RAG_ADQAB`](timeline_summarization/02_TA_RAG_ADQAB.md) | ADQAB (tin cổ phiếu, 7 kiểu câu trước/sau/khoảng) | 525 câu trắc nghiệm; 27,037 bài | Accuracy tại k = 5, 10, 20, 50 | Có | Repo `kwunhang/TA-RAG` (theo bài); giấy phép chưa rõ |
| [`03_TLQA`](timeline_summarization/03_TLQA.md) | TLQA (câu hỏi dạng danh sách gắn khoảng thời gian) | 1,655 câu (Political 881, Sports 774) | Precision/Recall/F1, Temporal Overlap, Temporal Jaccard | Có (GPT-4o-mini, Mistral 7B) | Repo `elixir-research-group/TLQA`, mã Apache-2.0 |

### Cơ chế 3: Conflict Resolution

| File | Bộ dữ liệu | Quy mô | Chỉ số | Có số baseline | Dữ liệu tải được? |
|---|---|---|---|---|---|
| [`01_MemoryAgentBench_FactConsolidation`](conflict_resolution/01_MemoryAgentBench_FactConsolidation.md) | FactConsolidation (fact mới đè fact cũ, đánh số thứ tự) | 100 câu một bước + 100 câu nhiều bước; ngữ cảnh 32K/64K/262K | SubEM | Có (10 hệ thống, gồm Mem0, HippoRAG-v2) | Hugging Face `ai-hyz/MemoryAgentBench`, MIT |
| [`02_LongMemEval`](conflict_resolution/02_LongMemEval.md) | LongMemEval (có `temporal-reasoning`, `knowledge-update`) | 500 câu; bản S khoảng 115K token | Accuracy do GPT-4o chấm | Có (Zep tự báo cáo, long-context LLM) | GitHub `xiaowu0162/LongMemEval`, MIT |
| [`03_VersionRAG_VersionQA`](conflict_resolution/03_VersionRAG_VersionQA.md) | VersionQA (tài liệu kỹ thuật có phiên bản) | 100 câu, 34 tài liệu | Accuracy (GPT-4.1 chấm) | Có (naive RAG, GraphRAG) | Repo `danielhuwiler/versionrag` có `data/test/evaluation_set.csv` (24 KB, xác nhận 2026-10-31) |
| [`04_HoH`](conflict_resolution/04_HoH.md) | HoH (ảnh hưởng của thông tin lỗi thời lên RAG, snapshot Wikipedia theo tháng) | khoảng 96K cặp QA; tập đánh giá 10,000 câu | Perfect / Missing / Harmful (LLM chấm), hit@k | Có | Apache-2.0; chưa rõ có toàn văn các phiên bản bài hay chỉ câu evidence |
| [`05_Conflicts_Cattan`](conflict_resolution/05_Conflicts_Cattan.md) | "Conflicts" của Google (5 loại xung đột, tài liệu Google Search thật) | 458 câu; Freshness 62, No conflict 161 | Accuracy dự đoán loại xung đột, Expected behavior | Có (6 mô hình) | GitHub `google-research-datasets/rag_conflicts` (đã archive), `conflicts.jsonl` 46.7 MB. Chỉ phần Freshness liên quan thời gian |

## Đã tải thử dữ liệu (2026-10-31)

Tải thật từ GitHub/Hugging Face, mở ra đếm; chưa chạy LLM. Bộ nào không tải được hoặc không tiếng Anh, không có gold dùng được thì đã xóa khỏi folder (TIDE, TimelyRAG, RA-RAG, CONFACT, RAMDocs, CAGB, TMRL, TPOUR, TANGO, Freshness, Time-sensitive RAG CIKM'24, TDBench, ConflictBank, FRESCO, EvoWiki, RECON, RAGuard, WikiContradict, NatConfQA).

| Bộ | Kết quả kiểm tra | Dùng được để so không |
|---|---|---|
| **TLQA** (Cơ chế 2) | Test 497 câu (251 political, 246 teams), median 8 đáp án/câu, mỗi đáp án kèm khoảng thời gian. Gold evidence chỉ là infobox (median 1.3K ký tự); tên đáp án khớp nguyên văn trong evidence chỉ 2191/4296 (≈51%, do định dạng như "→ X (loan)"). | Có: đúng dạng "lịch sử một thực thể", có F1/Temporal Overlap, baseline GPT-4o-mini. Nhưng không kèm kho văn bản, phải lấy trang Wikipedia theo `wikipedia_title`. |
| **HoH** (Cơ chế 3) | 111,972 dòng. Mỗi dòng: `question`, `answer` (hiện tại), `evidence` (1 câu), `outdated_infos` (đáp án cũ + câu cũ + ngày), `last_modified_time`, `document`. | Có: câu cũ/mới kèm mốc thời gian dùng thẳng làm `start_time`. Hạn chế: kho chỉ là các câu evidence (không phải bài Wikipedia nguyên văn), câu hỏi chủ yếu về giá trị hiện tại. |
| **FactConsolidation** (Cơ chế 3) | Danh sách fact đánh số, fact sau đè fact trước; ngữ cảnh 6K–262K token. | Có: SubEM, baseline 10 hệ thống (có Mem0). Hạn chế: không có mốc thời gian thật, chỉ có thứ tự số. |
| **VersionQA** (Cơ chế 3) | 100 câu, 3 cột `Type`/`Question`/`Answer` (đáp án tự do, GPT-4.1 chấm). 34 tài liệu release notes (md/pdf) kèm repo. | Có nhưng nhỏ, miền phần mềm, không có gold chunk. |
| **ADQAB** (Cơ chế 2) | 525 câu trắc nghiệm về xu hướng giá cổ phiếu, kho `C_final.jsonl` 127 MB. Không có gold chunk. | So được accuracy với BM25/Naive/+Reranker của họ; miền tài chính. |
| **ECT-QA** (Cơ chế 2) | Kho `base.jsonl.gz` 7.9 MB + `new.jsonl.gz` 1.9 MB, câu hỏi có `evidence_list`, `question_type`, `num_hops`; nhiều câu "unanswerable". | Dùng được; chấm bằng LLM judge và miền tài chính. |
| **LongMemEval** (Cơ chế 3) | Hugging Face `xiaowu0162/longmemeval-cleaned`: file `s`, `m`, `oracle`, không gated, MIT. Chưa tải (lớn). | Có; là hội thoại, không phải Wikipedia. |

## Bao phủ và chỗ hở

- **Cơ chế 1:** có TempRAGEval (gold chunk, nhưng phải thu hẹp kho 33.1M), DyG-RAG/TimeQA, TEMPO, TempRetriever (ChroniclingAmericaQA).
- **Cơ chế 2:** TLQA là bộ gần nhất với "lịch sử một thực thể" mà đã kiểm tải được. `timeline_gold` tự dựng từ TimeQA (`docs/eval/08_TIMELINE_EVAL_DESIGN.md`) vẫn là bộ chính; ECT-QA, ADQAB làm phụ.
- **Cơ chế 3:** HoH (có mốc thời gian cũ/mới), FactConsolidation, LongMemEval là ba bộ tải được và có baseline. Chưa bộ nào đo `end_time` (Evolution) cùng `invalidated_at` (Falsehood) như thiết kế.
- **Xung đột về nguồn: không làm.** Phạm vi Cơ chế 3 chỉ gồm xung đột thời gian (Evolution). Đã tìm và kiểm: chưa có bộ công khai tiếng Anh nào dùng độ tin cậy nguồn làm yếu tố quyết định đáp án; bộ gần nhất (CONFACT, ConfRAG) đã bị loại khỏi folder. Có thể nêu như hướng mở trong luận văn.
- **Không bộ nào đo `leakage_rate`** (chunk của tương lai lọt vào kết quả) hay `invalidated_at` / Falsehood thật. Hai chỉ số này chỉ đánh giá được trên bộ tự dựng của đồ án.

## Đề xuất dùng (mỗi cơ chế nhiều bộ)

| Cơ chế | Bộ chính | Bộ phụ |
|---|---|---|
| 1 | TempRAGEval (kho thu hẹp, đo `hit@k` trên gold chunk), ChroniclingAmericaQA | DyG-RAG/TimeQA, TEMPO |
| 2 | `timeline_gold` tự dựng, TLQA | ECT-QA, ADQAB |
| 3 | HoH, FactConsolidation, LongMemEval phần `knowledge-update` | VersionQA |

Mọi so sánh nên **chạy lại baseline của chính đồ án** (Plain RAG, vector top-k) cùng LLM và cùng chunk, rồi đối chiếu *khoảng cách giữa các hệ* với khoảng cách trong bài. Không đặt số tuyệt đối của đồ án cạnh số công bố, vì LLM, embedding và giao thức chấm khác nhau.

## Cách đọc độ tin cậy

- Ghi chú viết từ bản HTML arXiv, README và Hugging Face; phần lớn **chưa đối chiếu PDF**. Số baseline đều do bài tự báo cáo. Mục "Đã tải thử" ở trên là phần duy nhất mình kiểm trực tiếp trên dữ liệu.
- Mục 7 của mỗi file liệt kê chỗ chưa xác nhận.
- Giấy phép dữ liệu còn chưa rõ ở: TempRAGEval, TEMPO, ECT-QA, ADQAB (CC BY-NC-SA), Conflicts, TLQA (mã Apache-2.0, dữ liệu gốc Wikipedia).
- Cần đo tỉ lệ **gold chunk có chứa đáp án** trước khi báo `hit@k` ở TempRAGEval, TLQA, HoH.
- Số câu từng loại của LongMemEval chỉ xấp xỉ từ phần trăm; số chính xác phải đếm từ JSON.
- Trong bài TEMPO, abstract nói DiVeR có Temporal Coverage@10 cao nhất (71.4%) nhưng bảng cho ReasonIR 72.4%.
