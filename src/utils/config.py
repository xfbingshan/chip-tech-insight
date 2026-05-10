import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

class Config:
    def __init__(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self._cfg = yaml.safe_load(f)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Kimi Coding API 需要特定的 User-Agent
        self.openai_default_headers = {}
        if "api.kimi.com" in self.openai_base_url:
            self.openai_default_headers = {"User-Agent": "claude-code/0.1.0"}
    
    def get(self, key_path: str, default=None):
        keys = key_path.split(".")
        val = self._cfg
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
    
    @property
    def collection(self):
        return self._cfg.get("collection", {})
    
    @property
    def llm(self):
        return self._cfg.get("llm", {})
    
    @property
    def vector_store(self):
        return self._cfg.get("vector_store", {})
    
    @property
    def screening(self):
        return self._cfg.get("screening", {})
    
    @property
    def reporting(self):
        return self._cfg.get("reporting", {})
    
    @property
    def schedule(self):
        return self._cfg.get("schedule", {})

config = Config()
