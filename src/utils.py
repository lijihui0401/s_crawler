import os
import time
import requests
import hashlib
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    if len(filename) > 200:
        filename = filename[:200]
    return filename or "untitled"

def create_driver(use_existing_browser=True, debug_port=9222):
    """创建Selenium driver"""
    chrome_options = Options()
    
    if use_existing_browser:
        # 连接到已打开的Chrome浏览器
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        driver = webdriver.Chrome(options=chrome_options)
    else:
        # 创建新的Chrome实例
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver

def download_pdf_with_requests(download_link, filename, cookies, user_agent, download_dir, retry=1):
    """使用requests下载PDF文件 - 改进版，添加反爬虫策略"""
    import random
    filepath = os.path.join(download_dir, filename)
    
    # 调试：显示cookie信息
    print(f"[{filename}] 使用 {len(cookies)} 个cookies进行下载")
    if cookies:
        cookie_names = list(cookies.keys())
        print(f"[{filename}] Cookie名称: {cookie_names}")
    
    # 更完整的请求头
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0"
    }
    
    try:
        print(f"[{filename}] 正在下载到: {filepath}")
        
        # 随机延迟，模拟人类行为
        time.sleep(random.uniform(1, 3))
        
        r = requests.get(
            download_link, 
            headers=headers, 
            cookies=cookies, 
            timeout=60,
            stream=True  # 使用流式下载
        )
        
        if r.status_code == 403:
            print(f"[{filename}] 403错误 - 可能需要订阅权限或反爬虫检测")
            # 尝试不同的请求策略
            if retry > 0:
                print(f"[{filename}] 尝试不同的请求策略...")
                time.sleep(random.uniform(2, 5))
                
                # 尝试去掉一些可能触发检测的头部
                simple_headers = {
                    "User-Agent": user_agent,
                    "Accept": "*/*",
                    "Referer": "https://www.science.org/"
                }
                
                r = requests.get(
                    download_link,
                    headers=simple_headers,
                    cookies=cookies,
                    timeout=60,
                    stream=True
        )
        
        r.raise_for_status()
        
        # 流式写入文件
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"[{filename}] 下载成功！文件大小: {os.path.getsize(filepath)} 字节")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"[{filename}] 403 Forbidden - Science期刊拒绝访问，可能需要订阅权限")
        else:
            print(f"[{filename}] HTTP错误 {e.response.status_code}: {e}")
    except Exception as e:
        print(f"[{filename}] 下载失败：{e}")
    
        if retry > 0:
        print(f"[{filename}] 正在重试... (剩余重试次数: {retry-1})")
        time.sleep(random.uniform(3, 6))  # 重试前等待更长时间
            return download_pdf_with_requests(download_link, filename, cookies, user_agent, download_dir, retry=retry-1)
    
        return False

def is_page_normal(driver):
    """判断页面是否为正常内容（如能否获取到论文卡片/标题等元素）"""
    try:
        current_url = driver.current_url
        print(f"[DEBUG] 检查页面: {current_url}")
        
        # 检查搜索页面：能否找到论文卡片
        articles = driver.find_elements(By.CSS_SELECTOR, ".card.pb-3.mb-4.border-bottom")
        if articles and len(articles) > 0:
            print(f"[DEBUG] 找到{len(articles)}个论文卡片，页面正常")
            return True
        
        # 检查详情页：能否找到文章标题
        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1.article-title")
            if title and title.text.strip():
                print(f"[DEBUG] 找到文章标题: {title.text[:50]}...，页面正常")
                return True
        except NoSuchElementException:
            # 标题不是必需的，静默处理
            pass
            
        # 检查详情页：能否找到PDF图标（你提供的选择器）
        try:
            pdf_icons = driver.find_elements(By.CSS_SELECTOR, "i.icon-pdf")
            if pdf_icons and len(pdf_icons) > 0:
                print(f"[DEBUG] 找到{len(pdf_icons)}个PDF图标，页面正常")
                return True
        except NoSuchElementException:
            print("[DEBUG] 未找到PDF图标")
            pass
            
        # 检查PDF页面：能否找到下载按钮
        try:
            download_btn = driver.find_element(By.CSS_SELECTOR, "#app-navbar .btn-group.navbar-right .grouped.right a")
            if download_btn:
                print("[DEBUG] 找到下载按钮，页面正常")
                return True
        except NoSuchElementException:
            print("[DEBUG] 未找到下载按钮")
            pass
            
        # 检查是否有其他正常内容
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if len(body_text) > 100:  # 页面有足够的内容
                print(f"[DEBUG] 页面有{len(body_text)}字符内容，可能正常")
                return True
        except:
            pass
            
        print("[DEBUG] 页面内容检查失败，可能异常")
        return False
            
    except Exception as e:
        print(f"[DEBUG] 检查页面时异常: {e}")
        return False

def is_captcha_or_abnormal(driver):
    """判断页面是否为验证码/异常页面（关键词检测）"""
    try:
        page_text = driver.page_source.lower()
        title = driver.title.lower()
        
        print(f"[DEBUG] 页面标题: {title}")
        
        # 检查页面标题中的关键词
        title_keywords = ["cloudflare", "captcha", "verify", "checking"]
        if any(kw in title for kw in title_keywords):
            print(f"[DEBUG] 页面标题包含异常关键词: {title}")
            return True
            
        # 检查页面内容中的关键词
        content_keywords = ["captcha", "verify you are human", "cloudflare", "robot", "人机验证", "滑块", "checking your browser"]
        found_keywords = []
        for kw in content_keywords:
            if kw in page_text:
                found_keywords.append(kw)
                
        if found_keywords:
            print(f"[DEBUG] 页面内容包含异常关键词: {found_keywords}")
            return True
            
        print("[DEBUG] 未检测到异常关键词")
        return False
            
    except Exception as e:
        print(f"[DEBUG] 检查异常页面时出错: {e}")
        return False

def handle_captcha(driver, timeout=600):
    """
    简化的重试机制：找不到元素就等待5秒再找，连续三次找不到就刷新页面
    """
    print(f"\n[DEBUG] 开始元素检测，当前URL: {driver.current_url}")
    
    # 检查页面是否正常（能找到关键元素）
    if is_page_normal(driver):
        print("[DEBUG] 页面正常，无需处理")
        return False
    
    # 连续重试3次
    for attempt in range(3):
        print(f"[DEBUG] 第{attempt + 1}次重试，等待5秒...")
        time.sleep(5)
        
        # 重新检查页面
        if is_page_normal(driver):
            print("[DEBUG] 页面恢复正常，继续处理")
            return True
    
    # 连续3次都找不到，刷新页面
    print("[DEBUG] 连续3次未找到元素，刷新页面...")
    try:
        driver.refresh()
        time.sleep(5)  # 等待页面加载
        
        # 刷新后再次检查
        if is_page_normal(driver):
            print("[DEBUG] 刷新后页面正常，继续处理")
            return True
        else:
            print("[DEBUG] 刷新后页面仍异常，继续处理")
            return False
            
    except Exception as e:
        print(f"[DEBUG] 刷新页面失败: {e}")
        return False

def calculate_file_md5(filepath):
    """计算文件的MD5哈希值"""
    try:
        if not os.path.exists(filepath):
            return None
            
        md5_hash = hashlib.md5()
        with open(filepath, "rb") as f:
            # 分块读取大文件，避免内存占用过大
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        print(f"计算MD5失败: {e}")
        return None

def download_file(url, filepath, timeout=30, max_retries=3):
    """下载文件并返回MD5值"""
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        # 计算下载文件的MD5
        md5_value = calculate_file_md5(filepath)
        print(f"下载成功: {filepath}")
        print(f"MD5: {md5_value}")
        
        return True, md5_value
        
    except Exception as e:
        print(f"下载失败: {e}")
        if max_retries > 0:
            print(f"重试中... ({max_retries} 次剩余)")
            time.sleep(2)
            return download_file(url, filepath, timeout, max_retries - 1)
        return False, None

def extract_doi_from_url(url):
    """从Science URL中提取DOI"""
    import re
    # 匹配 /doi/10.1126/science.xxx 格式
    pattern = r'/doi/(10\.\d+/[^/]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def parse_publication_date(date_text):
    """解析发表日期文本为datetime对象"""
    from datetime import datetime
    try:
        # 处理 "10 Aug 2023" 格式
        return datetime.strptime(date_text.strip(), "%d %b %Y")
    except:
        try:
            # 处理其他可能的格式
            return datetime.strptime(date_text.strip(), "%Y-%m-%d")
        except:
            return None 