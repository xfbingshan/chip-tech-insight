"""
RSSCollector 单元测试
"""
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.collectors.rss_collector import RSSCollector


class TestRSSCollector:
    def test_init_reads_config(self):
        """初始化时正确读取配置"""
        collector = RSSCollector()
        assert isinstance(collector.sources, list)

    @patch("src.collectors.rss_collector.requests.get")
    def test_fetch_parses_rss20(self, mock_get):
        """能正确解析 RSS 2.0 feed"""
        rss_xml = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Intel Releases New Chip</title>
      <description>Intel announced a breakthrough in 3nm process.</description>
      <link>https://newsroom.intel.com/123</link>
      <pubDate>Mon, 09 May 2026 12:00:00 GMT</pubDate>
      <guid>https://newsroom.intel.com/123</guid>
    </item>
  </channel>
</rss>"""
        mock_resp = MagicMock()
        mock_resp.content = rss_xml.encode("utf-8")
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector = RSSCollector()
        collector.sources = [{"name": "Intel Newsroom", "url": "https://test.example.com/rss"}]
        collector.max_entries = 10
        collector.days_back = 30
        docs = collector.fetch()

        assert len(docs) == 1
        assert docs[0]["title"] == "Intel Releases New Chip"
        assert docs[0]["source"] == "rss:Intel Newsroom"

    @patch("src.collectors.rss_collector.requests.get")
    def test_fetch_parses_atom_feed(self, mock_get):
        """能正确解析 Atom feed"""
        atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>tag:example.com,2026:123</id>
    <title>MIT Research on Photonics</title>
    <summary>New photonics advance.</summary>
    <published>2026-05-09T12:00:00Z</published>
    <link href="https://example.com/123"/>
  </entry>
</feed>"""
        mock_resp = MagicMock()
        mock_resp.content = atom_xml.encode("utf-8")
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector = RSSCollector()
        collector.sources = [{"name": "MIT News", "url": "https://test.example.com/atom"}]
        collector.max_entries = 10
        collector.days_back = 30
        docs = collector.fetch()

        assert len(docs) == 1
        assert docs[0]["title"] == "MIT Research on Photonics"

    @patch("src.collectors.rss_collector.requests.get")
    def test_fetch_skips_old_entries(self, mock_get):
        """跳过过期的 RSS 条目"""
        rss_xml = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Old News</title>
      <description>Too old.</description>
      <link>https://example.com/old</link>
      <pubDate>Mon, 01 Jan 2020 12:00:00 GMT</pubDate>
      <guid>https://example.com/old</guid>
    </item>
  </channel>
</rss>"""
        mock_resp = MagicMock()
        mock_resp.content = rss_xml.encode("utf-8")
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        collector = RSSCollector()
        collector.sources = [{"name": "Test", "url": "https://test.example.com/rss"}]
        collector.max_entries = 10
        collector.days_back = 7
        docs = collector.fetch()

        assert len(docs) == 0

    @patch("src.collectors.rss_collector.requests.get")
    def test_fetch_graceful_on_error(self, mock_get):
        """某个源失败时优雅跳过"""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        collector = RSSCollector()
        collector.sources = [{"name": "Broken", "url": "https://broken.example.com"}]
        docs = collector.fetch()

        assert docs == []
