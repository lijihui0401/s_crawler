import os

# Science期刊爬虫配置
class ScienceConfig:
    # 基础配置
    SEARCH_URL = "https://www.science.org/action/doSearch?AllField=twist+angle+2D+materials&AfterYear=2010&BeforeYear=2025&queryID=54%2F8297718952&startPage=0&pageSize=10"
    DOWNLOAD_DIR = "science_downloads"
    MAX_COUNT = 20  # 最大抓取数量
    
    # 并发配置
    DRIVER_COUNT = 5  # 同时开启的driver数量
    DOWNLOAD_THREADS = 10  # PDF下载线程数
    
    # 时间配置
    SLEEP_TIME = 2  # 页面等待时间
    RETRY_COUNT = 1  # 重试次数
    
    # Chrome配置
    CHROME_DEBUG_PORT = 9222  # 第一个Chrome调试端口（用于收集链接）
    CHROME_DEBUG_PORTS = [9223, 9224, 9225, 9226]  # 其他Chrome调试端口（用于并发处理）
    
    # 选择器配置
    SELECTORS = {
        'search_cards': ".card.pb-3.mb-4.border-bottom",
        'title_link': ".card-header h2.article-title > a",
        'pdf_button': "#main > div.article-container > article > header > div > div.info-panel > div.info-panel__right-content > div.info-panel__formats.info-panel__item > a",
        'pdf_icon': "i.icon-pdf",
        'download_button': "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a",
        'next_page': "li.page-item.active + li.page-item > a"
    }
    
    @classmethod
    def create_download_dir(cls):
        """创建下载目录"""
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True) 