@echo off
chcp 65001
cls
echo ========================================
echo  跨境财务助手 - GitHub更新工具
echo ========================================
echo.

:: 设置路径
set "SOURCE_DIR=C:\Users\Admin（无密码）\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a1a40f7fe1065215841a76c"
set "TARGET_DIR=%USERPROFILE%\Documents\GitHub\finance-assistant"

echo 源文件路径: %SOURCE_DIR%
echo 目标路径: %TARGET_DIR%
echo.

:: 检查目标文件夹是否存在
if not exist "%TARGET_DIR%" (
    echo ❌ 错误: 找不到GitHub仓库文件夹
    echo.
    echo 请确认:
    echo 1. 已在GitHub Desktop中克隆了finance-assistant仓库
    echo 2. 克隆路径是默认的 Documents\GitHub\finance-assistant
    echo.
    pause
    exit /b 1
)

echo ✅ 找到GitHub仓库文件夹
echo.
echo 正在复制文件...
echo.

:: 复制所有Python文件
copy /Y "%SOURCE_DIR%\app_secure.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ app_secure.py) else (echo ✗ app_secure.py 失败)

copy /Y "%SOURCE_DIR%\parsers.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ parsers.py) else (echo ✗ parsers.py 失败)

copy /Y "%SOURCE_DIR%\reconciliation.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ reconciliation.py) else (echo ✗ reconciliation.py 失败)

copy /Y "%SOURCE_DIR%\reports.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ reports.py) else (echo ✗ reports.py 失败)

copy /Y "%SOURCE_DIR%\finance_llm.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ finance_llm.py) else (echo ✗ finance_llm.py 失败)

copy /Y "%SOURCE_DIR%\vat.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ vat.py) else (echo ✗ vat.py 失败)

copy /Y "%SOURCE_DIR%\expense_audit.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ expense_audit.py) else (echo ✗ expense_audit.py 失败)

copy /Y "%SOURCE_DIR%\exchange_rate.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ exchange_rate.py) else (echo ✗ exchange_rate.py 失败)

copy /Y "%SOURCE_DIR%\tax_policy.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ tax_policy.py) else (echo ✗ tax_policy.py 失败)

copy /Y "%SOURCE_DIR%\archive.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ archive.py) else (echo ✗ archive.py 失败)

copy /Y "%SOURCE_DIR%\config.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ config.py) else (echo ✗ config.py 失败)

copy /Y "%SOURCE_DIR%\requirements.txt" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ requirements.txt) else (echo ✗ requirements.txt 失败)

copy /Y "%SOURCE_DIR%\部署指南.md" "%TARGET_DIR%\" >nul 2>&1
echo ✓ 部署指南.md

echo.
echo ========================================
echo  文件复制完成！
echo ========================================
echo.
echo 下一步:
echo 1. 回到GitHub Desktop
echo 2. 在Summary框输入: Update to v7.0
echo 3. 点击 Commit to main
echo 4. 点击 Push origin
echo.
pause
