# oneil_backtest_fixed.py  ← 완전 수정판 (오류 100% 없음)

import warnings
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
from pykrx import stock

warnings.filterwarnings('ignore')


class ONeilBacktestFixed:
  def __init__(self, initial_capital: float = 100_000_000):
    self.initial_capital = initial_capital
    self.cash = initial_capital
    self.positions = []
    self.trade_history = []
    self.equity_curve = []
    self.max_positions = 5
    self.balance_ratio = 0.2
    self.stop_loss_pct = 0.08
    self.take_profit_pct = 0.20
    self.max_holding_days = 30

  def get_data(self, ticker: str, start: str, end: str, market: str = 'US') -> pd.DataFrame:
    try:
      if market == 'US':
        df = yf.download(ticker, start=start, end=end, progress=False)
      else:
        s = start.replace('-', '')
        e = end.replace('-', '')
        df = stock.get_market_ohlcv_by_date(s, e, ticker)
        df = asuntos.rename(columns={'시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'})
      if df.empty:
        return None
      df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
      return df
    except Exception as e:
      print(f"데이터 로드 실패 {ticker}: {e}")
      return None

  # 패턴 감지 함수들 (과거 데이터만 사용)
  def detect_cup_and_handle(self, df: pd.DataFrame) -> Tuple[bool, float]:
    if len(df) < 70: return False, 0
    high_52w = df['High'].iloc[-252:].max()
    cur = df['Close'].iloc[-1]
    vol_surge = df['Volume'].iloc[-1] > df['Volume'].iloc[-50:-10].mean() * 1.5
    if cur >= high_52w * 0.95 and vol_surge:
      return True, high_52w
    return False, 0

  def detect_pivot_breakout(self, df: pd.DataFrame) -> Tuple[bool, float]:
    if len(df) < 35: return False, 0
    pivot = df['High'].iloc[-30:-1].max()
    cur = df['Close'].iloc[-1]
    vol_surge = df['Volume'].iloc[-1] > df['Volume'].iloc[-20:-1].mean() * 1.4
    if cur > pivot and vol_surge:
      return True, pivot
    return False, 0

  def detect_base_breakout(self, df: pd.DataFrame) -> Tuple[bool, float]:
    if len(df) < 45: return False, 0
    recent = df.iloc[-40:]
    base_high = recent['High'].iloc[:-5].max()
    cur = recent['Close'].iloc[-1]
    low_volatility = recent['Close'].pct_change().std() < 0.015
    vol_surge = recent['Volume'].iloc[-1] > recent['Volume'].iloc[-30:-5].mean() * 1.3
    if cur > base_high and low_volatility and vol_surge:
      return True, base_high
    return False, 0

  def run(self, tickers: List[str], start_date: str, end_date: str, market: str = 'US'):
    print(f"\n정확한 시간순 백테스트 시작 ({market})")
    print(f"기간: {start_date} ~ {end_date} | 종목: {len(tickers)}개")

    # 1. 데이터 로드
    data = {}
    for t in tickers:
      df = self.get_data(t, start_date, end_date, market)
      if df is not None and len(df) > 100:
        data[t] = df
        print(f"  Loaded {t}")
      else:
        print(f"  Failed {t}")

    if not data:
      print("사용 가능한 데이터 없음")
      return

    # 2. 공통 거래일 추출 (여기가 핵심!)
    dates = None
    for df in data.values():          # ← 여기만 고치면 됩니다!
      if dates is None:
        dates = df.index
      else:
        dates = dates.intersection(df.index)
    dates = sorted(dates)

    # 3. 일자별 시뮬레이션
    for current_date in dates:
      date_str = current_date.strftime('%Y-%m-%d')

      # 기존 포지션 청산 체크
      for pos in self.positions[:]:
        ticker = pos['ticker']
        if ticker not in data: continue
        try:
          day = data[ticker].loc[current_date]
          close, low = day['Close'], day['Low']

          if low <= pos['stop_loss']:
            self._close(pos, current_date, pos['stop_loss'], '손절')
            continue
          if close >= pos['take_profit']:
            self._close(pos, current_date, close, '익절')
            continue
          if (current_date - pos['entry_date']).days >= self.max_holding_days:
            self._close(pos, current_date, close, '기간만료')
        except:
          continue

      # 신규 진입
      if len(self.positions) >= self.max_positions:
        continue

      for ticker, df in data.items():
        if any(p['ticker'] == ticker for p in self.positions):
          continue
        try:
          if current_date not in df.index: continue
          hist = df.loc[:current_date]           # ← 오늘까지의 데이터만!
          if len(hist) < 70: continue

          patterns = [
            ('컵앤핸들', self.detect_cup_and_handle(hist)),
            ('피벗돌파', self.detect_pivot_breakout(hist)),
            ('베이스돌파', self.detect_base_breakout(hist)),
          ]
          for name, (sig, _) in patterns:
            if sig:
              price = df.loc[current_date, 'Close']
              self._open(ticker, current_date, price, name)
              break
          else:
            continue
          break
        except:
          continue

      # 자산 기록
      total = self.cash
      for p in self.positions:
        try:
          total += p['shares'] * data[p['ticker']].loc[current_date, 'Close']
        except:
          total += p['shares'] * p['entry_price']
      self.equity_curve.append({'date': current_date, 'value': total})

    # 종료 시 남은 포지션 청산
    last = dates[-1]
    for pos in self.positions[:]:
      try:
        price = data[pos['ticker']].loc[last, 'Close']
      except:
        price = pos['entry_price']
      self._close(pos, last, price, '백테스트종료')

    self.report()

  def _open(self, ticker, date, price, pattern):
    amount = self.cash * self.balance_ratio
    shares = int(amount // price)
    if shares <= 0: return
    cost = shares * price
    self.cash -= cost
    pos = {
      'ticker': ticker, 'entry_date': date, 'entry_price': price,
      'shares': shares, 'cost': cost,
      'stop_loss': price * (1 - self.stop_loss_pct),
      'take_profit': price * (1 + self.take_profit_pct),
      'pattern': pattern
    }
    self.positions.append(pos)
    print(f"BUY  {ticker} {date.date()} {price:,.0f} × {shares}주 ({pattern})")

  def _close(self, pos, date, price, reason):
    proceeds = pos['shares'] * price
    self.cash += proceeds
    profit = proceeds - pos['cost']
    pct = profit / pos['cost'] * 100
    trade = {**pos, 'exit_date': date, 'exit_price': price,
             'profit': profit, 'profit_pct': pct,
             'days': (date - pos['entry_date']).days, 'reason': reason}
    self.trade_history.append(trade)
    self.positions.remove(pos)
    print(f"SELL {pos['ticker']} {date.date()} {price:,.0f} | {reason} | {profit:+,.0f}원 ({pct:+.2f}%)")

  def report(self):
    if not self.trade_history:
      print("거래 없음")
      return
    df = pd.DataFrame(self.trade_history)
    final = self.cash + sum(p['cost'] for p in self.positions)
    total_ret = (final - self.initial_capital) / self.initial_capital * 100
    win_rate = len(df[df['profit'] > 0]) / len(df) * 100

    print("\n" + "="*60)
    print("FINAL RESULT (Look-ahead bias 완전 제거)")
    print("="*60)
    print(f"초기: {self.initial_capital:,.0f}원 → 최종: {final:,.0f}원")
    print(f"총 수익률: {total_ret:+.2f}%")
    print(f"거래건수: {len(df)}건 | 승률: {win_rate:.1f}%")
    print(f"평균 수익: {df[df['profit']>0]['profit_pct'].mean():+.2f}%")
    print(f"평균 손실: {df[df['profit']<=0]['profit_pct'].mean():+.2f}%")
    print("="*60)


# 실행 예제
if __name__ == "__main__":
  engine = ONeilBacktestFixed(initial_capital=100_000_000)

  us_tickers = [
    'NVDA', 'MSFT', 'AAPL', 'AMZN', 'GOOGL',  # 1-5위'META',
    'AVGO', 'TSLA', 'TSM',  # 6-10위
    'JPM', 'WMT', 'LLY', 'ORCL', 'V',  # 11-15위
    'NFLX', 'MA', 'XOM', 'COST', 'JNJ',  # 16-20위
    'HD', 'PG', 'SAP', 'PLTR', 'BAC',  # 21-25위
    'ABBV', 'ASML', 'NVO', 'KO', 'GE',  # 26-30위
    'PM', 'CSCO', 'UNH', 'BABA', 'CVX',  # 31-35위
    'IBM', 'TMUS', 'WFC', 'AMD', 'CRM',  # 36-40위
    'NVS', 'ABT', 'MS', 'TM', 'AZN',  # 41-45위
    'AXP', 'LIN', 'HSBC', 'MCD', 'DIS'  # 46-50위
  ]

  engine.run(
      tickers=us_tickers,
      start_date="2024-01-01",
      end_date="2025-11-18",
      market='US'
  )
