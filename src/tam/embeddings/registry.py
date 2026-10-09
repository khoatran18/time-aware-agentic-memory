"""Sổ đăng ký provider embedding: tên trong yaml (`provider: "fastembed"`) -> class cài đặt.

Dùng:

    @register_dense("fastembed")
    class FastEmbedDense(DenseEmbedder): ...

LƯU Ý THUẬT NGỮ (dễ nhầm):
- "Đăng ký" = ghi CLASS vào dict (DENSE_PROVIDERS["fastembed"] = FastEmbedDense). Lúc này chỉ có class, tức bản thiết kế.
  CHƯA tạo đối tượng (instance), `__init__` CHƯA chạy, model CHƯA được nạp.
- "Tạo đối tượng" = gọi class (FastEmbedDense(...)). Việc này do factory làm về sau, qua `from_profile`.

Thời điểm đăng ký: khi file chứa class được import (lúc Python đọc xong định nghĩa class), không phải lúc tạo đối tượng.
Vì vậy providers/__init__.py phải import từng file provider; nếu không thì file không chạy, dict rỗng và factory báo
"provider chưa hỗ trợ".
"""
from __future__ import annotations

from tam.embeddings.base import DenseEmbedder, SparseEmbedder

# tên provider (khớp `provider:` trong yaml) -> CLASS (chưa phải đối tượng)
DENSE_PROVIDERS: dict[str, type[DenseEmbedder]] = {}
SPARSE_PROVIDERS: dict[str, type[SparseEmbedder]] = {}


def _register(table: dict, name: str):
    """Trả về một decorator sẽ đăng ký class vào `table` dưới tên `name`.

    Vì sao phải có hai tầng hàm: `@` chỉ tự truyền ĐÚNG MỘT đối số (class nằm dưới nó). Mà ta cần thêm `table` và `name`.
    Nên hàm ngoài (`_register`) nhận `table`, `name` rồi trả về hàm trong (`deco`), và `deco` nhớ lại hai giá trị đó.

    Thứ tự khi Python gặp `@register_dense("fastembed")` trên một class:
      1. gọi register_dense("fastembed") -> ra `deco`
      2. định nghĩa xong class FastEmbedDense
      3. gọi deco(FastEmbedDense): Python tự truyền class vào làm `cls`
    """

    def deco(cls):
        # `cls` = CHÍNH CLASS nằm ngay dưới dòng `@` (một class, không phải hàm, không phải đối tượng).
        # Tên "cls" chỉ là quy ước cho tham số kiểu class; Python gán giá trị vào khi gọi ở bước 3.
        if name in table:
            raise ValueError(f"Provider embedding {name!r} đã được đăng ký")
        table[name] = cls  # đăng ký: chỉ ghi class vào dict, chưa tạo đối tượng
        # Giá trị trả về của deco sẽ THAY THẾ tên class trong file provider (FastEmbedDense = deco(FastEmbedDense)).
        # Trả lại đúng `cls` để class giữ nguyên; quên return thì FastEmbedDense trở thành None.
        return cls

    return deco  # trả về hàm (không phải kết quả), vì Python sẽ gọi nó ở bước 3


def register_dense(name: str):
    """Dán lên class kế thừa DenseEmbedder. Đăng ký vào DENSE_PROVIDERS."""
    return _register(DENSE_PROVIDERS, name)


def register_sparse(name: str):
    """Dán lên class kế thừa SparseEmbedder. Đăng ký vào SPARSE_PROVIDERS."""
    return _register(SPARSE_PROVIDERS, name)
