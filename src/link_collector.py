import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .config import ScienceConfig
from .utils import handle_captcha

class LinkCollector:
    """链接收集器，负责从搜索页面收集所有详情页链接"""
    
    def __init__(self, driver):
        self.driver = driver
        self.config = ScienceConfig()
    
    def collect_all_links(self):
        """收集所有详情页链接"""
        print("开始收集详情页链接...")
        
        links = []
        page_num = 1
        
        while len(links) < self.config.MAX_COUNT:
            print(f"正在处理第{page_num}页...")
            
            # 检查人机验证
            if handle_captcha(self.driver):
                print("人机验证处理完成，继续收集...")
            
            # 收集当前页面的链接
            page_links = self._collect_page_links()
            links.extend(page_links)
            
            print(f"第{page_num}页收集到{len(page_links)}条链接，总计{len(links)}条")
            
            # 检查是否达到最大数量
            if len(links) >= self.config.MAX_COUNT:
                links = links[:self.config.MAX_COUNT]
                break
            
            # 尝试翻页
            if not self._go_to_next_page():
                print("没有下一页，结束收集")
                break
            
            page_num += 1
            time.sleep(self.config.SLEEP_TIME)
        
        print(f"共收集到{len(links)}条详情页链接\n")
        return links
    
    def _collect_page_links(self):
        """收集当前页面的详情页链接"""
        links = []
        
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, self.config.SELECTORS['search_cards'])
            
            for card in cards:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, self.config.SELECTORS['title_link'])
                    title = title_elem.text.strip()
                    detail_href = title_elem.get_attribute("href")
                    
                    if not detail_href:
                        continue
                    
                    # 确保URL是完整的
                    detail_url = detail_href if detail_href.startswith("http") else "https://www.science.org" + detail_href
                    
                    links.append({
                        "title": title,
                        "url": detail_url
                    })
                    
                except Exception as e:
                    print(f"收集详情页链接异常，跳过：{e}")
                    continue
                    
        except Exception as e:
            print(f"收集页面链接时发生异常：{e}")
        
        return links
    
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