@echo off
chcp 65001 >nul
title 跨境财务助手Pro
cls
echo.
echo  ========================================
echo        跨境财务助手 Pro v5.0
echo        正在启动，请稍候...
echo  ========================================
echo.

cd /d "%~dp0"
python -m streamlit run app_secure.py --server.headless true --browser.gatherUsageStats false --server.port 8501

if errorlevel 1 (
    echo.
    echo  启动失败，请检查Python环境
    echo.
    pause
)
