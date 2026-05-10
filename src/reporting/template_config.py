"""
PPT 模板配置加载器
支持从 settings.yaml 读取多套主题配色与字体参数
"""
from dataclasses import dataclass
from typing import Dict, List
from pptx.dml.color import RGBColor
from src.utils.config import config


@dataclass
class PPTTemplate:
    """PPT 主题配置"""
    name: str
    primary: RGBColor
    accent: RGBColor
    text: RGBColor
    light_bg: RGBColor
    white: RGBColor
    title_font_size: int
    section_font_size: int
    body_font_size: int
    slide_width: float
    slide_height: float


def _hex_to_rgb(hex_str: str) -> RGBColor:
    """将 #RRGGBB 字符串转为 RGBColor"""
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return RGBColor(r, g, b)


def load_template(name: str = None) -> PPTTemplate:
    """
    从 settings.yaml 加载指定 PPT 主题
    若配置缺失或主题不存在，回退到默认科技蓝
    """
    templates_cfg = config.reporting.get("templates", {})
    default_name = templates_cfg.get("default", "tech_blue")
    name = name or default_name

    theme_cfg = templates_cfg.get(name)
    if theme_cfg is None:
        # 回退到硬编码默认科技蓝
        return PPTTemplate(
            name="tech_blue_fallback",
            primary=RGBColor(0x1A, 0x23, 0x7E),
            accent=RGBColor(0x00, 0x96, 0xC7),
            text=RGBColor(0x33, 0x33, 0x33),
            light_bg=RGBColor(0xF0, 0xF4, 0xF8),
            white=RGBColor(0xFF, 0xFF, 0xFF),
            title_font_size=32,
            section_font_size=22,
            body_font_size=14,
            slide_width=13.333,
            slide_height=7.5,
        )

    return PPTTemplate(
        name=name,
        primary=_hex_to_rgb(theme_cfg.get("primary", "#1A237E")),
        accent=_hex_to_rgb(theme_cfg.get("accent", "#0096C7")),
        text=_hex_to_rgb(theme_cfg.get("text", "#333333")),
        light_bg=_hex_to_rgb(theme_cfg.get("light_bg", "#F0F4F8")),
        white=_hex_to_rgb(theme_cfg.get("white", "#FFFFFF")),
        title_font_size=theme_cfg.get("title_font_size", 32),
        section_font_size=theme_cfg.get("section_font_size", 22),
        body_font_size=theme_cfg.get("body_font_size", 14),
        slide_width=theme_cfg.get("slide_width", 13.333),
        slide_height=theme_cfg.get("slide_height", 7.5),
    )


def list_templates() -> List[str]:
    """返回可用主题名称列表（排除 'default' 键）"""
    templates_cfg = config.reporting.get("templates", {})
    return [k for k in templates_cfg.keys() if k != "default"]
