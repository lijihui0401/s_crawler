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
                    # 检查是否已存在（优先 DOI）
                    # 1. 先按 DOI 去重（只要 DOI 不重复，就允许写入）
                    if article.get('doi'):
                        cursor.execute(f"SELECT id FROM {self.table_name} WHERE doi=%s", (article['doi'],))
                        if cursor.fetchone():
                            print(f"已存在（DOI）: {article['title']}")
                            continue
                    
                    # 2. 当 DOI 为空时，再按 MD5 查重
                    if (not article.get('doi')) and article.get('pdf_md5'):
                        cursor.execute(f"SELECT id FROM {self.table_name} WHERE pdf_md5=%s", (article['pdf_md5'],))
                        if cursor.fetchone():
                            print(f"已存在（MD5）(无DOI): {article['title']}")
                            continue
                    
                    # 3. 若 DOI、MD5 均为空，再按标题查重
                    if (not article.get('doi')) and (not article.get('pdf_md5')) and article.get('title'):
                        cursor.execute(f"SELECT id FROM {self.table_name} WHERE title=%s", (article['title'],))
                        if cursor.fetchone():
                            print(f"已存在（标题）(无DOI/MD5): {article['title']}")
                            continue
                    
                    # 插入新文章
                    sql = f"""
                    INSERT INTO {self.table_name}
                    (doi, title, authors, journal, abstract, keywords, publication_date, 
                     url, pdf_url, download_path, pdf_md5)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # 打印完整的参数值，便于调试
                    print(f"准备插入文章: {article.get('title')}")
                    print(f"DOI: {article.get('doi')}")
                    print(f"URL: {article.get('url')}")
                    print(f"PDF URL: {article.get('pdf_url')}")
                    print(f"下载路径: {article.get('download_path')}")
                    print(f"PDF MD5: {article.get('pdf_md5')}")
                    
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
                    # 打印更详细的错误信息
                    import traceback
                    traceback.print_exc()
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"数据库保存完成，共处理{len(articles)}篇文章")
            return True
            
        except Exception as e:
            print(f"数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
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

    def is_doi_exists(self, doi: str) -> bool:
        """判断指定DOI是否已存在于数据库"""
        try:
            conn = pymysql.connect(**self.config.DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {self.table_name} WHERE doi=%s", (doi,))
            exists = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return exists
        except Exception as e:
            print(f"DOI查重失败: {e}")
            return False 