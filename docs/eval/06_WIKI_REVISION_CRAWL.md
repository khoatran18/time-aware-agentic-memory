# 06. Crawl lịch sử chỉnh sửa Wikipedia cho Cơ chế 3

Ngày đo: 2026-10-24. Mục đích: trả lời hai câu hỏi trước khi chốt mức đầu tư vào Cơ chế 3 (xem [`decisions/09`](../decisions/09_CONFLICT_RESOLUTION_SCOPE.md)):

1. Trong lịch sử chỉnh sửa Wikipedia có nhiều đính chính "sai từ đầu" thật không?
2. Sau một lần chỉnh sửa nhỏ, chunk có còn giữ nguyên để so hash và bỏ qua không?
3. Nếu chỉ tải lại cả trang (replace-all) thì có mất thông tin cũ không?
4. Ngoài hash chunk, nhận biết phần đã đổi bằng hash câu hay ghép mờ thì có tốt hơn không?
5. Một sự kiện có được nhiều trang nhắc lại không (để có mâu thuẫn chéo trang cần xử lý)?
6. Diff của Wikipedia có so được hai bản cách xa nhau không, và TimeQA ứng với bản Wikipedia nào?

## Dữ liệu và cách làm

- **Phạm vi:** 204 trang của `dataset/eval/real_subset.json` (bộ 400 câu), toàn bộ revision từ 2021-01-01 đến 2026-10-24, lấy qua MediaWiki API (`prop=revisions`).
- **Kết quả crawl:** 38,273 revision (metadata: `revid`, `timestamp`, `comment`, `tags`, `size`, `user`). Dữ liệu thô nằm ở `local/wiki_revisions/` (gitignore, tái tạo được bằng script).
- **Script:** [`scripts/crawl_wiki_revisions.py`](../../scripts/crawl_wiki_revisions.py), [`scripts/analyze_revision_comments.py`](../../scripts/analyze_revision_comments.py), [`scripts/measure_chunk_stability.py`](../../scripts/measure_chunk_stability.py), [`scripts/measure_old_info_retention.py`](../../scripts/measure_old_info_retention.py), [`scripts/measure_chunk_matching.py`](../../scripts/measure_chunk_matching.py), [`scripts/measure_cross_page_overlap.py`](../../scripts/measure_cross_page_overlap.py).

## 1. Đính chính "sai từ đầu" có nhiều không

Phân loại thô theo comment chỉnh sửa (từ khóa), không đọc diff:

| Nhóm | Số revision | Ghi chú |
|---|---:|---|
| Revert / undo / vandalism | 8,427 (22%) | Có ở 142/204 trang; phần lớn là phá hoại bị hoàn tác nhanh, không phải thông tin người dùng từng tin |
| Có từ khóa "fix/correct/..." nhưng là chỉnh nhiễu (typo, định dạng, tham chiếu, bot) | 1,049 | Loại |
| **Ứng viên đính chính** (từ khóa "fix/correct/incorrect/mistake/..." và không có từ nhiễu) | **961** (2.5%) | Có ở 151/204 trang |

Đọc tay mẫu ngẫu nhiên 40 trong 961 ứng viên:
- Rõ ràng là sửa sự thật: khoảng 5–6 (ví dụ Toungoo dynasty "incorrect date given as per sources", Vladimir Bukovsky sửa quốc tịch, Aleksandra Goryachkina "I had misread the source", Inter Milan sửa chức danh chủ tịch).
- Chưa rõ nội dung (comment chỉ ghi "fix", "Correction", "Fixed my mistake"): khoảng 5.
- Còn lại là nhiễu lọt qua bộ lọc: sửa định dạng, đổi tên file, cập nhật số liệu thống kê, sửa headings.

Ước lượng sơ bộ: khoảng 10–15% ứng viên là đính chính sự thật rõ ràng, tức vài trăm trường hợp trên 204 trang, nhưng **chưa kiểm diff** và phần lớn chưa chắc liên quan thuộc tính TimeQA (đội bóng, chức vụ, nơi làm việc...). Độ tin cậy thấp: mẫu chỉ 40 và một người đọc.

**Kết luận:** loại 4 (sai từ đầu) có nguồn nhưng nhiễu; muốn dùng phải lọc thủ công và đối chiếu Wikidata. Cũng cần lọc đính chính về mốc thời gian, vì chỉ loại này mới liên quan Cơ chế 3.

## 2. Chunk có giữ nguyên sau chỉnh sửa không

**Cách đo.** Lấy wikitext hai revision, làm sạch gần đúng (bỏ template, ref, link, bảng), chia chunk theo hai cách rồi so hash nội dung (chữ thường):
- **Theo đoạn** (giống TimeQA): tách theo dòng trống, đoạn dài hơn 100 từ cắt thành khúc 100 từ.
- **Cố định 100 từ:** nối toàn bộ văn bản rồi cắt mỗi 100 từ.

Chỉ số: tỉ lệ chunk của bản sau có hash trùng một chunk của bản trước ("giữ nguyên").

**Một lần sửa nhỏ** (300 cặp revision liên tiếp, không bot, không revert, thay đổi 20–3000 byte):

| Cách chia | Giữ nguyên trung bình | Trung vị | Cặp có ≥90% giữ nguyên | Cặp có <50% giữ nguyên |
|---|---:|---:|---:|---:|
| **Theo đoạn** | **0.980** | 1.000 | 96% | 0% |
| Cố định 100 từ | 0.800 | 1.000 | 67% | **20%** |

Trung bình mỗi lần sửa chỉ đổi 1.0 chunk trên khoảng 74 chunk khi chia theo đoạn.

**Khoảng cách dài** (bản đầu 2021 so với bản mới nhất, 56 trang):

| Cách chia | Giữ nguyên trung bình | Trung vị | Cặp có ≥90% giữ nguyên | Cặp có <50% giữ nguyên |
|---|---:|---:|---:|---:|
| Theo đoạn | 0.370 | 0.360 | 2% | 64% |
| Cố định 100 từ | 0.061 | 0.000 | 2% | 95% |

**Nhận xét**
- Chia cố định bị lệch dây chuyền: một chỗ sửa làm dịch ranh giới mọi chunk phía sau, nên 20% cặp mất hơn nửa chunk giữ nguyên. Chia theo đoạn thì không bị.
- Với chia theo đoạn, so hash tiết kiệm gần hết chi phí cho **mỗi lần sửa nhỏ** (~98% chunk bỏ qua được).
- Khi cập nhật dồn nhiều năm cùng lúc (2021 so với nay), chỉ còn khoảng 37% chunk giữ nguyên, nên lợi thế chi phí giảm mạnh. Mức tiết kiệm phụ thuộc tần suất nạp bản mới: nạp thường xuyên thì lợi, nạp thưa thì gần như tải lại cả trang.

## 3. Tải lại cả trang (replace-all) có mất thông tin cũ không

**Cách đo.** Với mỗi câu trong bộ 400 câu, đáp án chuẩn (`targets`, lấy từ bản TimeQA khoảng 2021) có còn xuất hiện trong trang Wikipedia **hiện tại** không (so khớp chuỗi sau chuẩn hóa chữ thường, bỏ dấu và dấu câu). Nếu còn thì tải lại cả trang vẫn giữ được thông tin cũ đó. Cả 400 đáp án đều khớp trong bản 2021, nên mẫu số là 400.

Có hai cách lấy văn bản hiện tại, cho hai cận:
- **extracts** (văn bản thuần của API) bỏ bảng và một số mục, nên đánh giá thấp: cận dưới.
- **wikitext thô** còn cả ref, template, bảng, nên có thể đếm cả đáp án chỉ nằm trong chú thích: cận trên.

| Nhóm | n | Còn lại (cận dưới) | Còn lại (cận trên) |
|---|---:|---:|---:|
| Tất cả | 400 | 0.885 | **0.945** |
| Mốc hỏi trước 2019 | 383 | 0.885 | 0.948 |
| Mốc hỏi từ 2019 | 17 | 0.882 | 0.882 |
| business | 50 | 0.920 | 0.920 |
| career | 50 | 0.880 | 0.920 |
| media_arts | 50 | 0.960 | 0.960 |
| military | 50 | 0.560 | 0.940 |
| person | 50 | 1.000 | 1.000 |
| place | 50 | 0.940 | 0.940 |
| politics | 50 | 0.840 | 0.880 |
| sports | 50 | 0.980 | 1.000 |

Nhóm military khác biệt lớn giữa hai cận vì đáp án nằm trong bảng danh sách chỉ huy (extracts bỏ bảng).

**Nhận xét**
- Sau gần 5 năm chỉnh sửa, **88.5–94.5%** đáp án cũ vẫn còn trong trang hiện tại. Wikipedia thường viết lại câu "hiện là X" thành "X đến 2024, sau đó Y", nên lịch sử nằm sẵn trong văn bản. Tải lại cả trang chỉ mất tối đa khoảng **5.5–11.5%** thông tin cũ.
- Phần "mất" gồm cả đáp án bị xóa thật (ví dụ danh sách thị trưởng Karlsøy, Loveland) lẫn đáp án đổi cách viết (`Lt . Cmdr`, `Ottawas central railway station`), nên lượng mất thật còn thấp hơn con số này.
- **Hệ quả:** kho phiên bản (đóng `end_time` thay vì xóa) chỉ bổ sung tối đa khoảng 5.5–11.5% thông tin lịch sử so với replace-all trên dữ liệu Wikipedia. Lợi thế chính của Cơ chế 3 trên Wikipedia là chi phí nạp (mục 2), không phải giữ lịch sử.

**Hạn chế riêng của phép đo này:** bộ 400 câu chủ yếu hỏi mốc lịch sử xa (383/400 trước 2019), chỉ 17 câu từ 2019, nên chưa phản ánh tốt các thay đổi gần đây. So khớp chuỗi đáp án không chứng minh thông tin còn gắn đúng mốc thời gian, chỉ chứng minh chuỗi còn xuất hiện.

## 4. Ba cách nhận biết phần đã đổi: hash chunk, hash câu, ghép mờ

**Cách đo.** Cùng dữ liệu và cách chia chunk theo đoạn như mục 2. Với mỗi chunk của bản sau:
- **A) Hash chunk:** chuẩn hóa rồi so hash với chunk của bản trước; không trùng thì phải xử lý.
- **B) Hash câu:** tách câu, so hash từng câu với tập câu của cả bản trước; chunk chỉ phải xử lý nếu có ít nhất một câu mới. Cách này không phụ thuộc ranh giới chunk.
- **C) Ghép mờ:** với chunk có câu mới, tìm chunk cũ giống nhất (Jaccard trên 3-gram từ) và chia theo độ giống: ≥0.8 (sửa nhỏ), 0.5–0.8 (sửa lớn), <0.5 (đoạn mới).

| | Một lần sửa nhỏ (300 cặp, 22,149 chunk) | Bản 2021 so với nay (56 trang, 2,302 chunk) |
|---|---:|---:|
| A) chunk phải xử lý | 1.2% (0.87/cặp) | 65.3% (26.8/cặp) |
| B) chunk phải xử lý | 1.2% (0.86/cặp) | 64.2% (26.4/cặp) |
| B) tỉ lệ từ thật sự mới trong chunk phải xử lý | 54.6% | 78.3% |
| C) ghép được, sửa nhỏ (≥0.8) | 46.3% | 19.6% |
| C) sửa lớn (0.5–0.8) | 22.2% | 19.0% |
| C) coi như đoạn mới (<0.5) | 31.5% (257 chunk) | 61.4% (1,479 chunk) |

**Nhận xét**
- Khi chia theo đoạn, hash chunk (A) và hash câu (B) cho gần như cùng kết quả (chênh 0.01 chunk/cặp). Lệch ranh giới chunk không phải vấn đề lớn với dữ liệu này, nên hash chunk theo đoạn chưa quá chặt như lo ngại ở một lần sửa nhỏ.
- Hash câu chỉ có ích ở chỗ thu hẹp phạm vi: trong chunk phải xử lý, chỉ khoảng một nửa số từ (một lần sửa nhỏ) là mới, nên có thể chỉ đưa các câu đổi vào LLM thay vì cả chunk.
- Khoảng cách dài: trang bị viết lại nhiều, 64–65% chunk phải xử lý dù dùng cách nào, và 61% chunk có câu mới không có chunk cũ nào giống (≥0.5). Lợi thế chi phí gần như mất và phần lớn chunk không có liên kết phiên bản.
- Ghép mờ (C) có vai trò liên kết phiên bản, không phải tiết kiệm chi phí: khi sửa nhỏ, khoảng 46% chunk có câu mới ghép được với chunk cũ giống ≥0.8.

**Cách chia chunk của TimeQA (suy từ dữ liệu, 39,035 chunk).** Mỗi đoạn được cắt thành các cửa sổ liên tiếp tối đa 100 từ, không chồng lấn. Vì vậy 23.9% chunk dài đúng 100 từ, 32.1% không kết thúc ở cuối câu, 15.8% bắt đầu giữa câu. Chunk có thể lấy từ câu 1 đến nửa câu 4.

**Đo lại hash câu cho đúng.** Bản đo trên tách câu bên trong từng chunk nên câu ở hai đầu chunk là mảnh cắt dở. Bản đo lại ghép các cửa sổ về đoạn đầy đủ, tách câu rồi đánh dấu cửa sổ nào chứa câu mới:

| | Một lần sửa nhỏ | Bản 2021 so với nay |
|---|---:|---:|
| A) hash chunk phải xử lý | 1.2% | 65.3% |
| B) hash câu trên đoạn đầy đủ phải xử lý | 1.0% | 60.6% |
| Tỉ lệ từ mới trong chunk phải xử lý | 51.7% | 77.4% |

Hash câu trên đoạn đầy đủ tốt hơn hash chunk một chút (giảm khoảng 17% số chunk khi sửa nhỏ, 4.7 điểm khi khoảng dài), nhưng vẫn không đáng kể; kết luận chung không đổi.

**Kiểm chứng cách chia chunk của TimeQA** (1,501 trang đầu của `pages.jsonl`, 39,035 chunk):
- 29,761 chunk **không** đứng sau một chunk dài đúng 100 từ trong cùng mục: 0% bắt đầu bằng chữ thường, tức bắt đầu ở đầu đoạn.
- 9,274 chunk đứng sau một chunk dài đúng 100 từ trong cùng mục: 66% bắt đầu bằng chữ thường, tức là phần tiếp nối giữa câu.
- 29,724 chunk ngắn hơn 100 từ: 88% kết thúc bằng dấu cuối câu (phần còn lại thường là tiêu đề, danh sách, trích dẫn).
- Chồng lấn giữa các cửa sổ liên tiếp gần như không có (140/9,274, nhiều khả năng trùng ngẫu nhiên).
- Trường `context` là một chuỗi liền không có dấu xuống dòng; ranh giới đoạn chỉ còn trong danh sách `paragraphs` (mỗi phần tử là một chunk kèm `title` mục). Có thể dựng lại đoạn từ chunk bằng quy tắc "chunk dài đúng 100 từ rồi đến chunk cùng mục là phần tiếp nối", nhưng đây là heuristic (đoạn dài đúng 100 từ sẽ bị nhầm).

**Kiểm chứng chia chunk nội bộ trong đoạn** ([`scripts/verify_timeqa_chunking.py`](../../scripts/verify_timeqa_chunking.py)). Ghép chunk thành nhóm (chunk dài đúng 100 từ rồi đến chunk cùng mục không kết thúc ở cuối câu thì nối vào nhóm trước), rồi so mỗi nhóm với các đoạn của bản Wikipedia đầu 2021 (60 trang, 1,384 nhóm, so khớp Jaccard 3-gram từ ≥ 0.8):

| Kết quả | Số nhóm | Tỉ lệ |
|---|---:|---:|
| Khớp đúng 1 đoạn Wikipedia | 855 | 61.8% |
| Khớp 2 đoạn Wikipedia liền kề gộp lại | 72 | 5.2% |
| Không khớp (khác phiên bản, làm sạch wikitext, bảng/danh sách) | 457 | 33.0% |

Kết luận: phần lớn nhóm khớp đúng một đoạn, nhưng **chưa chứng minh được** chunk của TimeQA không bao giờ gộp hai đoạn: 5.2% khớp hai đoạn gộp (có thể do TimeQA gộp đoạn ngắn, cũng có thể do cách mình tách đoạn từ wikitext), và 33% không khớp được vì sai khác phiên bản hoặc cách làm sạch. Thiết kế không nên dựa vào giả định "một chunk chỉ thuộc một đoạn".

**Hạn chế riêng của phép đo này:** chưa có đáp án đúng cho việc ghép (chưa biết cặp nào thật sự là cùng một đoạn), nên chưa đo được độ chính xác của ghép mờ, mới đo phân bố độ giống. Ngưỡng 0.8 và 0.5 là tùy chọn, chưa tinh chỉnh. Tách câu bằng regex thô, làm sạch wikitext gần đúng, và mẫu khoảng dài chỉ 56 trang.

## 5. Wikipedia chỉ ra chỗ đổi như thế nào (ví dụ thật)

Gọi API với hai lần sửa của trang Toungoo dynasty (revid 1273389748 và 1274026906, ngày 2025-02-05). Ghi chú của người sửa: "incorrect date given as per sources". Phản hồi `compare` có thông tin chung (`fromrevid`, `torevid`, `totimestamp`, `tocomment`) và `body` là bảng HTML diff. Đoạn đổi hiển thị:

```
CŨ : ... Taungoo Dynasty (<del class="diffchange">1485–1569</del>) at Taungoo ...
MỚI: ... Taungoo Dynasty (<ins class="diffchange">1485–1599</ins>) at Taungoo ...
```

Cả đoạn dài không đổi, chỉ một con số. Trên cùng trang, hai bản gần đó có ghi chú "wl" và "all sources say empire, not dynasty", cho thấy ghi chú của người sửa không đủ tin cậy để phân loại, cần LLM đọc diff.

## 6. Sự kiện có được trang khác nhắc lại không

**Cách đo.** Với mỗi câu trong bộ 400 câu (395 câu có tên chủ thể và đáp án đủ dài để so khớp), tìm trong cả 4,815 trang của `pages.jsonl` xem có trang **khác** chứa cả tên chủ thể và đáp án trong cửa sổ 300 ký tự (sau chuẩn hóa chữ thường, bỏ dấu và dấu câu) không. Đây là cận trên của "sự kiện được nhắc lại", vì nhắc cùng chủ thể và đáp án gần nhau chưa chắc là cùng một phát biểu.

| Chỉ số | Giá trị |
|---|---:|
| Câu có ít nhất một trang khác nhắc lại | 30/395 (7.6%) |
| Số trang khác trung bình trong các câu đó | 1.57 |
| Câu mà trang nhắc lại nằm trong bộ eval (204 trang) | 1 |
| Theo domain (có nhắc lại/tổng) | politics 9/50, sports 6/50, place 5/48, person 5/50, military 3/50, career 1/49, business 1/50, media_arts 0/48 |

Mẫu 10 câu cho thấy nhiều ca không phải cùng phát biểu: ví dụ Inter Milan (P286, Roberto Mancini) được trang Sarri, Allegri nhắc vì họ là người kế nhiệm, và Quim Torra được trang Laura Borràs nhắc trong ngữ cảnh khác.

**Nhận xét:** mâu thuẫn chéo trang chỉ có tiềm năng ở khoảng 7.6% câu (cận trên), và gần như toàn bộ trang nhắc lại **không nằm** trong 204 trang của bộ eval, nên muốn thử phải nạp thêm trang. Không đủ lớn để làm trọng tâm của Cơ chế 3 trên dữ liệu này.

**Hạn chế riêng của phép đo này:** so khớp chuỗi trong cửa sổ cố định, không hiểu ngữ nghĩa; chỉ xét câu có tên chủ thể và đáp án dài từ 4 ký tự; chưa thử cửa sổ khác.

## 7. Diff giữa hai bản cách xa nhau, và TimeQA ứng với bản nào

**API `compare` so được hai revision bất kỳ**, không chỉ hai bản liền kề. Thử với trang Toungoo dynasty: bản đầu 2021 (revid 1000035623, 2021-01-13) so với bản mới nhất (revid 1366708928, 2026-07-29), giữa hai bản có 153 lần sửa. Diff trả về 116 dòng bị xóa, 94 dòng thêm, 375 chỗ đổi mức từ. Vậy diff một lần từ bản cũ đến bản mới cho kết quả cuối giống nhau và rẻ hơn việc xử lý từng lần sửa một (đoạn bị sửa nhiều lần chỉ xử lý một lần).

**TimeQA không có số hiệu bản (revid).** Mình thử tìm bản Wikipedia khớp nhất với văn bản TimeQA trên 6 trang (độ chứa 3-gram của văn bản TimeQA trong bản wikitext đã làm sạch, thử 17 đến 29 bản mỗi trang trong khoảng 2020-06 đến 2022-12):

| Trang | Khớp cao nhất | Bản khớp nhất |
|---|---:|---|
| Toungoo dynasty | 0.963 | 2021-08 đến 2021-09 |
| Alex McLeish | 0.972 | 2022-04 đến 2022-05 (nhưng đường khớp gần như phẳng từ 2021-03) |
| Tommy Flowers | 0.985 | 2021-05 |
| Nora Ephron | 0.949 | 2021-05 |
| Atlético Madrid | 0.969 | 2021-05 đến 2021-08 |
| Roger Moore | 0.963 | 2021-04 đến 2021-06 |

Kết luận: TimeQA ứng với một bản Wikipedia khoảng **từ đầu đến giữa năm 2021** (cao nhất thường quanh 2021-04 đến 2021-09), nhưng **không xác định được một revid duy nhất**: đường khớp phẳng trên các trang ít thay đổi, và độ khớp tối đa chỉ 0.95 đến 0.985, không bao giờ 1.0 vì văn bản TimeQA đã qua xử lý (tách từ, bỏ bảng, bỏ danh sách). Giả định trước đó "bản đầu 2021 (2021-01-13) là S0" lệch vài tháng, có thể góp phần vào 33% nhóm chunk không khớp ở mục 4.

**Hệ quả cho thiết kế:** không thể lấy diff chính xác giữa văn bản TimeQA và bản mới. Phương án gọn: tự dựng S0 từ một revid Wikipedia cố định (ví dụ bản gần 2021-06-01), chia chunk bằng cùng quy tắc, rồi dùng diff API từ revid đó. Phần nhãn chunk đúng của TimeQA không dùng được nguyên cho S0 này, nên đánh giá Cơ chế 3 dùng đáp án chuỗi thay vì id chunk.

## Hạn chế của phép đo

- Làm sạch wikitext là gần đúng (regex), không giống pipeline tạo chunk thật của TimeQA; con số tuyệt đối có thể lệch, xu hướng thì ổn định.
- Cặp liên tiếp chọn có lọc (không bot, không revert, 20–3000 byte), nên loại sửa cực nhỏ và sửa rất lớn; mẫu khoảng dài chỉ 56 trang.
- Phân loại đính chính chỉ theo comment, chưa đối chiếu Wikidata hay đọc diff.
- Chưa đo chi phí gọi LLM thực tế, mới đo số chunk giữ nguyên.
