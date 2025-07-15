# 贡献指南

感谢您对Nature期刊爬虫项目的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告Bug

如果您发现了Bug，请：

1. 在GitHub Issues中搜索是否已有相关报告
2. 如果没有，请创建新的Issue
3. 提供详细的Bug描述，包括：
   - 操作系统和Python版本
   - 错误信息和日志
   - 重现步骤
   - 期望行为

### 功能请求

如果您有功能建议，请：

1. 在GitHub Issues中搜索是否已有相关请求
2. 如果没有，请创建新的Issue
3. 详细描述功能需求和使用场景

### 代码贡献

如果您想贡献代码，请：

1. Fork本项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建Pull Request

## 📋 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/n_crawler.git
cd n_crawler
```

### 2. 创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装开发依赖

```bash
pip install pytest black flake8 mypy
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_crawler.py

# 运行测试并显示覆盖率
pytest --cov=src
```

### 代码质量检查

```bash
# 代码格式化
black src/ main.py

# 代码检查
flake8 src/ main.py

# 类型检查
mypy src/ main.py
```

## 📝 代码规范

### Python代码风格

- 遵循PEP 8规范
- 使用4个空格缩进
- 行长度不超过88字符
- 使用类型注解

### 文档规范

- 所有函数和类都要有文档字符串
- 使用Google风格的文档字符串
- 重要功能要提供使用示例

### 提交信息规范

使用清晰的提交信息：

```
feat: 添加新功能
fix: 修复Bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

## 🏗️ 项目结构

```
n_crawler/
├── src/                    # 源代码
│   ├── crawlers/          # 爬虫模块
│   ├── models/            # 数据模型
│   └── utils/             # 工具函数
├── config/                # 配置文件
├── tests/                 # 测试文件
├── docs/                  # 文档
├── main.py               # 主程序
├── requirements.txt      # 依赖包
└── README.md            # 项目说明
```

## 🔧 开发指南

### 添加新功能

1. **创建功能分支**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **编写代码**
   - 遵循现有代码风格
   - 添加适当的注释和文档
   - 确保代码可读性

3. **添加测试**
   - 为新功能编写测试用例
   - 确保测试覆盖率

4. **更新文档**
   - 更新README.md（如果需要）
   - 更新USAGE.md（如果需要）
   - 添加代码注释

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   git push origin feature/new-feature
   ```

### 修复Bug

1. **创建修复分支**
   ```bash
   git checkout -b fix/bug-description
   ```

2. **修复问题**
   - 定位问题根源
   - 编写修复代码
   - 添加回归测试

3. **测试修复**
   - 运行相关测试
   - 手动验证修复效果

4. **提交修复**
   ```bash
   git add .
   git commit -m "fix: 修复Bug描述"
   git push origin fix/bug-description
   ```

## 📋 Pull Request指南

### 创建Pull Request

1. 确保代码通过所有测试
2. 更新相关文档
3. 提供清晰的PR描述
4. 关联相关Issue

### PR描述模板

```markdown
## 描述
简要描述此PR的更改

## 类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 测试相关

## 测试
- [ ] 已添加测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 已更新相关文档
- [ ] 已添加必要的注释
- [ ] 没有引入新的警告

## 相关Issue
Closes #123
```

## 🐛 调试指南

### 常见问题

1. **ChromeDriver问题**
   - 检查Chrome版本
   - 确认ChromeDriver版本匹配
   - 查看详细错误日志

2. **网络问题**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试使用代理

3. **依赖问题**
   - 更新pip：`pip install --upgrade pip`
   - 重新安装依赖：`pip install -r requirements.txt --force-reinstall`

### 日志调试

```bash
# 查看详细日志
tail -f logs/main.log
tail -f logs/nature_crawler.log

# 设置调试级别
export PYTHONPATH=.
python main.py --query "test" --max-results 1
```

## 📞 联系我们

如果您有任何问题或建议，请：

- 提交GitHub Issue
- 发送邮件至：[your-email@example.com]
- 参与项目讨论

## 📄 许可证

通过贡献代码，您同意您的贡献将在MIT许可证下发布。

---

感谢您的贡献！🎉 