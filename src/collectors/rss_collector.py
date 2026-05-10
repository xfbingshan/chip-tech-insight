"""
RSS 技术新闻采集器 - 使用 requests + xml 解析
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
from src.utils.config import config


class RSSCollector:
    def __init__(self) -> None:
        cfg = config.collection.get("rss", {})
        self.sources: List[Dict[str, str]] = cfg.get("sources", [])
        self.max_entries: int = cfg.get("max_entries", 30)

    def fetch(self) -> List[Dict[str, str]]:
        results = []
        cutoff = datetime.now().replace(
            tzinfo=__import__("datetime").timezone.utc
        ) - timedelta(days=config.collection.get("arxiv", {}).get("days_back", 7))

        for source in self.sources:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.9",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                }
                resp = requests.get(source["url"], timeout=30, headers=headers)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)

                # RSS 2.0 or Atom
                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")[: self.max_entries]
                    for item in items:
                        published = self._parse_rss_date(
                            self._get_text(item, "pubDate")
                        )
                        if published:
                            if published.tzinfo is None:
                                published = published.replace(
                                    tzinfo=__import__("datetime").timezone.utc
                                )
                            if published < cutoff:
                                continue

                        results.append(
                            {
                                "id": self._get_text(item, "guid")
                                or self._get_text(item, "link"),
                                "title": self._get_text(item, "title"),
                                "abstract": self._clean_html(
                                    self._get_text(item, "description")
                                ),
                                "authors": [],
                                "published": published.isoformat()
                                if published
                                else datetime.now().isoformat(),
                                "pdf_url": self._get_text(item, "link"),
                                "source": f"rss:{source['name']}",
                                "category": "news",
                            }
                        )
                else:
                    # Atom
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("atom:entry", ns)[: self.max_entries]:
                        published_str = self._get_atom_text(
                            entry, "atom:published", ns
                        ) or self._get_atom_text(entry, "atom:updated", ns)
                        try:
                            published = (
                                datetime.fromisoformat(
                                    published_str.replace("Z", "+00:00")
                                )
                                if published_str
                                else datetime.now(__import__("datetime").timezone.utc)
                            )
                        except (ValueError, TypeError):
                            published = datetime.now(
                                __import__("datetime").timezone.utc
                            )
                        if published < cutoff:
                            continue

                        results.append(
                            {
                                "id": self._get_atom_text(entry, "atom:id", ns),
                                "title": self._clean_html(
                                    self._get_atom_text(entry, "atom:title", ns)
                                ),
                                "abstract": self._clean_html(
                                    self._get_atom_text(entry, "atom:summary", ns)
                                ),
                                "authors": [],
                                "published": published.isoformat(),
                                "pdf_url": self._get_atom_link(entry, ns),
                                "source": f"rss:{source['name']}",
                                "category": "news",
                            }
                        )
            except (requests.exceptions.RequestException, ET.ParseError) as e:
                print(f"[RSS Error] {source['name']}: {e}")

        return results

    def _get_text(self, elem, tag):
        child = elem.find(tag)
        return child.text if child is not None else ""

    def _get_atom_text(self, elem, tag, ns):
        child = elem.find(tag, ns)
        return child.text if child is not None else ""

    def _get_atom_link(self, elem, ns):
        link = elem.find("atom:link", ns)
        return link.get("href", "") if link is not None else ""

    def _parse_rss_date(self, date_str: str) -> datetime:
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.now()

    def _clean_html(self, html: str) -> str:
        import re

        if not html:
            return ""
        text = re.sub(r"<[^>]+>", "", html)
        return " ".join(text.split())


if __name__ == "__main__":
    collector = RSSCollector()
    articles = collector.fetch()
    print(f"Fetched {len(articles)} articles from RSS")
    for a in articles[:3]:
        print(f"- {a['title'][:80]}... ({a['source']})")
