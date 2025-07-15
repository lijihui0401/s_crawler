#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务分配逻辑
"""

def test_task_allocation():
    """测试任务分配逻辑"""
    
    # 模拟20篇文章
    articles = [f"文章{i+1}" for i in range(20)]
    driver_count = 5
    
    print(f"总文章数: {len(articles)}")
    print(f"Driver数量: {driver_count}")
    print()
    
    # 复制DriverManager中的分配逻辑
    tasks_per_driver = len(articles) // driver_count
    remainder = len(articles) % driver_count
    
    print(f"每个driver基础任务数: {tasks_per_driver}")
    print(f"剩余任务数: {remainder}")
    print()
    
    # 分配任务
    start_idx = 0
    driver_tasks = []
    all_assigned_articles = []
    
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
            all_assigned_articles.extend(assigned_articles)
            
            print(f"Driver {i+1}: {len(assigned_articles)}篇文章")
            print(f"  文章: {assigned_articles}")
        
        start_idx = end_idx
    
    print()
    print(f"分配结果统计:")
    print(f"总分配文章数: {len(all_assigned_articles)}")
    print(f"原始文章数: {len(articles)}")
    print(f"是否相等: {len(all_assigned_articles) == len(articles)}")
    
    # 检查重复
    duplicates = []
    seen = set()
    for article in all_assigned_articles:
        if article in seen:
            duplicates.append(article)
        else:
            seen.add(article)
    
    print(f"重复文章数: {len(duplicates)}")
    if duplicates:
        print(f"重复文章: {duplicates}")
    
    # 检查遗漏
    missing = set(articles) - set(all_assigned_articles)
    print(f"遗漏文章数: {len(missing)}")
    if missing:
        print(f"遗漏文章: {list(missing)}")
    
    print()
    print("详细分配情况:")
    for task in driver_tasks:
        print(f"Driver {task['driver_index']+1}: {len(task['articles'])}篇文章")
        for j, article in enumerate(task['articles']):
            print(f"  {j+1}. {article}")

if __name__ == "__main__":
    test_task_allocation() 