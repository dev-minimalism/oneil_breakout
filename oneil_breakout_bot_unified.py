"""
윌리엄 오닐 돌파매매(CAN SLIM) 통합 알림 시스템
- 미국 주식 + 한국 주식 통합 지원
- 컵앤핸들 패턴 감지
- 피벗포인트 돌파 감지
- 거래량 급증 확인
- 텔레그램 알림 전송
"""

import time
import warnings
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from pykrx import stock

warnings.filterwarnings('ignore')

# 설정 파일 import
try:
  import config

  USE_CONFIG_FILE = True
except ImportError:
  print("⚠️  config.py 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
  USE_CONFIG_FILE = False


class UnifiedBreakoutDetector:
  """미국/한국 주식 통합 돌파매매 패턴 감지 클래스"""

  def __init__(self, telegram_token: str, chat_id: str):
    """
    Args:
        telegram_token: 텔레그램 봇 토큰
        chat_id: 텔레그램 채팅 ID
    """
    self.telegram_token = telegram_token
    self.chat_id = chat_id
    self.base_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    self.last_update_id = 0  # 마지막으로 처리한 메시지 ID

  def send_telegram_message(self, message: str):
    """텔레그램으로 메시지 전송"""
    try:
      payload = {
        'chat_id': self.chat_id,
        'text': message,
        'parse_mode': 'HTML'
      }
      response = requests.post(self.base_url, data=payload)
      if response.status_code == 200:
        print(f"✅ 텔레그램 전송 성공")
      else:
        print(f"❌ 텔레그램 전송 실패: {response.status_code}")
    except Exception as e:
      print(f"❌ 텔레그램 전송 오류: {e}")

  def check_telegram_messages(self) -> bool:
    """텔레그램 메시지 확인 및 /scan 명령어 감지"""
    try:
      url = f"https://api.telegram.org/bot{self.telegram_token}/getUpdates"
      params = {
        'offset': self.last_update_id + 1,
        'timeout': 1
      }
      response = requests.get(url, params=params, timeout=5)

      if response.status_code == 200:
        data = response.json()
        if data['ok'] and data['result']:
          for update in data['result']:
            self.last_update_id = update['update_id']

            # 메시지가 있는 경우
            if 'message' in update:
              message = update['message']
              chat_id = str(message['chat']['id'])
              text = message.get('text', '').strip()

              print(f"📨 메시지 수신: '{text}' from {chat_id}")

              # /scan 명령어 확인 (chat_id 비교를 문자열로 통일)
              if str(self.chat_id) == chat_id and text == '/scan':
                print(f"🔔 /scan 명령어 감지!")
                return True

      return False
    except Exception as e:
      print(f"⚠️  메시지 확인 오류: {e}")
      return False

  # ========================================
  # 미국 주식 관련 메서드
  # ========================================

  def get_us_stock_data(self, ticker: str, period: str = "6mo") -> pd.DataFrame:
    """미국 주식 데이터 가져오기"""
    try:
      stock_obj = yf.Ticker(ticker)
      df = stock_obj.history(period=period)
      if df.empty:
        print(f"⚠️  {ticker}: 데이터 없음")
        return None
      return df
    except Exception as e:
      print(f"❌ {ticker} 데이터 조회 실패: {e}")
      return None

  # ========================================
  # 한국 주식 관련 메서드
  # ========================================

  def get_kr_stock_name(self, ticker: str) -> str:
    """한국 주식 종목명 가져오기"""
    try:
      name = stock.get_market_ticker_name(ticker)
      return name if name else ticker
    except:
      return ticker

  def get_kr_stock_data(self, ticker: str, days: int = 120) -> pd.DataFrame:
    """한국 주식 데이터 가져오기"""
    try:
      end_date = datetime.now()
      start_date = end_date - timedelta(days=days)

      # OHLCV 데이터 가져오기
      df = stock.get_market_ohlcv_by_date(
          start_date.strftime("%Y%m%d"),
          end_date.strftime("%Y%m%d"),
          ticker
      )

      if df.empty:
        print(f"⚠️  {ticker}: 데이터 없음")
        return None

      # 컬럼명 확인 및 영문으로 변경
      column_mapping = {
        '시가': 'Open',
        '고가': 'High',
        '저가': 'Low',
        '종가': 'Close',
        '거래량': 'Volume'
      }

      df = df.rename(columns=column_mapping)
      required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
      df = df[required_columns]

      return df
    except Exception as e:
      print(f"❌ {ticker} 데이터 조회 실패: {e}")
      return None

  # ========================================
  # 패턴 감지 메서드 (공통)
  # ========================================

  def detect_cup_and_handle(self, df: pd.DataFrame, ticker: str,
      market: str) -> Dict:
    """컵 앤 핸들 패턴 감지"""
    if df is None or len(df) < 60:
      return None

    try:
      recent = df.tail(60).copy()
      close = recent['Close'].values

      # 컵 형성 확인
      mid_idx = len(close) // 2
      left_peak = np.max(close[:mid_idx])
      right_peak = np.max(close[mid_idx:])
      bottom = np.min(close[mid_idx - 10:mid_idx + 10])

      cup_depth = ((left_peak - bottom) / left_peak) * 100

      # 핸들 형성 확인
      handle = close[-10:]
      handle_depth = ((np.max(handle) - np.min(handle)) / np.max(handle)) * 100

      # 돌파 확인
      current_price = close[-1]
      resistance = np.max(close[-20:])
      breakout = current_price >= resistance * 0.99

      if 12 <= cup_depth <= 40 and handle_depth < 12 and breakout:
        signal = {
          'ticker': ticker,
          'pattern': '컵앤핸들',
          'market': market,
          'cup_depth': round(cup_depth, 2),
          'handle_depth': round(handle_depth, 2),
          'resistance': resistance,
          'current_price': current_price,
          'breakout_pct': round(
              ((current_price - resistance) / resistance) * 100, 2)
        }

        # 한국 주식이면 종목명 추가
        if market == 'KR':
          signal['name'] = self.get_kr_stock_name(ticker)

        return signal
    except Exception as e:
      print(f"⚠️  {ticker} 컵앤핸들 분석 오류: {e}")

    return None

  def detect_pivot_breakout(self, df: pd.DataFrame, ticker: str,
      market: str) -> Dict:
    """피벗 포인트 돌파 감지"""
    if df is None or len(df) < 30:
      return None

    try:
      recent = df.tail(30).copy()

      # 거래량 평균
      avg_volume = recent['Volume'].iloc[:-1].mean()
      current_volume = recent['Volume'].iloc[-1]
      volume_surge = (current_volume / avg_volume - 1) * 100

      # 가격 데이터
      close = recent['Close'].values
      current_price = close[-1]
      resistance = np.max(close[-20:-1])

      # 돌파 확인
      breakout = current_price > resistance
      breakout_pct = ((current_price - resistance) / resistance) * 100

      if breakout and volume_surge >= 50 and 0 < breakout_pct <= 5:
        signal = {
          'ticker': ticker,
          'pattern': '피벗돌파',
          'market': market,
          'resistance': resistance,
          'current_price': current_price,
          'breakout_pct': round(breakout_pct, 2),
          'volume_surge': round(volume_surge, 2)
        }

        if market == 'KR':
          signal['name'] = self.get_kr_stock_name(ticker)

        return signal
    except Exception as e:
      print(f"⚠️  {ticker} 피벗돌파 분석 오류: {e}")

    return None

  def detect_base_breakout(self, df: pd.DataFrame, ticker: str,
      market: str) -> Dict:
    """베이스(횡보구간) 돌파 감지"""
    if df is None or len(df) < 40:
      return None

    try:
      recent = df.tail(40).copy()
      close = recent['Close'].values

      # 횡보 구간 확인
      base_period = close[-30:-5]
      base_high = np.max(base_period)
      base_low = np.min(base_period)
      base_volatility = ((base_high - base_low) / base_low) * 100

      current_price = close[-1]
      breakout = current_price > base_high
      breakout_pct = ((current_price - base_high) / base_high) * 100

      # 거래량 확인
      avg_volume = recent['Volume'].iloc[-30:-5].mean()
      current_volume = recent['Volume'].iloc[-1]
      volume_surge = (current_volume / avg_volume - 1) * 100

      if base_volatility < 15 and breakout and volume_surge >= 40 and 0 < breakout_pct <= 7:
        signal = {
          'ticker': ticker,
          'pattern': '베이스돌파',
          'market': market,
          'base_high': base_high,
          'current_price': current_price,
          'breakout_pct': round(breakout_pct, 2),
          'volume_surge': round(volume_surge, 2),
          'base_volatility': round(base_volatility, 2)
        }

        if market == 'KR':
          signal['name'] = self.get_kr_stock_name(ticker)

        return signal
    except Exception as e:
      print(f"⚠️  {ticker} 베이스돌파 분석 오류: {e}")

    return None

  # ========================================
  # 종목 분석
  # ========================================

  def analyze_us_stock(self, ticker: str) -> List[Dict]:
    """미국 주식 분석"""
    print(f"🔍 🇺🇸 {ticker} 분석 중...", end=" ")

    df = self.get_us_stock_data(ticker)
    if df is None:
      print("❌")
      return []

    signals = []

    # 패턴 감지
    cup_signal = self.detect_cup_and_handle(df, ticker, 'US')
    if cup_signal:
      signals.append(cup_signal)

    pivot_signal = self.detect_pivot_breakout(df, ticker, 'US')
    if pivot_signal:
      signals.append(pivot_signal)

    base_signal = self.detect_base_breakout(df, ticker, 'US')
    if base_signal:
      signals.append(base_signal)

    if signals:
      print("✅")
    else:
      print("⚪")

    return signals

  def analyze_kr_stock(self, ticker: str) -> List[Dict]:
    """한국 주식 분석"""
    stock_name = self.get_kr_stock_name(ticker)
    print(f"🔍 🇰🇷 {stock_name}({ticker}) 분석 중...", end=" ")

    df = self.get_kr_stock_data(ticker)
    if df is None:
      print("❌")
      return []

    signals = []

    # 패턴 감지
    cup_signal = self.detect_cup_and_handle(df, ticker, 'KR')
    if cup_signal:
      signals.append(cup_signal)

    pivot_signal = self.detect_pivot_breakout(df, ticker, 'KR')
    if pivot_signal:
      signals.append(pivot_signal)

    base_signal = self.detect_base_breakout(df, ticker, 'KR')
    if base_signal:
      signals.append(base_signal)

    if signals:
      print("✅")
    else:
      print("⚪")

    return signals

  # ========================================
  # 메시지 포맷팅
  # ========================================

  def format_signal_message(self, signal: Dict) -> str:
    """신호를 텔레그램 메시지 형식으로 변환"""
    pattern = signal['pattern']
    ticker = signal['ticker']
    market = signal['market']

    # 시장 이모지
    market_emoji = "🇺🇸" if market == 'US' else "🇰🇷"
    market_text = "미국" if market == 'US' else "한국"

    # 티커 표시
    if market == 'US':
      ticker_display = f"<b>{ticker}</b>"
    else:
      ticker_display = f"<b>{signal.get('name', ticker)} ({ticker})</b>"

    # 가격 포맷
    if market == 'US':
      price_format = lambda x: f"${round(x, 2)}"
    else:
      price_format = lambda x: f"{int(x):,}원"

    # 패턴별 메시지
    if pattern == '컵앤핸들':
      msg = f"""
{market_emoji} <b>[컵앤핸들 패턴 감지]</b>

📊 시장: {market_text} 주식
🏢 종목: {ticker_display}
💰 현재가: {price_format(signal['current_price'])}
🎯 저항선: {price_format(signal['resistance'])}
📈 돌파율: {signal['breakout_pct']}%

📉 컵 깊이: {signal['cup_depth']}% (이상적: 12-33%)
🔧 핸들 깊이: {signal['handle_depth']}%

⚠️ 매수 타이밍: 돌파 후 5% 이내
⛔ 손절가: 매수가 -7~8%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    elif pattern == '피벗돌파':
      msg = f"""
{market_emoji} <b>[피벗 포인트 돌파!]</b>

📊 시장: {market_text} 주식
🏢 종목: {ticker_display}
💰 현재가: {price_format(signal['current_price'])}
🎯 돌파가: {price_format(signal['resistance'])}
📈 돌파율: {signal['breakout_pct']}%

📊 거래량 증가: +{signal['volume_surge']}%

✅ 강력한 매수 신호!
⛔ 손절가: 매수가 -7~8%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    elif pattern == '베이스돌파':
      msg = f"""
{market_emoji} <b>[베이스 돌파 감지]</b>

📊 시장: {market_text} 주식
🏢 종목: {ticker_display}
💰 현재가: {price_format(signal['current_price'])}
🎯 베이스 고점: {price_format(signal['base_high'])}
📈 돌파율: {signal['breakout_pct']}%

📊 거래량 증가: +{signal['volume_surge']}%
📉 횡보 변동성: {signal['base_volatility']}%

✅ 매수 고려 구간
⛔ 손절가: 매수가 -7~8%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    else:
      msg = f"{market_emoji} 신호 감지: {ticker_display} - {pattern}"

    return msg

  # ========================================
  # 통합 스캔
  # ========================================

  def run_unified_scan(self, us_tickers: List[str] = None,
      kr_tickers: List[str] = None,
      scan_us: bool = True, scan_kr: bool = True):
    """통합 스캔 실행"""
    print(f"\n{'=' * 60}")
    print(f"🔍 윌리엄 오닐 돌파매매 통합 스캔 시작")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    total_stocks = 0
    if scan_us and us_tickers:
      total_stocks += len(us_tickers)
    if scan_kr and kr_tickers:
      total_stocks += len(kr_tickers)

    print(f"📊 총 종목 수: {total_stocks}개")
    if scan_us and us_tickers:
      print(f"   🇺🇸 미국: {len(us_tickers)}개")
    if scan_kr and kr_tickers:
      print(f"   🇰🇷 한국: {len(kr_tickers)}개")
    print(f"{'=' * 60}\n")

    all_signals = []

    # 미국 주식 스캔
    if scan_us and us_tickers:
      print("🇺🇸 미국 주식 스캔 시작...\n")
      for ticker in us_tickers:
        try:
          signals = self.analyze_us_stock(ticker)
          if signals:
            for signal in signals:
              all_signals.append(signal)
              msg = self.format_signal_message(signal)
              self.send_telegram_message(msg)
              print(f"   ✅ {ticker}: {signal['pattern']} 신호 발견!")
              time.sleep(1)
        except Exception as e:
          print(f"   ⚠️  {ticker} 처리 중 오류: {e}")
          continue
      print()

    # 한국 주식 스캔
    if scan_kr and kr_tickers:
      print("🇰🇷 한국 주식 스캔 시작...\n")
      for ticker in kr_tickers:
        try:
          signals = self.analyze_kr_stock(ticker)
          if signals:
            for signal in signals:
              all_signals.append(signal)
              msg = self.format_signal_message(signal)
              self.send_telegram_message(msg)
              stock_name = signal.get('name', ticker)
              print(f"   ✅ {stock_name}({ticker}): {signal['pattern']} 신호 발견!")
              time.sleep(2)
        except Exception as e:
          print(f"   ⚠️  {ticker} 처리 중 오류: {e}")
          continue
      print()

    # 결과 요약
    if not all_signals:
      print("⚠️  현재 돌파 신호를 보이는 종목이 없습니다.")
    else:
      us_signals = [s for s in all_signals if s['market'] == 'US']
      kr_signals = [s for s in all_signals if s['market'] == 'KR']

      print(f"📊 총 {len(all_signals)}개 신호 발견")
      if us_signals:
        print(f"   🇺🇸 미국: {len(us_signals)}개")
      if kr_signals:
        print(f"   🇰🇷 한국: {len(kr_signals)}개")

    print(f"\n{'=' * 60}")
    print("✅ 스캔 완료")
    print(f"{'=' * 60}\n")

    return all_signals


def get_kospi_top_stocks(n: int = 50) -> List[str]:
  """KOSPI 시가총액 상위 종목 가져오기"""
  try:
    today = datetime.now().strftime("%Y%m%d")
    df = stock.get_market_cap_by_ticker(today, market="KOSPI")
    df = df.sort_values('시가총액', ascending=False)
    tickers = df.head(n).index.tolist()
    return tickers
  except Exception as e:
    print(f"⚠️  KOSPI 종목 조회 실패: {e}")
    return []


def get_kosdaq_top_stocks(n: int = 30) -> List[str]:
  """KOSDAQ 시가총액 상위 종목 가져오기"""
  try:
    today = datetime.now().strftime("%Y%m%d")
    df = stock.get_market_cap_by_ticker(today, market="KOSDAQ")
    df = df.sort_values('시가총액', ascending=False)
    tickers = df.head(n).index.tolist()
    return tickers
  except Exception as e:
    print(f"⚠️  KOSDAQ 종목 조회 실패: {e}")
    return []


def main():
  """메인 실행 함수"""

  # ========================================
  # 설정 불러오기
  # ========================================

  if USE_CONFIG_FILE:
    # config.py에서 설정 불러오기
    TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
    CHAT_ID = config.CHAT_ID
    US_WATCH_LIST = config.US_WATCH_LIST
    KR_WATCH_LIST = config.KR_WATCH_LIST
    SCAN_INTERVAL = config.SCAN_INTERVAL

    # 시장별 스캔 여부
    SCAN_US = getattr(config, 'SCAN_US_MARKET', True)
    SCAN_KR = getattr(config, 'SCAN_KR_MARKET', True)
    USE_AUTO_WATCHLIST = getattr(config, 'USE_AUTO_WATCHLIST', False)

    print("✅ config.py에서 설정을 불러왔습니다.\n")
  else:
    print("⚠️  config.py를 사용하려면:")
    print("   1. config_example.py를 config.py로 복사")
    print("   2. config.py를 열어서 설정 수정")
    print("\n기본 설정으로 실행합니다...\n")

    # 기본 설정
    TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "YOUR_CHAT_ID_HERE"

    US_WATCH_LIST = [
      "AAPL", "MSFT", "GOOGL", "AMZN", "META",
      "NVDA", "TSLA", "AMD", "CRM", "NFLX"
    ]

    KR_WATCH_LIST = [
      "005930", "000660", "035420", "373220", "035720"
    ]

    SCAN_US = True
    SCAN_KR = True
    USE_AUTO_WATCHLIST = False
    SCAN_INTERVAL = 3600

  # ========================================

  # 봇 초기화
  detector = UnifiedBreakoutDetector(TELEGRAM_TOKEN, CHAT_ID)

  # 자동 감시 종목 선택 (한국만)
  if USE_AUTO_WATCHLIST and SCAN_KR:
    print("📊 한국 주식: 자동으로 감시 종목 선택 중...")
    kospi_stocks = get_kospi_top_stocks(40)
    kosdaq_stocks = get_kosdaq_top_stocks(20)
    KR_WATCH_LIST = kospi_stocks + kosdaq_stocks
    print(f"✅ 한국 주식 {len(KR_WATCH_LIST)}개 종목 선택 완료\n")

  # 시작 메시지
  markets = []
  if SCAN_US:
    markets.append(f"🇺🇸 미국({len(US_WATCH_LIST)}개)")
  if SCAN_KR:
    markets.append(f"🇰🇷 한국({len(KR_WATCH_LIST)}개)")

  start_msg = f"""
🤖 <b>윌리엄 오닐 돌파매매 통합 봇 시작</b>

📊 감시 시장: {' + '.join(markets)}
⏰ 스캔 주기: {SCAN_INTERVAL // 60}분
📈 감지 패턴:
  - 컵앤핸들
  - 피벗 포인트 돌파
  - 베이스 돌파

💬 명령어:
  /scan - 즉시 스캔 실행

시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
  detector.send_telegram_message(start_msg)
  print(start_msg)
  print(f"🔧 Chat ID: {CHAT_ID}")
  print(f"📱 텔레그램 메시지를 5초마다 확인합니다.\n")

  # 무한 루프 실행
  try:
    last_scan_time = datetime.now()
    check_counter = 0  # 메시지 확인 카운터

    while True:
      current_time = datetime.now()
      time_since_last_scan = (current_time - last_scan_time).total_seconds()

      # /scan 명령어 확인
      if detector.check_telegram_messages():
        # 즉시 스캔 실행
        detector.send_telegram_message("🔍 수동 스캔을 시작합니다...")
        detector.run_unified_scan(
            us_tickers=US_WATCH_LIST if SCAN_US else None,
            kr_tickers=KR_WATCH_LIST if SCAN_KR else None,
            scan_us=SCAN_US,
            scan_kr=SCAN_KR
        )
        last_scan_time = datetime.now()
        detector.send_telegram_message("✅ 수동 스캔 완료!")
        check_counter = 0  # 카운터 리셋

      # 정기 스캔 시간 확인
      elif time_since_last_scan >= SCAN_INTERVAL:
        print("\n⏰ 정기 스캔 시작...")
        detector.run_unified_scan(
            us_tickers=US_WATCH_LIST if SCAN_US else None,
            kr_tickers=KR_WATCH_LIST if SCAN_KR else None,
            scan_us=SCAN_US,
            scan_kr=SCAN_KR
        )
        last_scan_time = datetime.now()
        check_counter = 0  # 카운터 리셋

      # 30초마다 (6번 체크할 때마다) 상태 출력
      if check_counter % 6 == 0:
        next_scan = last_scan_time + timedelta(seconds=SCAN_INTERVAL)
        remaining = int((next_scan - current_time).total_seconds())
        if remaining > 0:
          print(f"💤 대기중... (다음 스캔까지 {remaining}초 | /scan 명령어로 즉시 스캔)")

      check_counter += 1

      # 5초 대기 (메시지 체크 간격)
      time.sleep(5)

  except KeyboardInterrupt:
    print("\n\n⛔ 프로그램 종료")
    detector.send_telegram_message("⛔ 윌리엄 오닐 돌파매매 통합 봇 종료")


if __name__ == "__main__":
  main()
