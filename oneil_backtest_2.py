# oneil_backtest_fixed.py
# → 기존 기능 100% 유지 + look-ahead bias 완전 제거 + 정확한 시간순 백테스트

import warnings
from datetime import datetime
from typing import List, Dict, Tuple

import pandas as pd
import yfinance as yf
from pykrx import stock

warnings.filterwarnings('ignore')


class BacktestEngine:
  """윌리엄 오닐 돌파매매 백테스트 엔진 (시간순서 정숙)"""

  def __init__(self, initial_capital: float = 10_000_000):
    self.initial_capital = initial_capital
    self.cash = initial_capital  # 현재 현금
    self.positions: List[Dict] = []  # 현재 보유 포지션
    self.trade_history: List[Dict] = []  # 완료된 거래 기록
    self.start_date = None
    self.end_date = None

  # ============================================================
  # 데이터 수집 (기존 그대로)
  # ============================================================
  def get_us_stock_data(self, ticker: str, start_date: str,
      end_date: str) -> pd.DataFrame:
    try:
      df = yf.Ticker(ticker).history(start=start_date, end=end_date,
                                     auto_adjust=False)
      if df.empty:
        return None
      return df[['Open', 'High', 'Low', 'Close', 'Volume']]
    except Exception as e:
      print(f"US {ticker} 데이터 오류: {e}")
      return None

  def get_kr_stock_data(self, ticker: str, start_date: str,
      end_date: str) -> pd.DataFrame:
    try:
      s = start_date.replace('-', '')
      e = end_date.replace('-', '')
      df = stock.get_market_ohlcv_by_date(s, e, ticker)
      if df.empty:
        return None
      df = df.rename(
        columns={'시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close',
                 '거래량': 'Volume'})
      return df[['Open', 'High', 'Low', 'Close', 'Volume']]
    except Exception as e:
      print(f"KR {ticker} 데이터 오류: {e}")
      return None

  # ============================================================
  # 기존 패턴 감지 함수 (미래 데이터 사용 → 과거 데이터만 사용하도록 수정)
  # ============================================================
  def _detect_cup_and_handle(self, hist: pd.DataFrame) -> Tuple[bool, float]:
    """hist: 오늘까지의 데이터만 포함"""
    if len(hist) < 70:
      return False, 0
    window = hist.iloc[-70:]
    close = window['Close'].values
    mid = len(close) // 2
    left_peak = close[:mid].max()
    right_peak = close[mid:].max()
    bottom = close[mid - 10:mid + 10].min()
    cup_depth = (left_peak - bottom) / left_peak * 100
    handle_depth = (close[-15:].max() - close[-15:].min()) / close[
                                                             -15:].max() * 100
    resistance = window['Close'].iloc[-30:].max()
    breakout = close[-1] >= resistance * 0.99
    if 10 <= cup_depth <= 50 and handle_depth <= 15 and breakout:
      return True, resistance
    return False, 0

  def _detect_pivot_breakout(self, hist: pd.DataFrame) -> Tuple[bool, float]:
    if len(hist) < 40:
      return False, 0
    recent = hist.iloc[-40:]
    resistance = recent['High'].iloc[:-1].max()
    cur_price = recent['Close'].iloc[-1]
    cur_vol = recent['Volume'].iloc[-1]
    avg_vol = recent['Volume'].iloc[-20:-1].mean()
    if cur_price > resistance and cur_vol > avg_vol * 1.3:
      return True, resistance
    return False, 0

  def _detect_base_breakout(self, hist: pd.DataFrame) -> Tuple[bool, float]:
    if len(hist) < 50:
      return False, 0
    recent = hist.iloc[-50:]
    base_high = recent['High'].iloc[-35:-5].max()
    cur_price = recent['Close'].iloc[-1]
    cur_vol = recent['Volume'].iloc[-1]
    avg_vol = recent['Volume'].iloc[-35:-5].mean()
    volatility = (recent['High'].iloc[-35:-5].max() - recent['Low'].iloc[
                                                      -35:-5].min()) / recent[
                                                                         'Low'].iloc[
                                                                       -35:-5].min() * 100
    if volatility < 20 and cur_price > base_high and cur_vol > avg_vol * 1.2:
      return True, base_high
    return False, 0

  # ============================================================
  # 포지션 관리 (기존 그대로)
  # ============================================================
  def open_position(self, ticker: str, entry_date: datetime, entry_price: float,
      pattern: str, market: str):
    position_size = self.cash * 0.2
    shares = int(position_size // entry_price)
    if shares <= 0:
      return False
    cost = shares * entry_price
    self.cash -= cost
    pos = {
      'ticker': ticker, 'market': market, 'pattern': pattern,
      'entry_date': entry_date, 'entry_price': entry_price,
      'shares': shares, 'cost': cost,
      'stop_loss': entry_price * 0.92
    }
    self.positions.append(pos)
    return True

  def close_position(self, position: dict, exit_date: datetime,
      exit_price: float, reason: str):
    proceeds = position['shares'] * exit_price
    self.cash += proceeds
    profit = proceeds - position['cost']
    profit_pct = profit / position['cost'] * 100
    trade = {
      'ticker': position['ticker'], 'market': position['market'],
      'pattern': position['pattern'],
      'entry_date': position['entry_date'],
      'entry_price': position['entry_price'],
      'exit_date': exit_date, 'exit_price': exit_price,
      'shares': position['shares'], 'cost': position['cost'],
      'proceeds': proceeds, 'profit': profit,
      'profit_pct': profit_pct,
      'holding_days': (exit_date - position['entry_date']).days,
      'reason': reason
    }
    self.trade_history.append(trade)
    self.positions.remove(position)

  def check_exit_conditions(self, position: dict, current_date: datetime,
      current_price: float, high: float, low: float):
    if low <= position['stop_loss']:
      return True, position['stop_loss'], '손절'
    days = (current_date - position['entry_date']).days
    if days >= 30:
      return True, current_price, '보유기간만료'
    if current_price >= position['entry_price'] * 1.20:
      return True, current_price, '익절'
    return False, 0, ''

  # ============================================================
  # 핵심: 시간순서 포트폴리오 백테스트 (완전 새로 작성)
  # ============================================================
  def run_portfolio_backtest(self, tickers: List[str], start_date: str,
      end_date: str, market: str = 'US',
      patterns: List[str] = None):
    if patterns is None:
      patterns = ['cup', 'pivot', 'base']

    self.start_date = start_date
    self.end_date = end_date

    print(f"\n시간순서 백테스트 시작")
    print(
      f"기간: {start_date} ~ {end_date} | 종목 {len(tickers)}개 | 시장: {market}\n")

    # 1. 모든 종목 데이터 미리 로드
    data: Dict[str, pd.DataFrame] = {}
    for t in tickers:
      df = (self.get_us_stock_data(t, start_date, end_date) if market == 'US'
            else self.get_kr_stock_data(t, start_date, end_date))
      if df is not None and len(df) > 100:
        data[t] = df

    if not data:
      print("데이터 없음")
      return

    # 2. 공통 거래일 생성
    common_dates = None
    for df in data.values():
      if common_dates is None:
        common_dates = df.index
      else:
        common_dates = common_dates.intersection(df.index)
    dates = sorted(common_dates)

    # 3. 날짜별 시뮬레이션 (미래 데이터 절대 사용 금지)
    for current_date in dates:
      # 기존 포지션 청산 체크
      for pos in self.positions[:]:
        if pos['ticker'] not in data:
          continue
        try:
          day = data[pos['ticker']].loc[current_date]
          close, high, low = day['Close'], day['High'], day['Low']
          exit_flag, exit_price, reason = self.check_exit_conditions(
              pos, current_date, close, high, low)
          if exit_flag:
            self.close_position(pos, current_date, exit_price, reason)
        except:
          continue

      # 신규 진입 (최대 5개 포지션)
      if len(self.positions) >= 5:
        continue

      for ticker in tickers:
        if ticker not in data:
          continue
        if any(p['ticker'] == ticker for p in self.positions):
          continue

        df = data[ticker]
        if current_date not in df.index:
          continue
        hist = df.loc[:current_date]  # 오늘까지의 데이터만 사용 (핵심!)

        if len(hist) < 80:
          continue

        signal_found = False
        pattern_name = None

        if 'cup' in patterns:
          sig, _ = self._detect_cup_and_handle(hist)
          if sig:
            pattern_name = '컵앤핸들'
            signal_found = True

        if not signal_found and 'pivot' in patterns:
          sig, _ = self._detect_pivot_breakout(hist)
          if sig:
            pattern_name = '피벗돌파'
            signal_found = True

        if not signal_found and 'base' in patterns:
          sig, _ = self._detect_base_breakout(hist)
          if sig:
            pattern_name = '베이스돌파'
            signal_found = True

        if signal_found:
          price = df.loc[current_date, 'Close']
          self.open_position(ticker, current_date, price, pattern_name, market)
          break  # 한 티커에서 하나만 진입

    # 백테스트 종료 시 남은 포지션 청산
    last_date = dates[-1] if dates else datetime.now()
    for pos in self.positions[:]:
      try:
        price = data[pos['ticker']].loc[last_date, 'Close']
      except:
        price = pos['entry_price']
      self.close_position(pos, last_date, price, '백테스트종료')

    self.print_performance_report()

  # ============================================================
  # 기존 성과 분석·보고서 함수 (완전히 그대로)
  # ============================================================
  def calculate_performance(self) -> Dict:
    if not self.trade_history:
      return None
    df_trades = pd.DataFrame(self.trade_history)
    total_trades = len(df_trades)
    winning_trades = len(df_trades[df_trades['profit'] > 0])
    win_rate = winning_trades / total_trades * 100 if total_trades else 0
    total_profit = df_trades['profit'].sum()
    final_capital = self.cash + sum(p['cost'] for p in self.positions)
    total_return_pct = total_profit / self.initial_capital * 100

    try:
      start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
      end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
      years = (end_dt - start_dt).days / 365.25
      annualized_return = ((final_capital / self.initial_capital) ** (
            1 / years) - 1) * 100
    except:
      annualized_return = 0

    avg_profit = df_trades[df_trades['profit'] > 0][
      'profit_pct'].mean() if winning_trades else 0
    avg_loss = df_trades[df_trades['profit'] < 0][
      'profit_pct'].mean() if total_trades > winning_trades else 0
    max_profit = df_trades['profit_pct'].max()
    max_loss = df_trades['profit_pct'].min()
    avg_holding = df_trades['holding_days'].mean()

    pattern_stats = df_trades.groupby('pattern').agg({
      'profit_pct': ['count', 'mean', lambda x: (x > 0).sum() / len(x) * 100]
    }).round(2)

    return {
      'total_trades': total_trades, 'winning_trades': winning_trades,
      'win_rate': win_rate, 'initial_capital': self.initial_capital,
      'final_capital': final_capital, 'total_profit': total_profit,
      'total_return_pct': total_return_pct,
      'annualized_return': annualized_return,
      'avg_profit': avg_profit, 'avg_loss': avg_loss,
      'max_profit': max_profit, 'max_loss': max_loss,
      'avg_holding_days': avg_holding, 'pattern_stats': pattern_stats,
      'trade_df': df_trades
    }

  def print_performance_report(self):
    perf = self.calculate_performance()
    if perf is None:
      print("\n거래 내역이 없습니다.")
      return

    print(f"\n{'=' * 60}")
    print(f"백테스트 성과 보고서 (시간순서 정확)")
    print(f"{'=' * 60}\n")
    print(f"초기 자본:    {perf['initial_capital']:>15,.0f}원")
    print(f"최종 자본:    {perf['final_capital']:>15,.0f}원")
    print(
      f"총 수익:      {perf['total_profit']:>15,.0f}원 ({perf['total_return_pct']:>6.2f}%)")
    print(f"연환산 수익률: {perf['annualized_return']:>12.2f}%")
    print(f"\n총 거래: {perf['total_trades']:>3}건 | 승률: {perf['win_rate']:5.1f}%")
    print(
      f"평균 수익: {perf['avg_profit']:6.2f}% | 평균 손실: {perf['avg_loss']:6.2f}%")
    print(
      f"최대 수익: {perf['max_profit']:6.2f}% | 최대 손실: {perf['max_loss']:6.2f}%")
    print(f"평균 보유: {perf['avg_holding_days']:5.1f}일")

    print(f"\n패턴별 성과")
    print(f"{'패턴':<12} {'건수':>6} {'평균수익':>10} {'승률':>8}")
    print("-" * 40)
    for pat, row in perf['pattern_stats'].iterrows():
      cnt = int(row['profit_pct']['count'])
      avg = row['profit_pct']['mean']
      wr = row['profit_pct']['<lambda_0>']
      print(f"{pat:<12} {cnt:>5}건 {avg:>8.2f}% {wr:>7.1f}%")

    print(f"\n{'=' * 60}")

  def save_results(self, filename: str = "backtest_results.csv"):
    if self.trade_history:
      pd.DataFrame(self.trade_history).to_csv(filename, index=False,
                                              encoding='utf-8-sig')
      print(f"결과 저장: {filename}")


# ============================================================
# 실행 예시 (기존과 동일하게 사용 가능)
# ============================================================
if __name__ == "__main__":
  engine = BacktestEngine(initial_capital=100_000_000)

  us_tickers = [
    # 'NVDA', 'MSFT', 'AAPL', 'AMZN', 'GOOGL',  # 1-5위'META',
    # 'AVGO', 'TSLA', 'TSM',  # 6-10위
    # 'JPM', 'WMT', 'LLY', 'ORCL', 'V',  # 11-15위
    # 'NFLX', 'MA', 'XOM', 'COST', 'JNJ',  # 16-20위
    # 'HD', 'PG', 'SAP', 'PLTR', 'BAC',  # 21-25위
    # 'ABBV', 'ASML', 'NVO', 'KO', 'GE',  # 26-30위
    # 'PM', 'CSCO', 'UNH', 'BABA', 'CVX',  # 31-35위
    # 'IBM', 'TMUS', 'WFC', 'AMD', 'CRM',  # 36-40위
    # 'NVS', 'ABT', 'MS', 'TM', 'AZN',  # 41-45위
    # 'AXP', 'LIN', 'HSBC', 'MCD', 'DIS'  # 46-50위

    "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL",
    "META", "AVGO", "TSLA", "TSM",
    "JPM", "WMT", "LLY", "ORCL", "V",
    "NFLX", "MA", "XOM", "COST", "JNJ",
    "HD", "PG", "SAP", "PLTR", "BAC",
    "ABBV", "ASML", "NVO", "KO", "GE",
    "PM", "CSCO", "UNH", "BABA", "CVX",
    "IBM", "TMUS", "WFC", "AMD", "CRM",
    "NVS", "ABT", "MS", "TM", "AZN",
    "AXP", "LIN", "HSBC", "MCD", "DIS"
  ]

  engine.run_portfolio_backtest(
      tickers=us_tickers,
      start_date="2020-01-01",  # 2023년 강세장 → 거래 많이 나옴
      end_date="2025-11-18",
      market='US',
      patterns=['cup', 'pivot', 'base']
  )

  engine.save_results("oneil_fixed_2023.csv")
