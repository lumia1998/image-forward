from flask import Flask
import os
from config import Config

def create_app():
    """创建并配置Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 确保图片目录存在
    os.makedirs(Config.PICTURE_DIR, exist_ok=True)
    
    # 初始化认证模块
    from app.auth import init_auth
    init_auth(app)
    
    # 注册蓝图
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.redirect import redirect_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(redirect_bp)
    
    return app