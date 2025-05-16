# 图床转发 (Image-Forward)

一个基于Python Flask的图片合集管理和随机转发服务。

## 功能特点

- 管理界面，支持创建、查看、编辑和删除图片合集
- 支持上传本地图片和添加外部图片链接
- 通过特定URL随机返回合集中的图片（本地图片直接返回，外链HTTP重定向）
- 支持Docker部署

## 目录结构

```
image-forward/
│
├── app/                    # 应用代码
│   ├── routes/             # 路由模块
│   ├── storage/            # 存储管理
│   ├── auth/               # 认证模块
│   ├── static/             # 静态文件
│   └── templates/          # HTML模板
│
├── picture/                # 图片存储目录
├── config.py               # 配置文件
├── run.py                  # 应用入口
├── requirements.txt        # 依赖列表
├── Dockerfile              # Docker配置
├── docker-compose.yml      # Docker Compose配置
└── .env                    # 环境变量配置
```

## 快速开始

### 1. 环境配置

首先，创建并编辑`.env`文件设置管理员密码和其他配置：

```
# 管理员配置
ADMIN_PASSWORD=your_secure_password

# 其他可选配置
DEBUG=True
SECRET_KEY=your_secret_key
PORT=46000
```

### 2. 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动应用：

```bash
python run.py
```

### 3. Docker部署

使用Docker Compose启动服务：

```bash
docker-compose up -d
```

## 使用指南

### 访问地址

- 主页：`http://127.0.0.1:46000/`
- 管理界面：`http://127.0.0.1:46000/admin`
- 随机转发：`http://127.0.0.1:46000/合集名称`

### 管理流程

1. 访问管理界面并使用`.env`文件中设置的密码登录
2. 创建新的图片合集
3. 上传本地图片或添加外部图片链接
4. 通过随机转发URL测试功能

## 数据存储

- 所有图片和外链数据存储在项目运行目录下的`/picture`文件夹中
- 每个图片合集对应`/picture`下的一个子文件夹
- 合集下的本地图片直接存储在该子文件夹中
- 合集下的外部链接集中存储在子文件夹内一个与合集同名的`.txt`文件中