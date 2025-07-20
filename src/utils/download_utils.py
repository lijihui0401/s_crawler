"""
下载工具模块
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def download_file(url: str, filepath: str, timeout: int = 30, max_retries: int = 3, cookies: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
    """下载文件到本地"""
    import time
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 创建session
    session = requests.Session()
    
    # 处理cookie
    if isinstance(cookies, str):
        for item in cookies.split(";"):
            if "=" in item:
                name, value = item.strip().split("=", 1)
                session.cookies.set(name, value)
    
    # 设置headers
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"开始下载: {url}")
            logger.info(f"保存到: {filepath}")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            response = session.get(url, headers=headers, timeout=timeout, stream=True)
            
            # 改进的状态码处理
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                
                # 检查内容类型
                if 'application/pdf' in content_type or 'octet-stream' in content_type:
                    pass  # 内容类型正确，继续处理
                else:
                    # 内容类型不匹配，检查文件头
                    logger.warning(f"内容类型不是PDF: {content_type}，检查文件头")
                    first_chunk = next(response.iter_content(chunk_size=8192), None)
                    if not first_chunk or b'%PDF' not in first_chunk[:10]:
                        logger.error("下载失败: 文件头不是PDF标志")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                        continue  # 跳过当前重试，进入下一次循环
                    logger.info("文件头确认为PDF，继续下载")
                    
                # 写入文件
                with open(filepath, 'wb') as f:
                    # 如果已经读取了第一块，先写入
                    if 'first_chunk' in locals() and first_chunk:
                        f.write(first_chunk)
                    # 继续读取和写入剩余内容
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                # 下载后再次验证文件
                if os.path.getsize(filepath) < 1000:  # 小于1KB可能有问题
                    with open(filepath, 'rb') as f:
                        content = f.read(10)
                        if b'%PDF' not in content:
                            logger.error(f"下载的文件不是有效PDF，大小: {os.path.getsize(filepath)} 字节")
                            os.remove(filepath)  # 删除无效文件
                            if attempt < max_retries - 1:
                                time.sleep(2 ** attempt)
                            continue  # 尝试下一次重试
                            
                logger.info(f"下载完成: {filepath}")
                return True
            else:
                logger.warning(f"下载失败: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"下载最终失败: {url}")
                    return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"下载最终失败: {url}")
                return False
        except Exception as e:
            logger.error(f"下载时发生未知错误: {e}")
            return False
            
    return False


def get_file_size(filepath: str) -> Optional[int]:
    """
    获取文件大小
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件大小（字节），如果文件不存在返回None
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return None


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def is_valid_pdf_url(url: str) -> bool:
    """
    检查URL是否为有效的PDF链接
    
    Args:
        url: URL字符串
        
    Returns:
        是否为有效的PDF链接
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        return path.endswith('.pdf') or 'pdf' in path
    except Exception:
        return False


def get_filename_from_url(url: str) -> str:
    """
    从URL中提取文件名
    
    Args:
        url: URL字符串
        
    Returns:
        文件名
    """
    try:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = "download.pdf"
        return filename
    except Exception:
        return "download.pdf" 