@echo off
echo 正在启动5个Chrome浏览器...

echo 启动浏览器1 (端口9222) - 用于收集链接...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug_1"

echo 启动浏览器2 (端口9223) - 用于并发处理...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --user-data-dir="C:\temp\chrome_debug_2"

echo 启动浏览器3 (端口9224) - 用于并发处理...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9224 --user-data-dir="C:\temp\chrome_debug_3"

echo 启动浏览器4 (端口9225) - 用于并发处理...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9225 --user-data-dir="C:\temp\chrome_debug_4"

echo 启动浏览器5 (端口9226) - 用于并发处理...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9226 --user-data-dir="C:\temp\chrome_debug_5"

echo.
echo 所有浏览器启动完成！
echo 请在每个浏览器中登录Science网站，然后运行: python science_crawler_main.py
echo.
pause 