"""
轻量级向量存储 - 使用 numpy 实现 TF-IDF + 余弦相似度
替代 ChromaDB + sentence-transformers，零外部依赖
"""
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
from src.utils.config import config

class VectorStore:
    def __init__(self):
        cfg = config.vector_store
        self.path = Path(cfg.get("path", "./data/vector_db"))
        self.path.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = cfg.get("similarity_threshold", 0.85)
        
        self.docs_file = self.path / "docs.jsonl"
        self.vocab_file = self.path / "vocab.json"
        self.idf_file = self.path / "idf.json"
        
        self.vocab = self._load_json(self.vocab_file, {})
        self.idf = self._load_json(self.idf_file, {})
        self.documents = self._load_docs()
    
    def add(self, doc: Dict) -> bool:
        """添加文档，去重后入库"""
        doc_id = doc.get("id", "")
        text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
        
        # 计算向量
        vec = self._vectorize(text)
        
        # 去重检查
        if self._is_duplicate(vec):
            print(f"[Duplicate] Skipped: {doc.get('title', '')[:50]}...")
            return False
        
        # 存储
        record = {
            "id": doc_id,
            "vector": vec.tolist(),
            "metadata": {
                "title": doc.get("title", ""),
                "source": doc.get("source", ""),
                "published": doc.get("published", ""),
                "category": doc.get("assessment", {}).get("category", "Other"),
                "value_score": doc.get("assessment", {}).get("value_score", 0),
            }
        }
        
        self.documents.append(record)
        self._save_docs()
        return True
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """语义检索"""
        if not self.documents:
            return []
        
        q_vec = self._vectorize(query)
        scores = []
        for rec in self.documents:
            d_vec = np.array(rec["vector"])
            sim = self._cosine_sim(q_vec, d_vec)
            scores.append((sim, rec))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": rec["id"],
                "score": float(sim),
                "metadata": rec["metadata"],
            }
            for sim, rec in scores[:top_k]
        ]
    
    def get_recent(self, days: int = 7) -> List[Dict]:
        """获取最近文档（简单返回全部，上层按 published 过滤）"""
        return self.documents
    
    def _is_duplicate(self, vec: np.ndarray) -> bool:
        """检查是否重复"""
        if not self.documents:
            return False
        
        for rec in self.documents:
            d_vec = np.array(rec["vector"])
            sim = self._cosine_sim(vec, d_vec)
            if sim >= self.similarity_threshold:
                return True
        return False
    
    def _vectorize(self, text: str) -> np.ndarray:
        """TF-IDF 向量化"""
        tokens = self._tokenize(text)
        if not tokens:
            return np.zeros(len(self.vocab) or 1)
        
        # 动态扩展词汇表
        new_terms = set(tokens) - set(self.vocab.keys())
        if new_terms:
            for term in new_terms:
                self.vocab[term] = len(self.vocab)
            # 为新词初始化 idf=1（平滑）
            for term in new_terms:
                self.idf[term] = 1.0
            self._save_json(self.vocab_file, self.vocab)
            self._save_json(self.idf_file, self.idf)
            # 重新计算所有已有文档的向量（简单方案：仅更新新文档时扩展向量维度）
            # MVP 阶段：允许向量维度增长，旧向量补零
            for rec in self.documents:
                old_vec = np.array(rec["vector"])
                new_vec = np.zeros(len(self.vocab))
                new_vec[:len(old_vec)] = old_vec
                rec["vector"] = new_vec.tolist()
            self._save_docs()
        
        # 计算 TF
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        
        vec = np.zeros(len(self.vocab))
        for term, count in tf.items():
            idx = self.vocab.get(term)
            if idx is not None:
                idf_val = self.idf.get(term, 1.0)
                vec[idx] = count * idf_val
        
        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
    
    def _tokenize(self, text: str) -> List[str]:
        """简单英文分词"""
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = [t for t in text.split() if len(t) >= 3]
        return tokens
    
    def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        if len(a) != len(b):
            # 维度对齐
            max_len = max(len(a), len(b))
            a = np.pad(a, (0, max_len - len(a)))
            b = np.pad(b, (0, max_len - len(b)))
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
    
    def _load_docs(self) -> List[Dict]:
        docs = []
        if self.docs_file.exists():
            with open(self.docs_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        docs.append(json.loads(line))
        return docs
    
    def _save_docs(self):
        with open(self.docs_file, "w", encoding="utf-8") as f:
            for doc in self.documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    
    def _load_json(self, path: Path, default):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default
    
    def _save_json(self, path: Path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
