"""
VectorStore 单元测试
"""

from pathlib import Path
from src.storage.vector_store import VectorStore


class TestVectorStore:
    def test_init_creates_directories(self, temp_dir):
        """初始化时创建必要的目录"""
        store = VectorStore()
        assert Path(store.path).exists()

    def test_add_new_document(self, temp_dir, sample_doc):
        """添加新文档应成功"""
        store = VectorStore()
        store.path = Path(temp_dir) / "vector_db"
        store.docs_file = store.path / "docs.jsonl"
        store.vocab_file = store.path / "vocab.json"
        store.idf_file = store.path / "idf.json"
        store.path.mkdir(parents=True, exist_ok=True)
        store.documents = []
        store.vocab = {}
        store.idf = {}

        result = store.add(sample_doc)
        assert result is True
        assert len(store.documents) == 1
        assert store.documents[0]["id"] == sample_doc["id"]

    def test_duplicate_document_rejected(self, temp_dir, sample_doc):
        """重复文档应被拒绝"""
        store = VectorStore()
        store.path = Path(temp_dir) / "vector_db"
        store.docs_file = store.path / "docs.jsonl"
        store.vocab_file = store.path / "vocab.json"
        store.idf_file = store.path / "idf.json"
        store.path.mkdir(parents=True, exist_ok=True)
        store.documents = []
        store.vocab = {}
        store.idf = {}

        store.add(sample_doc)
        result = store.add(sample_doc)
        assert result is False

    def test_search_returns_results(self, temp_dir, sample_doc):
        """语义检索应返回结果"""
        store = VectorStore()
        store.path = Path(temp_dir) / "vector_db"
        store.docs_file = store.path / "docs.jsonl"
        store.vocab_file = store.path / "vocab.json"
        store.idf_file = store.path / "idf.json"
        store.path.mkdir(parents=True, exist_ok=True)
        store.documents = []
        store.vocab = {}
        store.idf = {}

        store.add(sample_doc)
        results = store.search("chip architecture")
        assert len(results) >= 1
        assert results[0]["id"] == sample_doc["id"]

    def test_cosine_similarity_range(self, temp_dir):
        """余弦相似度应在 [0, 1] 范围内"""
        import numpy as np

        store = VectorStore()
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        sim = store._cosine_sim(a, b)
        assert 0.0 <= sim <= 1.0
        assert sim == 0.0  # 正交向量

        c = np.array([1.0, 0.0, 0.0])
        sim2 = store._cosine_sim(a, c)
        assert sim2 == 1.0  # 相同向量

    def test_tokenize_extracts_keywords(self, temp_dir):
        """分词应提取有效关键词"""
        store = VectorStore()
        tokens = store._tokenize(
            "This is a Test of CHIP design and artificial intelligence processing!"
        )
        assert "test" in tokens
        assert "chip" in tokens
        assert "design" in tokens
        assert "artificial" in tokens
        assert "intelligence" in tokens
        assert "processing" in tokens
        assert "is" not in tokens  # 太短被过滤
