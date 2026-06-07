"""Morning economic study alert entry point."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from zoneinfo import ZoneInfo

from config import DATA_DIR, DEFAULT_MAX_NEWS, OUTPUTS_DIR, ensure_directories, load_email_config
from indicators import collect_indicators
from keyword_manager import (
    build_keyword_bank,
    ensure_default_files,
    extract_keyword_candidates,
    load_sector_templates,
    load_watchlist,
)
from news_collector import collect_news
from notifier import send_email
from report_builder import build_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="경제 공부용 아침 알림 자동화")
    parser.add_argument("--date", help="리포트 기준일. 예: 2026-06-08")
    parser.add_argument("--no-send", action="store_true", help="이메일을 보내지 않고 콘솔 출력과 파일 저장만 합니다.")
    parser.add_argument("--max-news", type=int, default=DEFAULT_MAX_NEWS, help="키워드별 최대 뉴스 수")
    return parser.parse_args()


def parse_target_date(value: str | None) -> date:
    if not value:
        return datetime.now(ZoneInfo("Asia/Seoul")).date()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        print("날짜 형식이 올바르지 않아 오늘 날짜로 실행합니다. 예: --date 2026-06-08")
        return datetime.now(ZoneInfo("Asia/Seoul")).date()


def main() -> None:
    args = parse_args()
    target_date = parse_target_date(args.date)
    date_text = target_date.isoformat()

    ensure_directories()
    ensure_default_files()

    indicator_path = DATA_DIR / f"economic_market_indicators_{date_text}.csv"
    news_path = DATA_DIR / f"daily_news_raw_{date_text}.csv"
    candidates_path = DATA_DIR / f"keyword_candidates_{date_text}.csv"
    report_path = OUTPUTS_DIR / f"daily_economic_study_note_{date_text}.txt"

    keyword_bank = build_keyword_bank()
    watchlist = load_watchlist()
    sectors = load_sector_templates()

    indicators = collect_indicators(target_date, indicator_path)
    news_df = collect_news(keyword_bank, target_date, news_path, max_news=args.max_news)
    candidates = extract_keyword_candidates(news_df, keyword_bank, target_date, candidates_path)
    report = build_report(target_date, indicators, news_df, candidates, watchlist, sectors, report_path)

    print(report)
    print(f"\n저장 완료: {report_path}")

    if args.no_send:
        print("no-send 옵션으로 이메일 발송은 건너뛰었습니다.")
        return

    subject = f"[경제 공부 알림] {date_text}"
    sent = send_email(subject, report, load_email_config())
    if sent:
        print("이메일 발송 완료")


if __name__ == "__main__":
    main()
