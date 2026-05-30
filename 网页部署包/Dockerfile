FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 创建数据目录
RUN mkdir -p data

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "app_secure.py", "--server.port=8501", "--server.address=0.0.0.0"]
