# Nhật ký triển khai 05: Ngữ nghĩa mốc thời gian, chia chunk và các vấn đề còn mở

Tiếp nối [`04_PROFILER_METRICS_INGESTION.md`](04_PROFILER_METRICS_INGESTION.md) mục 6. File này ghi lại các vấn đề phát hiện khi đọc dữ liệu TimeQA thật (`dataset/full_dataset/`) và các quyết định rút ra. Phần "đã làm" nhỏ; phần lớn là **vấn đề đã phân tích nhưng chưa sửa code**, ghi rõ để tuần sau khỏi phân tích lại. Chủ đề (`domain`) có file riêng: [`dataset/full_dataset/TOPICS.md`](../../dataset/full_dataset/TOPICS.md).

Số liệu lấy từ các tập `hard` của `D/test` (830 câu) và `D/train`, tính bằng script ngoài repo; chưa có metric nào trong repo tính các số này. Các số có chú thích "regex thô" chỉ để ước lượng.

---

## 1. Đã làm được

| Hạng mục | File | Ghi chú |
|---|---|---|
| Tách `source` và `doc_id` | `schemas/chunk.py`, `ingestion/loaders/timeqa.py`, `ingestion/pipeline.py`, `ingestion/types.py` | `source` = nơi phát hành (Wikipedia, tên báo), khóa tra credibility ở CC3; `doc_id` = tài liệu cụ thể (`/wiki/Knox_Cunningham`), tùy chọn, không index. `load_pages(..., source="Wikipedia")` truyền được nguồn khác, không fix cứng. Design 02 mục schema đã cập nhật |
| Sửa lint | `pyproject.toml`, `config/logging.py`, vài test | `ruff` 0.16.10 sạch. `DTZ001` bỏ qua trong `tests/*` vì test cố ý dùng datetime không múi giờ |
| README từng module | `src/tam/*/README.md` | Sơ đồ thứ tự vận hành: mỗi khối một file, node là `Class.hàm`, mũi tên đánh số |
| Phân tích chủ đề | `dataset/full_dataset/TOPICS.md` | `relation` là gì, vì sao không dùng làm filter, đề xuất 8 domain + `other`, tối đa 3 nhãn mỗi chunk |
| Prompt ingestion | `src/tam/llm/prompts/ingestion_time.md` | Cho phép suy mốc từ các chunk khác cùng tài liệu; ba trạng thái của `end`; 5 ví dụ mới (xem mục 3) |
| Test | toàn bộ | 121 xanh, 4 xfail cũ, chạy với Qdrant thật (docker) |

**Không đổi code logic ingestion** (`to_span`, `TimeExtractor`): chỉ prompt. `ChunkTime` chưa có trường nhãn chủ đề.

## 2. Chia chunk

### 2.1. Số liệu của `paragraphs`

- Mỗi trang trung vị 19 đoạn (tối đa 100), mỗi đoạn trung vị 69 từ, **tối đa đúng 100 từ**, p10 là 16 từ. Dataset đã chia sẵn theo cửa sổ khoảng 100 từ, có tiêu đề mục.
- 1.5% đoạn chỉ có 3 từ trở xuống (vd chỉ một dấu `.`).
- Đáp án nằm trọn trong **một** đoạn: 841/887 vị trí (95%); 44 (5%) là đáp án nằm ngay **tiêu đề mục** (vd "Tamworth"); 2 vị trí vắt qua hai đoạn.

### 2.2. Chunk ngắn có đủ ý không (788 chunk chứa đáp án)

| Đo | Kết quả |
|---|---|
| Chứa ít nhất một năm | 94% |
| Chứa đúng năm bắt đầu của sự kiện | 67% (527) |
| Năm bắt đầu chỉ có ở chunk liền trước hoặc liền sau | 6% (51) |
| Không có năm nào | 6% (45) |
| Dưới 30 từ | 4% (34) |
| Mở đầu bằng đại từ hoặc mạo từ ("He", "The") | 18% (141) |

Header `"Tên trang | Tên mục"` bù phần thực thể. Còn 27% chunk có năm bắt đầu theo nhãn dataset mà không thấy nguyên văn trong chunk hay chunk lân cận; chưa kiểm tra lý do, nhiều khả năng nhãn ghi mốc theo cách khác văn bản.

### 2.3. Quyết định

| Quyết định | Trạng thái |
|---|---|
| Chunk = một phần tử của `paragraphs` (đúng như `chunk_document` đang làm) | Giữ nguyên |
| **Không** gộp các đoạn cùng tiêu đề: gộp sẽ làm một chunk chứa nhiều mốc thời gian khác nhau, khoảng hiệu lực rộng và `Temporal_Score` mất khả năng phân biệt | Đã chốt |
| **Không** để LLM chia lại chunk: kết quả không tất định, `chunk_id` đổi giữa các lần chạy, nhãn đúng hỏng | Đã chốt |
| Khi sinh đáp án, đưa thêm chunk liền trước và liền sau (`page#(i-1)`, `page#(i+1)`) vào context. `chunk_id` đã có chỉ số đoạn nên không cần đổi schema | Đã chốt, **chưa làm** (chờ `generation/`) |
| Bỏ hoặc gộp mảnh quá nhỏ (vd dưới vài từ) vào đoạn trước | Chưa quyết. Nếu làm thì **phải tính lại chỉ số** trong `chunk_id` và nhãn đúng |

### 2.4. Nhãn đúng: `chunk_id` có trước khi gọi LLM

`chunk_id = "<page_id>#<chỉ số đoạn>"` do `chunk_document` sinh, **không phụ thuộc LLM**; LLM chỉ thêm `start_time`/`end_time`. Nên nhãn đúng cho mỗi câu hỏi tạo được offline, không tốn token:

1. Tìm vị trí text của từng đoạn trong `context` (duyệt tuần tự; thử trên 830 câu: ánh xạ được 100% trang).
2. Mỗi cặp `from`/`end` của câu hỏi thuộc đoạn nào thì lấy chỉ số đoạn đó.
3. Đáp án nằm ở tiêu đề mục (rơi vào khe giữa các đoạn) thì lấy đoạn kế tiếp (đúng 36/44 trường hợp, tức đoạn kế tiếp có `title` bằng đáp án).

Có hơn một chunk đáp án ở 26/830 câu (3%): `EvalCase.gold_ids` đã là tập hợp. **Chưa có script tạo nhãn.**

Lưu ý khi dùng: chunk đúng có thể bị bỏ lúc ingestion (không có năm, hoặc mốc sai), nên Hit@k thấp chưa chắc do retriever. Cần chỉ số "tỉ lệ chunk đáp án còn sống sau ingestion" và tính Hit@k trên các câu mà chunk đúng còn sống.

## 3. Mốc thời gian của chunk

### 3.1. LLM suy mốc từ cả trang

`TimeExtractor` vốn gửi **cả lô chunk của một trang** (tối đa 30 chunk mỗi lệnh gọi, trang trung vị 19 chunk nên thường một lệnh), nên LLM đã thấy toàn bộ. Cái cản là một dòng prompt cũ "chỉ dùng ngày có trong chính chunk". Đã sửa: được dùng ngày từ chunk khác của cùng tài liệu và tiêu đề, **vẫn cấm kiến thức ngoài tài liệu**.

Giới hạn không thể vượt: trên 1,812 câu, năm bắt đầu có xuất hiện trong trang ở 90% (1,625), năm kết thúc ở 83% (1,496). Tức 10% đến 17% sự kiện mà trang không viết ra mốc, LLM suy cũng không ra (cận trên, chỉ kiểm tra chuỗi năm có mặt).

### 3.2. Ba trạng thái của `end`

Cần phân biệt "đã kết thúc", "còn hiệu lực đến hiện tại" và "không biết". Cơ chế đã có sẵn trong `ChunkTime`/`to_span`, chỉ là trước đây prompt không nói rõ:

| Trạng thái | LLM trả | `to_span` cho `end_time` | Ý nghĩa với `Temporal_Score` |
|---|---|---|---|
| Đã kết thúc | `end` có giá trị | đúng ngày đó (chỉ-năm thì `YYYY-12-31`) | TH1 trong khoảng; ngoài khoảng thì TH2 |
| Còn hiệu lực | `end = null`, `ongoing = true` | `None` | TH1 với mọi `t_req >= start` |
| Không biết | `end = null`, `ongoing = false` | **cuối kỳ của `start`** (vd "joined in 2005" → `2005-12-31`) | `t_req` nằm trong kỳ `start` (vd trong năm 2005) thì TH1; `t_req` lớn hơn `end_time` (vd năm 2007) thì TH2 (decay). TH1/TH2 là kết quả tính cho **từng cặp (chunk, `t_req`)**, không phải hai giai đoạn nối tiếp |

`ongoing` chỉ nằm ở đầu ra của LLM (`ChunkTime`); `Chunk` lưu trong kho chỉ có `end_time`, trong đó `None` là còn hiệu lực. Vì vậy sau khi lưu, trạng thái "không biết" không còn phân biệt được với "đã kết thúc" (cả hai đều có `end_time` là một ngày). Điều này không ảnh hưởng cách chấm điểm hiện tại, nhưng **nên lưu** (đề xuất, chưa làm): thêm vào `Chunk` một trường không index `end_status` nhận `known`, `ongoing` hoặc `unknown` (`ongoing` thì `end_time = None`). Lý do:
- Đầu ra LLM tốn token để làm lại; có trạng thái trong kho thì đổi cách xử lý "không biết" mà **không phải ingest lại**.
- Cho phép ablation: coi "không biết" là đã kết thúc ở cuối kỳ `start` (hiện tại), hay coi là có thể còn hiệu lực (điểm không tụt về gần 0, hoặc `end_time = None`).
- Time-CoT có thể cảnh báo "chưa rõ khi nào kết thúc".
- Payload không index nên không vi phạm bất biến 4 trường.

Coi "không biết" là có thể còn hiệu lực (hướng "xét cả ongoing") thì tăng độ phủ với câu hỏi về hiện tại ("currently", `t_req = T_now`), vì chunk còn hiệu lực trả lời được rất nhiều câu hỏi. Nhưng như ví dụ A, B, C ở trên, nếu áp cho mọi chunk thiếu `end` thì thời gian mất khả năng phân biệt chunk mới nhất. Cách dung hòa cần đo: chỉ những chunk **không biết** mới được ưu đãi (vd điểm sàn thay vì decay về 0), còn chunk đã `known` thì giữ nguyên.

**Vì sao không để `NULL` cho trạng thái "không biết":** `NULL` nghĩa là còn hiệu lực. Trang sự nghiệp có các chunk "In 2001 he joined A", "In 2005 he moved to B", "In 2010 he moved to C" mà không nêu ngày rời đi: nếu cả ba `NULL` thì cả ba đều TH1 với `t_req = 2012`, thời gian không phân biệt được chunk mới nhất. Với "cuối kỳ của start", chunk C có `start` gần nhất nên điểm decay cao nhất, đúng ý của cơ chế TH2 ("lùi về quá khứ gần nhất").

Để mốc đúng hơn mà không phải đoán, prompt cho LLM tự đặt `end` khi văn bản cho thấy nó chấm dứt:
- Từ khóa kết thúc: "left", "moved to", "was replaced by", "resigned", "until", "retired", "divorced", "died".
- Chỉ sự kiện **loại trừ nhau** (một đội, một chức vụ, một vợ/chồng tại một thời điểm) mới bị sự kiện sau kết thúc. Việc làm hoặc tư cách thành viên có thể song song thì không (dùng trạng thái "không biết").
- Còn tồn tại đến khi người mất và trang có ngày mất thì `end` = ngày mất.

Ví dụ trên: A = 2001 đến 2005, B = 2005 đến 2010, C = 2010 đến `NULL` (nếu nói "still at the club"). Cách này cũng khớp bất biến *Timeline ≠ Conflict*: sự kiện sau chỉ đóng sự kiện trước khi văn bản nói rõ (hoặc chúng loại trừ nhau), không đóng tự động.

### 3.3. Ví dụ few-shot đã thêm (`ingestion_time.md`)

Có 4 ví dụ cũ (một chunk) và 5 ví dụ mới (nhiều chunk, cùng một tài liệu):

| Ví dụ | Dạy điều gì |
|---|---|
| Sam Rivera (3 câu lạc bộ) | `end` suy từ sự kiện kế tiếp loại trừ nhau; chunk cuối `ongoing` |
| Gary Mills (bổ nhiệm, kết quả, rời đi) | Chunk không có mốc riêng kế thừa `start` và `end` của cùng giai đoạn |
| Pat Moore (thị trưởng đến khi mất) | `end` = ngày mất lấy từ chunk khác |
| Dr Lee (hai tư cách thành viên) | Sự kiện có thể song song **không** bị chấm dứt: `end` = null, `ongoing` = false |
| Riverside FC (mô tả) | Không có mốc ở bất kỳ đâu: `start` = null, bị bỏ |

**Chưa kiểm chứng với LLM thật.** Cần đo: số chunk bị `no_time` trước và sau khi sửa prompt, và độ đúng của mốc suy luận (nguy cơ: kế thừa mốc sai cho chunk không liên quan).

### 3.4. `start_time` bắt buộc, và chunk không có mốc

`start_time` cần cho cả hard filter (`start_time <= t_req`) và `Temporal_Score`, nên chunk không suy ra được thì **bị bỏ** (`skipped_no_time`), đúng bất biến. Trên 788 chunk đáp án: 45 (6%) không có năm nào. Thông tin này đôi khi quan trọng, nên đề xuất (chưa vào design, chưa code):

1. Thang xử lý: mốc trong chunk, rồi kế thừa từ chunk lân cận cùng giai đoạn, rồi bỏ khỏi nhánh time-aware.
2. **Không bịa mốc**: mốc sai làm hỏng cả lọc cứng lẫn `Temporal_Score`.
3. Chunk không có mốc **không vứt**: giữ trong cùng collection với `start_time = NULL`. Hard filter `start_time <= t_req` tự loại chúng khỏi nhánh time-aware (Qdrant range filter không khớp trường rỗng) nên không rò rỉ. Khi kết quả ít hoặc điểm thấp, tìm thêm trong nhóm này bằng hybrid search thường (lọc `IsNull(start_time)`; `start_time` đã là payload index nên không thêm index mới, cần kiểm tra bằng test Qdrant thật).
4. Time-CoT phải ghi rõ "thông tin này không xác định được thời điểm".
5. Báo cáo: tỉ lệ chunk đáp án còn trong kho time-aware, và tỉ lệ câu chỉ trả lời được nhờ nhóm không có mốc. Với plain RAG mọi chunk đều trả lời được nên so sánh công bằng cần ghi rõ phần coverage này.

Cần sửa design: `Chunk.start_time` thành tùy chọn; bất biến "không có mốc thì không vào kho" thành "không vào nhánh time-aware". **Chưa quyết, chưa sửa.**

## 4. `Temporal_Score = 1` khi nào, và câu hỏi theo khoảng thời gian

### 4.1. Hiện trạng

`t_req` là **một điểm**. `Temporal_Score = 1.0` (TH1) khi `end_time` rỗng hoặc `end_time >= t_req`; hard filter đã đảm bảo `start_time <= t_req`, nên TH1 nghĩa là `t_req` nằm trong `[start_time, end_time]`. Ngược lại TH2 = `exp(-λ·Δyears)` với `Δyears` tính từ `start_time`.

TH1 **vẫn được xếp hạng**: `Final = W1·Semantic + W2·1.0`. Khi nhiều chunk cùng TH1, phần thời gian bằng nhau và `semantic_score` quyết định; hòa hoàn toàn thì xét `temporal_score` rồi `chunk_id`.

Profiler quy khoảng thời gian về một điểm bằng cách **lấy mốc cuối khoảng** ("during the 1990s" thành `1999-01-01`, "before X" thành X). Chưa có quy tắc cho "after X" hay "since X" trong `time_extractor.md`.

### 4.2. Vấn đề: người dùng hỏi theo khoảng

Phân loại câu `D/test.hard` bằng regex thô (830 câu):

| Dạng | Số câu | Tỉ lệ |
|---|---:|---:|
| between X and Y | 302 | 36% |
| before X | 56 | 7% |
| after, since X | 68 | 8% |
| early, mid, late; thập niên | 70 | 8% |
| còn lại (điểm "in/by tháng năm", một số là "in 2005 to 2006" lẫn vào) | 334 | 40% |

Ở mức easy, 757/830 câu (91%) là "from X to Y". Tức **khoảng thời gian là dạng phổ biến**, không phải ngoại lệ.

Hệ quả của việc quy về điểm cuối khoảng: chunk có hiệu lực `[s, e]` giao với khoảng hỏi `[a, b]` nhưng `e < b` bị TH2 trừ điểm dù đúng. Ví dụ hỏi "between Jan 1998 and Apr 2000", chunk hiệu lực 1998 đến 1999 vẫn trả lời đúng nhưng `t_req = 2000-04` nằm ngoài khoảng, điểm thành `exp(-0.5·Δ)`. Mặt khác, câu "after X" chưa có quy tắc.

### 4.3. Đề xuất (chưa quyết, chưa code)

| | Hiện tại | Đề xuất |
|---|---|---|
| Truy vấn | một điểm `t_req` | `t_req` (mốc cuối) + `t_req_start` tùy chọn (mốc đầu); "before X" thì một điểm (xem 4.4); "after X" thì khoảng là `[X, T_now]` |
| Hard filter | `start_time <= t_req` | giữ (`t_req` là mốc cuối): vẫn không rò rỉ tương lai |
| TH1 | `t_req ∈ [start, end]` | hai khoảng **giao nhau** |
| TH2 | `Δyears` từ `start_time` đến `t_req` | khoảng cách từ `end_time` của chunk đến `t_req_start` (cần cân nhắc) |
| Điểm TH1 | nhị phân 1.0 | nhị phân, hoặc theo tỉ lệ giao (ablation) |

### 4.4. Xử lý từng dạng câu hỏi (đề xuất)

Gọi khoảng của câu hỏi là `[a, b]`. Profiler trả `t_req = b` (như hiện tại) và `t_req_start = a`.
- **Hard filter:** luôn `start_time <= b`, nên không rò rỉ tương lai ở mọi dạng.
- **TH1:** khoảng của chunk `[start, end]` giao với `[a, b]`, tức `start <= b` và (`end` rỗng hoặc `end >= a`).
- **TH2:** chunk không giao (kết thúc trước `a`): `exp(-λ·Δyears)` với `Δyears = b - start_time`. Giữ nguyên công thức hiện tại (khi `a = b` thì y hệt); phương án thay thế là đo từ `end_time` đến `a`, để ablation.

| Dạng | Ví dụ | `[a, b]` | Ghi chú |
|---|---|---|---|
| Điểm (năm hoặc tháng) | "in 2005", "in Dec 2004" | cả kỳ: `[2005-01-01, 2005-12-31]`, `[2004-12-01, 2004-12-31]` | Xem lỗi về độ chính xác ngay dưới bảng |
| between X and Y | "between Apr 1987 and Nov 1988" | `[1987-04-01, 1988-11-30]` | TH1 cho chunk bất kỳ giao với khoảng |
| before X | "before Apr 2004" | `a = b = 2004-04-01` (ngày đầu của kỳ X, **tính cả X**) | Một điểm: cần chunk đang hiệu lực khi X sắp đến, không phải mọi chunk cũ hơn. Chunk không chứa điểm đó thì TH2, ưu tiên chunk gần nhất. Xem 4.5 về dữ liệu |
| after, since X | "after Jul 2018" | `[2018-07-01, T_now]` | Nhiều chunk có thể giao với khoảng này, nên `semantic_score` quyết định phần lớn. Quy tắc chưa có trong `time_extractor.md`; cần ablation xem nên ưu tiên chunk bắt đầu sớm nhất sau X hay không |
| early, mid, late; thập niên | "late 1990s", "the 1990s" | chia ba phần của thập niên: early `1990` đến `1993`, mid `1994` đến `1996`, late `1997` đến `1999`; "the 1990s" là `[1990-01-01, 1999-12-31]` | Giao khoảng nên chunk ở bất kỳ chỗ nào trong khoảng đều TH1 |

**Lỗi độ chính xác hiện có (đã tồn tại, không chỉ ở đề xuất này):** Profiler đổi "in 2005" thành `2005-01-01`, rồi hard filter `start_time <= 2005-01-01` loại mất chunk bắt đầu giữa năm 2005 (vd 2005-07) dù nó có hiệu lực trong năm 2005. Lấy `b` là **cuối kỳ** của mốc được nhắc (`2005-12-31`) thì không còn loại sai. Việc này nên sửa dù có làm `t_req_start` hay không. **Chưa sửa.**

### 4.5. "before X": vì sao lấy một điểm

Trên 497 câu "before X" (`D/test`, `D/train`, `C/test`, `C/dev`, mức hard, X có tháng) so khoảng đáp án theo nhãn `time_start`, `time_end` với X:

| Quan hệ giữa khoảng đáp án `[a, b]` và X | Số câu |
|---|---:|
| Chứa ngày liền trước X (và thường vắt qua X) | 476 (96%) |
| Bắt đầu đúng ngày đầu tháng của X (vd hỏi "before Apr 2004", đáp án bắt đầu "Apr 2004") | 19 (4%) |
| Bắt đầu sau X (nhãn lạ) | 2 |

Không có câu nào đáp án kết thúc trước X. Tức đáp án "before X" gần như luôn là sự việc **đang hiệu lực khi X đến**, nên dùng một điểm là đúng, không phải "mọi sự việc trước X". Vì nhãn chính xác đến tháng, nên điểm nên là `2004-04-01` (ngày đầu kỳ X, tính cả X) chứ không phải `2004-03-31`: cách sau loại mất 19 câu trên khi hard filter `start_time <= b` (đúng 4% số câu "before").

Giới hạn: số liệu dựa trên nhãn của dataset (mốc hard nằm trong khoảng nhãn), chưa kiểm tra với văn bản trang. Với dữ liệu ngoài TimeQA, "before X" có thể nghĩa là "mọi sự việc trước X"; khi đó cần trả nhiều chunk.

### 4.6. Câu hỏi chi tiết hơn chunk (hỏi theo tháng, chunk chỉ có năm)

Mốc trong chunk có độ chính xác khác nhau (`2005`, `2005-03`, `2005-03-15`) nhưng lưu thành datetime đầy đủ: `start` chỉ-năm thành `YYYY-01-01`, `end` chỉ-năm thành `YYYY-12-31`. Hệ quả:

- Chunk nói "in 2005" lưu `[2005-01-01, 2005-12-31]`. Câu hỏi "in Mar 2005" giao với khoảng đó nên **TH1** dù sự việc có thể xảy ra từ tháng 10. Hệ thống không thể biết, và cố ý không loại: loại nhầm sẽ mất đáp án, còn giữ nhầm chỉ làm xếp hạng kém chính xác hơn.
- Câu hỏi "in Dec 2004" với chunk "2005": `start = 2005-01-01 > b = 2004-12-31` bị hard filter loại, đúng.
- **Bất biến "không rò rỉ tương lai" chỉ đảm bảo ở độ chính xác của dữ liệu.** Chunk `start` chỉ-năm có thể thực ra bắt đầu muộn hơn trong năm; hệ thống chỉ biết "không sớm hơn đầu năm".
- Hai chunk cùng ghi "2005" (vd "In 2005 he joined A" và "In 2005 he left A and joined B") trùng khoảng nên thời gian không phân biệt được, `semantic_score` và Time-CoT phải xử lý.

Đề xuất (chưa làm): lưu thêm `start_precision` và `end_precision` (`year`, `month`, `day`), không index. Dùng cho: báo cáo (bao nhiêu chunk chỉ có độ chính xác năm), ablation (chunk độ chính xác thấp có nên được điểm thấp hơn TH1 đầy đủ khi câu hỏi chi tiết hơn), và Time-CoT ghi rõ "chỉ biết năm".

### 4.7. Decay khi khoảng cách tính bằng ngày

`Δyears` **không** làm tròn theo năm: `delta_years` chia số giây cho một năm Julian (365.25 ngày), nên khoảng cách vài ngày vẫn ra số thập phân và công thức chạy được. Nhưng với `λ = 0.5` (đơn vị: trên năm; chu kỳ bán rã `ln2/0.5` ≈ 1.39 năm ≈ 506 ngày) điểm gần như không đổi ở thang ngày:

| Khoảng cách | `Temporal_Score` |
|---|---:|
| 1 ngày | 0.9986 |
| 7 ngày | 0.9905 |
| 30 ngày | 0.9598 |
| 180 ngày | 0.7816 |
| 1 năm | 0.6067 |
| 5 năm | 0.0821 |

Với `W2 = 0.3`, chênh lệch 1 ngày chỉ làm `Final` khác khoảng 0.0004, nhỏ hơn nhiều so với chênh lệch `semantic_score`. Tức decay hiện tại chỉ có ý nghĩa ở thang năm (luật, chức vụ, TimeQA). Với dữ liệu mà các phiên bản cách nhau vài ngày (tin tức, giá cả), `λ` này không phân biệt được.

Hướng xử lý (chưa làm, cần khi có dữ liệu thang ngày):
- `λ` hoặc **chu kỳ bán rã theo từng domain** (luật tính bằng năm, tin tức tính bằng ngày), cấu hình trong yaml; khớp với tên "Half-life Decay" của design, khi viết `0.5^(Δ/half_life)` thì đơn vị tự do.
- Hai điều kiện đi kèm: độ chính xác mốc (mục 4.6) phải đến ngày thì mới có ý nghĩa; chunk chỉ-năm có `start = 01-01` làm `Δ` sai lệch tới gần một năm so với ngày thật.
- Tinh chỉnh `λ`, `W1/W2` đã có trong kế hoạch (tách mẫu `D/train` khỏi `D/test`).

Việc phải sửa nếu làm: `schemas/query.py`, `retrieval/temporal/scoring.py` (thêm hàm giao khoảng), `retrieval/temporal/filters.py`, prompt + `Extraction` của Profiler (few-shot cho between/after/before), `metrics_temporal.py`, design 02 mục 3 và 4. Cần có ca test cho mỗi dạng.

## 5. Chủ đề (`domain`)

Chi tiết ở `TOPICS.md`. Tóm tắt các quyết định:

- `relation` là nhãn của **câu hỏi**; 99% trang (và chunk đáp án) chỉ có một `relation`, nên lọc chunk theo `relation` là rò rỉ nhãn của bộ test. Chỉ dùng `relation` để chia nhóm khi báo cáo và để kiểm chứng nhãn LLM.
- `domain` của chunk do LLM gán từ văn bản, **tối đa 3 nhãn** (đã chốt), danh sách đóng dùng chung giữa ingestion và Profiler.
- Đề xuất 8 domain + `other` (`business`, `sports`, `career`, `person`, `politics`, `place`, `media_arts`, `military`), mỗi domain liệt kê các P; **chưa chốt**.
- Việc cần sửa: `Extraction.domain` thành danh sách đóng, `passes_hard_filter` đổi `==` thành `in`, thêm `topics` vào `ChunkTime` và prompt.
- Lợi ích của filter chủ đề trên TimeQA có thể nhỏ (câu hỏi nào cũng nêu tên thực thể); cần ablation có và không có.

## 6. Quyết định đã chốt và còn mở

| Chủ đề | Trạng thái |
|---|---|
| Chunk = đoạn của `paragraphs`, không gộp, không để LLM chia lại | Đã chốt |
| Trả thêm chunk trước và sau khi sinh đáp án | Đã chốt, chưa làm |
| LLM suy mốc từ cả trang, cấm kiến thức ngoài | Đã chốt, đã sửa prompt |
| Ba trạng thái của `end`; "không biết" thì cuối kỳ của `start` | Đã chốt, đã sửa prompt |
| Tối đa 3 nhãn `domain` mỗi chunk | Đã chốt |
| Danh sách 8 domain | Chưa chốt |
| Chunk không có `start_time`: giữ ở nhánh không có mốc | Chưa quyết |
| Câu hỏi theo khoảng thời gian: `t_req_start`, TH1 theo giao khoảng | Chưa quyết |
| Bỏ hoặc gộp mảnh nhỏ | Chưa quyết |
| Lưu `end_status` (`known`, `ongoing`, `unknown`) vào chunk (mục 3.2) | Đề xuất, chưa quyết, chưa thêm |
| Lưu `start_precision`, `end_precision` (mục 4.6) | Đề xuất, chưa quyết, chưa thêm |
| Ghi nguồn gốc mốc (nêu rõ / kế thừa / suy từ trang) vào chunk để ablation | Chưa quyết, chưa thêm |
| "before X": một điểm `b = X` (ngày đầu kỳ X, tính cả X) | Đề xuất có số liệu (mục 4.5), chưa code |

## 7. Việc tiếp theo

1. Chạy thử ingestion với LLM thật trên bộ local (21 trang): xem số chunk `no_time` sau khi sửa prompt, độ đúng của mốc suy luận (đã dặn ở process 04 mục 6, chưa làm).
2. Script tạo nhãn `gold_chunk_ids` cho từng `idx` của bộ local và bộ thật (mục 2.4), kèm chỉ số "tỉ lệ chunk đáp án còn sống".
3. Chốt mục 4 (khoảng thời gian) vì ảnh hưởng đến Profiler, scoring, metric và design.
4. Chốt danh sách `domain`, rồi thêm `topics` vào `ChunkTime`, Profiler và `passes_hard_filter`.
5. `generation/time_cot.py` với việc mở rộng chunk liền trước và liền sau.
