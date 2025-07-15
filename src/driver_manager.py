import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import ScienceConfig
from .utils import create_driver
from .pdf_processor import PDFProcessor

class DriverManager:
    """Driver管理器，负责管理多个driver实例"""
    
    def __init__(self):
        self.config = ScienceConfig()
        self.drivers = []
    
    def create_drivers(self, count=None):
        """创建指定数量的driver实例"""
        if count is None:
            count = self.config.DRIVER_COUNT
        
        print(f"正在创建{count}个driver实例...")
        
        for i in range(count):
            try:
                if i == 0:
                    # 第一个driver连接到现有浏览器（用于收集链接）
                    debug_port = self.config.CHROME_DEBUG_PORT
                    print(f"Driver {i+1} 连接到端口: {debug_port}")
                    driver = create_driver(debug_port=debug_port)
                elif i-1 < len(self.config.CHROME_DEBUG_PORTS):
                    # 其他driver连接到对应的现有浏览器
                    debug_port = self.config.CHROME_DEBUG_PORTS[i-1]
                    print(f"Driver {i+1} 连接到端口: {debug_port}")
                    driver = create_driver(debug_port=debug_port)
                else:
                    # 如果端口不够，创建新的Chrome实例
                    print(f"Driver {i+1} 创建新的Chrome实例")
                    driver = create_driver(headless=False)
                
                # 验证driver连接
                try:
                    current_url = driver.current_url
                    print(f"Driver {i+1} 连接成功，当前URL: {current_url}")
                except Exception as e:
                    print(f"Driver {i+1} 连接验证失败: {e}")
                    continue
                
                self.drivers.append(driver)
                print(f"Driver {i+1} 创建成功")
                
            except Exception as e:
                print(f"创建Driver {i+1} 失败：{e}")
                continue
        
        print(f"成功创建{len(self.drivers)}个driver实例")
        return len(self.drivers)
    
    def process_articles_with_multiple_drivers(self, articles):
        """使用多个driver并发处理文章"""
        if not self.drivers:
            print("没有可用的driver实例")
            return []
        
        # 将文章分配给不同的driver
        driver_count = len(self.drivers)
        tasks_per_driver = len(articles) // driver_count
        remainder = len(articles) % driver_count
        
        print(f"将{len(articles)}篇文章分配给{driver_count}个driver处理...")
        
        # 分配任务
        start_idx = 0
        driver_tasks = []
        
        for i in range(driver_count):
            # 计算当前driver的任务数量
            current_tasks = tasks_per_driver + (1 if i < remainder else 0)
            end_idx = start_idx + current_tasks
            
            if current_tasks > 0:
                assigned_articles = articles[start_idx:end_idx]
                driver_tasks.append({
                    'driver_index': i,
                    'articles': assigned_articles
                })
                print(f"Driver {i+1} 分配了 {len(assigned_articles)} 篇文章:")
                for j, article in enumerate(assigned_articles):
                    print(f"  {j+1}. {article['title']}")
            
            start_idx = end_idx
        
        # 使用线程池并发处理
        results = []
        with ThreadPoolExecutor(max_workers=driver_count) as executor:
            futures = []
            
            for task in driver_tasks:
                future = executor.submit(
                    self._process_articles_with_driver,
                    task['driver_index'],
                    task['articles']
                )
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    driver_results = future.result()
                    results.extend(driver_results)
                except Exception as e:
                    print(f"Driver处理任务异常：{e}")
        
        return results
    
    def _process_articles_with_driver(self, driver_index, articles):
        """单个driver处理分配的文章"""
        driver = self.drivers[driver_index]
        processor = PDFProcessor(driver)
        results = []
        
        print(f"[Driver {driver_index+1}] 开始处理{len(articles)}篇文章...")
        
        for i, article in enumerate(articles):
            try:
                print(f"[Driver {driver_index+1}] 处理第{i+1}篇文章: {article['title']}")
                result = processor.process_article(article)
                if result:
                    results.append(result)
                    print(f"[Driver {driver_index+1}] 第{i+1}篇文章处理成功")
                else:
                    print(f"[Driver {driver_index+1}] 第{i+1}篇文章处理失败")
                
                print(f"[Driver {driver_index+1}] 进度: {i+1}/{len(articles)}")
                
            except Exception as e:
                print(f"[Driver {driver_index+1}] 处理文章异常：{e}")
                continue
        
        print(f"[Driver {driver_index+1}] 完成处理，成功获取{len(results)}个PDF链接")
        return results
    
    def get_cookies_and_user_agent(self, driver_index=0):
        """获取指定driver的cookies和User-Agent"""
        if not self.drivers or driver_index >= len(self.drivers):
            return {}, ""
        
        driver = self.drivers[driver_index]
        
        try:
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            user_agent = driver.execute_script("return navigator.userAgent;")
            return cookies, user_agent
        except Exception as e:
            print(f"获取cookies和User-Agent失败：{e}")
            return {}, ""
    
    def close_all_drivers(self):
        """关闭所有driver实例"""
        print("正在关闭所有driver实例...")
        
        for i, driver in enumerate(self.drivers):
            try:
                driver.quit()
                print(f"Driver {i+1} 已关闭")
            except Exception as e:
                print(f"关闭Driver {i+1} 失败：{e}")
        
        self.drivers.clear()
        print("所有driver实例已关闭") 