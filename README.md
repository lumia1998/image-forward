# Image Forward 图片转发服务

一个轻量级的图片合集管理和 302 重定向转发服务，基于 Python Flask 构建。

## ✨ 功能特点

- 📁 **图片合集管理** - 创建、编辑、删除图片合集
- 🖼️ **多种来源支持** - 支持上传本地图片和添加外部图片链接
- 🔀 **随机转发** - 通过 URL 随机返回合集中的图片（302 重定向）
- 🔗 **API 端点管理** - 管理自定义 API 转发端点
- 🐳 **Docker 支持** - 一键部署，数据持久化
- 🎨 **自定义背景** - 支持自定义背景图片和透明度

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 或 Docker

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python run.py
```

### Docker 部署（推荐）

```bash
# 使用 Docker Compose 启动
docker-compose up -d --build
```

## ⚙️ 配置说明

创建 `.env` 文件进行配置：

```env
# Flask 密钥
SECRET_KEY=your_secret_key

# 调试模式
DEBUG=False

# 服务配置
HOST=0.0.0.0
PORT=46000

# 管理员密码
ADMIN_PASSWORD=admin

# 图片存储目录
PICTURE_DIR=picture

# 背景透明度 (0.1-1.0)
BACKGROUND_OPACITY=0.25
```

## 📂 数据持久化

Docker 部署时，以下目录会被持久化：

| 宿主机路径 | 容器路径 | 说明 |
|-----------|---------|------|
| `./picture` | `/app/picture` | 图片存储目录 |
| `./background` | `/app/background` | 背景图片目录 |
| `./config.json` | `/app/config.json` | API 端点配置 |

## 🌐 访问地址

- **主页**: `http://localhost:46000/`
- **管理后台**: `http://localhost:46000/admin`
- **随机图片**: `http://localhost:46000/{合集名称}`
- **API 端点**: `http://localhost:46000/{端点名称}`

## 📖 使用指南

1. 访问管理后台 `/admin`，使用配置的密码登录
2. 创建图片合集或 API 端点
3. 上传本地图片或添加外部图片链接
4. 通过 `/{合集名称}` 或 `/{端点名称}` 访问随机图片

## 🔧 API 端点

所有 API 端点均使用 **302 重定向** 方式转发请求到目标 URL。

## 📁 目录结构

```
image-forward/
├── app/                    # 应用主目录
│   ├── routes/            # 路由模块
│   ├── templates/         # HTML 模板
│   ├── static/           # 静态文件
│   └── background/       # 背景图片
├── picture/               # 图片存储目录
├── config.json           # API 端点配置
├── config.py             # 应用配置
├── run.py                # 启动脚本
├── Dockerfile            # Docker 构建文件
├── docker-compose.yml    # Docker Compose 配置
└── requirements.txt      # Python 依赖
```

## 📄 License

MIT License
