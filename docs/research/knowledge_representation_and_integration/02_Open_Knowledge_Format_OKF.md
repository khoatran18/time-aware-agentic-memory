# Open Knowledge Format (OKF) và mẫu "LLM wiki"

> ⚠️ **Đã cũ một phần:** file này viết dựa trên bản **v0.1** và tin tức. Bản hiện hành là **v0.2** (thêm các trường `sources` nguồn gốc, `generated` thông tin lúc sinh ra file, `verified` đã được kiểm chứng chưa, `status` trạng thái, `stale_after` thời điểm sau đó nội dung được coi là cũ; trường `timestamp` bị thay bằng `generated.at`). **Đọc [`09_OKF_v0.2_Spec.md`](09_OKF_v0.2_Spec.md)** (đặc tả đã đọc trực tiếp) và [`10_Karpathy_LLM_Wiki.md`](10_Karpathy_LLM_Wiki.md) (gist gốc) thay cho §1–§3 dưới đây; các bảng đối chiếu với đồ án ở `09` §9 thay thế bảng §3.

> OKF (Open Knowledge Format, định dạng mở lưu tri thức) bản v0.1 do Google Cloud công bố ngày **12/06/2026** (theo tin tức), là định dạng mở để đưa tri thức cho agent (chương trình dùng LLM để tự lập kế hoạch và gọi công cụ) dưới dạng **thư mục các file markdown** (markdown là kiểu văn bản thuần có ký hiệu định dạng đơn giản như `#` cho tiêu đề, file đuôi `.md`). Mỗi file có một khối YAML ở đầu (gọi là frontmatter, xem §2) chứa thông tin mô tả file. OKF chính thức hóa mẫu "LLM wiki" mà Andrej Karpathy phổ biến (gist, tức ghi chú đăng trên GitHub, ngày 03/04/2026 theo [Atlan](https://atlan.com/know/llm-wiki-vs-rag-knowledge-base/)); LLM (Large Language Model) là mô hình ngôn ngữ lớn như Claude, GPT, Gemini, còn wiki ở đây là một bộ trang tri thức liên kết với nhau. Đây là đúng loại "định dạng mở, không quá mịn" mà đề tài đang tìm hiểu.

## 1. Mẫu LLM wiki (Karpathy)

- Ý tưởng **[blog]**: thay vì embed tài liệu (biến văn bản thành dãy số biểu diễn ý nghĩa, gọi là embedding, để tìm theo độ giống nghĩa) rồi truy xuất lúc hỏi theo kiểu RAG (Retrieval-Augmented Generation: tìm đoạn tài liệu liên quan rồi đưa cho LLM đọc để trả lời), thì để **LLM "biên dịch" tài liệu thô thành một wiki markdown** gồm các trang tổng hợp + file `index` (trang mục lục) giúp agent định hướng; agent (ví dụ Claude Code) đọc/ghi wiki, còn Obsidian (ứng dụng ghi chú dùng file markdown) chỉ để con người xem.
- LLM định kỳ chạy "health check" (kiểm tra sức khỏe: rà lại toàn bộ wiki) để tìm mâu thuẫn và mục lỗi thời.
- Giới hạn quy mô: các nguồn bất đồng. Token (đơn vị văn bản mà LLM xử lý, khoảng một âm tiết hoặc một phần từ) là đơn vị đo ở đây: một nguồn nói tốt dưới ~50K–100K token, nguồn khác nói cá nhân 500K–2M token vẫn ổn nhưng **quy mô tổ chức vẫn cần RAG** ([MindStudio](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison), [lmmarketcap](https://lmmarketcap.com/reports/llm-knowledge-bases-karpathy)). Con số "giảm 95% token" là của vendor blog (blog của chính nhà cung cấp sản phẩm), chưa kiểm chứng.
- Ta chưa đọc gist gốc; mọi chi tiết ở trên là second-hand.

## 2. Đặc tả OKF v0.1 (đã đọc từ trang của Google Cloud)

| Thành phần | Quy định |
|---|---|
| Đơn vị | **Bundle** (gói) = một thư mục; **mỗi file `.md` là một concept** (một khái niệm hoặc đối tượng, ví dụ một bảng dữ liệu); đường dẫn file là danh tính concept |
| Frontmatter YAML | Bắt buộc duy nhất: `type`. Tùy chọn, có thể truy vấn: `title`, `description`, `resource`, `tags`, `timestamp` |
| Thân file | Markdown tự do, producer tự chọn các mục |
| Liên kết | Link markdown thông thường giữa các concept, tạo thành **đồ thị** (các file là nút, link là cạnh) vượt ra ngoài cây thư mục |
| File dành riêng | `index.md` (tiết lộ dần khi agent đi qua cây thư mục), `log.md` (lịch sử thay đổi theo thời gian) |
| Triết lý | Tối thiểu hóa quy định; producer và consumer độc lập; "format, not platform" |
| Công cụ tham chiếu | Agent làm giàu cho BigQuery, trình hiển thị HTML tĩnh, 3 bundle mẫu (GA4, Stack Overflow, Bitcoin) |
| Tích hợp | Google Knowledge Catalog nạp và phục vụ bundle cho agent |

Giải thích nhanh: **YAML** là định dạng văn bản khai báo dạng "khóa: giá trị", đặt giữa hai dòng `---` ở đầu file markdown; khối này gọi là **frontmatter** và chứa metadata (dữ liệu mô tả, như tiêu đề, nhãn). **Producer** là bên tạo ra bundle, **consumer** là bên đọc và dùng nó (ví dụ một agent). "Format, not platform" nghĩa là OKF chỉ quy định định dạng file, không bắt dùng một nền tảng nào. **BigQuery** là kho dữ liệu phân tích của Google Cloud; **GA4** là Google Analytics 4 (công cụ thống kê lượng truy cập web); **Knowledge Catalog** là dịch vụ danh mục tri thức của Google Cloud.

Repo: <https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf>. Ta chưa đọc trực tiếp repo/spec đầy đủ, chỉ đọc bản mô tả của Google Cloud và tin tức.

Ví dụ concept (rút gọn từ spec):

```markdown
---
type: BigQuery Table
title: Orders
description: One row per completed customer order.
tags: [sales, revenue]
timestamp: 2026-05-28T14:30:00Z
---
# Schema ...
Joined with [customers](/tables/customers.md) on `customer_id`.
```

## 3. OKF so với nhu cầu time-aware

| Nhu cầu của đồ án | OKF v0.1 có gì | Khoảng trống |
|---|---|---|
| Thời gian hiệu lực `[start_time, end_time]` | Chỉ có `timestamp` tùy chọn (ý nghĩa do producer tự định) | Không có khoảng hiệu lực; phải tự thêm trường |
| Phân biệt Evolution và Falsehood (`end_time` vs `invalidated_at`) | Không có | Tự thêm trường |
| Quan hệ `SUPERSEDES`/`CORRECTS` | Link markdown trơn, **không có kiểu cạnh** | Phải mã hóa kiểu quan hệ (trong frontmatter hoặc quy ước đặt tên mục) |
| Lịch sử thay đổi | `log.md` (ở cấp bundle) | Không đủ để truy vấn "trạng thái tại thời điểm T" một cách có cấu trúc |
| Chunk theo điều/khoản + hash nội dung | Mỗi file là một concept, tự do cấu trúc | Hoàn toàn dựng được: 1 file = 1 điều khoản **[suy luận]** |

Giải thích nhanh các thuật ngữ của đồ án trong bảng: `[start_time, end_time]` là khoảng thời gian một thông tin còn đúng ngoài đời (ví dụ ông A làm giám đốc từ 2020 đến 2023). **Evolution** (tiến hóa) là sự việc từng đúng rồi thay đổi theo thời gian, ví dụ nhân viên lên giám đốc; xử lý bằng cách đóng `end_time` của trạng thái cũ. **Falsehood** (sai lầm) là thông tin sai ngay từ đầu, ví dụ tin đồn bị đính chính; đánh dấu bằng `invalidated_at` (thời điểm phát hiện là không hợp lệ). `SUPERSEDES` là "thay thế" (thông tin mới thay thông tin cũ), `CORRECTS` là "đính chính" (sửa thông tin sai); kiểu cạnh là nhãn cho biết hai nút liên hệ với nhau như thế nào. **Chunk theo điều/khoản** là cắt văn bản luật theo từng điều để mỗi đoạn là một đơn vị trọn vẹn; **hash nội dung** là mã băm (dấu vân tay) của đoạn văn, hai đoạn giống hệt nhau thì hash giống nhau nên nhận ra được nội dung không đổi.

Vì spec **cố ý tối thiểu** và cho phép trường mở rộng ("producer decides which extra fields"), có thể xem OKF là **lớp vỏ trao đổi** và đặt các trường time-aware (có nhận biết thời gian) của đồ án lên trên như một *profile* (bộ quy ước bổ sung do mình định nghĩa, dùng chung định dạng nền của OKF).

## 4. Ưu nhược của OKF

**Ưu**
- Rất rẻ và dễ kiểm tra; con người đọc/sửa được; git cho sẵn lịch sử.
- Tương thích mọi công cụ (grep là lệnh tìm chuỗi trong file; vector search là tìm theo độ giống nghĩa; agent đọc file).
- Vendor-neutral (không phụ thuộc một nhà cung cấp nào), được một công ty lớn đứng sau, hợp thành "ngôn ngữ chung" (lingua franca) cho tri thức của agent ([ppc.land](https://ppc.land/googles-okf-wants-to-be-the-lingua-franca-for-ai-agent-knowledge/)).

**Nhược**
- v0.1, Google tự nhận sẽ còn tiến hóa; **mức độ chấp nhận chưa rõ**.
- Ngữ nghĩa nghèo: không kiểu cạnh, không thời gian hiệu lực, không độ tin cậy nguồn.
- Chất lượng giữa các producer có thể không đồng nhất (mỗi nơi tự định nghĩa `type`).
- Ở quy mô lớn một thư mục file không thay thế được index (chỉ mục giúp tìm nhanh): vector (tìm theo nghĩa), BM25 (thuật toán xếp hạng theo từ khóa, đếm mức trùng từ giữa câu hỏi và văn bản) và filter (lọc theo điều kiện).

## 5. Nguồn

- [Google Cloud — How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [The Decoder — OKF turns scattered docs into markdown files for AI agents](https://the-decoder.com/google-clouds-open-knowledge-format-turns-scattered-docs-into-markdown-files-for-ai-agents/)
- [heise — Open Knowledge Format](https://heise.de/-11332310), [ppc.land](https://ppc.land/googles-okf-wants-to-be-the-lingua-franca-for-ai-agent-knowledge/)
- [Atlan — LLM wiki vs RAG](https://atlan.com/know/llm-wiki-vs-rag-knowledge-base/), [MindStudio](https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison)

## Tài liệu tham khảo (docs, git)

- **Repo hiện hành (v0.2):** [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (repo hiện hành, có `SPEC.md`)
- **Repo cũ (v0.1):** [GoogleCloudPlatform/knowledge-catalog/okf](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (bản đóng băng, không còn bảo trì)
- **Gist LLM Wiki:** [Karpathy — LLM Wiki (gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
