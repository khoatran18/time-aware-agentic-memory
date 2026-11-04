# Hướng dẫn viết timeline vàng (đọc kỹ, làm đúng)

Đầu vào: một trang Wikipedia đã cắt thành chunk, mỗi chunk bắt đầu bằng dòng `=== CHUNK <chunk_id> ===`.
Nhiệm vụ: liệt kê MỌI sự kiện có ngày trong trang, theo schema JSON dưới. Chỉ dùng thông tin có trong chunk, không dùng kiến thức ngoài.

## Sự kiện là gì
- Một thay đổi hoặc việc xảy ra ở một thời điểm (năm/tháng/ngày) gắn với thực thể chính của trang: đổi chức vụ, chuyển nơi làm/ở, thành lập, sở hữu, đổi tên, phát hành/ra mắt, kết hôn, học, nhận giải, mất... Khoảng thời gian (1950-1960) là hai sự kiện: bắt đầu và kết thúc, chỉ khi văn bản nêu cả hai mốc.
- Chỉ ghi sự kiện văn bản có NÊU NGÀY (ít nhất năm). Sự kiện nhắc mà không có ngày: đưa vào `undated_mentions`, không vào `events`.
- Một sự kiện nhắc ở nhiều chunk chỉ ghi MỘT lần (nhiều mục trong evidence).
- Không bỏ sót: đọc từng chunk từ đầu đến cuối. Không gộp hai sự kiện khác ngày thành một. Không bịa.

## Schema
{"page_id": "...",
 "events": [
  {"id": "e1", "date": "1991" | "1991-05" | "1991-05-14", "grain": "year|month|day",
   "track": "role|affiliation|location|ownership_structure|work|naming|family|education|other",
   "label": "nhãn ngắn tự do, bắt buộc nếu track=other, còn lại có thể để rỗng",
   "text": "mô tả ngắn tiếng Anh ~10 từ",
   "evidence": [{"chunk_id": "...#N", "role": "both|date|description", "quote": "trích NGUYÊN VĂN từ chunk"}]}
 ],
 "undated_mentions": ["..."]}

- `date`: đúng mức độ mịn văn bản nêu (chỉ có năm thì ghi năm). Sắp `events` theo ngày tăng dần, id e1, e2... theo thứ tự đó.
- `evidence`: `both` = chunk có cả ngày và mô tả sự kiện; `date` = chunk chỉ có ngày; `description` = chunk chỉ có phần mô tả (không có ngày của sự kiện đó). Cần ít nhất một chunk `both`, hoặc một cặp `date`+`description`. Nếu nhiều chunk `both` cùng nêu thì ghi hết.
- `quote`: cắt nguyên văn liền mạch (dưới 25 từ) có trong chunk; không sửa chữ.

## Track (chọn một)
role = chức vụ, nhiệm kỳ, quân hàm, chỉ huy | affiliation = nơi làm việc, đội, đảng, tổ chức, giải đấu | location = nơi ở, trụ sở, quốc gia | ownership_structure = sở hữu, vận hành, công ty mẹ, nhà xuất bản, hãng đĩa | work = sản phẩm người/tổ chức làm ra (phát hành, trình diễn, dự án, công trình) | naming = tên chính thức, đổi tên | family = hôn nhân/gia đình | education = học tại | other = còn lại (kèm label).
Mơ hồ thì ưu tiên role > affiliation > work. Đoạn tiêu đề mục (sau dấu `|`) là gợi ý, không phải nhãn.
