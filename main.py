"""
Nature期刊爬虫主程序
"""

import argparse
import json
import logging
from pathlib import Path
from src.crawlers.nature_crawler import NatureCrawler
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
            logging.FileHandler('logs/main.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def save_articles_to_json(articles: list, filename: str = "articles.json"):
    """保存文章信息到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"文章信息已保存到: {filename}")
    except Exception as e:
        print(f"保存文章信息失败: {e}")


def save_articles_to_mysql(articles, db_config):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    for art in articles:
        # 查重（优先用doi，其次title）
        if art.get('doi'):
            cursor.execute("SELECT id FROM nature WHERE doi=%s", (art['doi'],))
            if cursor.fetchone():
                print(f"已存在: {art['title']}")
                continue
        elif art.get('title'):
            cursor.execute("SELECT id FROM nature WHERE title=%s", (art['title'],))
            if cursor.fetchone():
                print(f"已存在: {art['title']}")
                continue
        # 插入
        sql = """
        INSERT INTO nature
        (doi, title, authors, journal, abstract, keywords, publication_date, url, pdf_url, download_path, original_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, (
            art.get('doi'),
            art.get('title'),
            ', '.join(art.get('authors', [])),
            art.get('journal'),
            art.get('abstract'),
            ', '.join(art.get('keywords', [])) if art.get('keywords') else None,
            art.get('publication_date'),
            art.get('url'),
            art.get('pdf_url'),
            art.get('download_path'),
            art.get('original_url')
        ))
    conn.commit()
    cursor.close()
    conn.close()
    print("所有新文章已写入数据库。")


def extract_doi_from_url(url):
    import re
    m = re.search(r'/articles/([^/?#]+)', url)
    if m:
        return '10.1038/' + m.group(1)
    return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Nature期刊爬虫")
    parser.add_argument("--query", "-q", required=False, help="搜索关键词")
    parser.add_argument("--max-results", "-m", type=int, default=10, help="最大结果数量")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    parser.add_argument("--download-pdfs", action="store_true", help="下载PDF文件")
    parser.add_argument("--keep-browser", action="store_true", help="保持浏览器打开状态")
    parser.add_argument("--use-existing-browser", action="store_true", help="使用已存在的浏览器")
    parser.add_argument("--output", "-o", default="articles.json", help="输出文件名")
    parser.add_argument("--start-url", type=str, default=None, help="手动筛选后的结果页URL，优先于关键词")
    parser.add_argument("--download-dir", type=str, default="downloads", help="PDF下载目录")
    
    args = parser.parse_args()
    
    # 参数校验：必须提供 --query 或 --start-url 其中之一
    if not args.start_url and not args.query:
        parser.error("必须提供 --query 或 --start-url 其中之一。")
    
    # 设置日志
    logger = setup_logging()
    logger.info("开始运行Nature爬虫")
    
    # 确保下载目录存在
    FileUtils.ensure_directory("downloads")
    
    try:
        with NatureCrawler(
            headless=args.headless,
            use_existing_browser=args.use_existing_browser,
            download_dir=args.download_dir
        ) as crawler:
            # 判断使用哪种入口
            db_config = {
                'host': 'localhost',
                'user': 'root',
                'password': '12345678',
                'database': 'article_t_a_db',
                'charset': 'utf8mb4'
            }
            # 确保提取时查重生效，传递db_config
            if args.start_url:
                logger.info(f"使用自定义入口URL: {args.start_url}")
                articles_data = crawler.crawl_from_url(args.start_url, args.max_results, db_config=db_config)
            else:
                logger.info(f"搜索关键词: {args.query}")
                articles_data = crawler.search_articles(args.query, args.max_results)
            
            if not articles_data:
                logger.warning("未找到任何文章")
                return
            
            # 转换为Article对象
            articles = []
            for data in articles_data:
                doi = extract_doi_from_url(data.get('url', ''))
                article = Article(
                    title=data.get('title', ''),
                    url=data.get('url', ''),
                    authors=data.get('authors', []),
                    journal=data.get('journal', ''),
                    abstract=data.get('abstract', ''),
                    doi=doi
                )
                articles.append(article)
            
            # 保存文章信息
            articles_dict = [article.to_dict() for article in articles]
            save_articles_to_json(articles_dict, args.output)

            # 下载PDF文件并写入数据库（每篇文章）
            for i, article in enumerate(articles):
                logger.info(f"下载第 {i+1}/{len(articles)} 篇文章: {article.title}")
                pdf_filename = FileUtils.sanitize_filename(article.title) + ".pdf"
                info = crawler.download_pdf(article.url, filename=pdf_filename)
                if info and info.get('success'):
                    # 自动更新Article对象的所有字段，处理publication_date类型
                    for k, v in info.items():
                        if k == "publication_date" and isinstance(v, str) and v:
                            try:
                                v = datetime.fromisoformat(v)
                            except Exception:
                                v = None
                        if hasattr(article, k):
                            setattr(article, k, v)
                    article.download_path = f"{args.download_dir}/{pdf_filename}"
                    logger.info(f"PDF下载成功: {article.title}")
                else:
                    logger.warning(f"PDF下载失败: {article.title}")
            # 下载完所有PDF后，统一写入数据库
            articles_dict = [a.to_dict() for a in articles]
            save_articles_to_mysql(articles_dict, db_config)
            
            logger.info("爬虫任务完成")
            
            # 如果指定保持浏览器打开，则等待用户手动关闭
            if args.keep_browser:
                logger.info("浏览器将保持打开状态，请手动关闭浏览器窗口")
                input("按回车键关闭浏览器...")
                crawler.close_manual()
            
    except Exception as e:
        logger.error(f"爬虫运行失败: {e}")
        raise


if __name__ == "__main__":
    main() 