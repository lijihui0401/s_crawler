#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Science期刊爬虫主程序
支持多driver并发爬取，提高效率
"""

import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import ScienceConfig
from src.utils import create_driver
from src.link_collector import LinkCollector
from src.driver_manager import DriverManager
from src.download_manager import DownloadManager

def main():
    """主函数"""
    print("=" * 60)
    print("Science期刊爬虫 - 多Driver并发版本")
    print("=" * 60)
    
    # 创建配置
    config = ScienceConfig()
    config.create_download_dir()
    
    # 第一步：收集所有详情页链接
    print("\n第一步：收集详情页链接")
    print("-" * 40)
    
    # 创建第一个driver用于收集链接
    try:
        # 连接到现有浏览器
        collector_driver = create_driver(debug_port=config.CHROME_DEBUG_PORT)
        collector_driver.get(config.SEARCH_URL)
        time.sleep(config.SLEEP_TIME)
        
        # 收集链接
        collector = LinkCollector(collector_driver)
        all_articles = collector.collect_all_links()
        
        if not all_articles:
            print("没有收集到任何文章链接，程序退出")
            collector_driver.quit()
            return
        
        print(f"成功收集到{len(all_articles)}篇文章")
        
    except Exception as e:
        print(f"收集链接失败：{e}")
        return
    
    # 第二步：使用多driver并发处理文章
    print("\n第二步：多Driver并发处理文章")
    print("-" * 40)
    
    # 创建driver管理器
    driver_manager = DriverManager()
    
    try:
        # 创建多个driver实例
        driver_count = driver_manager.create_drivers()
        
        if driver_count == 0:
            print("没有成功创建任何driver实例，程序退出")
            return
        
        # 使用多driver并发处理文章
        pdf_tasks = driver_manager.process_articles_with_multiple_drivers(all_articles)
        
        if not pdf_tasks:
            print("没有获取到任何PDF下载链接，程序退出")
            return
        
        print(f"成功获取到{len(pdf_tasks)}个PDF下载链接")
        
    except Exception as e:
        print(f"多driver处理失败：{e}")
        return
    finally:
        # 关闭所有driver
        driver_manager.close_all_drivers()
        if 'collector_driver' in locals():
            collector_driver.quit()
    
    # 第三步：统计下载结果
    print("\n第三步：统计下载结果")
    print("-" * 40)
    
    try:
        # 统计下载结果
        successful_downloads = [task for task in pdf_tasks if task and task.get('downloaded', False)]
        failed_downloads = [task for task in pdf_tasks if task and not task.get('downloaded', False)]
        
        print(f"下载完成！")
        print(f"成功下载: {len(successful_downloads)}个")
        print(f"下载失败: {len(failed_downloads)}个")
        
        if failed_downloads:
            print("\n下载失败的文件：")
            for task in failed_downloads:
                print(f"- {task['title']}")
        
        # 显示下载统计
        download_manager = DownloadManager()
        stats = download_manager.get_download_stats()
        print(f"\n下载统计：")
        print(f"总文件数：{stats['total_files']}")
        print(f"总大小：{stats['total_size_mb']:.2f} MB")
        
    except Exception as e:
        print(f"统计下载结果失败：{e}")
        return
    
    print("\n" + "=" * 60)
    print("爬取完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序异常：{e}")
        import traceback
        traceback.print_exc() 