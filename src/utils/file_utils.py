"""
文件处理工具
"""

import os
import re
from pathlib import Path
from typing import List, Optional
import logging


class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除多余的空格
        filename = re.sub(r'\s+', ' ', filename).strip()
        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    @staticmethod
    def ensure_directory(directory: str) -> Path:
        """
        确保目录存在
        
        Args:
            directory: 目录路径
            
        Returns:
            Path对象
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_extension(filepath: str) -> str:
        """
        获取文件扩展名
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件扩展名
        """
        return Path(filepath).suffix.lower()
    
    @staticmethod
    def is_pdf_file(filepath: str) -> bool:
        """
        检查是否为PDF文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否为PDF文件
        """
        return FileUtils.get_file_extension(filepath) == '.pdf'
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            
        Returns:
            文件路径列表
        """
        path = Path(directory)
        if not path.exists():
            return []
        
        return list(path.glob(pattern))
    
    @staticmethod
    def get_file_size(filepath: str) -> Optional[int]:
        """
        获取文件大小
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            return Path(filepath).stat().st_size
        except Exception:
            return None 