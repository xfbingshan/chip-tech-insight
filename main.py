#!/usr/bin/env python3
"""
芯片技术洞察平台 - 主入口

Usage:
    python main.py              # 执行完整工作流
    python main.py --dry-run    # 仅运行不保存
"""
import argparse
import sys
from pathlib import Path

# 将项目根目录加入路径
project_root = str(Path(__file__).resolve().parent)
sys.path.insert(0, project_root)

from src.scheduler.pipeline import InsightPipeline

def main():
    parser = argparse.ArgumentParser(description="芯片技术洞察平台")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不保存数据")
    args = parser.parse_args()
    
    pipeline = InsightPipeline()
    pipeline.run(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
