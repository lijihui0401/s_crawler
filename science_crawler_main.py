#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Science期刊爬虫主程序
使用新的表结构，去掉original_url字段
"""

import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import ScienceConfig
from src.utils import create_driver
import src.utils as utils
from src.link_collector import LinkCollector
from src.driver_manager import DriverManager
from src.download_manager import DownloadManager
from src.database_manager import DatabaseManager

def main():
    """主函数"""
    import collections
    print("=" * 60)
    print("Science期刊爬虫 - 新表结构版本")
    print("=" * 60)
    
    # 记录所有步骤耗时
    step_times = collections.OrderedDict()
    total_start_time = time.time()
    
    # 创建配置
    t0 = time.time()
    config = ScienceConfig()
    config.create_download_dir()
    step_times['配置初始化'] = time.time() - t0
    
    # 创建driver管理器
    t0 = time.time()
    driver_manager = DriverManager()
    step_times['DriverManager初始化'] = time.time() - t0
    
    try:
        # 创建单个driver实例
        t0 = time.time()
        if not driver_manager.create_driver():
            print("创建driver失败，程序退出")
            return
        step_times['创建driver'] = time.time() - t0
        
        # 第一步：收集所有详情页链接
        print("\n第一步：收集详情页链接")
        print("-" * 40)
        
        # 使用driver访问搜索页面
        t0 = time.time()
        if driver_manager.driver:
            driver_manager.driver.get(config.SEARCH_URL)
            time.sleep(config.SLEEP_TIME)
        else:
            print("Driver未创建成功，程序退出")
            return
        step_times['页面加载'] = time.time() - t0
        
        # 收集链接
        t0 = time.time()
        collector = LinkCollector(driver_manager.driver)
        all_articles = collector.collect_all_links()
        step_times['收集详情页链接'] = time.time() - t0
        
        if not all_articles:
            print("没有收集到任何文章链接，程序退出")
            return
        print(f"成功收集到{len(all_articles)}篇文章")
        
        # 第二步：处理文章获取PDF链接
        print("\n第二步：处理文章获取PDF链接")
        print("-" * 40)
        t0 = time.time()
        pdf_tasks = driver_manager.process_articles(all_articles)
        step_times['处理文章获取PDF链接'] = time.time() - t0
        
        if not pdf_tasks:
            print("没有获取到任何PDF下载链接，程序退出")
            return
        print(f"成功获取到{len(pdf_tasks)}个PDF下载链接")
        
        # 第三步：下载PDF文件
        print("\n第三步：下载PDF文件")
        print("-" * 40)
        t0 = time.time()
        
        # 重新获取最新的cookies和user_agent
        print("重新获取最新的cookies和user_agent...")
        cookies, user_agent = driver_manager.get_cookies_and_user_agent()
        print(f"获取到 {len(cookies)} 个cookies")
        print(f"User-Agent: {user_agent[:50]}...")
        
        download_manager = DownloadManager()
        
        import random
        for i, task in enumerate(pdf_tasks):
            if task and task.get('download_link'):
                print(f"检查第{i+1}个PDF: {task['title']}")
                
                from src.utils import sanitize_filename
                filename = sanitize_filename(task['title']) + ".pdf"
                filepath = os.path.join(config.DOWNLOAD_DIR, filename)
                
                # 检查文件是否已经下载
                if os.path.exists(filepath):
                    success = True
                    print(f"PDF已存在: {task['title']}")
                else:
                    success = False
                    print(f"PDF未找到: {task['title']}")
                
                task['downloaded'] = success
                if success:
                    import hashlib
                    try:
                        md5_hash = hashlib.md5()
                        with open(filepath, "rb") as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                md5_hash.update(chunk)
                        task['pdf_md5'] = md5_hash.hexdigest()
                        task['download_path'] = filepath
                    except Exception as e:
                        print(f"计算MD5失败: {e}")
                        task['pdf_md5'] = None
                else:
                    task['pdf_md5'] = None
                    print(f"下载失败: {task['title']}")
                
                # 下载间隔，避免过于频繁
                if i < len(pdf_tasks) - 1:  # 不是最后一个
                    interval = random.uniform(config.RANDOM_DELAY_MIN, config.RANDOM_DELAY_MAX)
                    print(f"等待 {interval:.1f} 秒后继续下一个下载...")
                    time.sleep(interval)
        step_times['下载PDF文件'] = time.time() - t0
        
        # 第四步：保存到数据库
        print("\n第四步：保存到数据库")
        print("-" * 40)
        t0 = time.time()
        db_manager = DatabaseManager()
        articles_to_save = []
        for task in pdf_tasks:
            if task and task.get('downloaded', False):
                article_data = {
                    'title': task.get('title'),
                    'url': task.get('url'),
                    'doi': task.get('doi'),
                    'authors': task.get('authors', []),
                    'journal': task.get('journal', 'Science'),
                    'abstract': task.get('abstract', ''),
                    'keywords': task.get('keywords', []),
                    'publication_date': task.get('publication_date'),
                    'pdf_url': task.get('download_link'),
                    'download_path': task.get('download_path'),
                    'pdf_md5': task.get('pdf_md5')
                }
                articles_to_save.append(article_data)
        if articles_to_save:
            success = db_manager.save_articles_to_database(articles_to_save)
            if success:
                print(f"成功保存{len(articles_to_save)}篇文章到数据库")
            else:
                print("保存到数据库失败")
        else:
            print("没有成功下载的文章需要保存")
        step_times['保存到数据库'] = time.time() - t0
        
        # 第五步：统计结果
        print("\n第五步：统计结果")
        print("-" * 40)
        t0 = time.time()
        successful_downloads = [task for task in pdf_tasks if task and task.get('downloaded', False)]
        failed_downloads = [task for task in pdf_tasks if task and not task.get('downloaded', False)]
        print(f"下载完成！")
        print(f"成功下载: {len(successful_downloads)}个")
        print(f"下载失败: {len(failed_downloads)}个")
        if failed_downloads:
            print("\n下载失败的文件：")
            for task in failed_downloads:
                print(f"- {task['title']}")
        stats = download_manager.get_download_stats()
        print(f"\n下载统计：")
        print(f"总文件数：{stats['total_files']}")
        print(f"总大小：{stats['total_size_mb']:.2f} MB")
        db_count = db_manager.get_article_count()
        print(f"数据库中的文章总数：{db_count}")
        step_times['统计与收尾'] = time.time() - t0
        
        # 总体性能统计
        total_time = time.time() - total_start_time
        print(f"\n" + "=" * 60)
        print("详细性能统计")
        print("=" * 60)
        for k, v in step_times.items():
            print(f"{k:<20}: {v:.3f} 秒 ({v/total_time*100:.1f}%)")
        print(f"总耗时{'':<14}: {total_time:.3f} 秒 (100%)")
        print("=" * 60)
        
        # 性能分析建议
        print(f"\n性能分析:")
        for k, v in step_times.items():
            if v > total_time * 0.2:
                print(f"⚠️  {k} 占比较高 ({v/total_time*100:.1f}%)，建议重点关注优化！")
        print("\n爬取完成！")
        print("=" * 60)
    except Exception as e:
        print(f"程序执行失败：{e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        driver_manager.close_driver()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序异常：{e}")
        import traceback
        traceback.print_exc() 