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
        
        # 第二步和第三步合并：逐条处理文章获取PDF链接并立即下载入库
        print("\n第二步：逐条处理文章获取PDF链接并立即下载入库")
        print("-" * 40)
        t0 = time.time()
        
        success_count = 0
        
        def process_single_article(result, current_idx, total_count):
            """处理单篇文章的回调函数"""
            nonlocal success_count
            print(f"\n=== 处理第 {current_idx}/{total_count} 条 ===")
            print(f"文章: {result['title']}")
            print(f"DOI: {result.get('doi', '无')}")
            
            # 1. 下载PDF阶段
            try:
                filename = utils.sanitize_filename(result['title']) + ".pdf"
                filepath = os.path.join(config.DOWNLOAD_DIR, filename)
                
                # 防止文件名重复
                base_filepath = filepath
                counter = 1
                while os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    name_parts = os.path.splitext(filename)
                    new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
                    filepath = os.path.join(config.DOWNLOAD_DIR, new_filename)
                    counter += 1
                
                # 检查是否已经下载了PDF（可能是由PDFProcessor下载的）
                # 在PDFProcessor下载后，文件名可能已经被重命名，需要查找所有可能的文件名
                pdf_exists = False
                actual_filepath = None
                
                # 检查原始文件名
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    pdf_exists = True
                    actual_filepath = filepath
                else:
                    # 检查可能的重命名文件
                    for i in range(1, 10):  # 检查最多10个可能的重命名
                        name_parts = os.path.splitext(filename)
                        possible_name = f"{name_parts[0]}_{i}{name_parts[1]}"
                        possible_path = os.path.join(config.DOWNLOAD_DIR, possible_name)
                        if os.path.exists(possible_path) and os.path.getsize(possible_path) > 0:
                            pdf_exists = True
                            actual_filepath = possible_path
                            break
                
                if pdf_exists and actual_filepath:
                    print(f"> 发现已下载的PDF文件: {os.path.basename(actual_filepath)}")
                    download_success = True
                else:
                    # 尝试下载
                    print(f"> 未找到已下载的PDF文件，尝试下载...")
                    # 检查两个可能的键名
                    download_link = result.get('pdf_url') or result.get('download_link')
                    if not download_link:
                        print(f"! 没有PDF下载链接，但将继续处理文章信息")
                        # 即使没有下载链接，也继续处理
                        actual_filepath = None
                        download_success = False
                    else:
                        # 保存PDF下载链接到结果字典
                        result['pdf_url'] = download_link
                        download_success = False
                        for attempt in range(3):
                            try:
                                download_success = utils.download_file(download_link, filepath, timeout=30)
                                if download_success:
                                    actual_filepath = filepath
                                    break
                            except Exception as e:
                                print(f"下载失败: {str(e)}")
                        
                        if not download_success:
                            print(f"下载最终失败: {download_link}")
                            print(f"! PDF下载失败，但将继续处理文章信息")
                            actual_filepath = None
                
                # 2. PDF处理阶段
                try:
                    # 计算PDF的MD5（如果有PDF文件）
                    if actual_filepath and os.path.exists(actual_filepath):
                        import hashlib
                        with open(actual_filepath, "rb") as f:
                            pdf_md5 = hashlib.md5(f.read()).hexdigest()
                        result['pdf_md5'] = pdf_md5
                        result['download_path'] = actual_filepath
                    
                    result['download_success'] = download_success
                    
                    # 确保pdf_url键存在（可能是从download_link复制）
                    if result.get('download_link') and not result.get('pdf_url'):
                        result['pdf_url'] = result['download_link']
                    
                    # 确保必需的URL字段存在
                    if not result.get('url'):
                        result['url'] = result.get('detail_url') or result.get('url', 'https://www.science.org')
                    
                    # 3. 数据库入库阶段
                    try:
                        # 打印完整的文章数据用于调试
                        print("\n--- 准备保存到数据库的文章数据 ---")
                        print(f"标题: {result.get('title')}")
                        print(f"DOI: {result.get('doi')}")
                        print(f"URL: {result.get('url')}")
                        print(f"PDF URL: {result.get('pdf_url')}")
                        print(f"下载路径: {result.get('download_path')}")
                        print(f"PDF MD5: {result.get('pdf_md5')}")
                        print(f"作者: {result.get('authors')}")
                        print(f"摘要: {result.get('abstract', '')[:50]}...")
                        print("-----------------------------------\n")
                        
                        # 确保必要字段存在
                        if not result.get('title'):
                            print("× 文章缺少标题，无法保存到数据库")
                            return
                            
                        if not result.get('url'):
                            print("× 文章缺少URL，无法保存到数据库")
                            return
                        
                        # 保存到数据库
                        from src.database_manager import DatabaseManager
                        db_manager = DatabaseManager()
                        saved = db_manager.save_articles_to_database([result])
                        if saved:
                            success_count += 1
                            print(f"√ 文章信息已成功保存到数据库")
                        else:
                            print(f"× 文章信息保存到数据库失败")
                    except Exception as e:
                        print(f"数据库保存异常: {str(e)}")
                except Exception as e:
                    print(f"PDF处理异常: {str(e)}")
            except Exception as e:
                print(f"处理异常: {str(e)}")
            
            print(f"第{current_idx}篇文章处理成功")
            print(f"进度: {current_idx}/{total_count}")
        
        # 使用回调函数逐条处理
        driver_manager.process_articles(unique_articles, callback=process_single_article)
        step_times['逐条处理文章'] = time.time() - t0
        
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
        print(f"下载完成！")
        print(f"成功下载: {success_count}个")
        print(f"下载失败: {len(unique_articles) - success_count}个")
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