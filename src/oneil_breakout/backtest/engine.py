"""
윌리엄 오닐 돌파매매(CAN SLIM) 백테스트 엔진
- 컵앤핸들, 피벗돌파, 베이스돌파 패턴 백테스팅
- 미국/한국 주식 지원
- 손절/익절 시뮬레이션
- 성과 분석 및 보고서 생성
"""
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ..data.us_stock import get_us_stock_data_by_date
from ..data.kr_stock import get_kr_stock_data_by_date
from ..patterns.pivot import detect_pivot_breakout_at_index


class BacktestEngine:
    """윌리엄 오닐 돌파매매 백테스트 엔진"""

    def __init__(
        self,
        initial_capital: float = 10_000_000,
        stop_loss_pct: float = -8.0,
        take_profit_pct: float = 20.0,
        max_holding_days: int = 30,
        max_positions: int = 5,
        position_size_pct: float = 20.0
    ):
        """
        Args:
            initial_capital: 초기 자본
            stop_loss_pct: 손절 기준 (%)
            take_profit_pct: 익절 기준 (%)
            max_holding_days: 최대 보유 기간 (일)
            max_positions: 최대 포지션 수
            position_size_pct: 포지션 크기 (자본 대비 %)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_holding_days = max_holding_days
        self.max_positions = max_positions
        self.position_size_pct = position_size_pct

        self.positions: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.start_date: str | None = None
        self.end_date: str | None = None

    # ========================================
    # 패턴 감지
    # ========================================

    def detect_cup_and_handle(self, df: pd.DataFrame, idx: int) -> Tuple[bool, float]:
        """컵앤핸들 패턴 감지"""
        if idx < 60:
            return False, 0

        try:
            window = df.iloc[idx - 60:idx + 1]
            close = window['Close'].values

            mid_idx = len(close) // 2
            left_peak = np.max(close[:mid_idx])
            bottom = np.min(close[mid_idx - 10:mid_idx + 10])
            cup_depth = ((left_peak - bottom) / left_peak) * 100

            handle = close[-10:]
            handle_depth = ((np.max(handle) - np.min(handle)) / np.max(handle)) * 100

            current_price = close[-1]
            resistance = np.max(close[-20:])
            breakout = current_price >= resistance * 0.99

            if 12 <= cup_depth <= 40 and handle_depth < 12 and breakout:
                return True, resistance

        except:
            pass

        return False, 0

    def detect_pivot_breakout(self, df: pd.DataFrame, idx: int) -> Tuple[bool, float]:
        """피벗 포인트 돌파 감지"""
        return detect_pivot_breakout_at_index(df, idx)

    def detect_base_breakout(self, df: pd.DataFrame, idx: int) -> Tuple[bool, float]:
        """베이스 돌파 감지"""
        if idx < 40:
            return False, 0

        try:
            window = df.iloc[idx - 40:idx + 1]
            close = window['Close'].values

            base_period = close[-30:-5]
            base_high = np.max(base_period)
            base_low = np.min(base_period)
            base_volatility = ((base_high - base_low) / base_low) * 100

            current_price = close[-1]
            breakout = current_price > base_high
            breakout_pct = ((current_price - base_high) / base_high) * 100

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

    def open_position(
        self,
        ticker: str,
        entry_date: datetime,
        entry_price: float,
        pattern: str,
        market: str
    ) -> bool:
        """포지션 진입"""
        position_size = self.capital * (self.position_size_pct / 100)
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
                'stop_loss': entry_price * (1 + self.stop_loss_pct / 100)
            }
            self.positions.append(position)
            return True
        return False

    def close_position(
        self,
        position: Dict,
        exit_date: datetime,
        exit_price: float,
        reason: str
    ):
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

    def check_exit_conditions(
        self,
        position: Dict,
        current_date: datetime,
        current_price: float,
        low: float
    ) -> Tuple[bool, float, str]:
        """청산 조건 확인"""
        # 손절 확인
        if low <= position['stop_loss']:
            return True, position['stop_loss'], '손절'

        # 최대 보유 기간
        holding_days = (current_date - position['entry_date']).days
        if holding_days >= self.max_holding_days:
            return True, current_price, '보유기간만료'

        # 익절 확인
        take_profit_price = position['entry_price'] * (1 + self.take_profit_pct / 100)
        if current_price >= take_profit_price:
            return True, current_price, '익절'

        return False, current_price, ''

    # ========================================
    # 백테스트 실행
    # ========================================

    def run_backtest(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        market: str = 'US',
        patterns: List[str] | None = None
    ):
        """단일 종목 백테스트"""
        if patterns is None:
            patterns = ['cup', 'pivot', 'base']

        self.start_date = start_date
        self.end_date = end_date

        print(f"\n📊 {ticker} 백테스트 시작...")
        print(f"   기간: {start_date} ~ {end_date}")
        print(f"   시장: {market}")
        print(f"   패턴: {', '.join(patterns)}")

        # 데이터 가져오기
        if market == 'US':
            df = get_us_stock_data_by_date(ticker, start_date, end_date)
        else:
            df = get_kr_stock_data_by_date(ticker, start_date, end_date)

        if df is None or len(df) < 100:
            print(f"   ❌ 데이터 부족")
            return

        # 날짜별 시뮬레이션
        for idx in range(60, len(df)):
            current_date = df.index[idx]
            current_price = df['Close'].iloc[idx]
            low = df['Low'].iloc[idx]

            # 기존 포지션 관리
            for position in self.positions.copy():
                if position['ticker'] == ticker:
                    should_exit, exit_price, reason = self.check_exit_conditions(
                        position, current_date, current_price, low
                    )
                    if should_exit:
                        self.close_position(position, current_date, exit_price, reason)

            # 새로운 진입 기회 확인
            has_position = any(p['ticker'] == ticker for p in self.positions)
            if not has_position and len(self.positions) < self.max_positions:

                if 'cup' in patterns:
                    signal, _ = self.detect_cup_and_handle(df, idx)
                    if signal:
                        self.open_position(ticker, current_date, current_price, '컵앤핸들', market)
                        continue

                if 'pivot' in patterns:
                    signal, _ = self.detect_pivot_breakout(df, idx)
                    if signal:
                        self.open_position(ticker, current_date, current_price, '피벗돌파', market)
                        continue

                if 'base' in patterns:
                    signal, _ = self.detect_base_breakout(df, idx)
                    if signal:
                        self.open_position(ticker, current_date, current_price, '베이스돌파', market)

        # 백테스트 종료 시 남은 포지션 정리
        end_date_dt = df.index[-1]
        end_price = df['Close'].iloc[-1]
        for position in self.positions.copy():
            if position['ticker'] == ticker:
                self.close_position(position, end_date_dt, end_price, '백테스트종료')

        trade_count = len([t for t in self.trade_history if t['ticker'] == ticker])
        print(f"   ✅ 완료 (거래: {trade_count}건)")

    def run_portfolio_backtest(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        market: str = 'US',
        patterns: List[str] | None = None
    ):
        """다중 종목 포트폴리오 백테스트"""
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

    def calculate_performance(self) -> Dict | None:
        """성과 지표 계산"""
        if not self.trade_history:
            return None

        df_trades = pd.DataFrame(self.trade_history)

        total_trades = len(df_trades)
        winning_trades = len(df_trades[df_trades['profit'] > 0])
        losing_trades = len(df_trades[df_trades['profit'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        total_profit = df_trades['profit'].sum()
        total_return_pct = (total_profit / self.initial_capital) * 100
        final_capital = self.capital + sum(p['cost'] for p in self.positions)

        # 연간 수익률 (CAGR)
        annualized_return = 0
        if self.start_date and self.end_date:
            try:
                start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
                days = (end_dt - start_dt).days
                if days > 0:
                    years = days / 365.25
                    annualized_return = (((final_capital / self.initial_capital) ** (1 / years)) - 1) * 100
            except ValueError:
                pass

        avg_profit = df_trades[df_trades['profit'] > 0]['profit_pct'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['profit'] < 0]['profit_pct'].mean() if losing_trades > 0 else 0
        max_profit = df_trades['profit_pct'].max()
        max_loss = df_trades['profit_pct'].min()
        avg_holding_days = df_trades['holding_days'].mean()

        pattern_stats = df_trades.groupby('pattern').agg({
            'profit_pct': ['count', 'mean', lambda x: (x > 0).sum() / len(x) * 100]
        }).round(2)

        return {
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
            pattern_win_rate = stats['profit_pct']['<lambda_0>']
            print(f"{pattern:<12} {count:>8}건 {avg_return:>9.2f}% {pattern_win_rate:>7.1f}%")

        print(f"\n{'=' * 60}")

        # 최근 거래 내역
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