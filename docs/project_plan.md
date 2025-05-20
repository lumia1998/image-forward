# 项目增强计划

## 核心目标

1.  **统一背景图片**：`index`、`admin` 和 `login` 页面使用同一张背景图片。该图片路径在 `config.py` 中通过 `BACKGROUND_IMAGE_PATH` 配置。
2.  **配置方式更改与持久化**：
    *   `config.py` 作为主要配置源，包含所有配置项的硬编码默认值。用户可以通过 Docker Volume 映射宿主机上的自定义 `config.py` 来完全替换镜像中的默认 `config.py`。
    *   `.env` 文件作为可选覆盖层。容器内的 `config.py` 会尝试加载位于 `/app/.env` 的 `.env` 文件。如果用户通过 `docker-compose.yml` 的 `env_file` 指令或 volume 映射了 `.env` 文件，其内容可以覆盖从 `config.py` 加载的相应值。
    *   通过管理界面进行的任何配置更改都**不会**写入任何文件，仅影响当前运行的应用实例 (`app.config`)，应用重启后将丢失。
3.  **背景图片透明度可配置**：背景图片的透明度由配置文件中的 `BACKGROUND_OPACITY` 控制（默认为 `1.0`），并应用于所有页面的背景以及导航栏。
4.  **Docker Compose 体现映射**：`docker-compose.yml` 文件将清晰地展示如何通过 `volumes` 映射用户自定义的 `config.py`，并继续使用 `env_file` 来加载 `.env`。

## 详细计划步骤

### 阶段一：配置文件和 Docker Compose

1.  **`config.py` ([`config.py`](config.py))**:
    *   包含所有配置项的**硬编码默认值**。
    *   **保留** `from dotenv import load_dotenv` 和 `load_dotenv()` 调用。
    *   所有配置项（`SECRET_KEY`, `DEBUG`, `APP_NAME`, `BACKGROUND_IMAGE_PATH`, `BACKGROUND_OPACITY`, `HOST`, `PORT`, `ADMIN_PASSWORD`, `PICTURE_DIR`）都应有明确的默认值，同时允许被 `.env` 文件通过 `os.getenv()` 覆盖。
        ```python
        # config.py
        import os
        from dotenv import load_dotenv
        load_dotenv() # Load .env if present

        class Config:
            SECRET_KEY = os.getenv('SECRET_KEY', 'config_default_secret_key')
            DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
            APP_NAME = os.getenv('APP_NAME', '图床管理 (Config Default)')
            BACKGROUND_IMAGE_PATH = os.getenv('BACKGROUND_IMAGE_PATH', 'default_background.jpg')
            BACKGROUND_OPACITY = float(os.getenv('BACKGROUND_OPACITY', '1.0'))
            ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'config_default_admin_pass')
            HOST = os.getenv('HOST', '0.0.0.0')
            PORT = int(os.getenv('PORT', 46000))
            PICTURE_DIR = os.getenv('PICTURE_DIR', 'picture')
            MAX_CONTENT_LENGTH = 20 * 1024 * 1024
        ```
    *   移除不再需要的特定页面背景配置项（如 `BACKGROUND_LOGIN_IMAGE_PATH`, `BACKGROUND_ADMIN_IMAGE_PATH`）。

2.  **`.env` 文件 (项目根目录)**:
    *   此文件将由 `docker-compose.yml` 中的 `env_file: - .env` 指令加载到容器的环境变量中。
    *   `config.py` 中的 `os.getenv()` 调用将能够读取这些环境变量。
    *   用户可以在此文件中设置他们希望覆盖 `config.py` 默认值的配置。

3.  **`docker-compose.yml` ([`docker-compose.yml`](docker-compose.yml))**:
    *   **保留** `env_file: - .env`。
    *   在 `services.web.volumes` 部分，添加注释或一个实际的（但默认注释掉的）volume 映射示例，用于用户自定义的 `config.py`。
        ```yaml
        version: '3.8'

        services:
          web:
            build: .
            container_name: image_forward_app
            ports:
              - "46000:46000"
            env_file:
              - .env # Loads variables from .env into the container's environment
            volumes:
              - ./picture:/app/picture
              - ./app/background:/app/background # 映射项目内的 app/background 目录
              # To use a custom config.py, uncomment the line below and ensure
              # 'my_custom_config.py' (or your chosen name) exists in the same directory as this docker-compose.yml
              # - ./my_custom_config.py:/app/config.py
            restart: unless-stopped
        ```
    *   考虑移除或注释掉未被使用的 `volumes: picture_data:` 定义。

### 阶段二：应用逻辑调整 (主要是 `admin.py`)

4.  **修改 `app/routes/admin.py` ([`app/routes/admin.py`](app/routes/admin.py))**:
    *   在 `update_settings` 函数中:
        *   **移除** `from dotenv import find_dotenv, set_key`。
        *   **移除** `dotenv_path = ...` 和所有 `set_key(dotenv_path, ...)` 的调用。
        *   当通过表单提交配置更改时，这些更改将**仅**更新 `current_app.config['SETTING_KEY'] = new_value`。它们**不会**被写入任何文件。
        *   修改所有相关的 `flash` 消息，明确告知用户：通过管理界面所做的所有配置更改**仅在当前应用会话中有效**。要使更改永久生效，他们需要修改项目根目录下的 `.env` 文件，或者（如果使用了自定义 `config.py` 映射）修改他们映射的 `config.py` 文件。

### 阶段三：模板和文档微调

5.  **修改 HTML 模板**:
    *   **`app/templates/admin.html` ([`app/templates/admin.html`](app/templates/admin.html))**:
        *   在“个性化设置”表单中，移除“登录页背景”和“管理页背景”的上传字段。只保留一个统一的背景图片上传字段（对应 `BACKGROUND_IMAGE_PATH`）。
    *   **`app/templates/base.html` ([`app/templates/base.html`](app/templates/base.html))**:
        *   导航栏透明度 `style="--navbar-bg-opacity: {{ config.get('BACKGROUND_OPACITY', 1.0) }};"` 保持不变。
    *   **`app/templates/login.html` ([`app/templates/login.html`](app/templates/login.html))**:
        *   更新登录表单下的提示文字 (第 47 行) 改为类似 “请输入在您的配置文件 (`.env` 或 `config.py`) 中设置的管理密码”。

6.  **更新 `README.md` ([`README.md`](README.md))**:
    *   详细说明配置的加载顺序和优先级：
        1.  镜像中 `/app/config.py` 的硬编码默认值。
        2.  如果用户通过 Docker volume 将宿主机的自定义 `config.py` 映射到容器的 `/app/config.py`，则它将**完全取代**镜像中的默认 `config.py` 文件。
        3.  容器内的 `/app/config.py` 会尝试从环境变量中加载配置（通过 `os.getenv()`）。这些环境变量可以通过 `docker-compose.yml` 中的 `env_file: - .env` 指令从项目根目录的 `.env` 文件加载。因此，`.env` 文件中的值将覆盖从 `config.py` 加载的相应值。
    *   提供在 `docker-compose.yml` 中如何映射自定义 `config.py` 的清晰示例。
    *   强调通过管理界面进行的配置更改**不是持久的**。永久更改必须通过修改项目根目录的 `.env` 文件或用户映射的 `config.py` 文件来实现。
    *   更新“管理流程”中关于密码设置的说明。

### Mermaid 配置流程图

```mermaid
graph LR
    subgraph App Startup & Config Loading
        A_Host_Config[Host: custom_config.py (Optional)] --Volume Mount--> A_Container_Config[/app/config.py]
        B_Host_Env[Host: .env (Optional)] --env_file directive--> B_Container_Env[Container Environment Variables]
        A_Container_Config --Reads Defaults & Calls load_dotenv()--> C_Initial_Config_State
        B_Container_Env --os.getenv() overrides--> C_Initial_Config_State
        C_Initial_Config_State --> D_App_Config[app.config (Flask)]
    end

    subgraph User Access & Page Rendering
        E_User_Request[User Request (/, /admin, /login)] --> F_Route_Handler[Route Handler]
        F_Route_Handler --Reads from--> D_App_Config
        F_Route_Handler --> G_Render_HTML[Render HTML Template]
        G_Render_HTML --Uses Config Values--> H_Displayed_Page[Page Displays with Background & Settings]
    end

    subgraph Admin UI Settings Update (Runtime Only)
        I_Admin_Form[Admin UI: Update Settings Form] --Submit Data--> J_Update_Settings_Route[admin.py: update_settings]
        J_Update_Settings_Route --Modifies only--> D_App_Config
        J_Update_Settings_Route -.-> K_No_File_Write((No File Write for UI Changes))
        J_Update_Settings_Route --> L_Flash_Message[Flash Message: "Settings updated for current session only"]
    end

    note right of L_Flash_Message
        To persist changes, edit host's .env or custom_config.py
        and restart the application/container.
    end