#!/usr/bin/env python3
"""
コメント送信テスト（現在のシステム用）
"""

import sys
import os
import time

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.comment_websocket_server import get_comment_server

def main():
    """メイン関数"""
    print("🧪 コメント送信テスト開始（現在のシステム用）")
    
    # コメント表示用WebSocketサーバーを取得
    comment_server = get_comment_server()
    print(f"✅ コメントサーバー取得: {comment_server}")
    
    # テストコメントを送信
    print("📝 テストコメントを送信中...")
    
    test_comments = [
        "テストコメント1: こんにちは！",
        "テストコメント2: 動作確認中",
        "テストコメント3: WebSocket接続テスト",
        "テストコメント4: HTML表示テスト",
        "テストコメント5: 最終確認"
    ]
    
    for i, comment in enumerate(test_comments):
        print(f"📤 コメント {i+1}: {comment}")
        try:
            comment_server.process_comment(comment, f"test_user_{i}")
            print(f"✅ コメント {i+1} 送信完了")
        except Exception as e:
            print(f"❌ コメント {i+1} 送信エラー: {e}")
        time.sleep(2)
    
    print("✅ テスト完了")
    print("ブラウザでコメント表示を確認してください")

if __name__ == "__main__":
    main()
