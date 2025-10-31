"""
윌리엄 오닐 돌파매매(CAN SLIM) 자동 알림 시스템 - 한국 주식 버전
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
from pykrx import stock

warnings.filterwarnings('ignore')

# 설정 파일 import
try:
  import config

  USE_CONFIG_FILE = True
except ImportError:
  print("⚠️  config.py 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
  USE_CONFIG_FILE = False


class KoreanOneilBreakoutDetector:
  """한국 주식용 윌리엄 오닐 돌파매매 패턴 감지 클래스"""

  def __init__(self, telegram_token: str, chat_id: str):
    """
    Args:
        telegram_token: 텔레그램 봇 토큰
        chat_id: 텔레그램 채팅 ID
    """
    self.telegram_token = telegram_token
    self.chat_id = chat_id
    self.base_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

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

  def get_stock_name(self, ticker: str) -> str:
    """종목 이름 가져오기"""
    try:
      name = stock.get_market_ticker_name(ticker)
      return name if name else ticker
    except:
      return ticker

  def get_stock_data(self, ticker: str, days: int = 120) -> pd.DataFrame:
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

      # 컬럼명 확인 및 영문으로 변경 (유연하게 처리)
      # pykrx는 '시가', '고가', '저가', '종가', '거래량' 또는 '등락률' 포함 가능
      original_columns = df.columns.tolist()

      # 필요한 컬럼만 선택하고 이름 변경
      column_mapping = {
        '시가': 'Open',
        '고가': 'High',
        '저가': 'Low',
        '종가': 'Close',
        '거래량': 'Volume'
      }

      # 한글 컬럼명을 영문으로 변경
      df = df.rename(columns=column_mapping)

      # 필요한 컬럼만 선택 (OHLCV)
      required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
      df = df[required_columns]

      return df
    except Exception as e:
      print(f"❌ {ticker} 데이터 조회 실패: {e}")
      return None

  def detect_cup_and_handle(self, df: pd.DataFrame, ticker: str) -> Dict:
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
        stock_name = self.get_stock_name(ticker)
        return {
          'ticker': ticker,
          'name': stock_name,
          'pattern': '컵앤핸들',
          'cup_depth': round(cup_depth, 2),
          'handle_depth': round(handle_depth, 2),
          'resistance': int(resistance),
          'current_price': int(current_price),
          'breakout_pct': round(
              ((current_price - resistance) / resistance) * 100, 2)
        }
    except Exception as e:
      print(f"⚠️  {ticker} 컵앤핸들 분석 오류: {e}")

    return None

  def detect_pivot_breakout(self, df: pd.DataFrame, ticker: str) -> Dict:
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
        stock_name = self.get_stock_name(ticker)
        return {
          'ticker': ticker,
          'name': stock_name,
          'pattern': '피벗돌파',
          'resistance': int(resistance),
          'current_price': int(current_price),
          'breakout_pct': round(breakout_pct, 2),
          'volume_surge': round(volume_surge, 2)
        }
    except Exception as e:
      print(f"⚠️  {ticker} 피벗돌파 분석 오류: {e}")

    return None

  def detect_base_breakout(self, df: pd.DataFrame, ticker: str) -> Dict:
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
        stock_name = self.get_stock_name(ticker)
        return {
          'ticker': ticker,
          'name': stock_name,
          'pattern': '베이스돌파',
          'base_high': int(base_high),
          'current_price': int(current_price),
          'breakout_pct': round(breakout_pct, 2),
          'volume_surge': round(volume_surge, 2),
          'base_volatility': round(base_volatility, 2)
        }
    except Exception as e:
      print(f"⚠️  {ticker} 베이스돌파 분석 오류: {e}")

    return None

  def analyze_stock(self, ticker: str) -> List[Dict]:
    """종목 분석 및 신호 감지"""
    stock_name = self.get_stock_name(ticker)
    print(f"\n🔍 {stock_name}({ticker}) 분석 중...")

    df = self.get_stock_data(ticker)
    if df is None:
      return []

    signals = []

    # 패턴 감지
    cup_signal = self.detect_cup_and_handle(df, ticker)
    if cup_signal:
      signals.append(cup_signal)

    pivot_signal = self.detect_pivot_breakout(df, ticker)
    if pivot_signal:
      signals.append(pivot_signal)

    base_signal = self.detect_base_breakout(df, ticker)
    if base_signal:
      signals.append(base_signal)

    return signals

  def format_signal_message(self, signal: Dict) -> str:
    """신호를 텔레그램 메시지 형식으로 변환"""
    pattern = signal['pattern']
    ticker = signal['ticker']
    name = signal['name']

    if pattern == '컵앤핸들':
      msg = f"""
🏆 <b>[컵앤핸들 패턴 감지]</b>

📊 종목: <b>{name} ({ticker})</b>
💰 현재가: {signal['current_price']:,}원
🎯 저항선: {signal['resistance']:,}원
📈 돌파율: {signal['breakout_pct']}%

📉 컵 깊이: {signal['cup_depth']}% (이상적: 12-33%)
🔧 핸들 깊이: {signal['handle_depth']}%

⚠️ 매수 타이밍: 돌파 후 5% 이내
⛔ 손절가: 매수가 -7~8%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    elif pattern == '피벗돌파':
      msg = f"""
🚀 <b>[피벗 포인트 돌파!]</b>

📊 종목: <b>{name} ({ticker})</b>
💰 현재가: {signal['current_price']:,}원
🎯 돌파가: {signal['resistance']:,}원
📈 돌파율: {signal['breakout_pct']}%

📊 거래량 증가: +{signal['volume_surge']}%

✅ 강력한 매수 신호!
⛔ 손절가: 매수가 -7~8%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    elif pattern == '베이스돌파':
      msg = f"""
📈 <b>[베이스 돌파 감지]</b>

📊 종목: <b>{name} ({ticker})</b>
💰 현재가: {signal['current_price']:,}원
🎯 베이스 고점: {signal['base_high']:,}원
📈 돌파율: {signal['breakout_pct']}%

📊 거래량 증가: +{signal['volume_surge']}%
📉 횡보 변동성: {signal['base_volatility']}%

✅ 매수 고려 구간
⛔ 손절가: 매수가 -7~8%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    else:
      msg = f"신호 감지: {name}({ticker}) - {pattern}"

    return msg

  def run_scan(self, tickers: List[str]):
    """여러 종목 스캔 실행"""
    print(f"\n{'=' * 50}")
    print(f"🔍 윌리엄 오닐 돌파매매 스캔 시작 (한국 주식)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 종목 수: {len(tickers)}")
    print(f"{'=' * 50}")

    all_signals = []

    for ticker in tickers:
      try:
        signals = self.analyze_stock(ticker)
        if signals:
          for signal in signals:
            all_signals.append(signal)
            msg = self.format_signal_message(signal)
            self.send_telegram_message(msg)
            print(f"✅ {signal['name']}({ticker}): {signal['pattern']} 신호 발견!")
            time.sleep(2)  # API 제한 방지
      except Exception as e:
        print(f"⚠️  {ticker} 처리 중 오류: {e}")
        continue

    if not all_signals:
      print("\n⚠️  현재 돌파 신호를 보이는 종목이 없습니다.")
    else:
      summary = f"\n📊 총 {len(all_signals)}개 신호 발견"
      print(summary)

    print(f"\n{'=' * 50}")
    print("✅ 스캔 완료")
    print(f"{'=' * 50}\n")

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
    WATCH_LIST = config.KR_WATCH_LIST
    USE_AUTO_WATCHLIST = config.USE_AUTO_WATCHLIST
    SCAN_INTERVAL = config.SCAN_INTERVAL

    print("✅ config.py에서 설정을 불러왔습니다.")
  else:
    # config.py가 없을 때 기본 설정 사용
    print("⚠️  config.py를 사용하려면:")
    print("   1. config_example.py를 config.py로 복사")
    print("   2. config.py를 열어서 설정 수정")
    print("\n기본 설정으로 실행합니다...\n")

    # 텔레그램 봇 설정
    TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"  # 텔레그램 봇 토큰
    CHAT_ID = "YOUR_CHAT_ID_HERE"  # 텔레그램 채팅 ID

    # 감시할 종목 리스트 (한국 주식 종목코드)
    WATCH_LIST = [
      # 대형주
      "005930",  # 삼성전자
      "000660",  # SK하이닉스
      "035420",  # NAVER
      "207940",  # 삼성바이오로직스
      "005380",  # 현대차
      "051910",  # LG화학
      "006400",  # 삼성SDI
      "035720",  # 카카오

      # 2차전지
      "373220",  # LG에너지솔루션
      "086520",  # 에코프로
      "247540",  # 에코프로비엠

      # IT/바이오
      "068270",  # 셀트리온
      "091990",  # 셀트리온헬스케어
      "096770",  # SK이노베이션
      "028260",  # 삼성물산
    ]

    # 자동 감시 종목 선택
    USE_AUTO_WATCHLIST = False  # True로 설정하면 자동으로 상위 종목 선택

    # 스캔 주기 (초 단위)
    SCAN_INTERVAL = 3600  # 1시간마다

  # ========================================

  # 봇 초기화
  detector = KoreanOneilBreakoutDetector(TELEGRAM_TOKEN, CHAT_ID)

  # 자동 감시 종목 선택
  if USE_AUTO_WATCHLIST:
    print("📊 자동으로 감시 종목 선택 중...")
    kospi_stocks = get_kospi_top_stocks(40)
    kosdaq_stocks = get_kosdaq_top_stocks(20)
    WATCH_LIST = kospi_stocks + kosdaq_stocks
    print(f"✅ 총 {len(WATCH_LIST)}개 종목 선택 완료")

  # 시작 메시지
  start_msg = f"""
🤖 <b>윌리엄 오닐 돌파매매 봇 시작 (한국 주식)</b>

📊 감시 종목: {len(WATCH_LIST)}개
⏰ 스캔 주기: {SCAN_INTERVAL // 60}분
📈 감지 패턴:
  - 컵앤핸들
  - 피벗 포인트 돌파
  - 베이스 돌파

시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
  detector.send_telegram_message(start_msg)
  print(start_msg)

  # 무한 루프 실행
  try:
    while True:
      detector.run_scan(WATCH_LIST)

      # 다음 스캔까지 대기
      next_scan = datetime.now() + timedelta(seconds=SCAN_INTERVAL)
      print(f"⏰ 다음 스캔: {next_scan.strftime('%Y-%m-%d %H:%M:%S')}")
      print(f"💤 {SCAN_INTERVAL // 60}분 대기 중...\n")
      time.sleep(SCAN_INTERVAL)

  except KeyboardInterrupt:
    print("\n\n⛔ 프로그램 종료")
    detector.send_telegram_message("⛔ 윌리엄 오닐 돌파매매 봇 종료")


if __name__ == "__main__":
  main()
