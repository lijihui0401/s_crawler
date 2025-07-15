"""
Nature期刊爬虫
基于Selenium实现，模拟真实用户行为
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


class NatureCrawler:
    """Nature期刊爬虫类"""
    
    def __init__(self, headless: bool = False, download_dir: str = "downloads", use_existing_browser: bool = False, third_party_domain: str = None):
        """
        初始化爬虫
        
        Args:
            headless: 是否无头模式运行
            download_dir: 下载目录
            use_existing_browser: 是否使用已存在的浏览器
            third_party_domain: 第三方网站域名，如 nature.f.33tsg.xyz
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
        
        # 基础URL - 支持第三方网站
        if third_party_domain:
            self.base_url = f"https://{third_party_domain}"
            self.search_url = f"https://{third_party_domain}/search"
            self.logger.info(f"使用第三方网站: {third_party_domain}")
        else:
            self.base_url = "https://www.nature.com"
            self.search_url = "https://www.nature.com/search"
            self.logger.info("使用官方Nature网站")
        
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/nature_crawler.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            if self.use_existing_browser:
                # 只尝试连接到已存在的浏览器，失败直接抛异常
                self.logger.info("尝试连接到已存在的Chrome浏览器...")
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.logger.info("成功连接到已存在的Chrome浏览器")
                    return
                except Exception as e:
                    self.logger.error(f"连接已存在浏览器失败: {e}")
                    raise RuntimeError("未能连接到已存在的Chrome调试浏览器，请确认已正确启动并未关闭。")
            # 只有 use_existing_browser=False 时才自动新开浏览器
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            ua = UserAgent()
            chrome_options.add_argument(f"--user-agent={ua.random}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            prefs = {
                "download.default_directory": str(self.download_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                self.logger.warning(f"自动下载ChromeDriver失败: {e}")
                self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Chrome浏览器驱动初始化成功")
        except Exception as e:
            self.logger.error(f"浏览器驱动初始化失败: {e}")
            raise
    
    def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """随机延迟，模拟人类行为"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def search_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        搜索文章，自动翻页直到抓够max_results或无更多结果
        """
        try:
            self.logger.info(f"开始搜索: {query}")
            self.logger.info(f"目标获取文章数量: {max_results}")
            articles = []
            page = 1
            while len(articles) < max_results:
                # 构造当前页URL
                search_url = f"{self.search_url}?q={query}&page={page}"
                self.driver.get(search_url)
                self.random_delay(1.0, 3.0)  # 每翻一页加随机延迟
                
                # 等待页面加载
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
                
                article_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
                if not article_elements:
                    self.logger.info(f"第{page}页未找到文章，提前结束")
                    break
                
                for i, article in enumerate(article_elements):
                    if len(articles) >= max_results:
                        break
                    try:
                        article_info = self._extract_article_info(article)
                        if article_info:
                            articles.append(article_info)
                            self.logger.info(f"提取文章 {len(articles)}: {article_info.get('title', 'Unknown')}")
                        self.random_delay(0.5, 2.0)  # 每篇文章之间加随机延迟
                    except Exception as e:
                        self.logger.warning(f"提取文章信息失败: {e}")
                        continue
                
                # 检查是否有下一页
                try:
                    # 用XPATH查找class包含c-pagination__link且文本为Next page的a标签
                    next_btn = self.driver.find_element(By.XPATH, "//a[contains(@class, 'c-pagination__link') and contains(., 'Next page')]")
                    if next_btn and next_btn.is_enabled():
                        page += 1
                        self.logger.info(f"进入第{page}页...")
                        # self.random_delay(1, 2)  # 已在开头加过延迟
                    else:
                        self.logger.info("未找到下一页按钮，搜索结束")
                        break
                except Exception:
                    self.logger.info("未找到下一页按钮，搜索结束")
                    break
            
            # 显示获取结果
            self.logger.info(f"搜索完成，共找到 {len(articles)} 篇文章")
            if articles:
                self.logger.info("=== 获取到的文章URL列表 ===")
                for i, article in enumerate(articles, 1):
                    self.logger.info(f"{i:3d}. {article.get('title', 'Unknown')}")
                    self.logger.info(f"     URL: {article.get('url', 'N/A')}")
                self.logger.info("=== URL列表结束 ===")
                self.logger.info(f"✅ 成功获取 {len(articles)} 篇文章的URL，准备开始下载PDF...")
            else:
                self.logger.warning("❌ 未获取到任何文章URL")
            
            return articles
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []
    
    def is_title_exists(self, title, db_config):
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM nature WHERE title=%s", (title,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    
    def crawl_from_url(self, start_url: str, max_results: int = 10, db_config=None) -> List[Dict]:
        """
        从指定结果页URL开始抓取，自动翻页，直到抓够max_results或无更多结果
        """
        try:
            self.logger.info(f"从指定URL开始抓取: {start_url}")
            self.driver.get(start_url)
            self.random_delay(1.0, 2.0)
            # 检测当前页码
            try:
                page_elem = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "#content > div.u-container.u-mb-48 > nav > ul > li:nth-child(2) > span"
                )
                current_page = page_elem.text.strip()
                self.logger.info(f"当前搜索结果页码: {current_page}")
                print(f"当前搜索结果页码: {current_page}")
            except Exception as e:
                self.logger.warning(f"未检测到当前页码: {e}")
            articles = []
            current_url = start_url
            page = 1
            while len(articles) < max_results:
                self.driver.get(current_url)
                self.random_delay(1.0, 3.0)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
                article_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
                if not article_elements:
                    self.logger.info(f"第{page}页未找到文章，提前结束")
                    break
                for i, article in enumerate(article_elements):
                    if len(articles) >= max_results:
                        break
                    try:
                        article_info = self._extract_article_info(article)
                        if article_info:
                            # title查重
                            if db_config and self.is_title_exists(article_info['title'], db_config):
                                self.logger.info(f"已存在，跳过: {article_info['title']}")
                                continue
                            articles.append(article_info)
                            self.logger.info(f"提取文章 {len(articles)}: {article_info.get('title', 'Unknown')}")
                        self.random_delay(0.5, 2.0)
                    except Exception as e:
                        self.logger.warning(f"提取文章信息失败: {e}")
                        continue
                # 查找下一页按钮
                try:
                    next_btn = self.driver.find_element(By.XPATH, "//a[contains(@class, 'c-pagination__link') and contains(., 'Next page')]")
                    if next_btn and next_btn.is_enabled():
                        next_url = next_btn.get_attribute("href")
                        if not next_url:
                            self.logger.info("下一页按钮无href，结束")
                            break
                        current_url = next_url
                        page += 1
                        self.logger.info(f"进入第{page}页...")
                    else:
                        self.logger.info("未找到下一页按钮，抓取结束")
                        break
                except Exception:
                    self.logger.info("未找到下一页按钮，抓取结束")
                    break
            self.logger.info(f"抓取完成，共找到 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            self.logger.error(f"抓取失败: {e}")
            return []
    
    def _extract_article_info(self, article_element) -> Optional[Dict]:
        """提取文章信息"""
        try:
            # 标题 - 根据调试结果优化
            title_element = article_element.find_element(By.CSS_SELECTOR, "h3 a, h2 a, a[data-test='article-title'], h1[data-test='article-title']")
            title = title_element.text.strip()
            article_url = title_element.get_attribute("href")
            # 作者 - 根据调试结果优化
            authors = []
            try:
                author_elements = article_element.find_elements(
                    By.CSS_SELECTOR, 
                    "[data-test='author-name'], .author-name, .author, a[data-test='author-link']"
                )
                authors = [author.text.strip() for author in author_elements if author.text.strip()]
            except:
                pass
            # 摘要
            abstract = ""
            try:
                # 优先用精准选择器
                abstract_elem = self.driver.find_element(By.CSS_SELECTOR, "#Abs1-content > p")
                abstract = abstract_elem.text.strip()
            except Exception:
                try:
                    abstract_elem = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        "[data-test='abstract'], .abstract, .summary, p[data-test='article-summary']"
                    )
                    abstract = abstract_elem.text.strip()
                except Exception:
                    try:
                        p_elems = self.driver.find_elements(By.CSS_SELECTOR, "article p, section p, div p, p")
                        for p in p_elems:
                            txt = p.text.strip()
                            if len(txt) > 50:
                                abstract = txt
                                break
                    except Exception:
                        pass
            # 期刊信息
            journal = ""
            try:
                journal_elem = article_element.find_element(
                    By.CSS_SELECTOR, ".c-meta__item.c-meta__item--block-at-lg.u-text-bold"
                )
                journal = journal_elem.text.strip()
            except Exception:
                pass
            return {
                "title": title,
                "url": article_url,
                "authors": authors,
                "abstract": abstract,
                "journal": journal
            }
        except Exception as e:
            self.logger.warning(f"提取文章信息失败: {e}")
            return None
    
    def download_pdf(self, article_url: str, filename: str = None) -> dict:
        """
        下载PDF并提取详情页全部字段，返回详情页元数据dict。
        """
        result = {}
        try:
            self.logger.info(f"开始下载PDF: {article_url}")
            self.random_delay(1.0, 2.0)
            self.driver.get(article_url)
            self.random_delay(1.0, 2.0)
            self._handle_cookie_banner()
            # 提取详情页字段
            try:
                # 移除DOI
                # 移除期刊
                # 摘要
                abstract = ""
                try:
                    # 优先用精准选择器
                    abstract_elem = self.driver.find_element(By.CSS_SELECTOR, "#Abs1-content > p")
                    abstract = abstract_elem.text.strip()
                except Exception:
                    try:
                        abstract_elem = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            "[data-test='abstract'], .abstract, .summary, p[data-test='article-summary']"
                        )
                        abstract = abstract_elem.text.strip()
                    except Exception:
                        try:
                            p_elems = self.driver.find_elements(By.CSS_SELECTOR, "article p, section p, div p, p")
                            for p in p_elems:
                                txt = p.text.strip()
                                if len(txt) > 50:
                                    abstract = txt
                                    break
                        except Exception:
                            pass
                result['abstract'] = abstract
                # 作者
                authors = []
                try:
                    author_elems = self.driver.find_elements(By.CSS_SELECTOR, "[data-test='author-name'], .author-name, .author, a[data-test='author-link']")
                    authors = [a.text.strip() for a in author_elems if a.text.strip()]
                except Exception:
                    pass
                result['authors'] = authors
                # 关键词
                keywords = []
                try:
                    keyword_elems = self.driver.find_elements(By.CSS_SELECTOR, "[data-test='keyword'], .c-article-subject-list__subject")
                    keywords = [k.text.strip() for k in keyword_elems if k.text.strip()]
                except Exception:
                    pass
                result['keywords'] = keywords
                # 发表日期
                publication_date = None
                try:
                    date_elem = self.driver.find_element(By.CSS_SELECTOR, "time, [itemprop='datePublished']")
                    publication_date = date_elem.get_attribute('datetime') or date_elem.text.strip()
                except Exception:
                    pass
                result['publication_date'] = publication_date
                # PDF下载链接
                pdf_url = ""
                try:
                    pdf_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-test='download-pdf'][data-article-pdf='true']")
                    for link in pdf_links:
                        if link.text.strip().lower() == "download pdf":
                            pdf_url = link.get_attribute("href")
                            break
                    if not pdf_url and pdf_links:
                        pdf_url = pdf_links[0].get_attribute("href")
                except Exception:
                    pass
                result['pdf_url'] = pdf_url
            except Exception as e:
                self.logger.warning(f"详情页字段提取异常: {e}")
            # 下载PDF
            import requests
            import os
            local_filename = filename or (result.get('pdf_url') or article_url).split("/")[-1]
            local_path = os.path.join(str(self.download_dir), local_filename)
            try:
                cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
                headers = {
                    "User-Agent": self.driver.execute_script("return navigator.userAgent;")
                }
                r = requests.get(result.get('pdf_url') or article_url, headers=headers, cookies=cookies, timeout=30)
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(r.content)
                self.logger.info(f"PDF已保存到: {local_path}")
                result['download_path'] = local_path
                result['success'] = True
            except Exception as e:
                self.logger.error(f"直接下载PDF失败: {e}")
                screenshot_path = f"logs/pdf_download_direct_error_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                self.logger.info(f"直接下载异常已截图: {screenshot_path}")
                result['download_path'] = None
                result['success'] = False
            return result
        except Exception as e:
            self.logger.error(f"下载PDF失败: {e}")
            screenshot_path = f"logs/pdf_download_error_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"异常已截图: {screenshot_path}")
            result['download_path'] = None
            result['success'] = False
            return result
    
    def _check_auth_required(self) -> bool:
        """检查是否需要用户认证"""
        try:
            # 查找认证相关的元素
            auth_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".paywall, .subscription-required, [data-test='paywall'], .access-denied"
            )
            
            if auth_elements:
                self.logger.info("检测到付费墙或认证要求")
                return True
            
            # 检查页面标题是否包含认证相关文本
            page_title = self.driver.title.lower()
            if any(keyword in page_title for keyword in ['access denied', 'subscription required', 'paywall']):
                return True
                
            return False
            
        except Exception as e:
            self.logger.warning(f"检查认证状态失败: {e}")
            return False
    
    def _handle_cookie_banner(self):
        """处理Cookie横幅"""
        try:
            # 查找Cookie同意按钮
            cookie_buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[data-test='cookie-banner-accept'], .cc-banner__button, button[aria-label*='Accept'], button[aria-label*='同意']"
            )
            
            if cookie_buttons:
                cookie_buttons[0].click()
                self.logger.info("已关闭Cookie横幅")
                self.random_delay(1, 2)
                
        except Exception as e:
            self.logger.warning(f"处理Cookie横幅失败: {e}")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.logger.info("浏览器已关闭")
    
    def close_manual(self):
        """手动关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.logger.info("浏览器已手动关闭")
    
    def keep_open(self):
        """保持浏览器打开状态"""
        self.logger.info("浏览器将保持打开状态，请手动关闭")
        # 不关闭浏览器，让用户手动关闭
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 不自动关闭浏览器
        pass 