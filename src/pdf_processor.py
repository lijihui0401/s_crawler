import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .config import ScienceConfig
from .utils import handle_captcha

class PDFProcessor:
    """PDF处理器，负责处理单个详情页并获取PDF下载链接"""
    
    def __init__(self, driver):
        self.driver = driver
        self.config = ScienceConfig()
    
    def process_article(self, article_info):
        """处理单个文章，获取PDF下载链接并立即下载"""
        title = article_info["title"]
        detail_url = article_info["url"]
        
        print(f"处理文章: {title}")
        
        try:
            # 1. 跳转到详情页
            self.driver.get(detail_url)
            time.sleep(self.config.SLEEP_TIME)
            
            # 增加页面加载等待时间
            try:
                from selenium.webdriver.support.wait import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(("css selector", "body"))
                )
            except:
                print(f"[{title}] 页面加载超时，继续处理...")
            
            # 检查人机验证
            if handle_captcha(self.driver):
                print("人机验证处理完成，继续处理...")
            
            # 2. 查找PDF按钮
            pdf_page_url = self._find_pdf_page_url()
            if not pdf_page_url:
                print(f"[{title}] 未找到PDF按钮，跳过")
                return None
            
            # 3. 跳转到PDF页面
            self.driver.get(pdf_page_url)
            time.sleep(self.config.SLEEP_TIME)
            
            # 检查人机验证
            if handle_captcha(self.driver):
                print("人机验证处理完成，继续处理...")
            
            # 4. 获取PDF下载链接
            download_link = self._get_pdf_download_link()
            if not download_link:
                print(f"[{title}] 未找到PDF下载链接，跳过")
                return None
            
            print(f"[{title}] 获取到PDF下载链接，开始下载...")
            
            # 5. 立即下载PDF
            success = self._download_pdf_immediately(title, download_link)
            
            return {
                "title": title,
                "download_link": download_link,
                "downloaded": success
            }
            
        except Exception as e:
            print(f"[{title}] 处理异常，跳过：{e}")
            return None
    
    def _find_pdf_page_url(self):
        """在详情页查找PDF页面URL"""
        try:
            print(f"[DEBUG] 开始查找PDF按钮，当前URL: {self.driver.current_url}")
            
            # 方法1：使用你提供的PDF图标选择器（优先）
            try:
                pdf_icons = self.driver.find_elements(By.CSS_SELECTOR, "i.icon-pdf")
                print(f"[DEBUG] 找到{len(pdf_icons)}个PDF图标")
                
                for i, icon in enumerate(pdf_icons):
                    try:
                        # 找到包含PDF图标的父级a标签
                        parent_a = icon.find_element(By.XPATH, "./ancestor::a")
                        pdf_page_href = parent_a.get_attribute("href")
                        if pdf_page_href:
                            pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
                            print(f"[DEBUG] 通过PDF图标{i+1}找到按钮: {pdf_page_url}")
                            return pdf_page_url
                    except NoSuchElementException:
                        print(f"[DEBUG] PDF图标{i+1}的父级a标签未找到")
                        continue
            except Exception as e:
                print(f"[DEBUG] 通过PDF图标查找失败: {e}")
            
            # 方法2：使用配置中的CSS选择器
            try:
                pdf_button = self.driver.find_element(By.CSS_SELECTOR, self.config.SELECTORS['pdf_button'])
                pdf_page_href = pdf_button.get_attribute("href")
                if pdf_page_href:
                    pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
                    print(f"[DEBUG] 通过CSS选择器找到PDF按钮: {pdf_page_url}")
                    return pdf_page_url
            except NoSuchElementException:
                print("[DEBUG] CSS选择器未找到PDF按钮")
            
            # 方法3：使用XPath选择器
            try:
                pdf_icon = self.driver.find_element(By.XPATH, '//*[@id="main"]/div[1]/article/header/div/div[5]/div[2]/div[3]/a/i')
                parent_a = pdf_icon.find_element(By.XPATH, "./ancestor::a")
                pdf_page_href = parent_a.get_attribute("href")
                if pdf_page_href:
                    pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
                    print(f"[DEBUG] 通过XPath选择器找到PDF按钮: {pdf_page_url}")
                    return pdf_page_url
            except NoSuchElementException:
                print("[DEBUG] XPath选择器未找到PDF按钮")
            
            # 方法4：查找包含"pdf"的链接
            try:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                pdf_links = []
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "pdf" in href.lower():
                        pdf_links.append(href)
                
                if pdf_links:
                    print(f"[DEBUG] 通过href找到{len(pdf_links)}个PDF链接: {pdf_links[0]}")
                    return pdf_links[0]
                else:
                    print("[DEBUG] 未找到包含'pdf'的链接")
            except Exception as e:
                print(f"[DEBUG] 通过href查找失败: {e}")
            
            # 方法5：调试信息 - 显示页面上所有的链接
            try:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"[DEBUG] 页面上共有{len(all_links)}个链接")
                for i, link in enumerate(all_links[:10]):  # 只显示前10个
                    href = link.get_attribute("href")
                    text = link.text[:50] if link.text else "无文本"
                    print(f"[DEBUG] 链接{i+1}: {text} -> {href}")
            except Exception as e:
                print(f"[DEBUG] 获取链接调试信息失败: {e}")
            
            print("[DEBUG] 所有方法都未找到PDF按钮")
            return None
            
        except Exception as e:
            print(f"[DEBUG] 查找PDF按钮异常：{e}")
            return None
    
    def _get_pdf_download_link(self):
        """在PDF页面获取下载链接"""
        try:
            download_a_elem = self.driver.find_element(By.CSS_SELECTOR, self.config.SELECTORS['download_button'])
            download_link = download_a_elem.get_attribute("href")
            
            if download_link:
                return download_link
            else:
                return None
                
        except NoSuchElementException:
            return None
        except Exception as e:
            print(f"获取PDF下载链接异常：{e}")
            return None
    
    def _download_pdf_immediately(self, title, download_link):
        """立即下载PDF文件"""
        try:
            from .utils import sanitize_filename, download_file
            import os
            
            # 创建下载目录
            download_dir = self.config.DOWNLOAD_DIR
            os.makedirs(download_dir, exist_ok=True)
            
            # 生成文件名
            filename = sanitize_filename(title) + ".pdf"
            filepath = os.path.join(download_dir, filename)
            
            # 获取当前driver的cookies
            cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
            
            # 设置请求头
            headers = {
                'User-Agent': self.driver.execute_script("return navigator.userAgent;"),
                'Referer': self.driver.current_url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # 使用requests下载，带重试机制
            import requests
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(download_link, headers=headers, cookies=cookies, stream=True, timeout=30)
                    
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        print(f"[{title}] 下载成功: {filepath}")
                        return True
                    elif response.status_code == 403:
                        print(f"[{title}] 下载失败: HTTP 403 (可能需要订阅权限)")
                        return False
                    else:
                        print(f"[{title}] 下载失败: HTTP {response.status_code} (尝试 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # 指数退避
                        else:
                            return False
                            
                except Exception as e:
                    print(f"[{title}] 下载异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        return False
            
            return False
                
        except Exception as e:
            print(f"[{title}] 下载异常: {e}")
            return False 