"""
윌리엄 오닐 돌파매매(CAN SLIM) 백테스트 시스템
- 컵앤핸들, 피벗돌파, 베이스돌파 패턴 백테스팅
- 미국/한국 주식 지원
- 손절/익절 시뮬레이션
- 성과 분석 및 보고서 생성
"""

import warnings
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from pykrx import stock

warnings.filterwarnings('ignore')


class BacktestEngine:
  """윌리엄 오닐 돌파매매 백테스트 엔진"""

  def __init__(self, initial_capital: float = 10000000):
    """
    Args:
        initial_capital: 초기 자본 (기본: 1000만원)
    """
    self.initial_capital = initial_capital
    self.capital = initial_capital
    self.positions = []  # 현재 포지션
    self.trade_history = []  # 거래 내역
    self.daily_portfolio_value = []  # 일별 포트폴리오 가치
    self.start_date = None  # 백테스트 시작일
    self.end_date = None  # 백테스트 종료일

  # ========================================
  # 데이터 수집
  # ========================================

  def get_us_stock_data(self, ticker: str, start_date: str,
      end_date: str) -> pd.DataFrame:
    """미국 주식 데이터 가져오기"""
    try:
      stock_obj = yf.Ticker(ticker)
      df = stock_obj.history(start=start_date, end=end_date)
      if df.empty:
        return None
      return df
    except Exception as e:
      print(f"❌ {ticker} 데이터 조회 실패: {e}")
      return None

  def get_kr_stock_data(self, ticker: str, start_date: str,
      end_date: str) -> pd.DataFrame:
    """한국 주식 데이터 가져오기"""
    try:
      start = datetime.strptime(start_date, '%Y-%m-%d').strftime("%Y%m%d")
      end = datetime.strptime(end_date, '%Y-%m-%d').strftime("%Y%m%d")

      df = stock.get_market_ohlcv_by_date(start, end, ticker)
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
      return df[['Open', 'High', 'Low', 'Close', 'Volume']]
    except Exception as e:
      print(f"❌ {ticker} 데이터 조회 실패: {e}")
      return None

  # ========================================
  # 패턴 감지
  # ========================================

  def detect_cup_and_handle(self, df: pd.DataFrame, idx: int) -> Tuple[
    bool, float]:
    """
    컵앤핸들 패턴 감지
    Returns: (신호발생여부, 저항선)
    """
    if idx < 60:
      return False, 0

    try:
      window = df.iloc[idx - 60:idx + 1]
      close = window['Close'].values

      # 컵 형성
      mid_idx = len(close) // 2
      left_peak = np.max(close[:mid_idx])
      right_peak = np.max(close[mid_idx:])
      bottom = np.min(close[mid_idx - 10:mid_idx + 10])
      cup_depth = ((left_peak - bottom) / left_peak) * 100

      # 핸들 형성
      handle = close[-10:]
      handle_depth = ((np.max(handle) - np.min(handle)) / np.max(handle)) * 100

      # 돌파 확인
      current_price = close[-1]
      resistance = np.max(close[-20:])
      breakout = current_price >= resistance * 0.99

      if 12 <= cup_depth <= 40 and handle_depth < 12 and breakout:
        return True, resistance

    except:
      pass

    return False, 0

  def detect_pivot_breakout(self, df: pd.DataFrame, idx: int) -> Tuple[
    bool, float]:
    """
    피벗 포인트 돌파 감지
    Returns: (신호발생여부, 저항선)
    """
    if idx < 30:
      return False, 0

    try:
      window = df.iloc[idx - 30:idx + 1]

      # 거래량 확인
      avg_volume = window['Volume'].iloc[:-1].mean()
      current_volume = window['Volume'].iloc[-1]
      volume_surge = (current_volume / avg_volume - 1) * 100

      # 가격 확인
      close = window['Close'].values
      current_price = close[-1]
      resistance = np.max(close[-20:-1])
      breakout = current_price > resistance
      breakout_pct = ((current_price - resistance) / resistance) * 100

      if breakout and volume_surge >= 50 and 0 < breakout_pct <= 5:
        return True, resistance

    except:
      pass

    return False, 0

  def detect_base_breakout(self, df: pd.DataFrame, idx: int) -> Tuple[
    bool, float]:
    """
    베이스 돌파 감지
    Returns: (신호발생여부, 저항선)
    """
    if idx < 40:
      return False, 0

    try:
      window = df.iloc[idx - 40:idx + 1]
      close = window['Close'].values

      # 횡보 구간 확인
      base_period = close[-30:-5]
      base_high = np.max(base_period)
      base_low = np.min(base_period)
      base_volatility = ((base_high - base_low) / base_low) * 100

      current_price = close[-1]
      breakout = current_price > base_high
      breakout_pct = ((current_price - base_high) / base_high) * 100

      # 거래량 확인
      avg_volume = window['Volume'].iloc[-30:-5].mean()
      current_volume = window['Volume'].iloc[-1]
      volume_surge = (current_volume / avg_volume - 1) * 100

      if base_volatility < 15 and breakout and volume_surge >= 40 and 0 < breakout_pct <= 7:
        return True, base_high

    except:
      pass

    return False, 0

  # ========================================
  # 포지션 관리
  # ========================================

  def open_position(self, ticker: str, entry_date: datetime, entry_price: float,
      pattern: str, market: str):
    """포지션 진입"""
    # 사용 가능한 자본의 20%로 매수 (최대 5개 종목 분산)
    # position_size = self.initial_capital * 0.2
    position_size = self.capital * 0.2
    shares = int(position_size / entry_price)

    if shares > 0:
      cost = shares * entry_price
      self.capital -= cost

      position = {
        'ticker': ticker,
        'market': market,
        'pattern': pattern,
        'entry_date': entry_date,
        'entry_price': entry_price,
        'shares': shares,
        'cost': cost,
        'stop_loss': entry_price * 0.92  # 8% 손절
      }
      self.positions.append(position)
      return True
    return False

  def close_position(self, position: dict, exit_date: datetime,
      exit_price: float, reason: str):
    """포지션 청산"""
    proceeds = position['shares'] * exit_price
    self.capital += proceeds

    profit = proceeds - position['cost']
    profit_pct = (profit / position['cost']) * 100

    trade = {
      'ticker': position['ticker'],
      'market': position['market'],
      'pattern': position['pattern'],
      'entry_date': position['entry_date'],
      'entry_price': position['entry_price'],
      'exit_date': exit_date,
      'exit_price': exit_price,
      'shares': position['shares'],
      'cost': position['cost'],
      'proceeds': proceeds,
      'profit': profit,
      'profit_pct': profit_pct,
      'holding_days': (exit_date - position['entry_date']).days,
      'reason': reason
    }
    self.trade_history.append(trade)
    self.positions.remove(position)

  def check_exit_conditions(self, position: dict, current_date: datetime,
      current_price: float, high: float, low: float):
    """청산 조건 확인"""
    # 손절 확인
    if low <= position['stop_loss']:
      return True, position['stop_loss'], '손절'

    # 최대 보유 기간 (30일)
    holding_days = (current_date - position['entry_date']).days
    if holding_days >= 30:
      return True, current_price, '보유기간만료'

    # 익절 확인 (20% 이상 수익)
    if current_price >= position['entry_price'] * 1.20:
      return True, current_price, '익절'

    return False, current_price, ''

  # ========================================
  # 백테스트 실행
  # ========================================

  def run_backtest(self, ticker: str, start_date: str, end_date: str,
      market: str = 'US', patterns: List[str] = None):
    """
    단일 종목 백테스트

    Args:
        ticker: 종목 코드
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        market: 'US' 또는 'KR'
        patterns: 테스트할 패턴 리스트 ['cup', 'pivot', 'base']
    """
    if patterns is None:
      patterns = ['cup', 'pivot', 'base']

    # 백테스트 기간 저장 (단일 종목의 경우)
    self.start_date = start_date
    self.end_date = end_date

    print(f"\n📊 {ticker} 백테스트 시작...")
    print(f"   기간: {start_date} ~ {end_date}")
    print(f"   시장: {market}")
    print(f"   패턴: {', '.join(patterns)}")

    # 데이터 가져오기
    if market == 'US':
      df = self.get_us_stock_data(ticker, start_date, end_date)
    else:
      df = self.get_kr_stock_data(ticker, start_date, end_date)

    if df is None or len(df) < 100:
      print(f"   ❌ 데이터 부족")
      return

    # 날짜별 시뮬레이션
    for idx in range(60, len(df)):
      current_date = df.index[idx]
      current_price = df['Close'].iloc[idx]
      high = df['High'].iloc[idx]
      low = df['Low'].iloc[idx]

      # 기존 포지션 관리
      for position in self.positions.copy():
        if position['ticker'] == ticker:
          should_exit, exit_price, reason = self.check_exit_conditions(
              position, current_date, current_price, high, low
          )
          if should_exit:
            self.close_position(position, current_date, exit_price, reason)

      # 새로운 진입 기회 확인 (포지션이 없을 때만)
      has_position = any(p['ticker'] == ticker for p in self.positions)
      if not has_position and len(self.positions) < 5:  # 최대 5개 종목

        # 패턴별 감지
        if 'cup' in patterns:
          signal, resistance = self.detect_cup_and_handle(df, idx)
          if signal:
            self.open_position(ticker, current_date, current_price,
                               '컵앤핸들', market)
            continue

        if 'pivot' in patterns:
          signal, resistance = self.detect_pivot_breakout(df, idx)
          if signal:
            self.open_position(ticker, current_date, current_price,
                               '피벗돌파', market)
            continue

        if 'base' in patterns:
          signal, resistance = self.detect_base_breakout(df, idx)
          if signal:
            self.open_position(ticker, current_date, current_price,
                               '베이스돌파', market)

    # 백테스트 종료 시 남은 포지션 정리
    end_date_dt = df.index[-1]
    end_price = df['Close'].iloc[-1]
    for position in self.positions.copy():
      if position['ticker'] == ticker:
        self.close_position(position, end_date_dt, end_price, '백테스트종료')

    print(
        f"   ✅ 완료 (거래: {len([t for t in self.trade_history if t['ticker'] == ticker])}건)")

  def run_portfolio_backtest(self, tickers: List[str], start_date: str,
      end_date: str,
      market: str = 'US', patterns: List[str] = None):
    """
    다중 종목 포트폴리오 백테스트

    Args:
        tickers: 종목 리스트
        start_date: 시작일
        end_date: 종료일
        market: 'US' 또는 'KR'
        patterns: 테스트할 패턴 리스트
    """
    # 백테스트 기간 저장 (포트폴리오의 경우)
    self.start_date = start_date
    self.end_date = end_date

    print(f"\n{'=' * 60}")
    print(f"📈 포트폴리오 백테스트")
    print(f"{'=' * 60}")
    print(f"종목 수: {len(tickers)}개")
    print(f"기간: {start_date} ~ {end_date}")
    print(f"초기 자본: {self.initial_capital:,.0f}원")
    print(f"{'=' * 60}\n")

    for ticker in tickers:
      try:
        self.run_backtest(ticker, start_date, end_date, market, patterns)
      except Exception as e:
        print(f"   ❌ {ticker} 오류: {e}")
        continue

  # ========================================
  # 성과 분석
  # ========================================

  def calculate_performance(self) -> Dict:
    """성과 지표 계산"""
    if not self.trade_history:
      return None

    df_trades = pd.DataFrame(self.trade_history)

    # 기본 통계
    total_trades = len(df_trades)
    winning_trades = len(df_trades[df_trades['profit'] > 0])
    losing_trades = len(df_trades[df_trades['profit'] < 0])
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

    # 수익률
    total_profit = df_trades['profit'].sum()
    total_return_pct = (total_profit / self.initial_capital) * 100
    final_capital = self.capital + sum(p['cost'] for p in self.positions)

    # 연간 수익률 (CAGR) 계산
    annualized_return = 0
    if self.start_date and self.end_date:
      try:
        start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
        days = (end_dt - start_dt).days
        if days > 0:
          years = days / 365.25
          annualized_return = (((final_capital / self.initial_capital) ** (
              1 / years)) - 1) * 100
      except ValueError:
        pass  # 날짜 형식 오류 시 0으로 유지

    # 평균 수익/손실
    avg_profit = df_trades[df_trades['profit'] > 0][
      'profit_pct'].mean() if winning_trades > 0 else 0
    avg_loss = df_trades[df_trades['profit'] < 0][
      'profit_pct'].mean() if losing_trades > 0 else 0

    # 최대/최소
    max_profit = df_trades['profit_pct'].max()
    max_loss = df_trades['profit_pct'].min()

    # 평균 보유 기간
    avg_holding_days = df_trades['holding_days'].mean()

    # 패턴별 통계
    pattern_stats = df_trades.groupby('pattern').agg({
      'profit_pct': ['count', 'mean', lambda x: (x > 0).sum() / len(x) * 100]
    }).round(2)

    performance = {
      'total_trades': total_trades,
      'winning_trades': winning_trades,
      'losing_trades': losing_trades,
      'win_rate': win_rate,
      'initial_capital': self.initial_capital,
      'final_capital': final_capital,
      'total_profit': total_profit,
      'total_return_pct': total_return_pct,
      'annualized_return': annualized_return,
      'avg_profit': avg_profit,
      'avg_loss': avg_loss,
      'max_profit': max_profit,
      'max_loss': max_loss,
      'avg_holding_days': avg_holding_days,
      'pattern_stats': pattern_stats,
      'trade_df': df_trades
    }

    return performance

  def print_performance_report(self):
    """성과 보고서 출력"""
    perf = self.calculate_performance()

    if perf is None:
      print("\n⚠️  거래 내역이 없습니다.")
      return

    print(f"\n{'=' * 60}")
    print(f"📊 백테스트 성과 보고서")
    print(f"{'=' * 60}\n")

    print(f"💰 자본")
    print(f"   초기 자본:    {perf['initial_capital']:>15,.0f}원")
    print(f"   최종 자본:    {perf['final_capital']:>15,.0f}원")
    print(f"   총 수익:      {perf['total_profit']:>15,.0f}원")
    print(f"   수익률:       {perf['total_return_pct']:>15.2f}%")
    print(f"   연간 수익률:  {perf['annualized_return']:>15.2f}%")

    print(f"\n📈 거래 통계")
    print(f"   총 거래:      {perf['total_trades']:>15}건")
    print(f"   수익 거래:    {perf['winning_trades']:>15}건")
    print(f"   손실 거래:    {perf['losing_trades']:>15}건")
    print(f"   승률:         {perf['win_rate']:>15.2f}%")

    print(f"\n💵 수익/손실")
    print(f"   평균 수익:    {perf['avg_profit']:>15.2f}%")
    print(f"   평균 손실:    {perf['avg_loss']:>15.2f}%")
    print(f"   최대 수익:    {perf['max_profit']:>15.2f}%")
    print(f"   최대 손실:    {perf['max_loss']:>15.2f}%")

    print(f"\n⏱️  보유 기간")
    print(f"   평균:         {perf['avg_holding_days']:>15.1f}일")

    print(f"\n📊 패턴별 성과")
    print(f"{'패턴':<12} {'거래수':>8} {'평균수익':>10} {'승률':>8}")
    print(f"{'-' * 40}")
    for pattern, stats in perf['pattern_stats'].iterrows():
      count = int(stats['profit_pct']['count'])
      avg_return = stats['profit_pct']['mean']
      win_rate = stats['profit_pct']['<lambda_0>']
      print(f"{pattern:<12} {count:>8}건 {avg_return:>9.2f}% {win_rate:>7.1f}%")

    print(f"\n{'=' * 60}")

    # 개별 거래 내역 (최근 10건)
    print(f"\n📋 최근 거래 내역 (최근 10건)")
    print(f"{'-' * 60}")
    recent_trades = perf['trade_df'].tail(10)
    for _, trade in recent_trades.iterrows():
      profit_sign = "📈" if trade['profit'] > 0 else "📉"
      print(f"{profit_sign} {trade['ticker']:<8} {trade['pattern']:<10} "
            f"{trade['entry_date'].strftime('%Y-%m-%d')} → "
            f"{trade['exit_date'].strftime('%Y-%m-%d')} "
            f"({trade['holding_days']:>2}일) "
            f"{trade['profit_pct']:>7.2f}% "
            f"[{trade['reason']}]")

    print(f"{'=' * 60}\n")

  def save_results(self, filename: str = "backtest_results.csv"):
    """결과를 CSV 파일로 저장"""
    if self.trade_history:
      df = pd.DataFrame(self.trade_history)
      df.to_csv(filename, index=False, encoding='utf-8-sig')
      print(f"💾 결과 저장: {filename}")


# ========================================
# 실행 예제
# ========================================

def example_us_stocks():
  """미국 주식 백테스트 예제"""
  print("\n🇺🇸 미국 주식 백테스트 예제")

  # 백테스트 엔진 초기화 (초기 자본 $100,000)
  engine = BacktestEngine(initial_capital=100000)

  # 테스트할 종목
  tickers = ["AAPL",
             "MSFT",
             "GOOGL",
             "AMZN",
             "META",
             "NVDA",
             "AMD",
             "AVGO",
             "TSLA",
             "NFLX",
             "CRM",
             "ADBE",
             "PLTR",
             "SNOW",
             "CRWD",
             "NET",
             "DDOG",
             "ZS",
             "COIN",
             "SQ",
             "PYPL",
             "SHOP",
             "TSM",
             "JPM",
             "WMT",
             "LLY",
             "ORCL",
             "V",
             "MA",
             "XOM",
             "COST",
             "JNJ",
             "HD",
             "PG",
             "SAP",
             "BAC",
             "ABBV",
             "ASML",
             "NVO",
             "KO",
             "GE",
             "PM",
             "CSCO",
             "UNH",
             "BABA",
             "CVX",
             "IBM",
             "TMUS",
             "WFC",
             "NVS",
             "ABT",
             "MS",
             "TM",
             "AZN",
             "AXP",
             "LIN",
             "HSBC",
             "MCD",
             "DIS",
             "HOOD",
             "UMC",
             "BMNR",
             "CRCL",
             "RDDT",
             "QUBT",
             "WBTN",
             "CRWV",
             "VRT",
             "LMT",
             "BLK",
             "RBLX",
             "FIG",
             "SMR",
             "CPNG",
             "CRSP",
             "SOUN",
             "TLN",
             "SERV",
             "RZLV",
             "TTWO",
             "RKLB",
             "ASTS",
             "IREN",
             "RGTI",
             "MP",
             "CLS",
             "MELI"]

  # 백테스트 실행 (최근 2년)
  end_date = datetime.now().strftime('%Y-%m-%d')
  start_date = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')

  engine.run_portfolio_backtest(
      tickers=tickers,
      start_date=start_date,
      end_date=end_date,
      market='US',
      patterns=['cup', 'pivot', 'base']
  )

  # 결과 출력
  engine.print_performance_report()

  # 결과 저장
  engine.save_results('us_backtest_results.csv')


def example_kr_stocks():
  """한국 주식 백테스트 예제"""
  print("\n🇰🇷 한국 주식 백테스트 예제")

  # 백테스트 엔진 초기화
  engine = BacktestEngine(initial_capital=10000000)

  # 테스트할 종목 (삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션)
  tickers = ["005930",
             "000660",
             "035420",
             "035720",
             "373220",
             "086520",
             "247540",
             "066970",
             "068270",
             "091990",
             "207940",
             "326030",
             "005380",
             "000270",
             "051910",
             "006400",
             "096770",
             "009540",
             "010140"]

  # 백테스트 실행 (최근 2년)
  end_date = datetime.now().strftime('%Y-%m-%d')
  start_date = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')

  engine.run_portfolio_backtest(
      tickers=tickers,
      start_date=start_date,
      end_date=end_date,
      market='KR',
      patterns=['cup', 'pivot', 'base']
  )

  # 결과 출력
  engine.print_performance_report()

  # 결과 저장
  engine.save_results('kr_backtest_results.csv')


def custom_backtest():
  """커스텀 백테스트"""
  print("\n⚙️  커스텀 백테스트")

  # 설정
  INITIAL_CAPITAL = 10000000  # 초기 자본
  MARKET = 'US'  # 'US' 또는 'KR'
  TICKERS = ['AAPL', 'MSFT', 'GOOGL']  # 종목 리스트
  START_DATE = '2023-01-01'  # 시작일
  END_DATE = '2024-12-31'  # 종료일
  PATTERNS = ['pivot', 'base']  # 테스트할 패턴

  # 백테스트 실행
  engine = BacktestEngine(initial_capital=INITIAL_CAPITAL)
  engine.run_portfolio_backtest(TICKERS, START_DATE, END_DATE, MARKET, PATTERNS)
  engine.print_performance_report()
  engine.save_results('custom_backtest_results.csv')


if __name__ == "__main__":
  print("=" * 60)
  print("윌리엄 오닐 돌파매매 백테스트 시스템")
  print("=" * 60)

  # 실행할 예제 선택
  print("\n실행할 백테스트를 선택하세요:")
  print("1. 미국 주식 백테스트")
  print("2. 한국 주식 백테스트")
  print("3. 커스텀 백테스트 (코드 수정 필요)")

  choice = input("\n선택 (1-3): ").strip()

  if choice == '1':
    example_us_stocks()
  elif choice == '2':
    example_kr_stocks()
  elif choice == '3':
    custom_backtest()
  else:
    print("올바른 선택이 아닙니다. 미국 주식 백테스트를 실행합니다.")
    example_us_stocks()
