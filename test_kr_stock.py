"""
한국 주식 데이터 조회 테스트
pykrx가 제대로 동작하는지 확인
"""

from datetime import datetime, timedelta

from pykrx import stock


def test_single_stock(ticker):
  """단일 종목 테스트"""
  print(f"\n{'=' * 60}")
  print(f"📊 종목 테스트: {ticker}")
  print(f"{'=' * 60}")

  try:
    # 종목명 가져오기
    name = stock.get_market_ticker_name(ticker)
    print(f"✅ 종목명: {name}")

    # 데이터 가져오기
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    df = stock.get_market_ohlcv_by_date(
        start_date.strftime("%Y%m%d"),
        end_date.strftime("%Y%m%d"),
        ticker
    )

    if df.empty:
      print("❌ 데이터 없음")
      return False

    print(f"✅ 데이터 수집 성공!")
    print(
      f"   기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"   데이터 수: {len(df)}일")

    # 컬럼 정보
    print(f"\n📋 컬럼 정보:")
    print(f"   컬럼명: {df.columns.tolist()}")
    print(f"   컬럼 수: {len(df.columns)}")

    # 최근 데이터 미리보기
    print(f"\n📈 최근 5일 데이터:")
    print(df.tail())

    # 컬럼 변환 테스트
    print(f"\n🔄 컬럼 변환 테스트...")
    column_mapping = {
      '시가': 'Open',
      '고가': 'High',
      '저가': 'Low',
      '종가': 'Close',
      '거래량': 'Volume'
    }

    df_renamed = df.rename(columns=column_mapping)
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df_final = df_renamed[required_columns]

    print("✅ 컬럼 변환 성공!")
    print(f"   변환된 컬럼: {df_final.columns.tolist()}")

    return True

  except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    print(traceback.format_exc())
    return False


def test_multiple_stocks():
  """여러 종목 테스트"""
  print("""
╔══════════════════════════════════════════════════╗
║        한국 주식 데이터 조회 테스트               ║
╚══════════════════════════════════════════════════╝
    """)

  test_tickers = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("373220", "LG에너지솔루션"),
    ("035720", "카카오"),
  ]

  print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

  success_count = 0
  fail_count = 0

  for ticker, name in test_tickers:
    result = test_single_stock(ticker)
    if result:
      success_count += 1
    else:
      fail_count += 1

  # 결과 요약
  print(f"\n{'=' * 60}")
  print("📊 테스트 결과 요약")
  print(f"{'=' * 60}")
  print(f"✅ 성공: {success_count}개")
  print(f"❌ 실패: {fail_count}개")
  print(f"{'=' * 60}\n")

  if success_count > 0:
    print("✅ pykrx가 정상적으로 작동합니다!")
    print("   → 이제 메인 프로그램을 실행할 수 있습니다.\n")
  else:
    print("❌ 모든 종목에서 오류가 발생했습니다.")
    print("\n🔧 해결 방법:")
    print("   1. pykrx 재설치: pip install --upgrade pykrx")
    print("   2. 장 시간 확인: 한국 주식 시장 운영 시간 (09:00-15:30)")
    print("   3. 인터넷 연결 확인\n")


def check_market_time():
  """시장 운영 시간 확인"""
  now = datetime.now()

  # 평일 확인
  is_weekday = now.weekday() < 5  # 0-4는 월-금

  # 시간 확인 (9:00 - 15:30)
  current_time = now.time()
  market_open = datetime.strptime("09:00", "%H:%M").time()
  market_close = datetime.strptime("15:30", "%H:%M").time()
  is_market_hours = market_open <= current_time <= market_close

  print(f"\n📅 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
  print(f"📊 한국 주식 시장:")

  if is_weekday:
    print("   ✅ 평일")
    if is_market_hours:
      print("   ✅ 장 운영 중 (09:00-15:30)")
    else:
      if current_time < market_open:
        print("   ⚠️  장 시작 전 (09:00 개장)")
      else:
        print("   ⚠️  장 마감 (15:30 마감)")
  else:
    print("   ⚠️  주말/공휴일")

  print("\n💡 실시간 데이터는 장중에만 업데이트됩니다.")
  print("   과거 데이터는 언제든 조회 가능합니다.\n")


if __name__ == "__main__":
  check_market_time()
  test_multiple_stocks()
