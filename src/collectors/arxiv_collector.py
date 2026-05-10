"""
arXiv 论文采集器 - 使用 requests + xml 解析
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.utils.config import config

ARXIV_API = "http://export.arxiv.org/api/query"

class ArxivCollector:
    def __init__(self) -> None:
        cfg = config.collection.get("arxiv", {})
        self.categories: List[str] = cfg.get("categories", ["cs.AR"])
        self.max_results: int = cfg.get("max_results", 50)
        self.days_back: int = cfg.get("days_back", 7)
    
    def fetch(self) -> List[Dict[str, str]]:
        query = " OR ".join([f"cat:{c}" for c in self.categories])
        params = {
            "search_query": query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        
        resp = requests.get(ARXIV_API, params=params, timeout=60)
        resp.raise_for_status()
        
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        
        results = []
        cutoff = datetime.now() - timedelta(days=self.days_back)
        
        for entry in root.findall("atom:entry", ns):
            published_str = self._get_text(entry, "atom:published", ns)
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            if published.replace(tzinfo=None) < cutoff:
                continue
            
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
            cat = entry.find("arxiv:primary_category", ns)
            category = cat.get("term", "") if cat is not None else ""
            
            results.append({
                "id": self._get_text(entry, "atom:id", ns),
                "title": self._clean_text(self._get_text(entry, "atom:title", ns)),
                "abstract": self._clean_text(self._get_text(entry, "atom:summary", ns)),
                "authors": authors,
                "published": published.isoformat(),
                "pdf_url": self._get_text(entry, "atom:link", ns, attr="href", attr_val="type", attr_expected="application/pdf"),
                "source": "arxiv",
                "category": category,
            })
        
        return results
    
    def _get_text(self, elem, path, ns, attr=None, attr_val=None, attr_expected=None):
        found = elem.find(path, ns)
        if found is None:
            return ""
        if attr and attr_val and attr_expected:
            # 查找具有特定属性的 link
            for link in elem.findall(path, ns):
                if link.get(attr_val) == attr_expected:
                    return link.get(attr, "")
            return ""
        return found.text or ""
    
    def _clean_text(self, text: str) -> str:
        return " ".join(text.split())

if __name__ == "__main__":
    collector = ArxivCollector()
    papers = collector.fetch()
    print(f"Fetched {len(papers)} papers from arXiv")
    for p in papers[:3]:
        print(f"- {p['title'][:80]}... ({p['published'][:10]})")
