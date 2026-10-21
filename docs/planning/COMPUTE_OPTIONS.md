# Nơi chạy thí nghiệm nặng miễn phí (ghi 2026-10-21)

Ghi từ kiến thức của trợ lý, **chưa kiểm tra lại**; chính sách miễn phí đổi thường xuyên nên xem trang chính thức trước khi dùng. Chưa dùng nơi nào, mọi thí nghiệm đến nay chạy trên laptop (i5-13450HX, 16 luồng; chạy 5+ tiến trình thì CPU ~97°C).

| Nơi | Tài nguyên miễn phí (theo trí nhớ) | Điều khiển từ dòng lệnh? | Ghi chú |
|---|---|---|---|
| Kaggle Notebooks | CPU 4 nhân/~29 GB, hoặc GPU T4/P100 ~30 giờ/tuần, phiên ~9-12 giờ, có internet | Có: `kaggle` CLI (`kernels push/status/output`), cần API token | Hợp nhất cho lưới cross-encoder (GPU) |
| Google Colab (free) | GPU T4 có giới hạn, CPU 2 nhân, hay bị ngắt | Không có API chính thức | Dùng tay |
| Oracle Cloud Always Free | VM ARM tới 4 nhân/24 GB, chạy vĩnh viễn | Có: SSH | Cần thẻ, đôi khi hết chỗ; hợp việc CPU kéo dài |
| GitHub Codespaces | ~60 giờ-nhân/tháng, máy 2 nhân | Có: `gh codespace` | Quá yếu |
| Hugging Face Spaces (free) | 2 vCPU/16 GB | Có: git/API | Yếu |
| Modal | Tín dụng miễn phí hàng tháng, có GPU | Có: Python SDK/CLI | Dễ gọi từ code nhất, hết tín dụng thì dừng |
| Lightning AI | Tín dụng miễn phí, có GPU | Có: SDK/CLI | Tương tự Modal |

## Cần chuẩn bị nếu chuyển sang chạy ngoài
- Mã nguồn, `dataset/`, model embedding (`data/model/embedding`, ~65 MB) và reranker (`data/model/reranker`, bge-v2-m3 ~570 MB).
- Qdrant: code dùng `QdrantClient(url=...)`, nên cần chạy binary Qdrant ở đó hoặc đổi sang chế độ local; nạp lại 6752 điểm (khoảng 4 phút, không LLM).
- Không đưa `.env` (khóa API) lên các nơi này; các lượt cross-encoder không cần khóa LLM.
- GPU cần `fastembed-gpu` và đổi provider onnxruntime (phải sửa code một chút).

## Khi nào đáng dùng
Các việc nặng sắp tới: quét `w2` và `end_mode` với cross-encoder, nhiều bộ nhãn ingest, chia train/valid/test, đo độ trễ từng reranker. Việc còn lại hiện tại (~1,5 giờ) không đáng vì dựng môi trường tốn gần ngang.
