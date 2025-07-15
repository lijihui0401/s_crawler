@echo off
echo ===================================
echo Science期刊爬虫 - 单线程版本
echo ===================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 显示使用说明
echo 使用示例:
echo.
echo 1. 基本爬取（10篇文章）:
echo    python science_main.py --start-url "YOUR_URL" --max-results 10
echo.
echo 2. 爬取并保存到数据库:
echo    python science_main.py --start-url "YOUR_URL" --max-results 20 --save-to-db
echo.
echo 3. 爬取并下载PDF:
echo    python science_main.py --start-url "YOUR_URL" --max-results 10 --download-pdfs --save-to-db
echo.
echo 4. 使用已打开的浏览器:
echo    python science_main.py --start-url "YOUR_URL" --use-existing-browser --max-results 10
echo.
echo ===================================
echo.

REM 提示用户输入命令
set /p cmd="请输入完整命令 (或直接回车运行测试): "

if "%cmd%"=="" (
    echo 运行测试脚本...
    python test_science_single.py
) else (
    echo 执行命令: %cmd%
    %cmd%
)

echo.
pause