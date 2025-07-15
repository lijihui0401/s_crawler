"""
Science期刊爬虫主程序
使用单线程模式，参考Nature爬虫的实现
"""

import argparse
import json
import logging
from pathlib import Path
from src.crawlers.science_crawler import ScienceCrawler
from src.utils.file_utils import FileUtils
from src.models.article import Article
import pymysql
from datetime import datetime


def setup_logging():
    """设置日志"""
    # 确保logs目录存在
    FileUtils.ensure_directory("logs")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/science_main.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def save_articles_to_json(articles: list, filename: str = "science_articles.json"):
    """保存文章信息到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"文章信息已保存到: {filename}")
    except Exception as e:
        print(f"保存文章信息失败: {e}")


def save_articles_to_mysql(articles, db_config):
    """保存文章到MySQL数据库"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    saved_count = 0
    
    for art in articles:
        # 查重（优先用doi，其次title）
        if art.get('doi'):
            cursor.execute("SELECT id FROM science WHERE doi=%s", (art['doi'],))
            if cursor.fetchone():
                print(f"已存在(DOI重复): {art['title']}")
                continue
        else:
            cursor.execute("SELECT id FROM science WHERE title=%s", (art['title'],))
            if cursor.fetchone():
                print(f"已存在(标题重复): {art['title']}")
                continue
        
        # 插入新文章
        try:
            cursor.execute("""
                INSERT INTO science (title, authors, journal, journal_info, abstract, doi, url, pdf_url, download_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                art.get('title', ''),
                ', '.join(art.get('authors', [])),
                art.get('journal', 'Science'),
                art.get('journal_info', ''),
                art.get('abstract', ''),
                art.get('doi', ''),
                art.get('url', ''),
                art.get('pdf_url', ''),
                art.get('download_path', ''),
                datetime.now()
            ))
            conn.commit()
            saved_count += 1
            print(f"已保存到数据库: {art['title']}")
        except Exception as e:
            print(f"保存失败: {art['title']} - {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print(f"共保存{saved_count}篇文章到数据库")
    return saved_count


def extract_doi_from_url(url):
    """从URL中提取DOI"""
    import re
    # Science的DOI格式可能是 10.1126/science.xxx
    m = re.search(r'doi/([^/?#]+)', url)
    if m:
        return m.group(1)
    return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Science期刊爬虫")
    parser.add_argument("--start-url", type=str, required=True, help="Science搜索结果页URL")
    parser.add_argument("--max-results", "-m", type=int, default=10, help="最大结果数量")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    parser.add_argument("--download-pdfs", action="store_true", help="下载PDF文件")
    parser.add_argument("--use-existing-browser", action="store_true", help="使用已存在的浏览器")
    parser.add_argument("--output", "-o", default="science_articles.json", help="输出文件名")
    parser.add_argument("--download-dir", type=str, default="science_downloads", help="PDF下载目录")
    parser.add_argument("--save-to-db", action="store_true", help="保存到数据库")
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    logger.info("开始运行Science爬虫")
    
    # 确保下载目录存在
    FileUtils.ensure_directory(args.download_dir)
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '12345678',
        'database': 'article_t_a_db',
        'charset': 'utf8mb4'
    }
    
    try:
        with ScienceCrawler(
            headless=args.headless,
            use_existing_browser=args.use_existing_browser,
            download_dir=args.download_dir
        ) as crawler:
            # 抓取文章列表
            print(f"\n开始抓取Science文章...")
            print(f"目标URL: {args.start_url}")
            print(f"最大数量: {args.max_results}")
            print("-" * 60)
            
            # 如果需要保存到数据库，传递db_config进行去重
            articles = crawler.crawl_from_url(
                args.start_url, 
                args.max_results,
                db_config if args.save_to_db else None
            )
            
            if not articles:
                logger.warning("没有抓取到任何文章")
                return
            
            print(f"\n成功抓取{len(articles)}篇文章")
            
            # 获取每篇文章的详细信息
            print("\n获取文章详细信息...")
            for i, article in enumerate(articles, 1):
                print(f"处理 {i}/{len(articles)}: {article['title'][:50]}...")
                crawler.get_article_details(article)
                
                # 尝试从URL提取DOI
                if not article.get('doi') and article.get('url'):
                    doi = extract_doi_from_url(article['url'])
                    if doi:
                        article['doi'] = doi
            
            # 保存到JSON
            save_articles_to_json(articles, args.output)
            
            # 保存到数据库
            if args.save_to_db:
                print("\n保存到数据库...")
                save_articles_to_mysql(articles, db_config)
            
            # 下载PDF
            if args.download_pdfs:
                print("\n开始下载PDF文件...")
                success_count = 0
                for i, article in enumerate(articles, 1):
                    print(f"下载 {i}/{len(articles)}: {article['title'][:50]}...")
                    if crawler.download_pdf(article):
                        success_count += 1
                        # 更新数据库中的下载路径
                        if args.save_to_db and article.get('download_path'):
                            try:
                                conn = pymysql.connect(**db_config)
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE science SET download_path=%s WHERE title=%s",
                                    (article['download_path'], article['title'])
                                )
                                conn.commit()
                                cursor.close()
                                conn.close()
                            except Exception as e:
                                logger.error(f"更新下载路径失败: {e}")
                
                print(f"\nPDF下载完成: {success_count}/{len(articles)} 成功")
            
            # 打印总结
            print("\n" + "=" * 60)
            print("抓取完成！")
            print(f"总文章数: {len(articles)}")
            print(f"输出文件: {args.output}")
            if args.download_pdfs:
                print(f"PDF目录: {args.download_dir}")
            print("=" * 60)
            
    except Exception as e:
        logger.error(f"爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("Science爬虫运行结束")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序异常：{e}")
        import traceback
        traceback.print_exc()