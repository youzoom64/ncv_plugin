#!/usr/bin/env python3
"""
現在のシステムでコメント表示用WebSocketサーバーをテスト
"""

import sys
import os
import time
import asyncio
import websockets
import json

def test_websocket_connection():
    """WebSocket接続をテスト"""
    print("🔌 WebSocket接続テスト開始")
    
    try:
        # 同期的にWebSocket接続をテスト
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def test_connection():
            try:
                async with websockets.connect("ws://localhost:8080/ws") as websocket:
                    print("✅ WebSocket接続成功")
                    
                    # テストメッセージを送信
                    test_message = {
                        "type": "test",
                        "text": "テストメッセージ",
                        "timestamp": time.time()
                    }
                    
                    await websocket.send(json.dumps(test_message, ensure_ascii=False))
                    print("📤 テストメッセージ送信完了")
                    
                    # 応答を待機
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f"📨 応答受信: {response}")
                    except asyncio.TimeoutError:
                        print("⏰ タイムアウト: 応答を受信できませんでした")
                    
            except Exception as e:
                print(f"❌ WebSocket接続エラー: {e}")
        
        loop.run_until_complete(test_connection())
        loop.close()
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")

def test_http_connection():
    """HTTP接続をテスト"""
    print("🌐 HTTP接続テスト開始")
    
    try:
        import urllib.request
        
        # HTMLファイルを取得
        response = urllib.request.urlopen("http://localhost:8080/")
        html_content = response.read().decode('utf-8')
        
        if "<title>ニコ生コメント表示</title>" in html_content:
            print("✅ HTMLファイル取得成功")
            print(f"📄 HTMLサイズ: {len(html_content)} 文字")
        else:
            print("❌ HTMLファイルの内容が不正")
            
    except Exception as e:
        print(f"❌ HTTP接続エラー: {e}")

def main():
    """メイン関数"""
    print("🧪 現在のシステムテスト開始")
    
    # HTTP接続テスト
    test_http_connection()
    
    print()
    
    # WebSocket接続テスト
    test_websocket_connection()
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    main()
