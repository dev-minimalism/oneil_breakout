# 윌리엄 오닐 돌파매매 자동 알림 봇 🚀

윌리엄 오닐의 CAN SLIM 투자 기법 중 돌파매매(Breakout Trading) 패턴을 자동으로 감지하고 텔레그램으로 알림을 보내주는 파이썬 프로그램입니다.

## 🎯 새로운 통합 버전 출시! ⭐

**한 프로그램으로 미국 + 한국 주식을 동시에 모니터링!**

```
✨ 통합 버전의 장점:
- 🇺🇸 미국 + 🇰🇷 한국 주식 동시 지원
- 📝 설정 파일 하나로 통합 관리
- 💬 메시지에 국기 이모지로 명확히 구분
- 🖥️ 프로그램 하나만 실행
- ⚡ 리소스 효율적
```

---

## 📦 제공되는 버전

### 🏆 통합 버전 (추천!)
- `oneil_breakout_bot_unified.py` - 미국 + 한국 통합 ⭐
- `config.py` - 통합 설정 파일
- `README_UNIFIED.md` - 상세 가이드

### 📁 분리 버전
- `oneil_breakout_bot.py` - 미국 주식 전용
- `oneil_breakout_bot_kr.py` - 한국 주식 전용

### 🧪 테스트 도구
- `test_telegram.py` - 텔레그램 설정 테스트
- `test_kr_stock.py` - 한국 주식 데이터 테스트
- `test_scan.py` - 간단 스캔 테스트

---

## 🚀 빠른 시작 (5분)

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 텔레그램 봇 설정
1. `@BotFather`에서 봇 생성 → 토큰 받기
2. 봇에게 메시지 보낸 후 Chat ID 확인

### 3. config.py 수정
```python
TELEGRAM_TOKEN = "실제_봇_토큰"
CHAT_ID = "실제_Chat_ID"

SCAN_US_MARKET = True   # 미국
SCAN_KR_MARKET = True   # 한국

US_WATCH_LIST = ["AAPL", "MSFT", "NVDA"]
KR_WATCH_LIST = ["005930", "000660"]
```

### 4. 실행!
```bash
python oneil_breakout_bot_unified.py
```

---

## 📈 감지 패턴

- **컵 앤 핸들**: 가장 강력한 돌파 패턴
- **피벗 포인트 돌파**: 신고점 + 거래량 급증
- **베이스 돌파**: 횡보 구간 이탈

---

## 💬 알림 예시

```
🇺🇸 [피벗 포인트 돌파!]
종목: NVDA
현재가: $145.50
돌파율: 2.3%
거래량 증가: +75%
✅ 강력한 매수 신호!
```

```
🇰🇷 [피벗 포인트 돌파!]
종목: 삼성전자 (005930)
현재가: 72,500원
돌파율: 2.1%
거래량 증가: +85%
✅ 강력한 매수 신호!
```

---

## 🎯 어떤 버전?

**통합 버전 (추천)**: 대부분의 경우
- 미국 + 한국 모두 관심
- 설정 관리 쉽게

**분리 버전**: 특수한 경우
- 시장별 다른 스캔 주기
- 시장별 다른 텔레그램 채널

자세한 비교: `WHICH_VERSION.md`

---

## 🧪 테스트

```bash
# 텔레그램 설정 테스트
python test_telegram.py

# 한국 주식 데이터 테스트
python test_kr_stock.py
```

---

## 🔧 문제 해결

- 텔레그램 404 오류 → `QUICK_FIX.md`
- pykrx 데이터 오류 → `TROUBLESHOOTING.md`
- 전체 가이드 → `README_UNIFIED.md`

---

## 📚 가이드 문서

- `WHICH_VERSION.md` - 버전 선택 가이드
- `README_UNIFIED.md` - 통합 버전 상세 가이드
- `QUICKSTART.md` - 5분 빠른 시작
- `TROUBLESHOOTING.md` - 문제 해결
- `QUICK_FIX.md` - 긴급 해결

---

## ⚠️ 면책 조항

교육 목적 프로그램입니다. 모든 투자 판단과 손실은 본인 책임입니다.

---

**Happy Trading! 📈🚀**

통합 버전으로 더 쉽고 편리하게!
🇺🇸 + 🇰🇷 = 하나의 프로그램
