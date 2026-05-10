"""
ArxivCollector 单元测试
"""
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.collectors.arxiv_collector import ArxivCollector


class TestArxivCollector:
    def test_init_reads_config(self):
        """初始化时正确读取配置"""
        collector = ArxivCollector()
        assert collector.max_results > 0
        assert len(collector.categories) > 0

    @patch("src.collectors.arxiv_collector.requests.get")
    def test_fetch_parses_atom_xml(self, mock_get):
        """能正确解析 arXiv Atom XML 响应"""
        # 构造模拟的 Atom XML 响应
        atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2605.00001</id>
    <title>Test Paper on Chip Architecture</title>
    <summary>A novel approach to chip design.</summary>
    <published>2026-05-09T00:00:00Z</published>
    <author><name>Alice</name></author>
    <link href="https://arxiv.org/pdf/2605.00001.pdf" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AR"/>
  </entry>
</feed>"""
        mock_resp = MagicMock()
        mock_resp.content = atom_xml.encode("utf-8")
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector = ArxivCollector()
        # 将 days_back 设为足够大以确保不过滤
        collector.days_back = 30
        docs = collector.fetch()

        assert len(docs) == 1
        assert docs[0]["title"] == "Test Paper on Chip Architecture"
        assert docs[0]["source"] == "arxiv"
        assert "pdf" in docs[0]["pdf_url"]

    @patch("src.collectors.arxiv_collector.requests.get")
    def test_fetch_filters_by_date(self, mock_get):
        """能按日期过滤旧论文"""
        atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2605.00001</id>
    <title>Old Paper</title>
    <summary>Too old.</summary>
    <published>2020-01-01T00:00:00Z</published>
    <author><name>Alice</name></author>
    <link href="https://arxiv.org/pdf/2605.00001.pdf" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AR"/>
  </entry>
</feed>"""
        mock_resp = MagicMock()
        mock_resp.content = atom_xml.encode("utf-8")
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector = ArxivCollector()
        collector.days_back = 7
        docs = collector.fetch()

        assert len(docs) == 0  # 论文太旧，应被过滤

    @patch("src.collectors.arxiv_collector.requests.get")
    def test_fetch_empty_response(self, mock_get):
        """空响应返回空列表"""
        atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"></feed>"""
        mock_resp = MagicMock()
        mock_resp.content = atom_xml.encode("utf-8")
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector = ArxivCollector()
        collector.days_back = 30
        docs = collector.fetch()
        assert docs == []
