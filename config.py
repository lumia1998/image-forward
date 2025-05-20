import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 基础配置
class Config:
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'config_default_secret_key') # 更新默认值
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes') # 更新默认值和逻辑
    APP_NAME = os.getenv('APP_NAME', '向日葵的图床 (Config Default)') # 更新默认值，确保引号正确
    BACKGROUND_IMAGE_PATH = os.getenv('BACKGROUND_IMAGE_PATH', 'default_background.jpg') # 统一背景图片
    BACKGROUND_OPACITY = float(os.getenv('BACKGROUND_OPACITY', '0.25')) # 背景透明度，有效范围0.1-1.0，默认为0.25（不透明）
    NAVBAR_OPACITY = float(os.getenv('NAVBAR_OPACITY', '0.65')) # 导航栏透明度，默认为0.65
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 46000))

    # 管理员配置
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'config_default_admin_pass') # 更新默认值

    # 存储配置
    PICTURE_DIR = os.getenv('PICTURE_DIR', 'picture')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 最大上传文件大小：20MB