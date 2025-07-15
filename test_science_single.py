#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Science单线程爬虫
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.crawlers.science_crawler import ScienceCrawler


def test_basic_crawl():
    """测试基本爬取功能"""
    print("=" * 60)
    print("测试Science爬虫基本功能")
    print("=" * 60)
    
    # 测试URL
    test_url = "https://www.science.org/action/doSearch?AllField=twist+angle&AfterYear=2010&BeforeYear=2025"
    
    try:
        # 创建爬虫实例
        with ScienceCrawler(use_existing_browser=True) as crawler:
            print(f"\n1. 测试爬取文章列表...")
            print(f"   URL: {test_url}")
            
            # 爬取3篇文章测试
            articles = crawler.crawl_from_url(test_url, max_results=3)
            
            if articles:
                print(f"\n   成功爬取{len(articles)}篇文章:")
                for i, article in enumerate(articles, 1):
                    print(f"   {i}. {article['title'][:60]}...")
                    print(f"      作者: {', '.join(article['authors'][:3])}...")
                    print(f"      DOI: {article.get('doi', 'N/A')}")
                
                # 测试获取详情
                print(f"\n2. 测试获取文章详情...")
                test_article = articles[0]
                crawler.get_article_details(test_article)
                
                print(f"   标题: {test_article['title'][:60]}...")
                print(f"   摘要: {test_article.get('abstract', 'N/A')[:100]}...")
                print(f"   PDF链接: {test_article.get('pdf_url', 'N/A')}")
                
                print("\n✅ 测试通过！爬虫基本功能正常")
            else:
                print("\n❌ 未能爬取到文章，请检查:")
                print("   1. 网络连接是否正常")
                print("   2. 是否已启动Chrome调试模式")
                print("   3. Science网站是否需要登录")
                
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_database_dedup():
    """测试数据库去重功能"""
    print("\n" + "=" * 60)
    print("测试数据库去重功能")
    print("=" * 60)
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '12345678',
        'database': 'article_t_a_db',
        'charset': 'utf8mb4'
    }
    
    try:
        # 创建爬虫实例
        crawler = ScienceCrawler()
        
        # 测试标题
        test_title = "Test Article Title for Deduplication"
        
        # 检查是否存在
        exists = crawler.is_title_exists(test_title, db_config)
        print(f"文章 '{test_title}' 是否存在: {exists}")
        
        print("\n✅ 数据库连接正常")
        
    except Exception as e:
        print(f"\n❌ 数据库测试失败: {e}")
        print("   请检查:")
        print("   1. MySQL服务是否启动")
        print("   2. 数据库配置是否正确")
        print("   3. science表是否已创建")


def main():
    """主函数"""
    print("Science爬虫功能测试\n")
    
    # 运行测试
    test_basic_crawl()
    
    # 询问是否测试数据库
    print("\n" + "-" * 60)
    response = input("是否测试数据库功能? (y/n): ")
    if response.lower() == 'y':
        test_database_dedup()
    
    print("\n测试完成！")
    print("\n下一步:")
    print("1. 如果测试通过，可以运行: python science_main.py --help")
    print("2. 查看使用指南: SCIENCE_CRAWLER_GUIDE.md")


if __name__ == "__main__":
    main()