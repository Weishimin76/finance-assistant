@echo off
chcp 65001 >nul
echo ========================================
echo   跨境电商财务智能体 启动中...
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
pip install streamlit pandas openpyxl ollama requests plotly --quiet 2>nul

REM 检查 Ollama
echo [2/3] 检查 Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [警告] Ollama 未运行，AI问答功能将不可用
    echo        请在另一个终端运行: ollama serve
    echo.
) else (
    echo [OK] Ollama 已连接
)

REM 生成示例数据（如果不存在）
if not exist "data\sample_data" (
    echo [3/3] 生成示例数据...
    python generate_sample_data.py
) else (
    echo [3/3] 示例数据已存在
)

echo.
echo ========================================
echo   启动 Web 应用...
echo   浏览器访问: http://localhost:8501
echo   按 Ctrl+C 停止
echo ========================================
echo.

streamlit run app.py --server.port 8501 --server.headless true
