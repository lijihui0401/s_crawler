import os

# Science期刊爬虫配置
class ScienceConfig:
    # 基础配置
    SEARCH_URL = "https://www.science.org/action/doSearch?AllField=twist+angle+2D+materials&AfterYear=2010&BeforeYear=2025&queryID=54%2F8297718952&startPage=0&pageSize=100"
    DOWNLOAD_DIR = "science_downloads"
    MAX_COUNT = 2  # 最大抓取数量
    
    # 单一driver配置
    DRIVER_COUNT = 1  # 只使用1个driver
    DOWNLOAD_THREADS = 5  # PDF下载线程数
    
    # 时间配置
    SLEEP_TIME = 1  # 页面等待时间（从2秒减少到1秒）
    RETRY_COUNT = 1  # 重试次数
    
    # 反爬虫配置
    RANDOM_DELAY_MIN = 2  # 随机延迟最小值（秒）
    RANDOM_DELAY_MAX = 5  # 随机延迟最大值（秒）
    DOWNLOAD_DELAY_MIN = 1  # 下载前延迟最小值（秒）
    DOWNLOAD_DELAY_MAX = 3  # 下载前延迟最大值（秒）
    
    # Chrome配置
    CHROME_DEBUG_PORT = 9222  # Chrome调试端口
    
    # 数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '12345678',
        'database': 'article_t_a_db',
        'charset': 'utf8mb4',
        'port': 3306
    }
    
    # 表名
    TABLE_NAME = 'science'
    
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