"""
Template Manager - 配置模板管理模块

本模块负责管理条码生成器的配置模板，支持保存、加载、删除和列出模板。
模板以JSON格式存储，包含所有渲染配置参数。
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional


@dataclass
class Template:
    """模板数据类
    
    Attributes:
        name: 模板名称
        config: 配置字典，包含所有渲染参数
        created_at: 创建时间（ISO格式字符串）
        updated_at: 更新时间（ISO格式字符串）
    """
    name: str
    config: dict[str, Any]
    created_at: str
    updated_at: str


class TemplateManager:
    """配置模板管理器
    
    负责管理条码生成器的配置模板，支持以下功能：
    - 保存模板为JSON文件
    - 加载已保存的模板
    - 删除模板
    - 列出所有可用模板
    - 获取默认模板
    
    模板文件格式：
    {
        "name": "模板名称",
        "version": "1.0",
        "created_at": "ISO时间戳",
        "updated_at": "ISO时间戳",
        "config": {
            "dpi": 300,
            "width_mm": 37.29,
            ...
        }
    }
    """
    
    TEMPLATE_VERSION = "1.0"
    TEMPLATE_EXTENSION = ".json"
    
    # 默认模板配置（无附加码，符合GS1标准的推荐设置）
    DEFAULT_CONFIG = {
        "dpi": 1200,
        "width_mm": 32.5,
        "height_mm": 22.6,
        "width_px": None,
        "height_px": None,
        "lock_aspect_ratio": True,
        "color_mode": "BITMAP",
        "foreground_color": [0, 0, 0],
        "background_color": [255, 255, 255],
        "font_family": "Arial",
        "font_size": 125,
        "letter_spacing": 4.0,
        "isbn_text_offset_y": 4,
        "digits_offset_y": 3,
        "text_alignment": "center",
        "show_quiet_zone_indicator": True  # 默认显示静区标记
    }
    
    # 2位附加码默认配置
    ADDON_2_CONFIG = {
        "dpi": 1200,
        "width_mm": 32.5,
        "height_mm": 22.6,
        "width_px": None,
        "height_px": None,
        "lock_aspect_ratio": True,
        "color_mode": "BITMAP",
        "foreground_color": [0, 0, 0],
        "background_color": [255, 255, 255],
        "font_family": "Arial",
        "font_size": 98,
        "letter_spacing": 4.0,
        "isbn_text_offset_y": 4,
        "digits_offset_y": 3,
        "text_alignment": "center",
        "show_quiet_zone_indicator": True
    }
    
    def __init__(self, templates_dir: str):
        """初始化模板管理器
        
        Args:
            templates_dir: 模板存储目录路径
        """
        self.templates_dir = templates_dir
        self._ensure_templates_dir()
    
    def _ensure_templates_dir(self) -> None:
        """确保模板目录存在"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)
    
    def _get_template_path(self, name: str) -> str:
        """获取模板文件路径
        
        Args:
            name: 模板名称
            
        Returns:
            str: 模板文件完整路径
        """
        # 清理文件名，移除不安全字符
        safe_name = self._sanitize_filename(name)
        return os.path.join(self.templates_dir, f"{safe_name}{self.TEMPLATE_EXTENSION}")
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除不安全字符
        
        Args:
            name: 原始名称
            
        Returns:
            str: 安全的文件名
        """
        # 移除或替换不安全的文件名字符
        unsafe_chars = '<>:"/\\|?*'
        result = name
        for char in unsafe_chars:
            result = result.replace(char, '_')
        return result.strip()
    
    def save_template(self, name: str, config: dict[str, Any]) -> None:
        """保存模板为JSON文件
        
        Args:
            name: 模板名称
            config: 配置字典，包含所有渲染参数
            
        Raises:
            ValueError: 如果模板名称为空
            IOError: 如果文件写入失败
        """
        if not name or not name.strip():
            raise ValueError("模板名称不能为空")
        
        name = name.strip()
        template_path = self._get_template_path(name)
        
        # 检查是否是更新现有模板
        now = datetime.now().isoformat()
        if os.path.exists(template_path):
            # 加载现有模板以保留创建时间
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                created_at = existing.get('created_at', now)
            except (json.JSONDecodeError, IOError):
                created_at = now
        else:
            created_at = now
        
        # 构建模板数据
        template_data = {
            "name": name,
            "version": self.TEMPLATE_VERSION,
            "created_at": created_at,
            "updated_at": now,
            "config": self._serialize_config(config)
        }
        
        # 写入文件
        self._ensure_templates_dir()
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    def load_template(self, name: str) -> dict[str, Any]:
        """加载模板配置
        
        Args:
            name: 模板名称
            
        Returns:
            dict[str, Any]: 配置字典
            
        Raises:
            FileNotFoundError: 如果模板不存在
            ValueError: 如果模板文件格式无效
        """
        template_path = self._get_template_path(name)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板 '{name}' 不存在")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"模板文件格式无效: {e}")
        
        if 'config' not in template_data:
            raise ValueError("模板文件缺少 'config' 字段")
        
        return self._deserialize_config(template_data['config'])
    
    def delete_template(self, name: str) -> None:
        """删除模板
        
        Args:
            name: 模板名称
            
        Raises:
            FileNotFoundError: 如果模板不存在
        """
        template_path = self._get_template_path(name)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板 '{name}' 不存在")
        
        os.remove(template_path)
    
    def list_templates(self) -> list[str]:
        """列出所有可用模板名称
        
        Returns:
            list[str]: 模板名称列表
        """
        if not os.path.exists(self.templates_dir):
            return []
        
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(self.TEMPLATE_EXTENSION):
                # 从文件中读取实际模板名称
                filepath = os.path.join(self.templates_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'name' in data:
                            templates.append(data['name'])
                        else:
                            # 如果没有name字段，使用文件名
                            templates.append(filename[:-len(self.TEMPLATE_EXTENSION)])
                except (json.JSONDecodeError, IOError):
                    # 跳过无效的模板文件
                    continue
        
        return sorted(templates)
    
    def get_default_template(self) -> dict[str, Any]:
        """获取默认模板配置
        
        返回符合GS1标准的推荐设置。
        
        Returns:
            dict[str, Any]: 默认配置字典
        """
        return self.DEFAULT_CONFIG.copy()
    
    def get_addon_2_template(self) -> dict[str, Any]:
        """获取2位附加码默认模板配置
        
        Returns:
            dict[str, Any]: 2位附加码配置字典
        """
        return self.ADDON_2_CONFIG.copy()
    
    def get_template_info(self, name: str) -> Optional[Template]:
        """获取模板完整信息
        
        Args:
            name: 模板名称
            
        Returns:
            Template: 模板对象，如果不存在返回None
        """
        template_path = self._get_template_path(name)
        
        if not os.path.exists(template_path):
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Template(
                name=data.get('name', name),
                config=self._deserialize_config(data.get('config', {})),
                created_at=data.get('created_at', ''),
                updated_at=data.get('updated_at', '')
            )
        except (json.JSONDecodeError, IOError):
            return None
    
    def template_exists(self, name: str) -> bool:
        """检查模板是否存在
        
        Args:
            name: 模板名称
            
        Returns:
            bool: 模板是否存在
        """
        template_path = self._get_template_path(name)
        return os.path.exists(template_path)
    
    def _serialize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """序列化配置为可JSON化的格式
        
        将元组转换为列表，枚举转换为字符串等。
        
        Args:
            config: 原始配置字典
            
        Returns:
            dict[str, Any]: 可JSON序列化的配置
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, tuple):
                result[key] = list(value)
            elif hasattr(value, 'value'):  # 枚举类型
                result[key] = value.value
            elif hasattr(value, 'name'):  # 枚举类型（另一种方式）
                result[key] = value.name
            else:
                result[key] = value
        return result
    
    def _deserialize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """反序列化配置
        
        将列表转换回元组（对于颜色值）。
        
        Args:
            config: JSON加载的配置字典
            
        Returns:
            dict[str, Any]: 反序列化后的配置
        """
        result = {}
        for key, value in config.items():
            if key in ('foreground_color', 'background_color') and isinstance(value, list):
                result[key] = tuple(value)
            else:
                result[key] = value
        return result
