import os
import logging
from typing import Dict, Set, List, Tuple
from ..config import MEMES_BASE_DIR, MEMES_DATA_PATH_DEFAULT, DEFAULT_CATEGORY_DESCRIPTIONS
from ..utils import ensure_dir_exists, save_json, load_json

logger = logging.getLogger(__name__)

class CategoryManager:
    def __init__(self, active_group: str = "default"):
        """初始化类别管理器"""
        self.active_group = active_group
        self.memes_dir = os.path.join(MEMES_BASE_DIR, "memes", self.active_group)
        self.memes_data_path = os.path.join(MEMES_BASE_DIR, f"memes_data_{self.active_group}.json")
        
        ensure_dir_exists(self.memes_dir)
        self._ensure_data_file()
        self.descriptions = self._load_descriptions()

    def _ensure_data_file(self) -> None:
        """确保 memes_data.json 文件存在，不存在则创建并写入默认数据"""
        if not os.path.exists(self.memes_data_path):
            # 如果是默认组且默认配置文件存在，则复制
            if self.active_group == "default" and os.path.exists(MEMES_DATA_PATH_DEFAULT):
                 shutil.copy(MEMES_DATA_PATH_DEFAULT, self.memes_data_path)
            else:
                save_json(DEFAULT_CATEGORY_DESCRIPTIONS if self.active_group == "default" else {}, self.memes_data_path)
            logger.info(f"创建类别描述文件: {self.memes_data_path}")

    def _load_descriptions(self) -> Dict[str, str]:
        """加载类别描述配置"""
        default_data = DEFAULT_CATEGORY_DESCRIPTIONS if self.active_group == "default" else {}
        return load_json(self.memes_data_path, default_data)

    def get_local_categories(self) -> Set[str]:
        """获取本地文件夹中的类别"""
        try:
            return {d for d in os.listdir(self.memes_dir)
                   if os.path.isdir(os.path.join(self.memes_dir, d))}
        except Exception as e:
            logger.error(f"获取本地类别失败: {e}")
            return set()

    def get_sync_status(self) -> Tuple[List[str], List[str]]:
        """获取同步状态"""
        local_categories = self.get_local_categories()
        config_categories = set(self.descriptions.keys())
        
        return (
            list(local_categories - config_categories),
            list(config_categories - local_categories)
        )

    def update_description(self, category: str, description: str) -> bool:
        """更新类别描述"""
        try:
            self.descriptions[category] = description
            return save_json(self.descriptions, self.memes_data_path)
        except Exception as e:
            logger.error(f"更新类别描述失败: {e}")
            return False

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """重命名类别"""
        try:
            if old_name not in self.descriptions:
                return False
            
            description = self.descriptions.pop(old_name)
            self.descriptions[new_name] = description
            
            old_path = os.path.join(self.memes_dir, old_name)
            new_path = os.path.join(self.memes_dir, new_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            
            return save_json(self.descriptions, self.memes_data_path)
        except Exception as e:
            logger.error(f"重命名类别失败: {e}")
            return False

    def delete_category(self, category: str) -> bool:
        """删除类别"""
        try:
            if category in self.descriptions:
                del self.descriptions[category]
                save_json(self.descriptions, self.memes_data_path)
            
            category_path = os.path.join(self.memes_dir, category)
            if os.path.exists(category_path):
                import shutil
                shutil.rmtree(category_path)
            
            return True
        except Exception as e:
            logger.error(f"删除类别失败: {e}")
            return False

    def get_descriptions(self) -> Dict[str, str]:
        """获取所有类别描述"""
        return self.descriptions.copy()

    def sync_with_filesystem(self) -> bool:
        """同步文件系统和配置"""
        try:
            local_categories = self.get_local_categories()
            changed = False
            
            for category in local_categories:
                if category not in self.descriptions:
                    self.descriptions[category] = "请添加描述"
                    changed = True
            
            if changed:
                return save_json(self.descriptions, self.memes_data_path)
            return True
        except Exception as e:
            logger.error(f"同步文件系统失败: {e}")
            return False