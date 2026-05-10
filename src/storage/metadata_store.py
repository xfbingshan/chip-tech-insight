"""
元数据存储：JSON Lines 格式，保存完整的文档与评估结果
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.utils.config import config

class MetadataStore:
    def __init__(self):
        self.data_dir = Path("./data/documents")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.data_dir / "index.jsonl"
    
    def save(self, doc: Dict):
        """保存文档到索引"""
        with open(self.index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    
    def load_all(self) -> List[Dict[str, Any]]:
        """加载所有文档"""
        docs = []
        idx_path = Path(self.index_file)
        if not idx_path.exists():
            return docs
        
        with open(idx_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))
        return docs
    
    def load_recent(self, days: int = 7) -> List[Dict[str, Any]]:
        """加载最近几天的文档"""
        all_docs = self.load_all()
        cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
        
        recent = []
        for doc in all_docs:
            published = doc.get("published", "")
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                if dt.replace(tzinfo=None) >= cutoff:
                    recent.append(doc)
            except:
                recent.append(doc)
        return recent
    
    def get_by_category(self, category: str, days: int = 30) -> List[Dict]:
        """按技术分类获取文档"""
        recent = self.load_recent(days)
        return [
            d for d in recent
            if d.get("assessment", {}).get("category", "").lower() == category.lower()
        ]
    
    def get_by_decision(self, decision: str, days: int = 30) -> List[Dict]:
        """按决策类型获取文档"""
        recent = self.load_recent(days)
        return [
            d for d in recent
            if d.get("assessment", {}).get("decision", "").lower() == decision.lower()
        ]
