"""
윌리엄 오닐 돌파매매 - 한 번만 스캔하는 테스트 버전
텔레그램 연동 없이 콘솔에만 결과 출력
"""

import warnings
from datetime import datetime

import numpy as np
import yfinance as yf

warnings.filterwarnings('ignore')


def get_stock_data(ticker: str, period: str = "6mo"):
  """주식 데이터 가져오기"""
  try:
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df if not df.empty else None
  except Exception as e:
    print(f"❌ {ticker} 데이터 조회 실패: {e}")
    return None


def detect_pivot_breakout(df, ticker: str):
  """피벗 포인트 돌파 감지 (가장 간단하고 효과적인 패턴)"""
  if df is None or len(df) < 30:
    return None

  try:
    recent = df.tail(30).copy()

    # 거래량
    avg_volume = recent['Volume'].iloc[:-1].mean()
    current_volume = recent['Volume'].iloc[-1]
    volume_surge = (current_volume / avg_volume - 1) * 100

    # 가격
    close = recent['Close'].values
    current_price = close[-1]
    resistance = np.max(close[-20:-1])

    # 돌파 확인
    breakout = current_price > resistance
    breakout_pct = ((current_price - resistance) / resistance) * 100

    if breakout and volume_surge >= 50 and 0 < breakout_pct <= 5:
      return {
        'ticker': ticker,
        'current_price': round(current_price, 2),
        'resistance': round(resistance, 2),
        'breakout_pct': round(breakout_pct, 2),
        'volume_surge': round(volume_surge, 2)
      }
  except Exception as e:
    print(f"⚠️  {ticker} 분석 오류: {e}")

  return None


def analyze_stock(ticker: str):
  """종목 분석"""
  print(f"🔍 {ticker} 분석 중...", end=" ")

  df = get_stock_data(ticker)
  if df is None:
    print("❌ 데이터 없음")
    return None

  signal = detect_pivot_breakout(df, ticker)

  if signal:
    print("✅ 신호 발견!")
    return signal
  else:
    print("⚪ 신호 없음")
    return None


def print_signal(signal):
  """신호 출력"""
  print(f"""
{'=' * 60}
🚀 피벗 포인트 돌파 신호!

📊 종목: {signal['ticker']}
💰 현재가: ${signal['current_price']}
🎯 돌파가: ${signal['resistance']}
📈 돌파율: {signal['breakout_pct']}%
📊 거래량 증가: +{signal['volume_surge']}%

✅ 매수 고려 구간 (돌파 후 5% 이내)
⛔ 손절가: 매수가 -7~8%
{'=' * 60}
""")


def main():
  """메인 실행 함수"""

  print("""
╔══════════════════════════════════════════════════╗
║   윌리엄 오닐 돌파매매 스캐너 - 테스트 버전       ║
╚══════════════════════════════════════════════════╝
""")

  # 테스트할 종목 리스트
  test_tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "TSLA", "AMD", "CRM", "NFLX",
    "PLTR", "SNOW", "CRWD", "NET", "COIN"
  ]

  print(f"📅 스캔 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  print(f"📊 총 {len(test_tickers)}개 종목 분석\n")

  signals = []

  # 각 종목 분석
  for ticker in test_tickers:
    signal = analyze_stock(ticker)
    if signal:
      signals.append(signal)

  # 결과 출력
  print(f"\n{'=' * 60}")
  print(f"📊 스캔 완료: {len(signals)}개 신호 발견")
  print(f"{'=' * 60}\n")

  if signals:
    for signal in signals:
      print_signal(signal)
  else:
    print("⚠️  현재 돌파 신호를 보이는 종목이 없습니다.")
    print("💡 팁: 다른 시간에 다시 시도해보세요.\n")

  print("✅ 완료!")
  print("\n💡 실제 텔레그램 알림을 받으려면:")
  print("   → oneil_breakout_bot.py 파일을 사용하세요\n")


if __name__ == "__main__":
  main()
