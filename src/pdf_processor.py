import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from .config import ScienceConfig

class PDFProcessor:
    """PDF处理器，负责处理单个详情页并获取PDF下载链接"""
    
    def __init__(self, driver):
        self.driver = driver
        from .config import ScienceConfig
        self.config = ScienceConfig()
    
    def process_article(self, article_info):
        """处理单个文章，获取PDF下载链接并立即下载。只在详情页查找摘要、关键词、PDF链接，其他字段直接用article_info里的。"""
        title = article_info.get("title", "Unknown")
        print(f"[{title}] 开始处理详情页...")
        
        try:
            # 1. 加载详情页
            self.driver.get(article_info.get("url"))
            time.sleep(self.config.SLEEP_TIME)
            
            # 等待页面加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(("css selector", "body"))
                )
            except:
                print(f"[{title}] 页面加载超时，继续处理...")
            
            # 检查详情页目标元素（标题或PDF按钮）
            try:
                self.driver.find_element(By.CSS_SELECTOR, "h1.article-title, i.icon-pdf")
                print(f"[{title}] 详情页目标元素已加载")
            except Exception as e:
                print(f"[{title}] 详情页目标元素未找到: {e}")
                raise
            
            # 2. 只查找摘要、关键词等详情页独有字段
            article_details = self._extract_article_details()
            
            # 3. 查找PDF按钮
            pdf_page_url = self._find_pdf_page_url()
            if not pdf_page_url:
                print(f"[{title}] 未找到PDF按钮，跳过")
                return None
            
            # 4. 跳转到PDF页面
            self.driver.get(pdf_page_url)
            time.sleep(self.config.SLEEP_TIME)
            
            # 检查PDF页面目标元素（下载按钮）
            try:
                self.driver.find_element(By.CSS_SELECTOR, "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a > span, span.icon.material-icons")
                print(f"[{title}] PDF页面下载按钮已加载")
            except Exception as e:
                print(f"[{title}] PDF页面下载按钮未找到: {e}")
                raise
            
            # 5. 获取PDF下载链接
            download_link = self._get_pdf_download_link()
            if not download_link:
                print(f"[{title}] 未找到PDF下载链接，跳过")
                return None
            print(f"[{title}] 获取到PDF下载链接，开始下载...")
            
            # 6. 立即下载PDF
            success = self._download_pdf_immediately(title, download_link)
            
            # 合并所有信息
            result = {
                "title": article_info.get("title"),
                "url": article_info.get("url"),
                "download_link": download_link,
                "downloaded": success,
                "doi": article_info.get("doi"),
                "journal": article_info.get("journal"),
                "publication_date": article_info.get("publication_date"),
                "authors": article_info.get("authors", []),
            }
            # 添加从详情页获取的信息
            if article_details:
                result.update(article_details)
            return result
        except Exception as e:
            print(f"[{title}] 处理异常，跳过：{e}")
            return None
    
    def _find_pdf_page_url(self):
        """在详情页查找PDF页面URL - 细化调试每个选择器耗时"""
        try:
            print(f"[DEBUG] 开始查找PDF按钮，当前URL: {self.driver.current_url}")
            pdf_selectors = [
                "i.icon-pdf",
                "#main > div.article-container > article > header > div > div.info-panel > div.info-panel__right-content > div.info-panel__formats.info-panel__item > a",
                "a[href*='pdf']",
                "a[data-test='pdf-link']",
                "a[aria-label*='PDF']",
                ".pdf-link",
                "a[title*='PDF']"
            ]
            for selector in pdf_selectors:
                t_sel = time.time()
                try:
                    if selector == "i.icon-pdf":
                        pdf_icons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        print(f"[调试] PDF按钮选择器 {selector} 查找{len(pdf_icons)}个icon, 耗时: {time.time() - t_sel:.3f}秒")
                        for i, icon in enumerate(pdf_icons):
                            try:
                                parent_a = icon.find_element(By.XPATH, "./ancestor::a")
                                pdf_page_href = parent_a.get_attribute("href")
                                if pdf_page_href:
                                    pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
                                    print(f"[调试] PDF按钮选择器 {selector} 命中, 耗时: {time.time() - t_sel:.3f}秒")
                                    return pdf_page_url
                            except NoSuchElementException:
                                continue
                    else:
                        pdf_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        pdf_page_href = pdf_elem.get_attribute("href")
                        if pdf_page_href:
                            pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
                            print(f"[调试] PDF按钮选择器 {selector} 命中, 耗时: {time.time() - t_sel:.3f}秒")
                            return pdf_page_url
                    print(f"[调试] PDF按钮选择器 {selector} 未命中, 耗时: {time.time() - t_sel:.3f}秒")
                except NoSuchElementException:
                    print(f"[调试] PDF按钮选择器 {selector} 未命中, 耗时: {time.time() - t_sel:.3f}秒")
                    continue
                except Exception as e:
                    print(f"[调试] PDF按钮选择器 {selector} 异常: {e}, 耗时: {time.time() - t_sel:.3f}秒")
                    continue
            # 兜底方案
            try:
                t_sel = time.time()
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                pdf_links = []
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "pdf" in href.lower():
                        pdf_links.append(href)
                if pdf_links:
                    print(f"[调试] 兜底PDF链接查找命中, 耗时: {time.time() - t_sel:.3f}秒")
                    return pdf_links[0]
                else:
                    print(f"[调试] 兜底PDF链接查找未命中, 耗时: {time.time() - t_sel:.3f}秒")
            except Exception as e:
                print(f"[调试] 兜底PDF链接查找异常: {e}")
            print("[DEBUG] 所有方法都未找到PDF按钮")
            return None
        except Exception as e:
            print(f"[DEBUG] 查找PDF按钮异常：{e}")
            return None
    
    def _get_pdf_download_link(self):
        """在PDF页面获取下载链接 - 通过点击下载按钮"""
        try:
            # 等待页面完全加载
            import time
            time.sleep(2)
            
            # 滚动到页面顶部，确保没有遮挡
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 查找下载按钮
            download_selectors = [
                "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a > span",
                "span.icon.material-icons"
            ]
            
            download_elem = None
            for selector in download_selectors:
                try:
                    download_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if download_elem:
                        print(f"[调试] 找到下载按钮: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not download_elem:
                print("[调试] 未找到下载按钮")
                return None
            
            # 向上找到a标签并点击
            try:
                parent_a = download_elem.find_element(By.XPATH, "./ancestor::a")
                download_link = parent_a.get_attribute("href")
                
                if download_link:
                    print(f"[调试] 获取到下载链接: {download_link}")
                    
                    # 尝试多种点击方式
                    try:
                        # 方式1：直接点击
                        print("[调试] 尝试直接点击...")
                        parent_a.click()
                    except Exception as e1:
                        print(f"[调试] 直接点击失败: {e1}")
                        try:
                            # 方式2：JavaScript点击
                            print("[调试] 尝试JavaScript点击...")
                            self.driver.execute_script("arguments[0].click();", parent_a)
                        except Exception as e2:
                            print(f"[调试] JavaScript点击失败: {e2}")
                            try:
                                # 方式3：滚动到元素位置再点击
                                print("[调试] 尝试滚动到元素位置...")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", parent_a)
                                time.sleep(1)
                                parent_a.click()
                            except Exception as e3:
                                print(f"[调试] 滚动点击失败: {e3}")
                                # 方式4：直接访问下载链接
                                print("[调试] 直接访问下载链接...")
                                self.driver.get(download_link)
                    
                    # 等待下载开始
                    time.sleep(3)
                    
                    return download_link
                else:
                    print("[调试] 下载链接为空")
                    return None
                    
            except Exception as e:
                print(f"[调试] 点击下载按钮失败: {e}")
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
    
    def _extract_article_details(self):
        """提取文章详细信息（摘要、关键词等）- 细化调试每个选择器耗时"""
        details = {}
        try:
            # 提取摘要 - 多选择器详细调试
            abstract_selectors = [
                "div[role='paragraph']",  # Science特有的选择器
                ".abstract p",
                ".summary p", 
                "[data-test='abstract'] p",
                "div.abstract",
                "div.summary",
                ".article__body p",  # 文章正文段落
                "section[data-test='abstract'] p",
                "p[data-test='article-summary']"
            ]
            for selector in abstract_selectors:
                t_sel = time.time()
                try:
                    abstract_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if abstract_elem and abstract_elem.text.strip():
                        details["abstract"] = abstract_elem.text.strip()
                        print(f"[调试] 摘要选择器 {selector} 命中, 耗时: {time.time() - t_sel:.3f}秒")
                        break
                except NoSuchElementException:
                    print(f"[调试] 摘要选择器 {selector} 未命中, 耗时: {time.time() - t_sel:.3f}秒")
                    continue
                except Exception as e:
                    print(f"[调试] 摘要选择器 {selector} 异常: {e}, 耗时: {time.time() - t_sel:.3f}秒")
                    continue
        except Exception as e:
            print(f"[DEBUG] 提取文章详情异常: {e}")
        return details 