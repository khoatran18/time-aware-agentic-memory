# dataset/organized: bản đồ ngắn

Thư mục gom dữ liệu đã chuẩn hoá. Chi tiết đầy đủ: `docs/process/11_DATA_MAP.md`.

## Cơ chế 3 (Evolution vs Falsehood, cập nhật lúc nạp)

| Cần gì | Ở đâu |
|---|---|
| **Câu hỏi để chấm** (dùng bộ này) | `questions/mech3/<tập>/questions.jsonl` (tune 332, valid 309, test_clean 319 câu) |
| Nhãn chỗ sửa (200 chỗ/tập: C/E/F/A mỗi loại 50) | `past/<tập>/edits.jsonl` |
| Chunk bản quá khứ (id `<id>@past`) | `past/<tập>/chunks/<trang>.txt` |
| Chunk bản mới nhất (real) | `source/<tập>/chunks/<trang>.txt` |

Chưa nạp bản quá khứ vào Qdrant/Neo4j.

Loại chỗ sửa: **C** đổi một năm (code), **E** viết lại thành "còn tiếp diễn" (LLM), **F** thay một giá trị bằng giá trị sai (LLM), **A** diễn đạt lại, nội dung giữ nguyên (đối chứng).
Mỗi câu: `answer` = đáp án theo bản mới nhất; `expect.valid_now` / `stale_now` = chunk đang đúng / chunk cũ; `expect.past_also_valid` = chunk cũ có còn đúng không.

## Các file `vN` trong `past/<tập>/` (lịch sử, không dùng trực tiếp)

- `questions_vN.*` (N = 1, 2, ...): **số lần gộp** các đợt câu hỏi, không phải phiên bản prompt. Mỗi lần viết tay bù thêm câu thì gộp và kiểm mơ hồ lại, tăng N. Bản N lớn nhất là bản cuối, và đã được copy sang `questions/mech3/`.
  - `.final.jsonl`: sau khi LLM trả lời kiểm (bỏ câu rò rỉ kiến thức sẵn có, câu sai). `.audit.jsonl`: kiểm mơ hồ. `.clean.jsonl`: bộ sạch cuối của lần gộp đó.
  - Các đợt gộp: `questions` (sinh tự động), `questions_A2` (chỉ tune: sinh lại loại A bằng prompt mới), `questions_manual*` (viết tay bù chỗ sửa còn thiếu).
- `edits_v5/v6/v8_*.jsonl`, `edits_prev.jsonl`: bản lưu `edits.jsonl` trước mỗi lần sinh lại (v5 = lượt đầu, v6_preE2 = trước khi sinh lại E, v8_pre064swap = trước khi đổi chỗ test_clean-064). `edits.jsonl` là bản dùng.

## Cấu hình sinh (tất cả)

Model `hy4-flash-free` (thinking bật), prompt tiếng Anh, cache `data/llm_cache/past{gen,q,v,amb}_hy4-flash-free/`. Prompt sinh câu hỏi mới nhất dùng cho valid và test_clean (mọi loại) và cho loại A của tune; C/E/F của tune dùng prompt lượt đầu (chưa đối chiếu lại code).
Giới hạn: kiểm rò rỉ chỉ với hy4; câu có/không (E `current`/`historical`, `verify_false`) không kiểm rò rỉ; một số câu A viết tay ở mức trang (`scope: same_page_other_chunk`).
