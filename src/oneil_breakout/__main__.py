"""
윌리엄 오닐 돌파매매 봇 CLI 진입점

사용법:
    python -m oneil_breakout          # 봇 실행
    python -m oneil_breakout backtest # 백테스트 실행
    python -m oneil_breakout scan     # 즉시 스캔 (1회)
"""
import argparse
import sys

from .bot import BreakoutDetector
from .config import load_settings


def main():
    """메인 CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="윌리엄 오닐 돌파매매 봇 (CAN SLIM)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
    python -m oneil_breakout              # 봇 실행
    python -m oneil_breakout backtest     # 백테스트 실행
    python -m oneil_breakout scan         # 즉시 1회 스캔
    python -m oneil_breakout scan --us    # 미국만 스캔
    python -m oneil_breakout scan --kr    # 한국만 스캔
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='실행할 명령')

    # run 명령 (기본)
    run_parser = subparsers.add_parser('run', help='봇 실행 (기본)')

    # scan 명령
    scan_parser = subparsers.add_parser('scan', help='즉시 스캔 (1회)')
    scan_parser.add_argument('--us', action='store_true', help='미국 주식만 스캔')
    scan_parser.add_argument('--kr', action='store_true', help='한국 주식만 스캔')

    # backtest 명령
    backtest_parser = subparsers.add_parser('backtest', help='백테스트 실행')
    backtest_parser.add_argument('--market', choices=['US', 'KR'], default='US',
                                 help='시장 선택 (기본: US)')
    backtest_parser.add_argument('--start', type=str, help='시작일 (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', type=str, help='종료일 (YYYY-MM-DD)')
    backtest_parser.add_argument('--capital', type=float, default=100_000_000,
                                 help='초기 자본 (기본: 1억)')

    args = parser.parse_args()

    # 기본 명령어 (인자 없이 실행)
    if args.command is None or args.command == 'run':
        run_bot()
    elif args.command == 'scan':
        run_scan(args)
    elif args.command == 'backtest':
        run_backtest(args)


def run_bot():
    """봇 실행"""
    print("=" * 60)
    print("윌리엄 오닐 돌파매매 봇 (CAN SLIM)")
    print("=" * 60)

    settings = load_settings()

    if not settings.telegram.token or settings.telegram.token == "YOUR_BOT_TOKEN_HERE":
        print("\n⚠️  텔레그램 설정이 필요합니다!")
        print("\n설정 방법:")
        print("  1. config.py 파일에서 TELEGRAM_TOKEN과 CHAT_ID 설정")
        print("  2. 또는 환경변수로 설정:")
        print("     export TELEGRAM_TOKEN='your_token'")
        print("     export TELEGRAM_CHAT_ID='your_chat_id'")
        sys.exit(1)

    detector = BreakoutDetector(settings)
    detector.run()


def run_scan(args):
    """즉시 스캔"""
    print("=" * 60)
    print("윌리엄 오닐 돌파매매 - 즉시 스캔")
    print("=" * 60)

    settings = load_settings()
    detector = BreakoutDetector(settings)

    scan_us = not args.kr if args.us or args.kr else True
    scan_kr = not args.us if args.us or args.kr else True

    detector.run_manual_scan(scan_kr=scan_kr, scan_us=scan_us)


def run_backtest(args):
    """백테스트 실행"""
    from .backtest import BacktestEngine
    from datetime import datetime, timedelta

    print("=" * 60)
    print("윌리엄 오닐 돌파매매 - 백테스트")
    print("=" * 60)

    settings = load_settings()

    # 기간 설정
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')
    start_date = args.start or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    # 종목 리스트
    if args.market == 'US':
        tickers = settings.watchlist.us_stocks[:20]  # 상위 20개
    else:
        tickers = settings.watchlist.kr_stocks[:20]

    # 백테스트 실행
    engine = BacktestEngine(initial_capital=args.capital)
    engine.run_portfolio_backtest(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        market=args.market,
        patterns=['cup', 'pivot', 'base']
    )

    engine.print_performance_report()
    engine.save_results(f'{args.market.lower()}_backtest_results.csv')


if __name__ == "__main__":
    main()