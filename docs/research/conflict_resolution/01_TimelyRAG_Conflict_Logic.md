# Nghiên cứu: Xử lý Xung đột Dữ liệu & Cập nhật Luồng tin (Conflict Resolution)

## 1. Định nghĩa bài toán
Trong các hệ thống Agentic Memory, dữ liệu không tĩnh mà liên tục biến động. "Xung đột" ở đây không hẳn là lỗi của tài liệu, mà là sự phản ánh quá trình tiến hóa của thông tin theo thời gian thực (Streaming Updates).

Dựa trên thực tế báo chí, đồ án chia bài toán mâu thuẫn thành 2 dạng xung đột chính:
1. **Xung đột tuyến tính (Sự tiến hóa / Ghi đè thông tin):**
   - *Ví dụ vụ án án mạng:* 
     - Ngày 1: Báo đưa tin Nguyễn Văn A là nghi phạm chính.
     - Ngày 3: Báo đưa tin (đính chính): Bắt được hung thủ thật là Trần Văn B, Nguyễn Văn A bị oan.
   - *Bản chất:* Không phải tờ báo nói dối, mà là thông tin đã được "cập nhật". RAG truyền thống sẽ bối rối vì cả 2 bài báo đều chứa từ khóa "hung thủ", "Nguyễn Văn A". Nếu LLM đọc nhầm bài Ngày 1, nó sẽ vu oan cho A.
2. **Xung đột đa nguồn (Mâu thuẫn cùng thời điểm):**
   - *Ví dụ:* Sáng Ngày 3, Báo Chính Thống nói "B là hung thủ", nhưng cùng lúc đó một Blog cá nhân giật tít "A đã nhận tội".
   - *Bản chất:* Hai nguồn tin đối lập nhau tại đúng một mốc thời gian. Lúc này yếu tố thời gian là hòa, hệ thống phải xét đến độ tin cậy.

## 2. Giải pháp: Thuật toán Re-ranking Kép (Thời gian + Uy tín)
Để giải quyết triệt để Cơ chế số 3 trong Đồ án, hệ thống RAG không thể chỉ dựa vào Vector Ngữ nghĩa. Kế thừa tư tưởng của **TimelyRAG**, chúng ta thiết kế một tầng **Xếp hạng lại (Re-ranker)**.

Công thức xếp hạng cuối cùng:
`Final_Score = (W1 * Semantic_Score) + (W2 * Temporal_Score) + (W3 * Credibility_Score)`

Trong đó:
- `Semantic_Score`: Độ giống nhau về câu chữ (Lấy từ VectorDB gốc).
- `Temporal_Score`: Khoảng cách thời gian (Dùng hàm phân rã Exponential Decay). Tin càng xa thời điểm được hỏi thì điểm càng tụt dần về 0. Trị dứt điểm **Xung đột tuyến tính**.
- `Credibility_Score`: Điểm uy tín của nguồn tin (Được gán cứng vào Metadata lúc lưu data, ví dụ: Báo lớn = 1.0, Blog = 0.5). Trị dứt điểm **Xung đột đa nguồn**.

## 3. Kiến trúc Pipeline
- **Bước 1 (Retrieval):** Người dùng hỏi *"Hiện tại ai là hung thủ?"*. VectorDB truy xuất lên 5 đoạn văn giống nhau nhất (chứa cả tin Ngày 1, Ngày 3, Báo Chính Thống, Blog Lá Cải).
- **Bước 2 (Re-ranking):** Code Python chạy vòng lặp qua 5 đoạn văn, áp dụng công thức để tính lại điểm.
- **Bước 3 (Generation):** Tài liệu Ngày 3 của Báo Chính Thống có điểm cao nhất, vươn lên Top 1. LLM chỉ đọc tài liệu Top 1 và tự tin chốt câu trả lời cuối cùng.

## 4. Ví dụ Code Python (Pseudo-code)

Dưới đây là mô phỏng thuật toán Reranking cốt lõi của Cơ chế 3:

```python
import math

def calculate_temporal_score(query_timestamp, doc_timestamp):
    # Hàm phân rã thời gian (Exponential Decay)
    # Khoảng cách thời gian tính bằng NGÀY (thay vì NĂM như Luật pháp)
    time_diff_days = abs(query_timestamp - doc_timestamp)
    # Hệ số 0.2 giúp điểm rớt mạnh nếu tin qua 1, 2 ngày
    return math.exp(-0.2 * time_diff_days) 

def conflict_resolution_reranker(query_timestamp, retrieved_docs):
    """
    Mô phỏng 3 đoạn văn được VectorDB kéo lên:
    retrieved_docs = [
        {"source": "VnExpress", "credibility": 1.0, "time": 1, "text": "A là nghi phạm", "semantic_score": 0.95},
        {"source": "VnExpress", "credibility": 1.0, "time": 3, "text": "B là thủ phạm, A bị oan", "semantic_score": 0.92},
        {"source": "Blog_X",    "credibility": 0.3, "time": 3, "text": "A đã nhận tội", "semantic_score": 0.96}
    ]
    """
    # Trọng số (Tùy chỉnh lúc chạy thực nghiệm đồ án)
    W_SEM = 0.4  # Ngữ nghĩa
    W_TIME = 0.4 # Thời gian
    W_CRED = 0.2 # Độ uy tín nguồn
    
    reranked_results = []
    
    for doc in retrieved_docs:
        # 1. Tính điểm thời gian so với Ngày hiện tại (Ví dụ: query_timestamp = Ngày 3)
        time_score = calculate_temporal_score(query_timestamp, doc['time'])
        
        # 2. TÍNH TỔNG ĐIỂM FUSION
        final_score = (W_SEM * doc['semantic_score']) + \
                      (W_TIME * time_score) + \
                      (W_CRED * doc['credibility'])
                      
        reranked_results.append({
            "text": doc['text'],
            "source": doc['source'],
            "final_score": final_score,
            "details": f"Sem:{doc['semantic_score']} | Time:{time_score:.2f} | Cred:{doc['credibility']}"
        })
    
    # 3. Sắp xếp lại từ cao xuống thấp
    return sorted(reranked_results, key=lambda x: x["final_score"], reverse=True)

# ==========================================
# PHÂN TÍCH KẾT QUẢ KHI CHẠY CODE TRÊN:
# ==========================================
# Dù "Blog_X" có điểm Semantic cực cao (0.96), nhưng:
# - Bài báo "A là nghi phạm" (Ngày 1) sẽ bị dìm vì time_score rớt thê thảm do cách 2 ngày.
# - Blog "A nhận tội" (Ngày 3) có time_score cao, nhưng credibility quá thấp (0.3) -> Bị dìm điểm tổng.
# - Báo "B là thủ phạm" (Ngày 3) -> Thắng tuyệt đối ở cả time_score và credibility -> TOP 1!
```
