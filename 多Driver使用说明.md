# Science期刊爬虫 - 多Driver并发版本使用说明

## 项目结构

```
s_crawler/
├── src/
│   ├── __init__.py
│   ├── config.py          # 配置文件
│   ├── utils.py           # 工具函数
│   ├── link_collector.py  # 链接收集器
│   ├── pdf_processor.py   # PDF处理器
│   ├── driver_manager.py  # Driver管理器
│   └── download_manager.py # 下载管理器
├── science_crawler_main.py # 主程序
└── 多Driver使用说明.md     # 本文件
```

## 功能特点

1. **模块化设计**：代码拆分为多个模块，便于维护和扩展
2. **多Driver并发**：同时开启5个Chrome实例，真正并发处理
3. **人机验证处理**：自动检测并暂停等待用户手动处理
4. **异常重试**：自动重试失败的下载任务
5. **进度显示**：实时显示处理进度和统计信息

## 使用方法

### 1. 启动Chrome浏览器

首先需要启动Chrome浏览器并开启调试模式：

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

### 2. 运行爬虫

```bash
python science_crawler_main.py
```

## 配置说明

在 `src/config.py` 中可以修改以下配置：

```python
class ScienceConfig:
    # 基础配置
    SEARCH_URL = "https://www.science.org/action/doSearch?AllField=twist+angle&AfterYear=2010&BeforeYear=2025&queryID=26%2F8295040111"
    DOWNLOAD_DIR = "science_downloads"  # 下载目录
    MAX_COUNT = 20  # 最大抓取数量
    
    # 并发配置
    DRIVER_COUNT = 5  # 同时开启的driver数量
    DOWNLOAD_THREADS = 10  # PDF下载线程数
    
    # 时间配置
    SLEEP_TIME = 2  # 页面等待时间
    RETRY_COUNT = 1  # 重试次数
```

## 工作流程

1. **收集链接**：使用第一个driver收集所有详情页链接
2. **并发处理**：创建5个driver实例，并发处理文章获取PDF下载链接
3. **多线程下载**：使用requests多线程下载所有PDF文件

## 多Driver原理

- **真正并发**：每个driver是独立的Chrome实例，可以真正并发执行
- **任务分配**：将文章平均分配给各个driver处理
- **资源管理**：自动管理driver的创建和关闭

## 注意事项

1. **内存占用**：多开driver会占用较多内存，建议根据机器配置调整driver数量
2. **网络稳定**：确保网络连接稳定，避免频繁断线
3. **人机验证**：遇到验证码时会暂停，需要手动处理
4. **文件命名**：PDF文件以文章标题命名，特殊字符会被替换

## 故障排除

### 1. Driver创建失败
- 检查Chrome是否已启动并开启调试模式
- 确认端口9222未被占用
- 检查ChromeDriver版本是否与Chrome版本匹配

### 2. 下载失败
- 检查网络连接
- 确认cookies是否有效
- 查看是否遇到反爬限制

### 3. 内存不足
- 减少driver数量
- 减少并发下载线程数
- 关闭其他占用内存的程序

## 性能优化建议

1. **调整并发数**：根据机器性能调整driver数量和下载线程数
2. **优化等待时间**：根据网络情况调整页面等待时间
3. **分批处理**：对于大量文章，可以分批处理避免内存溢出 