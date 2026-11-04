# Hướng dẫn viết timeline vàng v2 (đọc kỹ, làm đúng)

Đầu vào: một trang Wikipedia đã cắt thành chunk, mỗi chunk bắt đầu bằng dòng `=== CHUNK <chunk_id> ===`.
Nhiệm vụ: liệt kê MỌI sự kiện có ngày của thực thể chính của trang, theo schema JSON dưới. Chỉ dùng thông tin trong chunk, không dùng kiến thức ngoài. Đọc từng chunk từ đầu đến cuối, không bỏ sót.

## Sự kiện là gì
- Một việc xảy ra hoặc một thay đổi ở một thời điểm gắn với thực thể chính: sinh, mất, thành lập, đổi chức vụ/nơi làm/nơi ở, sở hữu, đổi tên, phát hành/ra mắt/hoàn thành, kết hôn, học, nhận giải, sáp nhập, giải thể...
- Chỉ ghi khi văn bản NÊU NGÀY (ít nhất năm). Mốc theo thập kỷ/thế kỷ ("1360s", "the 1930s", "17th century", "early 2000s") KHÔNG ghi vào `events`; đưa vào `undated_mentions`.
- Khoảng thời gian có cả hai mốc ("1955-1959", "from 1942 to 1944") = HAI sự kiện: một cho mốc bắt đầu, một cho mốc kết thúc (cùng `text` kiểu "began ..." / "ended ..."). Chỉ có một mốc thì một sự kiện.
- Hai việc khác nhau xảy ra cùng ngày = hai sự kiện riêng (ví dụ nhận hai huy hiệu cùng ngày, đóng cửa và chuyển giao cùng ngày). Cùng một việc nhắc ở nhiều chunk = MỘT sự kiện với nhiều mục `evidence`.
- KHÔNG ghi: (1) bối cảnh không thuộc thực thể chính (một nhà thờ khác, một đảng khác lên nắm quyền...); (2) số đo/thống kê/trạng thái "as of" (số thành viên, cường độ sáng); (3) việc dự kiến/chưa xảy ra ("planned to", "expects to"); (4) mô tả chung không gắn mốc.
- Nguồn tự mâu thuẫn (hai ngày khác nhau cho cùng việc, ngày kết thúc trước ngày bắt đầu...): ghi nguyên văn từng mục, thêm `"flag": "source_inconsistent"` vào các sự kiện đó.
- `undated_mentions`: chỉ gồm SỰ KIỆN của thực thể có nhắc nhưng không có ngày (và mốc theo thập kỷ). Mô tả chung, đặc điểm, địa điểm... không đưa vào.

## Schema
{"page_id": "...",
 "events": [
  {"id": "e1", "date": "1991" | "1991-05" | "1991-05-14", "grain": "year|month|day",
   "track": "role|affiliation|location|ownership_structure|work|naming|family|education|other",
   "label": "nhãn ngắn tự do; bắt buộc nếu track=other",
   "text": "mô tả ngắn tiếng Anh ~10 từ",
   "evidence": [{"chunk_id": "...#N", "role": "both|date|description", "quote": "trích NGUYÊN VĂN từ chunk"}],
   "flag": "tùy chọn"}
 ],
 "undated_mentions": ["..."]}

- `date`: đúng mức độ mịn văn bản nêu, định dạng ISO (YYYY, YYYY-MM, YYYY-MM-DD). Sắp theo ngày tăng dần; id e1, e2... theo thứ tự đó.
- `evidence.role`: `both` = chunk có cả ngày và mô tả sự kiện; `date` = chunk chỉ có ngày; `description` = chunk chỉ có phần mô tả, KHÔNG chứa ngày của sự kiện đó. Cần ít nhất một chunk `both`, hoặc một cặp `date`+`description`.
- `quote`: cắt nguyên văn liền mạch, dưới 25 từ, đúng như trong chunk (giữ khoảng trắng và dấu như bản gốc); với `date`/`both` phải chứa ngày (ít nhất năm) của sự kiện.

## Track (chọn một)
role = chức vụ, nhiệm kỳ, quân hàm, chỉ huy, giám đốc | affiliation = nơi làm việc, đội, đảng, tổ chức, giải đấu, gia nhập/rời tổ chức | location = nơi ở, trụ sở, quốc gia, chuyển địa điểm | ownership_structure = sở hữu, vận hành, công ty mẹ, nhà xuất bản, hãng đĩa, chuyển giao quản lý | work = sản phẩm/công trình/chương trình người hoặc tổ chức làm ra (phát hành, trình diễn, xây dựng, hoàn thành, dự án) | naming = tên chính thức, đổi tên | family = hôn nhân/gia đình | education = học tại, tốt nghiệp | other = còn lại, kèm label (ví dụ birth, death, award, honour, founding, event).
Mơ hồ thì ưu tiên role > affiliation > work. Tiêu đề mục (sau dấu `|`) chỉ là gợi ý.

## Quyết định bổ sung sau mẫu thử 10 trang (2026-11-04)
- KHÔNG ghi: ngày của sắc lệnh/luật chỉ được liệt kê mà không nêu nội dung thay đổi gì; ngày sinh của con cái; tiểu sử cá nhân của người được nhắc trong trang của một chức vụ/tổ chức (chỉ ghi mốc nhậm chức/rời chức trong chức vụ đó).
- GHI: khoảng thời gian dùng huy hiệu/biểu tượng (hai sự kiện bắt đầu và kết thúc); sự kiện của thực thể tiền thân và danh sách chỉ huy/lãnh đạo của nó khi trang liệt kê chung.
- Không ghi thống kê theo mùa/năm (số trận, số lần) và mốc không đặt được (mùa "1941-42") thành sự kiện; mốc không đặt được đưa vào undated_mentions.
