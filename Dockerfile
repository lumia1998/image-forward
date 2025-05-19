# 1. 基础镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 安装系统依赖 (如果需要，例如图像处理库)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#  && rm -rf /var/lib/apt/lists/*

# 4. 复制依赖文件并安装 Python 包
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn # 安装 Gunicorn

# 5. 复制项目代码到工作目录
COPY . .

# 6. 设置环境变量 (端口等，虽然也可以在 docker-compose.yml 中设置，但这里可以设默认值)
ENV FLASK_APP run.py
ENV FLASK_RUN_HOST 0.0.0.0
# Gunicorn 配置相关的环境变量可以在 docker-compose.yml 中定义或直接在 CMD 中指定

# 7. 暴露应用程序端口 (与 config.py 中的 PORT 一致)
EXPOSE 46000

# 8. 定义容器启动时执行的命令 (使用 Gunicorn)
#   -w: worker 进程数, 通常设为 (2 * CPU核心数) + 1
#   -b: 绑定地址和端口
#   run:app: Gunicorn 查找 Flask app 实例的路径 (run.py 文件中的 app 对象)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:46000", "run:app"]