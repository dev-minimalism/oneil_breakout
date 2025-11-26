"""워치리스트 관리자"""
import json
import os
from datetime import datetime
from typing import List, Tuple

from pykrx import stock


class WatchlistManager:
    """감시 종목 관리 클래스"""

    def __init__(
        self,
        watchlist_file: str = "watchlist.json",
        default_us: List[str] | None = None,
        default_kr: List[str] | None = None
    ):
        """
        Args:
            watchlist_file: 감시 종목 저장 파일 경로
            default_us: 기본 미국 종목 리스트
            default_kr: 기본 한국 종목 리스트
        """
        self.watchlist_file = watchlist_file
        self.default_us = default_us or ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
        self.default_kr = default_kr or ["005930", "000660", "035420"]
        self.us_watchlist, self.kr_watchlist = self._load()

    def _load(self) -> Tuple[List[str], List[str]]:
        """감시 종목 파일에서 로드"""
        if os.path.exists(self.watchlist_file):
            try:
                with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('us', []), data.get('kr', [])
            except Exception as e:
                print(f"⚠️  감시 종목 로드 실패: {e}")

        return self.default_us.copy(), self.default_kr.copy()

    def _save(self) -> bool:
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

    def add_us(self, ticker: str) -> str:
        """
        미국 주식 추가

        Args:
            ticker: 종목 코드

        Returns:
            결과 메시지
        """
        ticker = ticker.upper().strip()
        if ticker in self.us_watchlist:
            return f"⚠️  {ticker}는 이미 감시 중입니다."

        self.us_watchlist.append(ticker)
        if self._save():
            return f"✅ 🇺🇸 {ticker} 추가 완료!\n현재 미국 종목: {len(self.us_watchlist)}개"
        else:
            self.us_watchlist.remove(ticker)
            return "❌ 저장 실패"

    def add_kr(self, ticker: str) -> str:
        """
        한국 주식 추가

        Args:
            ticker: 종목 코드

        Returns:
            결과 메시지
        """
        ticker = ticker.strip()
        if ticker in self.kr_watchlist:
            try:
                name = stock.get_market_ticker_name(ticker)
                return f"⚠️  {name}({ticker})는 이미 감시 중입니다."
            except:
                return f"⚠️  {ticker}는 이미 감시 중입니다."

        self.kr_watchlist.append(ticker)
        if self._save():
            try:
                name = stock.get_market_ticker_name(ticker)
                return f"✅ 🇰🇷 {name}({ticker}) 추가 완료!\n현재 한국 종목: {len(self.kr_watchlist)}개"
            except:
                return f"✅ 🇰🇷 {ticker} 추가 완료!\n현재 한국 종목: {len(self.kr_watchlist)}개"
        else:
            self.kr_watchlist.remove(ticker)
            return "❌ 저장 실패"

    def remove_us(self, ticker: str) -> str:
        """
        미국 주식 삭제

        Args:
            ticker: 종목 코드

        Returns:
            결과 메시지
        """
        ticker = ticker.upper().strip()
        if ticker not in self.us_watchlist:
            return f"⚠️  {ticker}는 감시 목록에 없습니다."

        self.us_watchlist.remove(ticker)
        if self._save():
            return f"✅ 🇺🇸 {ticker} 삭제 완료!\n현재 미국 종목: {len(self.us_watchlist)}개"
        else:
            self.us_watchlist.append(ticker)
            return "❌ 저장 실패"

    def remove_kr(self, ticker: str) -> str:
        """
        한국 주식 삭제

        Args:
            ticker: 종목 코드

        Returns:
            결과 메시지
        """
        ticker = ticker.strip()
        if ticker not in self.kr_watchlist:
            return f"⚠️  {ticker}는 감시 목록에 없습니다."

        try:
            name = stock.get_market_ticker_name(ticker)
            stock_display = f"{name}({ticker})"
        except:
            stock_display = ticker

        self.kr_watchlist.remove(ticker)
        if self._save():
            return f"✅ 🇰🇷 {stock_display} 삭제 완료!\n현재 한국 종목: {len(self.kr_watchlist)}개"
        else:
            self.kr_watchlist.append(ticker)
            return "❌ 저장 실패"

    def get_us(self) -> List[str]:
        """미국 감시 종목 조회"""
        return self.us_watchlist.copy()

    def get_kr(self) -> List[str]:
        """한국 감시 종목 조회"""
        return self.kr_watchlist.copy()

    def count_us(self) -> int:
        """미국 종목 개수"""
        return len(self.us_watchlist)

    def count_kr(self) -> int:
        """한국 종목 개수"""
        return len(self.kr_watchlist)

    def format_list_message(self) -> str:
        """
        감시 종목 목록 메시지 포맷팅

        Returns:
            포맷된 HTML 메시지
        """
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