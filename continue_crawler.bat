@echo off
echo 正在删除验证码信号文件，让爬虫继续运行...
if exist captcha_signal.txt (
    del captcha_signal.txt
    echo 信号文件已删除，爬虫将继续运行！
) else (
    echo 未找到信号文件，可能已经删除或不需要。
)
pause 