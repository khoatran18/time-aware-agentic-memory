"""Import mọi file provider ở đây: import khiến file chạy, decorator @register_* chạy, class được ĐĂNG KÝ vào registry
(chưa tạo đối tượng nào). Không import ở đây thì không ai import các file này nữa, registry rỗng.
Thêm provider mới: viết file trong thư mục này rồi thêm MỘT dòng import bên dưới."""
from tam.embedding.providers import fastembed  # noqa: F401
