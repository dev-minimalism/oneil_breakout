"""메시지 포맷터"""
from datetime import datetime
from typing import Dict


def format_signal_message(signal: Dict) -> str:
    """
    신호를 텔레그램 메시지 형식으로 변환

    Args:
        signal: 신호 딕셔너리

    Returns:
        포맷된 HTML 메시지
    """
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


def format_close_position_message(
    ticker: str,
    market: str,
    pattern: str,
    entry_price: float,
    exit_price: float,
    profit_pct: float,
    holding_days: int,
    reason: str
) -> str:
    """
    포지션 청산 메시지 포맷팅

    Args:
        ticker: 종목 코드
        market: 시장
        pattern: 패턴명
        entry_price: 진입가
        exit_price: 청산가
        profit_pct: 수익률
        holding_days: 보유 기간
        reason: 청산 사유

    Returns:
        포맷된 HTML 메시지
    """
    market_emoji = "🇺🇸" if market == 'US' else "🇰🇷"
    profit_emoji = '📈' if profit_pct > 0 else '📉'

    msg = f"""
{market_emoji} <b>[포지션 청산]</b>

🏢 종목: <b>{ticker}</b>
📊 패턴: {pattern}
💰 진입가: {entry_price:,.2f}
💵 청산가: {exit_price:,.2f}
{profit_emoji} 수익률: {profit_pct:+.2f}%
📅 보유기간: {holding_days}일

🔔 사유: {reason}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    return msg


def format_no_signal_message(scan_type: str, us_count: int = 0, kr_count: int = 0, scan_us: bool = False, scan_kr: bool = False) -> str:
    """
    신호 없음 메시지 포맷팅

    Args:
        scan_type: 스캔 타입 ("자동" 또는 "수동")
        us_count: 미국 종목 수
        kr_count: 한국 종목 수
        scan_us: 미국 스캔 여부
        scan_kr: 한국 스캔 여부

    Returns:
        포맷된 HTML 메시지
    """
    msg = f"""
⚪ <b>[{scan_type} 스캔 완료 - 신호 없음]</b>

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔍 스캔 대상:"""

    if scan_us:
        msg += f"\n   🇺🇸 미국: {us_count}개"
    if scan_kr:
        msg += f"\n   🇰🇷 한국: {kr_count}개"

    msg += "\n\n현재 매매 신호를 보이는 종목이 없습니다."

    return msg
