import json
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from wecom_responder.utils.consts import CONFIG_FILE


class ConfigManager:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self._config = {}
        self._load_main_config()

    def __getitem__(self, key):
        return self._config.get(key)

    def __setitem__(self, key, value):
        self._config[key] = value
        self._save_main_config()

    def _load_main_config(self):
        """加载主配置文件"""
        try:
            with self.config_path.open('r', encoding='utf8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"主配置文件 {self.config_path} 不存在")
            self._config = {"enabled_modules": {}, "module_params": {}}
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            self._config = {"enabled_modules": {}, "module_params": {}}
        except Exception as e:
            logger.error(f"加载主配置文件失败: {e}")
            self._config = {"enabled_modules": {}, "module_params": {}}

    def _save_main_config(self):
        """保存主配置文件"""
        try:
            with self.config_path.open('w', encoding='utf8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存主配置文件失败: {e}")

    def is_module_enabled(self, module_name: str) -> bool:
        """检查bp是否启用"""
        return self._config.get("enabled_modules", {}).get(module_name, False)
    
    def get_param(self, module_name: str) -> Dict[str, Any]:
        """获取bp配置"""
        return self._config.get("module_params", {}).get(module_name, {})
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

    def set_param(self, module_name: str, params: Dict[str, Any]):
        """设置bp配置"""
        if "module_params" not in self._config:
            self._config["module_params"] = {}
        self._config["module_params"][module_name] = params
        self._save_main_config()


# 全局配置管理器实例
config_manager = ConfigManager()
