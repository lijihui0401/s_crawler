import time
from .config import ScienceConfig
from .utils import create_driver
from .pdf_processor import PDFProcessor

class DriverManager:
    """Driver管理器，负责管理单个driver实例"""
    
    def __init__(self):
        self.config = ScienceConfig()
        self.driver = None
    
    def create_driver(self):
        """创建单个driver实例"""
        print("正在创建driver实例...")
        
        try:
            # 连接到现有浏览器
            debug_port = self.config.CHROME_DEBUG_PORT
            print(f"Driver 连接到端口: {debug_port}")
            self.driver = create_driver(debug_port=debug_port)
            
            # 验证driver连接
            try:
                current_url = self.driver.current_url
                print(f"Driver 连接成功，当前URL: {current_url}")
            except Exception as e:
                print(f"Driver 连接验证失败: {e}")
                return False
            
            print("Driver 创建成功")
            return True
            
        except Exception as e:
            print(f"创建Driver 失败：{e}")
            return False
    
    def process_articles(self, articles, callback=None):
        """使用单个driver处理文章，支持逐条处理回调"""
        if not self.driver:
            print("没有可用的driver实例")
            return []
        
        processor = PDFProcessor(self.driver)
        results = []
        
        print(f"开始处理{len(articles)}篇文章...")
        
        for i, article in enumerate(articles):
            try:
                print(f"处理第{i+1}篇文章: {article['title']}")
                result = processor.process_article(article)
                if result:
                    # 如果有回调函数，立即处理
                    if callback:
                        callback(result, i+1, len(articles))
                    else:
                        results.append(result)
                    print(f"第{i+1}篇文章处理成功")
                else:
                    print(f"第{i+1}篇文章处理失败")
                
                print(f"进度: {i+1}/{len(articles)}")
                
                # 减少延迟，避免请求过于频繁
                time.sleep(0.3)  # 从SLEEP_TIME减少到0.3秒
                
            except Exception as e:
                print(f"处理文章异常：{e}")
                continue
        
        if callback:
            print(f"完成处理，已通过回调函数逐条处理")
        else:
            print(f"完成处理，成功获取{len(results)}个PDF链接")
        return results
    
    def get_cookies_and_user_agent(self):
        """获取driver的cookies和User-Agent"""
        if not self.driver:
            return {}, ""
        
        try:
            cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            return cookies, user_agent
        except Exception as e:
            print(f"获取cookies和User-Agent失败：{e}")
            return {}, ""
    
    def close_driver(self):
        """关闭driver实例"""
        if self.driver:
            print("正在关闭driver实例...")
            try:
                self.driver.quit()
                print("Driver 已关闭")
            except Exception as e:
                print(f"关闭Driver 失败：{e}")
            finally:
                self.driver = None 