# Cơ chế 1: đo 15 hệ trên `valid` (399 câu)

Đo ngày 2026-11-28 (02:19–06:12 giờ Việt Nam), đủ 15 hệ (pipeline P1–P10, agent A1–A5) trên tập `valid`, cấu hình giữ nguyên như `tune` (`docs/eval/14_M1_TUNE_15_SYSTEMS.md`): prompt `m1_v4`, top-5, `time_mode=range`, `decay_from=end`, không điều chỉnh gì thêm trên `valid`. `test_clean` chưa đo.

## 1. Thiết lập

- **Dữ liệu:** `valid` 399 câu, chia 4 phần xen kẽ theo domain (`dataset/eval/valid1..4_subset.json`: 100, 100, 100, 99 câu); collection `tam_chunks_dev_valid`, profiler và extractions của `valid`.
- **Trả lời và agent:** DeepSeek V4.1 Flash qua OpenCode Go (`opencode_deepseek_flash`), thinking tắt, 10 luồng.
- **Judge:** GLM-5.3 qua Surplus Intelligence (`surplus_glm_5_3`, ghim `provider: dashscope-cn`, `reasoning_effort: none` và `thinking: disabled`), prompt `judge_m1`, 10 luồng. **Khác `tune`:** `tune` chấm bằng GLM-5.3 qua OpenCode. Hai nền tảng cùng model nhưng chưa đo độ lệch trên mẫu lớn (mới 10 câu: 9/10 cùng verdict).
- **Cross-encoder và `temporal_search` của A4/A5:** GPU Kaggle (fp16) qua tunnel Cloudflare; truy xuất không dùng cache điểm.
- **Cache:** thư mục riêng cho từng (hệ, phần): `data/llm_cache/ds_valid_ans_*`, `ds_valid_agent_*`, `surplus_glm_valid_*`.
- **Điều phối:** `local/scripts/run_valid.py` (từ `run_rest395.py`, không có pha đo thời gian); trạng thái `local/logs/valid/status.json`; tổng hợp `local/scripts/final_valid.py` (`local/results/final_valid.md`, `.json`).
- **Số câu:** pipeline chỉ có 397 câu trả lời. Hai câu của `valid1` (`/wiki/Young_Girl_with_a_Flower_Basket#P127#1`, `/wiki/Master-General_of_the_Ordnance_(Sweden)#P1308#1`) bị loại ở bước trả lời với mọi pipeline, còn agent chạy đủ 399. So cặp chỉ lấy phần giao.

## 2. Kết quả

Điểm luật (EM, F1, contains, từ chối) tính trên mọi câu có đáp án; điểm judge (strict = `matches_gold`, lenient = `verdict == correct`) tính trên mọi câu (judge xong đủ). In đậm: số lớn nhất mỗi cột.

| Hệ | n | EM | F1 | contains | từ chối | n judge | strict | lenient | partial | grounded | hallucinated | từ chối đúng lúc (n) | recall | precision | bước |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 397 | 0.428 | 0.470 | 0.436 | 0.332 | 397 | 0.476 | 0.542 | 0.005 | 0.660 | 0.000 | 0.83 (132) | 0.650 | 0.223 | – |
| P2 | 397 | 0.388 | 0.432 | 0.401 | 0.375 | 397 | 0.438 | 0.489 | 0.008 | 0.615 | 0.000 | 0.81 (149) | 0.605 | 0.223 | – |
| P3 | 397 | 0.461 | 0.513 | 0.481 | 0.264 | 397 | 0.521 | 0.589 | 0.020 | 0.730 | 0.000 | 0.76 (105) | 0.746 | 0.259 | – |
| P4 | 397 | 0.484 | 0.538 | 0.501 | 0.247 | 397 | 0.542 | 0.610 | 0.018 | 0.751 | 0.000 | 0.80 (98) | 0.751 | 0.266 | – |
| P5 | 397 | 0.496 | 0.548 | 0.514 | 0.196 | 397 | 0.562 | 0.645 | 0.013 | 0.801 | 0.000 | 0.73 (78) | 0.778 | 0.279 | – |
| P6 | 397 | 0.542 | 0.594 | 0.557 | 0.191 | 397 | 0.610 | 0.693 | 0.013 | 0.809 | 0.000 | 0.72 (76) | 0.824 | 0.291 | – |
| P7 | 397 | 0.544 | 0.600 | 0.559 | 0.156 | 397 | 0.615 | 0.718 | 0.023 | 0.841 | 0.000 | 0.76 (62) | 0.826 | 0.293 | – |
| P8 | 397 | 0.524 | 0.584 | 0.542 | 0.181 | 397 | 0.597 | 0.680 | 0.015 | 0.816 | 0.000 | 0.75 (72) | 0.798 | 0.279 | – |
| P9 | 397 | **0.582** | 0.627 | 0.599 | 0.141 | 397 | 0.647 | 0.733 | 0.015 | 0.856 | 0.000 | 0.66 (56) | 0.864 | 0.309 | – |
| P10 | 397 | 0.577 | 0.631 | 0.597 | 0.128 | 397 | 0.652 | 0.736 | 0.028 | **0.872** | 0.000 | 0.73 (51) | 0.866 | **0.319** | – |
| A1 | 399 | 0.549 | 0.627 | 0.589 | 0.180 | 399 | 0.647 | 0.717 | 0.028 | 0.807 | **0.008** | 0.50 (74) | 0.915 | 0.112 | 3.68 |
| A2 | 399 | 0.574 | 0.655 | **0.624** | 0.135 | 399 | 0.677 | 0.757 | 0.028 | 0.860 | 0.005 | 0.37 (54) | 0.942 | 0.180 | 2.76 |
| A3 | 399 | 0.576 | 0.646 | 0.617 | 0.173 | 399 | 0.662 | 0.744 | 0.020 | 0.820 | 0.005 | 0.51 (69) | 0.930 | 0.158 | 3.36 |
| A4 | 399 | 0.574 | **0.660** | 0.622 | 0.130 | 399 | **0.679** | 0.772 | **0.030** | 0.867 | 0.000 | 0.46 (52) | 0.945 | 0.209 | 2.60 |
| A5 | 399 | 0.571 | 0.641 | 0.614 | 0.173 | 399 | 0.672 | **0.774** | 0.023 | 0.825 | 0.000 | 0.38 (69) | **0.952** | 0.146 | 2.97 |

### 2.1 So cặp (trên các câu cả hai hệ đã chấm)

Chênh lệch = tỷ lệ đúng của hệ thứ nhất trừ hệ thứ hai; z = chênh / sai số chuẩn của chênh lệch cặp; "a hơn" và "b hơn" là số câu mà một hệ đúng còn hệ kia sai.

| Cặp | n | strict: chênh | z | a hơn | b hơn | lenient: chênh | z |
|---|---|---|---|---|---|---|---|
| P2 − P1 | 397 | −0.038 | −1.79 | 28 | 43 | −0.053 | −2.35 |
| P3 − P1 | 397 | +0.045 | +1.88 | 55 | 37 | +0.048 | +1.81 |
| P5 − P3 | 397 | +0.040 | +1.98 | 41 | 25 | +0.055 | +2.54 |
| P6 − P1 | 397 | +0.134 | +5.40 | 78 | 25 | +0.151 | +5.96 |
| P6 − P5 | 397 | +0.048 | +2.09 | 51 | 32 | +0.048 | +1.96 |
| P10 − P6 | 397 | +0.043 | +2.44 | 33 | 16 | +0.043 | +2.30 |
| P9 − P10 | 397 | −0.005 | −0.41 | 11 | 13 | −0.003 | −0.17 |
| P10 − P5 | 397 | +0.091 | +4.47 | 52 | 16 | +0.091 | +4.10 |
| A2 − P10 | 397 | +0.025 | +1.20 | 40 | 30 | +0.023 | +0.99 |
| A4 − A2 | 399 | +0.003 | +0.17 | 17 | 16 | +0.015 | +0.85 |
| A5 − A4 | 399 | −0.008 | −0.56 | 13 | 16 | +0.003 | +0.16 |
| A3 − A2 | 399 | −0.015 | −0.97 | 16 | 22 | −0.013 | −0.67 |
| A1 − A2 | 399 | −0.030 | −1.86 | 15 | 27 | −0.040 | −2.15 |
| A4 − P10 | 397 | +0.028 | +1.37 | 38 | 27 | +0.038 | +1.81 |
| A5 − P10 | 397 | +0.020 | +0.97 | 38 | 30 | +0.040 | +1.87 |

### 2.2 Đọc kết quả

- **Cái giữ nguyên so với `tune`:** thứ tự các nhóm. Temporal (P6) vượt xa dense (P1): +0.134 strict, z 5.4. Thêm cross-encoder (P3, P5) tốt hơn P1; hybrid (P2) kém hơn P1. P10 hơn P6 một chút có ý nghĩa ở mức khiêm tốn (+0.043, z 2.4; ở `tune` +0.015, z 1.3). P9 ≈ P10.
- **Agent so với pipeline:** A2, A4, A5 cao hơn P10 (+0.020 đến +0.028 strict, z từ 1.0 đến 1.4, +0.04 lenient, z 1.8–1.9), nhưng chưa vượt ngưỡng ý nghĩa; ở `tune` A2 − P10 là +0.042 (z 2.6). `temporal_search` (A4, A5) không giúp so với A2 (+0.003 và −0.008 so với A4). A3 (thêm grep) và A1 (chỉ grep, đọc trang) không hơn A2; A1 thấp hơn A2 rõ nhất (−0.030, z −1.9 strict; −0.040, z −2.2 lenient).
- **Từ chối:** pipeline từ chối đúng lúc 0.66–0.83, agent từ chối đúng lúc chỉ 0.37–0.51: agent từ chối ít hơn nhưng phần lớn không cần thiết (như `tune`).
- **Hallucinated** gần 0 ở mọi hệ (≤ 0.008).
- **A1:** `grounded` và `recall` dựa trên việc trích passage từ cả `read_page`, `grep` (như bản đã sửa ở `tune`).

### 2.3 So với `tune`

| Hệ | EM tune → valid | strict tune → valid | lenient tune → valid | recall (judge) tune → valid |
|---|---|---|---|---|
| P1 | 0.420 → 0.428 | 0.509 → 0.476 | 0.597 → 0.542 | 0.746 → 0.650 |
| P2 | 0.390 → 0.388 | 0.496 → 0.438 | 0.563 → 0.489 | 0.711 → 0.605 |
| P3 | 0.477 → 0.461 | 0.592 → 0.521 | 0.672 → 0.589 | 0.817 → 0.746 |
| P4 | 0.466 → 0.484 | 0.588 → 0.542 | 0.657 → 0.610 | 0.817 → 0.751 |
| P5 | 0.476 → 0.496 | 0.603 → 0.562 | 0.704 → 0.645 | 0.845 → 0.778 |
| P6 | 0.541 → 0.542 | 0.662 → 0.610 | 0.748 → 0.693 | 0.862 → 0.824 |
| P7 | 0.531 → 0.544 | 0.650 → 0.615 | 0.736 → 0.718 | 0.877 → 0.826 |
| P8 | 0.529 → 0.524 | 0.655 → 0.597 | 0.746 → 0.680 | 0.849 → 0.798 |
| P9 | 0.565 → 0.582 | 0.682 → 0.647 | 0.768 → 0.733 | 0.906 → 0.864 |
| P10 | 0.550 → 0.577 | 0.677 → 0.652 | 0.758 → 0.736 | 0.901 → 0.866 |
| A1 | 0.529 → 0.549 | 0.659 → 0.647 | 0.760 → 0.717 | 0.943 → 0.915 |
| A2 | 0.573 → 0.574 | 0.719 → 0.677 | 0.813 → 0.757 | 0.958 → 0.942 |
| A3 | 0.558 → 0.576 | 0.691 → 0.662 | 0.776 → 0.744 | 0.961 → 0.930 |
| A4 | 0.560 → 0.574 | 0.711 → 0.679 | 0.825 → 0.772 | 0.961 → 0.945 |
| A5 | 0.558 → 0.571 | 0.704 → 0.672 | 0.800 → 0.774 | 0.953 → 0.952 |

- **EM (không phụ thuộc judge) không giảm:** từ −0.016 đến +0.027, phần lớn tăng nhẹ.
- **Judge (strict) giảm 0.012–0.070, lenient giảm 0.018–0.083.** Khoảng cách giữa judge và EM co lại (P10: strict − EM từ 0.127 xuống 0.075), tức judge của `valid` công nhận ít đáp án "đúng khác dạng" hơn.
- **Truy xuất thật sự thấp hơn trên `valid`:** `hit@5` theo luật (không dùng judge) của P1 0.663 → 0.557, P6 0.790 → 0.715, P10 0.853 → 0.791 (`tune` 395 câu so với `valid`). Vì vậy `recall` của judge giảm phần nào là thật.
- **Chưa tách được phần do judge:** judge của hai tập là hai nền tảng khác nhau (OpenCode so với Surplus) trên hai tập câu khác nhau. Muốn tách cần chấm lại một tập bằng nền tảng kia (chẳng hạn một phần `tune` bằng Surplus, rẻ vì giá Surplus rất thấp). Chưa làm.

## 3. Chi phí, token, thời gian

### 3.1 DeepSeek (OpenCode Go)

Giá niêm yết ×1 (đợt chạy vào cuối tuần, không có khung ×2): 0,15 / 0,003 / 0,60 USD mỗi triệu token vào / trúng cache / ra. Agent lấy từ `agent_calls.jsonl` của thư mục kết quả cuối (kể cả các lượt phát lại cache); pipeline mỗi câu một lần gọi.

| Hệ | lượt gọi/câu | token vào/câu | cache/câu | token ra/câu | USD/câu | USD/đợt |
|---|---|---|---|---|---|---|
| P1 | 1.00 | 1680 | 741 | 26 | 0.00016 | 0.063 |
| P2 | 1.00 | 1714 | 750 | 26 | 0.00016 | 0.065 |
| P3 | 1.00 | 1769 | 820 | 27 | 0.00016 | 0.064 |
| P4 | 1.00 | 1769 | 800 | 27 | 0.00016 | 0.065 |
| P5 | 1.00 | 1765 | 770 | 27 | 0.00017 | 0.067 |
| P6 | 1.00 | 1738 | 775 | 27 | 0.00016 | 0.065 |
| P7 | 1.00 | 1760 | 763 | 28 | 0.00017 | 0.067 |
| P8 | 1.00 | 1728 | 772 | 28 | 0.00016 | 0.064 |
| P9 | 1.00 | 1769 | 796 | 28 | 0.00017 | 0.066 |
| P10 | 1.00 | 1775 | 826 | 28 | 0.00016 | 0.064 |
| A1 | 3.68 | 8310 | 5315 | 261 | 0.00062 | 0.248 |
| A2 | 2.76 | 6898 | 3692 | 225 | 0.00063 | 0.250 |
| A3 | 3.36 | 9694 | 6726 | 257 | 0.00062 | 0.247 |
| A4 | 2.60 | 6888 | 4044 | 244 | 0.00058 | 0.233 |
| A5 | 2.97 | 9506 | 6615 | 271 | 0.00062 | 0.246 |

Tổng DeepSeek 15 hệ: **1,87 USD** giá niêm yết.

### 3.2 Hai nền tảng, cả đợt (đo từ `llm_calls.jsonl` của mọi thư mục `output/` trong đợt)

| | DeepSeek V4.1 Flash / OpenCode Go | GLM-5.3 / Surplus (DashScope) |
|---|---|---|
| Số lần gọi | 10.104 (0 lỗi) | 5.995 (5.967 thành công, 28 lỗi 404) |
| Token vào | 23,41 triệu | 16,61 triệu |
| Token trúng cache provider | 13,63 triệu (58,2%) | 9,61 triệu (57,9%) |
| Token ra | 0,61 triệu | 1,08 triệu |
| Trung bình vào / ra mỗi lần | 2.317 / 60,4 | 2.783 / 181,2 |
| Thời gian trung vị mỗi lần (p90) | 1,59 giây (52,7 giây) | 3,57 giây (5,03 giây) |
| Token/s trung vị | 30,0 | 46,2 |
| Số lần thử lại | 1.457 (đều do 429) | 0 (28 lần 404 do offer biến mất, xem 4) |
| Tốc độ ổn định | khoảng 50 lần/phút (bị giới hạn bởi OpenCode) | khoảng 3,6 giây mỗi lần, 10 luồng |

- **p90 của DeepSeek** cao vì thời gian chờ thử lại sau 429 và các request treo tính vào thời gian một lần gọi.
- **Chi phí judge GLM:** theo giá tham chiếu của Surplus (1,155 / 4,29 USD mỗi triệu token vào / ra) tương đương khoảng 23,8 USD, theo giá OpenCode (1,40 / 0,26 / 4,40) khoảng 17 USD. **Giá thật phải trả lúc chạy rất thấp**: các offer DashScope giảm 99,9% so với tham chiếu, `price_input_per_1m` 1.120–1.240 và `price_output_per_1m` 4.160–4.590 tính theo micro-USD mỗi triệu token (tức khoảng 0,0011–0,0012 và 0,0042–0,0046 USD mỗi triệu token), nên toàn bộ judge chỉ khoảng 0,02–0,03 USD. Giá của từng offer đổi theo thời gian, chưa lấy số thanh toán thực từ tài khoản.
- **Cache provider** của Surplus lần này 57,9% (mẫu 10 câu trước đó là 47%), gần OpenCode.
- **Hạn mức OpenCode:** trước đợt chạy rolling 12%, tuần 56%, tháng 64%; sau đợt rolling 2%, tuần 60%, tháng 66%.

### 3.3 Thời gian (không phải độ trễ chính thức)

Đợt `valid` chạy nhiều tiến trình song song và có 429, nên thời gian LLM mỗi câu bao gồm cả chờ thử lại (pipeline khoảng 10 giây mỗi câu, agent 20–32 giây mỗi câu; công cụ của A4/A5 khoảng 0,75 giây mỗi câu trên GPU). **Không có pha đo thời gian truy xuất trên máy rảnh** cho `valid`; độ trễ chính thức cần đo riêng.

## 4. Sự cố trong đợt chạy

1. **Surplus 404 `minimum_discount_not_met` (04:01:25–04:02:03, 28 lần gọi GLM):** offer DashScope tạm biến mất, offer còn lại chỉ giảm 69,999%, dưới sàn giảm giá tài khoản 94%. Hai việc judge bị ảnh hưởng tự thử lại và hoàn tất; không còn lần nào sau đó.
2. **Hai agent treo (04:41–05:09):** `agent_2_A5` và `agent_3_A1` đứng yên khi một request tới OpenCode không trả (timeout 120 giây của profile không kích hoạt). Hai tiến trình con bị dừng theo đúng PID; điều phối tự chạy lại và các câu đã làm trúng cache agent.
3. **Nhãn `LỖI n=98` của 10 việc judge phần 1:** do phần `valid1` chỉ có 98 câu trả lời (không phải 100) nên `n` thấp hơn ngưỡng của điều phối. Judge đã chấm đủ 98/98; chỉ là nhãn trạng thái.
4. **429 của DeepSeek:** 1.457 lần thử lại trên khoảng 10.100 lần gọi (khoảng 14%); không có việc nào thất bại vì 429. Tốc độ DeepSeek giữ đúng khoảng 50 lần/phút kể cả khi giảm từ 10 xuống 4 luồng agent, nên giới hạn nằm ở OpenCode, không phải số luồng.

## 5. Giới hạn

- Judge của `valid` (Surplus) khác judge của `tune` (OpenCode); độ lệch chưa đo trên mẫu lớn (mới 10 câu, 9/10 cùng verdict). So điểm judge giữa `tune` và `valid` chỉ ở mức xu hướng; EM và `hit@5` không phụ thuộc judge.
- `valid` thấp hơn `tune` ở truy xuất (`hit@5`) và ở judge; chưa tách được phần do judge và phần do tập.
- Số câu pipeline 397 so với agent 399 (xem mục 1).
- Judge chưa đo mức đồng ý với người trên mẫu độc lập.
- Sai số chuẩn trên 397–399 câu khoảng 0,024; không kết luận từ chênh lệch dưới 0,03 nếu z < 2.
- Thời gian, token chạy song song, không phải độ trễ chính thức.

## 6. Dấu vết

- **Điều phối và tổng hợp:** `local/scripts/run_valid.py`, `local/scripts/final_valid.py`; trạng thái `local/logs/valid/status.json`; log từng việc `local/logs/valid/*.log`; kết quả `local/results/final_valid.{md,json}`.
- **Thư mục kết quả:** `output/20261128_0219*` đến `output/20261128_0609*`; trả lời và agent theo `ans_<phần>_<hệ>`, `agent_<phần>_<hệ>` trong `status.json`; thư mục judge cuối của mỗi việc lấy từ dòng "Ghi vào" cuối cùng trong `judge_<hệ>_<phần>.log`.
- **Cache:** `data/llm_cache/ds_valid_ans_<phần>_<hệ>_m1_v4`, `ds_valid_agent_<hệ>_<phần>_m1_v4`, `surplus_glm_valid_<hệ>_<phần>`.
- **Cấu hình:** profile `opencode_deepseek_flash` (thinking tắt) và `surplus_glm_5_3` (ghim `dashscope-cn`, `reasoning_effort: none`) trong `configs/config.dev.yaml`; GPU tối đa 2 truy xuất + agent A4/A5 qua `TAM_RERANK_REMOTE_URL`.
