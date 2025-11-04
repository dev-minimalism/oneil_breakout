# 🚨 빠른 문제 해결 가이드

## ❌ 텔레그램 404 오류

```
❌ 텔레그램 전송 실패: 404
```

### 원인
Chat ID가 잘못되었거나 봇에게 메시지를 보내지 않았습니다.

### 해결 방법

#### 1단계: 텔레그램 설정 테스트
```bash
python test_telegram.py
```
위 스크립트가 자동으로 문제를 진단하고 해결책을 알려줍니다!

#### 2단계: Chat ID 올바르게 찾기

**방법 A: 브라우저 사용**
1. 봇에게 메시지 보내기 (예: "hello" 또는 "/start")
2. 브라우저에서 열기:
   ```
   https://api.telegram.org/bot<봇토큰>/getUpdates
   ```
3. `"chat":{"id":` 뒤의 **숫자만** 복사
   - 예시: `"chat":{"id":123456789` → `123456789`
   - **따옴표 없이** 숫자만!

**방법 B: @userinfobot 사용**
1. 텔레그램에서 `@userinfobot` 검색
2. `/start` 입력
3. 표시되는 ID 복사

#### 3단계: 코드에 정확히 입력
```python
TELEGRAM_TOKEN = "123456789:ABCdefGHIjklMNO"  # 봇 토큰
CHAT_ID = "123456789"  # 숫자만! 따옴표는 코드에만
```

**❌ 잘못된 예:**
```python
CHAT_ID = "YOUR_CHAT_ID_HERE"  # 수정 안 함
CHAT_ID = "\"123456789\""      # 따옴표 중복
CHAT_ID = 123456789            # 따옴표 없음 (문자열이어야 함)
```

**✅ 올바른 예:**
```python
CHAT_ID = "123456789"          # 정확!
```

---

## ❌ pykrx 데이터 오류

```
❌ 데이터 조회 실패: Length mismatch: Expected axis has 6 elements, new values have 5 elements
```

### 원인
pykrx API가 반환하는 컬럼 수가 변경되었습니다.

### ✅ 해결됨!
업데이트된 `oneil_breakout_bot_kr.py` 파일을 다운로드하면 자동으로 해결됩니다.

### 테스트하기
```bash
python test_kr_stock.py
```
이 스크립트가 pykrx가 제대로 작동하는지 확인합니다.

---

## ⚠️ pkg_resources 경고 메시지

```
UserWarning: pkg_resources is deprecated as an API...
```

### 이건 경고일 뿐입니다
- 프로그램은 정상 작동합니다
- 무시해도 됩니다

### 경고 없애고 싶다면
```bash
pip install --upgrade setuptools
pip install pykrx --upgrade
```

또는 경고 숨기기:
```bash
# 프로그램 실행 시
python -W ignore oneil_breakout_bot_kr.py
```

---

## 🧪 전체 테스트 순서 (추천)

### 1. 한국 주식 데이터 테스트
```bash
python test_kr_stock.py
```
**기대 결과:** ✅ 성공: 5개

### 2. 텔레그램 설정 테스트
```bash
python test_telegram.py
```
**기대 결과:** ✅ 메시지 전송 성공!

### 3. 메인 프로그램 실행
```bash
python oneil_breakout_bot_kr.py
```

---

## 📋 설정 확인 체크리스트

### 텔레그램 설정
- [ ] 봇 토큰을 BotFather에서 받았나?
- [ ] 봇에게 메시지를 먼저 보냈나?
- [ ] Chat ID를 정확히 복사했나? (숫자만)
- [ ] 코드에 정확히 입력했나?

### Python 환경
- [ ] Python 3.8 이상 설치됨
- [ ] 가상환경 사용 중 (권장)
- [ ] 모든 패키지 설치됨 (`pip install -r requirements.txt`)

### 종목 코드
- [ ] 6자리 숫자 (예: "005930")
- [ ] 따옴표로 감싸져 있음
- [ ] 올바른 종목 코드 사용

---

## 🆘 여전히 안 되나요?

### 완전 재설치 (최후의 수단)
```bash
# 1. 가상환경 삭제
rm -rf .venv  # 또는 수동으로 삭제

# 2. 새 가상환경 생성
python3 -m venv .venv

# 3. 활성화
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate  # Windows

# 4. 패키지 재설치
pip install --upgrade pip
pip install setuptools
pip install -r requirements.txt

# 5. 테스트
python test_kr_stock.py
python test_telegram.py

# 6. 실행
python oneil_breakout_bot_kr.py
```

---

## 💡 추가 팁

### 로그 상세히 보기
프로그램 실행 시 더 자세한 정보를 보려면:
```python
# 파일 상단에 추가
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 한 종목만 테스트
```python
WATCH_LIST = ["005930"]  # 삼성전자만
```

### 스캔 간격 줄이기 (테스트용)
```python
SCAN_INTERVAL = 300  # 5분마다 (테스트용)
```

---

## 📞 도움 요청 시 포함할 정보

1. **Python 버전**
   ```bash
   python --version
   ```

2. **운영체제**
   - macOS, Windows, Linux?

3. **전체 에러 메시지**
   - 스크린샷 또는 복사

4. **어느 단계에서 발생?**
   - 설치? 텔레그램 설정? 실행?

5. **실행한 명령어**
   ```bash
   python oneil_breakout_bot_kr.py
   ```

위 정보와 함께 문의하면 정확한 해결책을 제공할 수 있습니다!
