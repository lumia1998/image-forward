import os
import random
from flask import current_app
from werkzeug.utils import secure_filename
import glob

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
            current_app.logger.debug(f"StorageManager: Initial PICTURE_DIR from config: {config_picture_dir}")
            self.picture_dir = config_picture_dir
            # 确保使用绝对路径，但不重复添加/app前缀
            if not os.path.isabs(self.picture_dir):
                self.picture_dir = os.path.abspath(self.picture_dir)
            current_app.logger.debug(f"StorageManager: Calculated absolute base_dir: {self.picture_dir}")
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
        """获取合集的封面图片文件名（最新上传的图片）

        Args:
            collection_name: 合集名称

        Returns:
            str: 最新图片的相对文件名，如果合集为空或不存在则返回 None
        """
        if not self.collection_exists(collection_name):
            current_app.logger.debug(f"合集 '{collection_name}' 不存在，无法获取封面。")
            return None

        image_filenames = self.get_collection_images(collection_name)
        if not image_filenames:
            current_app.logger.debug(f"合集 '{collection_name}' 为空，无法获取封面。")
            return None

        collection_path = os.path.join(self.base_dir, collection_name)
        
        images_with_mtime = []
        for filename in image_filenames:
            full_path = os.path.join(collection_path, filename)
            try:
                if os.path.exists(full_path):
                    mtime = os.path.getmtime(full_path)
                    images_with_mtime.append((mtime, filename))
                else:
                    current_app.logger.warning(f"获取封面时文件未找到 (可能在glob后被删除): {full_path}")
            except FileNotFoundError:
                current_app.logger.warning(f"获取封面时文件未找到 (FileNotFoundError): {full_path}")
                continue
            except Exception as e:
                current_app.logger.error(f"获取文件 '{full_path}' 修改时间时出错: {e}")
                continue
        
        if not images_with_mtime:
            current_app.logger.debug(f"合集 '{collection_name}' 中没有有效的图片文件来确定封面。")
            return None

        # 按修改时间降序排序，最新的在最前面
        images_with_mtime.sort(key=lambda item: item[0], reverse=True)
        
        latest_image_filename = images_with_mtime[0][1]
        current_app.logger.debug(f"合集 '{collection_name}' 的封面图片为: {latest_image_filename}")
        return latest_image_filename
    
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
            current_app.logger.debug(f"StorageManager: Attempting to save image to: {save_path}")
            image_file.save(save_path)
            current_app.logger.info(f"StorageManager: Successfully saved image to: {save_path}")
            return filename
        except Exception as e:
            current_app.logger.error(f"StorageManager: Failed to save image to {save_path}. Error: {e}")
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
        """从合集中随机获取一个资源（本地图片或外链）
        
        Args:
            collection_name: 合集名称
        
        Returns:
            tuple: (资源类型, 资源路径或URL)
                资源类型: 'local' 表示本地图片, 'external' 表示外部链接
                资源路径: 本地图片为完整文件路径, 外部链接为URL
        """
        if not self.collection_exists(collection_name):
            return None, None
        
        # 获取所有本地图片和外链
        local_images = self.get_collection_images(collection_name)
        external_links = self.get_collection_links(collection_name)
        
        # 合并资源
        resources = []
        for image in local_images:
            resources.append(('local', os.path.join(self.base_dir, collection_name, image)))
        
        for link in external_links:
            resources.append(('external', link))
        
        if not resources:
            return None, None
        
        # 随机选择一个资源
        resource_type, resource_path = random.choice(resources)
        return resource_type, resource_path