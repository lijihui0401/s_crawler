# N-Crawler (Nature期刊爬虫) - 详细使用指南

## 📋 目录

- [快速开始](#快速开始)
- [基本用法](#基本用法)
- [高级用法](#高级用法)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.8+
- Chrome浏览器
- MySQL（可选，用于数据存储）

### 2. 安装项目

```bash
# 克隆项目
git clone https://github.com/yourusername/n_crawler.git
cd n_crawler

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 3. 首次运行

```bash
# 简单搜索测试
python main.py --query "machine learning" --max-results 3
```

## 📖 基本用法

### 搜索文章

```bash
# 基本搜索
python main.py --query "artificial intelligence"

# 指定结果数量
python main.py --query "quantum computing" --max-results 20

# 无头模式（不显示浏览器）
python main.py --query "graphene" --headless --max-results 10
```

### 下载PDF

```bash
# 搜索并下载PDF
python main.py --query "machine learning" --download-pdfs --max-results 5

# 指定下载目录
python main.py --query "deep learning" --download-pdfs --download-dir "my_papers"
```

### 保存结果

```bash
# 自定义输出文件名
python main.py --query "neural networks" --output "ai_papers.json"

# 同时下载PDF和保存信息
python main.py --query "computer vision" --download-pdfs --output "vision_papers.json"
```

## 🔧 高级用法

### 使用现有浏览器

当需要机构认证或登录时，推荐使用现有浏览器模式：

```bash
# 1. 启动Chrome调试模式
chrome.exe --remote-debugging-port=9222

# 2. 在浏览器中进行机构认证/登录

# 3. 运行爬虫
python main.py --query "your topic" --use-existing-browser --download-pdfs
```

### 从筛选结果开始

如果你已经在Nature网站手动筛选了结果：

```bash
# 复制筛选后的URL，然后运行
python main.py --start-url "https://www.nature.com/search?q=twist+angle&subject=chemistry" --max-results 50 --download-pdfs
```

### 保持浏览器打开

调试时保持浏览器窗口打开：

```bash
python main.py --query "test" --keep-browser
```

## ⚙️ 配置说明

### 修改配置文件

编辑 `config/config.json` 来调整爬虫行为：

```json
{
  "delays": {
    "page_load": 3,        // 页面加载等待时间
    "element_wait": 10,    // 元素等待时间
    "random_min": 1,       // 随机延迟最小值
    "random_max": 3        // 随机延迟最大值
  },
  "user_agents": [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
  ],
  "chrome_options": {
    "headless": false,
    "no_sandbox": true,
    "disable_dev_shm_usage": true
  }
}
```

### 数据库配置

在 `main.py` 中修改数据库连接信息：

```python
db_config = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database',
    'charset': 'utf8mb4'
}
```

## 🔍 使用场景示例

### 场景1：学术研究

```bash
# 搜索特定领域的最新研究
python main.py --query "Nature Physics quantum materials" --max-results 100 --download-pdfs --headless
```

### 场景2：文献综述

```bash
# 搜索多个相关关键词
python main.py --query "machine learning neural networks" --max-results 200 --download-pdfs
```

### 场景3：机构访问

```bash
# 使用机构认证访问受限内容
# 1. 启动调试模式Chrome
chrome.exe --remote-debugging-port=9222

# 2. 在浏览器中进行机构认证

# 3. 运行爬虫
python main.py --query "your research topic" --use-existing-browser --download-pdfs --max-results 50
```

### 场景4：批量下载

```bash
# 从筛选结果批量下载
python main.py --start-url "your_filtered_search_url" --max-results 500 --download-pdfs --headless
```

## ❓ 常见问题

### Q1: ChromeDriver错误

**问题**: `WebDriverException: Message: unknown error: cannot find Chrome binary`

**解决**:
1. 确保Chrome浏览器已安装
2. 程序会自动下载ChromeDriver
3. 如仍有问题，手动下载对应版本的ChromeDriver

### Q2: 网络超时

**问题**: `TimeoutException: Message: timeout`

**解决**:
1. 增加配置文件中的超时时间
2. 检查网络连接
3. 某些地区可能需要代理

### Q3: PDF下载失败

**问题**: 无法下载PDF文件

**解决**:
1. 检查是否有机构访问权限
2. 尝试使用 `--use-existing-browser` 参数
3. 查看日志文件中的具体错误

### Q4: 元素定位失败

**问题**: `NoSuchElementException`

**解决**:
1. Nature网站可能更新，需要调整CSS选择器
2. 查看日志文件获取详细错误信息
3. 尝试增加等待时间

### Q5: 内存不足

**问题**: 处理大量文章时内存不足

**解决**:
1. 减少 `--max-results` 数量
2. 分批处理
3. 使用 `--headless` 模式减少内存占用

## 💡 最佳实践

### 1. 合理设置参数

```bash
# 推荐：从小批量开始测试
python main.py --query "test" --max-results 5

# 确认无误后再大批量处理
python main.py --query "your topic" --max-results 100 --download-pdfs
```

### 2. 使用日志调试

```bash
# 查看详细日志
tail -f logs/main.log
tail -f logs/nature_crawler.log
```

### 3. 定期备份数据

```bash
# 备份重要文件
cp articles.json articles_backup_$(date +%Y%m%d).json
```

### 4. 遵守访问频率

- 程序已内置随机延迟
- 避免过于频繁的访问
- 建议在非高峰时段运行

### 5. 机构认证最佳实践

```bash
# 1. 启动调试模式Chrome
chrome.exe --remote-debugging-port=9222

# 2. 在浏览器中完成所有认证步骤

# 3. 运行爬虫（复用认证状态）
python main.py --query "your topic" --use-existing-browser --download-pdfs
```

## 📊 输出文件说明

### JSON文件结构

```json
[
  {
    "title": "文章标题",
    "url": "文章链接",
    "authors": ["作者1", "作者2"],
    "journal": "期刊名称",
    "abstract": "文章摘要",
    "doi": "10.1038/xxx",
    "publication_date": "2023-01-01T00:00:00",
    "keywords": ["关键词1", "关键词2"],
    "pdf_url": "PDF链接",
    "download_path": "本地PDF路径"
  }
]
```

### 日志文件

- `logs/main.log`: 主程序日志
- `logs/nature_crawler.log`: 爬虫详细日志

### 下载文件

- PDF文件保存在 `downloads/` 目录
- 文件名自动清理特殊字符
- 支持自定义下载目录

## 🔒 安全注意事项

1. **合法使用**: 遵守Nature网站使用条款
2. **版权保护**: 仅用于学术研究，不得商业使用
3. **数据安全**: 妥善保管下载的PDF文件
4. **访问控制**: 避免过于频繁的访问

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件获取详细错误信息
2. 检查网络连接和Chrome浏览器
3. 提交GitHub Issue
4. 参考故障排除部分

---

**注意**: 本工具仅供学术研究使用，请遵守相关法律法规和网站使用条款。 