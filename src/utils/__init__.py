# 工具模块 

from .file_utils import FileUtils
from .driver_utils import create_driver, handle_captcha, wait_for_element, safe_click
from .download_utils import download_file, get_file_size, format_file_size

# 导出常用函数
sanitize_filename = FileUtils.sanitize_filename
ensure_directory = FileUtils.ensure_directory
is_pdf_file = FileUtils.is_pdf_file 

# 新增：计算文件 MD5
import hashlib


def calculate_file_md5(filepath: str) -> str:
    """计算指定文件的 MD5 哈希值 (32位十六进制)"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# 将函数暴露到 utils 命名空间
__all__ = [
    "sanitize_filename",
    "ensure_directory",
    "is_pdf_file",
    "calculate_file_md5",
] 