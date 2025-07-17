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
from src.utils.download_utils import download_file  # 新增

import hashlib
import random

# 用户自定义cookie和user-agent
COOKIES = "MACHINE_LAST_SEEN=2025-07-16T03%3A44%3A40.172-07%3A00;__gads=ID=cfa66b58f227b128:T=1752401220:RT=1752662996:S=ALNI_MaerjnUjKibf-S0HYOSBFPDJEhwcg;cookiePolicy=iaccept;consent={\"Marketing\":true,\"created_time\":\"2025-07-13T10:07:24.745Z\"};MAID=zV5gW1r5p3ESCgsZ80tePw==;__gpi=UID=0000115ee5b17a1d:T=1752401220:RT=1752662996:S=ALNI_MaiLSSFYJFT1hHFVuUaNaaXcOOXdQ;weby_location_cookie={\"location_requires_cookie_consent\":\"true\",\"location_requires_cookie_paywall\":\"false\",\"int\":\"22fb890f-1b07-4380-a472-c8bbb1157f5c\"};s_pltp=www.science.org%2Fdoi%2Fepdf%2F10.1126%2Fscience.abl8371;__cf_bm=DD9RtTzPm8KTr3DXCDw6SRfiWGLFgYQXhNgGKp8ob_Y-1752662680-1.0.1.1-P_DE_N_Pme6b5nBCyDOjHpPRsz2Ek4bq5mbDTJ8YqbBf32rOuM2hbDp9A9w1HhZxsbT5rk47MEO44R4FMSk1Spa_T7g42MasjGzpdQOoPac;__eoi=ID=afe440858526065e:T=1752401220:RT=1752662996:S=AA-AfjaBDP0vNp5CQzIuSJT_0DFS;JSESSIONID=04685CEEF358FA4A0AFAFEF7511AAEB2;s_plt=1.55"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

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
    
    # 新增：初始化download_manager
    download_manager = DownloadManager()
    
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
        
        # === 新增：下载前DOI查重 ===
        db_manager = DatabaseManager()
        unique_articles = []
        for article in all_articles:
            doi = article.get('doi')
            if doi and db_manager.is_doi_exists(doi):
                print(f"已存在（DOI查重）: {article['title']}")
                continue
            unique_articles.append(article)
        print(f"查重后剩余{len(unique_articles)}篇文章")
        
        # 第二步：处理文章获取PDF链接
        print("\n第二步：处理文章获取PDF链接")
        print("-" * 40)
        t0 = time.time()
        pdf_tasks = driver_manager.process_articles(unique_articles)
        step_times['处理文章获取PDF链接'] = time.time() - t0

        print(f"[调试] pdf_tasks 类型: {type(pdf_tasks)}")
        if isinstance(pdf_tasks, list):
            print(f"[调试] pdf_tasks 长度: {len(pdf_tasks)}")
            for idx, t in enumerate(pdf_tasks[:5]):
                print(f"[调试] pdf_tasks[{idx}]: {str(t)[:300]}")
            if len(pdf_tasks) > 5:
                print(f"[调试] ... 共{len(pdf_tasks)}条，仅展示前5条 ...")
        else:
            print(f"[调试] pdf_tasks 内容: {str(pdf_tasks)[:500]}")

        if not pdf_tasks:
            print("没有获取到任何PDF下载链接，程序退出")
            return
        print(f"成功获取到{len(pdf_tasks)}个PDF下载链接")
        
        # 第三步：严格串行处理PDF下载和入库
        print("\n第三步：严格串行处理PDF下载和入库")
        print("-" * 40)
        t0 = time.time()
        
        success_count = 0
        for idx, task in enumerate(pdf_tasks, 1):
            print(f"\n=== 处理第 {idx}/{len(pdf_tasks)} 条 ===")
            print(f"文章: {task['title']}")
            print(f"DOI: {task.get('doi', '无')}")
            try:
                # 1. 下载PDF
                filename = utils.sanitize_filename(task['title']) + ".pdf"
                filepath = os.path.join(config.DOWNLOAD_DIR, filename)
                if not os.path.exists(filepath):
                    print("> 开始下载PDF...")
                    if not download_file(
                        url=task['download_link'],
                        filepath=filepath,
                        timeout=30,
                        max_retries=3,
                        cookies=COOKIES,
                        user_agent=USER_AGENT
                    ):
                        print("! PDF下载失败，跳过该文章")
                        continue
                # 2. 计算MD5
                print("> 计算文件指纹...")
                with open(filepath, "rb") as f:
                    md5_hash = hashlib.md5(f.read()).hexdigest()
                task['pdf_md5'] = md5_hash
                task['download_path'] = filepath
                # 3. 立即入库
                print("> 写入数据库...")
                article_data = {
                    'title': task['title'],
                    'url': task['url'],
                    'doi': task.get('doi'),
                    'authors': task.get('authors', []),
                    'journal': task.get('journal', 'Science'),
                    'abstract': task.get('abstract', ''),
                    'keywords': task.get('keywords', []),
                    'publication_date': task.get('publication_date'),
                    'pdf_url': task['download_link'],
                    'download_path': task['download_path'],
                    'pdf_md5': task['pdf_md5']
                }
                if db_manager.save_articles_to_database([article_data]):
                    success_count += 1
                    print(f"√ 成功入库 (总计: {success_count}/{len(pdf_tasks)})")
                else:
                    print("! 数据库写入失败")
            except Exception as e:
                print(f"! 处理失败: {str(e)}")
                continue
            # 间隔等待
            if idx < len(pdf_tasks):
                delay = random.uniform(1.0, 3.0)
                print(f"> 等待 {delay:.1f}秒...")
                time.sleep(delay)
        step_times['下载和入库'] = time.time() - t0
        
        # 第四步：保存到数据库
        print("\n第四步：保存到数据库")
        print("-" * 40)
        t0 = time.time()
        print("已在下载环节逐条保存，无需批量保存")
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