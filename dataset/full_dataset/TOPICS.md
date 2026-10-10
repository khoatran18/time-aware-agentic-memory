# Chủ đề (`relation`) và `domain` của chunk

Ghi lại các vấn đề khi dùng `relation` của TimeQA làm bộ lọc chủ đề, và hướng đề xuất cho trường `domain_features.domain`. Số liệu đo trên các tập `hard` của `C/test`, `D/test`, `D/train`, `C/dev`. **Phần đề xuất ở mục 3 và 4 chưa chốt và chưa có code.**

## 1. `relation` là gì

`relation` là nhãn gắn vào mỗi **câu hỏi**, cho biết câu hỏi hỏi loại thông tin gì (một thuộc tính Wikidata). Nó không nằm trong văn bản trang. Có 71 chủ đề, danh sách đầy đủ ở `RELATIONS.md`.

| Câu hỏi | `relation` |
|---|---|
| What team was coached by Gary Mills in Dec 2001? | `P6087` (coach of sports team) |
| Lisa Marie Presley was married to which man in Oct 1995? | `P26` (spouse) |
| What position did Laurette Onkelinx hold in the early 2010s? | `P39` (position held) |

## 2. Hai vấn đề

### 2.1. Quá nhiều chủ đề

71 chủ đề quá mịn để làm bộ lọc. Lọc cứng mà gán sai chủ đề thì mất đáp án (kết quả rỗng), tệ hơn là không lọc. Cần gộp thành vài domain.

### 2.2. Mỗi trang gần như chỉ có một loại câu hỏi

| Đo | Kết quả |
|---|---|
| Số `relation` khác nhau trên mỗi trang (1,772 trang) | 99% chỉ có 1 |
| Số `relation` khác nhau trên mỗi chunk có đáp án (4,030 chunk) | 99% chỉ có 1 |

Ví dụ: trang `Gary_Mills_(footballer,_born_1961)` chỉ có câu hỏi `P6087`, không có câu hỏi về vợ hay học vấn, dù văn bản trang có thể nhắc tới. Đây là do cách chọn câu hỏi của dataset, không phải do nội dung văn bản. Văn bản thì đa chủ đề thật (trang Knox Cunningham nói cả học vấn, quân sự, chính trị, gia đình).

**Hệ quả:** lọc chunk theo `relation` của câu hỏi gần như là lọc luôn theo trang, tức là rò rỉ nhãn của bộ test và cho điểm cao giả. Vì vậy:
- `relation` chỉ dùng để **chia nhóm khi báo cáo điểm**, không dùng làm filter lúc truy xuất.
- `domain` của chunk phải do LLM gán từ **văn bản chunk**, không đọc từ file câu hỏi.

## 3. Đề xuất: 8 domain + `other`

Mỗi domain gồm các `relation` (P) sau. Bảng này là ánh xạ cố định `relation → domain` dùng để **báo cáo điểm** và để **kiểm chứng nhãn LLM** (so nhãn LLM gán cho chunk với domain suy ra từ `relation` của câu hỏi có đáp án nằm trong chunk đó). Không dùng khi xây kho. Tỉ lệ là phần trăm số câu trên `D/test.hard` (830 câu); relation không có trong bảng thì vào `other`.

| Domain | Mô tả (đưa vào prompt cho LLM) | `relation` (P: ý nghĩa) | Tỉ lệ |
|---|---|---|---|
| `business` | công ty, tổ chức: chủ sở hữu, điều hành, lãnh đạo, trụ sở, công ty mẹ/con | P127 owned by, P137 operator, P169 chief executive officer, P749 parent organization, P159 headquarters location, P355 subsidiary, P176 manufacturer, P488 chairperson, P1037 director/manager, P8047 country of registry, P366 use, P1830 owner of | 21% |
| `sports` | thể thao: đội, giải đấu, huấn luyện, sân nhà | P54 member of sports team, P6087 coach of sports team, P286 head coach, P641 sport, P118 league, P115 home venue, P2962 title of chess person, P1344 participant in | 19% |
| `career` | học vấn và nghề nghiệp của một người: nơi học, nơi làm việc, thành viên tổ chức | P108 employer, P69 educated at, P463 member of, P106 occupation, P937 work location, P1416 affiliation, P1075 rector | 16% |
| `person` | đời sống cá nhân: gia đình, nơi ở, quốc tịch, tên, giải thưởng, giam giữ | P26 spouse, P40 child, P551 residence, P27 country of citizenship, P1448 official name, P2561 name, P734 family name, P138 named after, P2632 place of detention, P166 award received | 14% |
| `politics` | chính trị, chức vụ nhà nước, đảng, người kế nhiệm | P39 position held, P102 member of political party, P6 head of government, P35 head of state, P1308 officeholder, P97 noble title, P1366 replaced by, P1365 replaces | 11% |
| `place` | địa điểm, lãnh thổ, công trình, hạ tầng | P17 country, P36 capital, P1376 capital of, P47 shares border with, P150 contains administrative territorial entity, P276 location, P121 item operated, P466 occupant, P559 terminus, P1435 heritage designation, P618 source of energy | 10% |
| `media_arts` | truyền thông, âm nhạc, xuất bản, nghệ thuật | P371 presenter, P449 original broadcaster, P264 record label, P175 performer, P123 publisher, P98 editor, P800 notable work, P608 exhibition history, P195 collection | 4% |
| `military` | quân đội: chỉ huy, quân hàm, binh chủng | P4791 commanded by, P410 military rank, P241 military branch | 4% |
| `other` | không thuộc các nhóm trên | P793 significant event, P710 participant, P5096 member of the crew of, ... | 1% |

Trên `D/train.hard`, `media_arts` lên 10% và `place` 14%. Trên `C/test.hard` (tập template, lệch về P54 và P39) thì `sports` 34%, `politics` 21%, `career` 21%. Các domain nhỏ như `military`, `media_arts` có thể gộp vào `other` nếu LLM gán không ổn định; cần xem khi chạy thử.

Đây là ánh xạ theo **ý nghĩa của relation**, không phải theo văn bản. Một số ranh giới mờ: P121/P466 (có thể là `business` hoặc `place`), P1075 rector (`career` hay `politics`), P166 award (`person` hay `media_arts`).

## 4. Đề xuất cho `domain` của chunk (chưa chốt)

- **Đơn vị chunk:** mỗi phần tử của `paragraphs` là một chunk (tối đa 100 từ). Mỗi chunk gắn **1 đến 3** nhãn, `domain` là danh sách. Prompt dặn chọn nhãn chiếm ưu thế trước, chỉ thêm nhãn khi đoạn thực sự nói về chủ đề đó.
- **Ai gán:** LLM, trong cùng lệnh gọi đang trích mốc thời gian lúc ingestion (thêm một trường vào `ChunkTime`), không tốn thêm lệnh gọi. Nó thấy cả lô chunk của trang nên có ngữ cảnh.
- **Danh sách đóng, dùng chung:** cùng một danh sách nhãn (mục 3) cho prompt ingestion và prompt Profiler. Câu hỏi của người dùng được kiểm tra trên danh sách này: có manh mối rõ ("footballer", "politician") thì chọn một nhãn, không rõ thì `null` (không lọc).
- **Khớp lọc:** giữ chunk nào có chứa nhãn của câu hỏi (`in`, không phải `==`).
- **Kiểm chứng nhãn LLM:** như mục 3, chỉ ở bước đánh giá.

Ví dụ gán thử trang Knox Cunningham (đọc tay, để minh họa cái LLM sẽ phải làm):

| Chunk | Mục | Nội dung chính | Nhãn |
|---|---|---|---|
| 0 | Knox Cunningham | giới thiệu, chính trị gia Ulster Unionist | `politics` |
| 1 | Early career | gia đình, học Fettes và Cambridge | `person`, `career` |
| 2 | Early career | gia đình sở hữu đất, kinh doanh | `person`, `business` |
| 3 | Early career | 1931 đi làm, 1935 kết hôn, 1939 hành nghề luật, quân đội | `career`, `person`, `military` |
| 4 | Early career | sau chiến tranh: YMCA, hội đồng địa phương | `career` |
| 5-6 | Parliament | nghị sĩ 1955, thư ký riêng cho Macmillan | `politics` |
| 7 | Post-Parliamentary | nghỉ hưu 1970, Master của Drapers Company | `politics`, `career` |
| 8 | Post-Parliamentary | qua đời 1976 | `person` |
| 9 | Post-Parliamentary | cáo buộc liên quan Kincora | `other` |
| 10 | Sources | một dòng trích dẫn | không có nhãn (nên bỏ) |

## 5. Lưu ý

- **Lợi ích của filter chủ đề trên TimeQA có thể nhỏ:** câu hỏi nào cũng nêu tên thực thể nên BM25 và dense đã thu hẹp về đúng trang. Filter có ích hơn ở miền không có tên riêng rõ ràng (luật, tin tức). Cần đo ablation có và không có filter trên bộ local.
- **Danh sách nhãn ở mục 3 chỉ là đề xuất,** có thể gộp thêm hoặc đổi tên trước khi code.
- Việc cần sửa khi làm: `Extraction.domain` trong `query/profiler.py` đổi từ chuỗi tự do sang danh sách đóng; `passes_hard_filter` đổi `==` thành `in`; thêm trường nhãn (tối đa 3) vào `ChunkTime` và prompt `ingestion_time.md`.
