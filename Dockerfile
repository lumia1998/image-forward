# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 46000

# 创建图片存储目录
VOLUME /app/picture

# 运行应用
CMD ["flask", "run", "--host=0.0.0.0", "--port=46000"]    