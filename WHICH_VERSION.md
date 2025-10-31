# 🤔 어떤 버전을 사용해야 할까?

## 📦 제공되는 버전

### 1️⃣ 통합 버전 (추천!) ⭐
```
oneil_breakout_bot_unified.py
```
- 미국 + 한국 주식 한 프로그램에서 관리
- 설정 파일 하나로 통합 관리
- 메시지에 국기 이모지로 명확히 구분

### 2️⃣ 분리 버전
```
oneil_breakout_bot.py      (미국 주식 전용)
oneil_breakout_bot_kr.py   (한국 주식 전용)
```
- 각 시장별 독립 실행
- 시장별 다른 스캔 주기 설정 가능

---

## 🎯 상황별 추천

### 👉 통합 버전을 선택하세요 (대부분의 경우)

**이런 분들에게 추천:**
- ✅ 미국과 한국 주식 둘 다 관심 있음
- ✅ 설정을 한 곳에서 관리하고 싶음
- ✅ 프로그램 하나만 실행하고 싶음
- ✅ 메시지를 깔끔하게 구분하고 싶음
- ✅ 컴퓨터 리소스 절약하고 싶음

**사용법:**
```bash
# config.py 수정
TELEGRAM_TOKEN = "실제_토큰"
CHAT_ID = "실제_Chat_ID"
SCAN_US_MARKET = True
SCAN_KR_MARKET = True

# 실행
python oneil_breakout_bot_unified.py
```

---

### 👉 분리 버전을 선택하세요

**이런 분들에게 추천:**
- ✅ 한 시장만 모니터링
- ✅ 시장별로 다른 스캔 주기 필요
- ✅ 시장별로 다른 텔레그램 채널 사용
- ✅ 별도의 서버나 컴퓨터에서 실행

**예시 1: 미국만 모니터링**
```bash
python oneil_breakout_bot.py
```

**예시 2: 한국만 모니터링**
```bash
python oneil_breakout_bot_kr.py
```

**예시 3: 둘 다 실행 (다른 스캔 주기)**
```bash
# 미국: 30분마다 (공격적)
python oneil_breakout_bot.py &

# 한국: 2시간마다 (보수적)
python oneil_breakout_bot_kr.py &
```

---

## 📊 버전 비교표

| 기능 | 통합 버전 | 분리 버전 |
|------|----------|----------|
| **프로그램 수** | 1개 ⭐ | 2개 |
| **설정 관리** | config.py 하나 ⭐ | 각 파일 수정 |
| **메시지 구분** | 🇺🇸🇰🇷 자동 구분 ⭐ | 구분 없음 |
| **리소스 사용** | 적음 ⭐ | 많음 |
| **시장별 ON/OFF** | config에서 쉽게 ⭐ | 프로그램 선택 |
| **다른 스캔 주기** | 불가 | 가능 ⭐ |
| **다른 텔레그램 채널** | 불가 | 가능 ⭐ |
| **관리 편의성** | 쉬움 ⭐ | 보통 |

---

## 💡 실전 시나리오

### 시나리오 1: 취미 투자자
**목표:** 미국/한국 주요 종목 모니터링

**추천: 통합 버전**
```python
# config.py
US_WATCH_LIST = ["AAPL", "MSFT", "NVDA"]
KR_WATCH_LIST = ["005930", "000660", "035420"]
SCAN_INTERVAL = 3600  # 1시간
```

---

### 시나리오 2: 미국 주식 집중 투자자
**목표:** 미국 주식만 관심, 한국은 무관심

**추천: 분리 버전 (미국)**
```bash
python oneil_breakout_bot.py
```

또는 **통합 버전**도 가능:
```python
# config.py
SCAN_US_MARKET = True
SCAN_KR_MARKET = False  # 한국 끄기
```

---

### 시나리오 3: 한국 주식 집중 투자자
**목표:** 한국 주식만 관심

**추천: 분리 버전 (한국)**
```bash
python oneil_breakout_bot_kr.py
```

또는 **통합 버전**:
```python
# config.py
SCAN_US_MARKET = False  # 미국 끄기
SCAN_KR_MARKET = True
```

---

### 시나리오 4: 전문 트레이더
**목표:** 미국 30분마다, 한국 2시간마다 다르게 스캔

**추천: 분리 버전**
```bash
# 터미널 1
python oneil_breakout_bot.py      # 30분 주기로 설정

# 터미널 2  
python oneil_breakout_bot_kr.py   # 2시간 주기로 설정
```

---

### 시나리오 5: 팀/그룹 사용
**목표:** 미국 팀과 한국 팀이 각각 다른 텔레그램 채널 사용

**추천: 분리 버전**
```python
# oneil_breakout_bot.py (미국 팀)
TELEGRAM_TOKEN = "미국팀_봇_토큰"
CHAT_ID = "미국팀_채널_ID"

# oneil_breakout_bot_kr.py (한국 팀)
TELEGRAM_TOKEN = "한국팀_봇_토큰"
CHAT_ID = "한국팀_채널_ID"
```

---

## 🚦 빠른 결정 플로우

```
시작
 │
 ├─ 미국 + 한국 둘 다 관심?
 │   └─ YES → 같은 스캔 주기 OK?
 │       ├─ YES → 통합 버전 ⭐
 │       └─ NO  → 분리 버전
 │
 └─ 한 시장만 관심?
     ├─ 미국만 → 분리 버전 (미국) 또는 통합 버전
     └─ 한국만 → 분리 버전 (한국) 또는 통합 버전
```

---

## 🎓 초보자 추천 경로

### 1주차: 테스트
```bash
# 통합 버전으로 시작
python test_telegram.py  # 텔레그램 테스트
python oneil_breakout_bot_unified.py
```

### 2-4주차: 검증
- 신호 정확도 확인
- 종목 수 조정
- 스캔 주기 최적화

### 이후: 필요에 따라 선택
- 대부분 통합 버전으로 충분
- 특수한 요구사항 있으면 분리 버전

---

## ⚖️ 최종 추천

### 🏆 1순위: 통합 버전
**90%의 사용자에게 적합**
- 간편한 관리
- 깔끔한 메시지
- 하나의 프로그램

### 2순위: 분리 버전  
**10%의 특수 케이스**
- 다른 스캔 주기 필요
- 다른 텔레그램 채널 필요
- 한 시장만 집중

---

## 📝 요약

| 당신의 상황 | 추천 버전 |
|------------|----------|
| 미국 + 한국 모두 관심 | 통합 ⭐ |
| 한 시장만 관심 | 통합 또는 분리 |
| 시장별 다른 주기 필요 | 분리 |
| 시장별 다른 채널 필요 | 분리 |
| 처음 사용 | 통합 ⭐ |
| 설정 관리 간단하게 | 통합 ⭐ |
| 컴퓨터 리소스 절약 | 통합 ⭐ |

---

## 🚀 빠른 시작

### 통합 버전 선택했다면:
1. `config.py` 수정
2. `python oneil_breakout_bot_unified.py` 실행

### 분리 버전 선택했다면:
1. 원하는 파일 내부 설정 수정
2. `python oneil_breakout_bot.py` 실행 (미국)
   또는 `python oneil_breakout_bot_kr.py` 실행 (한국)

---

**대부분의 경우 통합 버전을 추천합니다!** 🎯

궁금한 점이 있으면 README_UNIFIED.md를 참고하세요!
