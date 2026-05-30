@echo off
chcp 65001
cls
echo ========================================
echo  复制文件到GitHub仓库
echo ========================================
echo.

set "SOURCE=C:\Users\Admin（无密码）\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a1a40f7fe1065215841a76c"

echo 正在搜索GitHub仓库位置...
echo.

:: 搜索常见位置
if exist "%USERPROFILE%\Documents\GitHub\finance-assistant" (
    set "TARGET=%USERPROFILE%\Documents\GitHub\finance-assistant"
    echo 找到: %USERPROFILE%\Documents\GitHub\finance-assistant
    goto copy_files
)

if exist "%USERPROFILE%\文档\GitHub\finance-assistant" (
    set "TARGET=%USERPROFILE%\文档\GitHub\finance-assistant"
    echo 找到: %USERPROFILE%\文档\GitHub\finance-assistant
    goto copy_files
)

if exist "D:\GitHub\finance-assistant" (
    set "TARGET=D:\GitHub\finance-assistant"
    echo 找到: D:\GitHub\finance-assistant
    goto copy_files
)

echo 未找到GitHub仓库，请手动复制
echo.
echo 源文件位置:
echo %SOURCE%
echo.
echo 操作步骤:
echo 1. 打开GitHub Desktop
echo 2. 右键点击 finance-assistant 仓库
echo 3. 选择 "Open in Explorer"
echo 4. 将上述源文件夹中的文件复制进去
echo.
pause
exit /b 1

:copy_files
echo.
echo 目标位置: %TARGET%
echo.
echo 正在复制文件...
echo.

copy /Y "%SOURCE%\app_secure.py" "%TARGET%\" >nul 2>&1 && echo ✓ app_secure.py
copy /Y "%SOURCE%\parsers.py" "%TARGET%\" >nul 2>&1 && echo ✓ parsers.py
copy /Y "%SOURCE%\reconciliation.py" "%TARGET%\" >nul 2>&1 && echo ✓ reconciliation.py
copy /Y "%SOURCE%\reports.py" "%TARGET%\" >nul 2>&1 && echo ✓ reports.py
copy /Y "%SOURCE%\finance_llm.py" "%TARGET%\" >nul 2>&1 && echo ✓ finance_llm.py
copy /Y "%SOURCE%\vat.py" "%TARGET%\" >nul 2>&1 && echo ✓ vat.py
copy /Y "%SOURCE%\expense_audit.py" "%TARGET%\" >nul 2>&1 && echo ✓ expense_audit.py
copy /Y "%SOURCE%\exchange_rate.py" "%TARGET%\" >nul 2>&1 && echo ✓ exchange_rate.py
copy /Y "%SOURCE%\tax_policy.py" "%TARGET%\" >nul 2>&1 && echo ✓ tax_policy.py
copy /Y "%SOURCE%\archive.py" "%TARGET%\" >nul 2>&1 && echo ✓ archive.py
copy /Y "%SOURCE%\config.py" "%TARGET%\" >nul 2>&1 && echo ✓ config.py
copy /Y "%SOURCE%\requirements.txt" "%TARGET%\" >nul 2>&1 && echo ✓ requirements.txt

echo.
echo ========================================
echo  复制完成！
echo ========================================
echo.
echo 下一步操作:
echo 1. 打开 GitHub Desktop
echo 2. 在左侧可以看到文件变更
echo 3. 在 Summary 框输入: Update to v7.0
echo 4. 点击 "Commit to main"
echo 5. 点击 "Push origin"
echo.
echo 完成后访问:
echo https://finance-assistant-2ajmubkqwgnxhwxpootznl.streamlit.app/
echo.
pause
