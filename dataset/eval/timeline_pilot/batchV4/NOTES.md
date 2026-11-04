# batchV4 (valid set, seed 7204, GUIDE_v7)

10 trang từ `reserved_valid.json`. Session B dựng batch và chạy haiku, hết hạn mức giữa chừng; session chính đọc kiểm và vá (`tools/patch_bV4.py`). Haiku 283 mốc; sau vá 310 (+27, −0). `DIR=sub check.py` = 0 lỗi, `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy 10 trang.

| Trang | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|
| Chelyabinsk | 12 | 11 | 0 | 23 |
| Choi_Yoo_jung_singer | 18 | 0 | 0 | 18 |
| FC_Flora | 40 | 2 | 0 | 42 |
| Helmut_Lang_fashion_brand | 44 | 1 | 0 | 45 |
| HMAS_Cairns_J183 | 17 | 1 | 0 | 18 |
| Igor_Grabar | 49 | 6 | 0 | 55 |
| International_Association_for_Political_Science_Students | 17 | 0 | 0 | 17 |
| Vladimir_Bukovsky | 54 | 6 | 0 | 60 |
| Willy_Hernang_mez | 28 | 0 | 0 | 28 |
| Young_Girl_with_a_Flower_Basket | 4 | 0 | 0 | 4 |

## Mốc thêm
- Chelyabinsk (67 chunk, haiku chỉ 12 mốc): 1892 hoàn thành Samara-Zlatoust và khởi công Trans-Siberian, 1913 bảo tàng, 1930 và 1934 hai trường đại học, 1933 nhà máy máy kéo, 2007 trung tâm thương mại Gorky và bảo tàng thiết bị quân sự, 2011 Rodnik và thỏa thuận Beeline, 2013-02-15 thiên thạch.
- FC_Flora: sân A. Le Coq Arena mở rộng 2016 đến 2018 (hai mốc). Helmut Lang: 1997 chuyển sang New York. HMAS Cairns: 1938 Ủy ban Hải quân đề ra tàu phòng thủ đa năng.
- Grabar: 1897-01 bài báo bênh vực nghệ thuật tiên phong (cờ `approximate_date`), 1899 bài báo, 1918-06 quốc hữu hóa Tretyakov, 1921 giáo sư phục chế đầu tiên, 1926 bị thay bằng Shchusev, 1948 bị cuốn vào chiến dịch.
- Bukovsky: 1971-03-12 thư đăng trên The Times (`derived_date`), 1985 mở rộng thành American Foundation, 1987-03 thư của 10 nhà văn lưu vong, 2005-12-18 bài op-ed Washington Post, 2007-12-14 Yavlinsky ủng hộ, 2010-03-10 ký tuyên ngôn Putin must go.

## Không ghi (quyết định có chủ đích)
- Chelyabinsk: sự kiện thể thao đăng cai (2012, 2014, 2015, 2018) theo quy ước không ghi giải đấu; dân số theo năm; OKMO chuyển đi Omsk "sau 1962"; quà đồng hồ Olympic 1980; giá trị ảnh chụp 1914.
- FC_Flora: kết quả từng mùa giải vẫn ở `undated_mentions` (đúng GUIDE_v7).
- Grabar: cha mẹ bị bắt 1882 và bầu Quốc hội Hung 1869 (người khác); mục tài liệu tham khảo.
- Bukovsky: WPA lên án 1977 và rút lui 1983, Lệnh WFMH 1971 (sự kiện của tổ chức khác); phản ứng 1993; quỹ Gratitude 1998.
- Choi: "set to star in Cast: Age of Insiders in 2020" (kế hoạch).

## Ghi chú
- Haiku làm tốt các trang ngắn và trang có mục lịch sử rõ (Flora, Helmut Lang, Grabar, Bukovsky ghi trên 45 mốc); yếu nhất là trang địa danh có nhiều mục lặt vặt (Chelyabinsk).
- Session B ngừng ở bước kiểm `sub/` do hết hạn mức; phần đọc từng trang, vá và NOTES do session chính làm. Nếu B chạy lại, bảo B bỏ qua V4.
