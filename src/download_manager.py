import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import ScienceConfig
from .utils import sanitize_filename, download_file

class DownloadManager:
    """下载管理器，负责多线程下载PDF文件"""
    
    def __init__(self):
        self.config = ScienceConfig()
        self.config.create_download_dir()
    
    def download_all_pdfs(self, pdf_tasks, cookies, user_agent):
        """多线程下载所有PDF文件"""
        if not pdf_tasks:
            print("没有PDF下载任务")
            return []
        
        print(f"开始多线程下载{len(pdf_tasks)}个PDF文件...")
        
        successful_downloads = []
        failed_downloads = []
        
        with ThreadPoolExecutor(max_workers=self.config.DOWNLOAD_THREADS) as executor:
            # 提交所有下载任务
            future_to_task = {}
            
            for task in pdf_tasks:
                filename = sanitize_filename(task["title"]) + ".pdf"
                filepath = os.path.join(self.config.DOWNLOAD_DIR, filename)
                future = executor.submit(
                    download_file,
                    task["download_link"],
                    filepath,
                    30,  # timeout
                    3    # max_retries
                )
                future_to_task[future] = task
            
            # 收集结果
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success = future.result()
                    if success:
                        successful_downloads.append(task)
                    else:
                        failed_downloads.append(task)
                except Exception as e:
                    print(f"下载任务异常：{e}")
                    failed_downloads.append(task)
        
        # 输出统计信息
        print(f"\n下载完成！")
        print(f"成功下载: {len(successful_downloads)}个")
        print(f"下载失败: {len(failed_downloads)}个")
        
        if failed_downloads:
            print("\n下载失败的文件：")
            for task in failed_downloads:
                print(f"- {task['title']}")
        
        return successful_downloads
    
    def get_download_stats(self):
        """获取下载目录统计信息"""
        try:
            files = os.listdir(self.config.DOWNLOAD_DIR)
            pdf_files = [f for f in files if f.endswith('.pdf')]
            total_size = sum(
                os.path.getsize(os.path.join(self.config.DOWNLOAD_DIR, f)) 
                for f in pdf_files
            )
            
            return {
                'total_files': len(pdf_files),
                'total_size_mb': total_size / (1024 * 1024)
            }
        except Exception as e:
            print(f"获取下载统计信息失败：{e}")
            return {'total_files': 0, 'total_size_mb': 0} 