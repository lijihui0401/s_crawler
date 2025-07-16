import time
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from .config import ScienceConfig
from .database_manager import DatabaseManager

class LinkCollector:
    """链接收集器，负责从Science搜索页收集详情页链接"""
    
    def __init__(self, driver):
        self.driver = driver
        self.config = ScienceConfig()
        self.performance_stats = {}  # 性能统计
    
    def collect_all_links(self):
        """收集所有详情页链接，动态查重，直到达到MAX_COUNT或无更多新文章"""
        print("开始收集详情页链接...")
        start_time = time.time()
        links = []
        page_num = 1
        db_manager = DatabaseManager()
        
        while True:
            page_start_time = time.time()
            print(f"\n正在处理第{page_num}页...")
            
            # 只在第一页检查页面元素，后续页面跳过检查以提高速度
            if page_num == 1:
                element_check_start = time.time()
                try:
                    # 检测搜索页目标元素（文章卡片）
                    self.driver.find_element(By.CSS_SELECTOR, ".card.pb-3.mb-4.border-bottom")
                    print("搜索页目标元素已加载")
                except Exception as e:
                    print(f"搜索页目标元素未找到: {e}")
                    raise
                element_check_time = time.time() - element_check_start
                print(f"[性能] 页面元素检测耗时: {element_check_time:.3f}秒")
            
            # 收集当前页面的链接
            collection_start = time.time()
            page_links = self._collect_page_links()
            collection_time = time.time() - collection_start
            
            # === 新增：动态查重 ===
            for article in page_links:
                doi = article.get('doi')
                if doi and db_manager.is_doi_exists(doi):
                    print(f"已存在（DOI查重）: {article['title']}")
                    continue
                links.append(article)
                if len(links) >= self.config.MAX_COUNT:
                    break
            
            page_total_time = time.time() - page_start_time
            print(f"第{page_num}页收集到{len(page_links)}条链接，总计{len(links)}条（不重复）")
            print(f"[性能] 第{page_num}页总耗时: {page_total_time:.3f}秒")
            print(f"[性能] 链接收集耗时: {collection_time:.3f}秒")
            print(f"[性能] 平均每个链接耗时: {collection_time/len(page_links):.3f}秒" if page_links else "无链接")
            
            # 检查是否达到最大数量
            if len(links) >= self.config.MAX_COUNT:
                links = links[:self.config.MAX_COUNT]
                break
            
            # 尝试翻页
            if not self._go_to_next_page():
                print("没有下一页，结束收集")
                break
            
            page_num += 1
            # 减少翻页后的等待时间
            time.sleep(0.5)  # 从SLEEP_TIME减少到0.5秒
        
        total_time = time.time() - start_time
        print(f"\n" + "=" * 60)
        print(f"收集完成！共收集到{len(links)}条详情页链接（不重复）")
        print(f"[性能] 总耗时: {total_time:.3f}秒")
        print(f"[性能] 平均每页耗时: {total_time/page_num:.3f}秒")
        print(f"[性能] 平均每个链接耗时: {total_time/len(links):.3f}秒" if links else "无链接")
        print("=" * 60 + "\n")
        
        return links
    
    def _collect_page_links(self):
        """收集当前页面的详情页链接 - 带详细性能调试"""
        links = []
        
        try:
            print("[性能] 开始收集当前页面链接...")
            
            # 1. 获取所有卡片 - 这是第一个可能的瓶颈
            cards_start = time.time()
            cards = self.driver.find_elements(By.CSS_SELECTOR, self.config.SELECTORS['search_cards'])
            cards_time = time.time() - cards_start
            print(f"[性能] 获取{len(cards)}个文章卡片耗时: {cards_time:.3f}秒")
            
            if not cards:
                print("[性能] 警告：未找到任何文章卡片，可能是选择器问题")
                return links
            
            # 2. 处理每个卡片
            processing_start = time.time()
            for i, card in enumerate(cards):
                card_start = time.time()
                try:
                    # 在单个card元素内提取所有信息
                    article_info = self._extract_card_info(card)
                    if article_info:
                        links.append(article_info)
                    
                    card_time = time.time() - card_start
                    
                    # 每处理5个卡片显示一次进度和性能
                    if (i + 1) % 5 == 0:
                        avg_card_time = (time.time() - processing_start) / (i + 1)
                        print(f"[性能] 已处理 {i + 1}/{len(cards)} 个卡片")
                        print(f"[性能] 当前卡片耗时: {card_time:.3f}秒")
                        print(f"[性能] 平均每个卡片耗时: {avg_card_time:.3f}秒")
                    
                except Exception as e:
                    card_time = time.time() - card_start
                    print(f"[性能] 处理第{i+1}个卡片时异常，耗时: {card_time:.3f}秒，错误: {e}")
                    continue
            
            total_processing_time = time.time() - processing_start
            print(f"[性能] 当前页面处理完成，收集到{len(links)}条链接")
            print(f"[性能] 卡片处理总耗时: {total_processing_time:.3f}秒")
            print(f"[性能] 平均每个卡片处理耗时: {total_processing_time/len(cards):.3f}秒" if cards else "无卡片")
            
            return links
                    
        except Exception as e:
            print(f"[性能] 收集页面链接时发生异常：{e}")
            return []

    def _extract_card_info(self, card):
        """从单个卡片提取所有信息 - 针对Science搜索页结构优化作者选择器"""
        extract_start = time.time()
        
        try:
            # 1. 标题和链接提取
            title_start = time.time()
            title_selectors = [
                ".card-header h2.article-title > a",  # 主要选择器
                "h2.article-title > a",
                ".card-header a",
                "a[data-test='article-title']"
            ]
            
            title_elem = None
            title_selector_used = None
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text.strip():
                        title_selector_used = selector
                        break
                except:
                    continue
            
            title_time = time.time() - title_start
            
            if not title_elem:
                print(f"[性能] 标题提取失败，耗时: {title_time:.3f}秒")
                return None
            
            title = title_elem.text.strip()
            detail_href = title_elem.get_attribute("href")
            
            if not detail_href:
                print(f"[性能] 标题链接为空，耗时: {title_time:.3f}秒")
                return None
            
            # 确保URL是完整的
            detail_url = detail_href if detail_href.startswith("http") else "https://www.science.org" + detail_href
            
            # 基础信息
            article_info = {
                "title": title,
                "url": detail_url,
                "doi": self._extract_doi_from_url(detail_url),
                "journal": "Science"  # 默认值
            }
            
            # 2. 期刊信息提取
            journal_start = time.time()
            journal_selectors = [
                "span.card-meta__item.bullet-left",
                ".card-meta__item",
                ".journal-info",
                "span[data-test='journal']"
            ]
            
            journal_found = False
            for selector in journal_selectors:
                try:
                    journal_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if journal_elem and journal_elem.text.strip():
                        article_info["journal"] = journal_elem.text.strip()
                        journal_found = True
                        break
                except:
                    continue
            
            journal_time = time.time() - journal_start
            
            # 3. 发表日期提取
            date_start = time.time()
            date_selectors = [
                "time",
                ".publication-date",
                ".date",
                "span[data-test='date']"
            ]
            
            date_found = False
            for selector in date_selectors:
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if date_elem and date_elem.text.strip():
                        date_text = date_elem.text.strip()
                        article_info["publication_date"] = self._parse_publication_date(date_text)
                        date_found = True
                        break
                except:
                    continue
            
            date_time = time.time() - date_start
            
            # 4. 作者信息提取（只用.hlFld-ContribAuthor）
            author_start = time.time()
            authors = []
            author_selector_used = ".hlFld-ContribAuthor"
            try:
                author_elems = card.find_elements(By.CSS_SELECTOR, ".hlFld-ContribAuthor")
                if author_elems:
                    authors = [elem.text.strip() for elem in author_elems if elem.text.strip()]
            except Exception as e:
                print(f"[性能] 作者提取异常: {e}")
            author_time = time.time() - author_start
            if authors:
                article_info["authors"] = authors
            
            # 性能统计
            total_extract_time = time.time() - extract_start
            if total_extract_time > 0.1:
                print(f"[性能] 卡片信息提取耗时: {total_extract_time:.3f}秒")
                print(f"[性能]   - 标题提取: {title_time:.3f}秒 (选择器: {title_selector_used})")
                print(f"[性能]   - 期刊提取: {journal_time:.3f}秒 (成功: {journal_found})")
                print(f"[性能]   - 日期提取: {date_time:.3f}秒 (成功: {date_found})")
                print(f"[性能]   - 作者提取: {author_time:.3f}秒 (选择器: {author_selector_used}, 作者数: {len(authors)})")
            
            return article_info
        except Exception as e:
            extract_time = time.time() - extract_start
            print(f"[性能] 提取卡片信息失败，耗时: {extract_time:.3f}秒，错误: {e}")
            return None
    
    def _go_to_next_page(self):
        """跳转到下一页"""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, self.config.SELECTORS['next_page'])
            next_btn.click()
            print("翻到下一页...")
            return True
        except NoSuchElementException:
            return False
        except Exception as e:
            print(f"翻页异常：{e}")
            return False
    
    def _extract_doi_from_url(self, url):
        """从Science URL中提取DOI"""
        # 匹配 /doi/10.1126/science.xxx 格式
        pattern = r'/doi/(10\.\d+/[^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    
    def _parse_publication_date(self, date_text):
        """解析发表日期文本为datetime对象"""
        try:
            # 处理 "10 Aug 2023" 格式
            return datetime.strptime(date_text.strip(), "%d %b %Y")
        except:
            try:
                # 处理其他可能的格式
                return datetime.strptime(date_text.strip(), "%Y-%m-%d")
            except:
                return None 