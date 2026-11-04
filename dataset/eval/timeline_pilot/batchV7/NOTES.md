# batchV7 (valid set, seed 7207, GUIDE_v7)

10 trang từ `reserved_valid.json`, do session chính dựng, chạy 20 haiku song song cùng V8 rồi tự đọc kiểm. Haiku 413 mốc; sau vá 425 (+12). `DIR=sub check.py` = 0 lỗi, `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV78.py` (chung V7 và V8; chạy lại ghi đè `rev/` từ `sub/`).

| Trang | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|
| Esther_Ayuso | 15 | 0 | 0 | 15 |
| Han_dynasty | 61 | 5 | 0 | 66 |
| Healy_Hall | 26 | 2 | 0 | 28 |
| Leimen_Baden | 36 | 0 | 0 | 36 |
| Max_Planck_Institute_for_Astronomy | 18 | 3 | 0 | 21 |
| Monica_s_Gang | 74 | 0 | 0 | 74 |
| Nana_Okada | 47 | 0 | 0 | 47 |
| Security_Service_of_Ukraine | 106 | 0 | 0 | 106 |
| Sherif_Ashraf | 14 | 0 | 0 | 14 |
| Stord | 16 | 2 | 0 | 18 |

## Mốc thêm
- Han_dynasty (100 chunk; `gap.py` không bắt được năm TCN nên mình dò tay các đoạn có "BC/AD/CE"): hành trình Trương Khiên -0138 (`approximate_date`, năm dương lịch thiên văn: 139 TCN = -0138), lũ Hoàng Hà 11, Phật giáo được nhắc lần đầu 65, trận Quan Độ 200, trận Xích Bích 208.
- Max_Planck_Institute_for_Astronomy: IMPRS 2005, Haus der Astronomie thành lập 2009 và khánh thành 2011-12. Stord: Leirvik thành thị trấn 1997, tai nạn Atlantic Airways 2006-10-10. Healy_Hall: Healy làm hiệu trưởng Georgetown 1873, Georgetown Historic District 1967-05-28.

## Không ghi (quyết định có chủ đích)
- Esther_Ayuso: ngày sinh hai con (1990, 1991) theo quy ước không ghi sinh con.
- Security_Service_of_Ukraine: thống kê nhân sự, phản ứng và báo cáo của tổ chức khác; danh sách người đứng đầu đã ghi đủ (106 mốc).
- Monica_s_Gang: thông báo kế hoạch (trò chơi Zeebo 2010, mở lại công viên 2015) và truyện phái sinh có chủ ngữ không rõ.
- Sherif_Ashraf: 70 bàn mùa 2006-07 và số áo (thống kê), "Egyptian Cup 2008" của HJK (nguồn tự mâu thuẫn).
- Han_dynasty: ngày mất trong ngoặc của nhân vật phụ (chỉ ghi khi là sự kiện triều Hán).

## Ghi chú
- Haiku V7 và V8 đều không có lỗi `check.py` ở `sub/`; chất lượng thấp ở chỗ bỏ sót mốc đơn trong văn xuôi dài, như các đợt trước.
