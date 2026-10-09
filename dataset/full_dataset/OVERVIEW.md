# Tổng quan dataset_enriched

## 1. Cấu trúc folder

```
dataset_enriched/
├── C/{dev,train,test}.{easy,hard}.jsonl     câu hỏi template
├── D/{train,test}.{easy,hard}.jsonl         câu hỏi người viết (không có dev)
├── pages.jsonl                              văn bản các trang, 4,815 trang
├── demo_page.json                           1 phần tử của pages.jsonl, thụt lề cho dễ đọc
├── RELATIONS.md                             số câu theo từng chủ đề (relation)
├── EVAL_PLAN.md                             kế hoạch bộ đánh giá (local và thật), cách chấm, chi phí
├── README.md                                mô tả chi tiết
└── OVERVIEW.md                              tóm tắt
```

- **Nhóm (C/D)** là thư mục, **tập (dev/train/test)** và **mức (easy/hard)** nằm trong tên file. Các thông tin này không lặp lại trong từng dòng.
- **easy / hard:** cùng một câu hỏi và đáp án, khác cách nêu thời gian. easy nêu khoảng tường minh ("from 2004 to 2005"), hard nêu mốc ngầm cần suy luận ("before Apr 2004", "in Dec 2004").
- Dữ liệu chỉ gồm câu **có đáp án**. Các câu không có đáp án và 520 câu hard không có trong A đã bị bỏ (xem `README.md`).

## 2. Số câu hỏi

Ghi dạng **easy / hard**:

| Nhóm | dev | train | test | Total |
|---|---:|---:|---:|---:|
| **C** (template) | 2,674 / 2,674 | 12,532 / 12,532 | 2,613 / 2,613 | 17,819 / 17,819 |
| **D** (người viết) | không có | 982 / 982 | 830 / 830 | 1,812 / 1,812 |
| **Tổng C + D** | 2,674 / 2,674 | 13,514 / 13,514 | 3,443 / 3,443 | **19,631 / 19,631** (39,262 dòng) |

Easy và hard là hai cách hỏi của cùng một tập câu hỏi, nên số câu khác nhau thực sự là 19,631.

### Chủ đề (relation)

Có **71 chủ đề** (thuộc tính Wikidata, trường `relation`). Số chủ đề có mặt theo từng tập: C dev 52, C train 70, C test 50, D train 70, D test 50.

5 chủ đề lớn nhất (số câu mỗi mức easy hay hard, cả C và D): P54 member of sports team (5,400), P39 position held (3,836), P108 employer (1,527), P69 educated at (1,056), P26 spouse (715). Bảng đầy đủ 71 chủ đề, chia theo nhóm và tập, ở `RELATIONS.md`.

## 3. File `.jsonl` của C và D

Mỗi file có nhiều dòng, mỗi dòng là một JSON gọn (JSON Lines). Cách xem một dòng cho dễ đọc: `head -n1 C/test.hard.jsonl | python3 -m json.tool`.

Ví dụ một dòng (rút gọn định dạng):

```json
{
  "idx": "/wiki/Charlotte_Fitch_Roberts#P106#0",
  "page_id": "/wiki/Charlotte_Fitch_Roberts",
  "relation": "P106",
  "q_index": 0,
  "question": "What was the occupation of Charlotte Fitch Roberts from 1881 to 1882?",
  "targets": ["graduate assistant"],
  "time_start": "1881",
  "time_end": "1882",
  "answers": [{"para": 5, "from": 66, "end": 84, "answer": "graduate assistant"}],
  "from": [364],
  "end": [382]
}
```

| Trường | Là gì | Dùng để làm gì |
|---|---|---|
| `idx` | Định danh câu hỏi: `<trang>#<relation>#<số thứ tự>` (ba phần ngăn bởi `#`) | Khoá duy nhất của câu hỏi trong một file |
| `page_id` | Tên bài Wikipedia chứa đáp án (dấu ngoặc là phần phân biệt tên bài) | Tra văn bản trang trong `pages.jsonl` |
| `relation` | Thuộc tính Wikidata của câu hỏi, ví dụ `P39` (position held), `P106` (occupation) | Lọc hoặc thống kê theo chủ đề |
| `q_index` | Số thứ tự câu hỏi trong A (từ 0), là số cuối của `idx`; có thể nhảy số vì câu không đáp án đã bị bỏ | Đối chiếu ngược với A |
| `question` | Câu hỏi (template ở C, người viết ở D) | Đầu vào của model |
| `targets` | Danh sách đáp án đúng (một câu có thể có nhiều đáp án) | Đáp án đúng, dùng làm nhãn |
| `time_start`, `time_end` | Khoảng thời gian của sự kiện đã gán nhãn trong A, chính xác đến tháng. Không phải mốc nêu trong câu hỏi hard | Lọc hoặc phân tích theo thời gian |
| `from`, `end` | Vị trí ký tự của từng đáp án trong `context` (list, cùng thứ tự `targets`): `context[from[k]:end[k]] == targets[k]`. Có ở mọi tập | Nhãn vị trí đáp án trong văn bản; kiểm tra đáp án |
| `answers` | Đáp án theo định dạng gốc của A: `{para, from, end, answer}`. `para` là chỉ số đoạn trong `paras` của A, `from`/`end` là vị trí trong đoạn đó | Chỉ để đối chiếu với A. Không dùng với `pages.jsonl` |

## 4. `pages.jsonl`: một dòng là một trang

4,815 dòng, mỗi dòng một trang Wikipedia, dùng chung cho mọi câu hỏi cùng `page_id` (nên văn bản không bị lặp lại trong từng câu hỏi).

| Trường | Là gì | Dùng để làm gì |
|---|---|---|
| `page_id` | Tên bài Wikipedia, khoá duy nhất | Khớp với `page_id` của câu hỏi |
| `context` | Toàn bộ văn bản trang (tiêu đề + các đoạn nối lại) | Văn bản trang dạng một chuỗi; `from`/`end` tính trên chuỗi này |
| `paragraphs` | Cùng nội dung chia thành `[{title, text}]` theo đoạn | Văn bản trang chia theo đoạn |

`context` và `paragraphs` lấy từ các dòng C/D, không phải từ `paras` của A (hai cách chia này khác nhau, xem `README.md`).

## 5. Cách ghép câu hỏi với trang

Tra theo `page_id`:

```python
import json
pages = {p['page_id']: p for p in map(json.loads, open('pages.jsonl'))}
for line in open('C/test.hard.jsonl'):
    r = json.loads(line)
    ctx = pages[r['page_id']]['context']
    ans = [ctx[f:e] for f, e in zip(r['from'], r['end'])]   # == r['targets']
```

Muốn bản có `context` và `paragraphs` ngay trong từng dòng (dạng dữ liệu gốc): `python preprocess/build_enriched.py --inline-pages --out dataset_enriched_inline`.
