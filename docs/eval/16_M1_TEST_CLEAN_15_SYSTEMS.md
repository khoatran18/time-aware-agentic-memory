# Cơ chế 1: đo 15 hệ trên `test_clean` (400 câu)

Đo ngày 2026-11-28 (12:30–16:31 giờ Việt Nam), đủ 15 hệ (pipeline P1–P10, agent A1–A5) trên tập `test_clean`, **một lần duy nhất** với cấu hình đã khóa từ `tune` và `valid` (`docs/eval/14_M1_TUNE_15_SYSTEMS.md`, `docs/eval/15_M1_VALID_15_SYSTEMS.md`): prompt `m1_v4`, top-5, `time_mode=range`, `decay_from=end`. Không chỉnh gì trong và sau khi đo.

## 1. Thiết lập

- **Dữ liệu:** `test_clean` 400 câu, chia 4 phần xen kẽ theo domain (`dataset/eval/test1..4_subset.json`, mỗi phần 100 câu); collection `tam_chunks_dev_test_clean`, profiler và extractions của `test_clean`. Mọi hệ đủ 400 câu.
- **Trả lời và agent:** DeepSeek V4.1 Flash qua OpenCode Go (`opencode_deepseek_flash`), thinking tắt, 10 luồng.
- **Judge:** GLM-5.3 qua Surplus Intelligence (`surplus_glm_5_3`, ghim `provider: dashscope-cn`, `reasoning_effort: none` và `thinking: disabled`), prompt `judge_m1`, 10 luồng. Cùng nền tảng với `valid`; `tune` chấm bằng GLM-5.3 qua OpenCode.
- **Cross-encoder và `temporal_search` của A4/A5:** GPU Kaggle (fp16) qua tunnel Cloudflare; truy xuất không dùng cache điểm.
- **Cache:** thư mục riêng cho từng (hệ, phần): `data/llm_cache/ds_test_ans_*`, `ds_test_agent_*`, `surplus_glm_test_*`.
- **Điều phối:** `local/scripts/run_test.py` (sao từ `run_valid.py`); trạng thái `local/logs/test/status.json`; tổng hợp `local/scripts/final_test.py` (`local/results/final_test.md`, `.json`). Không có pha đo thời gian.

## 2. Kết quả

Điểm luật (EM, F1, contains, từ chối) và điểm judge (strict = `matches_gold`, lenient = `verdict == correct`) tính trên cả 400 câu. In đậm: số lớn nhất mỗi cột.

| Hệ | n | EM | F1 | contains | từ chối | n judge | strict | lenient | partial | grounded | hallucinated | từ chối đúng lúc (n) | recall | precision | bước |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 400 | 0.403 | 0.475 | 0.422 | 0.292 | 400 | 0.482 | 0.555 | 0.025 | 0.703 | 0.000 | 0.82 (117) | 0.670 | 0.221 | – |
| P2 | 400 | 0.352 | 0.423 | 0.375 | 0.350 | 400 | 0.432 | 0.475 | 0.020 | 0.645 | 0.000 | 0.84 (140) | 0.618 | 0.223 | – |
| P3 | 400 | 0.460 | 0.540 | 0.497 | 0.207 | 400 | 0.552 | 0.625 | 0.028 | 0.785 | 0.000 | 0.75 (83) | 0.767 | 0.264 | – |
| P4 | 400 | 0.472 | 0.549 | 0.507 | 0.205 | 400 | 0.560 | 0.635 | 0.020 | 0.795 | 0.000 | 0.78 (82) | 0.787 | 0.269 | – |
| P5 | 400 | 0.482 | 0.563 | 0.510 | 0.182 | 400 | 0.565 | 0.647 | 0.022 | 0.812 | 0.000 | 0.64 (73) | 0.823 | 0.274 | – |
| P6 | 400 | 0.535 | 0.615 | 0.555 | 0.155 | 400 | 0.625 | 0.708 | **0.033** | 0.843 | 0.000 | 0.76 (62) | 0.825 | 0.280 | – |
| P7 | 400 | 0.530 | 0.620 | 0.562 | 0.155 | 400 | 0.645 | 0.720 | 0.025 | 0.843 | 0.000 | 0.74 (62) | 0.850 | 0.287 | – |
| P8 | 400 | 0.520 | 0.600 | 0.547 | 0.163 | 400 | 0.613 | 0.688 | 0.022 | 0.833 | 0.000 | 0.82 (65) | 0.818 | 0.281 | – |
| P9 | 400 | 0.562 | 0.638 | 0.583 | 0.138 | 400 | 0.657 | 0.713 | 0.028 | 0.860 | 0.000 | 0.67 (55) | 0.875 | 0.318 | – |
| P10 | 400 | 0.550 | 0.638 | 0.578 | 0.133 | 400 | 0.655 | 0.718 | 0.025 | 0.863 | 0.000 | 0.66 (53) | 0.882 | **0.319** | – |
| A1 | 400 | 0.565 | 0.650 | 0.608 | 0.138 | 400 | 0.677 | 0.770 | 0.015 | 0.853 | **0.007** | 0.55 (55) | 0.922 | 0.108 | 3.63 |
| A2 | 400 | **0.583** | **0.672** | **0.635** | 0.120 | 400 | 0.690 | 0.782 | 0.015 | 0.880 | 0.000 | 0.50 (48) | 0.945 | 0.181 | 2.71 |
| A3 | 400 | 0.573 | 0.664 | 0.630 | 0.130 | 400 | 0.690 | 0.782 | 0.003 | 0.868 | 0.000 | 0.49 (53) | 0.945 | 0.132 | 3.25 |
| A4 | 400 | 0.562 | 0.665 | 0.627 | 0.098 | 400 | **0.695** | **0.815** | 0.015 | **0.902** | 0.000 | 0.51 (39) | 0.948 | 0.205 | 2.51 |
| A5 | 400 | 0.580 | 0.669 | 0.623 | 0.102 | 400 | 0.690 | 0.792 | 0.007 | 0.895 | 0.000 | 0.49 (41) | **0.958** | 0.139 | 2.88 |

### 2.1 So cặp (trên 400 câu)

Chênh lệch = tỷ lệ đúng của hệ thứ nhất trừ hệ thứ hai; z = chênh / sai số chuẩn của chênh lệch cặp; "a hơn" và "b hơn" là số câu mà một hệ đúng còn hệ kia sai.

| Cặp | n | strict: chênh | z | a hơn | b hơn | lenient: chênh | z |
|---|---|---|---|---|---|---|---|
| P2 − P1 | 400 | -0.050 | -2.48 | 23 | 43 | -0.080 | -3.63 |
| P3 − P1 | 400 | +0.070 | +3.39 | 49 | 21 | +0.070 | +3.05 |
| P5 − P3 | 400 | +0.013 | +0.66 | 31 | 26 | +0.022 | +1.04 |
| P6 − P1 | 400 | +0.142 | +6.25 | 74 | 17 | +0.152 | +6.51 |
| P6 − P5 | 400 | +0.060 | +2.64 | 54 | 30 | +0.060 | +2.39 |
| P10 − P6 | 400 | +0.030 | +1.81 | 28 | 16 | +0.010 | +0.59 |
| P9 − P10 | 400 | +0.003 | +0.21 | 12 | 11 | -0.005 | -0.34 |
| P10 − P5 | 400 | +0.090 | +4.27 | 55 | 19 | +0.070 | +2.98 |
| A2 − P10 | 400 | +0.035 | +1.84 | 36 | 22 | +0.065 | +3.14 |
| A4 − A2 | 400 | +0.005 | +0.33 | 19 | 17 | +0.033 | +1.99 |
| A5 − A4 | 400 | -0.005 | -0.41 | 11 | 13 | -0.022 | -1.57 |
| A3 − A2 | 400 | +0.000 | +0.00 | 16 | 16 | +0.000 | +0.00 |
| A1 − A2 | 400 | -0.013 | -0.80 | 17 | 22 | -0.013 | -0.70 |
| A4 − P10 | 400 | +0.040 | +2.15 | 36 | 20 | +0.098 | +4.55 |
| A5 − P10 | 400 | +0.035 | +1.84 | 36 | 22 | +0.075 | +3.54 |

### 2.2 Đọc kết quả

- **Thứ tự các nhóm giữ nguyên như `tune` và `valid`.** Temporal (P6) vượt xa dense (P1): +0,142 strict, z 6,25. Thêm cross-encoder (P3, P5) tốt hơn P1; hybrid (P2) kém hơn P1 (−0,050, z −2,5). P10 hơn P6 +0,030 (z 1,81, chưa vượt ngưỡng); P9 ≈ P10.
- **Agent so với pipeline:** A2, A3, A4, A5 đều cao hơn P10 (+0,035 đến +0,040 strict; lenient +0,065 đến +0,098), A4 − P10 vượt ngưỡng (z 2,15 strict, 4,55 lenient). `temporal_search` (A4, A5) không giúp so với A2 ở strict (+0,005 và −0,005 so với A4; lenient A4 − A2 +0,033, z 1,99). A3 (thêm grep) bằng A2; A1 (chỉ grep, đọc trang) thấp hơn A2 −0,013 (chưa có ý nghĩa).
- **Từ chối:** pipeline từ chối đúng lúc 0,64–0,84, agent chỉ 0,49–0,55: agent từ chối ít hơn nhưng phần lớn không cần thiết (như `tune`, `valid`).
- **Hallucinated** gần 0 ở mọi hệ (≤ 0,007).
- **A1:** `grounded` và `recall` dựa trên việc trích passage từ cả `read_page`, `grep` (như `tune`, `valid`).

### 2.3 So với `tune` và `valid`

EM không phụ thuộc judge; strict của `tune` do judge OpenCode, của `valid` và `test_clean` do judge Surplus. In đậm: số lớn nhất mỗi cột.

| Hệ | EM tune | EM valid | EM test | strict tune | strict valid | strict test |
|---|---|---|---|---|---|---|
| P1 | 0.420 | 0.428 | 0.403 | 0.509 | 0.476 | 0.482 |
| P2 | 0.390 | 0.388 | 0.352 | 0.496 | 0.438 | 0.432 |
| P3 | 0.477 | 0.461 | 0.460 | 0.592 | 0.521 | 0.552 |
| P4 | 0.466 | 0.484 | 0.472 | 0.588 | 0.542 | 0.560 |
| P5 | 0.476 | 0.496 | 0.482 | 0.603 | 0.562 | 0.565 |
| P6 | 0.541 | 0.542 | 0.535 | 0.662 | 0.610 | 0.625 |
| P7 | 0.531 | 0.544 | 0.530 | 0.650 | 0.615 | 0.645 |
| P8 | 0.529 | 0.524 | 0.520 | 0.655 | 0.597 | 0.613 |
| P9 | 0.565 | **0.582** | 0.562 | 0.682 | 0.647 | 0.657 |
| P10 | 0.550 | 0.577 | 0.550 | 0.677 | 0.652 | 0.655 |
| A1 | 0.529 | 0.549 | 0.565 | 0.659 | 0.647 | 0.677 |
| A2 | **0.573** | 0.574 | **0.583** | **0.719** | 0.677 | 0.690 |
| A3 | 0.558 | 0.576 | 0.573 | 0.691 | 0.662 | 0.690 |
| A4 | 0.560 | 0.574 | 0.562 | 0.711 | **0.679** | **0.695** |
| A5 | 0.558 | 0.571 | 0.580 | 0.704 | 0.672 | 0.690 |

Cặp chênh lệch strict qua ba tập (z trong ngoặc):

| Cặp | tune (595) | valid (397–399) | test_clean (400) |
|---|---|---|---|
| P6 − P1 | +0,153 (8,6) | +0,134 (5,4) | +0,142 (6,25) |
| P10 − P6 | +0,015 (1,3) | +0,043 (2,4) | +0,030 (1,81) |
| A2 − P10 | +0,042 (2,6) | +0,025 (1,2) | +0,035 (1,84) |
| A4 − A2 | −0,008 | +0,003 | +0,005 |
| A5 − A4 | −0,007 | −0,008 | −0,005 |
| A3 − A2 | −0,029 (−2,3) | −0,015 | 0,000 |
| A1 − A2 | −0,061 (−4,7) | −0,030 (−1,9) | −0,013 (−0,8) |

- **EM trên `test_clean` gần bằng `tune` và `valid`** (chênh −0,04 đến +0,04 so với `tune`): chất lượng trả lời không tụt trên tập chưa từng chạm. Prompt và tham số chỉ được chỉnh trên `tune`, nên `test_clean` là phép kiểm overfit cuối: chưa thấy dấu hiệu overfit.
- **Strict của `test_clean` gần `valid`, cả hai thấp hơn `tune`:** P10 0,677 / 0,652 / 0,655; A4 0,711 / 0,679 / 0,695; P1 0,509 / 0,476 / 0,482. `valid` và `test_clean` cùng judge Surplus, `tune` judge OpenCode. Điều này gợi ý phần giảm của `tune` sang `valid` đến từ `tune` (tập đã dùng để chỉnh, và/hoặc nền tảng judge) hơn là từ riêng `valid`; **chưa kiểm chứng**, vì chưa chấm lại một tập bằng nền tảng kia trên mẫu lớn (mới 10 câu lỗi của P10 ở `valid` chấm lại bằng OpenCode: strict giống 10/10, xem `docs/eval/15` mục 2.3).
- **Chênh giữa agent và pipeline nhỏ hơn `tune`:** A2 − P10 là +0,042 (z 2,6) ở `tune`, +0,025 ở `valid`, +0,035 ở `test_clean`; trên cả hai tập chưa dùng để chỉnh đều chưa vượt ngưỡng z = 2 ở strict (trừ A4 − P10 trên `test_clean`).

## 3. Chi phí, token, thời gian

### 3.1 DeepSeek (OpenCode Go)

Giá niêm yết ×1 (đợt chạy vào cuối tuần, không có khung ×2): 0,15 / 0,003 / 0,60 USD mỗi triệu token vào / trúng cache / ra. Agent lấy từ `agent_calls.jsonl` của thư mục kết quả cuối (kể cả các lượt phát lại cache); pipeline mỗi câu một lần gọi.

| Hệ | lượt gọi/câu | token vào/câu | cache/câu | token ra/câu | USD/câu | USD/đợt |
|---|---|---|---|---|---|---|
| P1 | 1.00 | 1680 | 743 | 27 | 0.00016 | 0.064 |
| P2 | 1.00 | 1719 | 751 | 26 | 0.00016 | 0.065 |
| P3 | 1.00 | 1773 | 757 | 28 | 0.00017 | 0.069 |
| P4 | 1.00 | 1776 | 772 | 28 | 0.00017 | 0.068 |
| P5 | 1.00 | 1768 | 780 | 28 | 0.00017 | 0.067 |
| P6 | 1.00 | 1735 | 766 | 28 | 0.00016 | 0.066 |
| P7 | 1.00 | 1756 | 770 | 28 | 0.00017 | 0.067 |
| P8 | 1.00 | 1725 | 798 | 28 | 0.00016 | 0.063 |
| P9 | 1.00 | 1772 | 789 | 28 | 0.00017 | 0.067 |
| P10 | 1.00 | 1784 | 794 | 28 | 0.00017 | 0.067 |
| A1 | 3.63 | 7972 | 5177 | 248 | 0.00058 | 0.233 |
| A2 | 2.71 | 6742 | 3614 | 224 | 0.00061 | 0.246 |
| A3 | 3.25 | 9474 | 6369 | 246 | 0.00063 | 0.253 |
| A4 | 2.51 | 6417 | 3731 | 236 | 0.00056 | 0.222 |
| A5 | 2.88 | 9221 | 6205 | 265 | 0.00063 | 0.252 |

Tổng DeepSeek 15 hệ: **1,87 USD** giá niêm yết.

### 3.2 Hai nền tảng, cả đợt (đo từ `llm_calls.jsonl` của mọi thư mục `output/` ghi trong log của đợt)

| | DeepSeek V4.1 Flash / OpenCode Go | GLM-5.3 / Surplus (DashScope) |
|---|---|---|
| Số lần gọi | 9.990 (0 lỗi): trả lời 4.000, agent 5.990 | 6.011 (6.000 thành công, 11 lỗi 404) |
| Token vào | 22,93 triệu | 16,72 triệu |
| Token trúng cache provider | 13,13 triệu (57,3%) | 9,66 triệu (57,8%) |
| Token ra | 0,60 triệu | 1,09 triệu |
| Trung bình vào / ra mỗi lần | 2.295 / 60,1 | 2.786 / 182,0 |
| Thời gian trung vị mỗi lần (p90) | trả lời 1,31 giây (1,77), agent 2,13 giây (2,71) | 4,70 giây (7,16) |
| Token ra/s trung vị | 20,8 (trả lời), 36,0 (agent) | 35,7 |
| Số lần thử lại | 1.436 (đều do 429): 658 ở khâu trả lời, 778 ở agent | 0 (11 lần 404 do offer biến mất, xem 4) |
| Tốc độ ổn định | khoảng 49 lần/phút (bị giới hạn bởi OpenCode) | khoảng 4,7 giây mỗi lần, 10 luồng |

- **Thời gian trung vị** tính theo `e2e_net_s` (không gồm chờ thử lại sau 429), nên không so trực tiếp với cột p90 của `valid`.
- **Chi phí judge GLM:** theo giá tham chiếu của Surplus (1,155 / 4,29 USD mỗi triệu token vào / ra) tương đương khoảng 24 USD, theo giá OpenCode (1,40 / 0,26 / 4,40) khoảng 17 USD. **Giá thật phải trả lúc chạy rất thấp**: offer DashScope giảm 99% (`price_input_per_1m` 1.130, `price_output_per_1m` 4.210, tính theo micro-USD mỗi triệu token, tức khoảng 0,0011 và 0,0042 USD mỗi triệu token), nên toàn bộ judge chỉ khoảng 0,02 USD. Chưa lấy số thanh toán thực từ tài khoản.
- **Cache provider** của hai nền tảng lần này gần nhau (57,3% và 57,8%), thấp hơn con số 72,6% hiển thị trên dashboard Surplus cho provider Z.ai.
- **Hạn mức OpenCode:** trước đợt chạy rolling 0%, tuần 60%, tháng 66%; sau đợt rolling 9%, tuần 64%, tháng 68%.

### 3.3 Thời gian (không phải độ trễ chính thức)

Đợt chạy nhiều tiến trình song song và có 429, nên thời gian LLM mỗi câu gồm cả chờ thử lại (pipeline 9,4–10,2 giây mỗi câu, agent 19,9–31,4 giây mỗi câu; công cụ của A4/A5 khoảng 1,0 và 0,93 giây mỗi câu trên GPU, của A1–A3 dưới 0,1 giây). **Không có pha đo thời gian truy xuất trên máy rảnh** cho `valid` và `test_clean`; độ trễ chính thức cần đo riêng.

## 4. Sự cố trong đợt chạy

1. **Hai agent treo vì request tới OpenCode không phản hồi** (timeout 120 giây của profile không kích hoạt): `agent_4_A5` (PID 205685) im 19 phút, dừng lúc 16:04; `agent_4_A4` (PID 200655) im 22 phút và mới xong 91/100 câu, dừng lúc 16:25. Dừng đúng PID; điều phối tự chạy lại, các câu đã làm trúng cache agent.
2. **Surplus 404 `minimum_discount_not_met`:** 11 lần gọi GLM ở việc `judge_A2_2` (offer DashScope tạm biến mất), tự thử lại và hoàn tất 100/100 judgment; không xảy ra ở việc khác.
3. **429 của DeepSeek:** 1.436 lần thử lại trên khoảng 9.990 lần gọi (khoảng 14%); không có việc nào thất bại vì 429.
4. **Thử ghim Z.ai cho judge** (theo yêu cầu, 20 câu): Surplus trả `404 minimum_discount_not_met` cho mọi request, vì với sàn giảm giá 94% của tài khoản chỉ có 18 offer đủ điều kiện, tốt nhất giảm 80%, các dòng Z.ai giảm 99% trên dashboard không được xét. Không có lần gọi nào thành công, không đổi cấu hình; `test_clean` giữ `dashscope-cn` cho ổn định. Script thử: `local/scripts/judge_zai.py`.
5. **Kiểm judge OpenCode so với Surplus trên 10 câu của P10 ở `valid`** (Surplus chấm strict sai): xem `docs/eval/15` mục 2.3; kết quả ở `local/results/xjudge/`.

## 5. Giới hạn

- `test_clean` chỉ chạy một lần; không đo nhiễu giữa các lần chạy LLM (quy tắc dự án).
- Judge của `valid` và `test_clean` (Surplus) khác judge của `tune` (OpenCode); độ lệch chưa đo trên mẫu lớn. So điểm judge giữa `tune` với hai tập kia chỉ ở mức xu hướng; EM không phụ thuộc judge.
- Judge chưa đo mức đồng ý với người trên mẫu độc lập.
- Sai số chuẩn trên 400 câu khoảng 0,024; không kết luận từ chênh lệch dưới 0,03 nếu z < 2.
- Thời gian, token chạy song song, không phải độ trễ chính thức; chưa có pha đo thời gian trên máy rảnh.
- Chưa tính `hit@5` theo luật cho `test_clean` (giữ ở `valid`).

## 6. Dấu vết

- **Điều phối và tổng hợp:** `local/scripts/run_test.py`, `local/scripts/final_test.py`; trạng thái `local/logs/test/status.json` (`xong_tat_ca` 16:31:06); log từng việc `local/logs/test/*.log`; kết quả `local/results/final_test.{md,json}`.
- **Thư mục kết quả:** `output/20261128_123009*` đến `output/20261128_1631*`; trả lời và agent theo `ans_<phần>_<hệ>`, `agent_<phần>_<hệ>` trong `status.json`; thư mục judge cuối của mỗi việc lấy từ dòng "Ghi vào" cuối cùng trong `judge_<hệ>_<phần>.log`.
- **Cache:** `data/llm_cache/ds_test_ans_<phần>_<hệ>_m1_v4`, `ds_test_agent_<hệ>_<phần>_m1_v4`, `surplus_glm_test_<hệ>_<phần>`.
- **Cấu hình:** profile `opencode_deepseek_flash` (thinking tắt) và `surplus_glm_5_3` (ghim `dashscope-cn`, `reasoning_effort: none`) trong `configs/config.dev.yaml`; GPU tối đa 2 truy xuất + agent A4/A5 qua `TAM_RERANK_REMOTE_URL`.
