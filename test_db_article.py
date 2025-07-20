#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试文章数据保存到数据库
"""

from src.database_manager import DatabaseManager
import time
import uuid

def main():
    """主函数"""
    print("开始测试文章数据保存...")
    
    # 创建一篇模拟文章数据
    test_article = {
        'title': f'Test Article {time.time()}',  # 添加时间戳确保唯一
        'doi': f'10.1126/science.{uuid.uuid4().hex[:8]}',  # 生成随机DOI
        'url': 'https://www.science.org/doi/10.1126/science.test',
        'pdf_url': 'https://www.science.org/doi/epdf/10.1126/science.test',
        'download_path': 'science_downloads/test_article.pdf',
        'pdf_md5': '123456789abcdef0123456789abcdef0',
        'authors': ['Author One', 'Author Two'],
        'abstract': 'This is a test abstract for database insertion testing.',
        'journal': 'Science',
        'publication_date': '2023-07-15',
        'keywords': 'test, database, insertion'
    }
    
    # 打印文章数据
    print("\n--- 测试文章数据 ---")
    for key, value in test_article.items():
        print(f"{key}: {value}")
    print("-------------------\n")
    
    # 保存到数据库
    db_manager = DatabaseManager()
    result = db_manager.save_articles_to_database([test_article])
    
    print(f"\n保存结果: {result}")
    
    # 查询数据库中的文章总数
    total_count = db_manager.get_article_count()
    print(f"数据库中的文章总数: {total_count}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 