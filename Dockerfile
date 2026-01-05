# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制项目代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/picture /app/background

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# 暴露端口
EXPOSE 46000

# 使用 Gunicorn 启动
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:46000", "run:app"]