"""Project configuration and shared constants."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

WATCHLIST_PATH = DATA_DIR / "watchlist.csv"
SECTOR_TEMPLATES_PATH = DATA_DIR / "sector_templates.csv"
KEYWORD_BANK_PATH = DATA_DIR / "keyword_bank.csv"

DEFAULT_MAX_NEWS = 10


INDICATORS = [
    {
        "key": "nasdaq",
        "name_kr": "나스닥",
        "ticker": "^IXIC",
        "category": "미국 주식",
        "unit": "pt",
        "why_watch": "미국 성장주와 기술주 심리를 확인하기 위해 봅니다.",
        "study_question": "나스닥 변화는 기술주 심리 변화인가, 금리 변화와 함께 봐야 하는가?",
    },
    {
        "key": "sp500",
        "name_kr": "S&P500",
        "ticker": "^GSPC",
        "category": "미국 주식",
        "unit": "pt",
        "why_watch": "미국 시장 전체 분위기를 확인하기 위해 봅니다.",
        "study_question": "S&P500 흐름은 시장 전반의 변화인가, 일부 업종 영향이 큰가?",
    },
    {
        "key": "dow",
        "name_kr": "다우존스",
        "ticker": "^DJI",
        "category": "미국 주식",
        "unit": "pt",
        "why_watch": "전통 대형 산업주의 흐름을 확인하기 위해 봅니다.",
        "study_question": "다우존스 흐름은 경기 민감 업종의 변화와 연결되는가?",
    },
    {
        "key": "sox",
        "name_kr": "필라델피아 반도체지수",
        "ticker": "^SOX",
        "category": "반도체",
        "unit": "pt",
        "why_watch": "글로벌 반도체 업종 흐름을 확인하고, 한국 반도체 종목이 같은 방향으로 움직이는지 보기 위해 봅니다.",
        "study_question": "반도체 흐름은 AI 수요 때문인가, 메모리 가격 변화 때문인가?",
    },
    {
        "key": "us10y",
        "name_kr": "미국 10년물 국채금리",
        "ticker": "^TNX",
        "category": "금리",
        "unit": "%",
        "why_watch": "장기금리, 할인율, 자금조달 비용을 확인하기 위해 봅니다.",
        "study_question": "금리 변화는 물가 기대 때문인가, 경기 우려 때문인가?",
    },
    {
        "key": "usdkrw",
        "name_kr": "원/달러 환율",
        "ticker": "KRW=X",
        "category": "환율",
        "unit": "원",
        "why_watch": "한국시장 외국인 수급과 수출기업 환경을 확인하기 위해 봅니다.",
        "study_question": "환율 변화는 달러 강세 때문인가, 원화 약세 때문인가?",
    },
    {
        "key": "dxy",
        "name_kr": "달러인덱스",
        "ticker": "DX-Y.NYB",
        "category": "환율",
        "unit": "pt",
        "why_watch": "글로벌 달러 강세와 약세를 확인하기 위해 봅니다.",
        "study_question": "원/달러 환율 변화가 글로벌 달러 흐름과 같은 방향인가?",
    },
    {
        "key": "wti",
        "name_kr": "WTI 유가",
        "ticker": "CL=F",
        "category": "원자재",
        "unit": "달러",
        "why_watch": "물가, 에너지 비용, 경기 수요와 공급 충격을 확인하기 위해 봅니다.",
        "study_question": "유가 변화는 수요 요인인가, 공급 요인인가?",
    },
    {
        "key": "gold",
        "name_kr": "금",
        "ticker": "GC=F",
        "category": "원자재",
        "unit": "달러",
        "why_watch": "안전자산 선호와 실질금리 흐름을 확인하기 위해 봅니다.",
        "study_question": "금 가격 변화는 안전자산 선호 때문인가, 금리 변화 때문인가?",
    },
    {
        "key": "copper",
        "name_kr": "구리",
        "ticker": "HG=F",
        "category": "원자재",
        "unit": "달러",
        "why_watch": "제조업 경기, 중국 경기, 전력 인프라 수요를 확인하기 위해 봅니다.",
        "study_question": "구리 변화는 제조업 수요 때문인가, 중국 경기 기대 때문인가?",
    },
]


CORE_KEYWORDS = [
    {"keyword_group": "미국 금리", "query": "미국 10년물 국채금리 OR 연준 OR 기준금리", "type": "core", "active": 1},
    {"keyword_group": "미국 물가", "query": "미국 CPI OR PCE 물가 OR 인플레이션", "type": "core", "active": 1},
    {"keyword_group": "미국 고용", "query": "미국 고용지표 OR 실업률 OR 비농업고용", "type": "core", "active": 1},
    {"keyword_group": "환율", "query": "원달러 환율 OR 달러인덱스 OR 원화", "type": "core", "active": 1},
    {"keyword_group": "유가", "query": "WTI 유가 OR 국제유가 OR OPEC", "type": "core", "active": 1},
    {"keyword_group": "한국 수급", "query": "외국인 순매수 OR 기관 순매수 OR 코스피 수급", "type": "core", "active": 1},
]


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_email_config() -> dict[str, str | int | None]:
    load_dotenv(BASE_DIR / ".env")
    port = os.getenv("SMTP_PORT", "587")
    try:
        smtp_port: int | None = int(port)
    except ValueError:
        smtp_port = None
    return {
        "sender": os.getenv("EMAIL_SENDER"),
        "password": os.getenv("EMAIL_PASSWORD"),
        "receiver": os.getenv("EMAIL_RECEIVER"),
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": smtp_port,
    }
