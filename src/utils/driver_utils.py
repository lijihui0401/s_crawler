"""
Driver工具模块
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def create_driver(headless: bool = False, debug_port: Optional[int] = None) -> webdriver.Chrome:
    """
    创建Chrome driver实例
    
    Args:
        headless: 是否无头模式
        debug_port: 调试端口，用于连接已打开的浏览器
        
    Returns:
        Chrome driver实例
    """
    options = Options()
    
    if debug_port:
        # 连接到已打开的浏览器
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        logger.info(f"连接到已打开的浏览器，调试端口: {debug_port}")
    else:
        # 创建新的浏览器实例
        if headless:
            options.add_argument("--headless")
        
        # 基本设置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # 禁用图片和CSS以加快速度
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        # 用户代理
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        logger.info("Chrome driver创建成功")
        return driver
    except Exception as e:
        logger.error(f"创建Chrome driver失败: {e}")
        raise


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
            
        # 检查详情页：能否找到PDF图标
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


def wait_for_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    等待元素出现
    
    Args:
        driver: WebDriver实例
        by: 定位方式
        value: 定位值
        timeout: 超时时间（秒）
        
    Returns:
        找到的元素，如果超时返回None
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((str(by), value))
        )
        return element
    except TimeoutException:
        logger.warning(f"等待元素超时: {by} = {value}")
        return None


def safe_click(driver: webdriver.Chrome, element, timeout: int = 10) -> bool:
    """
    安全点击元素
    
    Args:
        driver: WebDriver实例
        element: 要点击的元素
        timeout: 超时时间（秒）
        
    Returns:
        是否点击成功
    """
    try:
        # 等待元素可点击
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(element)
        )
        
        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        # 尝试点击
        element.click()
        return True
        
    except (TimeoutException, ElementClickInterceptedException) as e:
        logger.warning(f"点击元素失败: {e}")
        try:
            # 尝试JavaScript点击
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e2:
            logger.error(f"JavaScript点击也失败: {e2}")
            return False 