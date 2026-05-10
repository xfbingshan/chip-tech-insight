"""
Config 模块单元测试
"""
import os
import pytest
from src.utils.config import Config


class TestConfig:
    def test_config_loads_yaml(self):
        """验证配置能正确加载 YAML 文件"""
        cfg = Config()
        assert cfg._cfg is not None
        assert "collection" in cfg._cfg
        assert "llm" in cfg._cfg

    def test_config_get_existing_key(self):
        """获取存在的配置项"""
        cfg = Config()
        val = cfg.get("collection.arxiv.max_results")
        assert isinstance(val, int)
        assert val > 0

    def test_config_get_missing_key_returns_default(self):
        """获取不存在的配置项返回默认值"""
        cfg = Config()
        assert cfg.get("nonexistent.key", "default") == "default"
        assert cfg.get("nonexistent.key") is None

    def test_config_properties(self):
        """验证便捷属性访问"""
        cfg = Config()
        assert isinstance(cfg.collection, dict)
        assert isinstance(cfg.llm, dict)
        assert isinstance(cfg.vector_store, dict)
        assert isinstance(cfg.screening, dict)
        assert isinstance(cfg.reporting, dict)

    def test_openai_api_key_from_env(self, monkeypatch):
        """验证从环境变量读取 API Key"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://test.example.com")
        cfg = Config()
        assert cfg.openai_api_key == "sk-test-key"
        assert cfg.openai_base_url == "https://test.example.com"
