@echo off
chcp 65001
cls
echo ========================================
echo  查找GitHub仓库文件夹
echo ========================================
echo.

echo 正在搜索 finance-assistant 文件夹...
echo.

:: 在常见位置搜索
set "FOUND=0"

:: 检查Documents\GitHub
if exist "%USERPROFILE%\Documents\GitHub\finance-assistant" (
    echo ✅ 找到: %USERPROFILE%\Documents\GitHub\finance-assistant
    set "FOUND=1"
    set "TARGET_DIR=%USERPROFILE%\Documents\GitHub\finance-assistant"
)

:: 检查文档\GitHub
if exist "%USERPROFILE%\文档\GitHub\finance-assistant" (
    echo ✅ 找到: %USERPROFILE%\文档\GitHub\finance-assistant
    set "FOUND=1"
    set "TARGET_DIR=%USERPROFILE%\文档\GitHub\finance-assistant"
)

:: 检查Desktop
if exist "%USERPROFILE%\Desktop\finance-assistant" (
    echo ✅ 找到: %USERPROFILE%\Desktop\finance-assistant
    set "FOUND=1"
    set "TARGET_DIR=%USERPROFILE%\Desktop\finance-assistant"
)

:: 检查Downloads
if exist "%USERPROFILE%\Downloads\finance-assistant" (
    echo ✅ 找到: %USERPROFILE%\Downloads\finance-assistant
    set "FOUND=1"
    set "TARGET_DIR=%USERPROFILE%\Downloads\finance-assistant"
)

if %FOUND%==0 (
    echo ❌ 未找到 finance-assistant 文件夹
    echo.
    echo 请手动找到GitHub仓库位置：
    echo 1. 打开GitHub Desktop
    echo 2. 右键点击 finance-assistant 仓库
    echo 3. 选择 "Open in Explorer" 或 "在资源管理器中打开"
    echo 4. 复制地址栏的路径
    echo.
    echo 或者直接在GitHub Desktop中提交：
    echo 1. 点击 Repository -> Open in Explorer
    echo 2. 把新文件复制进去
    echo 3. 回到GitHub Desktop提交
)

echo.
pause
