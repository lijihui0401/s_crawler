#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 测试优化后的爬虫速度
"""

import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import ScienceConfig
from src.utils import create_driver
from src.link_collector import LinkCollector

def test_collection_speed():
    """测试链接收集速度"""
    print("=" * 50)
    print("性能测试 - 链接收集速度")
    print("=" * 50)
    
    # 创建配置
    config = ScienceConfig()
    
    # 创建driver
    print("创建driver...")
    driver = create_driver(debug_port=config.CHROME_DEBUG_PORT)
    
    if not driver:
        print("创建driver失败")
        return
    
    try:
        # 访问Science搜索页面
        print("访问Science搜索页面...")
        start_time = time.time()
        driver.get(config.SEARCH_URL)
        load_time = time.time() - start_time
        print(f"页面加载时间: {load_time:.2f}秒")
        
        # 测试链接收集速度
        print("\n开始测试链接收集速度...")
        collector = LinkCollector(driver)
        
        start_time = time.time()
        links = collector.collect_all_links()
        collection_time = time.time() - start_time
        
        print(f"\n性能测试结果:")
        print(f"收集到链接数量: {len(links)}")
        print(f"总耗时: {collection_time:.2f}秒")
        print(f"平均每个链接耗时: {collection_time/len(links):.3f}秒" if links else "无链接")
        
        # 显示前几个链接的标题
        if links:
            print(f"\n前5个链接:")
            for i, link in enumerate(links[:5]):
                print(f"{i+1}. {link['title'][:50]}...")
        
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 不关闭driver，让用户手动关闭
        print("\n测试完成，driver保持打开状态")
        print("请手动关闭浏览器窗口")

if __name__ == "__main__":
    try:
        test_collection_speed()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试异常：{e}")
        import traceback
        traceback.print_exc() 