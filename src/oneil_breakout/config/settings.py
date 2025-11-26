"""설정 관리"""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class TelegramSettings:
    """텔레그램 설정"""
    token: str = ""
    chat_id: str = ""


@dataclass
class PatternSettings:
    """패턴 감지 설정"""
    # 컵앤핸들
    cup_depth_min: float = 12.0
    cup_depth_max: float = 40.0
    handle_depth_max: float = 12.0

    # 피벗 돌파
    volume_surge_min: float = 50.0
    breakout_max: float = 5.0

    # 베이스 돌파
    base_volatility_max: float = 15.0
    base_volume_surge_min: float = 40.0
    base_breakout_max: float = 7.0


@dataclass
class TradingSettings:
    """거래 설정"""
    stop_loss_pct: float = -8.0
    take_profit_pct: float = 20.0
    max_holding_days: int = 30
    max_positions: int = 5
    position_size_pct: float = 20.0  # 각 포지션 크기 (자본 대비 %)


@dataclass
class ScanSettings:
    """스캔 설정"""
    interval_seconds: int = 1800  # 30분
    scan_us_market: bool = True
    scan_kr_market: bool = True
    request_delay: float = 1.0


@dataclass
class DataSettings:
    """데이터 설정"""
    analysis_period_days: int = 120  # 한국 주식
    analysis_period: str = "6mo"  # 미국 주식


@dataclass
class WatchlistSettings:
    """워치리스트 기본값"""
    us_stocks: List[str] = field(default_factory=lambda: [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META",
        "NVDA", "AMD", "AVGO",
        "TSLA", "NFLX", "CRM", "ADBE",
        "PLTR", "SNOW", "CRWD", "NET", "DDOG", "ZS",
        "COIN", "SQ", "PYPL",
        "SHOP"
    ])
    kr_stocks: List[str] = field(default_factory=lambda: [
        "005930", "000660", "035420", "035720",
        "373220", "086520", "247540", "066970",
        "068270", "091990", "207940", "326030",
        "005380", "000270",
        "051910", "006400", "096770",
        "009540", "010140"
    ])


@dataclass
class Settings:
    """전체 설정"""
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    pattern: PatternSettings = field(default_factory=PatternSettings)
    trading: TradingSettings = field(default_factory=TradingSettings)
    scan: ScanSettings = field(default_factory=ScanSettings)
    data: DataSettings = field(default_factory=DataSettings)
    watchlist: WatchlistSettings = field(default_factory=WatchlistSettings)

    # 파일 경로
    watchlist_file: str = "watchlist.json"
    positions_file: str = "positions.json"


def load_settings() -> Settings:
    """
    설정 로드 (환경 변수 및 config.py 지원)

    환경변수:
        TELEGRAM_TOKEN: 텔레그램 봇 토큰
        TELEGRAM_CHAT_ID: 텔레그램 채팅 ID
        SCAN_INTERVAL: 스캔 주기 (초)

    Returns:
        Settings 인스턴스
    """
    settings = Settings()

    # 환경 변수에서 로드
    if os.environ.get('TELEGRAM_TOKEN'):
        settings.telegram.token = os.environ['TELEGRAM_TOKEN']
    if os.environ.get('TELEGRAM_CHAT_ID'):
        settings.telegram.chat_id = os.environ['TELEGRAM_CHAT_ID']
    if os.environ.get('SCAN_INTERVAL'):
        settings.scan.interval_seconds = int(os.environ['SCAN_INTERVAL'])

    # config.py에서 로드 (있는 경우)
    try:
        import config as legacy_config

        if hasattr(legacy_config, 'TELEGRAM_TOKEN'):
            settings.telegram.token = legacy_config.TELEGRAM_TOKEN
        if hasattr(legacy_config, 'CHAT_ID'):
            settings.telegram.chat_id = legacy_config.CHAT_ID

        # 스캔 설정
        if hasattr(legacy_config, 'SCAN_INTERVAL'):
            settings.scan.interval_seconds = legacy_config.SCAN_INTERVAL
        if hasattr(legacy_config, 'SCAN_US_MARKET'):
            settings.scan.scan_us_market = legacy_config.SCAN_US_MARKET
        if hasattr(legacy_config, 'SCAN_KR_MARKET'):
            settings.scan.scan_kr_market = legacy_config.SCAN_KR_MARKET

        # 패턴 설정
        if hasattr(legacy_config, 'VOLUME_SURGE_MIN'):
            settings.pattern.volume_surge_min = legacy_config.VOLUME_SURGE_MIN
        if hasattr(legacy_config, 'BREAKOUT_MAX'):
            settings.pattern.breakout_max = legacy_config.BREAKOUT_MAX
        if hasattr(legacy_config, 'CUP_DEPTH_MIN'):
            settings.pattern.cup_depth_min = legacy_config.CUP_DEPTH_MIN
        if hasattr(legacy_config, 'CUP_DEPTH_MAX'):
            settings.pattern.cup_depth_max = legacy_config.CUP_DEPTH_MAX

        # 거래 설정
        if hasattr(legacy_config, 'STOP_LOSS_PERCENT'):
            settings.trading.stop_loss_pct = legacy_config.STOP_LOSS_PERCENT

        # 워치리스트
        if hasattr(legacy_config, 'US_WATCH_LIST'):
            settings.watchlist.us_stocks = legacy_config.US_WATCH_LIST
        if hasattr(legacy_config, 'KR_WATCH_LIST'):
            settings.watchlist.kr_stocks = legacy_config.KR_WATCH_LIST

        print("✅ config.py에서 설정을 불러왔습니다.")

    except ImportError:
        print("ℹ️  config.py 없음 - 기본 설정 사용")

    return settings