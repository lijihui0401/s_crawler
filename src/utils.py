import re
import os
import time
import requests
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
    """使用requests下载PDF文件"""
    filepath = os.path.join(download_dir, filename)
    
    try:
        print(f"[{filename}] 正在下载到: {filepath}")
        r = requests.get(
            download_link, 
            headers={"User-Agent": user_agent}, 
            cookies=cookies, 
            timeout=60
        )
        r.raise_for_status()
        
        with open(filepath, "wb") as f:
            f.write(r.content)
        
        print(f"[{filename}] 下载成功！")
        return True
        
    except Exception as e:
        print(f"[{filename}] 下载失败：{e}")
        if retry > 0:
            print(f"[{filename}] 正在重试...")
            time.sleep(2)
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
            print("[DEBUG] 未找到文章标题")
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
    先判断页面是否正常，再判断异常（关键词检测）。
    检测到异常时暂停，等待用户手动处理。
    """
    print(f"\n[DEBUG] 开始验证码检测，当前URL: {driver.current_url}")
    
    if is_page_normal(driver):
        print("[DEBUG] 页面正常，无需处理验证码")
        return False  # 页面正常，直接继续
        
    if is_captcha_or_abnormal(driver):
        print("\n" + "="*50)
        print("⚠️  检测到人机验证/异常页面，请在浏览器中手动完成验证！")
        print("完成后请按回车键继续...")
        print("="*50)
        
        # 在多线程环境中，使用文件信号而不是input()
        import os
        signal_file = "captcha_signal.txt"
        
        # 创建信号文件
        with open(signal_file, "w") as f:
            f.write("waiting")
        
        start_time = time.time()
        while not is_page_normal(driver):
            if time.time() - start_time > timeout:
                print("等待超时，请重试。")
                if os.path.exists(signal_file):
                    os.remove(signal_file)
                return False
                
            print("页面仍异常，请完成验证后删除captcha_signal.txt文件...")
            
            # 检查信号文件是否被删除
            if not os.path.exists(signal_file):
                print("检测到信号文件被删除，继续处理...")
                break
                
            time.sleep(2)  # 等待2秒再检查
            
        print("页面已恢复正常，继续任务。")
        return True
        
    # 既不正常也没检测到异常，可能是网络问题
    print("页面异常但未检测到验证码，可能是网络问题，建议刷新页面。")
    return False 