from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from app.storage import storage_manager
from app.auth.auth import login, logout, login_required
from dotenv import find_dotenv, set_key
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def index():
    """管理页：显示所有图片合集"""
    collections = storage_manager.get_all_collections()
    background_image_filename = current_app.config.get('BACKGROUND_IMAGE_PATH')
    background_opacity = current_app.config.get('BACKGROUND_OPACITY')
    return render_template('admin.html',
                           collections=collections,
                           background_image_filename=background_image_filename,
                           background_opacity=background_opacity)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    """登录页面"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if login(password):
            return redirect(url_for('admin.index'))
        else:
            flash('密码错误！', 'danger')
    background_image_filename = current_app.config.get('BACKGROUND_IMAGE_PATH')
    background_opacity = current_app.config.get('BACKGROUND_OPACITY')
    return render_template('login.html',
                           background_image_filename=background_image_filename,
                           background_opacity=background_opacity)

@admin_bp.route('/logout')
def logout_action():
    """登出操作"""
    logout()
    return redirect(url_for('admin.login_page'))

@admin_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """更新个性化设置"""
    # dotenv_path = find_dotenv() # 改为更明确的路径
    dotenv_path = os.path.join(current_app.root_path, '.env')
    settings_changed = False

    new_app_name = request.form.get('app_name')
    if new_app_name and new_app_name.strip() != current_app.config.get('APP_NAME'):
        set_key(dotenv_path, 'APP_NAME', new_app_name.strip())
        current_app.config['APP_NAME'] = new_app_name.strip() 
        flash('应用名称已更新。', 'success')
        settings_changed = True

    def process_background_image_upload(file_input_name, config_key_env_var, default_prefix_for_new_file):
        nonlocal settings_changed
        if file_input_name in request.files:
            file = request.files[file_input_name]
            if file and file.filename != '':
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                user_submitted_filename = file.filename # 保留用户原始文件名

                # 从用户提交的文件名中安全地提取扩展名
                _ , raw_file_extension = os.path.splitext(user_submitted_filename)
                file_ext = raw_file_extension.lower().lstrip('.')
                
                if not file_ext or file_ext not in allowed_extensions:
                    flash(f'文件 "{user_submitted_filename}" 的类型无效 (检测到: {file_ext})。请使用 {", ".join(allowed_extensions).upper()} 格式的图片。', 'danger')
                    current_app.logger.warning(f"无效文件类型上传: {user_submitted_filename}, 检测到扩展名: {file_ext}")
                    return

                # 使用配置中定义的默认文件名作为基础，并结合用户上传文件的安全扩展名
                # default_prefix_for_new_file 来自于 config.py 中的 os.getenv 第二个参数的基础名部分, e.g., 'default_login'
                # 这确保了我们总是用如 'default_login.png', 'default_admin.webp' 这样的文件名保存和引用
                base_name_for_saving = os.path.splitext(current_app.config.get(config_key_env_var, f"{default_prefix_for_new_file}.{file_ext}"))[0]
                new_filename = f"{base_name_for_saving}.{file_ext}"

                # 修改：背景图片保存到 /app/project_backgrounds/ (容器内路径)
                # current_app.root_path 通常是 /app
                background_save_dir = os.path.join(current_app.root_path, 'background')
                if not os.path.exists(background_save_dir):
                    try:
                        os.makedirs(background_save_dir, exist_ok=True)
                    except OSError as e:
                        current_app.logger.error(f"创建背景图片目录失败: {e}")
                        flash(f'创建背景图片目录失败: {background_save_dir}', 'danger')
                        return
                
                save_path = os.path.join(background_save_dir, new_filename)
                current_app.logger.debug(f"AdminRoutes: Background save directory: {background_save_dir}")
                current_app.logger.debug(f"AdminRoutes: Attempting to save background image to: {save_path}")
                
                try:
                    file.save(save_path)
                    set_key(dotenv_path, config_key_env_var, new_filename) # 更新.env中的文件名
                    current_app.config[config_key_env_var] = new_filename # 即时更新当前app config
                    flash(f'背景图片已更新为 {new_filename}。', 'success') # 统一提示信息
                    settings_changed = True
                except Exception as e:
                    current_app.logger.error(f"保存背景图片失败 ({new_filename}): {e}")
                    flash(f'保存背景图片失败: {e}', 'danger') # 统一提示信息
        return

    # 使用统一的表单字段名 'background_image', 统一的配置键, 和统一的默认前缀
    process_background_image_upload('background_image', 'BACKGROUND_IMAGE_PATH', 'default_background')

    new_opacity_str = request.form.get('background_opacity')
    if new_opacity_str:
        try:
            new_opacity = float(new_opacity_str)
            if 0.1 <= new_opacity <= 1.0:
                current_opacity = float(current_app.config.get('BACKGROUND_OPACITY', 1.0))
                if abs(new_opacity - current_opacity) > 1e-5: 
                    set_key(dotenv_path, 'BACKGROUND_OPACITY', str(new_opacity))
                    current_app.config['BACKGROUND_OPACITY'] = new_opacity
                    flash('背景透明度已更新。', 'success')
                    settings_changed = True
            else:
                flash('透明度值必须在 0.1 到 1.0 之间。', 'danger')
        except ValueError:
            flash('无效的透明度值。', 'danger')
            
    if not settings_changed:
        flash('没有检测到需要更新的设置。', 'info')
    else:
        flash('设置已保存。部分更改可能需要刷新页面或重启应用才能完全生效。', 'info')
        
    return redirect(url_for('admin.index'))

@admin_bp.route('/collection/create', methods=['POST'])
@login_required
def create_collection():
    collection_name = request.form.get('collection_name', '').strip()
    if not collection_name:
        flash('合集名称不能为空！', 'danger')
        return redirect(url_for('admin.index'))
    if not (collection_name.isalnum() or '_' in collection_name) or not collection_name.replace('_', '').isalnum(): # 更准确的检查
        flash('合集名称只能包含字母、数字和下划线！', 'danger')
        return redirect(url_for('admin.index'))
    result = storage_manager.create_collection(collection_name)
    if result:
        flash(f'合集 "{collection_name}" 创建成功！', 'success')
    else:
        flash(f'合集 "{collection_name}" 已存在！', 'warning')
    return redirect(url_for('admin.index'))

@admin_bp.route('/collection/delete', methods=['POST'])
@login_required
def delete_collection():
    collection_name = request.form.get('collection_name', '')
    if not collection_name:
        flash('参数错误！', 'danger')
        return redirect(url_for('admin.index'))
    result = storage_manager.delete_collection(collection_name)
    if result:
        flash(f'合集 "{collection_name}" 删除成功！', 'success')
    else:
        flash(f'删除合集 "{collection_name}" 失败！', 'danger')
    return redirect(url_for('admin.index'))

@admin_bp.route('/collection/<collection_name>')
@login_required
def manage_collection(collection_name):
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    images = storage_manager.get_collection_images(collection_name)
    links = storage_manager.get_collection_links(collection_name)
    image_urls = []
    for image_filename in images: # 变量名修改为 image_filename
        image_urls.append({
            'name': image_filename,
            # 修正图片URL构造
            'url': url_for('admin.serve_picture', filename=f'{collection_name}/{image_filename}')
        })
    return render_template(
        'manage_collection.html',
        collection_name=collection_name,
        images=image_urls,
        links=links
    )

@admin_bp.route('/collection/<collection_name>/upload', methods=['POST'])
@login_required
def upload_image(collection_name):
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    if 'images[]' not in request.files:
        flash('没有上传文件！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    files = request.files.getlist('images[]')
    if not files or all(not f.filename for f in files): # 更简洁的检查
        flash('没有选择文件！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    
    success_count = 0
    failed_count = 0
    errors = []
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'psd', 'tif'}
    
    for file in files:
        if file and file.filename: # 确保文件存在且有文件名
            original_filename = secure_filename(file.filename) # 安全处理文件名
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            
            if ext not in allowed_extensions:
                failed_count += 1
                errors.append(f"不支持的文件类型: {original_filename}")
                current_app.logger.warning(f"文件类型不支持: {original_filename}")
                continue
            
            # 检查文件大小
            file_content = file.read() # 一次性读取
            if len(file_content) > current_app.config.get('MAX_CONTENT_LENGTH', 20 * 1024 * 1024):
                failed_count += 1
                errors.append(f"文件过大: {original_filename}，最大允许20MB")
                current_app.logger.warning(f"文件过大: {original_filename}")
                file.seek(0) # 为下一个可能的处理器重置指针（虽然这里直接continue）
                continue
            
            file.seek(0) # 重置指针以供保存
            try:
                # storage_manager.add_image_to_collection 应该使用原始文件名或安全处理后的文件名
                saved_filename = storage_manager.add_image_to_collection(collection_name, file)
                if saved_filename:
                    success_count += 1
                    current_app.logger.info(f"成功上传文件: {saved_filename} 到合集 {collection_name}")
                else:
                    failed_count += 1
                    errors.append(f"文件 {original_filename} 保存失败（可能已存在或存储错误）。")
                    current_app.logger.error(f"文件保存失败: {original_filename}")
            except Exception as e:
                failed_count += 1
                errors.append(f"文件 {original_filename} 上传出错: {str(e)}")
                current_app.logger.error(f"文件上传异常: {original_filename}, 错误: {str(e)}")
    
    if success_count > 0:
        flash(f'成功上传 {success_count} 张图片！', 'success')
    if failed_count > 0:
        for error in errors:
            flash(error, 'warning')
        flash(f'有 {failed_count} 张图片上传失败或未处理！', 'warning')
    if success_count == 0 and failed_count == 0 and any(f.filename for f in files): # 确保有文件被尝试
         flash('没有有效的图片被上传（例如，全部为空文件或格式错误）。', 'info')

    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/collection/<collection_name>/add-links', methods=['POST'])
@login_required
def add_links(collection_name):
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    links_text = request.form.get('links', '')
    if not links_text.strip():
        flash('请输入至少一个外链！', 'warning')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    links = [link.strip() for link in links_text.splitlines() if link.strip()] # 使用 splitlines 更佳
    valid_links = [link for link in links if link.startswith(('http://', 'https://'))]
    if not valid_links:
        flash('没有有效的外链！所有链接必须以http://或https://开头。', 'warning')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    count = storage_manager.add_links_to_collection(collection_name, valid_links)
    flash(f'成功添加 {count} 个外链！', 'success')
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/collection/<collection_name>/delete-image', methods=['POST'])
@login_required
def delete_image(collection_name):
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    image_name = request.form.get('image_name', '')
    if not image_name:
        flash('参数错误！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    result = storage_manager.delete_image_from_collection(collection_name, image_name)
    if result:
        flash(f'图片 "{image_name}" 删除成功！', 'success')
    else:
        flash(f'删除图片 "{image_name}" 失败！', 'danger')
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/collection/<collection_name>/delete-link', methods=['POST'])
@login_required
def delete_link(collection_name):
    if not storage_manager.collection_exists(collection_name):
        abort(404)
    link = request.form.get('link', '')
    if not link:
        flash('参数错误！', 'danger')
        return redirect(url_for('admin.manage_collection', collection_name=collection_name))
    result = storage_manager.delete_link_from_collection(collection_name, link)
    if result:
        flash('外链删除成功！', 'success')
    else:
        flash('删除外链失败！', 'danger')
    return redirect(url_for('admin.manage_collection', collection_name=collection_name))

@admin_bp.route('/picture/<path:filename>')
def serve_picture(filename):
    """提供图片文件服务, 包括合集图片和背景图片"""
    # filename 可能像 'collection_name/image.jpg' 或 'background/bg.jpg'
    picture_base_dir = current_app.config.get('PICTURE_DIR', 'picture') # 'picture'
    # send_from_directory 需要绝对路径或相对于 app root 的路径
    # os.path.join 会正确处理 'picture' 和 'collection_name/image.jpg'
    # 或者 'picture' 和 'background/bg.jpg'
    # 但 send_from_directory 的第一个参数 'directory' 是指基础目录，不包含 filename 中的路径部分
    
    # 如果 filename 是 'background/my_bg.jpg', 则 directory 是 'picture', filename_for_send 是 'background/my_bg.jpg'
    # 如果 filename 是 'mycollection/my_image.jpg', 则 directory 是 'picture', filename_for_send 是 'mycollection/my_image.jpg'
    
    # 所以，directory 应该是 picture_base_dir
    # filename 已经是 'background/...' 或 'collection_name/...'
    
    absolute_picture_dir = os.path.abspath(picture_base_dir)
    # current_app.logger.debug(f"Attempting to serve: {filename} from directory: {absolute_picture_dir}")
    return send_from_directory(absolute_picture_dir, filename, as_attachment=False)