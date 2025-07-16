#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索页性能测试脚本 - 详细分析每一步的耗时
"""

import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import ScienceConfig
from src.utils import create_driver
from src.link_collector import LinkCollector
from selenium.webdriver.common.by import By

def test_search_performance():
    """测试搜索页性能"""
    print("=" * 70)
    print("搜索页性能测试 - 详细分析")
    print("=" * 70)
    
    # 创建配置
    config = ScienceConfig()
    
    # 创建driver
    print("1. 创建driver...")
    driver_start = time.time()
    driver = create_driver(debug_port=config.CHROME_DEBUG_PORT)
    driver_time = time.time() - driver_start
    
    if not driver:
        print("创建driver失败")
        return
    
    print(f"[性能] Driver创建耗时: {driver_time:.3f}秒")
    
    try:
        # 访问Science搜索页面
        print("\n2. 访问搜索页面...")
        page_load_start = time.time()
        driver.get(config.SEARCH_URL)
        
        # 等待页面基本加载
        time.sleep(1)
        page_load_time = time.time() - page_load_start
        print(f"[性能] 页面加载耗时: {page_load_time:.3f}秒")
        
        # 测试链接收集性能
        print("\n3. 开始性能测试...")
        collector = LinkCollector(driver)
        
        collection_start = time.time()
        links = collector.collect_all_links()
        collection_time = time.time() - collection_start
        
        print(f"\n" + "=" * 70)
        print("性能测试结果总结")
        print("=" * 70)
        print(f"Driver创建: {driver_time:.3f}秒")
        print(f"页面加载: {page_load_time:.3f}秒")
        print(f"链接收集: {collection_time:.3f}秒")
        print(f"总耗时: {driver_time + page_load_time + collection_time:.3f}秒")
        print(f"收集到链接: {len(links)}个")
        print(f"平均每个链接耗时: {collection_time/len(links):.3f}秒" if links else "无链接")
        
        # 性能分析
        print(f"\n性能分析:")
        if driver_time > 2:
            print(f"⚠️  Driver创建较慢 ({driver_time:.3f}秒)，可能是网络或Chrome启动问题")
        if page_load_time > 3:
            print(f"⚠️  页面加载较慢 ({page_load_time:.3f}秒)，可能是网络或网站响应慢")
        if collection_time > 5:
            print(f"⚠️  链接收集较慢 ({collection_time:.3f}秒)，可能是DOM查询效率问题")
        
        # 显示前几个链接的标题
        if links:
            print(f"\n收集到的链接:")
            for i, link in enumerate(links[:3]):
                print(f"{i+1}. {link['title'][:60]}...")
        
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 不关闭driver，让用户手动关闭
        print("\n测试完成，driver保持打开状态")
        print("请手动关闭浏览器窗口")

def analyze_dom_performance():
    """分析DOM查询性能"""
    print("\n" + "=" * 70)
    print("DOM查询性能分析")
    print("=" * 70)
    
    config = ScienceConfig()
    driver = create_driver(debug_port=config.CHROME_DEBUG_PORT)
    
    if not driver:
        return
    
    try:
        driver.get(config.SEARCH_URL)
        time.sleep(2)
        
        # 测试不同的选择器性能
        selectors_to_test = [
            ".card.pb-3.mb-4.border-bottom",  # 当前使用的选择器
            ".card",  # 简化选择器
            "[class*='card']",  # 模糊匹配
            "article",  # 通用选择器
            "div[class*='border']"  # 另一个可能的模式
        ]
        
        print("测试不同选择器的性能:")
        for selector in selectors_to_test:
            start_time = time.time()
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            query_time = time.time() - start_time
            print(f"选择器 '{selector}': {len(elements)}个元素, 耗时: {query_time:.3f}秒")
        
        # 测试单个元素查询性能
        print("\n测试单个元素查询性能:")
        cards = driver.find_elements(By.CSS_SELECTOR, config.SELECTORS['search_cards'])
        if cards:
            card = cards[0]
            
            # 测试标题查询
            title_selectors = [
                ".card-header h2.article-title > a",
                "h2.article-title > a", 
                ".card-header a",
                "a[data-test='article-title']"
            ]
            
            for selector in title_selectors:
                start_time = time.time()
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    query_time = time.time() - start_time
                    print(f"标题选择器 '{selector}': 成功, 耗时: {query_time:.3f}秒")
                except:
                    query_time = time.time() - start_time
                    print(f"标题选择器 '{selector}': 失败, 耗时: {query_time:.3f}秒")
        
    except Exception as e:
        print(f"DOM分析异常: {e}")
    finally:
        print("\nDOM分析完成")

if __name__ == "__main__":
    try:
        test_search_performance()
        analyze_dom_performance()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试异常：{e}")
        import traceback
        traceback.print_exc() 