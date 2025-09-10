import importlib
import inspect
from pathlib import Path
from typing import Optional, Any
from flask import Blueprint
from loguru import logger

from wecom_responder.utils.consts import ROUTES
from wecom_responder.utils.config import config_manager


class BpLoader:
    def __init__(self, routes_dir: Path = ROUTES):
        self.routes_dir = routes_dir
        self.loaded_bps: dict[str, list[Blueprint]] = {}

    def _discover_modules(self) -> list[str]:
        """搜索所有包含bp的 module name"""
        module_names = []
        
        for item in self.routes_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # folder_name = item.name
                python_files = list(item.glob('*.py'))
                
                if python_files:
                    module_names.extend([f.stem for f in python_files if f.stem != '__init__'])
        
        return module_names
    
    def _load_module(self, module_name: str) -> Optional[Any]:
        """加载bp模块"""
        module_path = f"wecom_responder.routes.{module_name}.{module_name}"
        try:
            module = importlib.import_module(module_path)
            return module
        except ImportError as e:
            logger.error(f"无法导入模块 {module_path}: {e}")
            return None
    
    def _get_bps_from_module(self, module: Any) -> list[Blueprint]:
        """从模块中提取bp对象"""
        bps = []
        
        for var_name, obj in inspect.getmembers(module):
            if isinstance(obj, Blueprint):
                bps.append(obj)

        return bps
    
    def _is_module_enabled(self, module_name: str) -> bool:
        """检查bp是否启用"""
        # 延迟导入配置管理器
        return config_manager.is_module_enabled(module_name)
    
    def get_bps_by_module_name(self, module_name: str) -> list[Blueprint]:
        """加载指定模块的所有bp"""
        if module_name in self.loaded_bps:
            return self.loaded_bps[module_name]
        
        bps = []
        module = self._load_module(module_name)
        if module:
            bps = self._get_bps_from_module(module)

        self.loaded_bps[module_name] = bps

        return bps
    
    def load_all_enabled_bps(self) -> dict[str, list[Blueprint]]:
        """加载所有启用的bp"""
        for module_name in self._discover_modules():
            if self._is_module_enabled(module_name):
                self.get_bps_by_module_name(module_name)

        return self.loaded_bps
    
    # def get_bp_by_name(self, module_name: str, bp_name: str = None) -> Optional[Blueprint]:
    #     """根据名称获取特定bp"""
    #     if module_name not in self.loaded_bps:
    #         self.load_bps_from_module(module_name)
    #
    #     bps = self.loaded_bps.get(module_name, [])
    #
    #     if bp_name:
    #         for bp in bps:
    #             if bp.name == bp_name:
    #                 return bp
    #         return None
    #     else:
    #         return bps[0] if bps else None
    
    # def list_available_bps(self) -> dict[str, dict[str, Any]]:
    #     """列出所有可用的bp信息"""
    #     module_names = self._discover_modules()
    #     result = {}
    #
    #     for module_name in module_names:
    #         enabled = self._is_module_enabled(module_name)
    #         result[module_name] = {
    #             "enabled": enabled,
    #             "module_name": module_name,
    #             "loaded": module_name in self.loaded_bps
    #         }
    #
    #     return result

# 全局bp加载器实例
bp_loader = BpLoader()