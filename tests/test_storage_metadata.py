"""
MetadataStore 单元测试
"""

from pathlib import Path
from src.storage.metadata_store import MetadataStore


class TestMetadataStore:
    def test_save_and_load(self, temp_dir, sample_doc):
        """保存后能正确加载"""
        store = MetadataStore()
        store.data_dir = Path(temp_dir) / "documents"
        store.index_file = store.data_dir / "index.jsonl"
        store.data_dir.mkdir(parents=True, exist_ok=True)

        store.save(sample_doc)
        docs = store.load_all()
        assert len(docs) == 1
        assert docs[0]["id"] == sample_doc["id"]

    def test_load_all_empty(self, temp_dir):
        """空索引返回空列表"""
        store = MetadataStore()
        store.data_dir = Path(temp_dir) / "documents"
        store.index_file = store.data_dir / "index.jsonl"
        store.data_dir.mkdir(parents=True, exist_ok=True)

        docs = store.load_all()
        assert docs == []

    def test_multiple_saves(self, temp_dir, sample_doc):
        """多次保存应追加而非覆盖"""
        store = MetadataStore()
        store.data_dir = Path(temp_dir) / "documents"
        store.index_file = store.data_dir / "index.jsonl"
        store.data_dir.mkdir(parents=True, exist_ok=True)

        doc1 = {**sample_doc, "id": "doc-1"}
        doc2 = {**sample_doc, "id": "doc-2"}
        store.save(doc1)
        store.save(doc2)

        docs = store.load_all()
        assert len(docs) == 2
        assert docs[0]["id"] == "doc-1"
        assert docs[1]["id"] == "doc-2"

    def test_load_recent(self, temp_dir, sample_doc):
        """能按日期范围加载"""
        store = MetadataStore()
        store.data_dir = Path(temp_dir) / "documents"
        store.index_file = store.data_dir / "index.jsonl"
        store.data_dir.mkdir(parents=True, exist_ok=True)

        # 一篇今天的，一篇去年的
        today_doc = {**sample_doc, "published": "2026-05-10T00:00:00"}
        old_doc = {**sample_doc, "published": "2025-01-01T00:00:00", "id": "old"}
        store.save(today_doc)
        store.save(old_doc)

        recent = store.load_recent(days=30)
        assert len(recent) >= 1
        ids = [d["id"] for d in recent]
        assert "test-001" in ids
