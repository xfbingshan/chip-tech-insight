import os
from typing import Any, Dict, Optional
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

class Config:
    def __init__(self) -> None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self._cfg: Dict[str, Any] = yaml.safe_load(f)
        
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Kimi Coding API 需要特定的 User-Agent
        self.openai_default_headers: Dict[str, str] = {}
        if "api.kimi.com" in self.openai_base_url:
            self.openai_default_headers = {"User-Agent": "claude-code/0.1.0"}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        val = self._cfg
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
    
    @property
    def collection(self) -> Dict[str, Any]:
        return self._cfg.get("collection", {})
    
    @property
    def llm(self) -> Dict[str, Any]:
        return self._cfg.get("llm", {})
    
    @property
    def vector_store(self) -> Dict[str, Any]:
        return self._cfg.get("vector_store", {})
    
    @property
    def screening(self) -> Dict[str, Any]:
        return self._cfg.get("screening", {})
    
    @property
    def reporting(self) -> Dict[str, Any]:
        return self._cfg.get("reporting", {})
    
    @property
    def schedule(self) -> Dict[str, Any]:
        return self._cfg.get("schedule", {})

config = Config()
