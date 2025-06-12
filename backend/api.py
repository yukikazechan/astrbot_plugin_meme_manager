from quart import Blueprint, jsonify, request, current_app
from .models import (
    scan_emoji_folder,
    get_emoji_by_category,
    add_emoji_to_category,
    delete_emoji_from_category,
)
import os
from ..config import MEMES_DIR
import logging


api = Blueprint("api", __name__)

logger = logging.getLogger(__name__)


@api.route("/emoji", methods=["GET"])
async def get_all_emojis():
    """获取所有表情包（按类别分组）"""
    plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
    active_group = plugin_config.get("plugin_config", {}).get("active_emotion_group", "default")
    emoji_data = await scan_emoji_folder(group=active_group)
    for category in emoji_data:
        if not isinstance(emoji_data[category], list):
            emoji_data[category] = []
    return jsonify(emoji_data)


@api.route("/emoji/<category>", methods=["GET"])
async def get_emojis_by_category(category):
    """获取指定类别的表情包"""
    plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
    active_group = plugin_config.get("plugin_config", {}).get("active_emotion_group", "default")
    emojis = get_emoji_by_category(category, group=active_group)
    if emojis is None:
        return jsonify({"message": "Category not found"}), 404
    return jsonify(emojis if isinstance(emojis, list) else []), 200


@api.route("/emoji/add", methods=["POST"])
async def add_emoji():
    """添加表情包到指定类别"""
    try:
        files = await request.files
        if not files or "image_file" not in files:
            return jsonify({"message": "没有找到上传的图片文件"}), 400
        
        image_file = files["image_file"]
        form = await request.form
        category = form.get("category")
        
        if not category:
            return jsonify({"message": "没有指定类别"}), 400
        
        if not image_file or not image_file.filename:
            return jsonify({"message": "无效的图片文件"}), 400

        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        active_group = plugin_config.get("plugin_config", {}).get("active_emotion_group", "default")
            
        logger.info(f"收到上传请求: 组={active_group}, 类别={category}, 文件名={image_file.filename}")
        
        try:
            result_path = add_emoji_to_category(category, image_file, group=active_group)
            
            category_manager = plugin_config.get("category_manager")
            if category_manager:
                category_manager.sync_with_filesystem()
                
            logger.info(f"表情包添加成功: {result_path}")
            return jsonify({
                "message": "表情包添加成功",
                "path": result_path,
                "category": category,
                "filename": image_file.filename
            }), 201
            
        except Exception as inner_e:
            logger.error(f"处理上传文件时出错: {inner_e}", exc_info=True)
            return jsonify({"message": f"处理上传文件时出错: {str(inner_e)}"}), 500
            
    except Exception as e:
        logger.error(f"处理上传请求时发生未知异常: {e}", exc_info=True)
        return jsonify({"message": f"处理上传请求时发生未知异常: {str(e)}"}), 500


@api.route("/emoji/delete", methods=["POST"])
async def delete_emoji():
    """删除指定类别的表情包"""
    data = await request.get_json()
    category = data.get("category")
    image_file = data.get("image_file")
    if not category or not image_file:
        return jsonify({"message": "Category and image file are required"}), 400

    plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
    active_group = plugin_config.get("plugin_config", {}).get("active_emotion_group", "default")

    if delete_emoji_from_category(category, image_file, group=active_group):
        return jsonify({"message": "Emoji deleted successfully", "category": category, "filename": image_file}), 200
    else:
        return jsonify({"message": "Emoji not found"}), 404


@api.route("/emotions", methods=["GET"])
async def get_emotions():
    """获取表情包类别描述"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        descriptions = category_manager.get_descriptions()
        return jsonify(descriptions)
    except Exception as e:
        current_app.logger.error(f"获取标签描述失败: {e}")
        return jsonify({"error": "获取标签描述失败"}), 500


@api.route("/category/delete", methods=["POST"])
async def delete_category():
    """删除表情包类别"""
    try:
        data = await request.get_json()

        category = data.get("category")
        if not category:
            return jsonify({"message": "Category is required"}), 400

        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        
        if not category_manager:
            return jsonify({"message": "Category manager not found"}), 404

        if category_manager.delete_category(category):
            return jsonify({"message": "Category deleted successfully"}), 200
        else:
            return jsonify({"message": "Failed to delete category"}), 500
    except Exception as e:
        return jsonify({"message": f"Failed to delete category: {str(e)}"}), 500


@api.route("/sync/status", methods=["GET"])
async def get_sync_status():
    """获取同步状态"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        
        if not category_manager:
            raise ValueError("未找到类别管理器")
        
        logger.info("获取同步状态...")
        missing_in_config, deleted_categories = category_manager.get_sync_status()
        
        return jsonify({
            "status": "ok",
            "differences": {
                "missing_in_config": missing_in_config,
                "deleted_categories": deleted_categories,
            }
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return jsonify({"error": "获取同步状态失败"}), 500


@api.route("/sync/config", methods=["POST"])
async def sync_config():
    """同步配置与文件夹结构的 API 端点"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        
        if not category_manager:
            raise ValueError("未找到类别管理器")
        
        logger.info("开始同步配置...")
        if category_manager.sync_with_filesystem():
            logger.info("配置同步成功")
            return jsonify({"message": "配置同步成功"}), 200
        else:
            logger.warning("配置同步失败")
            return jsonify({"message": "配置同步失败"}), 500
    except Exception as e:
        logger.error(f"配置同步失败: {e}")
        return jsonify({"message": f"配置同步失败: {str(e)}"}), 500


@api.route("/category/update_description", methods=["POST"])
async def update_category_description():
    """更新类别的描述"""
    try:
        data = await request.get_json()
        category = data.get("tag")
        description = data.get("description")
        if not category or not description:
            return jsonify({"message": "Category and description are required"}), 400

        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        
        if not category_manager:
            return jsonify({"message": "Category manager not found"}), 404

        if category_manager.update_description(category, description):
            # 返回更新后的类别和描述
            return jsonify({"category": category, "description": description}), 200
        else:
            return jsonify({"message": "Failed to update category description"}), 500
    except Exception as e:
        return jsonify({"message": f"Failed to update category description: {str(e)}"}), 500



@api.route("/category/restore", methods=["POST"])
async def restore_category():
    """恢复或创建新类别"""
    try:
        data = await request.get_json()

        category = data.get("category")
        description = data.get("description", "请添加描述")
        
        if not category:
            return jsonify({"message": "Category is required"}), 400

        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        
        if not category_manager:
            return jsonify({"message": "Category manager not found"}), 404

        # 创建类别目录
        active_group = plugin_config.get("plugin_config", {}).get("active_emotion_group", "default")
        category_path = os.path.join(MEMES_DIR, active_group, category)
        os.makedirs(category_path, exist_ok=True)

        # 更新类别描述
        if category_manager.update_description(category, description):
            return jsonify({"message": "Category created successfully", "description": description}), 200
        else:
            return jsonify({"message": "Failed to create category"}), 500

    except Exception as e:
        return jsonify({"message": f"Failed to create category: {str(e)}"}), 500


@api.route("/category/rename", methods=["POST"])
async def rename_category():
    """重命名类别"""
    try:
        data = await request.get_json()
        old_name = data.get("old_name")
        new_name = data.get("new_name")
        if not old_name or not new_name:
            return jsonify({"message": "Old and new category names are required"}), 400

        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        category_manager = plugin_config.get("category_manager")
        
        if not category_manager:
            return jsonify({"message": "Category manager not found"}), 404

        if category_manager.rename_category(old_name, new_name):
            return jsonify({"message": "Category renamed successfully"}), 200
        else:
            return jsonify({"message": "Failed to rename category"}), 500
    except Exception as e:
        return jsonify({"message": f"Failed to rename category: {str(e)}"}), 500


@api.route("/img_host/sync/status", methods=["GET"])
async def get_img_host_sync_status():
    """获取同步状态"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        img_sync = plugin_config.get("img_sync")
        if not img_sync:
            return jsonify({"error": "图床服务未配置"}), 400
            
        status = img_sync.check_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/img_host/sync/upload", methods=["POST"])
async def sync_to_remote():
    """同步到云端"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        img_sync = plugin_config.get("img_sync")
        if not img_sync:
            return jsonify({"message": "图床服务未配置"}), 400
            
        img_sync.sync_process = img_sync._start_sync_process('upload')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@api.route("/img_host/sync/download", methods=["POST"]) 
async def sync_from_remote():
    """从云端同步"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        img_sync = plugin_config.get("img_sync")
        if not img_sync:
            return jsonify({"message": "图床服务未配置"}), 400
            
        img_sync.sync_process = img_sync._start_sync_process('download')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@api.route("/img_host/sync/check_process", methods=["GET"])
async def check_sync_process():
    """检查同步进程状态"""
    try:
        plugin_config = current_app.config.get("PLUGIN_CONFIG", {})
        img_sync = plugin_config.get("img_sync")
        if not img_sync or not img_sync.sync_process:
            return jsonify({"completed": True, "success": True})
            
        if not img_sync.sync_process.is_alive():
            success = img_sync.sync_process.exitcode == 0
            img_sync.sync_process = None
            return jsonify({"completed": True, "success": success})
            
        return jsonify({"completed": False})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@api.route("/groups", methods=["GET"])
async def get_groups():
    """获取所有表情组"""
    try:
        plugin_config_all = current_app.config.get("PLUGIN_CONFIG", {})
        plugin_config = plugin_config_all.get("plugin_config", {})
        groups = plugin_config.get("emotion_groups", {"default": {}})
        active_group = plugin_config.get("active_emotion_group", "default")
        return jsonify({
            "groups": list(groups.keys()),
            "active_group": active_group
        })
    except Exception as e:
        logger.error(f"获取表情组失败: {e}")
        return jsonify({"error": "获取表情组失败"}), 500

@api.route("/group/create", methods=["POST"])
async def create_group():
    """创建新表情组"""
    try:
        data = await request.get_json()
        group_name = data.get("group_name")
        if not group_name:
            return jsonify({"message": "Group name is required"}), 400

        plugin_config_all = current_app.config.get("PLUGIN_CONFIG", {})
        plugin_context = plugin_config_all.get("plugin_context")
        plugin_name = plugin_config_all.get("plugin_name")
        
        plugin_conf = plugin_config_all.get("plugin_config")
        groups = plugin_conf.get("emotion_groups", {})
        if group_name in groups:
            return jsonify({"message": f"表情组 '{group_name}' 已存在。"}), 400

        # 复制 default 组的配置
        default_group_config = groups.get("default", {"high_confidence_emotions": []})
        groups[group_name] = default_group_config.copy()
        plugin_conf["emotion_groups"] = groups
        plugin_conf.save_config()
        
        # 复制 default 组的描述文件和目录结构
        from ..config import MEMES_BASE_DIR, DEFAULT_CATEGORY_DESCRIPTIONS
        from ..utils import load_json, save_json
        
        default_data_path = os.path.join(MEMES_BASE_DIR, "memes_data_default.json")
        new_data_path = os.path.join(MEMES_BASE_DIR, f"memes_data_{group_name}.json")
        
        default_descriptions = load_json(default_data_path, DEFAULT_CATEGORY_DESCRIPTIONS)
        save_json(default_descriptions, new_data_path)
        
        new_group_memes_dir = os.path.join(MEMES_DIR, group_name)
        os.makedirs(new_group_memes_dir, exist_ok=True)
        for category in default_descriptions.keys():
            os.makedirs(os.path.join(new_group_memes_dir, category), exist_ok=True)

        return jsonify({"message": f"表情组 '{group_name}' 已成功创建，并继承了 default 组的分类结构。"}), 201
    except Exception as e:
        logger.error(f"创建表情组失败: {e}")
        return jsonify({"message": f"创建表情组失败: {str(e)}"}), 500

@api.route("/group/delete", methods=["POST"])
async def delete_group():
    """删除表情组"""
    try:
        data = await request.get_json()
        group_name = data.get("group_name")
        if not group_name:
            return jsonify({"message": "Group name is required"}), 400
        if group_name == "default":
            return jsonify({"message": "Cannot delete default group"}), 400

        plugin_config_all = current_app.config.get("PLUGIN_CONFIG", {})
        plugin_context = plugin_config_all.get("plugin_context")
        plugin_name = plugin_config_all.get("plugin_name")
        
        plugin_conf = plugin_context.get_plugin_config(plugin_name)
        if plugin_conf.get("active_emotion_group") == group_name:
            return jsonify({"message": "Cannot delete active group"}), 400

        groups = plugin_conf.get("emotion_groups", {})
        if group_name not in groups:
            return jsonify({"message": f"Group '{group_name}' not found"}), 404
        
        del groups[group_name]
        plugin_conf["emotion_groups"] = groups
        plugin_conf.save_config()
        
        import shutil
        group_dir = os.path.join(MEMES_DIR, group_name)
        if os.path.exists(group_dir):
            shutil.rmtree(group_dir)

        return jsonify({"message": f"Group '{group_name}' deleted successfully. Please reload plugin."}), 200
    except Exception as e:
        logger.error(f"删除表情组失败: {e}")
        return jsonify({"message": f"删除表情组失败: {str(e)}"}), 500

@api.route("/group/switch", methods=["POST"])
async def switch_group():
    """切换激活的表情组"""
    try:
        data = await request.get_json()
        group_name = data.get("group_name")
        if not group_name:
            return jsonify({"message": "Group name is required"}), 400

        plugin_config_all = current_app.config.get("PLUGIN_CONFIG", {})
        plugin_context = plugin_config_all.get("plugin_context")
        plugin_name = plugin_config_all.get("plugin_name")
        
        plugin_conf = plugin_context.get_plugin_config(plugin_name)
        groups = plugin_conf.get("emotion_groups", {})
        if group_name not in groups:
            return jsonify({"message": f"Group '{group_name}' not found"}), 404

        plugin_conf["active_emotion_group"] = group_name
        plugin_conf.save_config()
        
        # 更新 category_manager
        category_manager = plugin_config_all.get("category_manager")
        if category_manager:
            category_manager.__init__(active_group=group_name)

        return jsonify({"message": f"Switched to group '{group_name}'. Please reload plugin."}), 200
    except Exception as e:
        logger.error(f"切换表情组失败: {e}")
        return jsonify({"message": f"切换表情组失败: {str(e)}"}), 500


