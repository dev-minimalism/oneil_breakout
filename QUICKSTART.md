# 🚀 빠른 시작 가이드 (5분 설정)

## 1단계: 패키지 설치 (1분)

```bash
pip install yfinance pandas numpy requests
```

한국 주식도 사용하려면:
```bash
pip install pykrx
```

---

## 2단계: 텔레그램 봇 만들기 (2분)

### A. 봇 생성
1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 입력
3. 봇 이름 입력 (예: Stock Alert Bot)
4. 봇 유저네임 입력 (예: my_stock_bot)
5. **토큰 복사** (예: `123456789:ABCdef...`)

### B. Chat ID 확인
1. 만든 봇에게 메시지 보내기 (아무거나)
2. 브라우저에서 열기:
   ```
   https://api.telegram.org/bot<토큰>/getUpdates
   ```
3. `"chat":{"id":` 뒤의 숫자가 Chat ID

---

## 3단계: 설정 파일 만들기 (1분)

### 방법 A: config.py 사용 (권장!) ⭐

```bash
# config.py 파일 생성
cp config_example.py config.py
```

**config.py 수정:**
```python
# 텔레그램 설정 (필수!)
TELEGRAM_TOKEN = "123456789:ABCdef..."  # 실제 토큰
CHAT_ID = "123456789"                   # 실제 Chat ID

# 한국 주식 감시 종목
KR_WATCH_LIST = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    # 원하는 종목 추가...
]

# 미국 주식 감시 종목
US_WATCH_LIST = [
    "AAPL",   # 애플
    "NVDA",   # 엔비디아
    # 원하는 종목 추가...
]

# 스캔 주기
SCAN_INTERVAL = 3600  # 1시간
```

### 방법 B: 파일 직접 수정

`oneil_breakout_bot.py` (미국) 또는 `oneil_breakout_bot_kr.py` (한국) 파일을 열어서:

**main() 함수 내부 (약 380줄 근처) 수정:**
```python
TELEGRAM_TOKEN = "여기에_토큰_입력"
CHAT_ID = "여기에_Chat_ID_입력"
```

---

## 4단계: 실행! (1분)

### 테스트 실행 (텔레그램 없이)
```bash
python test_scan.py
```

### 정식 실행 (텔레그램 알림)
```bash
# 미국 주식
python oneil_breakout_bot.py

# 한국 주식
python oneil_breakout_bot_kr.py
```

**config.py를 사용하는 경우:**
```
✅ config.py에서 설정을 불러왔습니다.
```
이 메시지가 나오면 성공!

---

## ✅ 완료!

프로그램이 1시간마다 자동으로 스캔하며,
돌파 신호가 발견되면 텔레그램으로 알림이 옵니다!

---

## 📱 텔레그램 알림 예시

```
🚀 [피벗 포인트 돌파!]

📊 종목: NVDA
💰 현재가: $145.50
📈 돌파율: 2.3%
📊 거래량 증가: +75%

✅ 강력한 매수 신호!
⛔ 손절가: 매수가 -7~8%
```

---

## 🆘 문제 해결

### "config.py를 찾을 수 없음"
```bash
# config.py 생성
cp config_example.py config.py

# 또는 수동으로 config.py 파일 생성 후 설정 입력
```

### "데이터를 가져올 수 없음"
```bash
# 한국 주식 데이터 테스트
python test_kr_stock.py
```

### "텔레그램 메시지가 안 옴"
```bash
# 텔레그램 설정 테스트
python test_telegram.py
```

### "너무 많은 신호가 옴"
config.py에서 조건 조정:
```python
VOLUME_SURGE_MIN = 70    # 50 → 70으로 증가
```

---

## 🎯 다음 단계

### 상세 가이드
- `CONFIG_GUIDE.md` - config.py 사용 방법
- `README.md` - 전체 사용 설명서
- `TROUBLESHOOTING.md` - 문제 해결

### 테스트 도구
- `test_telegram.py` - 텔레그램 설정 확인
- `test_kr_stock.py` - 한국 주식 데이터 테스트
- `test_scan.py` - 간단한 스캔 테스트

---

## 💡 config.py 장점

✅ **편리함** - 설정을 한 곳에서 관리  
✅ **재사용성** - 여러 프로그램에서 공유  
✅ **보안** - 토큰을 코드와 분리  
✅ **Git 관리** - .gitignore에 추가하여 공개 저장소에 안전

자세한 내용은 `CONFIG_GUIDE.md` 참고!
