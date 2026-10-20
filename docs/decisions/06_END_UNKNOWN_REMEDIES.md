# Quyết định 06: câu còn sai ở cấu hình tốt nhất, và cách xử lý chunk `unknown`

**Ngày:** 2026-10-20. **Trạng thái:** đề xuất 1 (tách `ongoing`/`unknown`) **đã code và đo ở bộ local** (đợt 3d), kết quả tốt, chờ xác nhận ở bộ thật; các đề xuất 2 đến 5 chưa quyết, chưa code. Số liệu: [`../eval/04_TEST_RESULTS.md`](../eval/04_TEST_RESULTS.md). Nền: [`02_END_TIME_ONGOING.md`](02_END_TIME_ONGOING.md) (các chế độ chấm `end`).

## Tóm tắt

Cấu hình tốt nhất ở bộ local (Cơ chế 1, tìm kiếm dense, `t_unknown` 0.3) vẫn sai 9/40 câu. Tra từng câu thì **không phải LLM gán sai mốc là chính**:
- 5 câu (lỗi **end**): LLM ghi `end_status = unknown` đúng sự thật (văn bản không nói chunk kết thúc khi nào), nhưng **công thức chấm điểm** coi "không biết" như "đã kết thúc".
- 2 câu (lỗi **lọc**): chunk chứa nhiều sự việc trong một khoảng thời gian, và nhãn dataset chỉ chính xác đến năm. Không phải LLM sai.
- 2 câu (lỗi **ngữ nghĩa**): tìm kiếm dense xếp chunk đáp án quá thấp.

Đề xuất làm trước: **tách cách xử lý `ongoing` và `unknown`** (mục 5, đề xuất 1). **Đã đo:** `mrr` 0.580 so với 0.542 của `stored` và 0.544 của `decay` (`hit@5` 0.825 so với 0.800), nhưng phần tăng không đến từ 5 câu lỗi end mà từ chunk `ongoing` không còn bị phạt.

## 1. Công thức chấm điểm hiện tại

`Final = 0.7·Semantic + 0.3·Temporal`. `Temporal` phụ thuộc loại chunk (`end_status` do code suy từ đầu ra LLM):

| Loại chunk | Nghĩa | `stored` (mặc định) | `open` | `decay d` |
|---|---|---|---|---|
| `known` | LLM biết ngày kết thúc | 1.0 nếu `t_req` trong `[start, end]`; sau `end`: `exp(-0.5·Δ)` | như `stored` | như `stored` |
| `ongoing` | Văn bản nói còn tiếp diễn (có câu trích làm bằng chứng) | 1.0 mãi | 1.0 mãi | `exp(-d·Δ)` |
| `unknown` | Văn bản không nói kết thúc hay tiếp diễn | Coi như hết cuối năm `start`, sau đó `exp(-0.5·Δ)` | 1.0 mãi | `exp(-d·Δ)` |
| không có `start` | (nhánh chunk không mốc) | `t_unknown` | `t_unknown` | `t_unknown` |

`Δ` = số năm từ `start` của chunk đến `t_req`. Ba chế độ `stored`/`open`/`decay` là giá trị của cờ `end_mode`; chúng chỉ khác nhau ở hai dòng `ongoing` và `unknown`. **Điểm yếu:** `open` và `decay` xử lý `ongoing` và `unknown` **cùng một cách**, dù hai loại có độ tin cậy rất khác (`ongoing` có bằng chứng, `unknown` không có gì).

## 2. Các nhóm lỗi (9/40 câu sai)

Đặt tên theo nguyên nhân (không dùng A/B/C vì trùng với A/B/C của ba chế độ chấm `end` ở `decisions/02`).

| Nhóm | Số câu | Biểu hiện | Gốc thật |
|---|---|---|---|
| **Lỗi end** | 5 | Chunk đáp án qua lọc, nằm trong 50 ứng viên, nhưng điểm thời gian thấp nên tụt khỏi top 5 | Công thức coi `unknown` như đã kết thúc |
| **Lỗi lọc** | 2 | Chunk đáp án bị lọc cứng loại (`start` sau `t_req`) | Một chunk chứa nhiều sự việc; nhãn dataset ở mức năm |
| **Lỗi ngữ nghĩa** | 2 | Chunk đáp án qua lọc nhưng dense xếp hạng 12 và 46 | Embedding nhỏ (`bge-small`) |

### Lỗi end (5 câu)

Mỗi chunk dưới đây có `end_status = unknown`. Lý do LLM ghi đều kiểu "nothing says when it stopped": LLM đã đọc cả trang và **chủ ý** để `unknown`, không phải gán sai. Bị phạt vì `stored` coi như hết cuối năm `start`:

| Câu (chunk) | `start` | `t_req` | Điểm thời gian (`stored`) | Hạng cuối: `stored` / `open` / `decay 0.1` |
|---|---|---|---|---|
| `Central_European_University` (#6) | 1989 | 1992-11 | khoảng 0.15 | 7 / **1** / **1** |
| `Condor_(airline)` (#3) | 2000 | 2018-01 | 0.0001 | 17 / **5** / 13 |
| `FC_Flora` (#14) | 2017-01 | 2019-08 | khoảng 0.27 | 7 / 10 / **5** |
| `Lotte_Reiniger` (#21) | 1949 | 1972-11 | gần 0 | 30 / 10 / 28 |
| `Volvo_9700` (#3) | 2001 | 2008-12 | khoảng 0.02 | 13 / 6 / 9 |

(Hạng cuối: nền dense, `t_unknown` 0.3. Top 5 mới tính là trúng.) `stored` cứu 0/5 câu vào top 5; `open` và `decay` cứu mỗi cách 2/5.

### Lỗi lọc (2 câu)

- **`New_Orleans_Baby_Cakes`:** hỏi tên chính thức vào cuối thập niên 1980, đáp án Denver Zephyrs. Chunk đáp án (#1) viết "The team began play in **1993** ... when the Denver Zephyrs relocated to Metairie": `start` = 1993 là đúng cho sự việc chính. Tên Denver Zephyrs là **giai đoạn trước 1993** trong cùng chunk, và **không chunk nào trong tài liệu ghi giai đoạn đó bắt đầu từ năm nào** (khoảng 1985 đến 1992 là nhãn dataset, lấy từ nguồn ngoài). Hệ chỉ biết "đến 1993". Hiện chunk chỉ có một khoảng `[start, end]` nên không biểu diễn được "trước 1993, không rõ từ khi nào".
- **`Garnidelia`:** hỏi "in **Mar 2017**", chunk viết "moved to Sacra Music in **April 2017**" (`start` = 2017-04). Nhãn dataset là 2017 đến 2018 (mức năm), bộ sinh câu hỏi chọn "Mar 2017" nằm trong khoảng đó mà không kiểm tra tháng. Theo văn bản, tháng 3 hãng chưa chuyển, nên lọc cứng loại chunk là **đúng**. Đây là nhiễu nhãn mức tháng. Hệ quả cho đánh giá: plain RAG (không lọc) lại có thể đúng câu này, nên nhiễu thiệt riêng Cơ chế 1.

### Lỗi ngữ nghĩa (2 câu)

`Beugró` (dense hạng 12), `Humongous_Entertainment` (dense hạng 46). Chunk đáp án qua lọc và điểm thời gian không phải nguyên nhân chính.

## 3. Đã thử ở bước truy vấn và kết quả

`open` và `decay` (ở `decisions/02`) chữa được 2/5 câu lỗi end mỗi cách, nhưng ở toàn bộ 40 câu lại làm hỏng câu khác (ví dụ `open`: 3 câu lên, 5 câu xuống). Lý do: ở bước chấm không có thông tin nào phân biệt chunk `unknown` còn đúng với chunk `unknown` đã hết hạn thật. `open` cho 1.0 nên chunk cũ ngang chunk đúng thời điểm; `decay` đỡ hơn vì ưu tiên chunk bắt đầu gần `t_req`.

## 4. Đã cân nhắc và bỏ

| Hướng | Lý do bỏ |
|---|---|
| Code suy `end` của chunk `unknown` từ `start` của chunk kế tiếp | **Prompt ingestion đã làm việc này**: LLM đọc cả trang theo thứ tự, và có quy tắc "một sự việc sau chỉ kết thúc sự việc trước khi hai cái không thể cùng đúng (một đội, một chức vụ, một người vợ/chồng); sự việc có thể chồng nhau thì dùng `unknown`", kèm `reason_end_date` bắt buộc nêu tên chunk nếu bằng chứng ở chunk khác. Chunk còn `unknown` là chỗ LLM đã chủ ý không kết luận; code suy thêm sẽ ghi đè phán đoán đó và dễ nối nhầm chuyện khác |
| Bắt LLM trích câu làm bằng chứng cho `start` (`start_evidence`) | Chỉ bắt được năm bịa. Hai câu lỗi lọc không do bịa: năm 1993 và tháng 4/2017 đều xuất hiện nguyên văn trong chunk, nên bằng chứng vẫn "đạt" |
| Điểm sàn cho chunk `unknown` (`Temporal = max(exp(-0.5Δ), u)`) | Gần trùng `decay` (đều là điểm giảm chậm cho chunk `unknown`), không có gì mới |

## 5. Đề xuất

| # | Đề xuất | Làm gì | Chi phí | Chữa |
|---|---|---|---|---|
| 1 | **Tách `ongoing` và `unknown`** | `ongoing` giữ 1.0; `unknown` dùng `decay` riêng. **Đã code (`end_mode: unknown_decay`) và đo: `mrr` 0.580.** Chi tiết dưới | Rẻ: sửa `scoring.py`, không nạp lại kho | Lỗi end (một phần) |
| 2 | **LLM ghi loại sự việc** | Thêm trường: trạng thái thường kéo dài (thành lập, sản xuất, trụ sở) hay sự kiện một lần (phát hành album ngày X). `unknown` + kéo dài thì chấm kiểu `decay`, `unknown` + một lần thì `stored` | Vừa: đổi prompt, ghi `03_PROMPT_CHANGELOG`, nạp lại kho (khoảng 15 phút local, vài giờ bộ thật). Chỉ làm nếu #1 chưa đủ; gộp vào lần nạp bộ thật | Lỗi end |
| 3 | **Một chunk, nhiều khoảng** | Biểu diễn "trước 1993" (khoảng chỉ có `end`) hoặc nhiều khoảng cho một chunk | Lớn: đổi schema và thiết kế; gắn với Cơ chế 2 (mốc theo sự việc). Phải cân nhắc mâu thuẫn bất biến "không rò rỉ tương lai", vì chunk nhắc sự kiện sau `t_req` nhưng được dùng cho `t_req` sớm hơn | Lỗi lọc (1/40 ở local) |
| 4 | **Ghi nhận nhiễu nhãn tháng** | Không nới lọc cứng (sẽ là hack). Ở bộ thật đếm các câu mà `t_req` sớm hơn `start` của chunk đáp án trong vòng một tháng, báo cáo kết quả có và không có chúng | Rẻ | Lỗi lọc (còn lại) |
| 5 | **Reranker hoặc embedding lớn hơn** | Cải thiện xếp hạng ngữ nghĩa | Tốn tính toán. **Quyết định 2026-10-20: chấp nhận lỗi ngữ nghĩa, không sửa; chỉ ghi nhận** | Lỗi ngữ nghĩa |

### Chi tiết đề xuất 1: tách `ongoing` và `unknown` (kế hoạch, chưa code)

**Ý tưởng.** Hai loại có độ tin cậy khác nhau nên xử lý riêng:
- `ongoing`: văn bản **có câu nói còn tiếp diễn** (có câu trích, code đã kiểm tra), nên tin: điểm 1.0 với mọi `t_req` sau `start`.
- `unknown`: **không có thông tin gì**. Không nên coi là "đã kết thúc" (như `stored`), cũng không nên coi là "còn mãi" (như `open`). Hợp lý nhất là "còn có thể đúng, nhưng càng xa `start` càng kém tin": điểm giảm dần.

**Công thức** cho chunk `unknown` (sau khi `t_req` ≥ `start`):

`Temporal = exp(-d · Δ)`, với `Δ` là số năm từ `start` đến `t_req`, `d` là tốc độ giảm.

`d` đọc theo chu kỳ bán rã (sau bao nhiêu năm điểm còn một nửa):

| `d` | Chu kỳ bán rã | Chunk `unknown` bắt đầu 2000, hỏi 2018 |
|---|---|---|
| 0.05 | 13.9 năm | 0.41 |
| 0.1 | 6.9 năm | 0.17 |
| 0.2 | 3.5 năm | 0.03 |
| 0.3 | 2.3 năm | 0.005 |

So với `stored` (0.0001 ở ví dụ này) và `open` (1.0).

**Cách đã đổi mã.** Thay vì tách `end_mode` thành hai lựa chọn độc lập, làm bản nhỏ nhất: thêm **một giá trị mới** `end_mode: unknown_decay` (cờ `--end-mode unknown_decay --open-decay d`) trong `scoring.py`: `ongoing` như `stored` (1.0 mãi), `unknown` `exp(-d·Δ)`, `known` như cũ. Ba chế độ cũ (`stored`, `open`, `decay`) **không đổi hành vi** (có test kiểm tra). Việc tách hẳn thành `ongoing_mode`/`unknown_mode` độc lập chưa cần.

**Kết quả đo** ([`../eval/04_TEST_RESULTS.md`](../eval/04_TEST_RESULTS.md) đợt 3d, nền dense, quét `d` 0.05 đến 0.3 × `t_unknown` tắt, 0.0 đến 0.7, 32 lần chạy):

| `end` | `mrr` / `hit@5` (`t_unknown` tắt) | `mrr` / `hit@5` (`t_unknown` 0.1) |
|---|---|---|
| `stored` | 0.494 / 0.675 | 0.542 / 0.800 |
| `open` | 0.519 / 0.700 | 0.525 / 0.725 |
| `decay 0.1` (cả hai loại) | 0.471 / 0.700 | 0.544 / 0.800 |
| **`unknown_decay 0.1`** | **0.525 / 0.725** | **0.580 / 0.825** |

- Cao nguyên: `d` 0.05 đến 0.2 với `t_unknown` 0.1 đến 0.4 đều cho 0.545 đến 0.581.
- So từng câu (`t_unknown` 0.1): so với `stored` 3 lên 2 xuống; so với `open` 9 lên 1 xuống; so với `decay` 2 lên 1 xuống. Chênh với `decay` và `stored` chưa chắc chắn từng câu.
- 5 câu lỗi end: vào top 5 được 2/5 (giống `decay` và `open`), không hơn. **Phần tăng đến từ câu khác**, nơi chunk `ongoing` không còn bị `decay` phạt (`Casus_Belli`, `Jean_Lassalle`).
- Dự đoán trước đó ở bản nháp này (tách `ongoing` chỉ đổi rất ít vì chỉ 34 chunk `ongoing` so với 187 `unknown`) **sai**: `mrr` tăng 0.036 so với `decay`.
- Cảnh báo: thêm 32 cấu hình trên 40 câu, nên con số đứng đầu là cận trên; cần xác nhận ở bộ thật.

**Còn lại:** 5 câu lỗi end vẫn chưa được chữa tốt hơn `decay`. Nếu bộ thật cho thấy lỗi end còn nhiều, thì đề xuất 2 (LLM ghi loại sự việc) là bước kế tiếp.

## 6. Ảnh hưởng thiết kế

- `docs/design/02` (Temporal_Score: TH1 khi `t_req` trong `[start, end]`, TH2 giảm dần) giả định `end_time` đáng tin. Thực tế `end` thường là `unknown`; nếu chọn đề xuất 1 hoặc 2 thì bước chấm điểm của design 02 phải ghi cách xử lý `unknown`.
- Đề xuất 3 (một chunk nhiều khoảng) trùng với hướng "mốc theo sự việc" của Cơ chế 2 (`decisions/02`, hướng (b), (c)): nên thiết kế chung, không làm riêng hai lần.

## 7. Điều cần đo nếu làm

- 5 câu lỗi end: lên top 5 bao nhiêu câu; số câu mới tụt (so với `stored`, `open`, `decay`).
- `mrr` và `hit@5` toàn bộ local (nền dense + `t_unknown` 0.2) trước và sau.
- Xác nhận trên bộ thật (400 câu), vì local chỉ có 5 câu lỗi end (sai số lớn). Cẩn thận chọn lọc quá khớp: càng thử nhiều `d` trên 40 câu càng bị đánh giá cao.
