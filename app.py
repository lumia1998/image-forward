import os
import random
import string
import shutil
import secrets
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
from PIL import Image
from io import BytesIO

# 加载环境变量
load_dotenv()

# 配置应用
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'picture')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
PASSWORD = os.getenv('ADMIN_PASSWORD', 'default')  # 默认密码，建议在.env中设置

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 身份验证装饰器
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# 扫描所有合集
def scan_collections():
    collections = []
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        return collections
    
    for item in os.listdir(app.config['UPLOAD_FOLDER']):
        item_path = os.path.join(app.config['UPLOAD_FOLDER'], item)
        if os.path.isdir(item_path):
            # 获取本地图片
            local_images = []
            for file in os.listdir(item_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    local_images.append(file)
            
            # 获取外链图片
            external_images = []
            txt_file = os.path.join(item_path, f"{item}.txt")
            if os.path.exists(txt_file):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    external_images = [line.strip() for line in f if line.strip()]
            
            collections.append({
                'name': item,
                'local_images': local_images,
                'external_images': external_images,
                'total_images': len(local_images) + len(external_images)
            })
    
    return collections

# 主页 - 显示所有合集
@app.route('/')
def index():
    collections = scan_collections()
    return render_template('index.html', collections=collections)

# 显示合集中的图片
@app.route('/<collection>')
def show_collection(collection):
    collections = scan_collections()
    collection_data = next((c for c in collections if c['name'] == collection), None)
    
    if not collection_data:
        abort(404)
    
    return render_template('collection.html', collection=collection_data)

# 随机转发
@app.route('/r/<collection>')
def random_forward(collection):
    collections = scan_collections()
    collection_data = next((c for c in collections if c['name'] == collection), None)
    
    if not collection_data or collection_data['total_images'] == 0:
        abort(404)
    
    # 合并所有图片（本地和外链）
    all_images = [{'type': 'local', 'url': img} for img in collection_data['local_images']]
    all_images.extend([{'type': 'external', 'url': img} for img in collection_data['external_images']])
    
    # 随机选择一个图片
    selected = random.choice(all_images)
    
    if selected['type'] == 'local':
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], collection), selected['url'])
    else:
        return redirect(selected['url'])

# 管理登录
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_index'))
        else:
            flash('密码错误', 'error')
    
    return render_template('admin/login.html')

# 管理登出
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# 管理首页
@app.route('/admin')
@admin_required
def admin_index():
    collections = scan_collections()
    return render_template('admin/index.html', collections=collections)

# 创建合集
@app.route('/admin/create', methods=['POST'])
@admin_required
def admin_create_collection():
    name = request.form.get('name').strip()
    if not name:
        flash('合集名称不能为空', 'error')
        return redirect(url_for('admin_index'))
    
    # 确保名称安全
    safe_name = secure_filename(name)
    if not safe_name:
        flash('无效的合集名称', 'error')
        return redirect(url_for('admin_index'))
    
    # 创建目录
    collection_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if os.path.exists(collection_path):
        flash('合集已存在', 'error')
        return redirect(url_for('admin_index'))
    
    os.makedirs(collection_path)
    flash(f'合集 "{safe_name}" 创建成功', 'success')
    return redirect(url_for('admin_index'))

# 删除合集
@app.route('/admin/delete/<collection>', methods=['POST'])
@admin_required
def admin_delete_collection(collection):
    collection_path = os.path.join(app.config['UPLOAD_FOLDER'], collection)
    
    if not os.path.exists(collection_path) or not os.path.isdir(collection_path):
        flash('合集不存在', 'error')
        return redirect(url_for('admin_index'))
    
    # 删除目录及其内容
    shutil.rmtree(collection_path)
    flash(f'合集 "{collection}" 已删除', 'success')
    return redirect(url_for('admin_index'))

# 显示合集管理页面
@app.route('/admin/manage/<collection>')
@admin_required
def admin_manage_collection(collection):
    collections = scan_collections()
    collection_data = next((c for c in collections if c['name'] == collection), None)
    
    if not collection_data:
        flash('合集不存在', 'error')
        return redirect(url_for('admin_index'))
    
    return render_template('admin/manage.html', collection=collection_data)

# 上传本地图片
@app.route('/admin/upload/<collection>', methods=['POST'])
@admin_required
def admin_upload_image(collection):
    collection_path = os.path.join(app.config['UPLOAD_FOLDER'], collection)
    
    if not os.path.exists(collection_path) or not os.path.isdir(collection_path):
        flash('合集不存在', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    # 检查是否有文件上传
    if 'images' not in request.files:
        flash('没有选择文件', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    files = request.files.getlist('images')
    
    for file in files:
        if file and file.filename:
            # 确保文件名安全
            filename = secure_filename(file.filename)
            file_path = os.path.join(collection_path, filename)
            
            # 保存文件
            file.save(file_path)
            
            # 检查是否为图片（可选）
            try:
                img = Image.open(file_path)
                img.verify()
            except (IOError, SyntaxError) as e:
                # 如果不是有效图片，删除文件
                os.remove(file_path)
                flash(f'文件 "{filename}" 不是有效图片', 'error')
    
    flash('图片上传成功', 'success')
    return redirect(url_for('admin_manage_collection', collection=collection))

# 添加外链图片
@app.route('/admin/add_external/<collection>', methods=['POST'])
@admin_required
def admin_add_external(collection):
    collection_path = os.path.join(app.config['UPLOAD_FOLDER'], collection)
    txt_file = os.path.join(collection_path, f"{collection}.txt")
    
    if not os.path.exists(collection_path) or not os.path.isdir(collection_path):
        flash('合集不存在', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    urls = request.form.get('urls', '').splitlines()
    urls = [url.strip() for url in urls if url.strip()]
    
    if not urls:
        flash('没有添加任何URL', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    # 追加到文件
    with open(txt_file, 'a', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')
    
    flash(f'成功添加 {len(urls)} 个外链', 'success')
    return redirect(url_for('admin_manage_collection', collection=collection))

# 删除本地图片
@app.route('/admin/delete_local/<collection>/<filename>', methods=['POST'])
@admin_required
def admin_delete_local_image(collection, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], collection, filename)
    
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        flash('图片不存在', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    os.remove(file_path)
    flash(f'图片 "{filename}" 已删除', 'success')
    return redirect(url_for('admin_manage_collection', collection=collection))

# 删除外链图片
@app.route('/admin/delete_external/<collection>/<int:index>', methods=['POST'])
@admin_required
def admin_delete_external_image(collection, index):
    collection_path = os.path.join(app.config['UPLOAD_FOLDER'], collection)
    txt_file = os.path.join(collection_path, f"{collection}.txt")
    
    if not os.path.exists(txt_file) or os.path.isdir(txt_file):
        flash('外链文件不存在', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    # 读取所有URL
    with open(txt_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if index < 0 or index >= len(urls):
        flash('外链不存在', 'error')
        return redirect(url_for('admin_manage_collection', collection=collection))
    
    # 删除指定URL
    deleted_url = urls.pop(index)
    
    # 写回文件
    with open(txt_file, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')
    
    flash(f'外链已删除: {deleted_url}', 'success')
    return redirect(url_for('admin_manage_collection', collection=collection))

# 图片预览
@app.route('/preview/<collection>/<filename>')
def preview_image(collection, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], collection), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=46000, debug=True)    