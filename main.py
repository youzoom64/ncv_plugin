import asyncio
import sys
import os

# 現在のスクリプトのディレクトリを取得してPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from handlers.websocket_handler import WebSocketHandler

def main():
    """メインエントリポイント"""
    handler = WebSocketHandler()
    
    try:
        asyncio.run(handler.connect_and_run("ws://localhost:8765"))
    except KeyboardInterrupt:
        print("\n[INFO] 👋 プログラムを終了します")
    except Exception as e:
        print(f"[ERROR] 予期しないエラー: {e}")

def test_mode():
    """テストモード"""
    handler = WebSocketHandler()
    handler.test_system()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_mode()
    else:
        main()