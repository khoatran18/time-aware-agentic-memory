# dataset_enriched

Nhóm C (template) và D (người viết) của TSQA, mỗi dòng đã ghép thêm thông tin từ nhóm A. Sinh bởi `../preprocess/build_enriched.py` từ `../dataset/` (không sửa file gốc). Xem `../dataset/README.md` để biết A/B/C/D là gì. `demo_page.json` là một phần tử của `pages.jsonl` (trang Knox Cunningham), thụt lề cho dễ đọc.

```
C/{train,dev,test}.{easy,hard}.jsonl
D/{train,test}.{easy,hard}.jsonl        # D không có dev
pages.jsonl                              # 1 dòng / trang, 4,815 trang
demo_page.json                           # 1 phần tử của pages.jsonl, thụt lề
RELATIONS.md                              # số câu theo từng chủ đề (relation)
EVAL_PLAN.md                              # kế hoạch bộ đánh giá (local và thật), cách chấm, chi phí
```

Tất cả `.jsonl` là JSON Lines: mỗi file có nhiều dòng, mỗi dòng là một câu hỏi. Tổng 39,262 dòng. Xem một dòng cho dễ đọc: `head -n1 C/test.hard.jsonl | python3 -m json.tool`.

## Số câu hỏi

Số dòng của từng file (đếm bằng `wc -l`), ghi dạng **easy / hard**. Easy và hard có cùng số câu ở mọi tập.

| Nhóm | dev | train | test | Total |
|---|---:|---:|---:|---:|
| **C** (template) | 2,674 / 2,674 | 12,532 / 12,532 | 2,613 / 2,613 | 17,819 / 17,819 |
| **D** (người viết) | không có | 982 / 982 | 830 / 830 | 1,812 / 1,812 |
| **Tổng C + D** | 2,674 / 2,674 | 13,514 / 13,514 | 3,443 / 3,443 | **19,631 / 19,631** (39,262 dòng) |

Easy và hard là hai cách hỏi của **cùng** một tập câu hỏi (cùng `idx`, cùng đáp án), nên số câu khác nhau thực sự chỉ là 19,631, không phải 39,262.

## Những câu đã bỏ so với `../dataset/`

- **520 câu hard của C không có trong A** (373 train, 66 dev, 81 test).
- **5,710 dòng không có đáp án** (`targets == ['']`): C easy và C hard mỗi mức 1,776 / 347 / 384 (train/dev/test), D easy và D hard mỗi mức 189 / 159 (train/test). Muốn dùng các câu này thì lấy từ `../dataset/`.

Còn lại: C easy = C hard = 12,532 / 2,674 / 2,613 (train/dev/test); D easy = D hard = 982 / 830 (train/test). Mọi dòng đều có đáp án và đủ `time_start`, `time_end`, `answers`.

## Một dòng

`split` (train/dev/test), nhóm (C/D) và mức (easy/hard) lấy từ đường dẫn file, không lặp lại trong dòng.

`idx = "/wiki/Eliot_Engel#P69#0"` gồm 3 phần ngăn bởi `#`: trang Wikipedia, relation, thứ tự câu hỏi. Hai phần đầu ghép lại (`/wiki/Eliot_Engel#P69`) là `index` của A.

| Trường | Nguồn | Ý nghĩa |
|---|---|---|
| `idx`, `question`, `targets` | C/D gốc | Như file gốc |
| `page_id` | A (`link`) | Tên bài Wikipedia, khoá tra sang `pages.jsonl` (`pages[row['page_id']]`). Dấu ngoặc là phần phân biệt tên bài, ví dụ `/wiki/Gary_Mills_(footballer,_born_1961)`; `_` thay khoảng trắng |
| `relation` | A (`type`) | Wikidata property, ví dụ `P39` (position held), `P69` (educated at) |
| `q_index` | `idx` | **Số thứ tự của câu hỏi trong A** (đếm từ 0): câu này là phần tử thứ `q_index` của `A[split][index].questions`. Chính là số cuối của `idx`, tách sẵn thành số nguyên. Ví dụ `idx = ...#P69#2` thì `q_index = 2`. Vì các câu không có đáp án đã bị bỏ nên `q_index` của một trang có thể bị nhảy số (0, 1, 3, ...) |
| `time_start`, `time_end` | A | Khoảng thời gian của **sự kiện đã gán nhãn trong A**, chính xác đến tháng (ví dụ `Jan 1854`). **Không phải** mốc trong câu hỏi: ở hard, câu hỏi nêu một mốc nằm trong khoảng này (ví dụ hỏi "between Apr 1987 and Nov 1988" thì A ghi `1985`-`1989`) |
| `from`, `end` | C/D gốc (train), tính từ A (dev/test) | Offset đáp án trong `context` của `pages.jsonl` (list, cùng thứ tự `targets`): `context[from[k]:end[k]] == targets[k]`. Có ở **mọi split** (C/D gốc chỉ có ở train) |
| `answers` | A | `[{para, from, end, answer}]` nguyên dạng A. `para` là chỉ số đoạn trong `paras` của A (nhiều đoạn hơn `paragraphs` của `pages.jsonl` vì tách cả tiêu đề mục) và `from`/`end` là offset **trong đoạn đó**, nên không dùng trực tiếp với `pages.jsonl`. Dùng `from`/`end` ở trên để cắt `context` |

## pages.jsonl

`{page_id, context, paragraphs}`: văn bản trang, dùng chung cho mọi dòng cùng `page_id` (đã kiểm chứng giống hệt giữa C/D, easy/hard và các split).
- `context` và `paragraphs` **lấy từ các dòng C/D** (không lấy `paras` của A).
- `context`: title + text nối lại (`from`/`end` tính trên chuỗi này).
- `paragraphs`: cùng nội dung chia thành `[{title, text}]`.

**Tra cứu chỉ theo `page_id`.** `relation` và `q_index` thuộc về câu hỏi, không nằm trong `pages.jsonl` và không cần để tra: một trang có thể có nhiều relation (ví dụ `/wiki/Marcia_Bunge` có `P108` và `P69`) nhưng các relation đó dùng chung một văn bản trang. `relation` dùng để lọc theo chủ đề; `q_index` dùng để đối chiếu với A.

```python
import json
pages = {p['page_id']: p for p in map(json.loads, open('pages.jsonl'))}
for line in open('C/test.hard.jsonl'):
    r = json.loads(line)
    ctx = pages[r['page_id']]['context']
    ans = [ctx[f:e] for f, e in zip(r['from'], r['end'])]   # == r['targets']
```

Cần bản có `context` + `paragraphs` ngay trong từng dòng (dạng dữ liệu gốc): `python preprocess/build_enriched.py --inline-pages --out dataset_enriched_inline`.

## `from`/`end` ở cấp dòng và `answers`: dùng cái nào

- **`from`/`end` ở cấp dòng: dùng được với `pages.jsonl`.** Là offset trong `context`, nên `context[from[k]:end[k]] == targets[k]`. Không cần A.
- **`answers[].para/from/end`: không dùng được với `pages.jsonl`.** `para` là chỉ số trong `paras` của **A** và `from`/`end` là offset **trong đoạn đó**. `paras` của A không có trong folder này, và không có quy tắc nào đổi `para` thành chỉ số trong `paragraphs`. Trường này chỉ để đối chiếu ngược với A. Muốn vị trí đáp án thì dùng `from`/`end` ở cấp dòng.

## `paras` (A) khác `paragraphs` (C/D) thế nào

Cùng nội dung chữ nhưng chia khác nhau. Ví dụ `/wiki/Charlotte_Fitch_Roberts`:

```
A: paras (8 phần tử)                          C/D: paragraphs (5 phần tử, {title, text})
[0] 'Charlotte Fitch Roberts'                 [0] 'Charlotte Fitch Roberts' | ' Charlotte Fitch Roberts ( February 13 ...'
[1] 'Charlotte Fitch Roberts ( February ...'  [1] 'Life'                    | ' Roberts was born on February 13 ...'
[2] 'Life .'                  <- tiêu đề mục  [2] 'Education and career'    | 'Roberts attended Wellesley College ...'
[3] 'Roberts was born on ...'                 [3] 'Education and career'    | '.'
[4] 'Education and career .' <- tiêu đề mục   [4] 'Education and career'    | ' Awards and professional bodies . Roberts was made ...'
[5] 'Roberts attended Wellesley ...'
[6] 'Awards and professional bodies .'
[7] 'Roberts was made a fellow ...'
```

- A tách tiêu đề mục thành phần tử riêng; C/D đưa tiêu đề mục vào trường `title`. Vì thế số phần tử và chỉ số khác nhau: `para = 5` của A ứng với `paragraphs[2]`, không có quy tắc chung để đổi.
- Cách chia của C/D hơi thô: `paragraphs[4]` mang `title = 'Education and career'` dù văn bản đã sang mục "Awards and professional bodies" (tiêu đề mục dính vào đầu `text`), và `paragraphs[3]` chỉ chứa dấu `.`. Nhiều `text` có thêm khoảng trắng đầu, nên offset trong từng đoạn của C/D lệch với A.
- Đáp án `graduate assistant` nằm ở `paras[5][66:84]` của A, và ở `context[364:382]` trong `pages.jsonl`: cùng một chỗ trong văn bản.

## Thông tin của A chưa mang vào

- **`succ`:** chỉ có ở 1,235 trong 5,061 phần tử của A, chưa rõ nghĩa.
- **`paras`:** thay bằng `context`/`paragraphs` của `pages.jsonl` (cùng nội dung chữ, cách chia khác).
- **Các câu không có đáp án** của A (và của C/D): đã bỏ.

Các trường còn lại của A đều đã có: `index` nằm trong `idx`, `link` thành `page_id`, `type` thành `relation`, mốc thời gian thành `time_start`/`time_end`, đáp án thành `answers` và `from`/`end`.

## Khoá ánh xạ sang A

`idx = "<index>#<i>"` → `A[split][index]["questions"][i]`. Phải kèm `split` vì có 2 `index` xuất hiện ở hai split. Offset trong `context` = vị trí bắt đầu đoạn `para` trong `' '.join(paras)` + `from` (khớp 100% với `from`/`end` gốc ở train).
