"""
通用博客爬虫 - 针对无 RSS 的机构技术博客
通过正则/HTML 解析提取最新文章
"""
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from src.utils.config import config

class BlogScraperCollector:
    """
    通用博客爬虫，支持通过配置的正则规则从 HTML 中提取文章。
    """
    def __init__(self):
        self.blogs = config.collection.get("blogs", [])
        self.days_back = config.collection.get("arxiv", {}).get("days_back", 7)
    
    def fetch(self) -> List[Dict]:
        """爬取所有配置的博客"""
        results = []
        if not self.blogs:
            return results
        for blog in self.blogs:
            if not blog or not blog.get("url"):
                continue
            try:
                docs = self._scrape_blog(blog)
                print(f"  [Blog] {blog['name']}: {len(docs)} articles")
                results.extend(docs)
            except Exception as e:
                print(f"  [Blog Error] {blog.get('name', 'unknown')}: {e}")
        return results
    
    def _scrape_blog(self, blog: Dict) -> List[Dict]:
        """爬取单个博客"""
        url = blog["url"]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text
        
        # 使用博客自定义规则或通用规则
        item_pattern = blog.get("item_regex", None)
        title_group = blog.get("title_group", 1)
        link_group = blog.get("link_group", 2)
        date_group = blog.get("date_group", 3)
        summary_group = blog.get("summary_group", 4)
        max_entries = blog.get("max_entries", 10)
        
        if item_pattern:
            # 自定义正则模式
            pattern = re.compile(item_pattern, re.IGNORECASE | re.DOTALL)
            matches = pattern.findall(html)[:max_entries]
        else:
            # 通用模式：尝试匹配常见博客结构
            matches = self._generic_extract(html, max_entries)
        
        docs = []
        cutoff = datetime.now() - timedelta(days=self.days_back)
        
        for match in matches:
            if isinstance(match, tuple):
                title = match[title_group - 1] if title_group <= len(match) else ""
                link = match[link_group - 1] if link_group <= len(match) else ""
                date_str = match[date_group - 1] if date_group <= len(match) else ""
                summary = match[summary_group - 1] if summary_group <= len(match) else ""
            else:
                title = match
                link = ""
                date_str = ""
                summary = ""
            
            title = self._clean_text(title)
            summary = self._clean_text(summary)
            link = self._resolve_url(link, url)
            
            # 尝试解析日期
            published = self._parse_date(date_str) or datetime.now()
            if published < cutoff:
                continue
            
            docs.append({
                "id": link or f"{blog['name']}:{hash(title) & 0xFFFFFFFF}",
                "title": title,
                "abstract": summary or title,
                "authors": [],
                "published": published.isoformat(),
                "pdf_url": link,
                "source": f"blog:{blog['name']}",
                "category": blog.get("category", "news"),
            })
        
        return docs
    
    def _generic_extract(self, html: str, max_entries: int) -> list:
        """
        通用提取策略：尝试多种常见博客 HTML 模式
        返回元组列表 (title, link, date, summary)
        """
        results = []
        
        # 策略 1: 匹配 <article> 标签内的内容
        article_pattern = re.compile(r'<article[^>]*>(.*?)</article>', re.IGNORECASE | re.DOTALL)
        articles = article_pattern.findall(html)[:max_entries]
        for art in articles:
            title_match = re.search(r'<h[1-6][^>]*>.*?<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>.*?</h[1-6]>', art, re.IGNORECASE | re.DOTALL)
            if title_match:
                link = title_match.group(1)
                title = re.sub(r'<[^>]+>', '', title_match.group(2))
            else:
                title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', art, re.IGNORECASE | re.DOTALL)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)) if title_match else ""
                link = ""
            
            summary_match = re.search(r'<p[^>]*>(.*?)</p>', art, re.IGNORECASE | re.DOTALL)
            summary = re.sub(r'<[^>]+>', '', summary_match.group(1)) if summary_match else ""
            
            date_match = re.search(r'<time[^>]*>(.*?)</time>', art, re.IGNORECASE | re.DOTALL)
            date_str = re.sub(r'<[^>]+>', '', date_match.group(1)) if date_match else ""
            
            if title:
                results.append((title.strip(), link, date_str, summary.strip()))
        
        if results:
            return results[:max_entries]
        
        # 策略 2: 匹配常见的博客卡片/列表项
        card_pattern = re.compile(
            r'<(?:div|li)[^>]*class=["\'][^"\']*(?:post|entry|card|item|blog)[^"\']*["\'][^>]*>'
            r'.*?<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
            r'.*?<p[^>]*>(.*?)</p>'
            r'.*?</(?:div|li)>',
            re.IGNORECASE | re.DOTALL
        )
        matches = card_pattern.findall(html)
        for link, title, summary in matches[:max_entries]:
            results.append((
                re.sub(r'<[^>]+>', '', title).strip(),
                link,
                "",
                re.sub(r'<[^>]+>', '', summary).strip()
            ))
        
        return results[:max_entries]
    
    def _clean_text(self, text: str) -> str:
        """清理 HTML 实体和多余空白"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = " ".join(text.split())
        return text.strip()
    
    def _resolve_url(self, link: str, base_url: str) -> str:
        """将相对链接转为绝对链接"""
        if not link:
            return ""
        if link.startswith("http://") or link.startswith("https://"):
            return link
        from urllib.parse import urljoin
        return urljoin(base_url, link)
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析多种日期格式"""
        if not date_str:
            return None
        date_str = date_str.strip()
        formats = [
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%d %B %Y",
            "%d %b %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
