"""
基本功能测试
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.article import Article
from src.utils.file_utils import FileUtils


class TestArticle(unittest.TestCase):
    """测试Article类"""
    
    def test_article_creation(self):
        """测试文章创建"""
        article = Article(
            title="Test Article",
            url="https://www.nature.com/articles/test",
            authors=["Author 1", "Author 2"],
            journal="Nature",
            abstract="This is a test abstract.",
            doi="10.1038/test"
        )
        
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.url, "https://www.nature.com/articles/test")
        self.assertEqual(article.authors, ["Author 1", "Author 2"])
        self.assertEqual(article.journal, "Nature")
        self.assertEqual(article.abstract, "This is a test abstract.")
        self.assertEqual(article.doi, "10.1038/test")
    
    def test_article_to_dict(self):
        """测试文章转字典"""
        article = Article(
            title="Test Article",
            url="https://www.nature.com/articles/test",
            authors=["Author 1"],
            journal="Nature",
            abstract="Test abstract",
            doi="10.1038/test"
        )
        
        article_dict = article.to_dict()
        
        self.assertIsInstance(article_dict, dict)
        self.assertEqual(article_dict["title"], "Test Article")
        self.assertEqual(article_dict["authors"], ["Author 1"])
        self.assertEqual(article_dict["doi"], "10.1038/test")


class TestFileUtils(unittest.TestCase):
    """测试FileUtils类"""
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        # 测试特殊字符清理
        dirty_name = "Test/File:Name*with?special<characters>"
        clean_name = FileUtils.sanitize_filename(dirty_name)
        
        self.assertNotIn("/", clean_name)
        self.assertNotIn(":", clean_name)
        self.assertNotIn("*", clean_name)
        self.assertNotIn("?", clean_name)
        self.assertNotIn("<", clean_name)
        self.assertNotIn(">", clean_name)
        
        # 测试中文字符
        chinese_name = "测试文件名"
        clean_chinese = FileUtils.sanitize_filename(chinese_name)
        self.assertEqual(clean_chinese, "测试文件名")
        
        # 测试空字符串
        empty_name = ""
        clean_empty = FileUtils.sanitize_filename(empty_name)
        self.assertEqual(clean_empty, "untitled")
    
    def test_ensure_directory(self):
        """测试目录创建"""
        test_dir = "test_directory"
        
        # 确保目录存在
        FileUtils.ensure_directory(test_dir)
        
        # 检查目录是否存在
        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(os.path.isdir(test_dir))
        
        # 清理测试目录
        if os.path.exists(test_dir):
            os.rmdir(test_dir)


if __name__ == "__main__":
    unittest.main() 