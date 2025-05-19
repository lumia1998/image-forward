# 图床转发 (Image-Forward)

一个基于Python Flask的图片合集管理和随机转发服务。

## 功能特点

- 管理界面，支持创建、查看、编辑和删除图片合集
- 支持上传本地图片和添加外部图片链接
- 通过特定URL随机返回合集中的图片（本地图片直接返回，外链HTTP重定向）
- 支持Docker部署
- 统一的背景图片和可配置的透明度

## 目录结构

```
image-forward/
│
├── app/                    # 应用代码
│   ├── routes/             # 路由模块
│   ├── storage/            # 存储管理
│   ├── auth/               # 认证模块
│   ├── static/             # 静态文件
│   ├── background/         # 存放背景图片
│   └── templates/          # HTML模板
│
├── picture/                # 图片存储目录 (通过Docker Volume持久化)
├── docs/                   # 文档目录 (例如: project_plan.md)
├── config.py               # 主要配置文件，包含默认设置
├── run.py                  # 应用入口
├── requirements.txt        # 依赖列表
├── Dockerfile              # Docker配置
├── docker-compose.yml      # Docker Compose配置
└── .env                    # (可选) 环境变量配置文件，用于覆盖config.py中的设置
```

## 快速开始

### 1. 环境配置

应用的配置主要通过项目根目录下的 `config.py` 文件进行管理。该文件包含了所有配置项的默认值。

**可选配置覆盖：**

您可以通过以下方式覆盖 `config.py` 中的默认设置：

*   **使用 `.env` 文件**：在项目根目录下创建一个名为 `.env` 的文件。此文件中的环境变量（例如 `ADMIN_PASSWORD=mysecret` 或 `APP_NAME="我的图床"`）将在应用启动时加载，并覆盖 `config.py` 中的相应默认值。
    ```env
    # .env 示例
    ADMIN_PASSWORD=your_secure_password
    APP_NAME=我的自定义图床名称
    DEBUG=True
    # SECRET_KEY=your_very_secret_key_for_production # 强烈建议在生产环境中设置此项
    # PORT=5000
    ```

*   **Docker 用户映射自定义 `config.py`**：如果您使用 Docker 部署，可以通过 `docker-compose.yml` 文件中的 `volumes` 指令，将宿主机上的自定义 `config.py` 文件映射到容器内的 `/app/config.py`，从而完全控制配置。详见下面的 "Docker部署" 部分。

**重要配置项说明：**

*   `ADMIN_PASSWORD`: 管理员登录密码。
*   `APP_NAME`: 应用显示的名称。
*   `BACKGROUND_IMAGE_PATH`: 统一的背景图片文件名（应存放于 `app/background/` 目录）。
*   `BACKGROUND_OPACITY`: 背景图片的透明度（0.1 到 1.0）。
*   `SECRET_KEY`: Flask 应用的密钥，用于会话管理等，**在生产环境中务必设置为一个复杂且唯一的字符串**。
*   `DEBUG`: 是否开启调试模式。生产环境建议设为 `False`。
*   `PORT`: 应用运行的端口。

**注意**：通过管理界面进行的配置更改（如应用名称、背景图片、透明度）**仅在当前应用会话中有效**，不会被持久化保存。要使更改永久生效，您需要修改项目根目录下的 `.env` 文件，或者（如果使用了 Docker 并映射了自定义 `config.py`）修改您映射的 `config.py` 文件，然后重启应用。

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

使用 Docker Compose 启动服务：

```bash
docker-compose up -d --build
```

`docker-compose.yml` 文件配置如下：

```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: image_forward_app
    ports:
      - "46000:46000" # 将配置的端口映射到主机
    env_file:
      - .env # 从项目根目录的 .env 文件加载环境变量到容器
    volumes:
      - ./picture:/app/picture # 持久化图片存储
      - ./app/background:/app/background # 映射背景图片目录
      # 如需使用自定义的 config.py 文件，请取消下面一行的注释，
      # 并确保 'my_custom_config.py' (或您选择的文件名) 存在于 docker-compose.yml 同级目录。
      # - ./my_custom_config.py:/app/config.py
    restart: unless-stopped
```
这允许您：
- 通过在项目根目录创建和修改 `.env` 文件来覆盖默认配置。
- （可选）通过取消注释并提供您自己的 `config.py` 文件（例如 `my_custom_config.py`）来完全替换应用内的默认配置。

## 使用指南

### 访问地址

- 主页：`http://127.0.0.1:PORT/` (PORT 为您配置的端口，默认为 46000)
- 管理界面：`http://127.0.0.1:PORT/admin`
- 随机转发：`http://127.0.0.1:PORT/合集名称`

### 管理流程

1. 访问管理界面并使用您在配置文件 (`config.py` 或通过 `.env` 文件覆盖的) 中设置的管理员密码登录。
2. 创建新的图片合集。
3. 上传本地图片或添加外部图片链接。
4. 通过随机转发URL测试功能。

## 数据存储

- 所有图片和外链数据存储在项目运行目录下的 `/picture` 文件夹中 (通过 Docker Volume 持久化)。
- 每个图片合集对应 `/picture` 下的一个子文件夹。
- 合集下的本地图片直接存储在该子文件夹中。
- 合集下的外部链接集中存储在子文件夹内一个与合集同名的 `.txt` 文件中。
- 背景图片存储在 `/app/background` 目录中。
