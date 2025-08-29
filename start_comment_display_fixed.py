#!/usr/bin/env python3
"""
コメント表示用WebSocketサーバーを直接起動
"""

import sys
import os

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.comment_websocket_server import get_comment_server
import asyncio

async def main():
    """メイン関数"""
    print("🚀 コメント表示用WebSocketサーバーを起動中...")
    
    # コメント表示用WebSocketサーバーを取得
    comment_server = get_comment_server()
    print(f"✅ コメントサーバー取得: {comment_server}")
    
    # サーバーを起動
    print("🔌 サーバー起動中...")
    try:
        await comment_server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 サーバー停止")
    except Exception as e:
        print(f"❌ サーバーエラー: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 終了")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
