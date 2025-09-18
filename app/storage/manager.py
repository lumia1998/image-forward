import os
import random
from flask import current_app
from werkzeug.utils import secure_filename
import glob
import requests
from urllib.parse import urlparse

class StorageManager:
    """存储管理器，负责处理图片合集的存储和检索"""
    
    def __init__(self):
        """初始化存储管理器"""
        self.picture_dir = None
    
    @property
    def base_dir(self):
        """获取图片存储的基础目录"""
        if not self.picture_dir:
            config_picture_dir = current_app.config.get('PICTURE_DIR', 'picture')
            current_app.logger.debug(f"StorageManager: Initial PICTURE_DIR from config: '{config_picture_dir}' and app.root_path: '{current_app.root_path}'")
            
            # 始终基于 app.root_path 构建路径，以避免受 Gunicorn CWD 影响
            if not os.path.isabs(config_picture_dir):
                # current_app.root_path is typically /app in the container
                self.picture_dir = os.path.join(current_app.root_path, config_picture_dir)
            else:
                # If PICTURE_DIR was somehow set as an absolute path, use it directly
                # This case is less likely for 'picture' but good for robustness
                self.picture_dir = config_picture_dir
            
            current_app.logger.info(f"StorageManager: Final calculated base_dir for pictures: {self.picture_dir}")
            os.makedirs(self.picture_dir, exist_ok=True)
        return self.picture_dir
    
    def get_all_collections(self):
        """获取所有图片合集"""
        collections = []
        for item in os.listdir(self.base_dir):
            if os.path.isdir(os.path.join(self.base_dir, item)) and item.lower() != 'background':
                collections.append(item)
        return collections
    
    def create_collection(self, collection_name):
        """创建新的图片合集
        
        Args:
            collection_name: 合集名称
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        collection_path = os.path.join(self.base_dir, collection_name)
        if os.path.exists(collection_path):
            return False
        
        os.makedirs(collection_path, exist_ok=True)
        return True
    
    def delete_collection(self, collection_name):
        """删除图片合集
        
        Args:
            collection_name: 合集名称
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        import shutil
        collection_path = os.path.join(self.base_dir, collection_name)
        if not os.path.exists(collection_path):
            return False
        
        try:
            shutil.rmtree(collection_path)
            return True
        except Exception:
            return False
    
    def collection_exists(self, collection_name):
        """检查合集是否存在
        
        Args:
            collection_name: 合集名称
        
        Returns:
            bool: 存在返回True，不存在返回False
        """
        collection_path = os.path.join(self.base_dir, collection_name)
        return os.path.exists(collection_path) and os.path.isdir(collection_path)
    
    def get_collection_images(self, collection_name):
        """获取合集中的所有本地图片
        
        Args:
            collection_name: 合集名称
        
        Returns:
            list: 图片文件名列表
        """
        if not self.collection_exists(collection_name):
            return []
        
        collection_path = os.path.join(self.base_dir, collection_name)
        images = []
        
        # 常见图片扩展名
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'psd', 'tif']
        
        for ext in image_extensions:
            pattern = os.path.join(collection_path, f'*.{ext}')
            images.extend(glob.glob(pattern))
            # 不区分大小写的扩展名
            pattern = os.path.join(collection_path, f'*.{ext.upper()}')
            images.extend(glob.glob(pattern))
        
        return [os.path.basename(image) for image in images]
    
    def get_collection_links(self, collection_name):
        """获取合集中的所有外链
        
        Args:
            collection_name: 合集名称
        
        Returns:
            list: 外链URL列表
        """
        if not self.collection_exists(collection_name):
            return []
        
        links_file = os.path.join(self.base_dir, collection_name, f"{collection_name}.txt")
        
        if not os.path.exists(links_file):
            return []
        
        with open(links_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def get_collection_cover_image_filename(self, collection_name):
        """获取合集的封面图片文件名。
        优先选择合集内按名称排序的第一张本地图片。
        如果本地图片不存在，则尝试下载第一个外部链接作为封面。

        Args:
            collection_name: 合集名称

        Returns:
            str: 封面图片的文件名，如果无法确定封面则返回 None
        """
        if not self.collection_exists(collection_name):
            current_app.logger.debug(f"合集 '{collection_name}' 不存在，无法获取封面。")
            return None

        collection_path = os.path.join(self.base_dir, collection_name)
        
        # 1. 尝试获取本地图片作为封面
        image_filenames = self.get_collection_images(collection_name)
        if image_filenames:
            # 按文件名排序，取第一张
            image_filenames.sort()
            cover_filename = image_filenames[0]
            current_app.logger.info(f"合集 '{collection_name}' 使用本地图片 '{cover_filename}' 作为封面。")
            return cover_filename

        # 2. 如果没有本地图片，尝试从外链下载封面
        current_app.logger.info(f"合集 '{collection_name}' 没有本地图片，尝试从外链获取封面。")
        external_links = self.get_collection_links(collection_name)
        if not external_links:
            current_app.logger.info(f"合集 '{collection_name}' 也没有外链，无法生成封面。")
            return None

        # 定义从外链下载的封面文件名
        # 为了避免与用户上传的文件名冲突，使用一个特殊的前缀或固定名称
        # 提取原始链接的文件名和扩展名可能复杂且不可靠，因此使用固定名称和尝试从content-type获取扩展名
        
        default_cover_from_link_basename = "_cover_from_link" # 基础名
        cover_from_link_filename = None # 完整文件名，稍后确定扩展名

        first_link = external_links[0]
        
        # 尝试从链接猜测一个扩展名，如果失败则默认为 .jpg
        try:
            link_path = requests.utils.urlparse(first_link).path
            link_ext = os.path.splitext(link_path)[1].lower()
            if link_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                 cover_from_link_filename = f"{default_cover_from_link_basename}{link_ext}"
            else:
                cover_from_link_filename = f"{default_cover_from_link_basename}.jpg" # 默认
        except Exception:
            cover_from_link_filename = f"{default_cover_from_link_basename}.jpg" # 默认

        cover_save_path = os.path.join(collection_path, cover_from_link_filename)

        if os.path.exists(cover_save_path):
            current_app.logger.info(f"合集 '{collection_name}' 已存在从外链下载的封面 '{cover_from_link_filename}'。")
            return cover_from_link_filename
        
        current_app.logger.info(f"合集 '{collection_name}': 尝试从 '{first_link}' 下载封面到 '{cover_save_path}'。")
        try:
            response = requests.get(first_link, timeout=10, stream=True) # stream=True for large files, timeout
            response.raise_for_status() # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

            # 再次尝试从 Content-Type 获取更准确的扩展名
            content_type = response.headers.get('content-type')
            actual_ext = ".jpg" # 默认
            if content_type:
                if 'image/jpeg' in content_type:
                    actual_ext = '.jpg'
                elif 'image/png' in content_type:
                    actual_ext = '.png'
                elif 'image/gif' in content_type:
                    actual_ext = '.gif'
                elif 'image/webp' in content_type:
                    actual_ext = '.webp'
            
            # 更新带正确扩展名的文件名和保存路径
            cover_from_link_filename = f"{default_cover_from_link_basename}{actual_ext}"
            cover_save_path = os.path.join(collection_path, cover_from_link_filename)

            # 再次检查，如果因为扩展名改变而导致文件已存在
            if os.path.exists(cover_save_path):
                current_app.logger.info(f"合集 '{collection_name}' 已存在从外链下载的封面 (更新扩展名后) '{cover_from_link_filename}'。")
                return cover_from_link_filename

            with open(cover_save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            current_app.logger.info(f"成功从 '{first_link}' 下载封面并保存为 '{cover_from_link_filename}'。")
            return cover_from_link_filename
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"下载封面 '{first_link}' 失败: {e}")
        except IOError as e:
            current_app.logger.error(f"保存下载的封面到 '{cover_save_path}' 失败: {e}")
        except Exception as e:
            current_app.logger.error(f"处理封面下载时发生未知错误: {e}")

        current_app.logger.warning(f"无法为合集 '{collection_name}' 获取或生成封面。")
        return None
    
    def add_image_to_collection(self, collection_name, image_file):
        """添加图片到合集
        
        Args:
            collection_name: 合集名称
            image_file: 图片文件对象
        
        Returns:
            str: 成功返回保存的文件名，失败返回None
        """
        if not self.collection_exists(collection_name):
            return None
        
        # 安全处理文件名
        filename = secure_filename(image_file.filename)
        save_path = os.path.join(self.base_dir, collection_name, filename)
        
        try:
            current_app.logger.debug(f"StorageManager: Attempting to save image '{filename}' to: {save_path}")
            image_file.save(save_path) # image_file is werkzeug.datastructures.FileStorage
            # Post-save verification
            if os.path.exists(save_path):
                current_app.logger.info(f"StorageManager: Successfully saved and verified image '{filename}' at: {save_path}")
                return filename # filename is secure_filename(image_file.filename)
            else:
                # This case should ideally not happen if save() didn't raise an exception,
                # but it's a good sanity check.
                current_app.logger.error(f"StorageManager: Image save operation for '{filename}' reported success, BUT FILE NOT FOUND at the expected path: {save_path}. Check permissions, disk space, or if the filename contained problematic characters not fully sanitized by secure_filename for this filesystem.")
                return None
        except Exception as e:
            # Log the full exception details for better debugging
            current_app.logger.error(f"StorageManager: Exception during saving image '{filename}' to '{save_path}'. Error: {e}", exc_info=True)
            return None
    
    def add_links_to_collection(self, collection_name, links):
        """添加外链到合集
        
        Args:
            collection_name: 合集名称
            links: 外链URL列表
        
        Returns:
            int: 成功添加的外链数量
        """
        if not self.collection_exists(collection_name):
            return 0
        
        links_file = os.path.join(self.base_dir, collection_name, f"{collection_name}.txt")
        
        count = 0
        with open(links_file, 'a', encoding='utf-8') as f:
            for link in links:
                link = link.strip()
                if link:
                    f.write(f"{link}\n")
                    count += 1
        
        return count
    
    def delete_image_from_collection(self, collection_name, image_name):
        """从合集中删除图片
        
        Args:
            collection_name: 合集名称
            image_name: 图片文件名
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if not self.collection_exists(collection_name):
            return False
        
        image_path = os.path.join(self.base_dir, collection_name, image_name)
        if not os.path.exists(image_path):
            return False
        
        try:
            os.remove(image_path)
            return True
        except Exception:
            return False
    
    def delete_link_from_collection(self, collection_name, link):
        """从合集中删除外链
        
        Args:
            collection_name: 合集名称
            link: 外链URL
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if not self.collection_exists(collection_name):
            return False
        
        links_file = os.path.join(self.base_dir, collection_name, f"{collection_name}.txt")
        if not os.path.exists(links_file):
            return False
        
        links = []
        removed = False
        
        # 读取所有链接
        with open(links_file, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f]
        
        # 移除指定链接
        if link in links:
            links.remove(link)
            removed = True
        
        # 重写链接文件
        if removed:
            with open(links_file, 'w', encoding='utf-8') as f:
                for l in links:
                    f.write(f"{l}\n")
        
        return removed
    
    def get_random_resource(self, collection_name):
        """从合集中随机获取一个资源（本地图片或外链），优先选择本地图片。
        
        Args:
            collection_name: 合集名称
        
        Returns:
            tuple or None: 成功则返回 (资源类型, 资源路径或URL)，失败则返回 None。
                         资源类型: 'local' 表示本地图片, 'external' 表示外部链接。
                         资源路径: 本地图片为完整文件路径, 外部链接为URL。
                         如果合集不存在或为空，则返回 (None, None)。
        """
        if not self.collection_exists(collection_name):
            return None, None

        # 1. 首先，获取并检查本地图片
        local_images = self.get_collection_images(collection_name)
        if local_images:
            # 如果本地图片列表不为空，随机选择一张并返回
            random_image_name = random.choice(local_images)
            image_path = os.path.join(self.base_dir, collection_name, random_image_name)
            return 'local', image_path

        # 2. 如果没有本地图片，再检查外部链接
        external_links = self.get_collection_links(collection_name)
        if external_links:
            # 如果外部链接列表不为空，随机选择一个并返回
            random_link = random.choice(external_links)
            return 'external', random_link

        # 3. 如果两者都为空，返回 None
        return None, None

    def cache_external_images(self, collection_name):
        """缓存合集中的所有外部图片到本地
        
        Args:
            collection_name: 合集名称
        
        Returns:
            int: 成功下载的图片数量
        """
        if not self.collection_exists(collection_name):
            current_app.logger.warning(f"缓存失败：合集 '{collection_name}' 不存在。")
            return 0
        
        external_links = self.get_collection_links(collection_name)
        if not external_links:
            current_app.logger.info(f"合集 '{collection_name}' 没有外部链接，无需缓存。")
            return 0
            
        collection_path = os.path.join(self.base_dir, collection_name)
        downloaded_count = 0
        
        for url in external_links:
            try:
                # 从URL中解析出文件名
                filename = os.path.basename(urlparse(url).path)
                if not filename:
                    # 如果URL路径为空或以/结尾，则尝试生成一个随机名称
                    filename = f"downloaded_{random.randint(1000, 9999)}.jpg"
                
                save_path = os.path.join(collection_path, secure_filename(filename))
                
                # 检查文件是否已存在
                if os.path.exists(save_path):
                    current_app.logger.debug(f"文件 '{save_path}' 已存在，跳过下载。")
                    continue
                
                current_app.logger.info(f"正在从 '{url}' 下载到 '{save_path}'...")
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    # 使用 iter_content 以流式方式写入，而不是 response.content
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded_count += 1
                current_app.logger.info(f"成功下载并保存 '{filename}'。")

            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"下载图片 '{url}' 失败: {e}")
            except IOError as e:
                current_app.logger.error(f"保存图片到 '{save_path}' 失败: {e}")
            except Exception as e:
                current_app.logger.error(f"处理链接 '{url}' 时发生未知错误: {e}")

        current_app.logger.info(f"合集 '{collection_name}' 的图片缓存完成，共下载 {downloaded_count} 张新图片。")
        return downloaded_count