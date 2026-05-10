"""
报告归档管理器
支持按日期归档、维护 JSON 索引、查询历史、自动清理
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.utils.config import config


class ArchiveManager:
    def __init__(self) -> None:
        self.archive_cfg = config.reporting.get("archive", {})
        self.enabled = self.archive_cfg.get("enabled", True)
        self.keep_days = self.archive_cfg.get("keep_days", 30)
        self.archive_by_date = self.archive_cfg.get("archive_by_date", True)

        index_path = self.archive_cfg.get(
            "index_file", "./data/reports/archive_index.json"
        )
        self.index_file = Path(index_path)
        self.index_file.parent.mkdir(parents=True, exist_ok=True)

        self.base_dir = Path(config.reporting.get("output_dir", "./data/reports"))

    def archive_reports(
        self, report_paths: List[str], run_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将报告归档到日期子目录，并更新索引
        返回归档记录
        """
        if not self.enabled:
            return {"archived": [], "skipped": report_paths}

        run_date = run_date or datetime.now().strftime("%Y-%m-%d")
        archive_dir = (
            self.base_dir / run_date if self.archive_by_date else self.base_dir
        )
        archive_dir.mkdir(parents=True, exist_ok=True)

        archived = []
        skipped = []

        for path_str in report_paths:
            src = Path(path_str)
            if not src.exists():
                skipped.append(str(src))
                continue

            dst = archive_dir / src.name
            # 如果已在目标目录，跳过移动
            if src.resolve() == dst.resolve():
                archived.append(str(dst))
                continue

            # 若目标已存在，覆盖
            shutil.move(str(src), str(dst))
            archived.append(str(dst))

        record = {
            "date": run_date,
            "timestamp": datetime.now().isoformat(),
            "reports": archived,
            "count": len(archived),
        }

        self._update_index(record)
        return {"archived": archived, "skipped": skipped, "record": record}

    def list_archives(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """按时间倒序列出归档记录"""
        index = self._load_index()
        records = index.get("records", [])

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            records = [
                r
                for r in records
                if datetime.fromisoformat(r.get("timestamp", "1970-01-01")) >= cutoff
            ]

        return sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)

    def get_archive(self, date: str) -> Optional[Dict[str, Any]]:
        """查询某一天的归档报告"""
        index = self._load_index()
        for record in index.get("records", []):
            if record.get("date") == date:
                return record
        return None

    def cleanup_old_reports(self) -> List[str]:
        """删除超过 keep_days 的归档目录及索引记录"""
        if not self.enabled or self.keep_days <= 0:
            return []

        cutoff = datetime.now() - timedelta(days=self.keep_days)
        index = self._load_index()
        records = index.get("records", [])

        removed_dirs = []
        new_records = []

        for record in records:
            record_time = datetime.fromisoformat(record.get("timestamp", "1970-01-01"))
            if record_time < cutoff:
                # 删除对应归档目录
                date_str = record.get("date", "")
                if date_str and self.archive_by_date:
                    old_dir = self.base_dir / date_str
                    if old_dir.exists() and old_dir.is_dir():
                        shutil.rmtree(old_dir)
                        removed_dirs.append(str(old_dir))
            else:
                new_records.append(record)

        index["records"] = new_records
        self._save_index(index)
        return removed_dirs

    def _load_index(self) -> Dict:
        """读取归档索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"records": []}

    def _save_index(self, index: Dict):
        """保存归档索引"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _update_index(self, record: Dict):
        """追加一条归档记录"""
        index = self._load_index()
        if "records" not in index:
            index["records"] = []

        # 若同一天已有记录，合并报告列表
        existing = None
        for r in index["records"]:
            if r.get("date") == record["date"]:
                existing = r
                break

        if existing:
            existing_reports = set(existing.get("reports", []))
            existing_reports.update(record.get("reports", []))
            existing["reports"] = sorted(existing_reports)
            existing["count"] = len(existing["reports"])
            existing["timestamp"] = record["timestamp"]
        else:
            index["records"].append(record)

        self._save_index(index)
