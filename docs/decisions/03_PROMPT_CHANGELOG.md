# Nhật ký thay đổi prompt

Mỗi dòng: ngày, file prompt, đổi gì, vì sao, hiệu quả đo được (nếu có). Quyết định lớn có file riêng ở thư mục này; đây chỉ là sổ ghi để biết kết quả ở `docs/eval/` ứng với phiên bản prompt nào. Từ 2026-10-19 (sau lần 4) config dùng combo `basic-gemini-3.5-flash-lite` chỉ chứa một model, nên các lần chạy sau không còn bị đổi model ngầm; các lần trước dùng `basic-llm`. Số liệu so sánh nhiều lần chạy phải kèm lưu ý: model phía sau combo `basic-llm` của 9router **thay đổi theo thời gian** (ngày 2026-10-19 một model bị ngừng và combo chuyển sang `gemini-3.1-flash-lite`), nên khác biệt giữa hai lần chạy không hoàn toàn do prompt.

## Quy ước phiên bản (từ 2026-10-20)

- Mỗi prompt là một file `<tên>_v<N>.md`. **Sửa nội dung thì tạo file mới `_v<N+1>`, không ghi đè bản cũ**: các lần chạy benchmark cũ vẫn cần đọc lại đúng prompt đã dùng. Mọi prompt có sẵn trước ngày này là `v1`.
- Code giữ hằng `PROMPT_VERSION` cạnh `PROMPT_PATH` (`query/profiler.py`, `query/range_profiler.py`, `ingestion/time_extraction.py`); `profile_eval.py` ghi `prompt_version` vào từng dòng `profiler.jsonl`.
- Cache LLM khóa theo tên schema, model và **nội dung** prompt (`llm/cache.py`), không theo tên file: đổi tên file mà nội dung giữ nguyên thì cache cũ vẫn trúng (đã kiểm: 330/330 lô ingestion và 399/400 câu Profiler v1 vẫn từ cache sau khi đổi tên); prompt mới thì khóa mới, cache cũ nằm yên và còn dùng được cho lần chạy cũ.

| Prompt | Phiên bản | Ghi chú |
|---|---|---|
| `ingestion_time` | `v1` | Bản mặc định, dùng ở mọi kết quả đến 2026-10-20 |
| `ingestion_time` | `v3` | **Bản thảo, mới thử 3 trang** (2026-10-20): v2 + phân biệt "các giai đoạn riêng" với "một nhiệm kỳ đang diễn ra" khi chunk có nhiều mốc. Chọn bằng `--prompt-version v3` |
| `ingestion_time` | `v2` | **Thử nghiệm** (2026-10-20): sự việc một lần khác sự việc mở trạng thái; chunk nhiều mốc lấy mốc sớm nhất và muộn nhất; chunk mở đầu về chủ thể. Chọn bằng `scripts/ingest.py --prompt-version v2` (mặc định `v1`); nạp vào collection riêng `tam_chunks_dev_real_v2` |
| `time_extractor` (Profiler) | `v1` | Trả một điểm `t_req` (`Profiler`, schema `Extraction`); dùng ở mọi kết quả đến 2026-10-20 |
| `time_extractor` (Profiler) | `v2` | Trả khoảng `t_start`/`t_end` ở độ mịn câu hỏi + `bound` (exact/after/before/none) (`RangeProfiler`, schema `RangeExtraction`); decisions/07 đề xuất 1. Khác schema nên là lớp riêng, `v1` không đổi |
| `time_extractor` (Profiler) | `v3` | **Dự kiến, chưa viết** (xem mục dưới) |

## `src/tam/llm/prompts/ingestion_time_v1.md` (gán mốc và domain cho chunk)

| Ngày | Đổi gì | Vì sao | Hiệu quả |
|---|---|---|---|
| trước 2026-10-19 | Cho phép lấy ngày từ chunk khác của trang; ba trạng thái của `end`; 5 ví dụ nhiều chunk | Chunk thiếu năm riêng bị bỏ oan | Chưa đo (`process/05` mục 3) |
| 2026-10-19 | Thêm trường `reason_end_date` (đặt trước `end`, `ongoing`) | Cần biết vì sao LLM suy ra `end`/`ongoing` | Phát hiện 42 chunk lý do tự mâu thuẫn với `ongoing` |
| 2026-10-19 | Thêm `domain` (danh sách đóng 8 + `other`, tối đa 3 nhãn), ví dụ gán nhãn tự đặt, mục "Output format" với JSON mẫu | Điểm cộng domain ở retrieval (decisions/01) | Nhãn có cho mọi chunk; 32/39 chunk đáp án khớp domain suy từ P (thước đo thô) |
| 2026-10-19 | Thêm `reason_domain` (trước `domain`) | Truy lại vì sao lệch nhãn | Cho thấy 7 ca lệch đều theo nội dung chunk; lệch nằm ở thước đo P→domain |
| 2026-10-19 | Thêm `ongoing_evidence` và siết quy tắc `ongoing` ("thiếu ngày kết thúc không phải bằng chứng") | `basic-llm` đặt `ongoing` bừa (decisions/02) | `ongoing` trên chunk đã nạp 170 → 35 |
| 2026-10-19 | Thử "bằng chứng nằm trong chính chunk", **đã gỡ** | Nghi `Casus_Belli` mượn câu của chunk khác; điều tra lại thì suy luận chéo chunk là đúng | Không áp dụng (xem decisions/02) |
| 2026-10-19 | Thử cho LLM viết năm âm cho mốc trước Công nguyên rồi **gỡ**; giữ "trước Công nguyên = không có mốc" | 3 chunk `Zambia` bị `invalid_time` | Không áp dụng (decisions/05: loại) |

### Dự kiến, chưa làm
- ~~Quy tắc ưu tiên "lĩnh vực của chủ thể hơn khía cạnh"~~ **bỏ** (2026-10-19): domain chỉ cộng điểm và gắn theo khía cạnh được hỏi, chunk được mang tới 3 nhãn gồm cả hai loại, nên không cần chọn một. Xem docs/eval/01 mục 3.
- Ghi nhận: `ingestion_time_v1.md` có thời gian sửa 11:48 giữa lần 2 và lần 4 mà sổ này không có dòng tương ứng; nội dung thay đổi chưa dựng lại được. Từ nay mỗi lần đổi prompt phải ghi dòng ở đây trước khi chạy.

## `src/tam/llm/prompts/ingestion_time_v2.md` (gán mốc và domain cho chunk)

Mục đích: giảm lỗi nhãn thời gian của chunk đúng (92/123 câu sai của cấu hình nền có nhãn lệch thời điểm hỏi: `eval/05` mục 6.12; đề xuất 9 ở `decisions/07`). Phần `domain` giống hệt v1 (đã diff) để chỉ đổi phần thời gian. `v1` không đổi.

| Ngày | Đổi gì | Vì sao | Hiệu quả |
|---|---|---|---|
| 2026-10-20 | Thay mục "ba trạng thái" bằng thứ tự quyết định cho `end` (một lần / nhiều mốc / chunk mở đầu / tình huống bắt đầu) | v1 tự mâu thuẫn: `end` định nghĩa "ngày muộn nhất của sự việc" mà trạng thái 3 bảo null; nhiều chunk có lý do "nothing says whether it stopped" vẫn điền `end` = năm `start` | Xem dưới |
| 2026-10-20 | Tách sự việc một lần khỏi sự việc mở trạng thái (nguyên tắc "hôm sau còn đúng không?" + 5 ví dụ khác loại, không liệt kê động từ) | LLM sao chép ngày bổ nhiệm/chuyển nhà vào `end` (khoảng 18 chunk sai) | |
| 2026-10-20 | Chunk nhiều mốc hoặc có khoảng ("1963–64"): `end` là mốc muộn nhất, không null | Khoảng 25 chunk danh sách bị rút thành một mốc | |
| 2026-10-20 | Chunk mở đầu về chủ thể: cả vòng đời (sinh/thành lập → mất/giải thể, không thì unknown), không áp "ngày sinh là cả sự việc" | Khoảng 9 chunk bị gán một ngày | |
| 2026-10-20 | Ví dụ tự bịa: giải thưởng, bổ nhiệm, danh sách giám đốc, tiểu sử người còn sống, công ty giải thể ở chunk khác, nơi ở Lisbon → Madrid, kể chuyện theo mùa | Mỗi quy tắc một ví dụ | |
| 2026-10-20 | **Không đụng chính sách `ongoing`** | Giữ như `decisions/02` (cần cụm nguyên văn) | |

**Ba lần thử trên 3 trang (113 chunk, `--dry-run`, 5 request mỗi lần)**, so với v1 về `end_status`:

| Bản | known / unknown | Nhận xét |
|---|---|---|
| v1 | 80 / 9 | |
| v2a (bản đầu) | 77 / 15 | Danh sách và lịch sử nhiều năm được khoảng rộng đúng hơn (1 Hanover Square, 1. FC Köln #33–35), nhưng 9 chunk kể mùa giải ("1977–78", "2012–13") bị chuyển sang `unknown`, chỉ còn năm bắt đầu (hồi quy) |
| **v2b (bản chọn)** | 76 / 19 | Đổi thứ tự: nhiều mốc hoặc khoảng đứng trước tình huống bắt đầu; thêm ví dụ kể chuyện; hồi quy mùa giải sửa được. Còn vài chunk lỡ sang `unknown` dù có hai năm (landmark 1965 và 1999) |
| v2c (thêm bước `Dates:` ở `reason_end_date`) | 59 / 35 | **Tệ hơn**, LLM nhỏ coi nhiều chunk hơn là "mở trạng thái"; đã gỡ |

Kết luận tạm: LLM nhỏ (Gemini 3.5 flash-lite) tuân thủ thứ tự quyết định chưa ổn định; 3 trang không đủ để chọn tiếp. Bản chọn là v2b; kết quả cuối phải đo bằng chỉ số truy xuất.

## `src/tam/llm/prompts/ingestion_time_v3.md` (gán mốc và domain cho chunk)

Bản thảo, đã thử 3 trang (113 chunk, 5 request) nhưng chưa đo bằng chỉ số truy xuất. Dựa trên v2 (bản v2b), sửa một chỗ; `v2` giữ nguyên để khớp kết quả đã chạy.

| Ngày | Đổi gì | Vì sao | Hiệu quả |
|---|---|---|---|
| 2026-10-20 | Bước 2 của "What `end` means" tách hai trường hợp: (a) các mốc là giai đoạn riêng (mùa giải, năm của một lịch sử, mục của danh sách) → chỉ dùng mốc trong chính chunk, chuyện tiếp ở chunk sau không kéo dài chunk này; (b) các mốc là các phần của **một** nhiệm kỳ/công việc/hôn nhân/nơi ở đang diễn ra mà chunk khác nói đã kết thúc → `end` là mốc kết thúc đó | v2b có xung đột chưa kiểm: chunk "bổ nhiệm 2004 ... thắng cúp 2005" nhận `end` 2005 (mốc muộn nhất trong chunk) dù chunk sau nói "rời chức 2007" cùng nhiệm kỳ. Ngược lại, coi cả mạch kể là một sự việc sẽ kéo mọi chunk của trang đến mốc cuối trang, mất khả năng phân biệt thời gian | |
| 2026-10-20 | Thêm hai ví dụ đối lập tự bịa (lịch sử đội theo mùa so với một nhiệm kỳ giám đốc) | Mỗi nhánh một ví dụ | |

Thử 3 trang (`--dry-run`, 5 request): `end_status` v1 80 known / 9 unknown / 1 ongoing; v2b 76 / 19 / 1; **v3 75 / 16 / 2** (20 chunk không mốc). Tức v3 ≈ v2b, vẫn nhiều `unknown` hơn v1. Hai ca xung đột nhắm tới (cùng nhiệm kỳ nhưng bước 2 cho `end` sớm) không có trong 3 trang này nên chưa kiểm. Còn lại: landmark 1965/1977 (Hanover #5), #29 (hai năm 1870, 1871 nhưng `unknown`), #8 vẫn `unknown` chỉ còn năm bắt đầu; Köln #1 thành `ongoing` (bằng chứng "as of 1 August 2019"). Rủi ro như v2c: thêm quy tắc có thể làm LLM nhỏ tuân thủ kém đi; phải đo trước khi tin.

## `src/tam/llm/prompts/time_extractor_v1.md` (Profiler)

Chưa đổi prompt. Phát hiện 2026-10-19: với `basic-llm`, các ví dụ dạng `semantic_query: ... | t_req: ...` khiến combo trả văn bản tự do thay vì JSON (40/40 câu lỗi). Xử lý bằng code (`tam/llm/structured.py`: đọc JSON từ văn bản, thử lại), không đổi prompt. Sau đó 0/40 lỗi.

## Dự kiến `time_extractor_v3` (chưa viết, 2026-10-20)

**Lỗi phát hiện ở `v2`** (chạy 400 câu bộ thật, `output/20261020_173521/profiler.jsonl`): 2 câu có cụm "late 1900s" (Alexander Imich `#P27#0`, John Francis Charles) bị đọc thành `t_start 1997`, `t_end 1999`, tức thập niên 1990, trong khi nhãn của bộ dữ liệu là 1903–1918 và 1906–1911 (thập niên 1900). Cả hai câu cùng mất khoảng thời gian đúng, nên Profiler `v2` giao khoảng nhãn ở 395/400 câu chứ không phải 400/400. Cùng lỗi ở `v1` (`t_req` 1999-12-31).

**Cách sửa dự kiến**: không thêm một ví dụ riêng cho "1900s" (sẽ khớp lỗi này nhưng dễ vấp lỗi kế cận). Viết một quy tắc chung cho các cách nêu thập niên và thế kỷ, kèm **vài ví dụ khác nhau** để mô hình hiểu nguyên tắc, như:
- "the Ns" (N chia hết cho 10) là mười năm `N` đến `N+9` **trong đúng thế kỷ được viết**, không bao giờ đổi sang thế kỷ khác (ví dụ khác nhau: 1850s, 1920s, 1960s, 2010s, 1900s đều xử lý cùng một cách).
- "early/mid/late" cộng thập niên: nửa đầu, giữa, nửa cuối của thập niên đó (không phải của thế kỷ).
- Thế kỷ viết bằng chữ ("the 19th century", "early 20th century") có quy tắc riêng, nêu rõ quy ước chọn (ví dụ thế kỷ 20 = 1900–1999).
- Khi một cụm có thể hiểu theo hai cách, chọn cách thứ tự gần với **chữ được viết** nhất.
Sau khi viết, kiểm trên hai câu lỗi ở trên và một mẫu câu có thập niên khác; không sửa `v1`/`v2`.
