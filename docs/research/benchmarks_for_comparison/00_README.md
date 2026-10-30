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
| [`04_TIDE`](temporal_retrieval/04_TIDE.md) | TIDE (văn bản luật hải quan sửa đổi; hỏi phiên bản nào có hiệu lực vào ngày nào) | 3,050 câu, 644 văn bản (1969 đến 2025), 8 loại câu | Accuracy, hội đồng 3 LLM chấm | Có (9 LLM, ba chế độ closed-book / gold context / RAG top-10) | Hugging Face `mahbubhimel/TIDE` (gated), MIT. **Văn bản code-mixed Bangla-English, hai hệ lịch** |

### Cơ chế 2: Timeline Summarization

| File | Bộ dữ liệu | Quy mô | Chỉ số | Có số baseline | Dữ liệu tải được? |
|---|---|---|---|---|---|
| [`01_TG_RAG_ECT_QA`](timeline_summarization/01_TG_RAG_ECT_QA.md) | ECT-QA (transcript báo cáo thu nhập), có kiểm thử cập nhật tăng dần | 1,005 câu cụ thể + 100 câu trừu tượng; 480 tài liệu | Correct/Refusal/Incorrect (LLM chấm), win rate | Có | Repo `hanjiale/Temporal-GraphRAG` (theo bài); giấy phép chưa rõ |
| [`02_TA_RAG_ADQAB`](timeline_summarization/02_TA_RAG_ADQAB.md) | ADQAB (tin cổ phiếu, 7 kiểu câu trước/sau/khoảng) | 525 câu trắc nghiệm; 27,037 bài | Accuracy tại k = 5, 10, 20, 50 | Có | Repo `kwunhang/TA-RAG` (theo bài); giấy phép chưa rõ |
| [`03_TDBench`](timeline_summarization/03_TDBench.md) | TDBench (sinh câu từ bảng dữ liệu có thời gian bằng SQL) | 9 bảng; 7,881 câu (Wikipedia + domain) | Accuracy, "time accuracy" | Có, nhưng đóng sách/không phải RAG | Repo `ssoy0701/tdbench` |
| [`04_TLQA`](timeline_summarization/04_TLQA.md) | TLQA (câu hỏi dạng danh sách gắn khoảng thời gian) | 1,655 câu (Political 881, Sports 774) | Precision/Recall/F1, Temporal Overlap, Temporal Jaccard | Có (GPT-4o-mini, Mistral 7B) | Repo `elixir-research-group/TLQA`, mã Apache-2.0 |

### Cơ chế 3: Conflict Resolution

| File | Bộ dữ liệu | Quy mô | Chỉ số | Có số baseline | Dữ liệu tải được? |
|---|---|---|---|---|---|
| [`01_MemoryAgentBench_FactConsolidation`](conflict_resolution/01_MemoryAgentBench_FactConsolidation.md) | FactConsolidation (fact mới đè fact cũ, đánh số thứ tự) | 100 câu một bước + 100 câu nhiều bước; ngữ cảnh 32K/64K/262K | SubEM | Có (10 hệ thống, gồm Mem0, HippoRAG-v2) | Hugging Face `ai-hyz/MemoryAgentBench`, MIT |
| [`02_LongMemEval`](conflict_resolution/02_LongMemEval.md) | LongMemEval (có `temporal-reasoning`, `knowledge-update`) | 500 câu; bản S khoảng 115K token | Accuracy do GPT-4o chấm | Có (Zep tự báo cáo, long-context LLM) | GitHub `xiaowu0162/LongMemEval`, MIT |
| [`03_VersionRAG_VersionQA`](conflict_resolution/03_VersionRAG_VersionQA.md) | VersionQA (tài liệu kỹ thuật có phiên bản) | 100 câu, 34 tài liệu | Accuracy (GPT-4.1 chấm) | Có (naive RAG, GraphRAG) | Repo `danielhuwiler/versionrag` có; **chưa xác nhận** có file VersionQA |
| [`04_ConflictBank`](conflict_resolution/04_ConflictBank.md) | ConflictBank (xung đột tri thức, có loại thời gian) | khoảng 513 nghìn câu QA trên Hub | chỉ số riêng của bài | Có | Hugging Face `CB_qa`, `CB_claim_evidence`; quá lớn nên phải lấy mẫu |
| [`05_EvoWiki`](conflict_resolution/05_EvoWiki.md) | EvoWiki (fact Wikidata đổi giữa ba snapshot, neo vào Wikipedia) | 10,264 câu (stable / evolved / uncharted); corpus 15K tài liệu gold | EM, precision câu trả lời lỗi thời | Có (Llama 3.1 8B, Mistral 7B; BM25, Contriever) | Dữ liệu trên MEGA, **repo chưa có mã ("Coming soon")** |
| [`06_FRESCO`](conflict_resolution/06_FRESCO.md) | FRESCO (re-ranker có ưu tiên bằng chứng mới nhất không, trên bản sửa Wikipedia) | 7,316 truy vấn (explicit + implicit), mỗi truy vấn 1 positive + 50 negative | MAP, nDCG@10, Hit@10, Obsolete Ratio | Có (19 re-ranker, không có bge-reranker-v2-m3 hay MiniLM) | Phải chạy `generate_data.sh`; dữ liệu CC-BY-NC |
| [`07_HoH`](conflict_resolution/07_HoH.md) | HoH (ảnh hưởng của thông tin lỗi thời lên RAG, snapshot Wikipedia theo tháng) | khoảng 96K cặp QA; tập đánh giá 10,000 câu | Perfect / Missing / Harmful (LLM chấm), hit@k | Có | Apache-2.0; chưa rõ có toàn văn các phiên bản bài hay chỉ câu evidence |
| [`08_RECON`](conflict_resolution/08_RECON.md) | RECON (hồ sơ dài: truyền lan vô hiệu hóa, xung đột nguồn) | 24 hồ sơ, 1,604 câu | Strict Accuracy, phân tích coverage | Có (Mem0, Mem0-Graph, long-context, RAG; tốt nhất 22.4%) | **Chưa công khai** (repo ẩn danh, chỉ hứa phát hành) |

## Bao phủ và chỗ hở

- **Cơ chế 1: tốt.** Có bốn lựa chọn, trong đó ba bộ dựa trên TimeQA/SituatedQA mà đồ án đã dùng. **TempRAGEval** và **TEMPO** là hai bộ có nhãn chunk gold nên đo được kiểu `hit@k`/`mrr` của đồ án; DyG-RAG chỉ so được EM/F1.
- **Cơ chế 2: yếu nhất.** Chưa có bộ nào đúng nghĩa "lịch sử một thực thể, nén gọn". ECT-QA và ADQAB là miền tài chính (một phần do LLM sinh), TLQA lấy đáp án từ infobox có cấu trúc nên dựng graph sẽ quá dễ, TDBench đo LLM đóng sách. Bộ `timeline_gold` tự dựng từ TimeQA (`docs/eval/08_TIMELINE_EVAL_DESIGN.md`) vẫn là bộ chính; các bộ này làm bộ phụ.
- **Cơ chế 3: nhiều lựa chọn hơn nhưng mỗi bộ có điểm yếu riêng.** FactConsolidation là fact phản thực, LongMemEval là hội thoại, ConflictBank do LLM sinh với mốc tương lai bịa, VersionQA là phiên bản phần mềm. Ba bộ mới dựa trên Wikipedia thay đổi thật: **HoH** (snapshot theo tháng, gold chứa đáp án, nhưng chủ yếu hỏi giá trị hiện tại), **EvoWiki** (ba snapshot Wikidata; nhãn gold không đảm bảo chứa đáp án; mã chưa phát hành), **FRESCO** (bản sửa Wikipedia, nhưng chỉ đo re-ranker với truy vấn "mới nhất"). **RECON** có nhóm truyền lan vô hiệu hóa và xung đột nguồn, nhưng chưa công khai. Mỗi bộ chỉ chạm một phần; chưa bộ nào đo `end_time` (Evolution) cùng `invalidated_at` (Falsehood) như thiết kế.
- **Không bộ nào đo `leakage_rate`** (chunk của tương lai lọt vào kết quả) và `invalidated_at` / Falsehood. Hai chỉ số này chỉ đánh giá được trên bộ tự dựng của đồ án.

## Đề xuất dùng (mỗi cơ chế nhiều bộ)

| Cơ chế | Bộ chính | Bộ phụ |
|---|---|---|
| 1 | TempRAGEval (đo `hit@k` trên chunk gold), DyG-RAG/TimeQA (EM/F1) | TEMPO (kiểm tổng quát hóa), LongMemEval phần `temporal-reasoning`, TIDE (nếu xử lý được tiếng Bengali và lịch Bangla) |
| 2 | `timeline_gold` tự dựng | ECT-QA (cập nhật tăng dần), TLQA, ADQAB, TDBench |
| 3 | HoH (Wikipedia thật, gold chứa đáp án), FactConsolidation (một bước), LongMemEval phần `knowledge-update` | FRESCO (kiểm cross-encoder), VersionQA, EvoWiki (khi có mã), RECON (khi công khai), ConflictBank (lấy mẫu phần temporal) |

Mọi so sánh nên **chạy lại baseline của chính đồ án** (Plain RAG, vector top-k) cùng LLM và cùng chunk, thay vì đặt cạnh số công bố, vì các bài dùng LLM, embedding và giao thức chấm khác nhau.

## Cách đọc độ tin cậy

- Các ghi chú được viết từ bản HTML của arXiv, README GitHub và Hugging Face; phần lớn **chưa đối chiếu với bản PDF**. Số baseline đều do chính các bài tự báo cáo.
- Mục 7 của mỗi file liệt kê chỗ chưa xác nhận. Những điểm quan trọng nhất:
  - Dữ liệu có thực sự tải và chạy được không: DyG-RAG (bộ con 2,613 câu), VersionQA, ECT-QA (số câu thật 1,005 hay 1,105: ba cách chia trong bài đều cộng ra 1,005), TempRAGEval (chưa mở CSV nên chưa rõ tên cột).
  - Giấy phép dữ liệu: mâu thuẫn hoặc chưa rõ ở TempRAGEval, TEMPO, ECT-QA, ADQAB, ConflictBank, EvoWiki, RECON; FRESCO là CC-BY-NC.
  - **Nhãn gold có chứa đáp án không**: HoH có (passage Relevant chứa đáp án đúng); EvoWiki và FRESCO **không đảm bảo** (distant supervision và khớp infobox); TempRAGEval, TEMPO, TIDE chưa chắc (xem mục 2 và 7 từng file). Cần đo tỉ lệ này ngay trên dữ liệu thật trước khi báo `hit@k`.
  - **Ngôn ngữ**: TIDE là Bangla-English code-mixed; mọi bộ khác dự kiến là tiếng Anh (phần lớn bài không nêu rõ).
  - FRESCO chỉ có truy vấn "mới nhất" nên không kiểm được chống rò rỉ tương lai; không có bge-reranker-v2-m3 hay MiniLM trong 19 re-ranker công bố, phải tự chạy.
  - Bài báo RECON: tên bài đúng là "Benchmarking Agent Memory for Compositional Reasoning over Long Contexts"; "Obfuscated Narratives" chỉ là cách giải thích tên viết tắt.
  - Số câu từng loại của LongMemEval: bài chỉ có phần trăm (khoảng 27% `temporal-reasoning`, 16% `knowledge-update`); số chính xác phải đếm từ JSON.
  - Trong bài TEMPO, abstract nói DiVeR có Temporal Coverage@10 cao nhất (71.4%) nhưng bảng cho ReasonIR 72.4%.
  - Số liệu của bài 2606.01435 (follow-up trên FactConsolidation) chưa xác nhận được; tiêu đề giữa trang và BibTeX khác nhau.
- ConflictBank trên Hub nhỏ hơn con số trong bài (khoảng 2.11 triệu dòng claim-evidence và 513 nghìn dòng QA so với 7.45 triệu và 553 nghìn); chưa rõ nguyên nhân.

## Liên hệ với tài liệu hiện có

- Ghi chú phương pháp (không lặp ở đây): `../temporal_retrieval/`, `../timeline_summarization/`, `../conflict_resolution/`.
- Ghi chú dataset đã có: `../../dataset/01` đến `06` (TimeQA, ChronoQA, StreamingQA, RealTimeQA, SituatedQA, TempLAMA).
- Hệ thống bộ nhớ so sánh: Zep, Mem0 ở `../knowledge_representation_and_integration/07_*`, `08_*`.
- Thiết kế đo Cơ chế 2: `../../eval/08_TIMELINE_EVAL_DESIGN.md`; kết quả Cơ chế 1: `../../eval/07_TUNE_VALID_RESULTS.md`.
