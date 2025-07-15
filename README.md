# N-Crawler (Nature期刊爬虫)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0+-green.svg)](https://selenium-python.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于Selenium的Nature期刊智能爬虫，支持文章搜索、元数据提取、PDF下载和数据库存储。

## ✨ 功能特性

- 🔍 **智能搜索**: 支持关键词搜索Nature期刊文章
- 📄 **PDF下载**: 自动下载文章PDF文件到本地
- 🗄️ **数据库存储**: 支持MySQL数据库存储，自动查重
- 📊 **元数据提取**: 提取标题、作者、摘要、DOI、关键词等完整信息
- 🤖 **模拟用户**: 使用Selenium模拟真实用户行为
- 🎯 **反检测**: 随机延迟、用户代理轮换等反检测机制
- 📝 **详细日志**: 完整的日志记录和错误处理
- 🌐 **多模式支持**: 支持直接搜索、第三方镜像站点、现有浏览器连接

## 📋 项目结构

```
n_crawler/
├── src/
│   ├── crawlers/
│   │   └── nature_crawler.py    # 主要爬虫类
│   ├── utils/
│   │   └── file_utils.py        # 文件处理工具
│   └── models/
│       └── article.py           # 文章数据模型
├── config/
│   └── config.json              # 配置文件
├── downloads/                   # PDF下载目录
├── logs/                        # 日志文件目录
├── main.py                      # 主程序
├── requirements.txt             # 依赖包
├── .gitignore                   # Git忽略文件
└── README.md                    # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Chrome浏览器
- MySQL数据库（可选）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/n_crawler.git
cd n_crawler
```

2. **创建虚拟环境**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置数据库（可选）**
```bash
# 创建数据库和表
mysql -u root -p
CREATE DATABASE article_t_a_db;
USE article_t_a_db;

CREATE TABLE nature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doi VARCHAR(255),
    title TEXT,
    authors TEXT,
    journal VARCHAR(255),
    abstract TEXT,
    keywords TEXT,
    publication_date DATETIME,
    url VARCHAR(500),
    pdf_url VARCHAR(500),
    download_path VARCHAR(500),
    original_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📖 使用方法

### 基本搜索

```bash
# 搜索文章（仅获取信息，不下载PDF）
python main.py --query "machine learning" --max-results 5
```

### 搜索并下载PDF

```bash
# 搜索文章并下载PDF文件
python main.py --query "artificial intelligence" --max-results 10 --download-pdfs
```

### 无头模式运行

```bash
# 无头模式运行（不显示浏览器窗口）
python main.py --query "quantum computing" --headless --download-pdfs
```

### 使用现有浏览器

```bash
# 连接到已打开的Chrome浏览器（需要先启动调试模式）
python main.py --query "graphene" --use-existing-browser --download-pdfs
```

### 从指定URL开始爬取

```bash
# 从手动筛选后的结果页开始爬取
python main.py --start-url "https://www.nature.com/search?q=twist+angle&subject=chemistry" --max-results 20 --download-pdfs
```

### 自定义输出文件

```bash
# 指定输出文件名
python main.py --query "neural networks" --output "ai_papers.json"
```

## 🔧 命令行参数

| 参数 | 简写 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--query` | `-q` | ❌ | - | 搜索关键词 |
| `--start-url` | - | ❌ | - | 手动筛选后的结果页URL |
| `--max-results` | `-m` | ❌ | 10 | 最大结果数量 |
| `--headless` | - | ❌ | False | 无头模式运行 |
| `--download-pdfs` | - | ❌ | False | 下载PDF文件 |
| `--use-existing-browser` | - | ❌ | False | 使用已存在的浏览器 |
| `--keep-browser` | - | ❌ | False | 保持浏览器打开状态 |
| `--output` | `-o` | ❌ | articles.json | 输出文件名 |
| `--download-dir` | - | ❌ | downloads | PDF下载目录 |

**注意**: 必须提供 `--query` 或 `--start-url` 其中之一。

## 📊 输出格式

### JSON文件格式

程序会生成JSON文件，包含完整的文章信息：

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

### 数据库存储

如果配置了MySQL数据库，文章信息会自动存储到数据库中，支持：
- 自动查重（基于DOI和标题）
- 完整元数据存储
- 下载路径记录

## ⚙️ 配置说明

### 配置文件 (config/config.json)

```json
{
  "delays": {
    "page_load": 3,
    "element_wait": 10,
    "random_min": 1,
    "random_max": 3
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

## 🔍 使用示例

### 示例1：搜索机器学习相关文章

```bash
python main.py --query "machine learning" --max-results 50 --download-pdfs --headless
```

### 示例2：搜索特定期刊的文章

```bash
python main.py --query "Nature Physics graphene" --max-results 20 --download-pdfs
```

### 示例3：使用现有浏览器（推荐用于机构认证）

```bash
# 1. 启动Chrome调试模式
chrome.exe --remote-debugging-port=9222

# 2. 在浏览器中进行机构认证

# 3. 运行爬虫
python main.py --query "quantum computing" --use-existing-browser --download-pdfs
```

### 示例4：从筛选结果开始爬取

```bash
# 1. 在Nature网站手动搜索并筛选
# 2. 复制结果页URL
# 3. 运行爬虫
python main.py --start-url "https://www.nature.com/search?q=twist+angle&subject=chemistry" --max-results 100 --download-pdfs
```

## 🛠️ 故障排除

### 常见问题

1. **ChromeDriver错误**
   - 确保Chrome浏览器已安装
   - 程序会自动下载ChromeDriver
   - 如遇问题，手动下载对应版本的ChromeDriver

2. **网络超时**
   - 增加配置文件中的超时时间
   - 检查网络连接
   - 某些地区可能需要代理

3. **元素定位失败**
   - Nature网站可能更新，需要调整CSS选择器
   - 查看日志文件获取详细错误信息

4. **PDF下载失败**
   - 检查是否有机构访问权限
   - 尝试使用 `--use-existing-browser` 参数
   - 查看日志文件中的具体错误

### 日志文件

程序会在 `logs/` 目录下生成详细的日志文件：
- `main.log`: 主程序日志
- `nature_crawler.log`: 爬虫详细日志

## 📝 开发说明

### 项目架构

- **src/crawlers/**: 爬虫核心逻辑
- **src/models/**: 数据模型定义
- **src/utils/**: 工具函数
- **config/**: 配置文件
- **main.py**: 主程序入口

### 扩展功能

1. **添加新的爬虫类**
   - 在 `src/crawlers/` 目录下创建新的爬虫类
   - 继承基础爬虫类或实现标准接口

2. **添加新的数据模型**
   - 在 `src/models/` 目录下创建新的模型类
   - 实现 `to_dict()` 方法

3. **添加新的工具函数**
   - 在 `src/utils/` 目录下添加工具函数
   - 保持代码模块化和可复用性

## ⚠️ 注意事项

1. **合法使用**: 请确保遵守Nature网站的使用条款和版权规定
2. **访问频率**: 程序已内置随机延迟，避免过于频繁的访问
3. **网络环境**: 确保网络连接稳定，某些地区可能需要代理
4. **机构认证**: 某些文章需要机构认证，建议使用现有浏览器模式
5. **数据备份**: 定期备份重要的搜索结果和下载文件

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至：[your-email@example.com]

---

**免责声明**: 本项目仅用于学术研究目的，使用者需自行承担使用风险，并遵守相关法律法规。 