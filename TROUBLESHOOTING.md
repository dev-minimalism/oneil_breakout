# 🔧 트러블슈팅 가이드

## 자주 발생하는 오류와 해결 방법

---

## ❌ ModuleNotFoundError: No module named 'pkg_resources'

### 원인
Python 3.12 이상에서 `setuptools`가 기본 설치되지 않음

### 해결 방법
```bash
pip install setuptools
```

또는 전체 재설치:
```bash
pip install --upgrade setuptools pykrx
```

---

## ❌ ModuleNotFoundError: No module named 'yfinance' (또는 다른 모듈)

### 해결 방법
```bash
# 모든 필수 패키지 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install yfinance pandas numpy requests pykrx
```

---

## ❌ 텔레그램 메시지가 전송되지 않음

### 확인 사항
1. **봇 토큰이 정확한가?**
   ```python
   TELEGRAM_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"  # 예시
   ```

2. **Chat ID가 정확한가?**
   - 브라우저에서 확인: `https://api.telegram.org/bot<토큰>/getUpdates`
   - 또는 `@userinfobot`에서 확인

3. **봇에게 먼저 메시지를 보냈는가?**
   - 봇에게 `/start` 또는 아무 메시지나 보내야 합니다

4. **인터넷 연결 확인**

### 테스트 코드
```python
import requests

token = "여기에_토큰"
chat_id = "여기에_Chat_ID"

url = f"https://api.telegram.org/bot{token}/sendMessage"
data = {"chat_id": chat_id, "text": "테스트 메시지"}

response = requests.post(url, data=data)
print(response.json())
```

---

## ❌ 한국 주식 데이터를 가져올 수 없음

### 원인
1. pykrx API 서버 점검 중
2. 잘못된 종목 코드
3. 시장 운영 시간 외

### 해결 방법
```python
# 종목 코드 확인
from pykrx import stock

# KOSPI 전체 종목
tickers = stock.get_market_ticker_list()
print(tickers[:10])

# 종목명으로 검색
kospi = stock.get_market_ticker_list(market="KOSPI")
for ticker in kospi:
    name = stock.get_market_ticker_name(ticker)
    if "삼성" in name:
        print(f"{name}: {ticker}")
```

### 시장 운영 시간
- 한국 주식: 평일 09:00 ~ 15:30
- 실시간 데이터는 장중에만 업데이트

---

## ❌ 미국 주식 데이터를 가져올 수 없음

### 원인
1. yfinance API 제한
2. 잘못된 티커
3. 네트워크 오류

### 해결 방법
```python
import yfinance as yf

# 티커 확인
ticker = yf.Ticker("AAPL")
print(ticker.info)

# 데이터 가져오기
df = ticker.history(period="1mo")
print(df.head())
```

### API 제한 회피
```python
import time

for ticker in tickers:
    # 각 요청 사이에 1초 대기
    data = get_stock_data(ticker)
    time.sleep(1)
```

---

## ❌ SSL 인증서 오류

### 해결 방법 (macOS)
```bash
# Python 인증서 설치
/Applications/Python\ 3.12/Install\ Certificates.command
```

### 해결 방법 (일반)
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

---

## ❌ 너무 많은 신호 / 잘못된 신호

### 조건 엄격하게 조정

**거래량 조건 높이기:**
```python
# oneil_breakout_bot.py 또는 oneil_breakout_bot_kr.py에서

# 피벗 돌파 - 약 227줄
if breakout and volume_surge >= 70 and 0 < breakout_pct <= 5:
#                             ^^
#                             50 → 70으로 변경

# 베이스 돌파 - 약 263줄  
if base_volatility < 15 and breakout and volume_surge >= 60 and 0 < breakout_pct <= 7:
#                                                        ^^
#                                                        40 → 60으로 변경
```

**컵 깊이 조건 조정:**
```python
# 컵앤핸들 - 약 155줄
if 15 <= cup_depth <= 30 and handle_depth < 10 and breakout:
#   ^^               ^^                      ^^
#   12→15           40→30                  12→10
```

---

## ❌ 프로그램이 멈춤 / 느림

### 원인
1. 너무 많은 종목 감시
2. API 제한
3. 네트워크 지연

### 해결 방법
```python
# 감시 종목 줄이기
WATCH_LIST = [
    "AAPL", "MSFT", "NVDA"  # 10-15개 정도만
]

# API 요청 간격 늘리기
time.sleep(2)  # 1초 → 2초
```

---

## ❌ 가상환경 관련 오류

### 가상환경 새로 만들기
```bash
# 기존 가상환경 삭제
rm -rf .venv

# 새로 만들기
python3 -m venv .venv

# 활성화
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

---

## ❌ Permission Denied (권한 오류)

### macOS/Linux
```bash
chmod +x oneil_breakout_bot.py
```

---

## ❌ 인코딩 오류 (한글 깨짐)

### 파일 인코딩 확인
```python
# 파일 상단에 추가
# -*- coding: utf-8 -*-
```

### 터미널 설정
```bash
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8
```

---

## 💡 디버깅 팁

### 1. 로그 레벨 조정
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 한 종목만 테스트
```python
WATCH_LIST = ["AAPL"]  # 하나만
```

### 3. 예외 처리 강화
```python
try:
    # 코드
except Exception as e:
    import traceback
    print(traceback.format_exc())
```

---

## 🆘 여전히 안 되나요?

1. **Python 버전 확인**
   ```bash
   python --version  # 3.8 이상 필요
   ```

2. **가상환경 사용 권장**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

3. **test_scan.py로 먼저 테스트**
   ```bash
   python test_scan.py
   ```

4. **에러 메시지 전체 복사**
   - 에러가 발생한 줄 번호와 메시지 확인

---

## 📞 추가 도움이 필요하면

- Python 버전
- 운영체제 (Windows/macOS/Linux)
- 전체 에러 메시지
- 어떤 단계에서 발생했는지

위 정보와 함께 문의하면 더 정확한 해결책을 제공할 수 있습니다!
