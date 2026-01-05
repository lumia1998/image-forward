import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 基础配置
class Config:
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'config_default_secret_key')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    APP_NAME = os.getenv('APP_NAME', '')
    BACKGROUND_IMAGE_PATH = os.getenv('BACKGROUND_IMAGE_PATH', 'default_background.jpg')
    BACKGROUND_OPACITY = float(os.getenv('BACKGROUND_OPACITY', '0.25'))
    NAVBAR_OPACITY = float(os.getenv('NAVBAR_OPACITY', '0.65'))
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 46000))

    # 管理员配置
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'config_default_admin_pass')
    ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'admin')
    ADMIN_COOKIE_NAME = 'image_forward_admin_token'

    # 配置文件路径（JSON 格式）
    CONFIG_PATH = os.getenv('CONFIG_PATH', os.path.join(os.path.dirname(__file__), 'config.json'))

    # 存储配置
    PICTURE_DIR = os.getenv('PICTURE_DIR', 'picture')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 最大上传文件大小：20MB
