# 10. Thiết kế bộ dữ liệu tự dựng cho Cơ chế 2 (timeline vàng viết từ chunk gốc)

Ghi ngày 2026-11-04. **Trạng thái: thiết kế (mục 1 đến 9) là đề xuất; đã chạy mẫu thử 5 và 10 trang để kiểm quy trình viết timeline (mục 10).** Chưa sinh câu hỏi, chưa chạy hệ nào trên bộ này. Các con số đếm ở mục 1 đến 9 là ước lượng thô, có chú thích rõ.

Quan hệ với tài liệu khác: [`08_TIMELINE_EVAL_DESIGN.md`](08_TIMELINE_EVAL_DESIGN.md) thiết kế đo dựa trên chú thích TimeQA (oracle dựng từ nhãn có sẵn, `timeline_gold` có lỗi gold, xem `src/tam/evaluation/timeline_gold.py`); file này là hướng thay thế: **người (hoặc subagent) đọc chunk gốc và viết timeline vàng**, câu hỏi sinh bằng mã. Lý do chọn tự dựng: các bộ công bố (ECT-QA, TLQA, ADQAB, TDBench) đều lệch miền, thiếu gold chunk hoặc thiếu văn bản (xem `research/benchmarks_for_comparison/timeline_summarization/` và `03_EVALUATION_PLAN_BY_MECHANISM.md`).

## 1. Nguồn và quy mô

- **Nguồn:** các trang `real` đã chia sẵn theo trang thành ba tập không trùng nhau: `tune` 203 trang, `valid` 167, `test_clean` 186.
- **Quy mô đề xuất (chưa chốt):** tune 300, valid 300, test 400 câu; khoảng 35, 35, 45 thực thể (mỗi thực thể khoảng 8 đến 9 câu). Mỗi trang là một thực thể chính.
- **Cỡ mẫu thực là số thực thể, không phải số câu**: các câu cùng thực thể dùng chung timeline nên tương quan. Giả định hệ số tương quan trong nhóm ≈ 0.3 (**chưa đo**) thì 400 câu / 45 thực thể tương đương khoảng 109 câu độc lập. Báo cáo phải ghi cả hai số và tính sai số chuẩn gom theo thực thể.
- **Ngưỡng nhận biết khác biệt:** với 100 câu độc lập, hai phương pháp cần lệch khoảng 11 đến 14 câu mới đạt 2 sai số chuẩn; bộ này chỉ phân biệt được chênh lớn (kiểu oracle so với vector top-k), không phân biệt hai biến thể đồ thị lệch vài điểm.
- **Đếm trang đủ điều kiện (bước 0):** chỉ là ước lượng, vì `extractions.jsonl` chỉ lưu 300 ký tự đầu mỗi chunk (`scripts/ingest.py:68`) nên số năm đếm được bị đánh thấp. Với điều kiện "≥3 chunk có ≥2 năm và ≥10 năm khác nhau" còn 154 / 203 (tune), 138 / 167 (valid), 141 / 186 (test_clean). Khi làm thật phải đọc văn bản đầy đủ từ `dataset/full_dataset/pages.jsonl`.

## 2. Quy trình sinh

```mermaid
flowchart TD
    A["Chọn trang đủ điều kiện<br/>(chia theo tập có sẵn)"] --> B["Subagent đọc chunk gốc<br/>viết timeline vàng (JSON)"]
    B --> C["Mã kiểm: quote, ngày, thứ tự, trùng"]
    C --> D["Mã sinh câu hỏi và đáp án từ mẫu"]
    D --> E["Viết lại cho khó<br/>(độ trùng từ khóa 0.1 đến 0.2)"]
    E --> F["Kiểm lần cuối bằng mã + đọc tay nhóm nhỏ"]
    B -. "mẫu 10 đến 15 thực thể" .-> G["Mình viết độc lập<br/>đo độ trùng sự kiện"]
```

- **Subagent chỉ viết timeline**, không biết câu hỏi và không biết hệ nào được so. Câu hỏi sinh bằng mã rồi viết lại cho khó (cùng cách với bộ kiểm khả năng ở `eval/09`).
- **Mẫu thử trước khi nhân rộng:** 5 đến 10 thực thể, hai bên (mình và subagent) viết độc lập, đo: sự kiện cả hai cùng có / tổng, ngày khớp, sự kiện chỉ một bên có (đọc tay xem lỗi bên nào). Độ trùng thấp (ví dụ dưới 80%) nghĩa là tiêu chí "thế nào là một sự kiện" chưa rõ, phải sửa hướng dẫn trước.
- **Cỡ việc ước lượng:** trung bình khoảng 30 chunk một trang (5,995 chunk / 203 trang của tune), nên 3 đến 4 trang mỗi subagent (**ước lượng, chưa đo**); khoảng 30 subagent cho 115 trang. Thử 5 trang trước.
- Sự kiện bị bỏ sót là lỗi khó thấy nhất (đếm và liệt kê sai nếu timeline vàng thiếu): chỉ kiểm bằng mã không đủ, nên cần bước so hai bên.

## 3. Cấu trúc timeline vàng

```json
{
  "page_id": "/wiki/Nguyen_Van_A",
  "events": [
    {"id": "e2", "date": "1991", "grain": "year", "track": "affiliation", "label": "club",
     "text": "moved to club Y",
     "evidence": [
       {"chunk_id": "/wiki/Nguyen_Van_A#1", "role": "date",        "quote": "In 1991 he left X and moved"},
       {"chunk_id": "/wiki/Nguyen_Van_A#2", "role": "description", "quote": "to Y, where he stayed for seven seasons"}
     ]}
  ],
  "undated_mentions": ["became a coach (no date given)"]
}
```

(Ví dụ minh họa, tên và chunk bịa.)

| Trường | Ý nghĩa |
|---|---|
| `id` | Nhãn sự kiện **trong trang đó**; khóa toàn cục là `page_id` + `id`. Mã gán sau khi sắp theo ngày; hòa ngày thì đánh dấu |
| `date` | Ngày ISO đúng mức độ văn bản nêu, không bổ sung |
| `grain` | `year`, `month` hoặc `day`; dùng để biết cặp nào so thứ tự được (cùng mức mịn và trùng thì "hòa", loại khỏi câu thứ tự) |
| `track` | Nhóm chủ đề của sự kiện (mục 4) |
| `label` | Nhãn tự do ngắn, tùy chọn; bắt buộc khi `track` là `other` |
| `text` | Mô tả ngắn bằng tiếng Anh, khoảng 10 từ; dùng chấm độ phủ khi câu trả lời là tóm tắt |
| `evidence` | Danh sách chunk chứa bằng chứng |
| `evidence[].role` | `both`: chunk tự có cả ngày và mô tả; `date`: chỉ có ngày; `description`: chỉ có phần mô tả (và không chứa ngày của sự kiện đó) |
| `evidence[].quote` | Trích nguyên văn, phải nằm đúng trong `chunk_id` đi kèm |
| `undated_mentions` | Sự kiện có nhắc nhưng không có ngày; dùng cho nhóm "không đủ thông tin" |

**Gold chunk tối thiểu của một sự kiện** là một chunk `both`, hoặc một cặp `date` + `description`. Nếu nhiều chunk `both` cùng nêu một sự kiện thì chỉ cần một (lựa chọn "hoặc"). Gold chunk của một câu là hợp các nhóm tối thiểu của những sự kiện câu đó dùng; một chunk có thể thuộc nhiều sự kiện, và khi hợp tập thì chỉ tính một lần.

**Ba tình huống một sự kiện trải nhiều chunk:** (1) ngày ở chunk này, mô tả ở chunk sau; (2) mốc bắt đầu và kết thúc ở hai chunk khác nhau; (3) cùng sự kiện nhắc ở hai chunk (tóm tắt rồi chi tiết), ghi một sự kiện nhiều chunk, không đếm hai lần.

**Hai cách chấm khai trước, báo cả hai:** *hit* (có ít nhất một chunk vàng trong kết quả) và *recall* (tỉ lệ chunk vàng tối thiểu có trong kết quả, lựa chọn "hoặc" tính một trong hai).

**Mã kiểm:** `chunk_id` tồn tại; `quote` có nguyên văn trong chunk và chứa ngày (với `date`/`both`); `description` không chứa ngày; sắp theo ngày đúng thứ tự; không trùng sự kiện; trang phải có ≥4 sự kiện trải ≥2 chunk.

## 4. Khung track

Khung dưới dựa trên 64 quan hệ Wikidata của 1,394 câu `real` (tune, valid, test_clean); nhãn quan hệ gán theo trí nhớ về Wikidata, chưa đối chiếu từng mã (không chắc: P4791, P2962, P8047, P559). Tỉ lệ là trước khi gộp.

| Track | Gồm | Ghi chú |
|---|---|---|
| `role` | chức vụ, nhiệm kỳ, người đứng đầu, quân hàm và chỉ huy (nhãn phụ `military`) | trước gộp: role 20.5% + military 9.5% |
| `affiliation` | nơi làm việc, đội, đảng, tổ chức, giải đấu | 18.7% |
| `location` | nơi ở, nơi làm việc, trụ sở, quốc gia | 13.8% |
| `ownership_structure` | sở hữu, vận hành, công ty mẹ, nhà xuất bản, hãng đĩa | 13.6% |
| `work` | **sản phẩm** người đó làm ra (phát hành, trình diễn, dự án) | 11.8% |
| `naming` | tên chính thức, đổi tên | 5.8% |
| `family` | vợ/chồng | 2.5% |
| `education` | học tại | 1.6% |
| `other` | còn lại, bắt buộc kèm `label` | giải thưởng/di sản (2.2%) vào đây hoặc nhóm riêng nếu cần |

- **Phân biệt dễ nhầm:** `work` là sản phẩm; `role` là vị trí giữ ("đạo diễn phim X" là `work`, "giám đốc hãng phim Y" là `role`). Mơ hồ thì ưu tiên `role` > `affiliation` > `work`.
- **Lối thoát:** `label` tự do cho `other`; sau mẫu thử, nếu một `label` chiếm hơn 5% sự kiện thì thành track mới (ngưỡng khai trước).
- Khung khai **trước** khi viết, không sửa theo kết quả. Sau mẫu thử đo tỉ lệ hai bên gán `track` khác nhau trên cùng sự kiện (vì vẫn có nhầm).
- Một trang chỉ có các track nó thực sự có (≥3 sự kiện mỗi track). Sinh và mất thường không thành track.

## 5. Dùng tiêu đề mục để gợi ý track

- `dataset/full_dataset/pages.jsonl`: mỗi trang có `paragraphs` gồm `{title, text}`; `title` là **tên mục** (ví dụ "Early life", "Club career", "Honors and awards"). Trên 127,233 đoạn chỉ 8.9% có tiêu đề trùng tên trang; 4,796 / 4,815 trang có ít nhất một tiêu đề mục.
- `src/tam/ingestion/chunking.py` đã đặt văn bản chunk dạng `"<tên trang> | <tên mục>\n..."`, nên tiêu đề mục đã nằm trong embedding và BM25.
- **Cách dùng:** đưa `title` của mục vào đầu vào của subagent làm gợi ý, và dùng làm kiểm chéo (`track` subagent gán nên khớp nhóm tiêu đề, lệch nhiều thì xem lại). **Không** dùng tiêu đề làm nhãn duy nhất: "History", "Career" chứa nhiều track; có tiêu đề là câu trích dẫn ("Nemtsov said :") do tách đoạn lỗi.
- **Điều cần kiểm lại:** docstring của `chunk_document` ghi "mỗi section thành một chunk", nhưng dữ liệu cho thấy trang Boris Nemtsov có 100 chunk (trung bình khoảng 377 ký tự) và một mục dài bị cắt thành nhiều chunk cùng tiêu đề; chưa kiểm nguyên nhân. Đây cũng là nguồn của tình huống "sự kiện trải nhiều chunk". Chưa kiểm chunk có chồng lấn (overlap) hay không.
- **Cho truy vấn:** lưu `section_title` thành trường payload để lọc hoặc tăng điểm theo track là phương án rẻ nhất (không cần LLM phân loại), nhưng payload hiện chỉ index 4 trường theo thiết kế nên thêm trường là thay đổi thiết kế; chưa nên làm khi chưa có chứng cứ. Cách chọn track lúc truy vấn (cạnh có kiểu hay chỉ thực thể và thời gian) thuộc thiết kế Cơ chế 2, không bị khung track của bộ dữ liệu áp đặt.

## 6. Loại câu hỏi

Quy tắc loại câu: **đáp án phải dùng ≥2 sự kiện** của timeline (nếu một lọc theo mốc lấy được một sự kiện thì đó là Cơ chế 1). Ví dụ "Which club did A join in 1991?" là Cơ chế 1, **không** đưa vào.

| Loại | Gold chunk |
|---|---|
| Liệt kê, đếm | các chunk của mọi sự kiện trong track |
| Thứ tự, khoảng cách | chunk của hai sự kiện |
| Đầu / cuối / kế tiếp | khai trước: tính cả chuỗi (để biết là đầu/cuối), không chỉ chunk chứa đáp án |
| Tóm tắt | chấm bằng độ phủ sự kiện (khớp `text`/`date`), không cần LLM judge (chưa chốt) |
| Không đủ thông tin (nhóm riêng) | sự kiện có `undated_mentions`, hoặc cặp trùng độ mịn, hoặc "sau sự kiện cuối". Đáp án đúng là "kho không nêu" chứ không phải "không có"; khoảng 10 câu mỗi tập; chấm riêng: tỉ lệ từ chối đúng và tỉ lệ bịa đáp án; đọc tay từng câu |

- **Bỏ nhóm `t_now`** (khoảng cách đến hiện tại, "N năm qua"): thuộc tính hạn và hiện tại của Cơ chế 1, không phải gom sự kiện (người dùng quyết 2026-11-04).
- Câu chéo track (ví dụ "lúc chuyển đội Y thì ông ở đâu") để sau, chưa làm đợt đầu.
- Mỗi trang không đều số track, nên "8 đến 9 câu mỗi thực thể" chỉ là trung bình; báo cáo ghi số trang thực dùng.

## 7. So sánh hệ

1. Vector top-k (cấu hình X của `eval/09`), LLM gom sự kiện từ chunk trả về.
2. Oracle đồ thị: đưa timeline vàng vào, đo trần.
3. Đồ thị trích bằng LLM (hệ thật).
4. Nếu còn thời gian: tái hiện DyG-RAG hoặc TG-RAG, chỉ khi (1) và (2) cho thấy còn chỗ để hơn.

Go/no-go: so (2) với (1); oracle không hơn vector top-k rõ rệt thì Cơ chế 2 không có lý do tồn tại ở bộ này.

## 8. Điểm yếu cần ghi nhận

- Một tác giả (mình) ra quy tắc, và model viết timeline cùng họ với mình: giảm bằng mẫu hai bên viết độc lập và, nếu muốn độc lập hơn, một mẫu kiểm bằng model khác họ (ví dụ Gemini).
- Không có số công bố để đặt cạnh, nên chỉ nói "hơn baseline của chính mình trên bộ này".
- Nhỏ và chỉ trong miền Wikipedia.
- Chấm tóm tắt bằng độ phủ sự kiện đo "đủ chưa", không đo văn phong.
- ECT-QA và TLQA có thể chạy một lần làm kiểm tra tổng quát hóa phụ, không dùng để chọn (chưa quyết).

## 9. Quyết định chưa chốt

1. Cỡ bộ (300/300/400 hay nhỏ hơn) sau khi đếm bước 0 bằng văn bản đầy đủ.
2. Có chạy ECT-QA làm kiểm tra phụ không.
3. Tóm tắt chỉ chấm bằng độ phủ sự kiện hay thêm LLM judge.
4. Khung track cuối cùng (gộp `military` vào `role`; xử lý giải thưởng).

## 10. Mẫu thử viết timeline (2026-11-04)

Mới làm **bước viết và kiểm timeline vàng**; chưa sinh câu hỏi, chưa chạy hệ nào. Dữ liệu lưu ở `dataset/eval/timeline_pilot/` (xem mục 10.5).

### 10.1 Mẫu 5 trang: mình và subagent haiku viết độc lập

Trang lấy từ tập `tune` (ngẫu nhiên trong các trang 12 đến 25 chunk có ít nhất 12 năm khác nhau, rồi chọn lại cho đa dạng): Mike Bongiorno, Great Tower Neuwerk, World Union for Progressive Judaism, Derek Barton, Ernst Hechler. Hai bên dùng chung `GUIDE_v1.md`; mình viết trước khi xem kết quả subagent; mỗi trang một subagent haiku, được dặn không đọc thư mục của mình (log truy cập: 0 lần).

Khớp sự kiện = cùng `date` và có chung ít nhất một `chunk_id` bằng chứng (nên **chưa đo** được chuyện hai bên ghi lệch ngày cho cùng sự kiện).

| Trang | Mình | Subagent | Khớp | `track` giống nhau |
|---|---|---|---|---|
| Derek Barton | 47 | 47 | 47 | 47/47 |
| Great Tower Neuwerk | 27 | 29 | 27 | 13/27 |
| Mike Bongiorno | 68 | 69 | 68 | 65/68 |
| World Union (WUPJ) | 34 | 34 | 33 | 32/33 |
| Ernst Hechler | 60 | 60 | 57 | 34/57 |
| **Tổng** | 236 | 239 | 232 | 191/232 (82%) |

- Mức sự kiện: 232/236 (mình) và 232/239 (subagent) khớp. `chunk_id` sai: 0; `quote` không nguyên văn: 1.
- Các chỗ lệch, đọc tay: mình sai 3 (ghi trùng một sự kiện, gộp hai huy hiệu cùng ngày, sót Iron Cross 1939); subagent sai 1 rõ (ghi một số đo, cường độ sáng 1952, thành sự kiện) và 1 điểm gây tranh cãi (một kế hoạch chưa xảy ra). Còn lại là cách tách hay gộp sự kiện khác nhau.
- `track` lệch 18%, chủ yếu `work` với `other` (công trình) và các sự kiện quân sự; ba trang còn lại khớp cao. Khung `track` còn mơ hồ.
- Giới hạn: hai bên dùng chung hướng dẫn, subagent cùng họ model với mình, chỉ 5 trang.
- Kết luận: hai bên bỏ sót khác nhau, nên một bên viết và bên kia soát lại tốt hơn mỗi bên một mình; haiku đủ dùng để viết bản nháp.

### 10.2 Mẫu 10 trang: subagent viết, mã kiểm, mình đọc đối chiếu

Quy trình: (1) subagent haiku viết theo `GUIDE_v2.md` (đã thêm quy tắc: ngày mốc thập kỷ không vào `events`, khoảng thời gian tách hai sự kiện, không ghi số đo/kế hoạch/bối cảnh, nguồn mâu thuẫn thì gắn cờ); (2) `check.py` kiểm tự động; (3) mình đọc từng trang cạnh chunk gốc (`view.py`) và sửa vào bản `rev/`; bản gốc của subagent giữ ở `sub/`.

Trang: Carl August Ehrensvärd, John Henry Whitley, Real Audiencia of Guatemala, Regius Professor of Civil Law (Oxford), Butch Levy, Frederick Ralph Sharp, Telekids, Seibu Shinjuku Line, Malvik, Southern Military District.

| | Số lượng | Mã kiểm bắt được |
|---|---|---|
| Sự kiện subagent viết | 289 | |
| Sai bằng chứng hoặc ngày | 7 | 6/7 |
| Không phải sự kiện của thực thể (thống kê, trùng) | 3 | 0/3 |
| Sót sự kiện rõ ràng | 12 | 0/12 |
| Sau khi sửa (bản `rev/`) | 301 | 0 lỗi thật |

- Lỗi sai và thừa: 10/289 (khoảng 3.5%). Sót rõ ràng: 12 (khoảng 4% trên tổng số thật). **Mã kiểm không bắt được lỗi sót nào**, nên bước đọc đối chiếu là bắt buộc.
- Ba trang không cần sửa: Malvik, Seibu Shinjuku Line, Frederick Ralph Sharp (ít sự kiện, cấu trúc đơn giản).
- Lỗi hay gặp của haiku: ghi thống kê theo mùa thành sự kiện; gắn bằng chứng từ chunk nói ngày khác; gán mốc "mùa 1941-42" thành năm 1941; bỏ sót sự kiện ở cuối trang.
- `undated_mentions` của haiku lẫn mô tả chung và mục thực ra có ngày ở chỗ khác; đã dọn (bỏ 11 mục). Còn lại: danh sách huân chương không ngày, mốc thập kỷ, sự kiện không nêu năm.
- Chi phí đọc của mình: chưa đo token; ước chừng mỗi trang 4 đến 10 nghìn token, nên 115 trang cần khoảng 600 đến 800 nghìn token (chia nhiều phiên, ước lượng).
- Chưa biết tỉ lệ lỗi còn lại sau khi mình đọc, vì chưa có người thứ ba (hoặc model khác họ) soát lại.

### 10.3 Quyết định về phạm vi "sự kiện" (người dùng chốt 2026-11-04)

- **Không ghi:** ngày của sắc lệnh hoặc luật chỉ được liệt kê mà không nêu thay đổi gì; ngày sinh con cái (timeline phải về chuỗi thời gian của chính thực thể); tiểu sử cá nhân của người được nhắc trong trang của một chức vụ hoặc tổ chức (chỉ ghi mốc nhậm chức và rời chức); thống kê theo mùa hoặc năm; số đo, kế hoạch chưa xảy ra, bối cảnh của thực thể khác; mốc theo thập kỷ hoặc thế kỷ (vào `undated_mentions`).
- **Ghi:** khoảng thời gian dùng huy hiệu hoặc biểu tượng (hai sự kiện bắt đầu và kết thúc); sự kiện của thực thể tiền thân và các chỉ huy của nó khi trang liệt kê chung.
- Nguồn tự mâu thuẫn: giữ từng mục và gắn `"flag": "source_inconsistent"`; loại các sự kiện đó khỏi câu thứ tự hoặc khoảng cách liên quan.
- `undated_mentions` chỉ chứa sự kiện của thực thể mà văn bản nhắc nhưng không nêu ngày; nếu ngày suy ra được hoặc có ở chỗ khác thì bỏ khỏi danh sách.
- Hai quy tắc đầu (sắc lệnh, con cái) đã được áp lên bản `rev/` của 10 trang; hướng dẫn `GUIDE_v2.md` đã ghi thêm mục "Quyết định bổ sung".

### 10.4 Việc còn lại trước khi nhân rộng

1. Chốt khung `track` (đang lệch 18% giữa hai bên; hoặc không để câu hỏi phụ thuộc `track`).
2. Một lượt soát độc lập (model khác họ, ví dụ Gemini) trên một phần mẫu để ước tỉ lệ lỗi còn lại.
3. Mã kiểm bắt được sai bằng chứng nhưng không bắt được sót: giữ bước đọc đối chiếu cho toàn bộ trang, chia theo lô khoảng 10 đến 15 trang.
4. Sinh câu hỏi từ các timeline đã kiểm và đọc tay mẫu câu hỏi.

### 10.5b Đợt 2: 10 trang nữa (2026-11-04)

Cùng quy trình (haiku viết, mã kiểm, mình đọc đối chiếu từng trang), `GUIDE_v3.md` giữ nguyên nội dung v2. Trang chọn từ `tune` (76 ứng viên còn lại, `random.seed(2027)`): Aero Union, August Maus, CS Aerostar Bacău, First Air Group, Klemzig (South Australia), Lev Polugaevsky, Martín de Gurrea y Aragón, Quelli che… il Calcio, Thomas Fearnley, Toungoo dynasty.

| Chỉ số | Giá trị |
|---|---|
| Sự kiện haiku viết | 242 |
| Sau khi mình sửa (`batch2/rev/`) | 239 |
| Sai hoặc thừa (đã bỏ hoặc sửa) | 22 (9%); 16 trong số đó là các chuyến tàu của Klemzig (không phải sự kiện của thực thể, chính subagent đã tự ghi chú) |
| Sót (đã thêm) | 18 |
| Mã kiểm báo | 8 lỗi: 1 sự kiện sai thật (CS Aerostar, mốc theo mùa), 1 quote không nguyên văn (Lev), 6 báo nhầm do năm viết tắt ("1984–85", "1830–32") |
| Mã kiểm bắt được lỗi sai nội dung | 1/22; sót: 0/18 |

Lỗi mới thấy ở đợt này: haiku ghi cả đánh giá ("extraordinary four-year period") thành sự kiện; ghi nhầm mốc khai mạc giải thưởng ("Iron Cross (1939)", "U-boat War Badge (1939)") thành ngày trao; ghi mốc theo mùa giải ("1993–94") thành một năm; bỏ sót các mốc suy ra được ("the following year", "that August").

**Quy ước mới do mình đặt (chờ người dùng xác nhận):** sự kiện có mốc suy ra được từ câu tương đối ("the following year", "that September") hoặc từ năm viết tắt ("1984–85" kết thúc mùa giải = 1985) được ghi thành sự kiện với `"flag": "derived_date"`. Mã kiểm bỏ qua điều kiện "quote chứa năm" cho các sự kiện này. 12 sự kiện thêm mới và 6 sự kiện cũ mang cờ này. Nếu không muốn dùng, lọc theo cờ.

Chưa kiểm độc lập: cũng như đợt 1, chỉ mình đọc một lượt.

### 10.5c Đợt 3: 10 trang nữa (2026-11-04)

Cùng quy trình; hướng dẫn `GUIDE_v4.md` = v3 + quy ước `derived_date`, bỏ sự kiện của vật mang (tàu, máy bay), bỏ câu đánh giá, năm ở tiêu đề giải thưởng và mốc theo mùa. Trang chọn từ `tune` (66 ứng viên còn lại, `random.seed(2028)`): 2AM (band), Albuquerque Dukes, Breitscheidplatz, David Young (Iowa), D. R. Shackleton Bailey, Fulk (King of Jerusalem), Garnidelia, Lower Norrland Military District, Michael Batty, Vindobona (train).

| Chỉ số | Giá trị |
|---|---|
| Sự kiện haiku viết | 323 |
| Sau khi mình sửa (`batch3/rev/`) | 333 |
| Sai hoặc thừa (đã bỏ) | 10 (3%) |
| Sót (đã thêm) | 20 (6%) |
| Mã kiểm báo | 1 lỗi, báo nhầm (năm viết tắt "1965–70"); bắt sai nội dung 0/10, sót 0/20 |
| Cờ trong `rev/` | 16 `derived_date`, 7 `approximate_date`, 2 `source_inconsistent` |

Lỗi sai/thừa: 4 mục "chủ chức vụ không rõ" (Lower Norrland, khoảng trống trong danh sách); 3 ở Vindobona (bối cảnh Czechoslovakia sau 1969, tuyến EuroCity khác, và một ngày sai: tên "Vindobona" dùng lại cho Railjet sau 12/2018, haiku gán 2014-12-14); 2 ở Michael Batty (giải thưởng "2017-2018" bị tách thành "bắt đầu/kết thúc kỳ", chuyển sang undated); 1 ở Albuquerque (tiểu sử một cầu thủ). Ngoài ra sửa cờ: gỡ `derived_date` khi năm có ghi rõ; thêm `approximate_date` cho mốc "c.", "1118 or 1119", "by 1928", "after 1916", "by 1994".

Sót chủ yếu: nhập ngũ và thông báo nhập ngũ (2AM, 3 mục cuối đoạn), các tour/concert trong danh sách (2AM), mốc cuối đoạn của trang địa danh (1895, 1916, 1928, 1930-04-01, 1961 ở Breitscheidplatz), các phiếu bầu/tuyên bố trong chuỗi mục chính trị (David Young, 3 mục), loạt xuất bản có năm bắt đầu và kết thúc (Shackleton Bailey: OCT 1958–1982). Tỉ lệ sai gần mức đợt 1b, thấp hơn đợt 2 vì không có trang nào nhiều sự kiện của vật mang.

Chưa kiểm độc lập: chỉ mình đọc một lượt.

### 10.5d Quyết định về phạm vi trang (2026-11-04, người dùng)

Mỗi bộ (`tune`, `valid`, `test_clean`) chỉ gồm các trang nó đang có: viết timeline vàng cho **toàn bộ** trang của bộ đó, rồi chỉ sinh câu hỏi từ các trang ấy. Không còn mục tiêu 35/35/45 thực thể cố định; cỡ bộ là số trang thực có (các số 300/300/400 câu ở mục 1 đến 9 chỉ còn là tham khảo).

Số liệu lúc ghi (đếm từ `dataset/eval/tune_subset.json`): `tune` có 203 trang; đã dùng 35 (30 có timeline vàng ở `pilot10/`, `batch2/`, `batch3/`, 5 trang `pilot5/` chỉ để so sánh); còn 168 trang chưa làm, tổng 5383 chunk không rỗng (trung vị 26, tối đa 100, nhỏ nhất 5); 85 trang dài hơn 25 chunk, 10 trang ngắn hơn 10. Ba mẫu thử trước chỉ chọn trang 10 đến 25 chunk nên chưa có kinh nghiệm với trang dài: cần quyết cách chia trang dài cho subagent (mỗi subagent một đoạn chunk, hay giới hạn chunk).

### 10.5e Đợt 4: 10 trang dài (26 đến 45 chunk, 2026-11-04)

Mục đích: thử haiku trên trang dài, vì 168 trang `tune` còn lại có 85 trang dài hơn 25 chunk. Mỗi subagent vẫn nhận nguyên một trang (không chia đoạn). Chọn ngẫu nhiên (`random.seed(2029)`) trong 54 trang `tune` chưa dùng có 26 đến 50 chunk không rỗng.

| | Số |
|---|---|
| Haiku viết (`batch4/sub/`) | 386 |
| Sai hoặc thừa (đã bỏ hoặc sửa nội dung) | 13 (3,4%) |
| Bỏ theo quy ước mới (mốc kết thúc của giải đấu) | 12 |
| Sót, đã thêm | 6 (1,6%) |
| Sau khi mình sửa (`batch4/rev/`) | 367 |
| Mã kiểm bắt được lỗi nội dung | 0/13 sai, 0/6 sót; 3 báo (2 báo nhầm, 1 quote ghép hai chỗ ở TU Leuna) |

Kết luận: haiku làm trang dài không tệ hơn trang vừa (sai/thừa 3,4% so với 3%, sót 1,6% so với 6%), nên chưa cần chia đoạn; cách đọc kiểm vẫn cần vì mã kiểm không bắt được lỗi nội dung. Lỗi hay gặp: gắn cờ `derived_date` cho ngày đã ghi rõ (5 chỗ), ghi phát biểu/bài báo/phim về thực thể thành sự kiện của nó (Monir: sách, phim, phỏng vấn; Meet the Press: chuyện lặt vặt về người dẫn), gộp số liệu thành sự kiện (tuyển 15 cầu thủ, mua cổ phần chung chung), sót mốc ở chỗ nằm sâu (hỏa hoạn 2014 ở đoạn cuối, chồng mất 1991).

Quy ước mình tự đặt thêm (chờ người dùng xác nhận): khoảng thời gian của một giải đấu mà thực thể tham dự (ví dụ "21 February to 1 March") ghi MỘT sự kiện ở ngày bắt đầu, không tách hai mốc, vì tham dự một giải không phải trạng thái bắt đầu và kết thúc (Blübaum bỏ 11 mốc "ended"). Nguyên tắc tách hai mốc vẫn giữ cho chức vụ, thời gian đảm nhiệm, giai đoạn dùng huy hiệu.

### 10.5f Đợt 5: 10 trang, có 2 trang rất dài (61 và 63 chunk, 2026-11-04)

Chọn ngẫu nhiên (`random.seed(2029)`) trong 158 trang `tune` chưa dùng: 8 trang 13 đến 41 chunk và 2 trang trên 45 chunk (The One Show, The Dark Eye) để thử giới hạn của việc đưa nguyên trang cho một subagent.

| | Số |
|---|---|
| Haiku viết (`batch5/sub/`) | 219 |
| Sai hoặc thừa (đã bỏ) | 8 (3,7%) |
| Sót, đã thêm | 7 (3,2%) |
| Sửa cờ hoặc nội dung chữ (không đổi số sự kiện) | 11 (cờ `derived_date` sai, thiếu `approximate_date`, ghi "unnamed" dù nguồn có tên) |
| Sau khi mình sửa (`batch5/rev/`) | 218 |
| Mã kiểm bắt được lỗi nội dung | 0/8 sai, 0/7 sót; 2 báo do mình thêm sự kiện thiếu năm trong quote |

Kết luận: hai trang 61 và 63 chunk không tệ hơn trang ngắn (The One Show: 51 sự kiện, thừa 2, sót 2; The Dark Eye: 27 sự kiện, chỉ thiếu 2 cờ), nên chưa cần chia đoạn dù dài trên 45 chunk. Trang còn lại tối đa 100 chunk vẫn chưa thử.

Lỗi mới thấy: bỏ qua tên người ngay trong câu nguồn (Agenzia: "Unnamed person" trong khi câu có "Giovanni Giovannini"), sót vai trò đi kèm một mốc đã ghi (Cavada là người dẫn đầu tiên ngày 6/1/1975; Antenne 2 đổi tên France 2 cùng ngày với việc giao Paul Amar), sót chương trình mới thêm (20h30 le dimanche), ghi mốc theo kế hoạch (hợp đồng AP 2015 đến 2020), ghi sự kiện một lần của khách (Ronan Keating dẫn một tập).

Quy ước mình tự đặt thêm (chờ người dùng xác nhận): (1) danh sách khách mời theo từng tập (Allsång på Skansen, 36 chunk) không ghi thành sự kiện, vì là liệt kê chứ không phải thay đổi của thực thể; (2) khoảng ngày của một chiến dịch quân sự thực thể tham gia (USS LCS, Gunto 18 đến 30 tháng 6) = MỘT sự kiện ở ngày bắt đầu, cùng nguyên tắc với giải đấu ở 10.5e; (3) mốc chỉ nêu như kế hoạch trong nguồn (thời hạn hợp đồng 2015 đến 2020) không ghi; (4) bài/ý kiến chỉ trích VỀ chương trình (Actuchomage, Bruno Masure) không ghi, nhưng sự cố xảy ra TRONG chương trình (báo động cháy, khiếu nại sau một lời nói trên sóng) vẫn ghi; (5) khi hai nơi trong cùng trang mâu thuẫn mà không rõ bên nào đúng (Chris Evans bắt đầu dẫn thứ Sáu tháng 8 năm 2010 hay "đầu 2011") thì gắn `source_inconsistent` cho mốc không nằm trong danh sách chính.

### 10.5g Đợt 6: 10 trang, có 3 trang 54 đến 72 chunk (2026-11-04)

Chọn ngẫu nhiên (`random.seed(2030)`) trong 148 trang `tune` chưa dùng: 7 trang 19 đến 41 chunk, 2 trang 54 và 62 chunk (D band, Jacqueline Cochran), 1 trang 72 chunk (Eliot Engel). Haiku dùng `GUIDE_v4.md` (chưa có các quy ước của 10.5f).

| | Số |
|---|---|
| Haiku viết (`batch6/sub/`) | 458 |
| Bỏ (`batch6/rev/`) | 90 |
| Sót, đã thêm | 8 (1,7%) |
| Sau khi mình sửa | 376 |
| Mã kiểm bắt được lỗi nội dung | 0/90 bỏ, 0/8 sót; 4 báo ở D band (2 quote không nguyên văn, 2 do cặp `date`+`description`) |

90 mốc bị bỏ tách theo lý do, vì phần lớn không phải haiku sai mà là quy ước chưa nằm trong hướng dẫn:

| Lý do | Số |
|---|---|
| Danh sách khách mời/giám khảo theo từng tập (Minuta slavy, 47 trong 54 mốc) | 47 |
| Tách hai mốc cho một khoảng tham gia (tour, đợt record, chiến dịch) nên gộp một mốc | 8 |
| Phát biểu, phỏng vấn, thư ngỏ, bài báo, kêu gọi của chính thực thể | 8 |
| Tưởng niệm và vinh danh sau khi mất (tem, đài, tên hố thiên thạch, đưa vào hall of fame) | 9 |
| Sự kiện của thực thể khác (luật Sixpack, Operation Midland đóng, cảnh sát bác chỉ trích) | 4 |
| Mơ hồ, trùng hoặc phụ (DFC "period ended", tiếp đón một khách trên YouTube, xếp hạng Forbes, rating HRC, mốc theo mùa) | 14 |

Sót 8: ngày không có năm trong câu nhưng năm rõ từ câu trước (D band: EP New Blood 18/7/2003, hồi phục 27/9/2003, tạp chí 7/8/2005; hết hiatus giữa 2015), người huấn luyện qua đời (Alemannia 1999), sân Old Tivoli xây 1908, từ chức chủ tịch AWS (Buzek), phiếu chống luật miễn trách nhiệm hãng súng 2003 (Engel). Cờ sửa: 15 chỗ (`approximate_date` thiếu cho "early", "circa", "spring", "mid"; `derived_date` sai khi năm đã ghi rõ).

Kết luận: trang 54 đến 72 chunk không làm haiku tệ hơn, và nguồn sai lệch lớn nhất là hướng dẫn thiếu quy ước chứ không phải độ dài trang. Đã viết `GUIDE_v5.md` (trong `batch6/`) gộp các quy ước mới để đợt 7 dùng; số bỏ ở đợt 7 là phép thử xem hướng dẫn mới có giảm lỗi không. Đã đọc đủ 10 trang, chưa đo trang 73 đến 100 chunk.

Quy ước mới này đều do mình đặt, chờ người dùng xác nhận (thêm vào 5 quy ước ở 10.5f): (6) phát biểu, phỏng vấn, bài báo của chính thực thể không ghi; chỉ ghi hành vi chính thức (bỏ phiếu, kiến nghị, thư gửi cơ quan, thông báo quyết định); (7) mốc tưởng niệm sau khi thực thể mất không ghi, vinh danh khi còn sống vẫn ghi; (8) khoảng tham gia của một hoạt động (tour, đợt record) là MỘT mốc ở ngày bắt đầu.

### 10.5h Đợt 7: 10 trang dùng `GUIDE_v5.md`, có Hanover 100 chunk (2026-11-04)

Chọn ngẫu nhiên (`random.seed(2031)`) trong 138 trang `tune` chưa dùng: 7 trang 9 đến 44 chunk, 2 trang 57 và 58 chunk (British Rail Class 40, Veliky Novgorod), 1 trang 100 chunk (Hanover). Đây là đợt đầu haiku đọc `GUIDE_v5.md` (có các quy ước của 10.5f và 10.5g).

| | Số |
|---|---|
| Haiku viết (`batch7/sub/`) | 260 |
| Bỏ | 28 (10,8%) |
| Sót, đã thêm | 13 (5,0%) |
| Sau khi mình sửa (`batch7/rev/`) | 245 |
| Mã kiểm bắt được lỗi nội dung | 0/28 bỏ, 0/13 sót; 16 báo, đều là lỗi quote/chunk hoặc năm dưới 1000 (sửa `check.py` bỏ số 0 đầu của năm như "0859") |

Lý do bỏ 28: sự cố của từng đầu máy trong trang về một lớp đầu máy (13, đều là sự kiện của vật mang), 4 lễ hội/cuộc thi định kỳ tổ chức trong thành phố (Hanover), 4 mốc "tên không nêu" bị lặp ở danh sách chủ tịch mất tên, 7 trùng, vụn hoặc không có ngày. Sót 13, trong đó 8 ở Veliky Novgorod (trang 58 chunk) toàn ở giữa trang (trạm buôn Visby 1080, đặc quyền thương nhân Đức 1229, trận Neva 1240, trận trên băng 1242, đóng kontor Hanse 1494, trạm Đức dựng lại 1603, bảo tàng gỗ 1964, sân bay 2006), còn lại là vợ Leahy mất, Böhme rời vị trí, Expo 2000, Biedroń/ILGA 2013, chuyến tàu khách đầu tiên của Class 40 sau 16 năm.

Kết luận: các loại lỗi mà `GUIDE_v5.md` nhắm tới (danh sách khách mời, phát biểu của chính thực thể, mốc tưởng niệm sau khi mất) không xuất hiện lại trong đợt này, nhưng đợt này gồm loại trang khác (thành phố, loạt đầu máy, chương trình) nên chưa phải phép thử sạch. Lỗi mới thuộc ba loại hướng dẫn chưa có quy ước (sự cố từng chiếc trong trang về cả lớp, sự kiện định kỳ trong trang địa danh, tên người bị mất trong danh sách), đã viết thêm vào `batch7/GUIDE_v6.md`. Sót 13 mốc (5,0%) cao hơn đợt 6 (1,7%), nhưng 8 trong số đó nằm ở một trang 58 chunk, nên chưa đủ để kết luận về độ dài trang. Trang 100 chunk (Hanover) chỉ có 1 mốc sót, nên chưa thấy giới hạn trên. Đã đọc đủ 10 trang.

Quy ước mới này đều do mình đặt, chờ người dùng xác nhận (thêm vào 5 quy ước ở 10.5f và 3 quy ước ở 10.5g): (9) sự cố, hành trình của từng đầu máy hay tàu trong trang về cả lớp là sự kiện của vật mang, không ghi; (10) lễ hội, cuộc thi định kỳ trong trang về địa danh là sự kiện của thực thể khác, không ghi; (11) tên người bị mất trong danh sách thì ghi một mốc "đổi người (không tên)", không ghi cặp "bắt đầu/kết thúc" rỗng.

### 10.5i Đợt 8: 10 trang dùng `GUIDE_v6.md` (2026-11-04)

Chọn ngẫu nhiên (`random.seed(2032)`) trong 128 trang `tune` chưa dùng: 7 trang 15 đến 37 chunk, 2 trang 46 và 67 chunk (Ralph Lauren Corporation, Atlanta Dream), 1 trang 81 chunk (David Hasselhoff). Đây là đợt đầu haiku đọc `GUIDE_v6.md` (đủ 11 quy ước).

| | Số |
|---|---|
| Haiku viết (`batch8/sub/`) | 372 |
| Bỏ | 4 (1,1%) |
| Sót, đã thêm | 18 (4,8%) |
| Sau khi mình sửa (`batch8/rev/`) | 386 |
| Mã kiểm bắt được lỗi nội dung | 0/4 bỏ, 0/18 sót; 5 báo, đều là lỗi quote hoặc cờ (quote cắt cụt, năm lấy từ câu trước, cờ gộp "derived_date; source_inconsistent") |

Lý do bỏ 4: một lần tái phát hành phim đổi tên (Hasselhoff), một lần dự trận bóng rổ, một lời tuyên bố ủng hộ đội bóng (quy ước 6), một lời tố của người khác ("bị sa thải") ghi như sự kiện. Sót 18, phần lớn là mốc đơn ở giữa trang: Hasselhoff (rời Y&R 1982, thông báo vai trong The Producers 2006, Peter Pan 2010, 9 to 5 2019), Atlanta Dream (chuỗi 17 trận thua 2008, chủ cũ tuyên bố bán 2009, chuyển sang Gateway Center 2021), Ralph Lauren (thông báo thay CEO 2015-09, dòng American Living ngừng 2019), Mary Raine (đến Úc, chồng đầu mất 1918), St Luke (thay nhà xứ 1840, Macquarie dự lễ 1820), Fort Tilden (khẩu đội 90 mm 1951-54), Slade Gorton (trung tâm mang tên ông 2010, vợ mất 2013), Amalric (hủy hôn nhân khi lên ngôi).

Kết luận: không còn loại lỗi hệ thống của đợt 5–7 (khách mời, phát biểu của thực thể, mốc tưởng niệm, sự cố từng chiếc, lễ hội định kỳ, tên bị mất); lỗi còn lại là sót mốc đơn và vài chỗ cờ/quote. Tỉ lệ sót 4,8% gần đợt 7 (5,0%), nên 11 quy ước giảm bỏ nhầm (từ 10,8% xuống 1,1%) nhưng không giảm sót. Trang 81 chunk (119 mốc) vẫn chỉ sót 4. Đã đọc đủ 10 trang. Không có quy ước mới.

### 10.5j Đợt 9: 10 trang dùng `GUIDE_v6.md`, có Los Angeles Rams 100 chunk (2026-11-04)

Chọn ngẫu nhiên (`random.seed(2033)`) trong 118 trang `tune` chưa dùng: 7 trang 11 đến 39 chunk, 2 trang 55 và 68 chunk (The Late Late Show, Janet Frame), 1 trang 100 chunk (Los Angeles Rams).

| | Số |
|---|---|
| Haiku viết (`batch9/sub/`) | 335 |
| Bỏ | 18 (5,4%) |
| Sót, đã thêm | 9 (2,8%) |
| Sau khi mình sửa (`batch9/rev/`) | 326 |
| Mã kiểm bắt được lỗi nội dung | 0/18 bỏ, 0/9 sót, 0/1 sai ngày (xem dưới); 5 báo, đều là lỗi quote hoặc thiếu chunk ngày |

Lý do bỏ 18: 8 mốc sau khi Janet Frame mất (xuất bản di cảo, giải thưởng truy tặng; đúng tinh thần quy ước 7 nhưng quy ước chưa nói rõ "xuất bản sau khi mất"), 9 mốc ở Los Angeles Rams (7 kết quả playoff theo mùa, theo quy ước 8, đưa vào `undated_mentions`; biệt danh "Shams" của đội thay thế trong cuộc đình công; một mốc trùng với mốc vào Super Bowl), 1 mốc trùng ở BAMF (khoảng "bê bối 2000-2018" bị tách hai mốc, theo quy ước 2 chỉ giữ mốc đầu). Sót 9: Costa Allegra thuê cho Paquet Cruises 2010, Selvon bỏ học năm 15 tuổi, Late Late Show (thử giọng khách mời 2004, Lassally nghỉ 2015, ban nhạc nhà 2015), Rams (gia nhập AFL 1936, nghỉ mùa 1943, hội đồng Inglewood duyệt sân 2015, họp báo trở về LA 2016). Một lỗi sai ngày mà mã kiểm không bắt: haiku gắn vụ tự tử và buổi trị liệu của Janet Frame vào 1943 (năm bắt đầu học sư phạm) trong khi văn bản nói "later that year" của năm thực tập, tức 1945; đã sửa.

Kết luận: tỉ lệ sót 2,8% thấp nhất từ đợt 5, nhưng tỉ lệ bỏ 5,4% cao hơn đợt 8 (1,1%) do hai trang có khối mốc thuộc quy ước chưa viết (sau khi mất, kết quả playoff theo mùa). Trang 100 chunk (Rams, 81 mốc sau sửa) vẫn không tệ hơn rõ. Đã đọc đủ 10 trang. Quy ước mới do mình đặt, chờ xác nhận: (12) xuất bản di cảo và giải thưởng truy tặng sau khi thực thể mất không ghi (mở rộng quy ước 7). Chưa thêm vào guide; sẽ thêm vào `GUIDE_v7.md` nếu bạn đồng ý.

### 10.5k Session phụ B: thiết lập và kiểm B1, B2 (2026-11-04)

Để làm nhanh hơn, một session Claude khác (tài khoản khác, cùng máy và repo) làm song song các batch `batchB1`, `batchB2`, `batchB3`, ... Cách tránh trùng và va chạm:

- `reserved_B.json`: 53 trang `tune` dành riêng cho session B (chia theo cùng tỉ lệ độ dài, `random.seed(7001)`); session chính chọn trang ngoài danh sách này.
- `tools/mk_batch.py <batch> <seed> reserved_B.json`: chọn 10 trang chưa dùng trong danh sách, dựng `{in,sub,rev}`, chép `GUIDE_v6.md`. Seed của session B là 7100 + N.
- Session B chỉ ghi vào `batchB*/` (kèm `NOTES.md`) và `tools/patch_bB*.py`; không sửa file này. Thống kê gộp vào đây do session chính làm.

Kết quả session B tự báo (đã kiểm lại cấu trúc và đọc mẫu):

| | B1 | B2 | Cộng |
|---|---|---|---|
| Haiku viết | 229 | 538 | 767 |
| Bỏ | 3 (1,3%) | 16 (3,0%) | 19 (2,5%) |
| Sót, đã thêm | 11 (4,8%) | 19 (3,5%) | 30 (3,9%) |
| Sau sửa (`batchB*/rev/`) | 237 | 541 | 778 |

Mình kiểm độc lập: mã kiểm trên `rev/` 0 lỗi; quét cấu trúc 20 trang (778 mốc, đúng số session B báo): cờ chỉ thuộc ba giá trị hợp lệ, không trùng id, cấp độ ngày khớp, thứ tự đúng. Đã đọc kỹ 6 trang (President of Uruguay, Entropa, Real Madrid, Imperial College, Luftflotte 1, Humongous); không thấy lỗi nội dung. Chưa đọc 14 trang còn lại. Các tỉ lệ bỏ/sót là so với phán đoán của chính session B, không phải đo độc lập. Hai điểm lưu ý: Real Madrid giữ 55 mốc "thắng giải giao hữu" lấy từ danh sách (quyết định quy ước, nên nêu rõ trong `NOTES.md`); `tools/view.py` luôn đọc `sub/` dù đặt `DIR=rev` (chỉ `check.py` theo `DIR`).

Hai quy ước session B tự đặt, chờ người dùng xác nhận: (A) danh sách tác phẩm bị mất tên (12 game Humongous) không ghi mốc, chỉ một dòng `undated_mentions` (mình thấy còn tranh cãi vì mỗi mục có năm và tên series); (B) bản dịch có năm trong thư mục (Georges Duby) ghi như mốc `work`.

### 10.5l Kiểm B3, B4 của session phụ B (2026-11-04)

| | B3 | B4 | Cộng B3+B4 |
|---|---|---|---|
| Haiku viết | 319 | 321 | 640 |
| Bỏ | 0 | 1 | 1 |
| Sót, session B đã thêm | 20 | 34 | 54 |
| Sau sửa theo session B | 339 | 354 | 693 |
| Mình thêm sau khi đọc kiểm | 0 | 5 | 5 |
| Cuối cùng (`rev/`) | 339 | 359 | 698 |

Gộp bốn batch B: 40 trang, haiku 1407, session B sửa thành 1471, cộng 5 mốc mình thêm là 1476. Cả hai session: 130 trang, 4267 mốc (2791 + 1476).

Cách kiểm: `check.py` trên `rev/` 0 lỗi cả hai batch; quét cấu trúc (id liên tục, cờ hợp lệ, cấp độ ngày khớp, không trùng mốc) sạch. Đọc tay 9/20 trang: B3 (World Festival, Permanent Secretary, Irene Kharisma, Hugh Scott, Rush Holt), B4 (Counselor, Line 7, Luftflotte 5, Fleetwood). **11 trang chưa đọc**: Milton Friedman, Razorfish, Hsu, First Things, Stommel, Bohemond, Livingstone, Good Game, Oxenstierna, Masters, MMK.

Phát hiện khi đọc, mã kiểm không bắt được:
- Counselor_to_the_President: sót 3 mốc, đều có năm trong câu: Trump tuyên bố chọn Conway và Bannon sau bầu cử 2016 (`derived_date`), Bannon vào Principals Committee 2017-01, Trump đưa Bannon ra khỏi NSC 2017-04.
- Line_7: sót 2 mốc trong mục Timeline: 2008-01-08 tin báo chí về kế hoạch, 2009-07-19 thông báo khởi công cuối tháng 8.
- Sửa bằng `tools/fix_B34.py` (chạy sau `patch_bB4.py`), `check.py` 0 lỗi sau sửa.
- 7 trang còn lại trong số đã đọc (World Festival, Permanent Secretary, Irene, Rush Holt, Hugh Scott, Luftflotte 5, Fleetwood) đúng ngày, không thấy sai; nhận xét nhỏ: Luftflotte 5 `e13` ghi tên đơn vị mới nhưng bỏ "Lofoten thành Ff 5" ở `e12`; Hugh Scott không ghi "dọa ra tranh thống đốc 1962" (loại ủng hộ/đe dọa ứng viên theo quy ước C).

Tỷ lệ sót ở batch B3 là 6,3% và B4 là 10,6% so với haiku (do Livingstone, Good Game, Bohemond có khối liệt kê dài). Con số này là session B tự đếm; qua mẫu 9 trang mình đọc, mình thêm được 5 mốc sót mà session B chưa thấy, tức tỷ lệ sót thật cao hơn một chút so với con số tự báo.

Hai quy ước mới chờ người dùng xác nhận: (D) bài giảng có tên và năm trong danh sách distinctions ghi như mốc `other` (Livingstone, +11 mốc); (E) danh sách triển lãm bảo tàng giữ làm mốc `work` (MMK, khoảng 85 mốc). Còn (A), (B), (C) từ B2, B3 chưa được xác nhận.

### 10.5m Kiểm B5 và chuyển toàn bộ trang còn lại sang session B (2026-11-04)

B5 (10 trang): haiku 278, session B bỏ 3, thêm 33 (11,9% so với haiku), sau sửa 308. `check.py` trên `rev/` 0 lỗi, quét cấu trúc sạch. Mình đọc kỹ 3 trang ngắn (PEN America, Tyne and Wear PTE, C38) và soát cờ `derived_date` của Beugró, Goryachkina: không thấy sai ngày hay sót thêm; `derived_date` của Beugró (28 mốc) hợp lý vì năm lấy từ tiêu đề mục. **7 trang B5 chưa đọc kỹ**. Cả hai session: 140 trang, 4575 mốc (2791 + 1784).

Ba quy ước mới của session B chờ xác nhận: (F) ngày sinh/mất của con ghi là mốc `family`, ngày mất vợ/chồng chỉ ghi khi nhân vật còn sống; (G) rating và peak rating không ghi (thống kê), "lần đầu vào top 10" thì ghi; (H) IM/GM norm ghi là `other` theo năm.

Phân công: `reserved_B.json` mở rộng từ 53 lên 108 trang (bản cũ ở `reserved_B.before_all.json`), nên session B nhận cả 58 trang tune chưa dùng còn lại (khoảng 6 batch: B6 đến B11, seed 7106 trở đi). Session chính chỉ đọc kiểm.

### 10.5n Kiểm B6, B7 của session B (2026-11-04)

| | B6 | B7 |
|---|---|---|
| Haiku viết | 343 | 412 |
| Session B: bỏ / thêm | 4 / 9 | 0 / 16 |
| Sau sửa theo session B | 348 | 428 |
| Mình thêm/bớt sau khi đọc | 0 | +7 (CEU +3, Exxon +4, Mannheim +1, Pelican −1) |
| Cuối cùng (`rev/`) | 348 | 435 |

`check.py` trên `rev/` 0 lỗi cả hai batch; quét cấu trúc sạch. Mình đọc kỹ 12/30 trang của B5–B7 (B5: PEN America, Tyne and Wear, C38; B6: Line 15, Milan Metro Line 3, U-96 một phần; B7: Pelican, Westover, Exxon Valdez, CEU, Archaeologia Cambrensis, Mannheim). Phần còn lại chưa đọc kỹ: B5 bảy trang, B6 bảy trang, B7 bốn trang (Panufnik, Holden, Warrior, News Quiz).

Sửa bằng `tools/fix_B67.py` (chạy SAU `patch_bB7.py`, an toàn khi chạy lại):
- CEU (haiku 13/72 chunk, session B thêm 4): vẫn sót 3 mốc mã kiểm không bắt: đề luật 2017-03-28 nhắm vào CEU, biểu tình ủng hộ CEU 2017-04-02, Tòa Công lý EU phán Lex CEU trái luật EU 2020-10-06. Session B bỏ nhóm "luật 2017 của chính phủ" theo quy ước K, nhưng đề luật này là sự kiện trung tâm của trang nên mình thêm lại.
- Exxon Valdez: session B bỏ cả khối tố tụng; trang có 4 mốc rõ ràng (1994 bồi thẩm đoàn, 2008-06 Tòa tối cao, 2008-08-27 thỏa thuận, 2009-06 tiền lãi), mình thêm lại.
- Pelican: hai mốc "period began/ended" 1936 và 1938 cho một việc mua giữa 1936–1938; gộp thành một mốc `approximate_date` 1936.
- Mannheim: sót Astronomische Gesellschaft thành lập ngày 1863-08-28 (Schönfeld trong ban sáng lập).

Quy ước mới của session B chờ xác nhận: (I) tên tàu/vật bị mất trong nguồn thì không ghi mốc, chỉ một dòng `undated_mentions`; (J) mốc "revised" trong danh mục tác phẩm được giữ; (K) tuổi thọ cha mẹ và sự kiện của người khác không ghi. Nhận xét: (I) bỏ 4 mốc của U-96 (ví dụ "đánh chìm một tàu ngày 1941-01-16", ngày và hành động đều rõ), cùng loại tranh cãi với (A); (J) giữ 22 mốc "revised" riêng của Panufnik (cộng khoảng 17 chú thích trong mốc "composed"); (K) đã làm mất khối tố tụng của Exxon và đề luật 2017 của CEU nên cần giới hạn lại (chỉ loại sự kiện không liên quan thực thể).

Gộp: session B 70 trang, 2567 mốc; session chính 90 trang, 2791 mốc; cả hai 160 trang, 5358 mốc. Còn 38 trang tune chưa dùng (B8 đến B11).

### 10.5o Kiểm B8, B9 và chốt quy ước I–K (2026-11-04)

| | B8 | B9 |
|---|---|---|
| Haiku viết | 262 | 311 |
| Session B: thêm / bỏ | +37 / −1 | +30 / −1 |
| Sau sửa theo session B | 298 | 339 |
| Mình thêm sau khi đọc | +2 (Zambia) | 0 |
| Cuối cùng (`rev/`) | 300 | 339 |

`check.py` trên `rev/` 0 lỗi; quét cấu trúc sạch. Mình đọc 8 trang (Lenin Peak, Carrier Air Group 17, Marc Bohan, Milan Metro 2, Irina Levitina, Zambia, Gethard, Mercury News một phần) và dùng `tools/gap.py` (liệt kê câu có năm mà không mốc nào trích) cho Zambia, Mercury News, Simferopol, Sainz, Rull, Gethard, Ocon: chất lượng tốt hơn B7; chỉ thấy Zambia sót 2 mốc (Livingstone thấy thác Victoria 1855, Burnham tìm đồng 1895), thêm bằng `tools/fix_B89.py`. Các câu có năm còn lại ở Mercury News, Simferopol là số liệu, ranh giới hoặc việc của thực thể khác nên không thêm. Chưa đọc kỹ: Goldberg, Franklin, Downs, Arnulf, Volvo 9700 và vài trang khác.

Quy ước I, J, K đã áp dụng từ B8 (người dùng chọn đề nghị của mình), và mình sửa B6, B7 cho khớp trong `tools/fix_B67.py`: (I) khôi phục 2 mốc mất tên của U-96 (hai mốc còn lại bị bỏ trước đó trùng với mốc có tên nên không khôi phục); (J) xóa 22 mốc "revised" riêng của Panufnik, giữ chú thích "revised" trong mốc "composed"; (K) chỉ loại sự kiện của thực thể khác khi không nhắm vào thực thể của trang.

Quy ước mới của session B ở B8, B9, đã chọn: (L) ngày cưới và ngày mất của con ghi như `family` (cùng quy ước F); (M) giải thưởng từng năm trong danh sách ghi là `award`; (N) kết quả từng trận hoặc ván cờ không ghi, trừ khi đổi chức vô địch hoặc là mốc "lần đầu"; (O) sự kiện của thực thể khác (Maravi 1480, FC TSK 2014) không ghi, cùng giới hạn như K.

Gộp: session B 90 trang, 3186 mốc; session chính 90 trang, 2791 mốc; cả hai 180 trang, 5977 mốc. Còn 18 trang tune chưa dùng (B10 10 trang, B11 8 trang).

### 10.5p Kiểm B10, B11 và hết trang tune (2026-11-04)

B10 (10 trang): haiku 273, sau sửa 291. B11 (8 trang): haiku 103, sau sửa 104; B11 có 5 trang dưới 8 chunk nên `mk_batch.py` bỏ qua, session B dựng `in/` tay. Mình đối chiếu `in/` của cả 18 trang với `pages.jsonl`: đúng tập tune, chỉ số chunk và nội dung khớp 100%. `check.py` trên `rev/` 0 lỗi, quét cấu trúc sạch.

Mình đọc kỹ 7 trang B11 (Charlotte Fitch Roberts, Tyyni Tuulio, Yugoslavia Davis Cup, Casus Belli, Greenbelt, Lassalle, Sastamala) và chạy `gap.py` cho 11 trang còn lại của B10, B11. Thêm 3 mốc bằng `tools/fix_B1011.py`: Sastamala (hai mốc phê chuẩn huy hiệu 1962-11-26 và 1963-02-12, của thực thể tiền thân Karkku), Brian Higgins (đánh giá Best Lawmaker 1993). Phần `gap.py` còn lại là kết quả mùa giải (đã loại theo quy ước N), việc của người khác, hoặc số liệu. Chưa đọc kỹ: Keith Emerson, Lowell, Senate of Canada Building, Eastern Army Division, Karlsøy, Swedish Air Force Flying School, Werner Hartmann, Sarah Palfrey Cooke, Andrew Mellon, Sevilla FC, Brian Higgins (chỉ xem danh sách mốc).

Quy ước mới session B tự đặt ở B10, B11, đã chấp nhận: cụm "mid-1990s", "late 1960s" không có năm cụ thể để `undated_mentions`; hoạt động có "giữa X và Y" của một cơ quan đặt tại nơi nào đó ghi hai mốc đầu và cuối; "ký ủng hộ một luật" không ghi.

**Kết thúc viết timeline cho tập `tune` (203 trang):** 90 trang session chính (batch 2 đến 9 và pilot10), 108 trang session B (B1 đến B11) và 5 trang pilot5. Mốc: session chính 2791, session B 3584, tổng 6375 (chưa tính pilot5). Chất lượng chưa đồng đều: khoảng một nửa số trang chưa ai đọc kỹ từng mốc.

### 10.5q Bắt đầu timeline cho tập `valid` (2026-11-04)

Quy mô: `valid` có 167 trang (khoảng 5063 chunk: 131 trang 8–45 chunk, 21 trang 46–72, 12 trang từ 73, 3 trang dưới 8), ước 17 batch; `test_clean` có 186 trang (5682 chunk), ước 19 batch. Ba tập không trùng trang. `valid` dùng để chọn phương pháp, nên cần timeline trước khi sinh câu hỏi cho nó.

Công cụ: `reserved_valid.json` (167 trang), `GUIDE_v7.md` (gộp mọi quy ước từ đợt B vào hướng dẫn cho haiku: di cảo, mất tên, bản dịch, "revised", hành động lập pháp, bài giảng, triển lãm, giải từng năm, rating, kết quả trận, việc của thực thể khác, "giữa X và Y", mục Timeline nhiều ngày lẻ), `tools/mk_batch.py` (chép `GUIDE_v7.md`, lấy cả trang dưới 8 chunk khi hết trang dài). Batch đặt tên `batchV1`, `batchV2`, ... seed 7201 trở đi; sửa bằng `tools/patch_bV*.py`.

Một mâu thuẫn mình chưa gỡ: quy ước F của session B (ngày sinh con là mốc `family`) trái quyết định cũ của người dùng (không ghi ngày sinh con). `GUIDE_v7.md` theo quyết định cũ: không ghi ngày sinh con, ghi ngày cưới và mất của con. Tập tune (từ B5 trở đi, ví dụ Whitney, Cambridge, Carisbrooke) còn các mốc sinh con đã ghi; có thể lọc bỏ sau bằng `label` hoặc text.

### 10.5r Kiểm V1, V2 (session B làm, 2026-11-04)

Session B làm `batchV1` và `batchV2` (20 trang): V1 haiku 451 → 481 mốc, V2 342 → 355 (thêm 46, bỏ 3). Mình kiểm: `DIR=rev check.py` = 0 lỗi cả hai; số mốc `sub/` và `rev/` khớp bảng của B; `gap.py` các trang mật độ thấp (ECB 300 chunk/38 mốc, Clitheroe, Numedal, Zerelda, Lanier); đọc danh sách mốc Valladolid, ECB, Lanier, Zerelda. Chưa đọc từng chunk của cả 20 trang, nên đây là kiểm mẫu, không phải kiểm hết.

- Các câu `gap.py` còn liệt kê ở ECB (nước gia nhập euro, báo cáo Nghị viện, promissory note Ireland, số liệu QE), Numedal (Sørland 1871, họp 1873) và Zerelda (em trai tự tử 1895) đều đúng theo quy ước đã ghi trong NOTES.md; mình không thấy mốc sót rõ ràng ở mẫu đã xem.
- Valladolid (70 chunk): haiku chỉ 26 mốc, B thêm 19. Danh sách sau sửa hợp lý, nhưng B tự đặt quy ước "ghi công trình, công ty, tuyến tàu, đại học; không ghi lễ hội và CLB thể thao" cho trang thành phố — ngoài GUIDE_v7. Ghi lại để thống nhất cho các trang thành phố sau.
- Quy ước L (ngày mất của con kể cả sau cha/mẹ): B áp nguyên văn, nên Lanier có 5 mốc (1885–1926) và Zerelda 4 mốc (1915–1934) mất sau nhân vật. Việc này chưa được người dùng quyết; người dùng đã chốt giữ nguyên như session B (ghi cả khi con mất sau cha/mẹ), nên không bỏ 9 mốc; đã ghi vào `GUIDE_v7.md`.
- Chỗ B có sửa lỗi của haiku đáng ghi: Numedal e18 (haiku gán 2014-04 cho việc nâng cấp tà vẹt, nguồn chỉ nói "sau vụ trật bánh") và Quaid e36 (text sai).
- Hạn chế như tune: `check.py` không bắt mốc sót hay sai ngày; phần chưa đọc từng chunk có thể còn vài mốc sót mỗi 10 trang.

### 10.5s Kiểm V3, V4 (2026-11-04)

V3 do session B làm xong (NOTES và `patch_bV3.py`); V4: haiku xong nhưng session B hết hạn mức, session chính đọc kiểm và vá (`patch_bV4.py`, +27 mốc, 283 → 310). `DIR=rev check.py` = 0 lỗi cả hai. V4 đọc kỹ cả 10 trang bằng `view.py` và `gap.py`: Chelyabinsk (67 chunk) haiku chỉ ghi 12 mốc nên thêm 11, các trang còn lại thêm 0–6. V3 mình chưa kiểm sâu (chỉ có số liệu từ NOTES của B).

### 10.5t Kiểm V5, V6 (cloud làm, 2026-11-04)

Lần đầu giao việc cho Claude cloud (nhánh `cloud/valid-timelines`): cloud dựng V5, V6 và chạy 20 haiku song song, `check.py` 0 lỗi, không đụng file ngoài phạm vi. Nhưng cloud sửa quá ít (V5 +5, V6 +4/−5) trong khi các trang dài còn nhiều mốc sót. Session chính đọc kiểm và vá bằng `tools/fix_V56.py` (V5 200 → 226, V6 312 → 321): SECR_N_class +19, Flatiron +6, Pérez +7, LB&SCR E4 +8, Gamvik +1, Gleaston +1, Manto −7 (tuyển tập ghi năm 1955 chuyển sang `undated_mentions`). Bài học: với trang dài (trên 40 chunk), phải bắt buộc đọc từng trang và nộp danh sách mốc thêm; số liệu "gap.py đã chạy" của cloud không đủ chứng minh đã đọc.

### 10.5u V7, V8 do session chính làm (2026-11-04)

Session chính dựng V7, V8 và chạy 20 haiku song song, rồi tự đọc kiểm bằng `gap.py` và đọc danh sách mốc; vá bằng `tools/patch_bV78.py`. V7 413 → 425, V8 258 → 266 (+20 ròng), `check.py` 0 lỗi ở cả `sub/` và `rev/`. Haiku làm tốt hơn V5/V6 cloud ở các trang dài (Myanmar, Security Service of Ukraine, Han dynasty gần như đủ). Điểm mới: `gap.py` không thấy năm TCN/CE (Han dynasty), phải dò tay bằng regex "BC|AD|CE". Tổng valid đã làm: V1–V8 (80 trang), còn 87 trang.

### 10.5 Dữ liệu và công cụ

Thư mục `dataset/eval/timeline_pilot/`:

- `pilot5/`: `in/` (chunk gốc, đúng cách `chunk_document` đánh số), `me/` (timeline mình viết: `.dsl` và `.json`), `sub/` (timeline subagent), `GUIDE_v1.md`.
- `pilot10/`: `in/`, `sub/` (bản gốc của subagent), `rev/` (bản sau khi mình đối chiếu, **đây là timeline vàng của 10 trang**), `GUIDE_v2.md`.
- `batch2/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 2**), `GUIDE_v3.md`; sửa bằng `tools/patch_b2.py`.
- `batch3/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 3**), `GUIDE_v4.md`; sửa bằng `tools/patch_b3.py`.
- `batch4/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang dài đợt 4**), `GUIDE_v4.md`; sửa bằng `tools/patch_b4.py`.
- `batch5/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 5**), `GUIDE_v4.md`; sửa bằng `tools/patch_b5.py`.
- `batch6/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 6**), `GUIDE_v4.md` (đã dùng) và `GUIDE_v5.md` (cho đợt sau); sửa bằng `tools/patch_b6.py`.
- `batch7/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 7**), `GUIDE_v5.md` (đã dùng) và `GUIDE_v6.md` (cho đợt sau); sửa bằng `tools/patch_b7.py`.
- `batch8/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 8**), `GUIDE_v6.md` (đã dùng); sửa bằng `tools/patch_b8.py`.
- `batch9/`: `in/`, `sub/`, `rev/` (**timeline vàng của 10 trang đợt 9**), `GUIDE_v6.md` (đã dùng); sửa bằng `tools/patch_b9.py`.
- `batchB1/` … `batchB11/`: do session phụ B tạo, mỗi batch có `in/`, `sub/`, `rev/` (**timeline vàng**), `NOTES.md`; sửa bằng `tools/patch_bB1.py` … `patch_bB4.py` và `tools/fix_B34.py` (5 mốc mình bổ sung). B5 và B6 chưa làm. `reserved_B.json` và `tools/mk_batch.py` xem 10.5k.
- `tools/`: `mk.py` (dựng JSON từ `.dsl` và kiểm quote), `cmp.py` (so hai bên), `check.py` (mã kiểm), `view.py` (xem chunk cạnh sự kiện), `patch.py` (các sửa của mình trên bản `sub/`).

Tất cả là dữ liệu mẫu thử, chưa phải bộ dữ liệu cuối. Các trang nằm trong tập `tune`, nên chưa dùng chung với `valid` hay `test_clean`.

### 10.5v V9, V10 do cloud làm, session chính kiểm (2026-11-04)

- Cloud (nhánh `cloud/valid-timelines`, commit `62ea9f4`) làm V9 (526 → 537) và V10 (558 → 558); `DIR=rev check.py` 0 lỗi. Tôi đọc `gap.py` từng trang dài và đối chiếu NOTES: V9 +12 (549), V10 +14 (572), `tools/fix_V910.py`.
- **Đính chính nhận định ban đầu:** nhìn số dòng `gap.py` (Whitman 33, Schröder 31) tôi tưởng cloud đọc thiếu như V5/V6; sau khi đọc, phần lớn dòng là phát biểu, việc của thực thể khác hoặc thống kê, đúng với quy ước và đã được NOTES của cloud giải thích. Tôi thêm 11 mốc rồi bỏ lại. Phần thiếu thật chủ yếu ở trang thể thao (mùa giải) và vài sự kiện chính thực thể.
- Ba quy ước mới trong `GUIDE_v7.md` (áp dụng từ V11): không ghi tai nạn của từng máy bay trên trang hãng; năm TCN dùng số thiên văn và `check.py` nhận dấu âm; danh hiệu/thăng hạng/đổi HLV theo mùa "1999–2000" ghi ở năm bắt đầu, `approximate_date`. **Hệ quả:** tune và V1–V10 để mùa giải ở `undated_mentions`, chỉ Galatasaray (V10) và vài mốc ở V9 dùng quy ước mới; cần nêu trong phần phương pháp.
- `check.py` sửa để nhận năm âm; Han dynasty (V7) từ 55 lỗi về 0.

### 10.5w V13, V14 do session chính làm (2026-11-04)

- Dựng V13 (seed 7213) và V14 (seed 7214) từ `reserved_valid.json` sau khi dựng V11, V12 (để cloud làm); bốn batch không trùng trang, còn 27 trang valid. 20 haiku song song, `DIR=sub check.py` 0 lỗi cả hai.
- Đọc kiểm bằng `gap.py` trang nào >2 dòng: V13 haiku 190 → 195 (+5: Engels +2, Max_Weber +1, Guy_Whittingham +1, Florida +1), V14 246 → 247 (+1: GER S69). Phần lớn dòng gap là tài liệu tham khảo, tai nạn từng đầu máy (quy ước mới) và việc của thực thể khác. `tools/patch_bV1314.py`.
- Lần này haiku bỏ sót ít hơn các đợt trước (+0,5/trang), phù hợp với quy ước đã chặt hơn (GUIDE_v7 có mục bổ sung). Chưa đọc từng chunk của cả 20 trang, chỉ `gap.py` và danh sách mốc trang có mật độ thấp.

