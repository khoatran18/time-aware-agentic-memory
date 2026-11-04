# batchV3 (valid set, seed 7203, GUIDE_v7)

10 trang từ `reserved_valid.json` (không trùng V1/V2: mk_batch loại trang đã có trong `*/in`). Haiku 269 mốc; sau vá 271 (+6, −4). `DIR=rev check.py` = 0 lỗi; `gap.py` đã chạy cả 10 trang. Patch: `tools/patch_bV3.py`.

| Trang | Haiku | Thêm | Bỏ | Sau sửa |
|---|---|---|---|---|
| Carles_Puigdemont | 52 | 1 | 0 | 53 |
| Amber_Diceless_Roleplaying_Game | 6 | 2 | 0 | 8 |
| Nik_Stauskas | 65 | 0 | 3 | 62 |
| Newton_D_Baker_House | 25 | 0 | 0 | 25 |
| Gordon_W_McKay | 32 | 0 | 0 | 32 |
| Lee_Nogan | 22 | 1 | 0 | 23 |
| John_Campbell_Brown | 24 | 1 | 0 | 25 |
| EMD_SDP40F | 12 | 0 | 1 | 11 |
| Tibbers_Castle | 14 | 1 | 0 | 15 |
| Evandro_Brand_o | 17 | 0 | 0 | 17 |

## Sửa lỗi (check.py báo 5 lỗi ở `sub/`)
- EMD e3: quote không chứa năm → "entered revenue service on June 22 , 1973".
- Campbell Brown e9 (1970): quote `both` thiếu 1970 → dùng "research assistant in 1968–70 and lecturer from 1970".
- Stauskas e38: quote `description` chứa 2014 → cặp `date` (chunk 48, có "2014 NBA draft") + `description` (chunk 47, "On April 15 ..."), cờ `derived_date`. Stauskas e60: quote `both` thiếu 2019 → cặp `date` (04 Feb 2019) + `description` ("waived by the Pacers on February 8"), `derived_date`.
- Tibbers e12: text chứa "21st century" bị báo là mốc thế kỷ → text "Site surveyed", quote "surveyed in 1912".

## Mốc bỏ
- EMD e5 (1974 EMD ngừng chế tạo): khoảng "1973–1974" là một hoạt động → một mốc ở 1973 (e2).
- Stauskas e19 (kỷ lục 79 cú ba điểm của sinh viên năm nhất), e52 (lần đầu 20 điểm hai trận liền), e21 (bắt đầu Puerto Rico Tip-Off vòng 1): thống kê/kỷ lục và chi tiết trận, không phải sự kiện của thực thể.

## Mốc thêm
- Amber: 2010-05 Rite Publishing được cấp phép dùng hệ luật; 2013-11 "Lords of Gossamer and Shadow (Diceless)" phát hành.
- Puigdemont: 2018-03-23 lệnh bắt châu Âu được ban hành lại (`derived_date`, từ "hai ngày trước" 25/3).
- Campbell Brown: 2016 OBE (bỏ dòng undated tương ứng). Nogan: 1995 chung kết play-off hạng Nhất của Reading (thua). Tibbers: 1451 có đề cập "toun" cạnh lâu đài.

## Quyết định tự đặt (không có trong GUIDE_v7)
- Amber: không ghi Guardians of Order phá sản 2006 (thực thể khác), các bài điểm sách 1992–93 (đánh giá về thực thể), Amberzine/Ambercon (không ngày).
- EMD: không ghi "1974–1976 FRA nêu 13 vụ" (khoảng không có mốc đầu rõ; có dòng undated "mid-1970s"), khen/chê 1975, mùa đông 1976–77, Amtrak 1971 (thực thể khác).
- Tibbers: không ghi Alexander III 1286, đề cập trong Registrum 1489/1541, vụ tấn công "toun" 1547 (sự kiện của thị trấn). e9 (1450 hay 1451) giữ cờ `approximate_date`.
- Puigdemont: không ghi trưng cầu 2017-10-01, tuyên bố độc lập 27/10 (của Quốc hội), phát biểu về Assange/EU, nhóm nhạc ~1980; giữ 2017-06 công bố trưng cầu và 2017-09 ký luật vì do ông thực hiện.
- Stauskas: giữ các giải thưởng tuần/giải thưởng mùa có ngày (`other`/award), chung kết/bắt đầu do ông tham gia; không ghi tweet và video thách đấu (lời/việc tự đăng của ông), xếp hạng tân binh, điểm trận.
- Newton D. Baker House (nhà): ghi chủ sở hữu/cư dân và công trình theo mốc; Fox 1974 (bảng) và 1976 (mua) cùng cờ `source_inconsistent` như haiku đặt.
- McKay: giữ chức danh ủy ban theo phiên họp (1967, 1969, 1971) và hai mốc bầu cử như haiku; cha/mẹ, nhà thời thơ ấu (xây 1916, dời 1973) không ghi.
- Nogan: kết quả/thống kê theo mùa vào `undated_mentions`; trận ra sân 2014-10-01 ở tuổi 45 không ghi.

## Ghi chú
- Haiku V3 không có gì bất thường; 9/10 file ghi trước khi báo xong (Stauskas ghi 18:38:50, báo sau đó). Trang dài (Puigdemont 50, Stauskas 75 chunk) haiku sót ít (0–3).
