@echo off
chcp 65001
cls
echo ========================================
echo  AI跨境财务管理平台 v9.1 - GitHub部署工具
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
echo 正在复制 v9.1 文件...
echo.

:: 复制所有核心Python文件（v9.1版本）
copy /Y "%SOURCE_DIR%\app.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ app.py - 主应用) else (echo ✗ app.py 失败)

copy /Y "%SOURCE_DIR%\ai_engine.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ ai_engine.py - AI引擎) else (echo ✗ ai_engine.py 失败)

copy /Y "%SOURCE_DIR%\database.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ database.py - 数据库) else (echo ✗ database.py 失败)

copy /Y "%SOURCE_DIR%\parsers.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ parsers.py - 文件解析) else (echo ✗ parsers.py 失败)

copy /Y "%SOURCE_DIR%\financial_knowledge.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ financial_knowledge.py - 知识库) else (echo ✗ financial_knowledge.py 失败)

copy /Y "%SOURCE_DIR%\realtime_data.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ realtime_data.py - 实时数据) else (echo ✗ realtime_data.py 失败)

copy /Y "%SOURCE_DIR%\platform_fees.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ platform_fees.py - 平台费率) else (echo ✗ platform_fees.py 失败)

copy /Y "%SOURCE_DIR%\report_generator.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ report_generator.py - 报表生成) else (echo ✗ report_generator.py 失败)

copy /Y "%SOURCE_DIR%\exchange_rate.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ exchange_rate.py - 汇率) else (echo ✗ exchange_rate.py 失败)

copy /Y "%SOURCE_DIR%\vat.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ vat.py - VAT计算) else (echo ✗ vat.py 失败)

copy /Y "%SOURCE_DIR%\tax_policy.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ tax_policy.py - 税务政策) else (echo ✗ tax_policy.py 失败)

copy /Y "%SOURCE_DIR%\config.py" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ config.py - 配置) else (echo ✗ config.py 失败)

copy /Y "%SOURCE_DIR%\requirements.txt" "%TARGET_DIR%\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ requirements.txt - 依赖) else (echo ✗ requirements.txt 失败)

:: 复制Streamlit配置
copy /Y "%SOURCE_DIR%\.streamlit\config.toml" "%TARGET_DIR%\.streamlit\" >nul 2>&1
if %errorlevel% == 0 (echo ✓ .streamlit/config.toml) else (echo ✗ config.toml 失败)

:: 复制部署指南
copy /Y "%SOURCE_DIR%\部署指南.md" "%TARGET_DIR%\" >nul 2>&1
echo ✓ 部署指南.md

echo.
echo ========================================
echo  文件复制完成！
echo ========================================
echo.
echo 下一步操作:
echo 1. 打开 GitHub Desktop
echo 2. 在 Summary 框输入: "Update to v9.1 - 全面升级版"
echo 3. 点击 Commit to main
echo 4. 点击 Push origin
echo.
echo 然后访问 Streamlit Cloud 部署:
echo https://share.streamlit.io/deploy
echo.
pause
