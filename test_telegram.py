"""
텔레그램 봇 설정 테스트 스크립트
봇 토큰과 Chat ID가 올바른지 확인합니다
"""

import requests
import sys

def test_telegram_bot():
    """텔레그램 봇 설정 테스트"""

    print("="*60)
    print("🤖 텔레그램 봇 설정 테스트")
    print("="*60)

    # 사용자에게 입력 받기
    print("\n📝 설정 정보를 입력하세요\n")

    bot_token = input("텔레그램 봇 토큰 입력: ").strip()
    if not bot_token:
        print("❌ 봇 토큰이 비어있습니다!")
        return

    chat_id = input("Chat ID 입력: ").strip()
    if not chat_id:
        print("❌ Chat ID가 비어있습니다!")
        return

    print("\n" + "="*60)
    print("🔍 테스트 시작...")
    print("="*60)

    # 1. 봇 정보 확인
    print("\n1️⃣ 봇 정보 확인 중...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result'].get('first_name', 'Unknown')
                bot_username = bot_info['result'].get('username', 'Unknown')
                print(f"   ✅ 봇 연결 성공!")
                print(f"   📛 봇 이름: {bot_name}")
                print(f"   🔤 봇 유저네임: @{bot_username}")
            else:
                print(f"   ❌ 봇 정보 조회 실패: {bot_info}")
                return
        else:
            print(f"   ❌ HTTP 오류: {response.status_code}")
            print(f"   💬 응답: {response.text}")
            print("\n   ⚠️  봇 토큰이 잘못되었을 수 있습니다!")
            return
    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")
        return

    # 2. 메시지 전송 테스트
    print("\n2️⃣ 테스트 메시지 전송 중...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': '✅ 텔레그램 봇 테스트 성공!\n\n윌리엄 오닐 돌파매매 봇이 정상적으로 작동합니다.',
            'parse_mode': 'HTML'
        }

        response = requests.post(url, data=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("   ✅ 메시지 전송 성공!")
                print("   📱 텔레그램 앱에서 메시지를 확인하세요!")
            else:
                print(f"   ❌ 메시지 전송 실패: {result}")
        elif response.status_code == 404:
            print("   ❌ HTTP 404 오류 - Chat ID를 찾을 수 없습니다!")
            print("\n   📋 Chat ID 확인 방법:")
            print("   1. 봇에게 아무 메시지나 보내기 (예: /start)")
            print("   2. 브라우저에서 다음 URL 열기:")
            print(f"      https://api.telegram.org/bot{bot_token}/getUpdates")
            print("   3. 결과에서 \"chat\":{\"id\":XXXXXXX 찾기")
            print("   4. 그 숫자가 Chat ID입니다")
        elif response.status_code == 401:
            print("   ❌ HTTP 401 오류 - 봇 토큰이 잘못되었습니다!")
        else:
            print(f"   ❌ HTTP 오류: {response.status_code}")
            print(f"   💬 응답: {response.text}")
    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")
        return

    # 3. 최근 업데이트 확인 (Chat ID 찾기 도움)
    print("\n3️⃣ Chat ID 재확인...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok') and updates.get('result'):
                print("   ℹ️  최근 대화 목록:")
                seen_chats = set()
                for update in updates['result'][-5:]:  # 최근 5개만
                    if 'message' in update:
                        msg_chat_id = update['message']['chat']['id']
                        chat_type = update['message']['chat'].get('type', 'unknown')

                        if msg_chat_id not in seen_chats:
                            seen_chats.add(msg_chat_id)

                            match_indicator = "✅ (입력한 ID와 일치)" if str(msg_chat_id) == str(chat_id) else ""
                            print(f"      Chat ID: {msg_chat_id} ({chat_type}) {match_indicator}")

                if str(chat_id) not in [str(cid) for cid in seen_chats]:
                    print(f"\n   ⚠️  입력한 Chat ID({chat_id})가 최근 대화에 없습니다!")
                    print("   💡 봇에게 먼저 메시지를 보내셨나요?")
            else:
                print("   ℹ️  최근 대화 없음")
                print("   💡 봇에게 메시지를 먼저 보내주세요!")
        else:
            print(f"   ⚠️  업데이트 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  업데이트 확인 중 오류: {e}")

    # 최종 결과
    print("\n" + "="*60)
    print("✅ 테스트 완료!")
    print("="*60)
    print("\n📋 설정 정보 (코드에 입력하세요):")
    print(f"   TELEGRAM_TOKEN = \"{bot_token}\"")
    print(f"   CHAT_ID = \"{chat_id}\"")
    print("\n")

def get_chat_id_helper(bot_token):
    """Chat ID 찾기 도우미"""
    print("\n🔍 Chat ID 찾기 도우미")
    print("="*60)

    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok') and updates.get('result'):
                print("✅ 발견된 Chat ID 목록:\n")

                seen_chats = {}
                for update in updates['result']:
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        chat_type = msg['chat'].get('type', 'unknown')

                        if chat_id not in seen_chats:
                            seen_chats[chat_id] = chat_type

                if seen_chats:
                    for chat_id, chat_type in seen_chats.items():
                        print(f"   Chat ID: {chat_id}")
                        print(f"   타입: {chat_type}")
                        print(f"   코드: CHAT_ID = \"{chat_id}\"")
                        print()
                else:
                    print("⚠️  Chat ID를 찾을 수 없습니다.")
                    print("💡 봇에게 메시지를 먼저 보내주세요!")
            else:
                print("⚠️  최근 메시지가 없습니다.")
                print("💡 봇에게 /start 또는 아무 메시지나 보내주세요!")
        else:
            print(f"❌ 오류: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║        텔레그램 봇 설정 테스트 도구               ║
╚══════════════════════════════════════════════════╝
    """)

    print("1️⃣  전체 테스트 (봇 토큰 + Chat ID)")
    print("2️⃣  Chat ID 찾기 (봇 토큰만 있을 때)")
    print()

    choice = input("선택하세요 (1 또는 2): ").strip()

    if choice == "1":
        test_telegram_bot()
    elif choice == "2":
        bot_token = input("\n텔레그램 봇 토큰 입력: ").strip()
        if bot_token:
            get_chat_id_helper(bot_token)
        else:
            print("❌ 봇 토큰이 비어있습니다!")
    else:
        print("❌ 잘못된 선택입니다!")
