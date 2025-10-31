# 🚀 윌리엄 오닐 돌파매매 통합 봇 사용 가이드

## ✨ 통합 버전의 장점

### 기존 방식 (분리 버전)
```
oneil_breakout_bot.py      (미국 주식)
oneil_breakout_bot_kr.py   (한국 주식)
→ 두 프로그램 따로 실행
→ 설정 파일도 따로 관리
→ 메시지 구분 어려움
```

### 새로운 방식 (통합 버전) ⭐
```
oneil_breakout_bot_unified.py
→ 한 프로그램에서 미국 + 한국 동시 지원
→ 설정 파일 하나로 관리
→ 메시지에 국기 이모지로 명확히 구분
```

---

## 🎯 주요 특징

### 1️⃣ 국가별 자동 구분
```
🇺🇸 [피벗 포인트 돌파!]
종목: NVDA
현재가: $145.50

🇰🇷 [피벗 포인트 돌파!]  
종목: 삼성전자 (005930)
현재가: 72,500원
```

### 2️⃣ 시장별 ON/OFF
```python
# config.py
SCAN_US_MARKET = True   # 미국 주식 스캔
SCAN_KR_MARKET = True   # 한국 주식 스캔

# 예시:
# 미국만: SCAN_US_MARKET = True, SCAN_KR_MARKET = False
# 한국만: SCAN_US_MARKET = False, SCAN_KR_MARKET = True
# 둘 다: 둘 다 True
```

### 3️⃣ 통합 스캔 결과
```
==================================================
🔍 윌리엄 오닐 돌파매매 통합 스캔 시작
📅 2025-10-31 10:00:00
📊 총 종목 수: 35개
   🇺🇸 미국: 20개
   🇰🇷 한국: 15개
==================================================

🇺🇸 미국 주식 스캔 시작...
🔍 🇺🇸 AAPL 분석 중... ⚪
🔍 🇺🇸 NVDA 분석 중... ✅
   ✅ NVDA: 피벗돌파 신호 발견!

🇰🇷 한국 주식 스캔 시작...
🔍 🇰🇷 삼성전자(005930) 분석 중... ✅
   ✅ 삼성전자(005930): 컵앤핸들 신호 발견!

📊 총 2개 신호 발견
   🇺🇸 미국: 1개
   🇰🇷 한국: 1개
```

---

## 🚀 빠른 시작 (5분)

### 1단계: 파일 준비
```bash
# 필요한 파일
oneil_breakout_bot_unified.py  ← 통합 봇
config.py                       ← 설정 파일
```

### 2단계: config.py 수정
```python
# config.py 열기
TELEGRAM_TOKEN = "실제_봇_토큰"
CHAT_ID = "실제_Chat_ID"

# 시장 선택
SCAN_US_MARKET = True   # 미국 스캔
SCAN_KR_MARKET = True   # 한국 스캔

# 종목 리스트
US_WATCH_LIST = ["AAPL", "MSFT", "NVDA"]  # 원하는 종목
KR_WATCH_LIST = ["005930", "000660"]      # 원하는 종목
```

### 3단계: 실행!
```bash
python oneil_breakout_bot_unified.py
```

---

## 📋 상황별 설정 예시

### 예시 1: 미국 주식만 모니터링
```python
# config.py
SCAN_US_MARKET = True
SCAN_KR_MARKET = False

US_WATCH_LIST = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"
]
```

### 예시 2: 한국 주식만 모니터링
```python
# config.py
SCAN_US_MARKET = False
SCAN_KR_MARKET = True

KR_WATCH_LIST = [
    "005930", "000660", "035420"
]
```

### 예시 3: 둘 다 모니터링 (추천!)
```python
# config.py
SCAN_US_MARKET = True
SCAN_KR_MARKET = True

US_WATCH_LIST = ["AAPL", "NVDA", "TSLA"]
KR_WATCH_LIST = ["005930", "000660", "035420"]
```

### 예시 4: 한국 자동 선택 + 미국 수동 선택
```python
# config.py
SCAN_US_MARKET = True
SCAN_KR_MARKET = True

# 미국: 직접 선택
US_WATCH_LIST = ["AAPL", "NVDA"]

# 한국: 자동 선택 (시가총액 상위)
USE_AUTO_WATCHLIST = True
KOSPI_TOP_N = 40
KOSDAQ_TOP_N = 20
```

---

## 🆚 기존 버전 vs 통합 버전

| 항목 | 분리 버전 | 통합 버전 |
|------|----------|----------|
| **프로그램 수** | 2개 | 1개 ⭐ |
| **설정 파일** | 분리 | 통합 ⭐ |
| **메시지 구분** | 어려움 | 쉬움 (🇺🇸🇰🇷) ⭐ |
| **리소스** | 2배 사용 | 1배 사용 ⭐ |
| **관리** | 복잡 | 간단 ⭐ |
| **시장 선택** | 프로그램 선택 | 설정으로 선택 ⭐ |

---

## 💡 시장 시간대 참고

### 한국 주식 시장
- 장 운영: 평일 09:00 ~ 15:30 (KST)
- 동시호가: 08:30 ~ 09:00

### 미국 주식 시장 (한국 시간)
- 여름: 22:30 ~ 05:00 (다음날)
- 겨울: 23:30 ~ 06:00 (다음날)

**시간대가 겹치지 않아서** 24시간 실행해도 괜찮습니다!

---

## 🔧 스캔 주기 추천

### 보수적 모니터링
```python
SCAN_INTERVAL = 7200  # 2시간마다
```

### 일반 모니터링 (권장)
```python
SCAN_INTERVAL = 3600  # 1시간마다
```

### 적극적 모니터링
```python
SCAN_INTERVAL = 1800  # 30분마다
```

---

## 📱 텔레그램 메시지 예시

### 시작 메시지
```
🤖 윌리엄 오닐 돌파매매 통합 봇 시작

📊 감시 시장: 🇺🇸 미국(20개) + 🇰🇷 한국(15개)
⏰ 스캔 주기: 60분
📈 감지 패턴:
  - 컵앤핸들
  - 피벗 포인트 돌파
  - 베이스 돌파

시작 시간: 2025-10-31 10:00:00
```

### 신호 메시지
```
🇺🇸 [피벗 포인트 돌파!]

📊 시장: 미국 주식
🏢 종목: NVDA
💰 현재가: $145.50
🎯 돌파가: $142.30
📈 돌파율: 2.25%

📊 거래량 증가: +78%

✅ 강력한 매수 신호!
⛔ 손절가: 매수가 -7~8%
```

---

## 🔄 기존 버전에서 마이그레이션

### 1. 설정 통합
```python
# 기존: oneil_breakout_bot.py
WATCH_LIST = ["AAPL", "NVDA"]

# 기존: oneil_breakout_bot_kr.py  
WATCH_LIST = ["005930", "000660"]

# 통합: config.py
US_WATCH_LIST = ["AAPL", "NVDA"]
KR_WATCH_LIST = ["005930", "000660"]
```

### 2. 실행 방법
```bash
# 기존
python oneil_breakout_bot.py &
python oneil_breakout_bot_kr.py &

# 통합
python oneil_breakout_bot_unified.py
```

---

## ⚙️ 고급 설정

### 각 시장별 다른 스캔 주기 원한다면?
통합 버전은 같은 주기를 사용합니다.
만약 다른 주기가 필요하면 분리 버전 사용을 추천합니다.

### API Rate Limit 고려
- 미국 + 한국 합쳐서 50개 이상이면 스캔 시간 고려
- 종목당 약 1-2초 소요

---

## 🆘 문제 해결

### 메시지가 너무 많이 와요
```python
# 종목 수 줄이기
US_WATCH_LIST = ["AAPL", "MSFT", "NVDA"]  # 5-10개 추천
KR_WATCH_LIST = ["005930", "000660"]       # 5-10개 추천

# 또는 조건 엄격하게
# (oneil_breakout_bot_unified.py 파일 내 조건 수정)
```

### 한 시장만 모니터링하고 싶어요
```python
# config.py
SCAN_US_MARKET = True   # 미국만
SCAN_KR_MARKET = False  # 한국 끄기
```

### 텔레그램이 안 와요
```bash
python test_telegram.py  # 텔레그램 설정 테스트
```

---

## 🎓 사용 팁

1. **처음에는 소수 종목으로 시작**
   - 미국 5개 + 한국 5개 정도

2. **신호 검증 후 종목 추가**
   - 1주일 정도 테스트 후 점진적 확대

3. **시장별 ON/OFF 활용**
   - 관심 없는 시장은 끄기

4. **스캔 주기 조절**
   - 시작은 2시간, 익숙해지면 1시간

5. **메시지 필터링**
   - 텔레그램 설정에서 중요 메시지만 알림

---

## 📊 예상 메시지 빈도

### 보수적 설정 (20개 종목, 2시간 주기)
- 신호 발생: 하루 1-3개
- 메시지: 하루 5-10개

### 일반 설정 (30개 종목, 1시간 주기)
- 신호 발생: 하루 2-5개
- 메시지: 하루 10-20개

### 적극적 설정 (50개 종목, 30분 주기)
- 신호 발생: 하루 5-10개
- 메시지: 하루 20-40개

---

## ✅ 체크리스트

시작 전 확인:
- [ ] config.py 수정 완료
- [ ] 텔레그램 봇 토큰 입력
- [ ] Chat ID 입력
- [ ] 모니터링할 시장 선택
- [ ] 종목 리스트 확인
- [ ] test_telegram.py 테스트 완료
- [ ] 실행!

---

**통합 버전으로 더 편리하게 투자하세요!** 🚀📈
