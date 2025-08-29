#!/usr/bin/env python3
"""
コメント表示システムテスト用スクリプト
"""

import asyncio
import websockets
import json
import time
import sys
import os

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.comment_websocket_server import get_comment_server

async def test_comment_display():
    """コメント表示をテスト"""
    print("🧪 コメント表示システムテスト開始")
    
    # コメントサーバーを取得
    server = get_comment_server()
    
    # テストコメントデータ
    test_comments = [
        {"text": "こんにちは！", "skin": "154", "font": 1},
        {"text": "テストコメントです", "skin": "6", "font": 5},
        {"text": "スキンとフォントのテスト", "skin": "7", "font": 10},
        {"text": "アニメーション確認", "skin": "8", "font": 15},
        {"text": "最後のテスト", "skin": "9", "font": 19}
    ]
    
    print("📝 テストコメントを送信します...")
    
    for i, comment_data in enumerate(test_comments, 1):
        print(f"  コメント {i}: {comment_data['text']} (スキン:{comment_data['skin']}, フォント:{comment_data['font']})")
        
        # コメントを送信
        server.process_comment(
            comment_data["text"], 
            user_id=f"test_user_{i}"
        )
        
        # 2秒待機
        await asyncio.sleep(2)
    
    print("✅ テスト完了！")
    print("ブラウザでコメント表示を確認してください。")

def main():
    """メイン関数"""
    try:
        asyncio.run(test_comment_display())
    except KeyboardInterrupt:
        print("\n👋 テスト中断")
    except Exception as e:
        print(f"❌ テストエラー: {e}")

if __name__ == "__main__":
    main()
