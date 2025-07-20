#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pdf_downloader.py

从数据库中读取 downloaded = 0 的 Science 文章记录，
拼接详情页 URL（https://www.science.org/doi/{doi}），
调用 PDFProcessor 下载 PDF 并更新下载状态。

使用：
    python pdf_downloader.py [--batch 20]
    # 每批 30 条，一共处理 100 条
python pdf_downloader.py --batch 30 --max 100
"""

import argparse
import os
import traceback
from typing import List, Dict

from src.driver_manager import DriverManager
from src.pdf_processor import PDFProcessor
from src.database_manager import DatabaseManager
from src.utils import calculate_file_md5


def parse_args():
    p = argparse.ArgumentParser(description="Download pending PDFs recorded in DB")
    p.add_argument("--batch", type=int, default=20, help="一次处理的记录数")
    p.add_argument("--max", type=int, default=None, help="最多处理多少条（None 表示全部）")
    return p.parse_args()


def build_article_dict(row: Dict) -> Dict:
    """根据数据库行构造 PDFProcessor 需要的 article_info"""
    url = row.get("url")
    if not url and row.get("doi"):
        url = f"https://www.science.org/doi/{row['doi']}"
    return {
        "title": row.get("title"),
        "url": url,
        "doi": row.get("doi"),
        "journal": row.get("journal"),
        "publication_date": row.get("publication_date"),
        "authors": row.get("authors", "").split(", ") if row.get("authors") else [],
    }


def main():
    args = parse_args()

    dbm = DatabaseManager()
    total_processed = 0

    dm = DriverManager()
    if not dm.create_driver():
        print("[pdf_downloader] 无法创建浏览器 driver，退出")
        return

    processor = PDFProcessor(dm.driver)

    while True:
        pending_rows: List[Dict] = dbm.fetch_pending_articles(limit=args.batch)
        if not pending_rows:
            print("[pdf_downloader] 没有待下载记录，任务结束")
            break

        for row in pending_rows:
            if args.max and total_processed >= args.max:
                break
            article_id = row["id"]
            try:
                article_info = build_article_dict(row)
                print(f"\n=== 开始下载 ID={article_id} DOI={row.get('doi')} ===")
                result = processor.process_article(article_info)
                if result and result.get("downloaded"):
                    pdf_path = result.get("download_path")
                    pdf_md5 = None
                    if pdf_path and os.path.exists(pdf_path):
                        pdf_md5 = calculate_file_md5(pdf_path)
                    dbm.update_download_status(article_id, True, pdf_path, pdf_md5, None)
                    print(f"[成功] ID={article_id} 下载完成")
                else:
                    dbm.update_download_status(article_id, False, last_error="下载失败或未找到链接")
                    print(f"[失败] ID={article_id} 下载失败")
            except Exception as e:
                print(f"[异常] ID={article_id} 处理出错: {e}")
                traceback.print_exc()
                dbm.update_download_status(article_id, False, last_error=str(e))
            total_processed += 1
            if args.max and total_processed >= args.max:
                break

        if args.max and total_processed >= args.max:
            print("[pdf_downloader] 达到 --max 限制，提前结束")
            break

    dm.close_driver()
    print(f"[pdf_downloader] 本次共处理 {total_processed} 条记录")


if __name__ == "__main__":
    main() 