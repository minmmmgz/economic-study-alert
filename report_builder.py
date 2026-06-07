"""Build the morning economic study report."""

from __future__ import annotations

from datetime import date
import re

import pandas as pd


REPORT_WORD_REPLACEMENTS = {
    "순매수": "수급 유입",
    "순매도": "수급 이탈",
    "매수": "투자행동",
    "매도": "투자행동",
    "목표가": "가격 전망 표현",
    "저평가": "가치평가 표현",
    "고평가": "가치평가 표현",
}

NEWS_SOURCE_SUFFIXES = [
    "KB Think",
    "뉴스핌",
    "초이스경제",
    "머니투데이",
    "TradingKey",
    "연합인포맥스",
    "뉴스투데이",
    "연합뉴스",
    "연합뉴스TV",
    "지디넷코리아",
    "조선비즈",
    "Chosunbiz",
    "글로벌이코노믹",
    "Counterpoint Research",
    "MBC 뉴스",
    "v.daum.net",
    "국민일보",
    "에너지안전신문",
    "경상일보",
    "MSN",
    "hidomin.com",
    "경향신문",
    "MTN 머니투데이방송",
]

ADVICE_LIKE_TITLE_WORDS = [
    "사면",
    "손해",
    "매수",
    "매도",
    "살 때",
    "주식 살",
    "기회일까",
    "조정의 시작",
    "목표가",
    "저평가",
    "고평가",
]
NOTE_UNHELPFUL_TITLE_WORDS = ["운명", "어디로", "쇼크"]


def _fmt_value(value, unit: str) -> str:
    if isinstance(value, str):
        return value
    if unit == "%":
        return f"{value:.2f}%"
    return f"{value:,.2f} {unit}".strip()


def _fmt_change_pct(value) -> str:
    if isinstance(value, str):
        return value
    return f"{value}%"


def _display_change_text(row) -> str:
    if row.get("category") == "금리" or row.get("key") == "us_10y":
        change = row.get("change")
        if isinstance(change, str):
            return f"전일 대비 {change}"
        bp = change * 100
        return f"전일 대비 {change:+.2f}%p, {bp:+.0f}bp"
    return f"전일 대비 {_fmt_change_pct(row.get('change_pct'))}"


def _published_date(value) -> str:
    if value is None or str(value).strip() == "":
        return "날짜 확인 필요"
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return "날짜 확인 필요"
    return parsed.strftime("%Y-%m-%d")


def _top_news(news_df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    if news_df.empty:
        return news_df
    sorted_news = news_df.copy()
    sorted_news["_published_dt"] = pd.to_datetime(sorted_news["published"], errors="coerce", utc=True)
    sorted_news = sorted_news.sort_values("_published_dt", ascending=False, na_position="last")
    rows = []
    for _, row in sorted_news.iterrows():
        title = str(row["title"])
        if any(word in title for word in ADVICE_LIKE_TITLE_WORDS + NOTE_UNHELPFUL_TITLE_WORDS):
            continue
        rows.append(row)
        if len(rows) >= limit:
            break
    if not rows:
        return news_df.head(limit)
    return pd.DataFrame(rows)


def _short_title(title: str, max_length: int = 62) -> str:
    cleaned = re.sub(r"https?://\S+", "", str(title))
    for source in NEWS_SOURCE_SUFFIXES:
        cleaned = re.sub(rf"\s*-\s*{re.escape(source)}\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("|", "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if "." in cleaned and len(cleaned) > max_length:
        first_sentence = cleaned.split(".", 1)[0].strip()
        if 18 <= len(first_sentence) <= max_length:
            return first_sentence
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 1].rstrip() + "…"


def _sanitize_report_text(text: str) -> str:
    sanitized = text
    for source, replacement in REPORT_WORD_REPLACEMENTS.items():
        sanitized = sanitized.replace(source, replacement)
    return sanitized


def _natural_sentence(text: str) -> str:
    value = str(text).strip()
    if not value or value == "확인 필요":
        return "확인 필요합니다."
    if value.endswith(("습니다.", "입니다.", "합니다.", "요.", "?")):
        return value
    if value.endswith("연결됨"):
        return value[:-3] + "연결되기 때문입니다."
    if value.endswith("민감함"):
        return value[:-3] + "민감하기 때문입니다."
    return value.rstrip(".") + "입니다."


def _watchlist_section(watchlist: pd.DataFrame, sectors: pd.DataFrame) -> list[str]:
    lines = ["4. 관심 종목별 확인 포인트", ""]
    sector_map = sectors.set_index("sector").to_dict("index")
    active_watchlist = watchlist[watchlist["active"].astype(str) == "1"]
    if active_watchlist.empty:
        return lines + ["활성화된 관심 종목이 없습니다. watchlist.csv를 확인해 주세요.", ""]

    for _, stock in active_watchlist.iterrows():
        sector = sector_map.get(stock["sector"], {})
        lines.extend(
            [
                f"[{stock['name']} / {sector.get('sector_name', stock['sector'])}]",
                f"왜 보는가: {_natural_sentence(sector.get('why_watch', '확인 필요'))}",
                f"관련 키워드: {sector.get('default_keywords', '확인 필요')}",
                f"종목별 추가 키워드: {stock.get('extra_keywords', '확인 필요')}",
                f"오늘 질문: {sector.get('study_question', '이 뉴스가 실제 지표와 연결되는지 확인할 필요가 있는가?')}",
                "",
            ]
        )
    return lines


def build_report(
    target_date: date,
    indicators: pd.DataFrame,
    news_df: pd.DataFrame,
    candidates: pd.DataFrame,
    watchlist: pd.DataFrame,
    sectors: pd.DataFrame,
    output_path,
) -> str:
    lines = [
        "[오늘의 경제 공부 알림]",
        f"기준일: {target_date.isoformat()}",
        "",
        "목적: 투자 판단이 아니라 경제 흐름 공부입니다.",
        "읽는 법: 단정하지 말고 원인을 나누어 확인합니다.",
        "",
        "1. 오늘의 핵심 지표 변화",
        "",
    ]

    for _, row in indicators.iterrows():
        lines.append(
            f"* {row['name_kr']} / {_fmt_value(row['latest'], row['unit'])} / {_display_change_text(row)} / {row['direction']}"
        )
        lines.append(f"  - 왜 보는가: {row['why_watch']}")
    lines.extend(["", "2. 지표를 이렇게 해석해볼 수 있음", ""])

    for _, row in indicators.iterrows():
        lines.append(f"* {row['name_kr']}: {row['interpretation']}")
    lines.extend(["", "3. 오늘의 주요 뉴스 후보", ""])

    top_news = _top_news(news_df, 10)
    if top_news.empty:
        lines.append("* 뉴스 데이터 없음: Google News RSS 연결 상태 또는 키워드 설정을 확인해 주세요.")
    else:
        lines.append("링크는 data/daily_news_raw CSV에 저장했습니다. 노트에는 제목과 이슈만 옮겨 적으면 됩니다.")
        lines.append("")
        for _, news in top_news.iterrows():
            title = _sanitize_report_text(_short_title(str(news["title"])))
            published = _published_date(news.get("published", ""))
            lines.append(f"* [{news['keyword_group']} / {published}] {title}")
    lines.append("")

    lines.extend(_watchlist_section(watchlist, sectors))
    lines.extend(["5. 오늘의 신규 키워드 후보", ""])

    if candidates.empty:
        lines.append("오늘은 새로 추가할 만한 키워드 후보가 뚜렷하지 않습니다.")
    else:
        if "keyword_type" not in candidates.columns:
            candidates = candidates.assign(keyword_type="경제/산업 키워드")
        for keyword_type in ["경제/산업 키워드", "기업/종목 키워드", "인물/기타 키워드"]:
            group = candidates[candidates["keyword_type"] == keyword_type].head(5)
            if group.empty:
                continue
            lines.append(f"[{keyword_type}]")
            for _, row in group.iterrows():
                lines.append(f"* {row['keyword']} / count: {row['count']} / importance_score: {row['importance_score']}")
            lines.append("")
    lines.extend(
        [
            "",
            "6. 네이버증권에서 직접 확인할 것",
            "",
            "* 코스피 외국인·기관 수급",
            "* 코스닥 외국인·기관 수급",
            "* 관심 종목 투자자별 매매동향",
            "* 관심 종목 뉴스/공시",
            "* 업종별 등락률",
            "* 거래대금 상위 업종",
            "",
            "7. 오늘 노트에 적을 질문",
            "",
            "* 미국 10년물 금리는 왜 움직였는가?",
            "* 환율 변화는 달러 강세 때문인가, 원화 약세 때문인가?",
            "* 유가 변화는 수요 요인인가, 공급 요인인가?",
            "* 관심 종목 뉴스는 실제 실적과 연결되는가, 기대감에 가까운가?",
            "* 오늘 뉴스에서 반복되는 단어는 어떤 지표와 연결되는가?",
            "",
            "8. 오늘의 한줄 정리 빈칸",
            "",
            "오늘 시장은 ______ 때문에 ______ 흐름을 보였다.",
            "",
            "※ 지표값은 yfinance 기준이며, 실제 거래소·증권사 표시값과 차이가 있을 수 있습니다.",
        ]
    )

    report = _sanitize_report_text("\n".join(lines))
    output_path.write_text(report, encoding="utf-8")
    return report
