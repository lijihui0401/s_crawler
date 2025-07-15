# Science爬虫使用指南

## 项目结构改进说明

### 原有问题
1. 多个文件分散，代码混乱
2. 使用多driver并发模式，复杂度高
3. 缺少数据库去重功能
4. 代码结构不统一

### 改进后的结构
```
src/
├── crawlers/
│   ├── nature_crawler.py    # Nature爬虫类（原有）
│   └── science_crawler.py   # Science爬虫类（新增，仿照nature）
├── models/
│   └── article.py          # 文章数据模型
└── utils/
    └── file_utils.py       # 文件工具类

main.py                     # Nature爬虫主程序（原有）
science_main.py            # Science爬虫主程序（新增）
database/
└── create_science_table.sql  # Science数据库表结构
```

## 使用方法

### 1. 创建数据库表
首先在MySQL中执行创建表的SQL：
```bash
mysql -u root -p article_t_a_db < database/create_science_table.sql
```

### 2. 基本使用

#### 抓取文章列表（不保存到数据库）
```bash
python science_main.py --start-url "https://www.science.org/action/doSearch?AllField=twist+angle&AfterYear=2010&BeforeYear=2025" --max-results 10
```

#### 抓取并保存到数据库（自动去重）
```bash
python science_main.py --start-url "YOUR_SEARCH_URL" --max-results 20 --save-to-db
```

#### 抓取并下载PDF
```bash
python science_main.py --start-url "YOUR_SEARCH_URL" --max-results 10 --download-pdfs --save-to-db
```

#### 使用已打开的浏览器
```bash
# 先启动Chrome调试模式
chrome --remote-debugging-port=9222

# 然后运行爬虫
python science_main.py --start-url "YOUR_SEARCH_URL" --use-existing-browser --max-results 10
```

### 3. 参数说明

- `--start-url`: Science搜索结果页URL（必需）
- `--max-results`: 最大抓取文章数量（默认10）
- `--save-to-db`: 保存到MySQL数据库
- `--download-pdfs`: 下载PDF文件
- `--use-existing-browser`: 使用已存在的浏览器
- `--headless`: 无头模式运行
- `--output`: JSON输出文件名（默认science_articles.json）
- `--download-dir`: PDF下载目录（默认science_downloads）

## 主要功能

### 1. 自动去重
- 数据库级别去重：通过DOI和标题进行查重
- 抓取时去重：如果启用`--save-to-db`，会在抓取时检查数据库避免重复

### 2. 信息提取
- 标题、作者、期刊信息
- DOI号
- 摘要（需要访问详情页）
- PDF链接

### 3. PDF下载
- 自动生成文件名
- 检查文件是否已存在
- 下载后更新数据库记录

## 与原多driver版本的区别

### 原版本（多driver并发）
- 复杂的driver管理
- 需要多个浏览器实例
- 代码分散在多个模块

### 新版本（单线程）
- 简单清晰的代码结构
- 一个浏览器实例
- 所有功能集中在一个类中
- 支持数据库去重
- 与Nature爬虫保持一致的风格

## 注意事项

1. **数据库配置**：默认使用本地MySQL，配置在`science_main.py`中：
   ```python
   db_config = {
       'host': 'localhost',
       'user': 'root',
       'password': '12345678',
       'database': 'article_t_a_db',
       'charset': 'utf8mb4'
   }
   ```

2. **网站反爬**：建议使用`--use-existing-browser`选项，手动登录后再运行爬虫

3. **速度控制**：代码中已加入随机延时，避免访问过快

## 后续优化建议

1. **配置文件**：将数据库配置移到单独的配置文件
2. **断点续爬**：保存爬取进度，支持中断后继续
3. **代理支持**：添加代理功能应对IP限制
4. **更多网站**：按照相同模式添加其他期刊网站的爬虫