import pymysql
from typing import List, Dict, Optional
from .config import ScienceConfig

class DatabaseManager:
    """数据库管理器，负责Science文章数据的存储"""
    
    def __init__(self):
        self.config = ScienceConfig()
        self.table_name = self.config.TABLE_NAME
    
    def save_articles_to_database(self, articles: List[Dict]) -> bool:
        """保存文章数据到数据库"""
        if not articles:
            print("没有文章数据需要保存")
            return True
        
        try:
            conn = pymysql.connect(**self.config.DB_CONFIG)
            cursor = conn.cursor()
            
            print(f"开始保存{len(articles)}篇文章到数据库表 {self.table_name}")
            
            for i, article in enumerate(articles):
                try:
                    # 检查是否已存在（通过DOI或标题）
                    if article.get('doi'):
                        cursor.execute(f"SELECT id FROM {self.table_name} WHERE doi=%s", (article['doi'],))
                        if cursor.fetchone():
                            print(f"已存在（DOI）: {article['title']}")
                            continue
                    
                    if article.get('title'):
                        cursor.execute(f"SELECT id FROM {self.table_name} WHERE title=%s", (article['title'],))
                        if cursor.fetchone():
                            print(f"已存在（标题）: {article['title']}")
                            continue
                    
                    # 插入新文章
                    sql = f"""
                    INSERT INTO {self.table_name}
                    (doi, title, authors, journal, abstract, keywords, publication_date, 
                     url, pdf_url, download_path, pdf_md5)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(sql, (
                        article.get('doi'),
                        article.get('title'),
                        ', '.join(article.get('authors', [])) if article.get('authors') else None,
                        article.get('journal', 'Science'),
                        article.get('abstract'),
                        ', '.join(article.get('keywords', [])) if article.get('keywords') else None,
                        article.get('publication_date'),
                        article.get('url'),
                        article.get('pdf_url'),
                        article.get('download_path'),
                        article.get('pdf_md5')
                    ))
                    
                    print(f"保存成功 ({i+1}/{len(articles)}): {article['title']}")
                    
                except Exception as e:
                    print(f"保存文章失败: {article.get('title', 'Unknown')} - {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"数据库保存完成，共处理{len(articles)}篇文章")
            return True
            
        except Exception as e:
            print(f"数据库操作失败: {e}")
            return False
    
    def get_article_count(self) -> int:
        """获取数据库中的文章总数"""
        try:
            conn = pymysql.connect(**self.config.DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"获取文章数量失败: {e}")
            return 0
    
    def get_articles_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        """根据关键词搜索文章"""
        try:
            conn = pymysql.connect(**self.config.DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            sql = f"""
            SELECT * FROM {self.table_name} 
            WHERE title LIKE %s OR abstract LIKE %s OR keywords LIKE %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            search_term = f"%{keyword}%"
            cursor.execute(sql, (search_term, search_term, search_term, limit))
            articles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return articles
            
        except Exception as e:
            print(f"搜索文章失败: {e}")
            return [] 