"""
Pytest 共享 fixtures
"""
import sys
from pathlib import Path
import tempfile
import pytest

# 确保项目根目录在路径中
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def temp_dir():
    """提供临时目录，测试结束后自动清理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_doc():
    """提供一篇示例文档，包含足够芯片关键词以通过 MOCK 初筛"""
    return {
        "id": "test-001",
        "title": "A Novel Chip Architecture for AI Inference",
        "abstract": "This processor paper proposes a new chip architecture for GPU inference that improves energy efficiency by 40% using SRAM cache optimization.",
        "authors": ["Alice", "Bob"],
        "published": "2026-05-01T00:00:00",
        "pdf_url": "https://arxiv.org/pdf/2605.00001",
        "source": "arxiv",
        "category": "cs.AR",
    }


@pytest.fixture
def sample_screened_doc(sample_doc):
    """提供一篇已初筛的示例文档"""
    return {
        **sample_doc,
        "assessment": {
            "relevance": 8.5,
            "category": "Architecture",
            "summary": "新型 AI 推理芯片架构",
            "trl": 5,
            "value_score": 9.0,
            "decision": "Deep Dive",
            "key_players": ["Intel", "MIT"],
            "keywords": ["ai", "architecture", "inference"],
        },
        "structured_summary": {
            "innovations": ["能效提升40%", "新型数据流设计"],
            "metrics": {"performance": "40% better", "power": "30% lower"},
            "limitations": ["仅仿真验证"],
            "implications": ["适合边缘计算场景"],
            "technical_depth": "Deep",
        },
        "screened_at": "2026-05-10T12:00:00",
    }
