import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 基础配置
class Config:
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', 'yes', '1')
    APP_NAME = os.getenv('APP_NAME', '我的图床管理界面')
    BACKGROUND_LOGIN_IMAGE_PATH = os.getenv('BACKGROUND_LOGIN_IMAGE_PATH', 'default_login.jpg') # 默认登录背景图片
    BACKGROUND_ADMIN_IMAGE_PATH = os.getenv('BACKGROUND_ADMIN_IMAGE_PATH', 'default_admin.jpg') # 默认管理后台背景图片
    BACKGROUND_OPACITY = float(os.getenv('BACKGROUND_OPACITY', '1.0')) # 背景透明度，默认为1.0（不透明）
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 46000))
    
    # 管理员配置
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
    
    # 存储配置
    PICTURE_DIR = os.getenv('PICTURE_DIR', 'picture')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 最大上传文件大小：20MB