# Kết quả ingestion bộ local (LLM gán mốc thời gian và domain)

Lần 1 và 2 (2026-10-19): `python scripts/ingest.py --dry-run` trên 37 trang của `dataset/eval/local_subset.json` (40 câu, 8 domain × 5). LLM: role `ingestion_time` = 9router, combo `basic-llm` (model thật phía sau combo chưa rõ). Chi tiết từng chunk: `output/20261019_104340/extractions.jsonl` (thư mục `output/` bị gitignore). Cách dựng bộ và mã: [`../process/06_EVAL_SUBSET.md`](../process/06_EVAL_SUBSET.md).

`--dry-run` = chạy tới bước LLM rồi dừng, không embedding, không ghi Qdrant; chỉ ghi `extractions.jsonl`.

## 1. Số liệu chung

| Đo | Kết quả |
|---|---|
| Chunk tổng / có mốc (vào kho) / `no_time` / `invalid_time` / `llm_error` | 1275 / 1058 / 216 / 1 / 0 |
| Số nhãn `domain` mỗi chunk: 0 / 1 / 2 / 3 | 23 / 807 / 429 / 16 |
| Nhãn nhiều nhất | politics 289, place 288, business 269, sports 269, media_arts 217, career 135, person 112, military 102, other 32 |
| `ongoing = true` | 177 chunk |

## 2. Chunk đáp án còn sống: 39/41

"Chunk đáp án" = chunk trong `gold_chunk_ids` của câu hỏi. "Còn sống" = sau khi LLM gán mốc, chunk đó **vẫn được nạp vào kho**. Chunk bị bỏ vì không có mốc (`no_time`) thì không vào Qdrant, nên retriever không thể trả về nó dù thuật toán tốt đến đâu. Vì vậy 39/41 (95%) là **trần của Hit@k** trên bộ này.

Hai chunk mất, đều `no_time`:
- `/wiki/Central_European_University#62`, đáp án "Monica Macovei".
- `/wiki/Pskov#0`, đáp án "Russia".

## 3. Domain: 31/39 chunk đáp án có nhãn LLM chứa domain suy từ `relation`

Domain của câu hỏi ở đây **suy từ `relation` (P) qua bảng trong `TOPICS.md`**, chỉ là mốc đối chiếu, không phải nhãn "đúng tuyệt đối". 8 trường hợp lệch:

| Domain suy từ P | P | Nhãn LLM gán cho chunk | Câu hỏi (rút gọn) |
|---|---|---|---|
| person | P1448 | military, place | Air Armament Center được đặt tên chính thức là gì năm 1944 |
| business | P488 | politics | Ai chủ trì Alliance of Small Island States |
| career | P1075 | business, place | Hiệu trưởng Central European University |
| media_arts | P800 | place | Holden thiết kế ga nào (kiến trúc sư) |
| business | P488 | career, politics | IMU do ai chủ tịch sau 1983 |
| person | P551 | media_arts, business | Đạo diễn Lotte Reiniger sống ở đâu |
| person | P1448 | sports | Tên chính thức của Baby Cakes |
| career | P108 | sports | Rui Vitória làm việc ở đâu (đội bóng) |

Phần lớn là nhãn LLM hợp lý theo nội dung (chunk nói về đội bóng thì `sports`), còn bảng P→domain mới là phép ước lượng thô. Tức "lệch" ở đây chưa chắc là LLM sai.

### Vì sao lệch: 8 nhãn trộn hai trục

Nhãn gồm hai kiểu không cùng loại: **lĩnh vực của chủ thể** (`sports`, `military`, `business`, `politics`, `media_arts`, `place`) và **khía cạnh được nói tới** (`career`, `person`). Chunk về một huấn luyện viên vừa là `career` vừa là `sports`, prompt chưa có quy tắc chọn nên LLM chọn theo nội dung (đúng cả hai). Thước P→domain thì suy từ *khía cạnh được hỏi* (P108 employer → career) nên lệch với nhãn theo lĩnh vực. Ca đáng ngờ duy nhất là CEU (lịch sử trường đại học bị gán `business`). Hướng sửa dự kiến (chưa làm, chờ đo khớp Profiler với chunk): thêm quy tắc "ưu tiên lĩnh vực của chủ thể hơn khía cạnh" kèm 2 ví dụ, dùng chung cho ingestion và Profiler. Xem [`../decisions/03_PROMPT_CHANGELOG.md`](../decisions/03_PROMPT_CHANGELOG.md).

### Rủi ro thật cho retrieval

Điều quan trọng không phải domain suy từ P, mà là **nhãn Profiler gán cho câu hỏi lúc truy vấn có khớp nhãn của chunk hay không**. `domain` là hard filter, nên nếu Profiler gán `place` mà chunk đáp án chỉ có `["media_arts"]` thì chunk bị loại và không có cách cứu. Chưa đo được vì Profiler chưa chạy trên 40 câu này, và Profiler hiện còn trả `domain` chuỗi tự do. Hướng giảm rủi ro (chưa làm):
- Profiler chỉ điền `domain` khi câu hỏi rất rõ, còn lại `null` (đã có trong prompt Profiler).
- Chạy ablation có và không có filter `domain` (`TOPICS.md` mục 5 đã dự kiến).
- Cân nhắc dùng `domain` để cộng điểm (soft boost) thay vì loại cứng.
- Đo trực tiếp: với 40 câu, chạy Profiler rồi kiểm tra chunk đáp án có qua được filter không.

## 4. Vấn đề `ongoing`

`basic-llm` đặt `ongoing = true` ở 177 chunk, trong đó **42 chunk** có `reason_end_date` nói "không có ngày kết thúc / không được nhắc". Trái quy tắc prompt (không biết thì `ongoing = false`). Hậu quả: `end_time = None`, chunk được `Temporal_Score = 1.0` với mọi `t_req` sau `start`. Chưa sửa; cần siết prompt hoặc thêm kiểm tra rồi chạy lại để so.

## 5. Lỗi định dạng của `basic-llm`

Combo bỏ qua structured output, trả JSON trong khối markdown, đôi khi viết hoa khóa (`Index`) hoặc sai dấu phẩy. Đã xử lý trong `TimeExtractor` (đọc JSON từ văn bản, thử lại tối đa 3 lần, hết lần thì `llm_error`). Lần chạy này 0 lô `llm_error`.

## 6. Chạy lại sau khi siết prompt (2026-10-19, `output/20261019_111731/`)

Thay đổi: thêm `reason_domain` và `ongoing_evidence` (câu trích nguyên văn khi `ongoing`, code kiểm tra có trong văn bản và có dấu hiệu còn hiệu lực), siết quy tắc `ongoing` trong prompt. Xem [`../decisions/02_END_TIME_ONGOING.md`](../decisions/02_END_TIME_ONGOING.md).

| Đo | Lần 1 | Lần 2 |
|---|---:|---:|
| Chunk có mốc / `no_time` / `invalid_time` | 1058 / 216 / 1 | 1029 / 243 / 3 |
| `ongoing = true` (tổng, gồm cả chunk bị bỏ vì không mốc) | 177 | **38** |
| Trong đó chunk đã nạp vào kho | 170 | **35** |
| Trong đó lý do có cụm "no end date / not mentioned" | 42 | 8 (đều kèm bằng chứng hợp lệ như "since 2017", nên không còn mâu thuẫn) |
| Bị code hạ vì bằng chứng không đạt | (chưa có) | 4 |
| Chunk đáp án còn sống | 39/41 | 39/41 (vẫn mất `Central_European_University#62`, `Pskov#0`) |
| Domain khớp domain suy từ P | 31/39 | 32/39 |
| Số nhãn mỗi chunk 0 / 1 / 2 / 3 | 23 / 807 / 429 / 16 | 24 / 843 / 385 / 23 |

- Phần lớn việc giảm `ongoing` (170 → 35 chunk đã nạp) do prompt siết; kiểm tra của code chỉ hạ thêm 4 chunk. Các `ongoing` còn lại có bằng chứng thật ("since 2017", "currently", "since 2006").
- Bằng chứng bị hạ nhầm: "to this day" (thiếu dấu hiệu `this day` trong danh sách; đã thêm). Bằng chứng bị hạ đúng: "married 2018", "commonly referred to as".
- Số chunk không có mốc tăng 216 → 243: LLM thận trọng hơn. Cần theo dõi vì chunk `no_time` bị bỏ khỏi kho.
- Chưa kiểm tra tay xem 38 chunk `ongoing` có đúng hết không, và 135 chunk từng `ongoing` ở lần 1 nay rơi vào "không biết" (`end_time` = cuối kỳ của `start`) có làm hại câu cần "hiện tại" không.

## 7. Độ chính xác của mốc so với nhãn dataset

**Phép đo.** Mỗi câu có `time_start`/`time_end` (nhãn dataset): khoảng hiệu lực của *sự việc trả lời câu hỏi*. So với `[start, end]` LLM gán cho chunk đáp án (39 chunk còn sống, so theo năm). Script đo: so `local_subset.json` với `extractions.jsonl`.

**Giới hạn của phép đo (đọc kỹ trước khi dùng số):** nhãn là mức *sự việc*, còn mốc của chunk là mức *chunk* = hợp các mốc của mọi sự việc trong đoạn. Ví dụ chunk `Alliance_of_Small_Island_States#24` liệt kê chủ tịch từ 1991 đến nay; nhãn câu hỏi là 2002 đến 2005 (một dòng trong danh sách) nhưng mốc chunk đúng là 1991 đến present. Nên "không khớp nhãn" không đồng nghĩa LLM sai.

| Đo (39 chunk đáp án) | Lần 1 | Lần 2 |
|---|---:|---:|
| `start` đúng năm nhãn | 10 | 12 |
| `end` đúng năm nhãn | 6 | 3 |
| Khoảng chunk **phủ** khoảng nhãn (`start ≤ nhãn start`, `end` rỗng hoặc `≥ nhãn end`) | 29 | 24 |
| Khoảng chunk **giao** khoảng nhãn | 34 | 31 |
| Chunk đáp án có `ongoing = true` | 8 | 3 |

- **Lần 2 không tốt hơn ở các số này, có chỗ kém hơn.** Nguyên nhân chính: chunk kiểu "joined X in 2006" (nhãn 2006 đến 2020) trước đây hay được `ongoing` nên `end_time = None` và phủ nhãn; nay về "không biết" nên `end` = hết năm 2006, không phủ. Đây là đánh đổi có chủ ý: điểm phủ nhãn giảm nhưng số chunk bị coi còn hiệu lực sai cũng giảm (170 → 35).
- Hậu quả cho `Temporal_Score`: chunk đáp án "joined 2006" với `t_req = 2010` rơi vào TH2 (`exp(-0.5·4) ≈ 0.14`) thay vì TH1 (1.0). Có thể làm chunk đúng tụt hạng. Đây là lý do cần lưu `end_status` và thử ba cách chấm (quyết định 02).
- 15/39 chunk đáp án không phủ nhãn ở lần 2. Phần lớn là chunk mốc chung chung hoặc chứa nhiều sự việc (vd `Lotte_Reiniger` nhãn 1948 đến 1980, LLM gán 1949 đến 1953; `Volvo_9700` nhãn 2008 đến 2009, LLM gán 2001).

**Chunk đáp án bị bỏ (2/41), đều hợp lý:**

| Chunk | Vì sao không có mốc |
|---|---|
| `Central_European_University#62` | Danh sách cựu sinh viên, không có năm nào (đáp án "Monica Macovei") |
| `Pskov#0` | "Pskov là một thành phố ở miền tây bắc Nga..." không có năm (đáp án "Russia") |

Không phải LLM sót: văn bản không có mốc. Chỉ nhánh "chunk không có mốc" (`process/05` mục 3.4, chưa quyết) cứu được hai chunk này.

**Kiểm tra `ongoing` (35 chunk đã nạp, lần 2).** Đọc tay lý do và bằng chứng của khoảng 25 chunk:
- Đúng/chấp nhận được: bằng chứng "since 2017", "currently", "since 2002", "to the present", "present", "continues to occupy the building". Kể cả `Alliance_of_Small_Island_States#24` (danh sách chủ tịch kết thúc "2019–present") và `Jean_Lassalle#0` (đại biểu "since 2002", start 1955 là ngày sinh): mốc chunk là hợp các sự việc.
- Đáng ngờ: `Casus_Belli_(magazine)#3, #4, #6` có bằng chứng "Since 2020" (nói về Casus TV) trong khi mốc chunk là 2011, 1992, 1980: bằng chứng có thể lấy từ chunk khác của trang và không mô tả sự việc của chính chunk. `Atlético_Madrid#83` ("since 2001" nhưng start 1911) và `Volvo_9700#29` ("they offer since 2012" nhưng start 2000) cũng vậy.
- **Điểm yếu của kiểm tra hiện tại:** câu bằng chứng chỉ phải nằm trong văn bản của *cả lô chunk của trang*, chưa buộc nằm trong *chính chunk đó*. Chưa kiểm tra tay đủ 35.

**Thiếu so sánh trực tiếp:** chưa có nhãn mốc thủ công cho từng chunk, nên các số trên chỉ là gián tiếp qua nhãn câu hỏi.

## 8. Lần nạp thật vào Qdrant (lần 4) và so ba lần chạy

Báo cáo tự động: `python scripts/ingestion_report.py lan1=output/20261019_104340 lan2=output/20261019_111731 lan4=output/20261019_120005 --profiler output/20261019_115213/profiler.jsonl` (mã: `src/tam/evaluation/ingestion_report.py`, `profiler_report.py`).

| Đo | Lần 1 | Lần 2 | Lần 4 (nạp thật, 949 chunk) |
|---|---:|---:|---:|
| Chunk vào kho / bỏ vì không có mốc / bỏ vì mốc sai | 1058 / 216 / 1 | 1029 / 243 / 3 | 949 / 321 / 5 |
| Chunk vào kho có `ongoing = true` | 170 | 35 | 51 |
| `ongoing` bị code đổi về "không biết" vì bằng chứng không đạt | 0 | 4 | 12 |
| Chunk đáp án còn trong kho | 39/41 | 39/41 | 38/41 |
| Nhãn domain LLM của chunk đáp án chứa domain suy từ P | 31/39 | 32/39 | 34/38 |
| Năm `start` của chunk = năm `time_start` của nhãn | 10 | 12 | 12 |
| Năm `end` của chunk = năm `time_end` của nhãn | 6 | 3 | 6 |
| Khoảng chunk bao trọn / giao khoảng nhãn | 29 / 34 | 24 / 31 | 22 / 32 |

### Giải thích thuật ngữ trong bảng

- **Bị bỏ vì không có mốc (`no_time`):** LLM không gán được `start` cho chunk, nên chunk không vào Qdrant (bất biến của đồ án).
- **`ongoing` bị code đổi về "không biết":** LLM nói chunk "còn tiếp diễn" (`ongoing = true`) và phải trích một câu làm bằng chứng. Nếu câu đó không có trong trang, hoặc không chứa từ báo hiệu còn hiệu lực (`since`, `present`, `currently`, `still`...), code đổi nhãn về "không biết" (`end` = hết năm của `start`). Trong báo cáo cũ em viết tắt là "bị hạ".
- **Năm `start`/`end` đúng nhãn:** nhãn của dataset (`time_start`, `time_end`) là khoảng thời gian sự việc đáp án có hiệu lực. Đếm số chunk đáp án mà năm LLM gán trùng năm trong nhãn. Chỉ là phép đo gián tiếp vì chunk có thể chứa nhiều sự việc (xem mục 7).
- **Bao trọn / giao:** khoảng `[start, end]` của chunk chứa hết khoảng nhãn / có phần chung với nó.

### Vì sao lần 4 có vẻ kém hơn lần 2

Nguyên nhân chính nhìn thấy được là số chunk **không có mốc** tăng từ 243 lên 321 (93 chunk có mốc ở lần 2 mất mốc ở lần 4, 15 chunk ngược lại). Đã kiểm tra:
- Đây **không** phải lỗi định dạng hay LLM bỏ sót chunk: chỉ 1 chunk bị sót, 0 lô lỗi, không có lần thử lại thất bại.
- Phần lớn chunk mất mốc là chunk **không có năm trong chính văn bản** (ví dụ `Charles_Holden#1`: "After working and training in Bolton and Manchester, Holden moved to London..."). Ở lần 2 LLM gán cho chúng mốc kế thừa từ chunk lân cận; ở lần 4 nó để trống. Chỉ khoảng 15 chunk `no_time` có sẵn một năm trong 300 ký tự đầu (và cả lần 2 lẫn lần 4 đều có số này).
- Giữa hai lần, model phía sau combo `basic-llm` đã đổi (lần 2 là model khác, lần 4 là `gemini-3.1-flash-lite`), nên em không tách được phần do model và phần do prompt/code. **Chưa chứng minh được đây là suy giảm do code.** Mốc kế thừa ở lần 2 có đúng hay không cũng chưa kiểm tra: số "năm `start` đúng nhãn" của hai lần bằng nhau (12), nên chưa thấy lợi ích rõ của việc kế thừa.
- Hệ quả thực tế: chunk không có mốc không vào kho và retriever không tìm thấy được (mất thêm chunk đáp án `Rui_Vitória#2`). Đây là lý do nhánh "chunk không có mốc" (`process/05` mục 3.4, chưa quyết) đáng cân nhắc.

### Profiler so với nhãn chunk (40 câu)

Từ `output/20261019_115213/profiler.jsonl`: 0/40 lỗi; `t_req` nằm trong khoảng nhãn 40/40; `domain` để trống 26 câu, điền 14 câu. Trong 13 câu điền domain mà chunk đáp án còn sống, nhãn của Profiler **khớp** nhãn chunk ở cả 13 câu, tức lọc cứng domain ở các câu này không làm mất chunk đúng. Mẫu nhỏ và Profiler hiện chỉ điền khi rất rõ nên con số này chưa nói gì về trường hợp Profiler phải đoán.

## 9. Chưa làm

- Nạp vào Qdrant (cần bật Qdrant và embedding).
- Chưa có cache kết quả LLM: chạy lại là gọi LLM lại cho cả 37 trang.
- Chưa chạy Profiler trên 40 câu để đo khả năng khớp `domain`.
- Chưa chạy retrieval/eval (Hit@k, MRR) trên bộ local.
