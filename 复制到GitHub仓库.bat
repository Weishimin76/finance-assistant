@echo off
chcp 65001
cls
echo ========================================
echo  复制文件到GitHub仓库
echo ========================================
echo.

echo 请告诉我GitHub仓库在哪里？
echo.
echo 常见位置：
echo 1. C:\Users\%USERNAME%\Documents\GitHub\finance-assistant
echo 2. C:\Users\%USERNAME%\文档\GitHub\finance-assistant  
echo 3. D:\finance-assistant
echo 4. 桌面
echo.

:: 尝试自动找到
set "TARGET="

if exist "%USERPROFILE%\Documents\GitHub\finance-assistant" (
    set "TARGET=%USERPROFILE%\Documents\GitHub\finance-assistant"
    goto found
)

if exist "%USERPROFILE%\文档\GitHub\finance-assistant" (
    set "TARGET=%USERPROFILE%\文档\GitHub\finance-assistant"
    goto found
)

if exist "C:\GitHub\finance-assistant" (
    set "TARGET=C:\GitHub\finance-assistant"
    goto found
)

if exist "%USERPROFILE%\Desktop\finance-assistant" (
    set "TARGET=%USERPROFILE%\Desktop\finance-assistant"
    goto found
)

:manual
cls
echo 自动搜索未找到，请手动输入路径
echo.
echo 如何找到路径：
echo 1. 打开GitHub Desktop
echo 2. 右键点击 finance-assistant 仓库
echo 3. 选择 "Open in Explorer"
echo 4. 复制地址栏的路径
echo.
set /p TARGET=请输入完整路径: 

if not exist "%TARGET%" (
    echo.
    echo 路径不存在，请重新输入
    pause
    goto manual
)

:found
echo.
echo ✅ 找到目标: %TARGET%
echo.
echo 源文件: C:\Users\Admin（无密码）\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a1a40f7fe1065215841a76c
echo.
echo 按任意键开始复制...
pause >nul

cls
echo 正在复制文件...
echo.

set "SOURCE=C:\Users\Admin（无密码）\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a1a40f7fe1065215841a76c"

copy /Y "%SOURCE%\*.py" "%TARGET%\" >nul 2>&1
copy /Y "%SOURCE%\*.txt" "%TARGET%\" >nul 2>&1
copy /Y "%SOURCE%\*.md" "%TARGET%\" >nul 2>&1
copy /Y "%SOURCE%\*.toml" "%TARGET%\" >nul 2>&1

echo ✅ 复制完成！
echo.
echo 下一步：
echo 1. 回到GitHub Desktop
echo 2. 在Summary框输入: Update to v7.0
echo 3. 点击 Commit to main
echo 4. 点击 Push origin
echo.
pause
