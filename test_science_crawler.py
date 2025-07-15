#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Science期刊爬虫测试版本
用于验证多driver功能是否正常工作
"""

import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config():
    """测试配置模块"""
    print("测试配置模块...")
    try:
        from src.config import ScienceConfig
        config = ScienceConfig()
        print(f"✓ 配置加载成功")
        print(f"  - 下载目录: {config.DOWNLOAD_DIR}")
        print(f"  - Driver数量: {config.DRIVER_COUNT}")
        print(f"  - 下载线程数: {config.DOWNLOAD_THREADS}")
        return True
    except Exception as e:
        print(f"✗ 配置模块测试失败: {e}")
        return False

def test_utils():
    """测试工具函数"""
    print("\n测试工具函数...")
    try:
        from src.utils import sanitize_filename, create_driver
        from src.config import ScienceConfig
        
        # 测试文件名清理
        test_filename = "Test: File/Name*with?special<characters>"
        cleaned = sanitize_filename(test_filename)
        print(f"✓ 文件名清理: '{test_filename}' -> '{cleaned}'")
        
        # 测试driver创建（不实际创建）
        print("✓ 工具函数加载成功")
        return True
    except Exception as e:
        print(f"✗ 工具函数测试失败: {e}")
        return False

def test_modules():
    """测试所有模块导入"""
    print("\n测试模块导入...")
    modules = [
        'src.link_collector',
        'src.pdf_processor', 
        'src.driver_manager',
        'src.download_manager'
    ]
    
    success_count = 0
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"✗ {module_name} 导入失败: {e}")
    
    return success_count == len(modules)

def test_driver_creation():
    """测试driver创建（不实际创建）"""
    print("\n测试driver创建逻辑...")
    try:
        from src.driver_manager import DriverManager
        from src.config import ScienceConfig
        
        config = ScienceConfig()
        driver_manager = DriverManager(use_existing_browser=True)
        
        print(f"✓ Driver管理器创建成功")
        print(f"  - 配置的driver数量: {config.DRIVER_COUNT}")
        print(f"  - 使用现有浏览器: {driver_manager.use_existing_browser}")
        
        return True
    except Exception as e:
        print(f"✗ Driver创建测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("Science期刊爬虫 - 模块测试")
    print("=" * 60)
    
    tests = [
        test_config,
        test_utils,
        test_modules,
        test_driver_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！可以运行主程序")
        print("\n下一步:")
        print("1. 启动Chrome浏览器: chrome.exe --remote-debugging-port=9222")
        print("2. 运行主程序: python science_crawler_main.py")
    else:
        print("✗ 部分测试失败，请检查代码")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 