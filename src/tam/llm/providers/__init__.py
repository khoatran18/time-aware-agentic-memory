"""Import mọi file provider ở đây: import khiến decorator @register_llm chạy và hàm build được ĐĂNG KÝ vào registry
(chưa tạo chat model nào). Thêm provider mới: viết file trong thư mục này rồi thêm MỘT dòng import bên dưới."""
from tam.llm.providers import anthropic, ollama, openai  # noqa: F401
