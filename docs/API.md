# 模块接口契约文档

## 1. Collectors 接口

### 基类约定
所有采集器必须实现：
```python
def fetch(self) -> List[Dict]:
    """
    返回原始文档列表。
    每个文档必须包含字段：id, title, abstract, authors, published, pdf_url, source, category
    """
```

### ArxivCollector
```python
class ArxivCollector:
    def __init__(self):
        # 从 config.collection.arxiv 读取 categories, max_results, days_back
        ...
    
    def fetch(self) -> List[Dict]:
        # 调用 arXiv API (http://export.arxiv.org/api/query)
        # 返回 Atom XML 解析后的文档列表
        ...
```

### RSSCollector
```python
class RSSCollector:
    def __init__(self):
        # 从 config.collection.rss 读取 sources, max_entries
        ...
    
    def fetch(self) -> List[Dict]:
        # 解析 RSS 2.0 / Atom feed
        # 处理多种日期格式和时区
        ...
```

### BlogScraperCollector
```python
class BlogScraperCollector:
    def __init__(self):
        # 从 config.collection.blogs 读取博客列表
        ...
    
    def fetch(self) -> List[Dict]:
        # 通过 HTTP GET 获取 HTML
        # 支持自定义正则规则和通用自动提取
        # timeout=10s，快速失败
        ...
```

---

## 2. Agents 接口

### ScreenerAgent
```python
class ScreenerAgent:
    def screen(self, doc: Dict) -> Optional[Dict]:
        """
        对单篇文档进行初筛。
        输入：Raw Document
        输出：带 assessment 字段的 Document，或 None（被过滤）
        """
    
    def batch_screen(self, docs: List[Dict]) -> List[Dict]:
        """批量初筛，内部调用 screen()"""
```

**assessment 输出结构**：
```python
{
    "relevance": float,        # 0-10
    "category": str,           # Architecture/EDA/Process/...
    "summary": str,
    "trl": int,                # 1-9
    "value_score": float,      # 0-10
    "decision": str,           # Deep Dive / Flash Brief / Ignore
    "key_players": List[str],  # 机构名称列表
    "keywords": List[str],
}
```

### SummarizerAgent
```python
class SummarizerAgent:
    def summarize(self, doc: Dict) -> Dict:
        """
        对通过初筛的文档生成结构化摘要。
        输入：带 assessment 的 Document
        输出：增加 structured_summary 字段的 Document
        """
```

### InsightGeneratorAgent
```python
class InsightGeneratorAgent:
    def generate_flash(self, docs: List[Dict]) -> Dict:
        """基于多篇文献生成技术快讯内容"""
    
    def generate_deep_dive(self, docs: List[Dict]) -> Dict:
        """基于多篇文献生成深度洞察内容"""
```

---

## 3. Storage 接口

### VectorStore
```python
class VectorStore:
    def add(self, doc: Dict) -> bool:
        """
        添加文档到向量库，自动去重。
        返回：True（新文档）/ False（重复文档）
        """
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义检索，返回最相似的文档"""
    
    def get_recent(self, days: int = 7) -> List[Dict]:
        """获取最近添加的文档"""
```

### MetadataStore
```python
class MetadataStore:
    def save(self, doc: Dict):
        """追加保存文档到 JSONL 索引"""
    
    def load_all(self) -> List[Dict]:
        """加载所有文档"""
    
    def load_recent(self, days: int = 7) -> List[Dict]:
        """加载最近 N 天的文档"""
    
    def get_by_category(self, category: str, days: int = 30) -> List[Dict]:
        """按技术分类获取"""
    
    def get_by_decision(self, decision: str, days: int = 30) -> List[Dict]:
        """按决策类型获取"""
```

---

## 4. Reporting 接口

### ReportGenerator
```python
class ReportGenerator:
    def generate_flash_brief(self, content: Dict, docs: List[Dict]) -> str:
        """
        生成技术快讯报告。
        返回：生成的 Markdown 文件路径
        """
    
    def generate_deep_dive(self, content: Dict, docs: List[Dict]) -> str:
        """
        生成深度洞察报告。
        返回：生成的 Markdown 文件路径
        """
    
    def generate_org_brief(self, org_name: str, docs: List[Dict]) -> str:
        """
        生成机构动态报告。
        返回：生成的 Markdown 文件路径
        """
```

---

## 5. Pipeline 接口

### InsightPipeline
```python
class InsightPipeline:
    def __init__(self):
        # 初始化所有采集器、Agent、存储、报告生成器
        ...
    
    def run(self, dry_run: bool = False) -> List[Dict]:
        """
        执行完整工作流。
        
        Args:
            dry_run: True 时不保存数据，仅打印流程
        
        Returns:
            报告列表，每项包含 type, topic, path
        """
```

**内部阶段**：
1. `_collect()` → `List[Dict]`（Raw Docs）
2. `screener.batch_screen()` → `List[Dict]`（Screened Docs）
3. `summarizer.summarize()` + `vector_store.add()` + `metadata_store.save()` → `List[Dict]`（Processed Docs）
4. `_cluster()` → `Dict[str, List[Dict]]`（技术方向簇）
5. `_cluster_by_org()` → `Dict[str, List[Dict]]`（机构维度簇）
6. 报告生成 → `List[Dict]`（报告元数据）
