from flask import session, redirect, url_for, request, flash
from functools import wraps

def init_auth(app):
    """初始化认证模块
    
    Args:
        app: Flask应用实例
    """
    # 在请求前检查认证状态
    @app.before_request
    def check_auth():
        # 只对管理路由进行认证检查
        if request.path.startswith('/admin') and not request.path.endswith('/login'):
            if not is_authenticated():
                return redirect(url_for('admin.login'))

def login(password):
    """用户登录
    
    Args:
        password: 用户提交的密码
    
    Returns:
        bool: 登录成功返回True，失败返回False
    """
    from flask import current_app
    admin_password = current_app.config.get('ADMIN_PASSWORD')
    
    if password == admin_password:
        session['authenticated'] = True
        return True
    return False

def logout():
    """用户登出"""
    session.pop('authenticated', None)

def is_authenticated():
    """检查用户是否已认证
    
    Returns:
        bool: 已认证返回True，未认证返回False
    """
    return session.get('authenticated', False)

def login_required(f):
    """要求登录的装饰器
    
    Args:
        f: 被装饰的函数
    
    Returns:
        函数: 包装后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function