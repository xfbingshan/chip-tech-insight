"""
ReportGenerator 单元测试
"""

from pathlib import Path
from src.reporting.report_generator import ReportGenerator


class TestReportGenerator:
    def test_generate_flash_brief_creates_file(self, temp_dir, sample_doc):
        """生成技术快讯应创建 Markdown 文件"""
        gen = ReportGenerator()
        gen.output_dir = temp_dir

        content = {
            "技术名称": "Test Chip Architecture",
            "关键创新": ["创新点1", "创新点2"],
            "成熟度评估": {"等级": 5, "理由": "原型验证阶段"},
            "主要玩家": ["Intel", "MIT"],
            "一句话建议": "建议持续关注",
        }
        path = gen.generate_flash_brief(content, [sample_doc])

        assert Path(path).exists()
        assert path.endswith(".md")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        assert "Test Chip Architecture" in text
        assert "创新点1" in text

    def test_generate_deep_dive_creates_file(self, temp_dir, sample_doc):
        """生成深度洞察应创建 Markdown 文件"""
        gen = ReportGenerator()
        gen.output_dir = temp_dir

        content = {
            "封面标题": "Deep Dive Test",
            "核心结论": "这是一个测试",
            "背景与动机": "测试背景",
            "技术原理": "测试原理",
            "业界进展": ["里程碑1"],
            "竞争格局矩阵": [{"玩家": "A", "路线": "X"}],
            "优劣势分析": {
                "优势": ["强"],
                "劣势": ["弱"],
                "机会": ["多"],
                "威胁": ["少"],
            },
            "对芯片设计的启示": ["启示1"],
            "行动建议": {"短期": "做A", "中期": "做B", "长期": "做C"},
        }
        path = gen.generate_deep_dive(content, [sample_doc])

        assert Path(path).exists()
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        assert "Deep Dive Test" in text
        assert "里程碑1" in text

    def test_generate_org_brief_creates_file(self, temp_dir, sample_screened_doc):
        """生成机构动态应创建 Markdown 文件"""
        gen = ReportGenerator()
        gen.output_dir = temp_dir

        path = gen.generate_org_brief("Intel", [sample_screened_doc])

        assert Path(path).exists()
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        assert "Intel" in text
        assert "技术洞察" in text
        assert "Architecture" in text  # 涉及方向

    def test_safe_name_removes_special_chars(self, temp_dir):
        """文件名安全化处理应去除特殊字符"""
        gen = ReportGenerator()
        gen.output_dir = temp_dir

        name = gen._safe_name("Intel / NVIDIA 合作?")
        assert "/" not in name
        assert "?" not in name
        assert " " not in name
        assert name == "Intel_NVIDIA"

    def test_safe_name_handles_empty(self, temp_dir):
        """空名称应返回默认值"""
        gen = ReportGenerator()
        gen.output_dir = temp_dir

        name = gen._safe_name("?!@#")
        assert name == "report"
