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
    """
    下载文件，支持自定义cookie和user-agent，并严格校验为PDF
    """
    headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    session = requests.Session()
    if cookies:
        headers['Cookie'] = cookies
    for attempt in range(max_retries):
        try:
            logger.info(f"开始下载: {url}")
            logger.info(f"保存到: {filepath}")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            response = session.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.error(f"下载失败: Content-Type不是PDF, 而是: {content_type}")
                return False
            # 检查文件头
            iter_content = response.iter_content(chunk_size=8192)
            try:
                first_chunk = next(iter_content)
            except StopIteration:
                logger.error("下载失败: 文件内容为空")
                return False
            if b'%PDF' not in first_chunk[:10]:
                logger.error("下载失败: 文件头不是PDF标志")
                return False
            with open(filepath, 'wb') as f:
                f.write(first_chunk)
                for chunk in iter_content:
                    if chunk:
                        f.write(chunk)
            logger.info(f"下载完成: {filepath}")
            return True
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