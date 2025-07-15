"""
文章数据模型
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Article:
    """文章数据模型"""
    
    title: str
    url: str
    authors: List[str]
    journal: str
    abstract: str
    doi: Optional[str] = None
    publication_date: Optional[datetime] = None
    keywords: Optional[List[str]] = None
    pdf_url: Optional[str] = None
    download_path: Optional[str] = None
    original_url: Optional[str] = None  # 原始Nature URL，用于第三方镜像站点
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "url": self.url,
            "authors": self.authors,
            "journal": self.journal,
            "abstract": self.abstract,
            "doi": self.doi,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "keywords": self.keywords,
            "pdf_url": self.pdf_url,
            "download_path": self.download_path,
            "original_url": self.original_url
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Article':
        """从字典创建对象"""
        publication_date = None
        if data.get('publication_date'):
            try:
                publication_date = datetime.fromisoformat(data['publication_date'])
            except:
                pass
        
        return cls(
            title=data['title'],
            url=data['url'],
            authors=data.get('authors', []),
            journal=data.get('journal', ''),
            abstract=data.get('abstract', ''),
            doi=data.get('doi'),
            publication_date=publication_date,
            keywords=data.get('keywords', []),
            pdf_url=data.get('pdf_url'),
            download_path=data.get('download_path'),
            original_url=data.get('original_url')
        ) 