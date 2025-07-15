import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. 配置
SEARCH_URL = "https://www.science.org/action/doSearch?AllField=twist+angle&AfterYear=2010&BeforeYear=2025&queryID=26%2F8295040111"
DOWNLOAD_DIR = "t_a_download"
CHROME_DEBUG_PORT = 9222  # 你需要用 --remote-debugging-port=9222 启动Chrome
MAX_COUNT = 20
THREADS = 10
TABS = 5
SLEEP_TIME = 2

# 2. 工具函数：清理文件名
def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    if len(filename) > 200:
        filename = filename[:200]
    return filename or "untitled"

# 3. 创建下载目录
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 4. 启动Selenium，连接到已打开的浏览器
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{CHROME_DEBUG_PORT}")
driver = webdriver.Chrome(options=chrome_options)

driver.get(SEARCH_URL)
time.sleep(SLEEP_TIME)

# 5. 批量收集详情页链接和标题
links = []
while len(links) < MAX_COUNT:
    cards = driver.find_elements(By.CSS_SELECTOR, ".card.pb-3.mb-4.border-bottom")
    for card in cards:
        if len(links) >= MAX_COUNT:
            break
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, ".card-header h2.article-title > a")
            title = title_elem.text.strip()
            detail_href = title_elem.get_attribute("href")
            if not detail_href:
                continue
            detail_url = detail_href if detail_href.startswith("http") else "https://www.science.org" + detail_href
            links.append({"title": title, "url": detail_url})
        except Exception as e:
            print(f"收集详情页链接异常，跳过：{e}")
            continue
    # 翻页
    if len(links) < MAX_COUNT:
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "li.page-item.active + li.page-item > a")
            next_btn.click()
            print("翻到下一页收集更多链接...")
            time.sleep(SLEEP_TIME)
        except Exception:
            print("没有下一页，结束收集。")
            break

print(f"共收集到{len(links)}条详情页链接。\n")

# 6. 新开5个标签页，并分配任务
# 先分组
groups = [[] for _ in range(TABS)]
for idx, item in enumerate(links):
    groups[idx % TABS].append(item)

# 打开新标签页
for _ in range(TABS - 1):
    driver.execute_script("window.open('about:blank')")
    time.sleep(0.5)
window_handles = driver.window_handles

# 7. 每个标签页串行处理自己的任务队列，收集所有PDF下载链接
pdf_download_tasks = []
from bs4 import BeautifulSoup
for tab_idx, handle in enumerate(window_handles[:TABS]):
    driver.switch_to.window(handle)
    print(f"\n[标签页{tab_idx+1}] 开始处理 {len(groups[tab_idx])} 条任务...")
    for item in groups[tab_idx]:
        title = item["title"]
        detail_url = item["url"]
        print(f"[标签页{tab_idx+1}] 处理: {title}")
        try:
            driver.get(detail_url)
            time.sleep(SLEEP_TIME)
            # 健壮查找PDF按钮
            pdf_a_elem = None
            a_tags = driver.find_elements(By.CSS_SELECTOR, "#main > div.article-container > article > header a")
            for a in a_tags:
                try:
                    i = a.find_element(By.CSS_SELECTOR, "i.icon-pdf")
                    pdf_a_elem = a
                    break
                except Exception:
                    continue
            if not pdf_a_elem:
                print(f"[标签页{tab_idx+1}] [{title}] 未找到PDF按钮，跳过")
                continue
            pdf_page_href = pdf_a_elem.get_attribute("href")
            if not pdf_page_href:
                print(f"[标签页{tab_idx+1}] [{title}] 未找到PDF页链接，跳过")
                continue
            pdf_page_url = pdf_page_href if pdf_page_href.startswith("http") else "https://www.science.org" + pdf_page_href
            driver.get(pdf_page_url)
            time.sleep(SLEEP_TIME)
            # 获取下载链接
            try:
                download_a_elem = driver.find_element(By.CSS_SELECTOR, "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a")
                download_link = download_a_elem.get_attribute("href")
                if not download_link:
                    print(f"[标签页{tab_idx+1}] [{title}] 未找到PDF下载链接，跳过")
                    continue
                pdf_download_tasks.append({"title": title, "download_link": download_link})
                print(f"[标签页{tab_idx+1}] [{title}] 获取到PDF下载链接")
            except Exception:
                print(f"[标签页{tab_idx+1}] [{title}] 未找到PDF下载链接，跳过")
                continue
        except Exception as e:
            print(f"[标签页{tab_idx+1}] [{title}] 处理异常，跳过：{e}")
            continue

# 8. 获取cookie和User-Agent（用于requests）
cookies = {c['name']: c['value'] for c in driver.get_cookies()}
user_agent = driver.execute_script("return navigator.userAgent;")
driver.quit()

print(f"\n共获取到{len(pdf_download_tasks)}个PDF下载链接，开始多线程下载...\n")

# 9. 多线程下载PDF

def download_pdf_worker(item, cookies, user_agent, retry=1):
    title = item["title"]
    download_link = item["download_link"]
    try:
        filename = sanitize_filename(title) + ".pdf"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        print(f"[{title}] 正在下载到: {filepath}")
        r = requests.get(download_link, headers={"User-Agent": user_agent}, cookies=cookies, timeout=60)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(r.content)
        print(f"[{title}] 下载成功！")
        return True
    except Exception as e:
        print(f"[{title}] 下载失败：{e}")
        if retry > 0:
            print(f"[{title}] 正在重试...")
            return download_pdf_worker(item, cookies, user_agent, retry=retry-1)
        return False

with ThreadPoolExecutor(max_workers=THREADS) as executor:
    futures = [executor.submit(download_pdf_worker, item, cookies, user_agent, 1) for item in pdf_download_tasks]
    for idx, future in enumerate(as_completed(futures)):
        try:
            result = future.result()
        except Exception as e:
            print(f"第{idx+1}条多线程任务异常：{e}") 