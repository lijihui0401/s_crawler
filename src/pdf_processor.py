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
    
    def process_article(self, article_info, cookies_str=None, user_agent=None):
        """处理单个文章，获取PDF下载链接并立即下载。支持外部传入cookie和user-agent。"""
        title = article_info.get("title", "Unknown")
        print(f"[{title}] 开始处理详情页...")
        try:
            self.driver.get(article_info.get("url"))
            time.sleep(self.config.SLEEP_TIME)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(("css selector", "body"))
                )
            except:
                print(f"[{title}] 页面加载超时，继续处理...")
            # 只检查PDF按钮，不检查标题（标题已在搜索页获取）
            try:
                self.driver.find_element(By.CSS_SELECTOR, "i.icon-pdf")
                print(f"[{title}] PDF按钮已加载")
            except Exception as e:
                print(f"[{title}] PDF按钮未找到: {e}")
                # 不立即抛出异常，继续尝试其他方法
            article_details = self._extract_article_details()
            pdf_page_url = self._find_pdf_page_url()
            if not pdf_page_url:
                print(f"[{title}] 未找到PDF按钮，跳过")
                return None
            self.driver.get(pdf_page_url)
            time.sleep(self.config.SLEEP_TIME)
            try:
                self.driver.find_element(By.CSS_SELECTOR, "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a > span, span.icon.material-icons")
                print(f"[{title}] PDF页面下载按钮已加载")
            except Exception as e:
                print(f"[{title}] PDF页面下载按钮未找到: {e}")
                raise
            download_link = self._get_pdf_download_link()
            if not download_link:
                print(f"[{title}] 未找到PDF下载链接，跳过")
                return None
            print(f"[{title}] 获取到PDF下载链接，开始下载...")
            success = self._download_pdf_immediately(title, download_link, cookies_str, user_agent)
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
            if article_details:
                result.update(article_details)
            return result
        except Exception as e:
            print(f"[{title}] 处理异常，跳过：{e}")
            return None
    
    def _find_pdf_page_url(self):
        """在详情页查找PDF页面URL - 使用确切的选择器"""
        try:
            print(f"[DEBUG] 开始查找PDF按钮，当前URL: {self.driver.current_url}")
            
            # 使用用户提供的确切选择器
            main_selector = "#main > div.article-container > article > header > div > div.info-panel > div.info-panel__right-content > div.info-panel__formats.info-panel__item > a > i"
            t_sel = time.time()
            
            try:
                # 查找PDF图标
                pdf_icon = self.driver.find_element(By.CSS_SELECTOR, main_selector)
                print(f"[调试] PDF按钮选择器 {main_selector} 命中, 耗时: {time.time() - t_sel:.3f}秒")
                
                # 获取父级a元素
                parent_a = pdf_icon.find_element(By.XPATH, "./parent::a")
                pdf_page_href = parent_a.get_attribute("href")
                
                if pdf_page_href:
                    # 确保URL完整
                    pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
                    print(f"[调试] 获取到PDF页面URL: {pdf_page_url}")
                    return pdf_page_url
            except NoSuchElementException:
                print(f"[调试] 未找到确切的PDF按钮选择器: {main_selector}, 耗时: {time.time() - t_sel:.3f}秒")
            
            # 备用选择器方案
            pdf_selectors = [
                "i.icon-pdf",
                "#main > div.article-container > article > header > div > div.info-panel > div.info-panel__right-content > div.info-panel__formats.info-panel__item > a",
                "a[href*='pdf']",
                "a[data-test='pdf-link']",
                "a[aria-label*='PDF']",
                ".pdf-link",
                "a[title*='PDF']",
                "a.show-pdf",
                "a.pdf-button",
                "a[href*='pdf'][href*='download=true']",
                ".article-action-pdf a"
            ]
            
            for selector in pdf_selectors:
                t_sel = time.time()
                try:
                    # 特别处理icon元素
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
                except NoSuchElementException:
                    print(f"[调试] PDF按钮选择器 {selector} 未命中, 耗时: {time.time() - t_sel:.3f}秒")
                    continue
                except Exception as e:
                    print(f"[调试] PDF按钮选择器 {selector} 异常: {e}, 耗时: {time.time() - t_sel:.3f}秒")
                    continue
            
            # 兜底方案: 查找包含"pdf"的所有链接
            t_sel = time.time()
            try:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                pdf_links = []
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and ("pdf" in href.lower() or "epdf" in href.lower()):
                        pdf_links.append(href)
                if pdf_links:
                    print(f"[调试] 兜底PDF链接查找命中, 耗时: {time.time() - t_sel:.3f}秒")
                    return pdf_links[0]
                else:
                    print(f"[调试] 兜底PDF链接查找未命中, 耗时: {time.time() - t_sel:.3f}秒")
            except Exception as e:
                print(f"[调试] 兜底PDF链接查找异常: {e}, 耗时: {time.time() - t_sel:.3f}秒")
                
            print("[DEBUG] 所有方法都未找到PDF按钮")
            return None
        except Exception as e:
            print(f"[DEBUG] 查找PDF按钮异常：{e}")
            return None
    
    def _get_pdf_download_link(self):
        """在PDF页面获取下载链接 - 使用确切的选择器"""
        try:
            # 精确选择器
            download_selector = "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a"
            a_elem = self.driver.find_element(By.CSS_SELECTOR, download_selector)
            download_link = a_elem.get_attribute("href")
            if download_link:
                print(f"[调试] 精准选择器获取到下载链接: {download_link}")
                return download_link
            
            # 备用选择器
            backup_selectors = [
                'a[href*="download=true"]',
                '.download-button',
                'a[data-test="pdf-download"]',
                '.pdf-download-btn',
                'a.article-dl-pdf-link-free',
                'a[title*="Download"]',
                'a[aria-label*="Download"]',
                'a.c-pdf-download__link',
                'a[data-track-action="download pdf"]',
                '.download-links-holder a',
                'a.download-link'
            ]
            
            for selector in backup_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    href = elem.get_attribute("href")
                    if href:
                        print(f"[调试] 备用选择器 {selector} 获取到下载链接: {href}")
                        return href
                except Exception:
                    continue
                    
            print(f"[调试] 未能获取到PDF下载链接")
            return None
        except Exception as e:
            print(f"[调试] 获取PDF下载链接异常: {e}")
            return None
    
    def _download_pdf_immediately(self, title, download_link, cookies_str=None, user_agent=None):
        """用requests+cookie下载PDF文件"""
        try:
            from .utils import sanitize_filename
            import os
            import requests
            
            # 创建下载目录
            download_dir = self.config.DOWNLOAD_DIR
            os.makedirs(download_dir, exist_ok=True)
            
            # 处理文件名
            filename = sanitize_filename(title) + ".pdf"
            
            # 防止文件名重复
            base_filepath = os.path.join(download_dir, filename)
            filepath = base_filepath
            counter = 1
            while os.path.exists(filepath):
                name_parts = os.path.splitext(filename)
                new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
                filepath = os.path.join(download_dir, new_filename)
                counter += 1
                if counter > 2:  # 只在第一次重命名时打印，避免日志过多
                    print(f"[{title}] 文件名重复，使用新文件名: {new_filename}")
                
            # 处理cookie
            def cookie_str_to_dict(cookie_str):
                cookies = {}
                for item in cookie_str.split(';'):
                    if '=' in item:
                        k, v = item.strip().split('=', 1)
                        cookies[k] = v
                return cookies
                
            cookies = cookie_str_to_dict(cookies_str) if cookies_str else {c['name']: c['value'] for c in self.driver.get_cookies()}
            headers = {
                'User-Agent': user_agent or self.driver.execute_script("return navigator.userAgent;"),
                'Referer': self.driver.current_url,
                'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(download_link, headers=headers, cookies=cookies, stream=True, timeout=30)
                    
                    # 改进的状态码处理
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '').lower()
                        
                        # 检查内容类型
                        if 'application/pdf' in content_type or 'octet-stream' in content_type:
                            pass  # 内容类型正确，继续处理
                        else:
                            # 内容类型不匹配，检查文件头
                            print(f"[{title}] 警告: 内容类型不是PDF ({content_type})，检查文件头")
                            first_chunk = next(response.iter_content(chunk_size=8192), None)
                            if not first_chunk or b'%PDF' not in first_chunk[:10]:
                                print(f"[{title}] 下载失败: 文件头不是PDF标志 (尝试 {attempt + 1}/{max_retries})")
                                if attempt < max_retries - 1:
                                    time.sleep(2 ** attempt)
                                continue  # 跳过当前重试，进入下一次循环
                            print(f"[{title}] 文件头确认为PDF，继续下载")
                            
                        # 写入文件
                        with open(filepath, 'wb') as f:
                            # 如果已经读取了第一块，先写入
                            if 'first_chunk' in locals() and first_chunk:
                                f.write(first_chunk)
                            # 继续读取和写入剩余内容
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    
                        # 下载后再次验证文件
                        if os.path.getsize(filepath) < 1000:  # 小于1KB可能有问题
                            with open(filepath, 'rb') as f:
                                content = f.read(10)
                                if b'%PDF' not in content:
                                    print(f"[{title}] 下载的文件不是有效PDF，大小: {os.path.getsize(filepath)} 字节")
                                    os.remove(filepath)  # 删除无效文件
                                    if attempt < max_retries - 1:
                                        time.sleep(2 ** attempt)
                                    continue  # 尝试下一次重试
                                    
                        print(f"[{title}] 下载成功: {filepath}")
                        print(f"[调试] PDFProcessor 实际下载绝对路径: {os.path.abspath(filepath)}")
                        return True
                    elif response.status_code == 403:
                        print(f"[{title}] 下载失败: HTTP 403 (可能需要订阅权限)")
                        return False
                    else:
                        print(f"[{title}] 下载失败: HTTP {response.status_code} (尝试 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
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