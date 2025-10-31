"""
윌리엄 오닐 돌파매매(CAN SLIM) 통합 알림 시스템 - 스마트 버전
- 시간대별 자동 시장 선택 (한국 장중/미국 장중)
- 텔레그램 명령어로 종목 관리
- 미국 주식 + 한국 주식 통합 지원
- 컵앤핸들, 피벗 포인트, 베이스 돌파 패턴 감지
"""

import json
import os
import threading
import time
import warnings
from datetime import datetime, timedelta, time as dt_time
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


class SmartUnifiedBreakoutDetector:
  """스마트 통합 돌파매매 패턴 감지 클래스"""

  def __init__(self, telegram_token: str, chat_id: str,
      watchlist_file: str = "watchlist.json"):
    """
    Args:
        telegram_token: 텔레그램 봇 토큰
        chat_id: 텔레그램 채팅 ID
        watchlist_file: 감시 종목 저장 파일
    """
    self.telegram_token = telegram_token
    self.chat_id = chat_id
    self.base_url = f"https://api.telegram.org/bot{telegram_token}"
    self.watchlist_file = watchlist_file
    self.last_update_id = 0

    # 감시 종목 로드
    self.us_watchlist, self.kr_watchlist = self.load_watchlist()

    print(f"✅ 감시 종목 로드 완료")
    print(f"   🇺🇸 미국: {len(self.us_watchlist)}개")
    print(f"   🇰🇷 한국: {len(self.kr_watchlist)}개")

  # ========================================
  # 감시 종목 관리
  # ========================================

  def load_watchlist(self) -> tuple:
    """감시 종목 파일에서 로드"""
    if os.path.exists(self.watchlist_file):
      try:
        with open(self.watchlist_file, 'r', encoding='utf-8') as f:
          data = json.load(f)
          return data.get('us', []), data.get('kr', [])
      except Exception as e:
        print(f"⚠️  감시 종목 로드 실패: {e}")

    # 기본 감시 종목 (파일이 없을 때)
    return (
      ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
      ["005930", "000660", "035420"]
    )

  def save_watchlist(self):
    """감시 종목 파일에 저장"""
    try:
      data = {
        'us': self.us_watchlist,
        'kr': self.kr_watchlist,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      }
      with open(self.watchlist_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
      return True
    except Exception as e:
      print(f"❌ 감시 종목 저장 실패: {e}")
      return False

  def add_us_stock(self, ticker: str) -> str:
    """미국 주식 추가"""
    ticker = ticker.upper().strip()
    if ticker in self.us_watchlist:
      return f"⚠️  {ticker}는 이미 감시 중입니다."

    self.us_watchlist.append(ticker)
    if self.save_watchlist():
      return f"✅ 🇺🇸 {ticker} 추가 완료!\n현재 미국 종목: {len(self.us_watchlist)}개"
    else:
      self.us_watchlist.remove(ticker)
      return "❌ 저장 실패"

  def add_kr_stock(self, ticker: str) -> str:
    """한국 주식 추가"""
    ticker = ticker.strip()
    if ticker in self.kr_watchlist:
      try:
        name = stock.get_market_ticker_name(ticker)
        return f"⚠️  {name}({ticker})는 이미 감시 중입니다."
      except:
        return f"⚠️  {ticker}는 이미 감시 중입니다."

    self.kr_watchlist.append(ticker)
    if self.save_watchlist():
      try:
        name = stock.get_market_ticker_name(ticker)
        return f"✅ 🇰🇷 {name}({ticker}) 추가 완료!\n현재 한국 종목: {len(self.kr_watchlist)}개"
      except:
        return f"✅ 🇰🇷 {ticker} 추가 완료!\n현재 한국 종목: {len(self.kr_watchlist)}개"
    else:
      self.kr_watchlist.remove(ticker)
      return "❌ 저장 실패"

  def remove_us_stock(self, ticker: str) -> str:
    """미국 주식 삭제"""
    ticker = ticker.upper().strip()
    if ticker not in self.us_watchlist:
      return f"⚠️  {ticker}는 감시 목록에 없습니다."

    self.us_watchlist.remove(ticker)
    if self.save_watchlist():
      return f"✅ 🇺🇸 {ticker} 삭제 완료!\n현재 미국 종목: {len(self.us_watchlist)}개"
    else:
      self.us_watchlist.append(ticker)
      return "❌ 저장 실패"

  def remove_kr_stock(self, ticker: str) -> str:
    """한국 주식 삭제"""
    ticker = ticker.strip()
    if ticker not in self.kr_watchlist:
      return f"⚠️  {ticker}는 감시 목록에 없습니다."

    try:
      name = stock.get_market_ticker_name(ticker)
      stock_display = f"{name}({ticker})"
    except:
      stock_display = ticker

    self.kr_watchlist.remove(ticker)
    if self.save_watchlist():
      return f"✅ 🇰🇷 {stock_display} 삭제 완료!\n현재 한국 종목: {len(self.kr_watchlist)}개"
    else:
      self.kr_watchlist.append(ticker)
      return "❌ 저장 실패"

  def list_watchlist(self) -> str:
    """감시 종목 목록 조회"""
    msg = "📊 <b>현재 감시 종목</b>\n\n"

    msg += f"🇺🇸 <b>미국 주식</b> ({len(self.us_watchlist)}개)\n"
    if self.us_watchlist:
      msg += ", ".join(self.us_watchlist)
    else:
      msg += "없음"

    msg += f"\n\n🇰🇷 <b>한국 주식</b> ({len(self.kr_watchlist)}개)\n"
    if self.kr_watchlist:
      kr_names = []
      for ticker in self.kr_watchlist:
        try:
          name = stock.get_market_ticker_name(ticker)
          kr_names.append(f"{name}({ticker})")
        except:
          kr_names.append(ticker)
      msg += ", ".join(kr_names)
    else:
      msg += "없음"

    return msg

  # ========================================
  # 시간대 체크
  # ========================================

  def get_market_status(self) -> Dict[str, bool]:
    """현재 시간에 따른 시장 상태 확인"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()  # 0=월요일, 6=일요일

    # 주말 체크
    is_weekend = weekday >= 5

    # 한국 장중: 09:00 - 15:30 (평일)
    kr_open = dt_time(9, 0)
    kr_close = dt_time(15, 30)
    is_kr_market = (not is_weekend) and (kr_open <= current_time <= kr_close)

    # 미국 장중 (한국 시간): 22:30 - 06:00 다음날
    # 여름시간(3월 둘째주 ~ 11월 첫째주): 22:30 - 05:00
    # 겨울시간: 23:30 - 06:00
    # 간단하게 22:30 - 06:00으로 설정
    us_open_night = dt_time(22, 30)
    us_close_morning = dt_time(6, 0)

    is_us_market = False
    if not is_weekend:
      # 22:30 이후 (당일 밤)
      if current_time >= us_open_night:
        is_us_market = True
      # 06:00 이전 (다음날 새벽)
      elif current_time <= us_close_morning:
        is_us_market = True

    return {
      'kr': is_kr_market,
      'us': is_us_market,
      'time': now.strftime('%H:%M:%S'),
      'weekday': weekday
    }

  # ========================================
  # 텔레그램 메시지
  # ========================================

  def send_telegram_message(self, message: str):
    """텔레그램으로 메시지 전송"""
    try:
      payload = {
        'chat_id': self.chat_id,
        'text': message,
        'parse_mode': 'HTML'
      }
      response = requests.post(f"{self.base_url}/sendMessage", data=payload)
      if response.status_code == 200:
        print(f"✅ 텔레그램 전송 성공")
      else:
        print(f"❌ 텔레그램 전송 실패: {response.status_code}")
    except Exception as e:
      print(f"❌ 텔레그램 전송 오류: {e}")

  # ========================================
  # 텔레그램 명령어 처리
  # ========================================

  def process_command(self, message: str) -> str:
    """텔레그램 명령어 처리"""
    parts = message.strip().split()
    if not parts:
      return None

    command = parts[0].lower()

    # 도움말
    if command == '/help' or command == '/start':
      return """
🤖 <b>윌리엄 오닐 돌파매매 봇 명령어</b>

<b>종목 관리:</b>
/add_us [티커] - 미국 주식 추가
  예: /add_us AAPL

/add_kr [종목코드] - 한국 주식 추가
  예: /add_kr 005930

/remove_us [티커] - 미국 주식 삭제
  예: /remove_us AAPL

/remove_kr [종목코드] - 한국 주식 삭제
  예: /remove_kr 005930

/list - 현재 감시 종목 보기

/status - 시장 상태 확인

<b>팁:</b>
• 봇이 자동으로 장 시간에 맞춰 스캔합니다
• 한국: 09:00-15:30
• 미국: 22:30-06:00
"""

    # 종목 추가/삭제
    elif command == '/add_us':
      if len(parts) < 2:
        return "❌ 사용법: /add_us [티커]\n예: /add_us AAPL"
      return self.add_us_stock(parts[1])

    elif command == '/add_kr':
      if len(parts) < 2:
        return "❌ 사용법: /add_kr [종목코드]\n예: /add_kr 005930"
      return self.add_kr_stock(parts[1])

    elif command == '/remove_us':
      if len(parts) < 2:
        return "❌ 사용법: /remove_us [티커]\n예: /remove_us AAPL"
      return self.remove_us_stock(parts[1])

    elif command == '/remove_kr':
      if len(parts) < 2:
        return "❌ 사용법: /remove_kr [종목코드]\n예: /remove_kr 005930"
      return self.remove_kr_stock(parts[1])

    # 목록 보기
    elif command == '/list':
      return self.list_watchlist()

    # 상태 확인
    elif command == '/status':
      market_status = self.get_market_status()
      msg = "📊 <b>시장 상태</b>\n\n"
      msg += f"⏰ 현재 시간: {market_status['time']}\n\n"

      if market_status['kr']:
        msg += "🇰🇷 한국 장중 (09:00-15:30)\n"
        msg += f"   감시 중: {len(self.kr_watchlist)}개 종목\n"
      else:
        msg += "🇰🇷 한국 장 마감\n"

      if market_status['us']:
        msg += "🇺🇸 미국 장중 (22:30-06:00)\n"
        msg += f"   감시 중: {len(self.us_watchlist)}개 종목\n"
      else:
        msg += "🇺🇸 미국 장 마감\n"

      if not market_status['kr'] and not market_status['us']:
        msg += "\n⏸️  현재 휴장 시간입니다"

      return msg

    return None

  def check_telegram_updates(self):
    """텔레그램 메시지 확인 (명령어 처리)"""
    try:
      url = f"{self.base_url}/getUpdates"
      params = {
        'offset': self.last_update_id + 1,
        'timeout': 10
      }
      response = requests.get(url, params=params, timeout=15)

      if response.status_code == 200:
        data = response.json()
        if data.get('ok') and data.get('result'):
          for update in data['result']:
            self.last_update_id = update['update_id']

            if 'message' in update and 'text' in update['message']:
              message_text = update['message']['text']
              chat_id = str(update['message']['chat']['id'])

              # 올바른 채팅방에서 온 메시지만 처리
              if chat_id == str(self.chat_id):
                reply = self.process_command(message_text)
                if reply:
                  self.send_telegram_message(reply)
    except Exception as e:
      print(f"⚠️  텔레그램 업데이트 확인 오류: {e}")

  def start_command_listener(self):
    """백그라운드에서 텔레그램 명령어 리스너 시작"""

    def listener_loop():
      while True:
        try:
          self.check_telegram_updates()
          time.sleep(2)  # 2초마다 체크
        except Exception as e:
          print(f"⚠️  리스너 오류: {e}")
          time.sleep(5)

    thread = threading.Thread(target=listener_loop, daemon=True)
    thread.start()
    print("✅ 텔레그램 명령어 리스너 시작")

  # ========================================
  # 미국 주식 관련 메서드
  # ========================================

  def get_us_stock_data(self, ticker: str, period: str = "6mo") -> pd.DataFrame:
    """미국 주식 데이터 가져오기"""
    try:
      stock_obj = yf.Ticker(ticker)
      df = stock_obj.history(period=period)
      if df.empty:
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

      df = stock.get_market_ohlcv_by_date(
          start_date.strftime("%Y%m%d"),
          end_date.strftime("%Y%m%d"),
          ticker
      )

      if df.empty:
        return None

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
  # 패턴 감지 메서드 (기존과 동일)
  # ========================================

  def detect_pivot_breakout(self, df: pd.DataFrame, ticker: str,
      market: str) -> Dict:
    """피벗 포인트 돌파 감지"""
    if df is None or len(df) < 30:
      return None

    try:
      recent = df.tail(30).copy()
      avg_volume = recent['Volume'].iloc[:-1].mean()
      current_volume = recent['Volume'].iloc[-1]
      volume_surge = (current_volume / avg_volume - 1) * 100

      close = recent['Close'].values
      current_price = close[-1]
      resistance = np.max(close[-20:-1])

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
      pass

    return None

  # ========================================
  # 종목 분석
  # ========================================

  def analyze_us_stock(self, ticker: str) -> List[Dict]:
    """미국 주식 분석"""
    df = self.get_us_stock_data(ticker)
    if df is None:
      return []

    signals = []
    pivot_signal = self.detect_pivot_breakout(df, ticker, 'US')
    if pivot_signal:
      signals.append(pivot_signal)

    return signals

  def analyze_kr_stock(self, ticker: str) -> List[Dict]:
    """한국 주식 분석"""
    df = self.get_kr_stock_data(ticker)
    if df is None:
      return []

    signals = []
    pivot_signal = self.detect_pivot_breakout(df, ticker, 'KR')
    if pivot_signal:
      signals.append(pivot_signal)

    return signals

  # ========================================
  # 메시지 포맷팅
  # ========================================

  def format_signal_message(self, signal: Dict) -> str:
    """신호를 텔레그램 메시지 형식으로 변환"""
    pattern = signal['pattern']
    ticker = signal['ticker']
    market = signal['market']

    market_emoji = "🇺🇸" if market == 'US' else "🇰🇷"
    market_text = "미국" if market == 'US' else "한국"

    if market == 'US':
      ticker_display = f"<b>{ticker}</b>"
      price_format = lambda x: f"${round(x, 2)}"
    else:
      ticker_display = f"<b>{signal.get('name', ticker)} ({ticker})</b>"
      price_format = lambda x: f"{int(x):,}원"

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
    return msg

  # ========================================
  # 스마트 스캔 (시간대별 자동 선택)
  # ========================================

  def run_smart_scan(self):
    """시간대에 따라 자동으로 시장 선택하여 스캔"""
    market_status = self.get_market_status()

    print(f"\n{'=' * 60}")
    print(f"🔍 윌리엄 오닐 스마트 스캔")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    scan_kr = market_status['kr']
    scan_us = market_status['us']

    if not scan_kr and not scan_us:
      print("⏸️  휴장 시간입니다. 다음 장 시작까지 대기...")
      print(f"{'=' * 60}\n")
      return []

    if scan_kr:
      print(f"🇰🇷 한국 장중 - 한국 주식 스캔 ({len(self.kr_watchlist)}개)")
    if scan_us:
      print(f"🇺🇸 미국 장중 - 미국 주식 스캔 ({len(self.us_watchlist)}개)")

    print(f"{'=' * 60}\n")

    all_signals = []

    # 미국 주식 스캔
    if scan_us and self.us_watchlist:
      print("🇺🇸 미국 주식 스캔 중...\n")
      for ticker in self.us_watchlist:
        try:
          print(f"  🔍 {ticker}...", end=" ")
          signals = self.analyze_us_stock(ticker)
          if signals:
            for signal in signals:
              all_signals.append(signal)
              msg = self.format_signal_message(signal)
              self.send_telegram_message(msg)
              print(f"✅ 신호!")
              time.sleep(1)
          else:
            print("⚪")
        except Exception as e:
          print(f"❌ 오류")
      print()

    # 한국 주식 스캔
    if scan_kr and self.kr_watchlist:
      print("🇰🇷 한국 주식 스캔 중...\n")
      for ticker in self.kr_watchlist:
        try:
          name = self.get_kr_stock_name(ticker)
          print(f"  🔍 {name}({ticker})...", end=" ")
          signals = self.analyze_kr_stock(ticker)
          if signals:
            for signal in signals:
              all_signals.append(signal)
              msg = self.format_signal_message(signal)
              self.send_telegram_message(msg)
              print(f"✅ 신호!")
              time.sleep(2)
          else:
            print("⚪")
        except Exception as e:
          print(f"❌ 오류")
      print()

    # 결과 요약
    if all_signals:
      us_signals = [s for s in all_signals if s['market'] == 'US']
      kr_signals = [s for s in all_signals if s['market'] == 'KR']

      print(f"📊 {len(all_signals)}개 신호 발견", end="")
      if us_signals:
        print(f" (🇺🇸 {len(us_signals)}개", end="")
      if kr_signals:
        if us_signals:
          print(f", 🇰🇷 {len(kr_signals)}개)", end="")
        else:
          print(f" (🇰🇷 {len(kr_signals)}개)", end="")
      print()
    else:
      print("⚪ 신호 없음")

    print(f"\n{'=' * 60}\n")

    return all_signals


def main():
  """메인 실행 함수"""

  # ========================================
  # 설정 불러오기
  # ========================================

  if USE_CONFIG_FILE:
    TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
    CHAT_ID = config.CHAT_ID
    print("✅ config.py에서 설정을 불러왔습니다.\n")
  else:
    print("⚠️  config.py를 사용하려면:")
    print("   1. config_example.py를 config.py로 복사")
    print("   2. config.py를 열어서 설정 수정")
    print("\n기본 설정으로 실행합니다...\n")

    TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "YOUR_CHAT_ID_HERE"

  # 스캔 주기: 30분 (1800초)
  SCAN_INTERVAL = 1800

  # ========================================

  # 봇 초기화
  detector = SmartUnifiedBreakoutDetector(TELEGRAM_TOKEN, CHAT_ID)

  # 텔레그램 명령어 리스너 시작
  detector.start_command_listener()

  # 시작 메시지
  market_status = detector.get_market_status()
  status_text = []
  if market_status['kr']:
    status_text.append("🇰🇷 한국 장중")
  if market_status['us']:
    status_text.append("🇺🇸 미국 장중")
  if not status_text:
    status_text.append("⏸️  휴장 중")

  start_msg = f"""
🤖 <b>윌리엄 오닐 스마트 돌파매매 봇 시작</b>

📊 감시 종목:
   🇺🇸 미국: {len(detector.us_watchlist)}개
   🇰🇷 한국: {len(detector.kr_watchlist)}개

⏰ 스캔 주기: 30분
🕐 현재 상태: {' + '.join(status_text)}

📈 자동 스캔:
   • 한국 장중 (09:00-15:30)
   • 미국 장중 (22:30-06:00)

💬 명령어: /help

시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
  detector.send_telegram_message(start_msg)
  print(start_msg)

  # 무한 루프 실행
  try:
    while True:
      detector.run_smart_scan()

      # 다음 스캔까지 대기
      next_scan = datetime.now() + timedelta(seconds=SCAN_INTERVAL)
      print(f"⏰ 다음 스캔: {next_scan.strftime('%Y-%m-%d %H:%M:%S')}")
      print(f"💤 30분 대기 중...\n")
      time.sleep(SCAN_INTERVAL)

  except KeyboardInterrupt:
    print("\n\n⛔ 프로그램 종료")
    detector.send_telegram_message("⛔ 윌리엄 오닐 스마트 돌파매매 봇 종료")


if __name__ == "__main__":
  main()
