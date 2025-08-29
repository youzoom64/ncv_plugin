#!/usr/bin/env python3
"""
コメント表示用WebSocketサーバーの動作テスト
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

async def test_websocket_server():
    """WebSocketサーバーの動作をテスト"""
    print("🧪 コメント表示用WebSocketサーバーの動作テスト開始")
    
    # コメント表示用WebSocketサーバーを取得
    comment_server = get_comment_server()
    print(f"✅ コメントサーバー取得: {comment_server}")
    
    # サーバーを起動
    print("🚀 サーバー起動中...")
    server_task = asyncio.create_task(comment_server.start_server())
    
    # 少し待機
    await asyncio.sleep(3)
    
    # テストコメントを送信
    print("📝 テストコメントを送信中...")
    comment_server.process_comment("テストコメントです！", "test_user")
    
    # さらに待機
    await asyncio.sleep(2)
    
    # サーバーを停止
    print("🛑 サーバー停止中...")
    server_task.cancel()
    
    print("✅ テスト完了")

async def test_websocket_client():
    """WebSocketクライアントとしてテスト"""
    print("🔌 WebSocketクライアントとしてテスト開始")
    
    try:
        async with websockets.connect("ws://localhost:8080/ws") as websocket:
            print("✅ WebSocket接続成功")
            
            # メッセージを受信
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 受信メッセージ: {message}")
                
                # JSONとしてパース
                data = json.loads(message)
                print(f"📊 パース結果: {data}")
                
            except asyncio.TimeoutError:
                print("⏰ タイムアウト: メッセージを受信できませんでした")
                
    except Exception as e:
        print(f"❌ WebSocket接続エラー: {e}")

async def main():
    """メイン関数"""
    print("🎯 コメント表示システムテスト開始")
    
    # サーバーテスト
    await test_websocket_server()
    
    # クライアントテスト
    await test_websocket_client()
    
    print("🏁 テスト完了")

if __name__ == "__main__":
    asyncio.run(main())
