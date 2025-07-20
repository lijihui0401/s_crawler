#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
collect_meta.py

一次性抓取 Science 搜索结果页中的论文元数据（标题、DOI、作者、期刊、发布日期、详情页 URL），
并写入数据库，字段 downloaded 默认 0。该脚本不下载 PDF，只负责元数据采集。

使用方法：
    python collect_meta.py [--max N] [--query SEARCH_URL]

如果不提供 --query，则使用 config.ScienceConfig.SEARCH_URL。
# 默认配置
python collect_meta.py

# 指定最大 500 条、改用自定义搜索 URL
python collect_meta.py --max 500 --query "https://www.science.org/action/doSearch?AllField=quantum"
"""

import argparse
import sys
from typing import List, Dict

from src.driver_manager import DriverManager
from src.link_collector import LinkCollector
from src.database_manager import DatabaseManager
from src.config import ScienceConfig


def parse_args():
    parser = argparse.ArgumentParser(description="Collect metadata from Science search pages")
    parser.add_argument("--max", type=int, default=None, help="Maximum records to collect (override config.MAX_COUNT)")
    parser.add_argument("--query", type=str, default=None, help="Search url to start with")
    return parser.parse_args()


def main():
    args = parse_args()

    # Override config if CLI provides values
    if args.max:
        ScienceConfig.MAX_COUNT = args.max
    if args.query:
        ScienceConfig.SEARCH_URL = args.query

    # Create driver
    dm = DriverManager()
    if not dm.create_driver():
        print("[collect_meta] 无法创建浏览器 driver，退出")
        sys.exit(1)

    # 打开搜索页
    dm.driver.get(ScienceConfig.SEARCH_URL)

    collector = LinkCollector(dm.driver)
    articles: List[Dict] = collector.collect_all_links()
    print(f"[collect_meta] 共采集到 {len(articles)} 条元数据")

    # 入库
    if articles:
        dbm = DatabaseManager()
        for art in articles:
            art["downloaded"] = 0
            art["dl_attempts"] = 0
        dbm.save_articles_to_database(articles)
    else:
        print("[collect_meta] 未采集到任何新文章")

    dm.close_driver()


if __name__ == "__main__":
    main() 