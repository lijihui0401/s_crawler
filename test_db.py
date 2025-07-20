# 测试数据库连接和插入操作
from src.database_manager import DatabaseManager

# 创建一个简单的测试文章
test_article = {
    'title': 'Test Article',
    'doi': 'test.doi.123456',
    'url': 'https://example.com',
    'pdf_url': 'https://example.com/pdf',
    'download_path': 'test.pdf',
    'pdf_md5': '123456789abcdef'
}

# 尝试保存到数据库
db_manager = DatabaseManager()
result = db_manager.save_articles_to_database([test_article])
print(f"保存结果: {result}")