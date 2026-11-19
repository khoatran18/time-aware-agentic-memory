# Kết quả các cấu hình trên 600 câu timeline v9 (tune), thinking bật và tắt

Ghi 2026-11-15. Tổng hợp một chỗ để đưa vào báo cáo. Phân tích đầy đủ nằm ở `docs/planning/02_AGENT_SEARCH_BASELINE.md` (mục 11.16 đến 11.20 và mục 14); cách tái hiện (script, lệnh, thư mục kết quả): `docs/eval/11_REPRODUCE_V9_RUNS.md`.

## 1. Phạm vi

- **Dữ liệu:** 600 câu v9 thuộc split tune (195 trang có trong graph Neo4j và đủ chunk trong kho vector `tam_chunks_dev_tune`); loại `list` 214, `first_last_next` 165, `order_gap` 157, `summary` 64. Bộ con: `dataset/eval/v9_graph203_subset.json`.
- **LLM:** `opencode_deepseek_flash` (OpenCode Go, DeepSeek V4.1 Flash). Mỗi cấu hình chạy một lần cho mỗi chế độ; mọi lần gọi qua cache.
- **Chấm:** `scripts/v9_eval/v9_score.py` (exact, F1 theo mốc), cùng thước đo cho mọi cấu hình.
- **Nhãn cấu hình (mục 14):** a dense thuần; b hybrid (dense + BM25); d hybrid + sự kiện của chunk (không đi ô); f graph + vector (f: `graph`; f′: `graph_tb`; f″: `graph_tt`); g agent A; h agent B; i agent B + graph. c (có lọc thời gian) và e (graph không vector) bỏ vì không áp dụng được cho câu neo vào sự kiện (chỉ 78/600 câu có năm).

## 2. Kết quả

**Bảng đầy đủ (600 câu tune, một lần chạy mỗi cấu hình và mỗi chế độ; trung bình mỗi câu).** Nhãn theo mục 14 (a–i). "Truy xuất" = truy xuất vector/graph (a, b, d, f) hoặc thời gian công cụ (g, h, i). Token vào/cache/ra tính trên các câu có lần gọi LLM thật (cache cục bộ trúng thì không có số đo). USD tính theo giá Flash (vào chưa cache 0,15; cache 0,003; ra 0,60 USD mỗi triệu token), cho 600 câu.

*Thinking tắt (`--no-thinking`, `THINKING=off`)*

| # | Cấu hình | exact | F1 | token vào (cache) | token ra | lượt LLM | truy xuất | LLM | cả câu | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| a | dense, chunk thô, k = 15 | 0,728 | 0,865 | 1.990 (16%) | 74 | 1 | 20 ms | 4,5 s | 4,5 s | 0,18 |
| b | hybrid, chunk thô, k = 15 | 0,747 | 0,864 | 2.057 (16%) | 74 | 1 | 46 ms | 3,7 s | 3,8 s | 0,18 |
| d | hybrid + sự kiện, không đi ô | 0,678 | 0,819 | 797 (20%) | 35 | 1 | 26 ms | 2,5 s | 2,5 s | 0,07 |
| f | graph + vector (`graph`) | 0,700 | 0,833 | 1.151 (24%) | 35 | 1 | 32 ms | 2,6 s | 2,6 s | 0,09 |
| f′ | `graph_tb` | 0,698 | 0,841 | 1.101 (34%) | 35 | 1 | 32 ms | 2,5 s | 2,6 s | 0,08 |
| f″ | `graph_tt` | 0,613 | 0,748 | 781 (39%) | 32 | 1 | 30 ms | 2,5 s | 2,5 s | 0,06 |
| g | agent A | 0,782 | 0,870 | 7.683 (67%) | 255 | 3,94 | 33 ms | 12,9 s | 13,0 s | 0,33 |
| h | agent B | 0,820 | 0,916 | 6.821 (55%) | 256 | 2,56 | 44 ms | 9,8 s | 9,8 s | 0,37 |
| i | agent B + graph | **0,853** | **0,934** | 7.697 (63%) | 247 | 2,51 | 44 ms | 9,5 s | 9,6 s | 0,35 |

*Thinking bật (mặc định, các lần đo trước đó)*

| # | Cấu hình | exact | F1 | token vào (cache) | token ra | lượt LLM | truy xuất | LLM | cả câu | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| a | dense, chunk thô, k = 15 | 0,845 | 0,919 | 2.016 (21%) | 1.245 | 1 | 13 ms | 14,9 s | 14,9 s | 0,59 |
| b | hybrid, chunk thô, k = 15 | **0,868** | 0,930 | 2.082 (24%) | 1.275 | 1 | 14 ms | 15,2 s | 15,2 s | 0,60 |
| d | hybrid + sự kiện | 0,732 | 0,847 | không đo theo cấu hình (xem dưới) | | 1 | | | | |
| f | `graph` | 0,768 | 0,873 | không đo theo cấu hình | | 1 | | | | |
| f′ | `graph_tb` | 0,753 | 0,877 | không đo theo cấu hình | | 1 | | | | |
| f″ | `graph_tt` | 0,660 | 0,779 | không đo theo cấu hình | | 1 | | | | |
| g | agent A | 0,835 | 0,889 | 8.755 (63%) | 581 | 4,10 | 45 ms | 16,2 s | 13,0 s | 0,51 |
| h | agent B | 0,922 | 0,969 | 10.620 (53%) | 844 | 3,16 | 60 ms | 16,7 s | 13,5 s | 0,77 |
| i | agent B + graph | **0,928** | **0,975** | 10.035 (59%) | 636 | 2,89 | 52 ms | 13,1 s | 11,6 s | 0,61 |

**Thiếu số đo của d, f, f′, f″ khi thinking bật.** Lần chạy đó (`output/20261115_191028`) không gắn mã câu vào số đo LLM, chỉ có tổng của bốn cấu hình: 2.034 lần gọi thật, 1,98 triệu token vào (0,62 triệu cache), 1,19 triệu token ra, trung bình 973 token vào, 585 token ra và 8,8 s mỗi lần gọi, khoảng 0,92 USD. Đã thử ghép từng lần gọi cũ với prompt qua số token vào nhưng **không đạt** (1.309/1.807 prompt có token vào trùng prompt khác; chỉ khoảng 17% câu ghép không mơ hồ), nên không dùng. Muốn có số chính xác phải chạy lại với thinking bật (khoảng 0,9 USD, cần cache mới).

**Nhận xét.**
1. Tắt thinking làm tụt exact ở mọi cấu hình (a −11,7; b −12,1; d −5,4; f −6,8; f′ −5,5; f″ −4,7; g −5,3; h −10,2; i −7,5 điểm), nhiều nhất ở `list` và `summary`; `order_gap` gần như không đổi. Chi phí giảm 1,5 đến 3,3 lần (a, b 3,3 lần; h 2,1; i 1,7; g 1,5).
2. Khi tắt, thứ tự exact là i 0,853 > h 0,820 > g 0,782 > b 0,747 > a 0,728 > f 0,700 ≈ f′ 0,698 > d 0,678 > f″ 0,613. Khi bật: i 0,928 > h 0,922 > b 0,868 > a 0,845 > g 0,835 > f 0,768 > f′ 0,753 > d 0,732 > f″ 0,660. Agent có đồ thị (i) đứng đầu ở cả hai chế độ; ở chế độ tắt thì agent A (g) vượt a, b, còn khi bật thì a, b vượt g.
3. Graph (f) hơn d 2 đến 3,6 điểm ở cả hai chế độ; lọc track (f″) kém nhất ở cả hai chế độ.
4. Thời gian cả câu của agent giảm ít (i: 11,6 → 9,6 s) vì mỗi lượt chỉ có khoảng 120 token suy luận và thời gian chờ token đầu tiên (TTFT) mỗi lượt khoảng 3 s không đổi theo chế độ (i: 3,1 s tắt, 3,9 s bật). a, b nhanh hơn 3 đến 4 lần (15 → 4 s) vì dồn cả việc đọc 15 đoạn vào một lần suy luận.
5. **Hạn chế về thời gian:** các lần chạy tắt thinking chạy cùng lúc bốn việc song song (khoảng 50 yêu cầu đồng thời), các lần bật chạy với tải khác nhau; chênh thời gian giữa hai chế độ lẫn ảnh hưởng của tải, không phải số sạch. Muốn số sạch cần mẫu nhỏ (khoảng 30 câu) chạy 1 đến 2 luồng.
6. **Lỗi đã gặp khi chạy:** lần chạy d, f đầu tiên (`output/20261115_221726`) vì lệnh sửa không áp dụng nên vẫn chạy thinking bật và trúng toàn bộ cache cũ (2.400 hit, 1 giây); đã bỏ, thay bằng `output/20261115_223117` (0 hit, token ra 35 mỗi lần).

## 3. Nơi lưu kết quả thô

`output/` bị gitignore, chỉ có trên máy. Thinking bật: `output/agent_v9_tune600/` (A, B, B_graph, fixed). Thinking tắt: `output/agent_v9_tune600/no_thinking/` (thư mục `20261115_220350`, `220403`, `221538`, `221538_2`, `221607`, `223117`). Tên thư mục gốc và lệnh chạy từng cấu hình: `docs/eval/11_REPRODUCE_V9_RUNS.md` mục 4 đến 6.

## 4. Đo lại các cấu hình dùng graph sau khi ingest lại (thinking tắt, 619 câu)

Ghi 2026-11-17. Graph tune được ingest lại với thinking tắt (203 trang, 8.792 sự kiện; `node_id` đổi nên cache cũ không dùng lại). Kho vector tune được nạp bù 97 chunk không có mốc (5.995 chunk, `fill: undated_dropped`, graph trỏ tới chunk nào cũng có trong kho). Chỉ đo lại các cấu hình dùng graph (d, f, f′, f″, i); a, b, g, h không dùng graph nên **không đo lại** và vẫn là số ở mục 2.

**Khác với mục 2:** bộ câu hỏi là `dataset/eval/v9_graph_tune_subset.json` (**619 câu**, 176 trang có câu; không loại trang nào vì kho đủ chunk), gồm 600 câu cũ và 19 câu thêm. Reader và agent chạy thinking tắt, 30 luồng, cache riêng (`data/llm_cache/reader_nothink/`, `agent_nothink/`; khóa mới vì `node_id` đổi). Loại câu: `list` 221, `first_last_next` 171, `order_gap` 162, `summary` 65.

| # | Cấu hình | exact | F1 | token vào (cache) | token ra | lượt LLM | truy xuất | cả câu | USD (619 câu) |
|---|---|---|---|---|---|---|---|---|---|
| d | hybrid + sự kiện, không đi ô | 0,672 | 0,816 | 765 (16%) | 34 | 1 | 43 ms | 3,7 s | 0,07 |
| f | graph + vector (`graph`) | 0,703 | 0,825 | 1.128 (30%) | 35 | 1 | 51 ms | 4,0 s | 0,09 |
| f′ | `graph_tb` | **0,709** | **0,835** | 1.078 (29%) | 35 | 1 | 52 ms | 3,6 s | 0,09 |
| f″ | `graph_tt` | 0,630 | 0,773 | 752 (32%) | 31 | 1 | 50 ms | 3,7 s | 0,06 |
| i | agent B + graph | **0,860** | **0,940** | 7.627 (61%) | 247 | 2,50 | 90 ms | 9,7 s | 0,38 |

Theo loại, exact: i — `first_last_next` 0,89, `list` 0,81, `order_gap` 0,98, `summary` 0,66. d/f/f′/f″ — `list` 0,53/0,60/0,58/0,53; `summary` 0,40/0,51/0,52/0,48; `first_last_next` 0,71/0,70/0,74/0,75; `order_gap` 0,94/0,92/0,93/0,70.

**So với lần đo trước (cùng thinking tắt, trên đúng 600 câu chung).** d 0,678 → 0,675; f 0,700 → 0,713; f′ 0,698 → 0,717; f″ 0,613 → 0,630. Chênh trong khoảng −0,3 đến +1,9 điểm (một lần chạy mỗi lần, không đo nhiễu), nên ingest lại không đổi kết luận: graph (f, f′) vẫn hơn d khoảng 4 điểm, f″ vẫn kém nhất. i trên 619 câu 0,860 so với 0,853 trên 600 câu cũ (chưa chấm riêng trên 600 câu chung).

**Ghi chú.**
1. Số tuyệt đối không so thẳng với a, b, g, h (đo trên 600 câu, kho vector chưa có chunk bù); kho tune nay có thêm 97 chunk nên a, b có thể lệch nhẹ nếu đo lại, chưa đo.
2. Số trúng cache cục bộ trong lần d, f: 75/2.476 (cùng prompt giữa các cấu hình trong một lần chạy, không phải cache cũ).
3. Thư mục thô: `output/20261117_115607` (d, f, f′, f″; 2.476 mục, 311 s) và `output/20261117_115405` (i; 619 câu, `stop_reason` đều là `answer`). Lệnh: `THINKING=off WORKERS=30 SUBSET=dataset/eval/v9_graph_tune_subset.json python3 -I scripts/v9_eval/v9_fixed_eval.py`; `python3 scripts/run_agent_search.py --subset dataset/eval/v9_graph_tune_subset.json --n 1000 --prompt v5 --workers 30 --no-thinking --kind B --graph --normalize-page-names`.

## 5. Kết quả trên tập valid (554 câu, thinking tắt)

Ghi 2026-11-17. Chín cấu hình a–i chạy một lần mỗi cấu hình trên split valid, thinking tắt, **50 luồng gộp** (5 tiến trình song song, mỗi tiến trình 10 luồng; hai tiến trình a, b và d, f chạy lại với 25 luồng vì lần đầu chết ở bước ghi `run_meta.json`, chưa gọi LLM nên không tốn tiền). Các cấu hình, prompt, chấm điểm và cách tính USD giống mục 2 và mục 4; chỉ đổi dữ liệu.

**Dữ liệu.** 554 câu, 167 trang (`dataset/eval/v9_graph_valid_subset.json`, dựng bằng `make_v9_graph_subset.py --collection tam_chunks_dev_valid`); `list` 158, `first_last_next` 128, `order_gap` 210, `summary` 58. Kho vector `tam_chunks_dev_valid`: 5.063 chunk (179 chunk bù không có mốc, `fill: undated_dropped`). Graph valid: 167 trang, 7.490 sự kiện, ingest thinking tắt (`local/ingest_eval/graph_build_V.py`, danh sách nút `graph_nodes_V.json`). Tên trang trong graph và trong file câu hỏi đã bỏ dấu (ví dụ `Atl_tico_Madrid`); bộ con dùng đúng tên đó. Phủ chunk gold ở k = 15: dense 0,903, hybrid 0,940.

| # | Cấu hình | exact | F1 | token vào (cache) | token ra | lượt LLM | truy xuất | cả câu | USD (554 câu) |
|---|---|---|---|---|---|---|---|---|---|
| a | dense, chunk thô, k = 15 | 0,792 | 0,893 | 1.960 (18%) | 64 | 1 | 32 ms | 2,6 s | 0,15 |
| b | hybrid, chunk thô, k = 15 | 0,807 | 0,885 | 2.047 (19%) | 64 | 1 | 32 ms | 2,8 s | 0,16 |
| d | hybrid + sự kiện, không đi ô | 0,751 | 0,825 | 777 (14%) | 33 | 1 | 39 ms | 3,2 s | **0,07** |
| f | graph + vector (`graph`) | 0,769 | 0,823 | 1.146 (26%) | 33 | 1 | 55 ms | 3,3 s | 0,08 |
| f′ | `graph_tb` | 0,733 | 0,807 | 1.098 (27%) | 33 | 1 | 54 ms | 3,3 s | 0,08 |
| f″ | `graph_tt` | 0,644 | 0,763 | 788 (30%) | 31 | 1 | 53 ms | 3,2 s | **0,06** |
| g | agent A | 0,829 | 0,883 | 7.457 (69%) | 252 | 3,82 | 23 ms | 17,4 s | 0,29 |
| h | agent B | 0,883 | 0,938 | 6.034 (57%) | 229 | 2,45 | 50 ms | 12,9 s | 0,30 |
| i | agent B + graph | **0,886** | **0,947** | 7.349 (63%) | 229 | 2,43 | 54 ms | 12,9 s | 0,31 |

Theo loại, exact (a / b / d / f / f′ / f″ / g / h / i): `list` 0,696 / 0,734 / 0,576 / 0,646 / 0,595 / 0,601 / 0,747 / 0,797 / 0,823; `summary` 0,690 / 0,724 / 0,655 / 0,586 / 0,466 / 0,552 / 0,655 / 0,724 / 0,707; `first_last_next` 0,734 / 0,688 / 0,719 / 0,695 / 0,664 / 0,641 / 0,781 / 0,883 / 0,883; `order_gap` 0,929 / 0,957 / 0,929 / 0,957 / 0,952 / 0,705 / 0,967 / 0,990 / 0,986.

**Nhận xét.**
1. Thứ tự exact trên valid: i 0,886 ≈ h 0,883 > g 0,829 > b 0,807 > a 0,792 > f 0,769 > d 0,751 > f′ 0,733 > f″ 0,644. So với tune (mục 2 và 4) thứ tự giống nhau ở phần đầu (agent B có và không graph đứng đầu, g, b, a rồi nhóm cố định) và f″ vẫn kém nhất. Hai điểm đổi: f hơn f′ trên valid (tune f′ hơn f một chút) và h ≈ i (hơn kém 0,3 điểm, trong khoảng chênh của một lần chạy).
2. Graph (f) vẫn hơn d (+1,8 điểm), nhỏ hơn mức trên tune (+3 đến 4 điểm). Agent có graph (i) chỉ hơn agent chỉ vector (h) 0,3 điểm exact và 0,9 điểm F1, không tới mức đáng kể trên một lần chạy.
3. Chi phí tính theo 554 câu: nhóm cố định 0,06–0,16 USD, agent khoảng 0,3 USD (gấp 2 đến 5 lần).
4. **Thời gian không so được giữa các cấu hình và với mục 2:** cả năm tiến trình chạy cùng lúc (50 luồng gộp) nên thời gian chờ LLM chứa tải. Agent cả câu 12,9 s (g 17,4 s), nhóm cố định 2,6 đến 3,3 s.

Thư mục thô (chỉ có trên máy): a, b `output/20261117_173120`; d, f, f′, f″ `output/20261117_173237`; g `output/20261117_171410`; h `output/20261117_171410_3`; i `output/20261117_171410_2`. Mỗi thư mục có `run_meta.json` (thinking, mô hình, kho, số luồng, mã git), `prompts.jsonl`, `system_prompt.txt`, `llm_calls.jsonl`, `results.jsonl`; agent thêm `agent_trace.jsonl`, `tool_texts.jsonl`, `agent_calls.jsonl`.

## 6. Kết quả trên tập test_clean (659 câu, thinking tắt, chạy một lần)

Ghi 2026-11-17. Chín cấu hình a–i giữ nguyên như đã chạy trên tune và valid (k = 15, prompt v5, thinking tắt, không chỉnh gì sau khi xem kết quả), chạy **một lần** trên tập giữ lại. 5 tiến trình song song, mỗi tiến trình 10 luồng (tổng 50 khi cả năm còn chạy).

**Dữ liệu.** 659 câu, 173 trang có câu (`dataset/eval/v9_graph_test_clean_subset.json`; không trùng trang hay mã câu với tune, valid); `list` 211, `first_last_next` 166, `order_gap` 212, `summary` 70. Kho vector `tam_chunks_dev_test_clean`: 5.682 chunk (110 bù). Graph: 186 trang, 8.240 sự kiện, ingest thinking tắt (danh sách nút `graph_nodes_C.json`). Phủ chunk gold ở k = 15: dense 0,854, hybrid 0,898.

| # | Cấu hình | exact | F1 | token vào (cache) | token ra | lượt LLM | truy xuất | cả câu | USD (659 câu) |
|---|---|---|---|---|---|---|---|---|---|
| a | dense, chunk thô, k = 15 | 0,754 | 0,865 | 1.975 (18%) | 68 | 1 | 52 ms | 5,5 s | 0,19 |
| b | hybrid, chunk thô, k = 15 | 0,780 | 0,877 | 2.054 (19%) | 69 | 1 | 52 ms | 5,6 s | 0,19 |
| d | hybrid + sự kiện, không đi ô | 0,689 | 0,793 | 791 (19%) | 33 | 1 | 59 ms | 4,1 s | 0,08 |
| f | graph + vector (`graph`) | 0,728 | 0,826 | 1.175 (29%) | 34 | 1 | 75 ms | 4,2 s | 0,10 |
| f′ | `graph_tb` | 0,689 | 0,823 | 1.122 (36%) | 34 | 1 | 75 ms | 4,3 s | 0,09 |
| f″ | `graph_tt` | 0,619 | 0,767 | 787 (40%) | 32 | 1 | 74 ms | 4,1 s | **0,06** |
| g | agent A | 0,804 | 0,859 | 7.445 (68%) | 251 | 3,83 | 33 ms | 19,4 s | 0,35 |
| h | agent B | 0,869 | 0,933 | 6.651 (57%) | 248 | 2,54 | 51 ms | 14,8 s | 0,39 |
| i | agent B + graph | **0,897** | **0,947** | 7.984 (64%) | 244 | 2,55 | 54 ms | 15,0 s | 0,39 |

Theo loại, exact (a / b / d / f / f′ / f″ / g / h / i): `list` 0,635 / 0,687 / 0,512 / 0,592 / 0,521 / 0,526 / 0,678 / 0,796 / 0,844; `summary` 0,671 / 0,671 / 0,543 / 0,671 / 0,557 / 0,571 / 0,714 / 0,729 / 0,814; `first_last_next` 0,723 / 0,723 / 0,699 / 0,693 / 0,705 / 0,657 / 0,777 / 0,855 / 0,880; `order_gap` 0,925 / 0,953 / 0,906 / 0,910 / 0,887 / 0,698 / 0,981 / 1,000 / 0,991. Agent g có 3 câu trả lời không đọc được JSON (`badjson`, tính là sai); các cấu hình còn lại 0.

**So với tune và valid (exact, thinking tắt).**

| # | tune | valid | test_clean | test − valid |
|---|---|---|---|---|
| a | 0,728 | 0,792 | 0,754 | −3,8 |
| b | 0,747 | 0,807 | 0,780 | −2,7 |
| d | 0,675 | 0,751 | 0,689 | −6,2 |
| f | 0,713 | 0,769 | 0,728 | −4,1 |
| f′ | 0,717 | 0,733 | 0,689 | −4,4 |
| f″ | 0,630 | 0,644 | 0,619 | −2,5 |
| g | 0,782 | 0,829 | 0,804 | −2,5 |
| h | 0,820 | 0,883 | 0,869 | −1,4 |
| i | 0,860 | 0,886 | 0,897 | +1,1 |

(tune: a, b, g, h trên 600 câu ở mục 2; d, f, f′, f″, i trên 600 câu chung ở mục 4. d, f, f′, f″, i trên tune dùng giá trị đo lại sau khi ingest lại graph.)

**Nhận xét.**
1. Thứ tự exact trên test_clean: i 0,897 > h 0,869 > g 0,804 > b 0,780 > a 0,754 > f 0,728 > d 0,689 = f′ 0,689 > f″ 0,619. Cùng thứ tự với valid ở các vị trí đầu (agent B, g, b, a) và f″ vẫn cuối. Kết luận chính giữ nguyên: agent có graph dẫn đầu, graph (f) hơn d (+3,9 điểm) và hơn f′ trên cả valid lẫn test_clean.
2. **Không thấy dấu hiệu overfit:** không cấu hình nào tụt quá 6,2 điểm so với valid, thứ tự giữ nguyên, và i còn tăng nhẹ (+1,1). Phần lớn cấu hình thấp hơn valid 1,4 đến 6,2 điểm, khớp dự đoán trước khi chạy: phủ chunk gold của test_clean thấp hơn (hybrid 0,898 so với 0,940 ở valid), và các cấu hình dựa vào top-k chunk (d −6,2; a −3,8; b −2,7) giảm nhiều hơn các agent (g −2,5; h −1,4; i +1,1).
3. i hơn h 2,8 điểm exact (0,3 điểm ở valid); i hơn h ở cả bốn loại câu trừ `order_gap` (0,991 so với 1,000). Mỗi cấu hình chạy một lần nên chênh dưới khoảng 2 điểm chưa phân biệt được; 2,8 điểm là lần chênh lớn nhất trong ba tập và cùng chiều với tune (i 0,860 so với h 0,820, nhưng hai số đo trên bộ câu khác nhau: 619 và 600 câu).
4. Chi phí tính theo 659 câu: nhóm cố định 0,06 đến 0,19 USD; agent 0,35 đến 0,39 USD (gấp 2 đến 6 lần).
5. **Thời gian không so được giữa cấu hình và giữa các tập:** năm tiến trình chạy cùng lúc, d, f, f′, f″ chỉ có 10 luồng (tổng 1.100 s), nên thời gian chờ LLM lẫn tải. Độ trễ một lần gọi 3 đến 5 s là sàn cố định theo thời gian chờ token đầu tiên.

Thư mục thô (chỉ có trên máy): a, b `output/20261117_175918`; d, f, f′, f″ `output/20261117_180117`; g (agent A) `output/20261117_175808_3`; h (agent B) `output/20261117_175808_2`; i (agent B + graph) `output/20261117_175808`. Mỗi thư mục có `run_meta.json`, `prompts.jsonl`, `system_prompt.txt`, `llm_calls.jsonl`, `results.jsonl`; agent thêm `agent_trace.jsonl`, `tool_texts.jsonl`, `agent_calls.jsonl`.
