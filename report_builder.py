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


def _summary_change_text(row) -> str:
    if row.get("category") == "금리" or row.get("key") in {"us10y", "us_10y"}:
        change = row.get("change")
        if isinstance(change, str):
            return str(change)
        bp = change * 100
        return f"{change:+.2f}%p, {bp:+.0f}bp"

    change_pct = row.get("change_pct")
    if isinstance(change_pct, str):
        return change_pct
    return f"{change_pct:+.2f}%"


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


SUMMARY_INDICATORS = {
    "nasdaq": ("나스닥", "성장주·기술주 심리"),
    "sox": ("필라델피아 반도체지수", "글로벌 반도체 업종"),
    "us10y": ("미국 10년물 금리", "금리 부담"),
    "us_10y": ("미국 10년물 금리", "금리 부담"),
    "usdkrw": ("원/달러 환율", "외국인 수급·수출환경"),
    "wti": ("WTI 유가", "물가·에너지 비용"),
}


def _summary_indicator_lines(indicators: pd.DataFrame) -> list[str]:
    lines = []
    for key in ["nasdaq", "sox", "us10y", "us_10y", "usdkrw", "wti"]:
        matched = indicators[indicators["key"] == key]
        if matched.empty:
            continue
        row = matched.iloc[0]
        name, tag = SUMMARY_INDICATORS[key]
        lines.append(f"* {name}: {_summary_change_text(row)} {row['direction']} / {tag}")
    return lines


def _contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _summary_issues(news_df: pd.DataFrame, candidates: pd.DataFrame) -> list[str]:
    text_parts = []
    if not news_df.empty:
        text_parts.extend(news_df["title"].astype(str).tolist())
        text_parts.extend(news_df["keyword_group"].astype(str).tolist())
    if not candidates.empty:
        text_parts.extend(candidates["keyword"].astype(str).tolist())
    joined = " ".join(text_parts)

    issue_rules = [
        ("환율 흐름", ["환율", "원달러", "원·달러", "달러"]),
        ("반도체·HBM", ["반도체", "HBM", "D램", "DRAM", "메모리"]),
        ("전력망·수주", ["전력망", "수주", "전력", "원전", "SMR"]),
        ("유가·에너지 비용", ["유가", "WTI", "에너지", "OPEC"]),
        ("미국 금리·고용", ["금리", "국채", "고용", "비농업", "연준"]),
    ]
    issues = [label for label, words in issue_rules if _contains_any(joined, words)]
    return issues[:5] if issues else ["금리·환율 흐름", "주요 업종 뉴스", "관심 종목 이슈"]


def _summary_market_sentences(indicators: pd.DataFrame, issues: list[str]) -> list[str]:
    direction_by_key = {row["key"]: row["direction"] for _, row in indicators.iterrows()}
    nasdaq_direction = direction_by_key.get("nasdaq", "확인 필요")
    sox_direction = direction_by_key.get("sox", "확인 필요")
    rate_direction = direction_by_key.get("us10y", direction_by_key.get("us_10y", "확인 필요"))
    fx_direction = direction_by_key.get("usdkrw", "확인 필요")
    issue_text = ", ".join(issues[:3])

    return [
        f"오늘은 나스닥과 반도체지수가 {nasdaq_direction}/{sox_direction} 흐름을 보였고, 금리와 환율은 각각 {rate_direction}/{fx_direction}인지 확인해야 하는 날입니다.",
        f"뉴스와 키워드에서는 {issue_text} 이슈가 반복적으로 나타났습니다.",
        "따라서 오늘은 개별 종목보다 금리, 환율, 반도체 업황 기대가 서로 어떻게 연결되는지 공부해 봅니다.",
    ]


def _watchlist_summary_lines(watchlist: pd.DataFrame) -> list[str]:
    active_watchlist = watchlist[watchlist["active"].astype(str) == "1"]
    if active_watchlist.empty:
        return ["* 활성화된 관심 종목이 없습니다. watchlist.csv를 확인해 주세요."]

    lines = []
    for _, stock in active_watchlist.iterrows():
        sector = stock.get("sector", "")
        name = stock.get("name", "관심 종목")
        if sector == "semiconductor":
            point = "반도체지수 흐름과 HBM 기대 뉴스를 분리해서 보기"
        elif sector == "auto":
            point = "환율 변화가 수출환경과 소비수요에 어떻게 연결되는지 보기"
        elif sector == "energy_power":
            point = "전력망·수주 뉴스가 실제 수주 흐름으로 이어지는지 보기"
        elif sector == "battery":
            point = "전기차 수요와 원자재 가격 변화를 함께 보기"
        elif sector == "shipbuilding":
            point = "선가와 수주 뉴스가 업황 변화와 연결되는지 보기"
        elif sector == "bank":
            point = "금리 변화와 대출·건전성 이슈를 함께 보기"
        elif sector == "bio":
            point = "개별 이벤트가 업종 흐름과 구분되는지 보기"
        else:
            point = "오늘 뉴스가 실제 지표와 연결되는지 보기"
        lines.append(f"* {name}: {point}")
    return lines


def build_email_summary(
    target_date: date,
    indicators: pd.DataFrame,
    news_df: pd.DataFrame,
    candidates: pd.DataFrame,
    watchlist: pd.DataFrame,
) -> str:
    issues = _summary_issues(news_df, candidates)
    lines = [
        "[오늘의 경제 공부 알림]",
        f"기준일: {target_date.isoformat()}",
        "",
        "1. 오늘 시장 한줄 요약",
        "",
    ]
    lines.extend(f"* {sentence}" for sentence in _summary_market_sentences(indicators, issues))
    lines.extend(["", "2. 오늘 꼭 볼 지표 5개", ""])
    lines.extend(_summary_indicator_lines(indicators))
    lines.extend(["", "3. 오늘 반복 이슈", ""])
    lines.extend(f"* {issue}" for issue in issues[:5])
    lines.extend(["", "4. 관심 종목 확인 포인트", ""])
    lines.extend(_watchlist_summary_lines(watchlist))
    lines.extend(
        [
            "",
            "5. 오늘 노트 질문",
            "",
            "* 오늘 시장 부담은 금리 상승, 환율 상승, 반도체 업종 약세 중 무엇의 영향이 더 컸는가?",
            "* 뉴스에서 반복된 이슈가 실제 지표와 수급에도 반영되고 있는가?",
            "",
            "6. 한줄 정리",
            "",
            "오늘 시장은 ______ 때문에 ______ 흐름을 보였다.",
            "",
            "※ 상세 지표, 뉴스 제목, 키워드 후보는 TXT/CSV에 저장되었습니다.",
        ]
    )
    return _sanitize_report_text("\n".join(lines))


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
        "1. 오늘의 핵심 지표 변화",
        "",
    ]

    for _, row in indicators.iterrows():
        lines.append(
            f"* {row['name_kr']} / {_fmt_value(row['latest'], row['unit'])} / {_display_change_text(row)} / {row['direction']}"
        )
        lines.append(f"  {row['why_watch']}")
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
