"""News service — parses AUT news from ajou.uz/en/post/news."""

import re
import asyncio
from datetime import datetime
import httpx

BASE_URL = "https://ajou.uz"
NEWS_URL = f"{BASE_URL}/en/post/news?category=1"


def _clean(text: str) -> str:
    text = re.sub(r'&ndash;', '–', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _parse_news_list(html: str) -> list[dict]:
    """Parse news cards from the listing page."""
    items = []

    # Each card: <img src="/uploads/news/..."> + <h4>TITLE</h4> + date + link id
    # Pattern based on actual HTML structure
    cards = re.findall(
        r'href="/en/post/new\?id=(\d+)"[^>]*><h4>([^<]+)</h4>.*?'
        r'<i class="fa fa-calendar"></i>\s*<span>\s*([^<]+)</span>',
        html, re.DOTALL
    )
    for post_id, title, date_str in cards:
        image_match = re.search(rf'/uploads/news/[^"]*{post_id}[^"]*', html)
        image_url = f"{BASE_URL}{image_match.group(0)}" if image_match else ""

        # Parse date dd.mm.yyyy
        published_at = None
        try:
            published_at = datetime.strptime(date_str.strip(), "%d.%m.%Y")
        except ValueError:
            pass

        items.append({
            "external_id": int(post_id),
            "title": _clean(title),
            "url": f"{BASE_URL}/en/post/new?id={post_id}",
            "image_url": image_url,
            "published_at": published_at,
            "content": "",
        })

    return items


def _fetch_news_content(post_id: int) -> str:
    """Fetch full content of a single news post."""
    try:
        with httpx.Client(follow_redirects=True, timeout=10) as client:
            r = client.get(f"{BASE_URL}/en/post/new?id={post_id}")
            if r.status_code != 200:
                return ""
            # Extract main content
            content_match = re.search(
                r'<div[^>]*class="[^"]*singel-dashboard[^"]*"[^>]*>(.*?)</div>\s*</div>',
                r.text, re.DOTALL
            )
            if content_match:
                text = re.sub(r'<[^>]+>', ' ', content_match.group(1))
                return _clean(text)
    except Exception:
        pass
    return ""


def fetch_news(limit: int = 20) -> list[dict]:
    """Fetch news list from ajou.uz. Returns list of news dicts."""
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            r = client.get(NEWS_URL)
            if r.status_code != 200:
                return []
            items = _parse_news_list(r.text)
            # Deduplicate by external_id
            seen = set()
            unique = []
            for item in items:
                if item["external_id"] not in seen:
                    seen.add(item["external_id"])
                    unique.append(item)
            return unique[:limit]
    except Exception as e:
        print(f"News fetch error: {e}")
        return []


async def fetch_news_async(limit: int = 20) -> list[dict]:
    return await asyncio.to_thread(fetch_news, limit)
