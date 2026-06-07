"""Create keyword files and extract new study keyword candidates."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date

import pandas as pd

from config import CORE_KEYWORDS, KEYWORD_BANK_PATH, SECTOR_TEMPLATES_PATH, WATCHLIST_PATH


DEFAULT_WATCHLIST = [
    ["삼성전자", "005930.KS", "KR", "semiconductor", "HBM;AI반도체", "삼성전자 HBM;DRAM 가격;엔비디아", 1],
    ["현대차", "005380.KS", "KR", "auto", "하이브리드;전기차", "현대차 미국 판매;자동차 관세;전기차 보조금", 1],
    ["두산에너빌리티", "034020.KS", "KR", "energy_power", "원전;전력망", "두산에너빌리티 원전;SMR;가스터빈;전력망 투자", 1],
]

DEFAULT_SECTORS = [
    ["semiconductor", "반도체", "반도체 업황;HBM;DRAM 가격;NAND 가격;엔비디아;TSMC;마이크론", "한국 증시와 수출에 영향이 크고 AI 투자 흐름과 연결됨", "반도체 뉴스는 AI 수요 때문인가 메모리 가격 때문인가?"],
    ["auto", "자동차", "자동차 판매;미국 자동차 수요;하이브리드;전기차 보조금;자동차 관세;환율", "수출·환율·소비금리와 연결됨", "자동차 뉴스는 환율 때문인가 소비 수요 때문인가?"],
    ["energy_power", "원전/전력", "원전;SMR;전력망;가스터빈;AI 데이터센터 전력;전력기기", "정책·전력수요·수주 사이클과 연결됨", "전력 뉴스는 정책 기대인가 실제 수주 가능성인가?"],
    ["shipbuilding", "조선", "LNG선;선가;수주;해양플랜트;방산;운임", "글로벌 경기·에너지 운송·수주 사이클과 연결됨", "조선 뉴스는 선가 상승인가 수주 증가인가?"],
    ["battery", "2차전지", "전기차 수요;리튬 가격;배터리 소재;ESS;IRA;전기차 보조금", "전기차 수요와 원자재 가격에 민감함", "배터리 뉴스는 수요 회복인가 원가 변화인가?"],
    ["bank", "은행", "기준금리;순이자마진;가계대출;부동산 PF;연체율", "금리와 경기 안정성에 민감함", "은행 뉴스는 금리 효과인가 부실 위험인가?"],
    ["bio", "바이오", "임상;FDA;신약 승인;기술수출;금리", "금리와 개별 이벤트에 민감함", "바이오 뉴스는 실적보다 이벤트 기대인가?"],
]

STOPWORDS = {
    "관련", "오늘", "이번", "지난", "속보", "단독", "종합", "기자", "뉴스", "경제", "시장", "증시", "한국",
    "미국", "상승", "하락", "전망", "가능성", "확인", "필요", "올해", "내년", "억원", "조원", "대비",
    "최고", "최대", "속도", "유지", "규모", "수준", "복귀", "예상", "상회", "부합", "감소", "영향", "급격히",
    "성장", "논의", "이후", "이전", "장관", "대통령", "부총리", "대표", "회장",
    "어디로", "지금", "사면", "손해", "운명", "가른다", "거의", "확정", "만에", "부터", "보다",
    "미국서", "내일", "회동", "견고", "추락", "강세", "약세", "쇼크", "급등", "급락", "돌파",
    "THE", "AND", "FOR", "WITH", "FROM", "DAUM", "NET", "WWW", "COM", "CO", "KR", "V", "SK",
    "머니투데이", "연합뉴스", "연합뉴스TV", "한국경제", "매일경제", "연합인포맥스", "뉴스핌", "뉴스투데이",
    "글로벌이코노믹", "동아일보", "전자신문", "조선비즈", "CHOSUNBIZ", "지디넷코리아", "초이스경제",
    "더구루", "서울경제", "이데일리", "아시아경제", "파이낸셜뉴스", "헤럴드경제", "뉴시스",
    "비즈니스포스트", "전기신문",
    "TRADINGKEY", "COUNTERPOINT", "RESEARCH", "MBC", "TV", "KB", "THINK", "V.DAUM.NET",
}

IMPORTANT_WORDS = {
    "금리", "국채", "연준", "CPI", "PCE", "물가", "고용", "실업률", "환율", "달러", "유가", "OPEC",
    "관세", "수출", "반도체", "HBM", "DRAM", "전기차", "원전", "SMR", "전력망", "데이터센터", "중국",
    "PMI", "수주", "실적",
}

WEAK_STANDALONE_WORDS = {
    "젠슨", "황", "일론", "머스크", "팀", "쿡", "제롬", "파월", "도널드", "트럼프",
}

PERSON_KEYWORDS = {
    "최태원", "젠슨 황", "일론 머스크", "제롬 파월", "도널드 트럼프", "팀 쿡",
}

COMPANY_HINTS = {
    "삼성", "삼성전자", "현대차", "기아", "두산에너빌리티", "SK하이닉스", "엔비디아", "TSMC",
    "마이크론", "LG에너지솔루션", "HD현대중공업",
}

MEDIA_SOURCES = {
    "KB Think", "뉴스핌", "초이스경제", "머니투데이", "TradingKey", "연합인포맥스", "뉴스투데이",
    "연합뉴스", "지디넷코리아", "연합뉴스TV", "조선비즈", "Chosunbiz", "글로벌이코노믹",
    "Counterpoint Research", "MBC 뉴스", "한국경제", "매일경제", "전자신문", "동아일보",
    "더구루", "서울경제", "이데일리", "아시아경제", "파이낸셜뉴스", "헤럴드경제", "뉴시스",
    "비즈니스포스트", "전기신문",
}


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(";") if part.strip()]


def _remove_media_source(title: str) -> str:
    cleaned = str(title)
    for source in MEDIA_SOURCES:
        cleaned = cleaned.replace(source, " ")
    return re.sub(r"\s+", " ", cleaned)


def ensure_default_files() -> None:
    if not WATCHLIST_PATH.exists():
        pd.DataFrame(
            DEFAULT_WATCHLIST,
            columns=["name", "ticker", "market", "sector", "theme", "extra_keywords", "active"],
        ).to_csv(WATCHLIST_PATH, index=False, encoding="utf-8-sig")

    if not SECTOR_TEMPLATES_PATH.exists():
        pd.DataFrame(
            DEFAULT_SECTORS,
            columns=["sector", "sector_name", "default_keywords", "why_watch", "study_question"],
        ).to_csv(SECTOR_TEMPLATES_PATH, index=False, encoding="utf-8-sig")

    if not KEYWORD_BANK_PATH.exists():
        pd.DataFrame(CORE_KEYWORDS, columns=["keyword_group", "query", "type", "active"]).to_csv(
            KEYWORD_BANK_PATH, index=False, encoding="utf-8-sig"
        )


def load_watchlist() -> pd.DataFrame:
    return pd.read_csv(WATCHLIST_PATH).fillna("")


def load_sector_templates() -> pd.DataFrame:
    return pd.read_csv(SECTOR_TEMPLATES_PATH).fillna("")


def build_keyword_bank() -> pd.DataFrame:
    keyword_bank = pd.read_csv(KEYWORD_BANK_PATH).fillna("")
    watchlist = load_watchlist()
    sectors = load_sector_templates().set_index("sector")

    generated_rows = []
    active_watchlist = watchlist[watchlist["active"].astype(str) == "1"]
    for _, stock in active_watchlist.iterrows():
        sector = stock["sector"]
        if sector in sectors.index:
            for keyword in _split_semicolon(sectors.loc[sector, "default_keywords"]):
                generated_rows.append({"keyword_group": sectors.loc[sector, "sector_name"], "query": keyword, "type": "sector", "active": 1})
        for keyword in _split_semicolon(stock["extra_keywords"]):
            generated_rows.append({"keyword_group": stock["name"], "query": keyword, "type": "watchlist", "active": 1})

    combined = pd.concat([keyword_bank, pd.DataFrame(generated_rows)], ignore_index=True)
    combined = combined.drop_duplicates(subset=["keyword_group", "query", "type"]).reset_index(drop=True)
    return combined


def _existing_keyword_tokens(keyword_bank: pd.DataFrame) -> tuple[set[str], str]:
    text = " ".join(keyword_bank["query"].astype(str).tolist())
    upper_text = text.upper()
    return set(re.findall(r"[가-힣A-Za-z0-9]+", upper_text)), upper_text


def _importance_score(word: str, count: int) -> int:
    score = count
    if word.upper() in {w.upper() for w in IMPORTANT_WORDS}:
        score += 5
    if any(important.upper() in word.upper() for important in IMPORTANT_WORDS):
        score += 2
    if count >= 4:
        score += 2
    if _keyword_type(word) == "인물/기타":
        score -= 2
    return min(score, 10)


def _keyword_type(word: str) -> str:
    upper_word = word.upper()
    if word in PERSON_KEYWORDS:
        return "인물/기타"
    if any(hint.upper() in upper_word for hint in COMPANY_HINTS):
        return "기업/종목 키워드"
    if any(important.upper() in upper_word for important in IMPORTANT_WORDS):
        return "경제/산업 키워드"
    return "인물/기타" if len(word) <= 3 and re.fullmatch(r"[가-힣]+", word) else "경제/산업 키워드"


def _normalize_word(word: str) -> str:
    return word.upper() if re.fullmatch(r"[A-Za-z0-9]+", word) else word


def _is_noise_word(word: str, existing: set[str], existing_text: str) -> bool:
    normalized = _normalize_word(word)
    if len(normalized) < 2:
        return True
    if re.fullmatch(r"\d+년|\d+월|\d+분기|\d+위|\d+배", normalized):
        return True
    if normalized in STOPWORDS or normalized.upper() in STOPWORDS:
        return True
    if normalized in WEAK_STANDALONE_WORDS or normalized.upper() in WEAK_STANDALONE_WORDS:
        return True
    if normalized.upper() in existing or normalized.upper() in existing_text:
        return True
    return False


def _is_noise_phrase(phrase: str, existing_text: str) -> bool:
    normalized = phrase.upper()
    if normalized in existing_text:
        return True
    if any(part in STOPWORDS or part.upper() in STOPWORDS for part in phrase.split()):
        return True
    return False


def extract_keyword_candidates(news_df: pd.DataFrame, keyword_bank: pd.DataFrame, target_date: date, output_path) -> pd.DataFrame:
    if news_df.empty:
        df = pd.DataFrame(columns=["date", "keyword", "count", "importance_score"])
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return df

    existing, existing_text = _existing_keyword_tokens(keyword_bank)

    filtered = []
    for title in news_df["title"].astype(str).tolist():
        words = re.findall(r"[가-힣A-Za-z0-9]+", _remove_media_source(title))
        normalized_words = []
        for word in words:
            normalized = _normalize_word(word)
            if not _is_noise_word(normalized, existing, existing_text):
                normalized_words.append(normalized)
                filtered.append(normalized)

        for first, second in zip(normalized_words, normalized_words[1:]):
            phrase = f"{first} {second}"
            if not _is_noise_phrase(phrase, existing_text):
                filtered.append(phrase)

    counter = Counter(filtered)
    rows = [
        {
            "date": target_date.isoformat(),
            "keyword": word,
            "count": count,
            "importance_score": _importance_score(word, count),
            "keyword_type": _keyword_type(word),
        }
        for word, count in counter.items()
        if count >= 2
    ]
    df = pd.DataFrame(rows, columns=["date", "keyword", "count", "importance_score", "keyword_type"])
    if not df.empty:
        df = df.sort_values(["importance_score", "count", "keyword"], ascending=[False, False, True]).reset_index(drop=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df
