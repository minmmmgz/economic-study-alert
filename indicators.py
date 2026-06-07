"""Collect market indicators with yfinance."""

from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from config import INDICATORS


def _format_direction(change: float | None) -> str:
    if change is None:
        return "확인 필요"
    if change > 0:
        return "상승"
    if change < 0:
        return "하락"
    return "보합"


def _normalize_tnx(ticker: str, value: float | None) -> float | None:
    if ticker == "^TNX" and value is not None and value > 20:
        return value / 10
    return value


def _interpret_indicator(name: str, direction: str) -> str:
    if direction == "확인 필요":
        return f"{name} 데이터는 확인 필요합니다. 수치가 비어 있으면 거래 휴장, 지연, 수집 오류 가능성을 구분해야 합니다."
    if name == "미국 10년물 국채금리":
        if direction == "상승":
            return "금리 상승은 물가 부담, 국채 수급, 연준 기대 변화 중 무엇 때문인지 나누어 봅니다."
        if direction == "하락":
            return "금리 하락은 물가 안정 기대인지, 경기 둔화 우려인지 구분해 봅니다."
        return "금리가 보합이면 물가, 고용, 연준 발언을 함께 확인합니다."
    if name == "원/달러 환율":
        return "환율 변화가 달러 강세 때문인지, 원화 약세 때문인지 구분해 봅니다."
    if name == "WTI 유가":
        return "유가 변화는 수요, 공급, 산유국 정책, 중동 이슈를 나누어 봅니다."
    if name == "필라델피아 반도체지수":
        return "반도체 흐름은 AI 수요, 메모리 가격, 주요 기업 실적을 나누어 봅니다."
    if name == "금":
        return "금 가격은 안전자산 선호, 실질금리, 달러 흐름을 함께 봅니다."
    if name == "구리":
        return "구리는 제조업, 중국 경기, 전력 인프라 수요를 함께 봅니다."
    return f"{name} {direction}은 시장 심리 변화일 수 있습니다. 금리, 환율, 업종 흐름과 함께 봅니다."


def _empty_row(meta: dict) -> dict:
    return {
        **meta,
        "latest": "데이터 없음",
        "previous": "데이터 없음",
        "change": "확인 필요",
        "change_pct": "확인 필요",
        "direction": "확인 필요",
        "interpretation": _interpret_indicator(meta["name_kr"], "확인 필요"),
    }


def collect_indicators(target_date: date, output_path) -> pd.DataFrame:
    rows = []
    for meta in INDICATORS:
        try:
            hist = yf.Ticker(meta["ticker"]).history(period="7d", interval="1d", auto_adjust=False, timeout=10)
            hist = hist.dropna(subset=["Close"])
            if len(hist) < 2:
                rows.append(_empty_row(meta))
                continue

            latest = _normalize_tnx(meta["ticker"], float(hist["Close"].iloc[-1]))
            previous = _normalize_tnx(meta["ticker"], float(hist["Close"].iloc[-2]))
            if latest is None or previous in (None, 0):
                rows.append(_empty_row(meta))
                continue

            change = latest - previous
            change_pct = (change / previous) * 100
            direction = _format_direction(change)
            rows.append(
                {
                    **meta,
                    "latest": round(latest, 4),
                    "previous": round(previous, 4),
                    "change": round(change, 4),
                    "change_pct": round(change_pct, 2),
                    "direction": direction,
                    "interpretation": _interpret_indicator(meta["name_kr"], direction),
                }
            )
        except Exception as exc:
            row = _empty_row(meta)
            row["interpretation"] = f"데이터 수집 중 오류가 있어 확인 필요합니다. 네트워크 연결, 티커, 휴장 여부를 구분해서 확인해 주세요. 오류 요약: {type(exc).__name__}"
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df
