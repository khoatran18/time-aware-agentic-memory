# 14. Cơ chế 1: kết quả 15 hệ trên `tune` 200 câu, có judge LLM (2026-11-26)

Kết quả đo Cơ chế 1 (truy xuất thời gian, chỉ vector, không graph) bằng DeepSeek flash và chấm bằng GLM-5.3. Kế hoạch và việc còn lại: `docs/planning/03_MECH1_DEEPSEEK_AND_AGENT_EVAL.md` mục 14 đến 18. Kiểm tay 50 câu của judge: `13_JUDGE_M1_CHECK_50.md`. Biểu đồ: `figures/m1_tune_15systems.svg`. **Cập nhật 2026-11-26 (chiều): đã đo thêm 395 câu `tune` còn lại và gộp thành 595 câu, A1, A3 đã chấm lại; xem mục 7.**

## 1. Đã đo gì

- **Dữ liệu:** `tune` 200 câu TimeQA = `tune100` + `tune100c` (100 câu mỗi tập). Chưa đụng `valid`, `test_clean`. Mỗi cấu hình chạy một lần.
- **Trả lời và agent:** DeepSeek flash (`opencode_deepseek_flash`, thinking tắt), prompt `answer_m1_v4` (pipeline) và `agent_m1_v4` (agent), top-5 đoạn cho pipeline.
- **Cấu hình thời gian:** `time_mode = range`, `decay_from = end` cho mọi thành phần thời gian (P6 đến P10 và `temporal_search` của A4, A5).
- **Judge:** GLM-5.3 qua OpenCode Go (`opencode_glm_5_3`, thinking tắt), prompt `judge_m1.md`, mỗi cặp (câu hỏi, đáp án) một lần gọi, 200 lần mỗi hệ, tổng 3.000 lần, không lỗi.

| Hệ | Là gì |
|---|---|
| P1 | dense (vector) |
| P2 | hybrid (dense + BM25) |
| P3, P4, P5 | dense + cross-encoder (MiniLM L6, MiniLM L12, bge) |
| P6 | Temporal (lọc `start_time <= T_req` + điểm thời gian), không cross-encoder |
| P7, P8 | P6 + cross-encoder L6, L12 |
| P9 | P6 + bge, trộn điểm |
| P10 | cấu hình X của Cơ chế 1 (cấu hình chính) |
| A1 | agent kiểu A: `grep`, `read_page` trên văn bản thuần |
| A2 | agent kiểu B: `vector_search`, `read_chunk` |
| A3 | agent kiểu C: A + B |
| A4 | B + `temporal_search` (range) |
| A5 | C + `temporal_search` (range) |

## 2. Cách tính các điểm

**Điểm ngoài judge (cho cả pipeline và agent)**, so với danh sách gold (`tam.generation.scoring`); agent chấm trên dòng `Answer:`:
- **EM:** đáp án sau khi chuẩn hóa trùng đúng một gold. Câu từ chối tính 0.
- **F1:** F1 mức từ giữa đáp án và gold khớp nhất.
- **contains:** gold nằm trong đáp án hoặc ngược lại sau chuẩn hóa.
- **Từ chối:** tỉ lệ câu hệ không trả lời (pipeline: cờ `refused`; agent: dòng `Answer:` trống hoặc câu kiểu "không thể trả lời").

**Đầu vào của judge (mỗi câu):** câu hỏi (có nêu mốc thời gian), danh sách gold, các đoạn hệ đã có khi trả lời (pipeline: top-5 đoạn từ Qdrant theo `context_ids`; agent: các đoạn thấy trong kết quả công cụ, tối đa 20), danh sách số đoạn hệ nêu làm bằng chứng, và đáp án của hệ (hoặc "không trả lời").

**Đầu ra của judge (schema `Judgment`, `scripts/judge_answers.py`, ghi vào `judgments.jsonl`):**

| Trường | Giá trị | Ý nghĩa |
|---|---|---|
| `reason` | 1–2 câu | lý do, nêu đoạn hoặc gold đã dựa vào (không dùng nháy kép) |
| `verdict` | correct / partial / wrong / refusal | đáp án có đúng cho đúng thời điểm hỏi không (judge tự xét, dùng đoạn văn khi gold sai) |
| `match_type` | same / format_variant / alternate_valid / subset / superset / different / none | quan hệ với gold: giống, khác cách viết, khác gold nhưng đúng theo đoạn, chỉ một phần gold, gold cộng thêm, khác hẳn, từ chối |
| `matches_gold` | true/false | chỉ so đáp án với gold (bỏ qua khác biệt cách viết); không phụ thuộc gold đúng hay sai |
| `gold_in_passages` | true/false | gold (hoặc nghĩa của nó) có trong các đoạn hệ có: **context recall** |
| `relevant_passages` | danh sách số | đoạn nói về đúng thứ được hỏi và đúng khoảng thời gian: dùng tính **context precision** |
| `grounded` | true/false | có đoạn nào nêu đáp án (bất kể thời kỳ): **faithfulness**; câu từ chối = false |
| `hallucinated` | true/false | đáp án chứa tên/số/ngày không có trong đoạn nào (bịa hoặc dùng kiến thức ngoài); đáp án sai nhưng có trong đoạn (khác thời kỳ) KHÔNG phải bịa |
| `answer_relevant` | true/false | đáp án đúng loại thứ được hỏi (người cho "ai"...), kể cả khi sai |
| `completeness` | complete / incomplete / not_applicable | có đủ các mục câu hỏi cần không |
| `refusal_quality` | not_refusal / justified / borderline / unjustified | từ chối có đúng lúc không: justified = không đoạn nào có đáp án; borderline = có đoạn gợi ý yếu; unjustified = có đoạn nêu đáp án cho đúng thời điểm mà vẫn từ chối |
| `citation_support` | true / false / none | các đoạn hệ trích dẫn có nêu đáp án không; none = không trích dẫn |
| `label_issue` | none / multi_gold / ambiguous / gold_not_an_answer / time_mismatch | nhãn gold có vấn đề: nhiều đáp án đúng, câu mơ hồ, gold không phải câu trả lời, gold thuộc thời điểm khác |

Mã thêm: `answer_in_passages` (kiểm chuỗi đáp án có trong đoạn), `n_passages`, `cited`.

**Điểm tổng hợp trên mỗi hệ (200 câu):**
- **Judge nghiêm** = tỉ lệ `matches_gold = true`. **Judge rộng** = tỉ lệ `verdict = correct` (gồm `alternate_valid`: đúng theo đoạn dù khác gold). Hai điểm này bù cho EM chấm sai khi cách viết khác hoặc gold nhiều giá trị.
- **partial** = tỉ lệ `verdict = partial`.
- **grounded** (faithfulness) = tỉ lệ `grounded = true`; **bịa** = tỉ lệ `hallucinated = true` (cả hai trên tất cả câu, câu từ chối tính grounded = false).
- **Từ chối đúng lúc** = trong các câu `verdict = refusal`, tỉ lệ `refusal_quality = justified` (số trong ngoặc là số câu từ chối).
- **Context recall** = tỉ lệ `gold_in_passages = true`. **Context precision** = trung bình mỗi câu của (số đoạn trong `relevant_passages` / số đoạn hệ có).
- `answer_relevant`, **đủ ý** (`completeness = complete`) và **trích dẫn đúng** (`citation_support = true` trên các câu có trích dẫn) tính trên các câu có trả lời. `label_issue ≠ none` = tỉ lệ câu judge thấy nhãn có vấn đề.

## 2b. Giải thích các điểm bằng ví dụ

- **Context recall** (0 đến 1, cao là tốt) = hệ có **lấy được đoạn chứa đáp án gold** hay không (đo truy xuất, chưa nói gì tới việc trả lời đúng). Ví dụ: câu hỏi "ai là chỉ huy Sư đoàn miền Đông tháng 4/1978", gold "Bengt Selander"; nếu trong các đoạn hệ có một đoạn nêu tên đó thì `gold_in_passages = true`. Với agent, "các đoạn hệ có" là mọi đoạn agent đã đọc qua các lần gọi công cụ (tối đa 20), nên recall của agent (0,98) cao hơn pipeline chỉ có top-5 (0,72–0,90): agent được tìm nhiều lần.
- **Context precision** (0 đến 1) = trong các đoạn hệ có, **bao nhiêu phần là đoạn liên quan** (nói về đúng thứ được hỏi và đúng khoảng thời gian; đoạn đúng chủ thể nhưng khác thời kỳ không tính). Ví dụ: top-5 có 1 đoạn đúng thời kỳ thì precision = 1/5 = 0,2. Điểm thấp (0,2–0,35) là bình thường: đa số câu chỉ có 1 đến 2 đoạn đúng thời kỳ, các đoạn còn lại là thời kỳ khác của cùng một trang. Agent thấp hơn (A2 0,195) vì đọc tới 20 đoạn; không đọc là agent kém. Dùng để so các cách truy xuất cùng top-5 (P9 0,345 và P10 0,339 chọn đoạn đúng thời kỳ tốt nhất; P2 hybrid 0,243 kém nhất).
- **Đủ ý (`completeness`)** = đáp án có **đưa đủ các mục câu hỏi cần**. `complete`: đủ. `incomplete`: câu hỏi hoặc gold cần nhiều mục mà đáp án nêu bớt, ví dụ gold gồm "Hon-Kawagoe Station" và "Kokubunji" (hai đáp án đều đúng), đáp án chỉ nêu "Kokubunji" thì `verdict = correct` nhưng `completeness = incomplete`. Câu một đáp án thì tính `not_applicable`. Cột "đủ ý" trong bảng = tỉ lệ `complete` trên các câu có trả lời; đây là điểm chất lượng phụ, không thay cho độ đúng. A4 0,797 và A2 0,765 cao nhất.
- **Faithfulness (`grounded`)** = đáp án có xuất hiện trong một đoạn nào đó hệ đã thấy (không xét đúng thời kỳ). **Bịa (`hallucinated`)** = đáp án chứa tên, số, ngày không nằm trong đoạn nào. Hai điểm này đo hệ có tự nghĩ ra không, khác với đúng/sai.
- **Từ chối đúng lúc** = trong các câu hệ từ chối, tỉ lệ từ chối mà **thật sự không đoạn nào có đáp án** cho thời điểm đó. `unjustified` = có đoạn nêu đáp án cho đúng thời điểm mà vẫn từ chối.

### Vì sao "từ chối đúng lúc" của agent (0,31–0,43) thấp hơn pipeline (0,76–0,94)

Đếm trên 200 câu mỗi hệ, các câu từ chối (kèm số ca gold có trong đoạn):

| Hệ | Số từ chối | justified | unjustified | borderline | gold có trong đoạn |
|---|---|---|---|---|---|
| P1 | 55 | 46 | 7 | 2 | 15 |
| P6 | 23 | 20 | 3 | 0 | 6 |
| P10 | 17 | 16 | 1 | 0 | 6 |
| A2 | 13 | 4 | 9 | 0 | 12 |
| A3 | 21 | 9 | 10 | 2 | 16 |
| A4 | 13 | 5 | 7 | 1 | 13 |
| A5 | 14 | 6 | 8 | 0 | 10 |

Nguyên nhân: pipeline chỉ thấy top-5, nên khi từ chối thường là vì truy xuất trượt (gold không nằm trong 5 đoạn): từ chối đó là đúng. Agent tìm nhiều lần nên gần như luôn có đoạn chứa gold (recall 0,98): khi agent vẫn từ chối thì thường là đã thấy nhưng đọc quá chặt (đoạn không ghi khoảng thời gian, hoặc hơi lệch mốc). Agent từ chối rất ít (13–14 câu) nên mỗi ca đổi nhãn làm tỉ lệ nhảy khoảng 8 điểm phần trăm: đây là xu hướng, không phải con số chắc. Ý nghĩa: từ chối của agent là lỗi có thể sửa bằng prompt, còn từ chối của pipeline chủ yếu là lỗi truy xuất.

## 3. Vì sao A1 chưa có điểm judge dùng được

A1 **đã đo** EM, F1, contains, từ chối (0,595 / 0,671 / 0,655 / 0,115) và **đã chạy judge 200 câu**, nhưng các điểm judge của A1 không dùng được. Nguyên nhân: judge cần "các đoạn hệ đã thấy". Với agent, mã (`agent_passages` trong `scripts/judge_answers.py`) chỉ tách đoạn từ kết quả công cụ có dạng chunk của `vector_search` (`/wiki/<Trang>#<id> (<khoảng hiệu lực>) <văn bản>`). `grep` và `read_page` của A1 trả định dạng khác (tên trang, số đoạn, trích dòng; `read_page` trả cả trang), nên regex không tách được gì: `n_passages = 0` cho cả 200 câu. Judge không có đoạn nào để đối chiếu, nên `grounded` = 0, `bịa` = 0,405 (đáp án nào cũng bị coi là không có trong đoạn), recall = precision = 0; `judge nghiêm/rộng` của A1 chỉ dựa vào đáp án và gold nên cũng chưa tin được. A3 (grep + vector) chỉ thiếu phần `grep`/`read_page`, nên các cột đoạn văn bị hụt một phần. Cách sửa: cho `agent_passages` đọc cả kết quả `grep` và `read_page` rồi chấm lại A1, A3 (~400 lần gọi GLM); chưa làm, chờ người dùng đồng ý.

## 4. Kết quả
**Phạm vi:** `tune100` + `tune100c` (200 câu), `m1_v4`, top-5, DeepSeek flash (thinking tắt), chỉ `time_mode = range`, `decay_from = end`. Judge: GLM-5.3 (`opencode_glm_5_3`, thinking tắt), prompt `judge_m1.md`, đủ 200 câu mỗi hệ (30 lượt chạy × 100 câu, không lỗi). Chưa đụng `valid`, `test_clean`. Mỗi cấu hình chạy một lần. Bảng sinh bởi `local/scripts/final_table.py` (kết quả `local/results/final_table.json`); thư mục judge ghi trong `local/logs/rest2/status.json`; log `local/logs/rest2/`, chạy bằng `local/scripts/run_rest2.py` (10 luồng DeepSeek + 10 luồng GLM theo lời người dùng sau khi 20 + 20 gây 429).

| Hệ | EM | F1 | contains | từ chối | judge nghiêm | judge rộng | grounded | bịa | từ chối đúng lúc (số từ chối) | context recall | context precision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 dense | 0,430 | 0,503 | 0,450 | 0,275 | 0,495 | 0,600 | 0,720 | 0,005 | 0,84 (55) | 0,720 | 0,255 |
| P2 hybrid | 0,360 | 0,434 | 0,375 | 0,340 | 0,445 | 0,525 | 0,650 | 0,005 | 0,85 (68) | 0,665 | 0,243 |
| P3 dense+L6 | 0,510 | 0,567 | 0,535 | 0,205 | 0,575 | 0,670 | 0,785 | 0,005 | 0,80 (41) | 0,820 | 0,281 |
| P4 dense+L12 | 0,490 | 0,558 | 0,525 | 0,210 | 0,585 | 0,670 | 0,790 | 0,000 | 0,83 (42) | 0,795 | 0,281 |
| P5 dense+bge | 0,510 | 0,580 | 0,560 | 0,170 | 0,595 | 0,710 | 0,820 | 0,005 | 0,76 (34) | 0,840 | 0,298 |
| P6 Temporal | 0,605 | 0,672 | 0,640 | 0,115 | 0,685 | 0,755 | 0,875 | 0,000 | 0,87 (23) | 0,845 | 0,302 |
| P7 +L6 | 0,605 | 0,670 | 0,635 | 0,090 | 0,675 | 0,765 | 0,910 | 0,000 | 0,78 (18) | 0,880 | 0,313 |
| P8 +L12 | 0,595 | 0,657 | 0,620 | 0,110 | 0,670 | 0,765 | 0,880 | 0,010 | 0,77 (22) | 0,835 | 0,298 |
| P9 +bge mix | 0,630 | 0,698 | 0,670 | 0,080 | 0,715 | 0,795 | 0,920 | 0,000 | 0,88 (16) | 0,895 | 0,345 |
| P10 X | **0,640** | 0,697 | 0,675 | 0,085 | **0,720** | 0,785 | 0,910 | 0,005 | 0,94 (17) | 0,900 | 0,339 |
| A1 grep | 0,595 | 0,671 | 0,655 | 0,115 | *không dùng được* | *không dùng được* | | | | | |
| A2 vector | **0,650** | 0,719 | 0,695 | 0,065 | **0,750** | 0,835 | 0,935 | 0,000 | 0,31 (13) | 0,975 | 0,195 |
| A3 grep+vector | 0,610 | 0,681 | 0,670 | 0,105 | 0,700 | 0,745 | 0,735* | 0,110* | 0,43 (21) | 0,810* | 0,242* |
| A4 +temporal (range) | 0,625 | 0,697 | 0,680 | 0,065 | **0,750** | **0,870** | 0,930 | 0,000 | 0,38 (13) | 0,985 | 0,223 |
| A5 +temporal (range) | 0,620 | 0,697 | 0,685 | 0,070 | 0,720 | 0,835 | 0,905 | 0,020 | 0,43 (14) | 0,930 | 0,299 |

(`judge nghiêm` = `matches_gold`; `judge rộng` = `verdict = correct`, gồm `alternate_valid`; `partial` ≤ 0,02 ở mọi hệ. Lượt/số bước agent: A1 3,54; A2 2,63; A3 3,10; A4 2,48; A5 2,79.)

Biểu đồ: `docs/eval/figures/m1_tune_15systems.svg` (EM, judge nghiêm, judge rộng; từ chối, từ chối đúng lúc, context recall cho 14 hệ, bỏ A1).

**Các điểm còn lại (cùng 200 câu mỗi hệ):** `answer_relevant`, `đủ ý` và `trích dẫn đúng` tính trên các câu có trả lời (không từ chối; trích dẫn tính trên câu có trích dẫn, số trong ngoặc là số câu). `label_issue ≠ none` = tỉ lệ câu judge thấy nhãn có vấn đề (nhiều gold, mơ hồ, lệch thời gian...), chỉ ở mức xu hướng.

| Hệ | F1 | contains | partial | grounded | bịa | context precision | answer_relevant | đủ ý (complete) | trích dẫn đúng (citation true) | label_issue ≠ none | lượt agent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 0.503 | 0.450 | 0.005 | 0.720 | 0.005 | 0.255 | 0.993 | 0.662 | 0.98 (145) | 0.160 | – |
| P2 | 0.434 | 0.375 | 0.005 | 0.650 | 0.005 | 0.243 | 0.992 | 0.682 | 0.98 (132) | 0.180 | – |
| P3 | 0.567 | 0.535 | 0.005 | 0.785 | 0.005 | 0.281 | 0.987 | 0.717 | 0.99 (159) | 0.185 | – |
| P4 | 0.558 | 0.525 | 0.005 | 0.790 | 0.000 | 0.281 | 1.000 | 0.747 | 0.99 (158) | 0.160 | – |
| P5 | 0.580 | 0.560 | 0.000 | 0.820 | 0.005 | 0.298 | 1.000 | 0.711 | 0.99 (166) | 0.200 | – |
| P6 | 0.672 | 0.640 | 0.010 | 0.875 | 0.000 | 0.302 | 0.989 | 0.712 | 0.99 (177) | 0.165 | – |
| P7 | 0.670 | 0.635 | 0.020 | 0.910 | 0.000 | 0.313 | 1.000 | 0.720 | 0.99 (182) | 0.180 | – |
| P8 | 0.657 | 0.620 | 0.005 | 0.880 | 0.010 | 0.298 | 0.994 | 0.697 | 0.99 (178) | 0.175 | – |
| P9 | 0.698 | 0.670 | 0.015 | 0.920 | 0.000 | 0.345 | 1.000 | 0.739 | 1.00 (184) | 0.195 | – |
| P10 | 0.697 | 0.675 | 0.010 | 0.910 | 0.005 | 0.339 | 1.000 | 0.732 | 0.99 (183) | 0.165 | – |
| A1 | 0.671 | 0.655 | 0.020 | n/a | n/a | n/a | 1.000 | 0.670 | n/a | 0.070 | 3.54 |
| A2 | 0.719 | 0.695 | 0.010 | 0.935 | 0.000 | 0.195 | 0.995 | 0.765 | 1.00 (186) | 0.185 | 2.63 |
| A3 | 0.681 | 0.670 | 0.020 | 0.735 | 0.110 | 0.242 | 1.000 | 0.704 | 0.97 (98) | 0.185 | 3.10 |
| A4 | 0.697 | 0.680 | 0.005 | 0.930 | 0.000 | 0.223 | 1.000 | 0.797 | 0.99 (187) | 0.215 | 2.48 |
| A5 | 0.697 | 0.685 | 0.010 | 0.905 | 0.020 | 0.299 | 1.000 | 0.763 | 0.98 (133) | 0.205 | 2.79 |

### Chi phí: token và USD (DeepSeek flash, không tính judge)

Giá lấy từ `planning/03` mục 7 (dòng chi phí): 0,15 / 0,003 / 0,60 USD mỗi triệu token vào / token vào trúng cache / token ra (ngoài giờ cao điểm; giờ cao điểm gấp đôi). USD = (vào − cache) × 0,15 + cache × 0,003 + ra × 0,60, giả định `cached_input_tokens` là một phần của `input_tokens`. Agent: lấy từ `agent_calls.jsonl` (đủ 200 câu, kể cả lượt phát lại cache vì cache lưu số đo gốc). Pipeline: mỗi câu đúng một lần gọi; trung bình trên các lần gọi quan sát được trong `llm_calls.jsonl` (P2, P3, P4 thấy 100/200, P5 thấy 36, P7 154, P8 175 vì phần còn lại phát lại từ cache sau lần dừng giữa chừng), rồi nhân lên 200 câu; token mỗi lần gọi pipeline gần bằng nhau (cùng prompt, top-5) nên ngoại suy ổn. Script: `local/scripts/cost_table.py`.

| Hệ | lượt LLM/câu | token vào/câu | trong đó cache | token ra/câu | USD/câu | USD/200 câu |
|---|---|---|---|---|---|---|
| P1 | 1.00 | 1675 | 758 | 27 | 0.00016 | 0.031 |
| P2 | 1.00 | 1703 | 760 | 26 | 0.00016 | 0.032 |
| P3 | 1.00 | 1757 | 760 | 28 | 0.00017 | 0.034 |
| P4 | 1.00 | 1760 | 760 | 27 | 0.00017 | 0.034 |
| P5 | 1.00 | 1765 | 725 | 28 | 0.00017 | 0.035 |
| P6 | 1.00 | 1720 | 806 | 28 | 0.00016 | 0.031 |
| P7 | 1.00 | 1757 | 774 | 28 | 0.00017 | 0.033 |
| P8 | 1.00 | 1718 | 761 | 28 | 0.00016 | 0.033 |
| P9 | 1.00 | 1758 | 761 | 28 | 0.00017 | 0.034 |
| P10 | 1.00 | 1766 | 760 | 28 | 0.00017 | 0.034 |
| A1 | 3.54 | 8275 | 5089 | 261 | 0.00065 | 0.130 |
| A2 | 2.63 | 6594 | 3153 | 228 | 0.00066 | 0.132 |
| A3 | 3.10 | 9056 | 5693 | 245 | 0.00067 | 0.134 |
| A4 | 2.48 | 6226 | 3518 | 234 | 0.00056 | 0.111 |
| A5 | 2.79 | 8917 | 5418 | 268 | 0.00070 | 0.140 |

Tổng 15 hệ x 200 câu khoảng 0.98 USD cho phần trả lời và agent. Agent tốn gấp khoảng 3 đến 4 lần pipeline (2,5 đến 3,5 lượt LLM, 6.000 đến 9.000 token vào mỗi câu so với khoảng 1.700). Judge không gồm trong bảng này (xem dưới). Thời gian: xem bảng ngay dưới.

**Judge GLM-5.3 (OpenCode Go):** giá 1,40 / 0,26 / 4,40 USD mỗi triệu token vào / token vào trúng cache / token ra (tra 2026-11-26 trên [trang Go của OpenCode](https://opencode.ai/docs/go/) và [OpenCode Data](https://opencode.ai/data/zhipuai/glm-5-3.md)). Số liệu thật: cộng mọi lần gọi `llm_call` của `glm-5.3` trong `llm_calls.jsonl` của mọi thư mục `output/20261126_*` từ 00:34 (kể cả các thư mục dừng giữa chừng, vì lượt gọi thật nằm ở đó; các lần chạy lại chỉ phát lại cache): **3.004 lần gọi thành công, 0 lỗi, 7,99 triệu token vào (4,63 triệu trúng cache), 0,50 triệu token ra, trung bình 20,5 giây mỗi lần gọi** (3.000 câu + 4 lần gọi lại). Chi phí = (7,99 − 4,63) × 1,40 + 4,63 × 0,26 + 0,50 × 4,40 ≈ **8,13 USD** cho 15 hệ × 200 câu, khoảng 0,0027 USD mỗi câu chấm. Đắt hơn nhiều so với chi phí trả lời toàn bộ 15 hệ (khoảng 0,98 USD) vì judge đọc cả các đoạn văn và GLM đắt hơn DeepSeek khoảng 9 lần giá vào. Không gồm các lượt thử judge trước đợt đo (tuning prompt, 50 câu kiểm tay, 6 đáp án bịa).

### Thời gian (cộng trên 200 câu, tuần tự từng câu; KHÔNG phải độ trễ chính thức)

Cách tính: **pipeline:** truy xuất = tổng `timings_ms.total` trong `predictions.jsonl` của lượt truy xuất (embed + search + fuse + rerank + neighbors); LLM = trung bình `e2e_net_s` của các lần gọi thật quan sát được (không tính thời gian chờ thử lại 429) × 200 (một lần gọi mỗi câu). **Agent:** truy xuất/công cụ = tổng `tool_time_s` (thời gian chạy công cụ: `vector_search`, `temporal_search`, `grep`, `read_page`...), LLM = tổng `llm_time_s` (mọi lượt LLM của câu), lấy từ `results.jsonl`. Tổng cả hai = hai cột trước cộng lại (giả định chạy tuần tự, đúng với agent và pipeline trả lời từng câu).

| Hệ | Tổng truy xuất / công cụ (s) | Tổng LLM (s) | Tổng cả hai (s) | Truy xuất/câu (s) | LLM/câu (s) | Tổng/câu (s) |
|---|---|---|---|---|---|---|
| P1 | 2.3 | 464.8 | 467.1 | 0.011 | 2.32 | 2.34 |
| P2 | 7.6 | 563.5 | 571.1 | 0.038 | 2.82 | 2.86 |
| P3 | 49.7 | 518.2 | 568.0 | 0.249 | 2.59 | 2.84 |
| P4 | 8.8 | 550.2 | 559.0 | 0.044 | 2.75 | 2.80 |
| P5 | 14.4 | 506.3 | 520.8 | 0.072 | 2.53 | 2.60 |
| P6 | 4.3 | 532.4 | 536.7 | 0.022 | 2.66 | 2.68 |
| P7 | 25.5 | 531.3 | 556.8 | 0.128 | 2.66 | 2.78 |
| P8 | 29.5 | 505.2 | 534.7 | 0.147 | 2.53 | 2.67 |
| P9 | 44.4 | 468.4 | 512.8 | 0.222 | 2.34 | 2.56 |
| P10 | 14.1 | 514.8 | 528.9 | 0.070 | 2.57 | 2.64 |
| A1 | 13.4 | 4681.2 | 4694.6 | 0.067 | 23.41 | 23.47 |
| A2 | 22.2 | 6007.4 | 6029.6 | 0.111 | 30.04 | 30.15 |
| A3 | 15.9 | 4290.6 | 4306.5 | 0.080 | 21.45 | 21.53 |
| A4 | 3488.4 | 2269.5 | 5757.9 | 17.442 | 11.35 | 28.79 |
| A5 | 1323.7 | 2431.7 | 3755.4 | 6.619 | 12.16 | 18.78 |

Vì sao các số này chỉ để tham khảo:
- Các lượt chạy chồng nhau, CPU bị tranh chấp, có 429, nên thời gian dao động theo lúc chạy: LLM mỗi câu của A2 là 30 giây nhưng A4 chỉ 11 giây dù cùng kiểu B, chênh nhau chủ yếu do lúc chạy A2 các tiến trình khác đang chạy.
- **A4 có thời gian công cụ 17,4 giây mỗi câu** vì lượt A4 dùng trong bảng là bản phát lại cache chạy lại `temporal_search` (nạp cross-encoder bge trên CPU) khi máy đang tải nặng; A5 chạy sau khi giảm tải là 6,6 giây mỗi câu. Hai con số không so được với nhau và cũng không phải thời gian `temporal_search` thật khi máy rảnh.
- Pipeline: truy xuất tính theo từng lượt `evaluate.py` riêng, chạy lúc tải khác nhau (P3 0,25 giây mỗi câu so với P4 0,04 giây dù cùng loại cross-encoder nhỏ), nên khác biệt giữa các cấu hình pipeline trong cột này là nhiễu.
- Phần ổn định hơn cả: LLM mỗi lần gọi pipeline khoảng 2,3 đến 2,8 giây (một lần gọi/câu), và agent tốn thời gian LLM gấp 4 đến 10 lần pipeline vì 2,5 đến 3,5 lượt/câu.
- **Judge GLM-5.3:** 3.004 lần gọi, trung bình 20,5 giây mỗi lần (cộng dồn khoảng 61.600 giây = 17,1 giờ gọi); chạy 10 luồng song song, đồng hồ thực của cả đợt (đo, trả lời và judge xen kẽ, có dừng chỉnh luồng) khoảng 1 giờ 49 phút (00:34 đến 02:23).

**Cảnh báo về độ tin cậy:**
- **A1 (và một phần A3): judge không đo được faithfulness, recall, precision.** Passage của agent lấy từ kết quả công cụ theo định dạng chunk của `vector_search`; `grep`/`read_page` không có định dạng đó nên judge của A1 nhận **0 đoạn** (`n_passages = 0`): `grounded` 0,00, `bịa` 0,405, recall 0,00 đều là hệ quả của việc đó, KHÔNG phải đặc tính của A1. Với A3, judge chỉ thấy phần vector (trung bình 6,3 đoạn) nên `grounded`, `bịa`, recall, precision (dấu *) bị hụt. Các điểm `judge nghiêm/rộng` của A1 cũng chỉ dựa vào đáp án và gold, chưa tin được. Cần sửa cách lấy passage cho `read_page`/`grep` rồi chấm lại A1, A3 (200 câu mỗi hệ, ~400 lần gọi GLM) trước khi dùng các cột này.
- **Token, USD:** xem bảng chi phí ở trên (pipeline ngoại suy từ các lần gọi quan sát được). Thời gian đo khi chạy song song, KHÔNG phải độ trễ chính thức; chưa tính chi phí judge.
- **Judge chưa đo mức đồng ý với người** (`docs/eval/13_JUDGE_M1_CHECK_50.md` dùng để chỉnh prompt). `judge nghiêm` hơi lạc quan khi đáp án là tập con của gold (`subset`), hoặc khi gold nhiều giá trị. Đã gặp một ca `verdict = wrong` nhưng `matches_gold = true` (Seibu Shinjuku, nhãn `time_mismatch`): hai trường không luôn nhất quán.

**Đọc 20 câu ngẫu nhiên (seed 7) để kiểm judge:** 16/20 hợp lý. Các ca đáng chú ý: (1) P4 "Fellow of the Royal Society" so với gold "Royal Society" → `format_variant`, đúng; (2) P2 Telekids, đáp án Irene Moors trong khi gold Anniko van Santen từ 1992 → judge chấm `alternate_valid` (đúng theo passage, `time_mismatch`), hợp lý, EM chấm sai; (3) P2 Cochran: từ chối vì passage ghi 1953 ngoài khoảng 1930–1936 → từ chối đúng lúc nhưng gold có trong passage, nhãn `time_mismatch`; (4) A2 "University of Tehran" so với gold dài → `subset` nhưng `matches_gold = true` (hơi rộng); (5) P9 Seibu: `wrong` nhưng `matches_gold = true` (không nhất quán); (6) P7 Diane Downs: `alternate_valid` với `label_issue = gold_not_an_answer`. Judge đáng tin ở mức xu hướng; không dùng chênh lệch dưới ~0,03 để kết luận.

**Đọc bảng:**
1. Pipeline: P1 < P2 (hybrid kém dense) < P3/P4/P5 (thêm cross-encoder) < P6–P8 < P9 ≈ P10. Judge nghiêm: 0,495 → 0,595 (cross-encoder) → 0,685 (Temporal) → 0,720 (X): thứ tự giống EM. Temporal tăng recall (0,72 → 0,85) và giảm từ chối (0,275 → 0,115).
2. Agent: A2 (vector) vẫn không kém A4/A5 (có `temporal_search`): judge nghiêm A2 = A4 = 0,750, A5 0,720. A4 có judge rộng cao nhất (0,870). Thêm grep (A3) không giúp (0,700).
3. Pipeline tốt nhất (P10 0,720 nghiêm) thấp hơn A2/A4 (0,750) về judge nghiêm nhưng cao hơn A1/A3; EM thì P10 0,640 ≈ A2 0,650. Chưa phân biệt được (sai số chuẩn khoảng 0,03).
4. Từ chối: pipeline từ chối nhiều hơn (0,08–0,34) nhưng phần lớn đúng lúc (0,76–0,94). Agent từ chối ít (0,065–0,07) nhưng chỉ 31–43% là đúng lúc: đa số từ chối của agent là do đọc quá chặt hoặc thiếu mốc thời gian dù có thấy gold (xem mục 14). Cùng `refusal_quality` chỉ ở mức xu hướng.
5. Bịa gần như bằng 0 ở mọi hệ có passage đầy đủ (≤ 0,02).

**Việc tiếp theo (cần người dùng quyết):** (a) sửa passage cho A1/A3 rồi chấm lại; (b) đo mức đồng ý judge–người trên mẫu 50 câu mới; (c) đo token/thời gian chính thức trên máy rảnh (CPU hay GPU chưa chốt); (d) `valid`, `test_clean` chỉ khi được bảo.

## 5. Giới hạn

- Nhãn TimeQA có nhiều gold, gold lệch thời kỳ: khoảng 16–22% câu bị judge ghi `label_issue ≠ none` ở mọi hệ; khoảng 22/100 câu sai ở mọi hệ (xem `planning/03` mục 11). Vì thế dùng judge rộng và EM song song, không dùng một điểm duy nhất.
- Judge chưa đo mức đồng ý với người trên mẫu độc lập; judge không ổn định với câu nhập nhằng; `refusal_quality` và `label_issue` chỉ ở mức xu hướng.
- Sai số chuẩn trên 200 câu khoảng 0,03; không kết luận từ chênh lệch nhỏ hơn.
- Thời gian, token chạy song song hoặc phát lại cache, không phải độ trễ chính thức.

## 6. Dấu vết: thư mục đã dùng để tổng hợp bảng

Mọi thư mục nằm dưới `output/` (không xóa). Mỗi thư mục có `run.log`, `config.resolved.yaml`, `llm_calls.jsonl` (token, cache, thời gian, lỗi của từng lần gọi) và: `answers.jsonl` + `metrics.json` (trả lời pipeline), `results.jsonl` + `agent_calls.jsonl` + `agent_trace.jsonl` + `tool_texts.jsonl` + `run_meta.json` (agent), `predictions.jsonl` (truy xuất), `judgments.jsonl` (judge). Trạng thái từng việc của đợt đo: `local/logs/rest2/status.json` (và `status_prev.json`, `local/logs/rest2_run1..3/` là các lượt dừng để chỉnh số luồng; log từng việc `local/logs/rest2/*.log`). Điều phối: `local/scripts/run_rest2.py`; tổng hợp: `local/scripts/final_table.py`, `cost_table.py`. Cache dùng lại được khi chạy lại cùng đầu vào.

| Hệ | Tập | Thư mục kết quả trả lời / agent | Thư mục truy xuất (evaluate.py) | Thư mục judge | Cache LLM trả lời/agent | Cache judge |
|---|---|---|---|---|---|---|
| P1 | tune100 | `20261125_193644_4` | `20261125_191637` | `20261126_004110_5` | cache của lượt đo ban đầu (`ds_pm_*`, `ds_t100*`) | `judge_glm_P1_a` |
| P1 | tune100c | `20261125_202129_3` | `20261125_202115` | `20261126_004110_3` | cache của lượt đo ban đầu (`ds_pm_*`, `ds_t100*`) | `judge_glm_P1_c` |
| P2 | tune100 | `20261125_235243` | `20261125_235228_3` | `20261126_010303` | `ds_rest_ans_a_P2_m1_v4` | `judge_glm_P2_a` |
| P2 | tune100c | `20261126_004117` | `20261126_003455_3` | `20261126_014006` | `ds_rest_ans_c_P2_m1_v4` | `judge_glm_P2_c` |
| P3 | tune100 | `20261125_235248` | `20261125_235228_4` | `20261126_010606` | `ds_rest_ans_a_P3_m1_v4` | `judge_glm_P3_a` |
| P3 | tune100c | `20261126_004110_6` | `20261125_235312` | `20261126_013706` | `ds_rest_ans_c_P3_m1_v4` | `judge_glm_P3_c` |
| P4 | tune100 | `20261125_235253` | `20261125_235234` | `20261126_011106` | `ds_rest_ans_a_P4_m1_v4` | `judge_glm_P4_a` |
| P4 | tune100c | `20261126_004120_2` | `20261126_004110` | `20261126_014607` | `ds_rest_ans_c_P4_m1_v4` | `judge_glm_P4_c` |
| P5 | tune100 | `20261126_004110_4` | `20261125_235258` | `20261126_013006` | `ds_rest_ans_a_P5_m1_v4` | `judge_glm_P5_a` |
| P5 | tune100c | `20261126_004125` | `20261126_004110_2` | `20261126_015010` | `ds_rest_ans_c_P5_m1_v4` | `judge_glm_P5_c` |
| P6 | tune100 | `20261125_222409_2` | `20261125_222331` | `20261126_004118` | cache của lượt đo ban đầu (`ds_pm_*`, `ds_t100*`) | `judge_glm_P6_a` |
| P6 | tune100c | `20261125_222410` | `20261125_222350` | `20261126_004120` | cache của lượt đo ban đầu (`ds_pm_*`, `ds_t100*`) | `judge_glm_P6_c` |
| P7 | tune100 | `20261126_003457_2` | `20261125_235237` | `20261126_011607` | `ds_rest_ans_a_P7_m1_v4` | `judge_glm_P7_a` |
| P7 | tune100c | `20261126_004136` | `20261126_004118_2` | `20261126_015604` | `ds_rest_ans_c_P7_m1_v4` | `judge_glm_P7_c` |
| P8 | tune100 | `20261126_003456_2` | `20261125_235241` | `20261126_012106` | `ds_rest_ans_a_P8_m1_v4` | `judge_glm_P8_a` |
| P8 | tune100c | `20261126_004251` | `20261126_004124` | `20261126_020604` | `ds_rest_ans_c_P8_m1_v4` | `judge_glm_P8_c` |
| P9 | tune100 | `20261126_003455_2` | `20261125_235253_2` | `20261126_012611` | `ds_rest_ans_a_P9_m1_v4` | `judge_glm_P9_a` |
| P9 | tune100c | `20261126_004219` | `20261126_004133` | `20261126_020006` | `ds_rest_ans_c_P9_m1_v4` | `judge_glm_P9_c` |
| P10 | tune100 | `20261125_222408_7` | `20261125_222318` | `20261126_004124_2` | cache của lượt đo ban đầu (`ds_pm_*`, `ds_t100*`) | `judge_glm_P10_a` |
| P10 | tune100c | `20261125_222408_8` | `20261125_222335` | `20261126_004128` | cache của lượt đo ban đầu (`ds_pm_*`, `ds_t100*`) | `judge_glm_P10_c` |
| A1 | tune100 | `20261125_215259_2` | – | `20261126_004221` | `ds_agent_a_A1_m1_v4` | `judge_glm_A1_a` |
| A1 | tune100c | `20261125_215259_3` | – | `20261126_004221_2` | `ds_agent_c_A1_m1_v4` | `judge_glm_A1_c` |
| A2 | tune100 | `20261125_193644_2` | – | `20261126_004506` | `ds_agent_tune50_A2_m1_v4` | `judge_glm_A2_a` |
| A2 | tune100c | `20261125_202128_3` | – | `20261126_004518` | `ds_agent_tune100c_A2_m1_v4` | `judge_glm_A2_c` |
| A3 | tune100 | `20261125_215259_4` | – | `20261126_004814` | `ds_agent_a_A3_m1_v4` | `judge_glm_A3_a` |
| A3 | tune100c | `20261125_215259` | – | `20261126_004910` | `ds_agent_c_A3_m1_v4` | `judge_glm_A3_c` |
| A4 | tune100 | `20261125_225541_5` | – | `20261126_005313` | `ds_pm_agent_a_A4r_m1_v4` | `judge_glm_A4_a` |
| A4 | tune100c | `20261125_231302` | – | `20261126_005606` | `ds_pm_agent_c_A4r_m1_v4` | `judge_glm_A4_c` |
| A5 | tune100 | `20261126_004109` | – | `20261126_021003` | `ds_rest_agent_a_A5_m1_v4` | `judge_glm_A5_a` |
| A5 | tune100c | `20261126_004109_2` | – | `20261126_021612` | `ds_rest_agent_c_A5_m1_v4` | `judge_glm_A5_c` |

Thư mục dở dang không dùng cho bảng (giữ nguyên): `20261125_2352*`, `2353*` (lần chạy chưa được phép), `20261126_0034*` (lượt chạy trước khi giảm luồng), các thư mục judge thử (`20261125_235800` đến `20261126_002254`, gồm lượt thử 6 đáp án bịa cố ý).

## 7. Đợt 395 câu `tune` còn lại và gộp 595 câu (2026-11-26)

Đo nốt phần `tune` chưa đo: `tune` có 595 câu (400 câu gốc + 195 câu thêm từ `real`, `scripts/extend_tune_with_real.py`), đã đo 200 (`tune100` + `tune100c`), còn **395 câu**. Không đụng `valid`, `test_clean`. Nguồn các bảng: `local/scripts/final595.py` (điểm), `local/scripts/cost_time395.py` (chi phí, thời gian), kết quả thô `local/results/final595.json`.

### 7.1 Cách làm và khác biệt so với 200 câu

- **Chia phần:** 395 câu chia 4 phần (99, 99, 99, 98 câu), xen kẽ theo domain: `dataset/eval/tunerest1..4_subset.json` (và `tunerest_subset.json` đủ 395 câu để đo thời gian). Để các khâu gối nhau: truy xuất, trả lời, judge chạy song song theo từng phần (`local/scripts/run_rest395.py`).
- **Cấu hình giữ như 200 câu:** `m1_v4`, top-5, `time_mode = range`, `decay_from = end`, DeepSeek flash (thinking tắt), judge GLM-5.3 (`judge_m1`, thinking tắt), 15 hệ P1 đến P10 và A1 đến A5, mỗi hệ một lần.
- **Khác 1: cross-encoder chạy trên GPU Kaggle.** Cross-encoder (bge-reranker-v2-m3-int8, MiniLM L6, L12) của P3 đến P5, P7 đến P10 và `temporal_search` của A4, A5 gọi server `/rerank` qua đường hầm Cloudflare (`TAM_RERANK_REMOTE_URL`, `TAM_RERANK_REMOTE_ALL=1`). Điểm fp16 trên GPU khác nhẹ điểm int8 trên CPU của 200 câu cũ (khóa cache điểm riêng `remote:`). Khi gộp 595 câu, xếp hạng trong cùng một hệ có thể lệch nhẹ vì lý do này. Mọi lượt truy xuất đều bật `--no-score-cache`.
- **Khác 2: judge GLM-5.3 chấm đủ 395 câu** (phần 3, 4 chấm làm hai đợt, cùng judge, cùng prompt); điểm judge tính trên 395 và 595 câu.
- **Khác 3: A1, A3, A5 đã chấm lại.** `agent_passages` trong `scripts/judge_answers.py` đã sửa để đọc cả kết quả `read_page` và `grep` (agent kind A, C); chấm lại A1, A3, A5 trên 200 câu cũ và phần 1, 2; phần 3, 4 chấm bằng bản đã sửa. Mục 3 ở trên (mô tả lỗi) vẫn đúng cho lần chấm cũ; **số liệu của A1, A3 trong mục 4 là số cũ, dùng số ở mục 7**. Trên 200 câu cũ: A1 recall 0,000 lên 0,950, grounded 0,000 lên 0,880, lenient 0,620 lên 0,770; A3 recall 0,810 lên 0,970, lenient 0,745 lên 0,795; hallucinated về 0,000 ở cả hai.
- **Luồng:** DeepSeek 6 luồng, GLM 6 luồng (hạ từ 10 do 429). DeepSeek tự tạm dừng ở khung giá ×2 (mục 7.6).
- **ONNX mở thừa luồng:** `fastembed` tạo embedding cho câu hỏi bằng ONNX trên CPU, tự ghim luồng lên mọi nhân và bỏ qua `taskset`, làm CPU lên 75–85%. Đã thêm biến `TAM_EMBED_THREADS` (`src/tam/embedding/providers/fastembed.py`), đặt 1 luồng mỗi tiến trình thì CPU còn khoảng 10%. Không đổi model, kết quả không đổi.

### 7.2 Kết quả

Cách đọc cột: `n` là số câu có đáp án (điểm luật); `n judge` là số câu đã chấm (điểm judge). `EM trên câu đã chấm` để so cùng tập với điểm judge. Giải nghĩa các nhãn ở mục 2.

### 395 câu còn lại (EM, F1, contains, từ chối trên 395 câu; điểm judge trên các câu đã chấm)

| Hệ | n | EM | F1 | contains | từ chối | n judge | EM trên câu đã chấm | strict | lenient | partial | grounded | hallucinated | từ chối đúng lúc (n) | recall | precision | bước |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 395 | 0.415 | 0.501 | 0.458 | 0.248 | 395 | 0.415 | 0.516 | 0.595 | 0.015 | 0.737 | **0.010** | 0.74 (98) | 0.759 | 0.262 | – |
| P2 | 395 | 0.405 | 0.491 | 0.453 | **0.271** | 395 | 0.405 | 0.522 | 0.582 | 0.013 | 0.722 | 0.005 | **0.80 (107)** | 0.734 | 0.260 | – |
| P3 | 395 | 0.461 | 0.564 | 0.544 | 0.195 | 395 | 0.461 | 0.600 | 0.673 | 0.010 | 0.797 | 0.003 | 0.73 (77) | 0.815 | 0.279 | – |
| P4 | 395 | 0.453 | 0.551 | 0.527 | 0.208 | 395 | 0.453 | 0.590 | 0.651 | 0.008 | 0.787 | 0.005 | 0.65 (82) | 0.828 | 0.281 | – |
| P5 | 395 | 0.458 | 0.561 | 0.537 | 0.172 | 395 | 0.458 | 0.608 | 0.701 | 0.008 | 0.825 | 0.003 | 0.75 (68) | 0.848 | 0.299 | – |
| P6 | 395 | 0.509 | 0.610 | 0.582 | 0.147 | 395 | 0.509 | 0.651 | 0.744 | 0.013 | 0.851 | 0.003 | 0.67 (58) | 0.871 | 0.313 | – |
| P7 | 395 | 0.494 | 0.612 | 0.572 | 0.134 | 395 | 0.494 | 0.638 | 0.722 | **0.025** | 0.861 | 0.003 | 0.70 (53) | 0.876 | 0.312 | – |
| P8 | 395 | 0.496 | 0.612 | 0.567 | 0.147 | 395 | 0.496 | 0.648 | 0.737 | 0.005 | 0.848 | 0.003 | 0.67 (58) | 0.856 | 0.305 | – |
| P9 | 395 | 0.532 | 0.626 | 0.597 | 0.132 | 395 | 0.532 | 0.666 | 0.754 | 0.013 | 0.866 | 0.003 | 0.65 (52) | 0.911 | **0.334** | – |
| P10 | 395 | 0.504 | 0.609 | 0.577 | 0.134 | 395 | 0.504 | 0.656 | 0.744 | 0.005 | 0.863 | 0.003 | 0.68 (53) | 0.901 | 0.328 | – |
| A1 | 395 | 0.496 | 0.611 | 0.595 | 0.152 | 395 | 0.496 | 0.643 | 0.754 | 0.013 | 0.838 | 0.008 | 0.48 (61) | 0.939 | 0.127 | 3.58 |
| A2 | 395 | **0.534** | **0.661** | **0.641** | 0.114 | 395 | **0.534** | **0.704** | **0.803** | 0.008 | 0.886 | 0.000 | 0.47 (45) | 0.949 | 0.197 | 2.66 |
| A3 | 395 | 0.532 | 0.635 | 0.623 | 0.144 | 395 | 0.532 | 0.678 | 0.767 | 0.005 | 0.851 | 0.003 | 0.43 (58) | **0.957** | 0.157 | 3.14 |
| A4 | 395 | 0.527 | 0.649 | 0.625 | 0.101 | 395 | 0.527 | 0.691 | **0.803** | 0.008 | **0.896** | 0.003 | 0.55 (40) | 0.949 | 0.227 | 2.52 |
| A5 | 395 | 0.527 | 0.649 | 0.633 | 0.106 | 395 | 0.527 | 0.689 | 0.782 | 0.010 | 0.886 | 0.005 | 0.55 (42) | 0.942 | 0.154 | 2.90 |

### Gộp 595 câu (200 cũ + 395 mới)

| Hệ | n | EM | F1 | contains | từ chối | n judge | EM trên câu đã chấm | strict | lenient | partial | grounded | hallucinated | từ chối đúng lúc (n) | recall | precision | bước |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 595 | 0.420 | 0.501 | 0.455 | 0.257 | 595 | 0.420 | 0.509 | 0.597 | 0.012 | 0.731 | **0.008** | 0.78 (153) | 0.746 | 0.260 | – |
| P2 | 595 | 0.390 | 0.472 | 0.427 | **0.294** | 595 | 0.390 | 0.496 | 0.563 | 0.010 | 0.697 | 0.005 | **0.82 (175)** | 0.711 | 0.254 | – |
| P3 | 595 | 0.477 | 0.565 | 0.541 | 0.198 | 595 | 0.477 | 0.592 | 0.672 | 0.008 | 0.793 | 0.003 | 0.75 (118) | 0.817 | 0.280 | – |
| P4 | 595 | 0.466 | 0.553 | 0.526 | 0.208 | 595 | 0.466 | 0.588 | 0.657 | 0.007 | 0.788 | 0.003 | 0.71 (124) | 0.817 | 0.281 | – |
| P5 | 595 | 0.476 | 0.568 | 0.545 | 0.171 | 595 | 0.476 | 0.603 | 0.704 | 0.005 | 0.824 | 0.003 | 0.75 (102) | 0.845 | 0.298 | – |
| P6 | 595 | 0.541 | 0.631 | 0.602 | 0.136 | 595 | 0.541 | 0.662 | 0.748 | 0.012 | 0.859 | 0.002 | 0.73 (81) | 0.862 | 0.310 | – |
| P7 | 595 | 0.531 | 0.632 | 0.593 | 0.119 | 595 | 0.531 | 0.650 | 0.736 | **0.024** | 0.877 | 0.002 | 0.72 (71) | 0.877 | 0.313 | – |
| P8 | 595 | 0.529 | 0.627 | 0.585 | 0.134 | 595 | 0.529 | 0.655 | 0.746 | 0.005 | 0.859 | 0.005 | 0.70 (80) | 0.849 | 0.303 | – |
| P9 | 595 | 0.565 | 0.650 | 0.622 | 0.114 | 595 | 0.565 | 0.682 | 0.768 | 0.013 | 0.884 | 0.002 | 0.71 (68) | 0.906 | **0.338** | – |
| P10 | 595 | 0.550 | 0.639 | 0.610 | 0.118 | 595 | 0.550 | 0.677 | 0.758 | 0.007 | 0.879 | 0.003 | 0.74 (70) | 0.901 | 0.331 | – |
| A1 | 595 | 0.529 | 0.631 | 0.615 | 0.139 | 595 | 0.529 | 0.659 | 0.760 | 0.018 | 0.852 | 0.005 | 0.46 (84) | 0.943 | 0.132 | 3.57 |
| A2 | 595 | **0.573** | **0.680** | **0.659** | 0.097 | 595 | **0.573** | **0.719** | 0.813 | 0.008 | 0.903 | 0.000 | 0.43 (58) | 0.958 | 0.197 | 2.65 |
| A3 | 595 | 0.558 | 0.650 | 0.639 | 0.131 | 595 | 0.558 | 0.691 | 0.776 | 0.010 | 0.864 | 0.002 | 0.44 (79) | **0.961** | 0.158 | 3.13 |
| A4 | 595 | 0.560 | 0.665 | 0.644 | 0.089 | 595 | 0.560 | 0.711 | **0.825** | 0.007 | **0.908** | 0.002 | 0.51 (53) | **0.961** | 0.226 | 2.51 |
| A5 | 595 | 0.558 | 0.665 | 0.650 | 0.094 | 595 | 0.558 | 0.704 | 0.800 | 0.008 | 0.901 | 0.003 | 0.48 (56) | 0.953 | 0.157 | 2.87 |

### So cặp (strict, 595 câu)

| Cặp | n | chênh | z | a hơn | b hơn |
|---|---|---|---|---|---|
| P2 − P1 | 595 | -0.013 | -0.79 | 47 | 55 |
| P3 − P1 | 595 | +0.082 | +4.34 | 90 | 41 |
| P5 − P3 | 595 | +0.012 | +0.80 | 42 | 35 |
| P6 − P1 | 595 | +0.153 | +8.63 | 108 | 17 |
| P6 − P5 | 595 | +0.059 | +3.67 | 64 | 29 |
| P10 − P6 | 595 | +0.015 | +1.31 | 28 | 19 |
| P9 − P10 | 595 | +0.005 | +0.52 | 18 | 15 |
| P10 − P5 | 595 | +0.074 | +5.09 | 61 | 17 |
| A2 − P10 | 595 | +0.042 | +2.55 | 61 | 36 |
| A4 − A2 | 595 | -0.008 | -0.80 | 17 | 22 |
| A5 − A4 | 595 | -0.007 | -0.62 | 19 | 23 |
| A3 − A2 | 595 | -0.029 | -2.34 | 18 | 35 |
| A1 − A2 | 595 | -0.061 | -4.65 | 13 | 49 |
| A4 − P10 | 595 | +0.034 | +1.97 | 62 | 42 |

### 7.3 Đọc kết quả

1. **Pipeline lặp lại 200 câu.** P1 và P2 gần nhau (P2 không hơn P1); cross-encoder giúp (P3 − P1 = +0,082, z 4,3); Temporal giúp nhiều nhất (P6 − P1 = +0,153, z 8,6; P6 − P5 = +0,059, z 3,7). **Cấu hình X (P10) hơn P6 chỉ +0,015 (z 1,3)** và P9 ≈ P10: lợi thế của cross-encoder trộn trên Temporal đơn thuần là nhỏ, chưa đủ để kết luận.
2. **Agent: A2 (vector) tốt nhất.** A2 hơn P10 (+0,042, z 2,6, strict); trên 200 câu cũ chưa phân biệt được. A4 và A5 (thêm `temporal_search`) không hơn A2 (A4 − A2 = −0,008; A5 − A4 = −0,007). Thêm `grep`/`read_page` làm kém đi: A3 − A2 = −0,029 (z −2,3), A1 − A2 = −0,061 (z −4,7).
3. **Agent đọc đủ bằng chứng nhưng đọc nhiều:** recall 0,93–0,96 nhưng precision chỉ 0,13–0,23 (pipeline 0,25–0,34), vì agent đọc tới 20 đoạn.
4. **Từ chối:** pipeline từ chối nhiều hơn nhưng phần lớn đúng lúc (0,70–0,82); agent từ chối ít hơn (0,09–0,14) nhưng chỉ 0,43–0,51 là đúng lúc.
5. **Bịa gần như bằng 0** (≤ 0,008) ở mọi hệ.
6. **Sai số:** trên 595 câu, sai số chuẩn của điểm khoảng 0,7 là 0,019 (200 câu: 0,032). Chênh lệch dưới 0,03 vẫn không nên diễn giải.

### 7.4 Chi phí

### Chi phí DeepSeek (395 câu)

| Hệ | lượt gọi/câu | token vào/câu | cache/câu | token ra/câu | USD/câu | USD/395 câu |
|---|---|---|---|---|---|---|
| P1 | 1.00 | 1673 | 747 | 27 | 0.00016 | 0.062 |
| P2 | 1.00 | 1712 | 757 | 27 | 0.00016 | 0.064 |
| P3 | 1.00 | 1766 | 764 | 28 | 0.00017 | 0.067 |
| P4 | 1.00 | 1763 | 750 | 28 | 0.00017 | 0.067 |
| P5 | 1.00 | 1761 | 767 | 28 | 0.00017 | 0.066 |
| P6 | 1.00 | 1729 | 767 | 28 | 0.00016 | 0.065 |
| P7 | 1.00 | 1760 | 769 | 28 | 0.00017 | 0.066 |
| P8 | 1.00 | 1722 | 794 | 28 | 0.00016 | 0.063 |
| P9 | 1.00 | 1762 | 783 | 28 | 0.00017 | 0.066 |
| P10 | 1.00 | 1772 | 777 | 28 | 0.00017 | 0.067 |
| A1 | 3.58 | 7760 | 4821 | 248 | 0.00060 | 0.239 |
| A2 | 2.66 | 6775 | 3373 | 227 | 0.00066 | 0.259 |
| A3 | 3.14 | 8726 | 5697 | 233 | 0.00061 | 0.241 |
| A4 | 2.52 | 6481 | 3628 | 236 | 0.00058 | 0.229 |
| A5 | 2.90 | 9069 | 5913 | 258 | 0.00065 | 0.255 |

Tổng DeepSeek 15 hệ × 395 câu: 1.88 USD

Judge GLM-5.3 (395 câu đủ + chấm lại A1, A3, A5 trên 400 câu): 6719 lần gọi quan sát, vào 18.80M, cache 10.14M, ra 1.13M, 19.72 USD giá niêm yết, 4.7 s/lần. Tổng GLM đã dùng tính cả việc chấm lại A1, A3 (400 câu mỗi hệ) và các lượt chấm lại do dừng giữa chừng; `e2e_net_s` là thời gian không tính chờ sau 429 (lần đo 200 câu trước ghi 20,5 giây mỗi lần là thời gian đồng hồ gồm chờ).

Giá DeepSeek tính ở hệ số ×1: đợt chạy đã tạm dừng đúng khung ×2 nên mọi lần gọi nằm ngoài khung giá nhân đôi.

### 7.5 Thời gian: tách CPU và GPU (395 câu)

Hai phần: (a) **đo riêng truy xuất pipeline**: mỗi pipeline chạy lại trên đủ 395 câu, một lượt trên CPU (4 luồng) và, với pipeline có cross-encoder, một lượt trên GPU; không cache điểm; chạy lúc máy chỉ còn judge (không phải máy rảnh hoàn toàn); (b) **tổng thời gian cả truy xuất lẫn LLM**. Số LLM lấy từ lúc chạy song song, đã tạm dừng/chờ nhiều lần nên chỉ để tham khảo.

**Truy xuất pipeline, đo riêng 395 câu, không cache điểm** (tổng s; ms/câu; trong đó rerank ms/câu)

| Hệ | CPU tổng | CPU ms/câu | CPU rerank ms/câu | GPU tổng | GPU ms/câu | GPU rerank ms/câu |
|---|---|---|---|---|---|---|
| P1 | 5.0 | 13 | 0 | – | – | – |
| P2 | 5.1 | 13 | 0 | – | – | – |
| P3 | 283.4 | 718 | 684 | 295.9 | 749 | 733 |
| P4 | 441.4 | 1117 | 1088 | 260.2 | 659 | 643 |
| P5 | 1414.6 | 3581 | 3551 | 410.4 | 1039 | 1022 |
| P6 | 9.6 | 24 | 0 | – | – | – |
| P7 | 178.1 | 451 | 382 | 400.4 | 1014 | 980 |
| P8 | 200.2 | 507 | 430 | 318.5 | 806 | 769 |
| P9 | 2111.6 | 5346 | 5269 | 545.7 | 1381 | 1345 |
| P10 | 1449.5 | 3670 | 3602 | 386.5 | 978 | 949 |

**LLM và tổng** (pipeline: LLM = trung bình e2e_net_s của các lần gọi quan sát × 395; agent: cộng từ results.jsonl)

| Hệ | thiết bị truy xuất/công cụ | truy xuất hoặc công cụ (s) | LLM (s) | tổng (s) | /câu: truy xuất | LLM | tổng |
|---|---|---|---|---|---|---|---|
| P1 | CPU | 5.0 | 750.0 | 755.0 | 0.013 | 1.90 | 1.91 |
| P2 | CPU | 5.1 | 677.0 | 682.1 | 0.013 | 1.71 | 1.73 |
| P3 | CPU | 283.4 | 733.9 | 1017.3 | 0.718 | 1.86 | 2.58 |
| P3 | GPU | 295.9 | 733.9 | 1029.8 | 0.749 | 1.86 | 2.61 |
| P4 | CPU | 441.4 | 991.1 | 1432.5 | 1.117 | 2.51 | 3.63 |
| P4 | GPU | 260.2 | 991.1 | 1251.3 | 0.659 | 2.51 | 3.17 |
| P5 | CPU | 1414.6 | 762.3 | 2176.9 | 3.581 | 1.93 | 5.51 |
| P5 | GPU | 410.4 | 762.3 | 1172.8 | 1.039 | 1.93 | 2.97 |
| P6 | CPU | 9.6 | 847.9 | 857.5 | 0.024 | 2.15 | 2.17 |
| P7 | CPU | 178.1 | 748.2 | 926.3 | 0.451 | 1.89 | 2.34 |
| P7 | GPU | 400.4 | 748.2 | 1148.6 | 1.014 | 1.89 | 2.91 |
| P8 | CPU | 200.2 | 746.0 | 946.1 | 0.507 | 1.89 | 2.40 |
| P8 | GPU | 318.5 | 746.0 | 1064.5 | 0.806 | 1.89 | 2.69 |
| P9 | CPU | 2111.6 | 745.7 | 2857.3 | 5.346 | 1.89 | 7.23 |
| P9 | GPU | 545.7 | 745.7 | 1291.4 | 1.381 | 1.89 | 3.27 |
| P10 | CPU | 1449.5 | 807.2 | 2256.7 | 3.670 | 2.04 | 5.71 |
| P10 | GPU | 386.5 | 807.2 | 1193.7 | 0.978 | 2.04 | 3.02 |
| A1 | CPU | 27.3 | 11175.3 | 11202.5 | 0.069 | 28.29 | 28.36 |
| A2 | CPU | 17.7 | 8611.9 | 8629.7 | 0.045 | 21.80 | 21.85 |
| A3 | CPU | 22.1 | 8837.2 | 8859.3 | 0.056 | 22.37 | 22.43 |
| A4 | GPU (bge qua Kaggle) | 354.7 | 7304.3 | 7659.0 | 0.898 | 18.49 | 19.39 |
| A5 | GPU (bge qua Kaggle) | 311.6 | 7462.5 | 7774.1 | 0.789 | 18.89 | 19.68 |

A4, A5 trên CPU (200 câu cũ, chạy lúc máy tải nặng, không sạch): tool/câu A4 17.4 s, A5 6.6 s

**Đọc:**
- **GPU nhanh hơn rõ với bge:** P5 từ 3,58 giây mỗi câu xuống 1,04 (3,4 lần), P9 từ 5,35 xuống 1,38 (3,9 lần), P10 từ 3,67 xuống 0,98 (3,8 lần). Với MiniLM (P3, P7, P8) CPU **nhanh hơn hoặc bằng** GPU (P3: 0,72 so với 0,75; P7: 0,45 so với 1,01; P8: 0,51 so với 0,81) vì model nhỏ và chi phí gọi qua đường hầm (vài trăm mili giây mỗi lần gọi, chưa đo riêng) lớn hơn thời gian tính.
- **GPU ở đây gồm độ trễ mạng** (đường hầm Cloudflare, Kaggle), không phải độ trễ GPU cục bộ.
- **Truy xuất vẫn nhỏ so với LLM** ở pipeline: từ 0,01 đến 5,3 giây mỗi câu (CPU) so với 1,7 đến 2,5 giây LLM; chỉ bge trên CPU (P5, P9, P10) làm truy xuất lớn hơn LLM. Agent: LLM chiếm hơn 95% thời gian (18–28 giây mỗi câu), công cụ chỉ 0,05–0,9 giây.
- **A4, A5 trên CPU:** chỉ có số 200 câu cũ (A4 17,4 giây, A5 6,6 giây mỗi câu cho công cụ), đo lúc máy tải nặng nên không sạch; số GPU của 395 câu là 0,9 và 0,8 giây. Chưa có số CPU sạch cho A4, A5.
- **Độ trễ chính thức vẫn chưa đo** (máy rảnh, một luồng, p50 và p90).

### 7.6 Quy tắc giá và hạn mức của OpenCode Go (đo ngày 2026-11-26)

- **Nguồn:** `https://opencode.ai/inference/go/v1/models` (giá, hệ số theo giờ) và `GET /inference/go/v1/usage` (phần trăm hạn mức; cần key có gói Go, gửi `User-Agent: tam-thesis-agent-eval/0.1`); mỗi response chat có `usage.opencode.{list_cost, allowance, tokens}`.
- **DeepSeek V4.1 Flash:** giá niêm yết 0,15 / 0,003 / 0,60 USD mỗi triệu token (vào / cache / ra). **Nhân ×2 từ thứ Hai đến thứ Sáu, khung UTC 01:00–04:00 và 06:00–10:00** (giờ Việt Nam 08:00–11:00 và 13:00–17:00). Đo xác nhận: lúc 13:07 giờ VN, `list_cost` gấp 2,00 lần giá gốc.
- **GLM-5.3:** 1,40 / 0,26 / 4,40 USD, **không có hệ số theo giờ**, đo hai lần trong khung cao điểm của Z.ai (13:08 và 14:05 giờ VN), hệ số 1,00.
- **Hạn mức gói:** `allowance` bị trừ bằng 0,6 lần `list_cost` với DeepSeek Flash và 0,3 lần với GLM-5.3 (khớp công thức 60 ÷ hạn mức tháng của model, 100 và 200). Hạn mức: 5 giờ bằng 20% hạn mức tháng, tuần 50%. Sau đợt này: 5 giờ 15%, tuần 51%, tháng 62% (trước đợt 53%). Chưa có lần nào chạm giới hạn; 429 đo được là giới hạn tốc độ theo phút (khoảng 6 lần mỗi phút mỗi bên khi 6 luồng), không phải hết hạn mức.
- **Không có khuyến mãi giảm giá** nào áp dụng cho hai model này (doc chỉ ghi giảm 50% cho Gemini 4 Argon đến 30/11).
- **Hạn mức thực tế cần theo dõi** nếu chạy `valid` và `test_clean` trong cùng tuần (tuần đã dùng 51%).

### 7.7 Dấu vết

Mọi thư mục dưới `output/` (không xóa). Trạng thái: `local/logs/rest395/status.json` (và `status_timing.json`, `local/logs/rejudge_A/status.json`, `status_A5.json`, `local/logs/judge_rest98/status.json`), log từng việc ở cùng thư mục; điều phối: `local/scripts/run_rest395.py` (chạy chính, `TIMING_ONLY=1` cho pha đo thời gian), `local/scripts/rejudge_A.py` (chấm lại A1, A3). Cache LLM: `data/llm_cache/ds_r395_*` (DeepSeek), `judge_glm_r395_*` và `judge_glm_fixA_*` (judge). Bản cũ của doc này trước khi gộp: `local/results/doc14_before_395.md`; bản cũ của `scripts/judge_answers.py`: `local/scripts/judge_answers.before_fix.py`.

| Hệ | Phần | Thư mục trả lời / agent | Thư mục truy xuất | Thư mục judge | Judge chấm lại (A1, A3, A5) |
|---|---|---|---|---|---|
| P1 | tunerest1 | `output/20261126_110903_2` | `output/20261126_110621` | `output/20261126_112235_5` | `–` |
| P1 | tunerest2 | `output/20261126_114710` | `output/20261126_111240` | `output/20261126_122510` | `–` |
| P1 | tunerest3 | `output/20261126_122906` | `output/20261126_112416` | `output/20261126_133314` | `–` |
| P1 | tunerest4 | `output/20261126_171807` | `output/20261126_113119` | `output/20261126_172704` | `–` |
| P2 | tunerest1 | `output/20261126_110903` | `output/20261126_110621_2` | `output/20261126_112235_3` | `–` |
| P2 | tunerest2 | `output/20261126_114803` | `output/20261126_111244` | `output/20261126_122216` | `–` |
| P2 | tunerest3 | `output/20261126_123310` | `output/20261126_112420` | `output/20261126_134220` | `–` |
| P2 | tunerest4 | `output/20261126_172119` | `output/20261126_113122` | `output/20261126_173104` | `–` |
| P3 | tunerest1 | `output/20261126_112236` | `output/20261126_110629_2` | `output/20261126_112923` | `–` |
| P3 | tunerest2 | `output/20261126_115521` | `output/20261126_111247` | `output/20261126_123509` | `–` |
| P3 | tunerest3 | `output/20261126_123717` | `output/20261126_112423` | `output/20261126_134313` | `–` |
| P3 | tunerest4 | `output/20261126_172704_2` | `output/20261126_113126` | `output/20261126_173508_2` | `–` |
| P4 | tunerest1 | `output/20261126_111411` | `output/20261126_110629` | `output/20261126_112923_4` | `–` |
| P4 | tunerest2 | `output/20261126_115613` | `output/20261126_111336` | `output/20261126_123307` | `–` |
| P4 | tunerest3 | `output/20261126_124017` | `output/20261126_112436` | `output/20261126_135211` | `–` |
| P4 | tunerest4 | `output/20261126_173104_2` | `output/20261126_113135` | `output/20261126_174006_2` | `–` |
| P5 | tunerest1 | `output/20261126_112923_3` | `output/20261126_110904` | `output/20261126_113412` | `–` |
| P5 | tunerest2 | `output/20261126_120410` | `output/20261126_111406` | `output/20261126_125748_2` | `–` |
| P5 | tunerest3 | `output/20261126_124514` | `output/20261126_112603` | `output/20261126_135414` | `–` |
| P5 | tunerest4 | `output/20261126_173508` | `output/20261126_113302` | `output/20261126_174227` | `–` |
| P6 | tunerest1 | `output/20261126_112923_2` | `output/20261126_110744` | `output/20261126_114406` | `–` |
| P6 | tunerest2 | `output/20261126_120416` | `output/20261126_111451` | `output/20261126_124508` | `–` |
| P6 | tunerest3 | `output/20261126_170001` | `output/20261126_112613` | `output/20261126_170039` | `–` |
| P6 | tunerest4 | `output/20261126_174006` | `output/20261126_113316` | `output/20261126_174544` | `–` |
| P7 | tunerest1 | `output/20261126_113018` | `output/20261126_110904_2` | `output/20261126_115417` | `–` |
| P7 | tunerest2 | `output/20261126_121227` | `output/20261126_111604` | `output/20261126_125748` | `–` |
| P7 | tunerest3 | `output/20261126_170001_2` | `output/20261126_112618` | `output/20261126_171102_2` | `–` |
| P7 | tunerest4 | `output/20261126_174227_2` | `output/20261126_113321` | `output/20261126_174725` | `–` |
| P8 | tunerest1 | `output/20261126_113021` | `output/20261126_111037` | `output/20261126_115309` | `–` |
| P8 | tunerest2 | `output/20261126_121310` | `output/20261126_111925` | `output/20261126_130307` | `–` |
| P8 | tunerest3 | `output/20261126_171101_3` | `output/20261126_112738` | `output/20261126_171309` | `–` |
| P8 | tunerest4 | `output/20261126_174544_2` | `output/20261126_113451` | `output/20261126_174941` | `–` |
| P9 | tunerest1 | `output/20261126_113909` | `output/20261126_111051` | `output/20261126_120508` | `–` |
| P9 | tunerest2 | `output/20261126_122022` | `output/20261126_112237` | `output/20261126_130613` | `–` |
| P9 | tunerest3 | `output/20261126_171102_3` | `output/20261126_112924` | `output/20261126_171813` | `–` |
| P9 | tunerest4 | `output/20261126_174710` | `output/20261126_113454` | `output/20261126_175136` | `–` |
| P10 | tunerest1 | `output/20261126_113910` | `output/20261126_111200` | `output/20261126_120309` | `–` |
| P10 | tunerest2 | `output/20261126_122129` | `output/20261126_112236_2` | `output/20261126_131207` | `–` |
| P10 | tunerest3 | `output/20261126_171308` | `output/20261126_112923_5` | `output/20261126_172120_2` | `–` |
| P10 | tunerest4 | `output/20261126_174941_2` | `output/20261126_113612` | `output/20261126_175358` | `–` |
| A1 | tunerest1 | `output/20261126_112922_2` | `–` | `output/20261126_114417` | `output/20261126_142228` |
| A1 | tunerest2 | `output/20261126_115212` | `–` | `output/20261126_131606` | `output/20261126_143516` |
| A1 | tunerest3 | `output/20261126_171101` | `–` | `output/20261126_172219` | `–` |
| A1 | tunerest4 | `output/20261126_174555` | `–` | `output/20261126_175624_2` | `–` |
| A2 | tunerest1 | `output/20261126_112235` | `–` | `output/20261126_113404` | `–` |
| A2 | tunerest2 | `output/20261126_121203` | `–` | `output/20261126_132309` | `–` |
| A2 | tunerest3 | `output/20261126_171101_2` | `–` | `output/20261126_173016` | `–` |
| A2 | tunerest4 | `output/20261126_175230` | `–` | `output/20261126_175922` | `–` |
| A3 | tunerest1 | `output/20261126_112922` | `–` | `output/20261126_121309` | `output/20261126_142815` |
| A3 | tunerest2 | `output/20261126_121723` | `–` | `output/20261126_132310` | `output/20261126_144033` |
| A3 | tunerest3 | `output/20261126_172120` | `–` | `output/20261126_174212_2` | `–` |
| A3 | tunerest4 | `output/20261126_175624` | `–` | `output/20261126_180406` | `–` |
| A4 | tunerest1 | `output/20261126_113217` | `–` | `output/20261126_121504` | `–` |
| A4 | tunerest2 | `output/20261126_123126` | `–` | `output/20261126_133311` | `–` |
| A4 | tunerest3 | `output/20261126_173016_2` | `–` | `output/20261126_174555_2` | `–` |
| A4 | tunerest4 | `output/20261126_175923` | `–` | `output/20261126_180717` | `–` |
| A5 | tunerest1 | `output/20261126_114923` | `–` | `output/20261126_124212` | `output/20261128_015007` |
| A5 | tunerest2 | `output/20261126_170118_2` | `–` | `output/20261126_171102` | `output/20261128_015120` |
| A5 | tunerest3 | `output/20261126_174212` | `–` | `output/20261126_175230_2` | `–` |
| A5 | tunerest4 | `output/20261126_180406_2` | `–` | `output/20261126_181212` | `–` |

Chấm lại A1, A3 trên 200 câu cũ: A1_tune100: `output/20261126_135632`, A1_tune100c: `output/20261126_140735`, A3_tune100: `output/20261126_141230`, A3_tune100c: `output/20261126_141742`

Đo thời gian riêng (395 câu, `--no-score-cache`): cpu_P1: `output/20261126_125747`, cpu_P2: `output/20261126_125755`, cpu_P3: `output/20261126_125803`, gpu_P3: `output/20261126_130252`, cpu_P4: `output/20261126_130751`, gpu_P4: `output/20261126_131517`, cpu_P5: `output/20261126_131940`, gpu_P5: `output/20261126_134324`, cpu_P6: `output/20261126_135018`, cpu_P7: `output/20261126_135030`, gpu_P7: `output/20261126_135335`, cpu_P8: `output/20261126_140018`, gpu_P8: `output/20261126_140344`, cpu_P9: `output/20261126_140906`, gpu_P9: `output/20261126_144426`, cpu_P10: `output/20261126_145335`, gpu_P10: `output/20261126_151749`

### 7.8 Việc còn lại

- Đo mức đồng ý judge và người trên mẫu 50 câu mới; đo độ trễ chính thức trên máy rảnh.
- `valid` (399 câu), `test_clean` (400 câu) chỉ khi được bảo. Đã chốt cho `valid` (2026-11-28): chạy đủ 15 hệ; trả lời và agent bằng DeepSeek flash qua OpenCode (`opencode_deepseek_flash`); judge GLM-5.3 qua Surplus (`surplus_glm_5_3`, mục 7.9) với cache local riêng; cross-encoder qua GPU Kaggle (link do người dùng đưa khi chạy). Judge của `valid` khác nền tảng với judge của tune (OpenCode): chênh lệch mới đo trên 10 câu (mục 7.9), nên so điểm judge giữa tune và `valid` chỉ ở mức xu hướng. Kết quả `valid` đã đo xong: `docs/eval/15_M1_VALID_15_SYSTEMS.md`.

### 7.9 Surplus Intelligence (đo ngày 2026-11-28)

- **Kết nối:** tương thích OpenAI, `base_url` `https://api.surplusintelligence.ai/v1`, khóa `inf_...` trong biến `SURPLUS_API_KEY` (`.env`). Profile `surplus_glm_5_3` (`glm-5.3`), `surplus_deepseek_flash_1017` (`deepseek-v4.1-flash-1017`), cả hai ghim `provider: "dashscope-cn"` (Alibaba DashScope, id lấy từ `GET /v1/providers`; 47 provider, 17 không trusted).
- **Tắt thinking:** với GLM, `thinking: disabled` bị bỏ qua (reasoning 7 token); chỉ `reasoning_effort: "none"` tắt được (0 token). DeepSeek tắt được bằng cả hai. Hai profile đặt cả hai trường.
- **Giá:** giá mỗi offer do người bán đặt, đổi theo giờ (`GET /api/markets/<model>`; đo lúc 02:00: DashScope giảm 99,9% với GLM, 95–96% với DeepSeek, niêm yết 1,155 / 4,29 và 0,158 / 0,710 USD mỗi triệu token). Tài khoản có **sàn mua tối thiểu giảm giá**; khi offer rơi dưới sàn thì `404 minimum_discount_not_met` (đã gặp với sàn 95%, người dùng hạ xuống dưới 94%). Sàn chỉ đổi được trong cài đặt tài khoản hoặc key, không đổi được qua đường dẫn.
- **Mẫu 10 lần gọi mỗi model** (so với OpenCode, 99 lần): GLM trung vị 3,4 giây (4,1), 47,8 token/s (40,0), 10/10 một lần gọi (OpenCode 30 lần gọi lại); DeepSeek trung vị 1,64 giây (1,42), 15,5 token/s (18,7). Judge GLM trên 10 câu: 9/10 cùng verdict, strict 0,8 (Surplus) và 0,9 (OpenCode). DeepSeek: 9/10 đáp án giống hệt (câu khác: Surplus từ chối). **Cache provider thấp hơn:** GLM 47,3% (OpenCode 64,1%), DeepSeek 40,4% (44,5%); mẫu nhỏ, OpenCode có `session_header`. Vì vậy dùng cache local riêng (`data/llm_cache/surplus_*` hoặc theo từng lần chạy) để chạy lại không tốn lần gọi mới.
