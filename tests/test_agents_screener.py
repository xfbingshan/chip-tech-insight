"""
ScreenerAgent 单元测试
"""

from src.agents.screener import ScreenerAgent


class TestScreenerAgent:
    def test_mock_screen_chip_related(self, sample_doc):
        """MOCK 模式能识别芯片相关文献"""
        agent = ScreenerAgent()
        result = agent._mock_screen(sample_doc)
        assert result is not None
        assert "assessment" in result
        assert result["assessment"]["relevance"] > 0

    def test_mock_screen_unrelated_returns_none(self):
        """MOCK 模式应过滤不相关文献"""
        agent = ScreenerAgent()
        unrelated = {
            "id": "test-002",
            "title": "Advances in Botany",
            "abstract": "This paper discusses plant genetics and photosynthesis mechanisms.",
            "authors": ["Alice"],
            "published": "2026-05-01T00:00:00",
            "pdf_url": "",
            "source": "arxiv",
            "category": "bio",
        }
        result = agent._mock_screen(unrelated)
        assert result is None

    def test_mock_screen_detects_intel(self):
        """能检测 Intel 关键词并提升价值分"""
        agent = ScreenerAgent()
        doc = {
            "id": "test-003",
            "title": "Intel New Chip Architecture",
            "abstract": "Intel proposes a breakthrough in 3nm processor technology with SRAM cache optimization for AI inference hardware.",
            "authors": ["Alice"],
            "published": "2026-05-01T00:00:00",
            "pdf_url": "",
            "source": "arxiv",
            "category": "cs.AR",
        }
        result = agent._mock_screen(doc)
        assert result is not None
        assert result["assessment"]["value_score"] >= result["assessment"]["relevance"]
        assert (
            "Intel" in result["assessment"]["key_players"]
            or "intel" in result["assessment"]["key_players"]
        )

    def test_mock_screen_categorizes_base_station(self):
        """能正确分类基站/RAN 相关文献"""
        agent = ScreenerAgent()
        doc = {
            "id": "test-004",
            "title": "5G Base Station RF Frontend Design",
            "abstract": "A novel mmWave beamforming system for base station transceivers using massive MIMO.",
            "authors": ["Alice"],
            "published": "2026-05-01T00:00:00",
            "pdf_url": "",
            "source": "arxiv",
            "category": "eess.SP",
        }
        result = agent._mock_screen(doc)
        assert result is not None
        assert result["assessment"]["category"] == "Base Station / RAN"

    def test_batch_screen_filters_and_keeps(self, sample_doc):
        """批量初筛应过滤低相关性并保留高相关性"""
        agent = ScreenerAgent()
        docs = [
            sample_doc,
            {
                "id": "test-005",
                "title": "Gardening Tips for Beginners",
                "abstract": "How to grow tomatoes in your backyard.",
                "authors": ["Alice"],
                "published": "2026-05-01T00:00:00",
                "pdf_url": "",
                "source": "rss",
                "category": "news",
            },
        ]
        results = agent.batch_screen(docs)
        assert len(results) == 1
        assert results[0]["id"] == sample_doc["id"]
