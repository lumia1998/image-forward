import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 基础配置
class Config:
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', 'yes', '1')
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 46000))
    
    # 管理员配置
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
    
    # 存储配置
    PICTURE_DIR = os.getenv('PICTURE_DIR', 'picture')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 最大上传文件大小：20MB