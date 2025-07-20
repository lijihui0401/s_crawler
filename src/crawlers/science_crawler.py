"""
Science期刊爬虫
基于Selenium实现，模拟真实用户行为
参考Nature爬虫的单线程模式
"""

import time
import random
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import os
from pathlib import Path
import pymysql


class ScienceCrawler:
    """Science期刊爬虫类"""
    
    def __init__(self, headless: bool = False, download_dir: str = "science_downloads", use_existing_browser: bool = False):
        """
        初始化爬虫
        
        Args:
            headless: 是否无头模式运行
            download_dir: 下载目录
            use_existing_browser: 是否使用已存在的浏览器
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化浏览器
        self.driver = None
        self.headless = headless
        self.use_existing_browser = use_existing_browser
        self._setup_driver()
        
        # Science基础URL
        self.base_url = "https://www.science.org"
        
    def _setup_logging(self):
        """设置日志"""
        # 确保logs目录存在
        os.makedirs("logs", exist_ok=True)
        
        self.logger = logging.getLogger('ScienceCrawler')
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        fh = logging.FileHandler('logs/science_crawler.log', encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 格式器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def _setup_driver(self):
        """设置Chrome驱动"""
        try:
            if self.use_existing_browser:
                # 连接到已存在的浏览器
                options = Options()
                options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                self.driver = webdriver.Chrome(options=options)
                self.logger.info("已连接到现有浏览器")
            else:
                # 创建新的浏览器实例
                options = Options()
                
                if self.headless:
                    options.add_argument('--headless')
                
                # 设置下载目录
                prefs = {
                    "download.default_directory": str(self.download_dir.absolute()),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": False
                }
                options.add_experimental_option("prefs", prefs)
                
                # 其他选项
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # 随机User-Agent
                ua = UserAgent()
                options.add_argument(f'user-agent={ua.random}')
                
                # 创建驱动
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                
                # 执行CDP命令
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
                })
                
                self.logger.info("Chrome驱动设置完成")
                
        except Exception as e:
            self.logger.error(f"设置Chrome驱动失败: {e}")
            raise
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.driver and not self.use_existing_browser:
            self.driver.quit()
            self.logger.info("浏览器已关闭")
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机延时"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def is_title_exists(self, title: str, db_config: dict) -> bool:
        """检查文章标题是否已存在于数据库"""
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM science WHERE title=%s", (title,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        except Exception as e:
            self.logger.error(f"数据库查询失败: {e}")
            return False
    
    def crawl_from_url(self, start_url: str, max_results: int = 10, db_config: dict = None) -> List[Dict]:
        """
        从指定的搜索结果页开始抓取
        
        Args:
            start_url: 搜索结果页URL
            max_results: 最大抓取数量
            db_config: 数据库配置，用于去重
            
        Returns:
            文章信息列表
        """
        try:
            self.logger.info(f"开始从URL抓取: {start_url}")
            self.driver.get(start_url)
            self.random_delay(2.0, 3.0)
            
            articles = []
            current_url = start_url
            page = 1
            
            while len(articles) < max_results:
                self.logger.info(f"正在处理第{page}页...")
                
                # 等待页面加载
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-result-list"))
                    )
                except TimeoutException:
                    self.logger.warning("页面加载超时")
                    break
                
                # 获取所有文章元素
                article_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "div.card.pb-3.border-bottom"
                )
                
                if not article_elements:
                    self.logger.info("未找到文章，结束抓取")
                    break
                
                # 提取每篇文章的信息
                for article_elem in article_elements:
                    if len(articles) >= max_results:
                        break
                    
                    try:
                        article_info = self._extract_article_info(article_elem)
                        if article_info:
                            # 数据库去重
                            if db_config and self.is_title_exists(article_info['title'], db_config):
                                self.logger.info(f"文章已存在，跳过: {article_info['title']}")
                                continue
                            
                            articles.append(article_info)
                            self.logger.info(f"成功提取文章 {len(articles)}: {article_info['title']}")
                        
                        self.random_delay(0.5, 1.5)
                        
                    except Exception as e:
                        self.logger.warning(f"提取文章信息失败: {e}")
                        continue
                
                # 尝试进入下一页
                if len(articles) < max_results:
                    if not self._go_to_next_page():
                        self.logger.info("没有更多页面，结束抓取")
                        break
                    page += 1
                    self.random_delay(2.0, 3.0)
            
            self.logger.info(f"抓取完成，共获取{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            self.logger.error(f"抓取过程出错: {e}")
            return []
    
    def _extract_article_info(self, article_element) -> Optional[Dict]:
        """提取单篇文章的信息"""
        try:
            # 标题和链接
            title_elem = article_element.find_element(By.CSS_SELECTOR, "h3.mb-1 a")
            title = title_elem.text.strip()
            article_url = title_elem.get_attribute("href")
            if not article_url.startswith("http"):
                article_url = self.base_url + article_url
            
            # 作者
            authors = []
            try:
                author_elems = article_element.find_elements(By.CSS_SELECTOR, "span.text-authors")
                authors = [elem.text.strip() for elem in author_elems if elem.text.strip()]
            except:
                pass
            
            # 期刊信息
            journal_info = ""
            try:
                journal_elem = article_element.find_element(By.CSS_SELECTOR, "div.text-meta")
                journal_info = journal_elem.text.strip()
            except:
                pass
            
            # DOI
            doi = ""
            try:
                doi_elem = article_element.find_element(By.CSS_SELECTOR, "a[href*='doi.org']")
                doi = doi_elem.get_attribute("href").split("doi.org/")[-1]
            except:
                pass
            
            return {
                "title": title,
                "url": article_url,
                "authors": authors,
                "journal": "Science",
                "journal_info": journal_info,
                "doi": doi,
                "abstract": "",  # 摘要需要进入详情页获取
                "pdf_url": None
            }
            
        except Exception as e:
            self.logger.warning(f"提取文章信息失败: {e}")
            return None
    
    def _go_to_next_page(self) -> bool:
        """尝试进入下一页"""
        try:
            # Science网站的下一页按钮
            next_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                "a.pagination__btn--next"
            )
            
            if next_button and next_button.is_enabled():
                next_button.click()
                return True
            
            return False
            
        except Exception:
            return False
    
    def get_article_details(self, article_info: Dict) -> Dict:
        """获取文章详细信息（包括摘要和PDF链接）"""
        try:
            self.logger.info(f"获取文章详情: {article_info['title']}")
            self.driver.get(article_info['url'])
            self.random_delay(2.0, 3.0)
            
            # 获取摘要
            try:
                abstract_elem = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "div.article-section__content p, section[id*='abstract'] p"
                )
                article_info['abstract'] = abstract_elem.text.strip()
            except:
                self.logger.warning("未找到摘要")
            
            # 获取PDF链接
            try:
                pdf_link_elem = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "a[href*='.pdf'], a.article-tools__item--pdf"
                )
                pdf_url = pdf_link_elem.get_attribute("href")
                if not pdf_url.startswith("http"):
                    pdf_url = self.base_url + pdf_url
                article_info['pdf_url'] = pdf_url
            except:
                self.logger.warning("未找到PDF链接")
            
            return article_info
            
        except Exception as e:
            self.logger.error(f"获取文章详情失败: {e}")
            return article_info
    
    def download_pdf(self, article_info: Dict) -> bool:
        """下载PDF文件"""
        if not article_info.get('pdf_url'):
            self.logger.warning(f"文章没有PDF链接: {article_info['title']}")
            return False
        
        try:
            # 生成文件名（使用标题的前50个字符）
            safe_title = "".join(c for c in article_info['title'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.pdf"
            filepath = self.download_dir / filename
            
            # 如果文件已存在，跳过
            if filepath.exists():
                self.logger.info(f"PDF已存在: {filename}")
                article_info['download_path'] = str(filepath)
                return True
            
            # 下载PDF
            self.logger.info(f"开始下载PDF: {filename}")
            self.driver.get(article_info['pdf_url'])
            self.random_delay(3.0, 5.0)
            
            # 等待下载完成（简单的方式）
            time.sleep(5)
            
            # 检查是否下载成功
            if filepath.exists():
                self.logger.info(f"PDF下载成功: {filename}")
                article_info['download_path'] = str(filepath)
                return True
            else:
                self.logger.warning(f"PDF下载失败: {filename}")
                return False
                
        except Exception as e:
            self.logger.error(f"下载PDF时出错: {e}")
            return False