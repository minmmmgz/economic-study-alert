"""Collect Google News RSS titles for study keywords."""

from __future__ import annotations

from datetime import date
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import feedparser
import pandas as pd


GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"


def collect_news(keyword_bank: pd.DataFrame, target_date: date, output_path, max_news: int = 10) -> pd.DataFrame:
    rows = []
    active_keywords = keyword_bank[keyword_bank["active"].astype(str) == "1"].copy()

    for _, item in active_keywords.iterrows():
        query = str(item["query"]).strip()
        if not query:
            continue
        try:
            url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
            request = Request(url, headers={"User-Agent": "Mozilla/5.0 economic-study-alert"})
            with urlopen(request, timeout=10) as response:
                feed = feedparser.parse(response.read())
            for entry in feed.entries[:max_news]:
                rows.append(
                    {
                        "date": target_date.isoformat(),
                        "keyword_group": item["keyword_group"],
                        "query": query,
                        "title": getattr(entry, "title", "데이터 없음"),
                        "published": getattr(entry, "published", "확인 필요"),
                        "link": getattr(entry, "link", ""),
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "date": target_date.isoformat(),
                    "keyword_group": item["keyword_group"],
                    "query": query,
                    "title": f"뉴스 수집 오류: {exc}",
                    "published": "확인 필요",
                    "link": "",
                }
            )

    df = pd.DataFrame(rows, columns=["date", "keyword_group", "query", "title", "published", "link"])
    if not df.empty:
        df = df.drop_duplicates(subset=["title"]).reset_index(drop=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df
