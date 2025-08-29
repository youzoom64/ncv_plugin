#!/usr/bin/env python3
"""
実際のコメントを送信してテスト
"""

import sys
import os
import time
import asyncio
import websockets
import json

def test_real_comment():
    """実際のコメントを送信してテスト"""
    print("🧪 実際のコメント送信テスト開始")
    
    try:
        # 同期的にWebSocket接続をテスト
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_real_comment():
            try:
                async with websockets.connect("ws://localhost:8080/ws") as websocket:
                    print("✅ WebSocket接続成功")
                    
                    # 実際のコメントデータを送信
                    real_comment = {
                        "type": "comment",
                        "text": "おすすさん",
                        "user_id": "a:ePCftCx33jk_4sOG",
                        "timestamp": time.time()
                    }
                    
                    await websocket.send(json.dumps(real_comment, ensure_ascii=False))
                    print("📤 実際のコメント送信完了")
                    
                    # 応答を待機
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f"📨 応答受信: {response}")
                    except asyncio.TimeoutError:
                        print("⏰ タイムアウト: 応答を受信できませんでした")
                    
            except Exception as e:
                print(f"❌ WebSocket接続エラー: {e}")
        
        loop.run_until_complete(send_real_comment())
        loop.close()
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")

def main():
    """メイン関数"""
    print("🧪 実際のコメント送信テスト開始")
    
    # 実際のコメント送信テスト
    test_real_comment()
    
    print("\n✅ テスト完了")
    print("ブラウザでコメント表示を確認してください")

if __name__ == "__main__":
    main()
