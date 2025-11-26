"""스마트 통합 돌파매매 감지 봇"""
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List

from ..config import Settings, load_settings
from ..data.us_stock import get_us_stock_data
from ..data.kr_stock import get_kr_stock_data, get_kr_stock_name
from ..patterns.pivot import detect_pivot_breakout
from ..market.status import get_market_status, format_market_status_message
from ..positions import PositionManager
from ..watchlist import WatchlistManager
from ..telegram.client import TelegramClient
from ..telegram.formatter import (
    format_signal_message,
    format_close_position_message,
    format_no_signal_message
)


class BreakoutDetector:
    """스마트 통합 돌파매매 패턴 감지 봇"""

    def __init__(self, settings: Settings | None = None):
        """
        Args:
            settings: 설정 객체 (None이면 자동 로드)
        """
        self.settings = settings or load_settings()

        # 텔레그램 클라이언트
        self.telegram = TelegramClient(
            self.settings.telegram.token,
            self.settings.telegram.chat_id
        )

        # 워치리스트 관리자
        self.watchlist = WatchlistManager(
            self.settings.watchlist_file,
            self.settings.watchlist.us_stocks,
            self.settings.watchlist.kr_stocks
        )

        # 포지션 관리자
        self.positions = PositionManager(
            self.settings.positions_file,
            self.settings.trading.stop_loss_pct,
            self.settings.trading.take_profit_pct,
            self.settings.trading.max_holding_days
        )

        # 스캔 락
        self.scan_lock = threading.Lock()
        self.is_scanning = False

        print(f"✅ 감시 종목 로드 완료")
        print(f"   🇺🇸 미국: {self.watchlist.count_us()}개")
        print(f"   🇰🇷 한국: {self.watchlist.count_kr()}개")
        print(f"✅ 포지션 로드 완료: {self.positions.count()}개")

    # ========================================
    # 텔레그램 명령어 처리
    # ========================================

    def process_command(self, message: str) -> str | None:
        """텔레그램 명령어 처리"""
        parts = message.strip().split()
        if not parts:
            return None

        command = parts[0].lower()

        if command in ('/help', '/start'):
            return self._get_help_message()

        elif command == '/add_us':
            if len(parts) < 2:
                return "❌ 사용법: /add_us [티커]\n예: /add_us AAPL"
            return self.watchlist.add_us(parts[1])

        elif command == '/add_kr':
            if len(parts) < 2:
                return "❌ 사용법: /add_kr [종목코드]\n예: /add_kr 005930"
            return self.watchlist.add_kr(parts[1])

        elif command == '/remove_us':
            if len(parts) < 2:
                return "❌ 사용법: /remove_us [티커]\n예: /remove_us AAPL"
            return self.watchlist.remove_us(parts[1])

        elif command == '/remove_kr':
            if len(parts) < 2:
                return "❌ 사용법: /remove_kr [종목코드]\n예: /remove_kr 005930"
            return self.watchlist.remove_kr(parts[1])

        elif command == '/list':
            return self.watchlist.format_list_message()

        elif command == '/status':
            market_status = get_market_status()
            return format_market_status_message(
                market_status,
                self.watchlist.count_kr(),
                self.watchlist.count_us(),
                self.is_scanning
            )

        elif command == '/scan':
            return 'SCAN_ALL'

        elif command == '/scan_kr':
            return 'SCAN_KR'

        elif command == '/scan_us':
            return 'SCAN_US'

        elif command == '/positions':
            return self.positions.format_list_message(self._get_current_price)

        elif command == '/close':
            if len(parts) < 2:
                return "❌ 사용법: /close [티커]\n예: /close AAPL"
            return self._close_position_command(parts[1].upper())

        return None

    def _get_help_message(self) -> str:
        """도움말 메시지"""
        return """
🤖 <b>윌리엄 오닐 돌파매매 봇 명령어</b>

<b>즉시 스캔:</b>
/scan - 🌍 전체 시장 즉시 스캔
/scan_kr - 🇰🇷 한국장만 즉시 스캔
/scan_us - 🇺🇸 미국장만 즉시 스캔

<b>포지션 관리:</b>
/positions - 현재 보유 포지션 보기
/close [티커] - 포지션 수동 청산
  예: /close AAPL

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
• 매수 신호 발생 시 자동으로 포지션 추적
• 손절(-8%), 익절(+20%), 30일 만료 시 알림
• 봇이 자동으로 장 시간에 맞춰 스캔합니다
• 한국: 09:00-15:30
• 미국: 22:30-06:00
"""

    def _close_position_command(self, ticker: str) -> str:
        """포지션 청산 명령 처리"""
        pos = self.positions.get(ticker)
        if not pos:
            return f"❌ {ticker} 포지션을 찾을 수 없습니다."

        try:
            current_price = self._get_current_price(ticker, pos['market'])
            if current_price:
                self._close_position(pos, current_price, "수동 청산")
                return f"✅ {ticker} 포지션이 청산되었습니다."
            else:
                return f"❌ {ticker} 현재가 조회 실패"
        except Exception as e:
            return f"❌ 청산 중 오류: {e}"

    def _get_current_price(self, ticker: str, market: str) -> float | None:
        """현재가 조회"""
        if market == 'US':
            df = get_us_stock_data(ticker, period="5d")
        else:
            df = get_kr_stock_data(ticker, days=7)

        if df is not None and len(df) > 0:
            return df['Close'].iloc[-1]
        return None

    # ========================================
    # 포지션 관리
    # ========================================

    def _close_position(self, position: Dict, exit_price: float, reason: str):
        """포지션 청산 처리"""
        profit_pct, holding_days = self.positions.calculate_profit(position, exit_price)

        msg = format_close_position_message(
            position['ticker'],
            position['market'],
            position['pattern'],
            position['entry_price'],
            exit_price,
            profit_pct,
            holding_days,
            reason
        )
        self.telegram.send_message(msg)
        self.positions.remove(position['ticker'])
        print(f"  ❌ 포지션 청산: {position['ticker']} ({reason}) {profit_pct:+.2f}%")

    def check_positions(self):
        """포지션 추적 및 청산 조건 확인"""
        if self.positions.count() == 0:
            return

        print(f"\n📊 포지션 추적 중... ({self.positions.count()}개)")

        for pos in self.positions.get_all():
            ticker = pos['ticker']
            try:
                current_price = self._get_current_price(ticker, pos['market'])
                if current_price is None:
                    continue

                profit_pct, holding_days = self.positions.calculate_profit(pos, current_price)
                print(f"  🔍 {ticker}: {current_price:,.2f} ({profit_pct:+.2f}%)", end="")

                should_exit, exit_price, reason = self.positions.check_exit_conditions(pos, current_price)
                if should_exit:
                    print(f" ⚠️ {reason}!")
                    self._close_position(pos, exit_price, reason)
                else:
                    print(f" ⚪")

                time.sleep(1)

            except Exception as e:
                print(f" ❌ 오류: {e}")

    # ========================================
    # 종목 분석
    # ========================================

    def analyze_us_stock(self, ticker: str) -> List[Dict]:
        """미국 주식 분석"""
        df = get_us_stock_data(ticker, self.settings.data.analysis_period)
        if df is None:
            return []

        signals = []
        pivot_signal = detect_pivot_breakout(
            df, ticker, 'US',
            volume_surge_min=self.settings.pattern.volume_surge_min,
            breakout_max=self.settings.pattern.breakout_max
        )
        if pivot_signal:
            signals.append(pivot_signal)

        return signals

    def analyze_kr_stock(self, ticker: str) -> List[Dict]:
        """한국 주식 분석"""
        df = get_kr_stock_data(ticker, self.settings.data.analysis_period_days)
        if df is None:
            return []

        signals = []
        stock_name = get_kr_stock_name(ticker)
        pivot_signal = detect_pivot_breakout(
            df, ticker, 'KR', stock_name,
            volume_surge_min=self.settings.pattern.volume_surge_min,
            breakout_max=self.settings.pattern.breakout_max
        )
        if pivot_signal:
            signals.append(pivot_signal)

        return signals

    # ========================================
    # 스캔 실행
    # ========================================

    def run_manual_scan(self, scan_kr: bool = True, scan_us: bool = True) -> List[Dict]:
        """수동 스캔 (시간대 무관)"""
        print(f"\n{'=' * 60}")
        print(f"🔍 수동 스캔")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if scan_kr:
            print(f"🇰🇷 한국 주식 스캔 ({self.watchlist.count_kr()}개)")
        if scan_us:
            print(f"🇺🇸 미국 주식 스캔 ({self.watchlist.count_us()}개)")

        print(f"{'=' * 60}\n")

        all_signals = []

        # 미국 주식 스캔
        if scan_us:
            signals = self._scan_us_stocks()
            all_signals.extend(signals)

        # 한국 주식 스캔
        if scan_kr:
            signals = self._scan_kr_stocks()
            all_signals.extend(signals)

        self._print_scan_summary(all_signals, scan_us, scan_kr, "수동")

        return all_signals

    def run_smart_scan(self) -> List[Dict]:
        """시간대에 따라 자동으로 시장 선택하여 스캔"""
        if self.is_scanning:
            print("\n⏸️  수동 스캔이 진행 중입니다. 이번 주기는 건너뜁니다...\n")
            return []

        market_status = get_market_status()

        print(f"\n{'=' * 60}")
        print(f"🔍 윌리엄 오닐 스마트 스캔")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        scan_kr = market_status['kr']
        scan_us = market_status['us']

        if not scan_kr and not scan_us:
            print("⏸️  휴장 시간입니다. 다음 장 시작까지 대기...")
            print(f"{'=' * 60}\n")
            self.check_positions()
            return []

        if scan_kr:
            print(f"🇰🇷 한국 장중 - 한국 주식 스캔 ({self.watchlist.count_kr()}개)")
        if scan_us:
            print(f"🇺🇸 미국 장중 - 미국 주식 스캔 ({self.watchlist.count_us()}개)")

        print(f"{'=' * 60}\n")

        # 먼저 포지션 추적
        self.check_positions()

        all_signals = []

        # 미국 주식 스캔
        if scan_us:
            signals = self._scan_us_stocks()
            all_signals.extend(signals)

        # 한국 주식 스캔
        if scan_kr:
            signals = self._scan_kr_stocks()
            all_signals.extend(signals)

        self._print_scan_summary(all_signals, scan_us, scan_kr, "자동")

        return all_signals

    def _scan_us_stocks(self) -> List[Dict]:
        """미국 주식 스캔"""
        signals = []
        us_tickers = self.watchlist.get_us()

        if not us_tickers:
            return signals

        print("🇺🇸 미국 주식 스캔 중...\n")

        for ticker in us_tickers:
            try:
                print(f"  🔍 {ticker}...", end=" ")
                stock_signals = self.analyze_us_stock(ticker)

                if stock_signals:
                    for signal in stock_signals:
                        signals.append(signal)
                        msg = format_signal_message(signal)
                        self.telegram.send_message(msg)

                        # 포지션 자동 추가
                        if not self.positions.has_position(ticker):
                            self.positions.add(
                                ticker=ticker,
                                market='US',
                                entry_price=signal['current_price'],
                                pattern=signal['pattern'],
                                signal=signal
                            )

                        print(f"✅ 신호!")
                        time.sleep(1)
                else:
                    print("⚪")
            except Exception:
                print(f"❌ 오류")
        print()

        return signals

    def _scan_kr_stocks(self) -> List[Dict]:
        """한국 주식 스캔"""
        signals = []
        kr_tickers = self.watchlist.get_kr()

        if not kr_tickers:
            return signals

        print("🇰🇷 한국 주식 스캔 중...\n")

        for ticker in kr_tickers:
            try:
                name = get_kr_stock_name(ticker)
                print(f"  🔍 {name}({ticker})...", end=" ")
                stock_signals = self.analyze_kr_stock(ticker)

                if stock_signals:
                    for signal in stock_signals:
                        signals.append(signal)
                        msg = format_signal_message(signal)
                        self.telegram.send_message(msg)

                        # 포지션 자동 추가
                        if not self.positions.has_position(ticker):
                            self.positions.add(
                                ticker=ticker,
                                market='KR',
                                entry_price=signal['current_price'],
                                pattern=signal['pattern'],
                                signal=signal
                            )

                        print(f"✅ 신호!")
                        time.sleep(2)
                else:
                    print("⚪")
            except Exception:
                print(f"❌ 오류")
        print()

        return signals

    def _print_scan_summary(
        self,
        all_signals: List[Dict],
        scan_us: bool,
        scan_kr: bool,
        scan_type: str
    ):
        """스캔 결과 요약 출력"""
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

            msg = format_no_signal_message(
                scan_type,
                self.watchlist.count_us(),
                self.watchlist.count_kr(),
                scan_us,
                scan_kr
            )
            self.telegram.send_message(msg)

        print(f"\n{'=' * 60}\n")

    # ========================================
    # 스캔 스레드 관리
    # ========================================

    def _execute_scan_in_thread(self, scan_kr: bool, scan_us: bool, scan_type: str):
        """별도 스레드에서 스캔 실행"""
        if self.is_scanning:
            self.telegram.send_message("⚠️  이미 스캔이 진행 중입니다. 완료 후 다시 시도해주세요.")
            return

        if not self.scan_lock.acquire(blocking=False):
            self.telegram.send_message("⚠️  다른 스캔이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return

        try:
            self.is_scanning = True
            print(f"\n🔔 {scan_type} 명령어 수신 - 스캔 시작")
            self.run_manual_scan(scan_kr=scan_kr, scan_us=scan_us)
            self.telegram.send_message(f"✅ {scan_type} 완료!")
        except Exception as e:
            print(f"❌ 스캔 중 오류: {e}")
            self.telegram.send_message(f"❌ 스캔 중 오류가 발생했습니다: {str(e)}")
        finally:
            self.is_scanning = False
            self.scan_lock.release()

    def check_telegram_updates(self):
        """텔레그램 메시지 확인 (명령어 처리)"""
        updates = self.telegram.get_updates()

        for update in updates:
            message_text = update['text']
            reply = self.process_command(message_text)

            if reply == 'SCAN_ALL':
                self.telegram.send_message("🌍 전체 시장 수동 스캔을 시작합니다...")
                scan_thread = threading.Thread(
                    target=self._execute_scan_in_thread,
                    args=(True, True, "전체 시장 수동 스캔"),
                    daemon=True
                )
                scan_thread.start()

            elif reply == 'SCAN_KR':
                self.telegram.send_message("🇰🇷 한국장 수동 스캔을 시작합니다...")
                scan_thread = threading.Thread(
                    target=self._execute_scan_in_thread,
                    args=(True, False, "한국장 수동 스캔"),
                    daemon=True
                )
                scan_thread.start()

            elif reply == 'SCAN_US':
                self.telegram.send_message("🇺🇸 미국장 수동 스캔을 시작합니다...")
                scan_thread = threading.Thread(
                    target=self._execute_scan_in_thread,
                    args=(False, True, "미국장 수동 스캔"),
                    daemon=True
                )
                scan_thread.start()

            elif reply:
                self.telegram.send_message(reply)

    def start_command_listener(self):
        """백그라운드에서 텔레그램 명령어 리스너 시작"""

        def listener_loop():
            while True:
                try:
                    self.check_telegram_updates()
                    time.sleep(2)
                except Exception as e:
                    print(f"⚠️  리스너 오류: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=listener_loop, daemon=True)
        thread.start()
        print("✅ 텔레그램 명령어 리스너 시작")

    # ========================================
    # 메인 실행
    # ========================================

    def get_start_message(self) -> str:
        """시작 메시지 생성"""
        market_status = get_market_status()
        status_text = []
        if market_status['kr']:
            status_text.append("🇰🇷 한국 장중")
        if market_status['us']:
            status_text.append("🇺🇸 미국 장중")
        if not status_text:
            status_text.append("⏸️  휴장 중")

        interval_min = self.settings.scan.interval_seconds // 60

        return f"""
🤖 <b>윌리엄 오닐 스마트 돌파매매 봇 시작</b>

📊 감시 종목:
   🇺🇸 미국: {self.watchlist.count_us()}개
   🇰🇷 한국: {self.watchlist.count_kr()}개

📍 현재 포지션: {self.positions.count()}개

⏰ 스캔 주기: {interval_min}분
🕐 현재 상태: {' + '.join(status_text)}

📈 자동 스캔:
   • 한국 장중 (09:00-15:30)
   • 미국 장중 (22:30-06:00)

🎯 자동 포지션 추적:
   • 매수 신호 시 자동 기록
   • 손절({self.settings.trading.stop_loss_pct}%), 익절(+{self.settings.trading.take_profit_pct}%), {self.settings.trading.max_holding_days}일 만료 알림

💬 명령어:
   /scan - 🌍 전체 즉시 스캔
   /scan_kr - 🇰🇷 한국만 즉시 스캔
   /scan_us - 🇺🇸 미국만 즉시 스캔
   /positions - 현재 포지션 보기
   /help - 전체 명령어 보기

시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    def run(self):
        """메인 실행 루프"""
        # 텔레그램 명령어 리스너 시작
        self.start_command_listener()

        # 시작 메시지
        start_msg = self.get_start_message()
        self.telegram.send_message(start_msg)
        print(start_msg)

        scan_interval = self.settings.scan.interval_seconds

        try:
            while True:
                self.run_smart_scan()

                # 다음 스캔까지 대기
                next_scan = datetime.now() + timedelta(seconds=scan_interval)
                print(f"⏰ 다음 스캔: {next_scan.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"💤 {scan_interval // 60}분 대기 중...\n")
                time.sleep(scan_interval)

        except KeyboardInterrupt:
            print("\n\n⛔ 프로그램 종료")
            self.telegram.send_message("⛔ 윌리엄 오닐 스마트 돌파매매 봇 종료")