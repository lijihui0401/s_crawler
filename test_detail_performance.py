#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试详情页处理性能，详细统计每个步骤的耗时
"""
import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import ScienceConfig
from src.utils import create_driver
from src.pdf_processor import PDFProcessor

from selenium.webdriver.common.by import By


def test_detail_performance():
    print("=" * 60)
    print("详情页处理性能测试 - 详细分析")
    print("=" * 60)
    
    # 1. 选取一个真实的详情页URL（可手动替换）
    test_url = "https://www.science.org/doi/10.1126/science.abl8371"  # 请替换为你想测试的详情页
    
    # 2. 创建driver
    config = ScienceConfig()
    print("创建driver...")
    driver = create_driver(debug_port=config.CHROME_DEBUG_PORT)
    if not driver:
        print("创建driver失败")
        return
    
    processor = PDFProcessor(driver)
    
    # 3. 统计各步骤耗时
    step_times = {}
    total_start = time.time()
    print(f"\n加载详情页: {test_url}")
    t0 = time.time()
    driver.get(test_url)
    step_times['加载详情页'] = time.time() - t0
    
    # 页面加载等待
    t0 = time.time()
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except:
        print("页面加载超时，继续处理...")
    step_times['等待页面加载'] = time.time() - t0

    # 检查页面元素（只检测详情页目标元素：标题或PDF按钮）
    t0 = time.time()
    try:
        # 详情页目标元素：标题或PDF按钮
        driver.find_element(By.CSS_SELECTOR, "h1.article-title, i.icon-pdf")
        print("页面目标元素已加载")
    except Exception as e:
        print(f"页面目标元素未找到: {e}")
        raise
    step_times['页面元素检测'] = time.time() - t0

    # 提取摘要
    t0 = time.time()
    details = {}
    try:
        details = processor._extract_article_details()
    except Exception as e:
        print(f"摘要提取异常: {e}")
        raise
    step_times['提取摘要/关键词'] = time.time() - t0

    # 查找PDF按钮
    t0 = time.time()
    pdf_page_url = None
    try:
        pdf_page_url = processor._find_pdf_page_url()
        if not pdf_page_url:
            raise Exception("未找到PDF按钮")
    except Exception as e:
        print(f"查找PDF按钮异常: {e}")
        raise
    step_times['查找PDF按钮'] = time.time() - t0

    # 跳转到PDF页面
    t0 = time.time()
    if pdf_page_url:
        driver.get(pdf_page_url)
    step_times['加载PDF页面'] = time.time() - t0

    # 检查PDF页面元素（只检测下载按钮）
    t0 = time.time()
    try:
        driver.find_element(By.CSS_SELECTOR, "#app-navbar > div.btn-group.navbar-right > div.grouped.right > a > span, span.icon.material-icons")
        print("PDF页面下载按钮已加载")
    except Exception as e:
        print(f"PDF页面下载按钮未找到: {e}")
        raise
    step_times['PDF页面元素检测'] = time.time() - t0

    # 获取PDF下载链接
    t0 = time.time()
    download_link = None
    try:
        download_link = processor._get_pdf_download_link()
        if not download_link:
            raise Exception("未找到下载链接")
    except Exception as e:
        print(f"查找下载链接异常: {e}")
        raise
    step_times['查找下载链接'] = time.time() - t0
    
    total_time = time.time() - total_start
    print("\n" + "=" * 60)
    print("详情页各步骤耗时统计")
    print("=" * 60)
    for k, v in step_times.items():
        print(f"{k:<16}: {v:.3f} 秒 ({v/total_time*100:.1f}%)")
    print(f"总耗时{'':<10}: {total_time:.3f} 秒 (100%)")
    print("=" * 60)
    print(f"\n摘要: {details.get('abstract', '')[:100]}...")
    print(f"关键词: {details.get('keywords', [])}")
    print(f"PDF页面: {pdf_page_url}")
    print(f"下载链接: {download_link}")
    print("\n测试完成，driver保持打开状态，请手动关闭浏览器窗口")

if __name__ == "__main__":
    test_detail_performance() 