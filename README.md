# economic-study-alert

매일 아침 경제 지표와 주요 경제 뉴스 제목을 모아 이메일로 보내는 경제 공부용 알림 프로젝트입니다.

이 프로젝트는 투자 추천 도구가 아닙니다. 목적은 매수/매도 판단이 아니라, 지표를 왜 보는지 이해하고 굿노트나 노션에 공부 노트를 적을 질문을 만드는 것입니다.

## 설치 방법

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## `.env` 설정 방법

`.env.example`을 참고해서 프로젝트 루트에 `.env` 파일을 만듭니다.

```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver_email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

민감한 비밀번호는 코드에 직접 쓰지 말고 반드시 `.env`에만 보관하세요.

## Gmail 앱 비밀번호 주의

Gmail을 사용할 때는 일반 로그인 비밀번호가 아니라 앱 비밀번호를 사용하는 것이 안전합니다. Google 계정에서 2단계 인증을 켠 뒤 앱 비밀번호를 발급하고, 그 값을 `EMAIL_PASSWORD`에 넣어 주세요.

## 실행 방법

기본 실행은 리포트를 만들고 이메일을 발송합니다.

```bash
python main.py
```

테스트 실행은 이메일을 보내지 않고 콘솔 출력과 파일 저장만 합니다.

```bash
python main.py --no-send
```

날짜와 뉴스 개수를 지정할 수도 있습니다.

```bash
python main.py --date 2026-06-08 --max-news 10 --no-send
```

## 자동 생성 파일

처음 실행하면 아래 파일이 없을 때 자동 생성됩니다.

```text
data/watchlist.csv
data/sector_templates.csv
data/keyword_bank.csv
```

실행 결과는 아래처럼 저장됩니다.

```text
data/economic_market_indicators_YYYY-MM-DD.csv
data/daily_news_raw_YYYY-MM-DD.csv
data/keyword_candidates_YYYY-MM-DD.csv
outputs/daily_economic_study_note_YYYY-MM-DD.txt
```

## 관심 종목 수정 방법

관심 종목은 `data/watchlist.csv`에서 관리합니다. 코드를 수정하지 않고 CSV에 줄을 추가하면 됩니다.

컬럼은 다음과 같습니다.

```text
name,ticker,market,sector,theme,extra_keywords,active
```

`active`가 `1`이면 알림에 포함되고, `0`이면 제외됩니다.

## 새로운 관심 종목 추가 예시

```csv
HD현대중공업,329180.KS,KR,shipbuilding,LNG선;방산,HD현대중공업 수주;LNG선;조선업황;선가,1
LG에너지솔루션,373220.KS,KR,battery,전기차;ESS,LG에너지솔루션;배터리 수요;리튬 가격;ESS,1
```

## 산업 템플릿 수정 방법

산업별 기본 키워드는 `data/sector_templates.csv`에서 관리합니다.

컬럼은 다음과 같습니다.

```text
sector,sector_name,default_keywords,why_watch,study_question
```

관심 종목의 `sector` 값과 산업 템플릿의 `sector` 값이 같으면, 해당 산업 키워드와 공부 질문이 자동으로 연결됩니다.

## 키워드 후보

뉴스 제목에서 반복 등장한 단어를 찾아 `data/keyword_candidates_YYYY-MM-DD.csv`에 저장합니다. 기존 `keyword_bank.csv`에 없는 단어만 후보로 남기며, 경제적으로 중요한 단어에는 `importance_score`가 더 높게 부여됩니다.

자동 후보는 바로 알림 키워드로 추가하지 않습니다. 사용자가 공부에 필요하다고 판단한 뒤 `keyword_bank.csv`에 직접 추가하는 방식이 안전합니다.

## 주의

이 프로그램은 경제 공부 보조 도구입니다. 리포트에는 매수, 매도, 목표가 같은 투자 조언 표현을 넣지 않도록 설계했습니다. 모든 문장은 가능성, 확인 필요, 구분해야 함이라는 관점으로 읽어 주세요.
