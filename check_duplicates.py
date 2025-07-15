#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查文章标题是否有重复
"""

def check_duplicates():
    """检查文章标题是否有重复"""
    
    # 从日志中提取的文章标题
    titles = [
        "In situ manipulation of van der Waals heterostructures for twistronics",
        "Mapping twist-tuned multiband topology in bilayer WSe2",
        "Ferromagnetism in magic-angle graphene",
        "Moiré photonics and optoelectronics",
        "Programming twist angle and strain profiles in 2D materials",
        "Time-reversal symmetry breaking superconductivity between twisted cuprate superconductors",
        "Direct visualization of magnetic domains and moiré magnetism in twisted 2D magnets",
        "Abnormal conductivity in low-angle twisted bilayer graphene",
        "Anomalous superconductivity in twisted MoTe2 nanojunctions",
        "A quantum ruler for orbital magnetism in moiré quantum matter"
    ]
    
    print(f"总文章数: {len(titles)}")
    print()
    
    # 检查重复
    duplicates = []
    seen = set()
    for title in titles:
        if title in seen:
            duplicates.append(title)
        else:
            seen.add(title)
    
    print(f"重复文章数: {len(duplicates)}")
    if duplicates:
        print(f"重复文章: {duplicates}")
    else:
        print("没有重复文章")
    
    print()
    print("所有文章标题:")
    for i, title in enumerate(titles, 1):
        print(f"{i:2d}. {title}")
    
    # 检查是否有相似标题
    print()
    print("检查相似标题:")
    for i, title1 in enumerate(titles):
        for j, title2 in enumerate(titles[i+1:], i+1):
            # 计算相似度（简单方法）
            words1 = set(title1.lower().split())
            words2 = set(title2.lower().split())
            similarity = len(words1.intersection(words2)) / len(words1.union(words2))
            if similarity > 0.5:  # 相似度超过50%
                print(f"相似度 {similarity:.2f}: '{title1}' vs '{title2}'")

if __name__ == "__main__":
    check_duplicates() 