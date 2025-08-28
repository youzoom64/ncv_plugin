#!/usr/bin/env python3
"""
コメント表示用WebSocketサーバー
既存のWebSocketハンドラーと連携してコメントデータを送信
"""

import asyncio
import websockets
import json
import logging
from typing import Set, Dict, Any
import sys
import os

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.comment_parser import parse_comment
from core.settings_manager import SettingsManager
from core.user_manager import UserManager

class CommentWebSocketServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.settings_manager = SettingsManager(UserManager())
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """クライアント接続を登録"""
        self.clients.add(websocket)
        self.logger.info(f"クライアント接続: {len(self.clients)} 接続中")
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """クライアント接続を解除"""
        self.clients.remove(websocket)
        self.logger.info(f"クライアント切断: {len(self.clients)} 接続中")
    
    async def send_comment(self, comment_data: Dict[str, Any]):
        """全クライアントにコメントデータを送信"""
        if not self.clients:
            return
        
        # コメントデータを整形
        display_data = {
            "type": "comment",
            "text": comment_data.get("text", ""),
            "skin": comment_data.get("skin"),
            "font": comment_data.get("font", 0),
            "timestamp": comment_data.get("timestamp", 0)
        }
        
        message = json.dumps(display_data, ensure_ascii=False)
        
        # 全クライアントに送信
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"送信エラー: {e}")
                disconnected_clients.add(client)
        
        # 切断されたクライアントを削除
        for client in disconnected_clients:
            await self.unregister(client)
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """クライアント接続を処理"""
        await self.register(websocket)
        try:
            async for message in websocket:
                # クライアントからのメッセージを処理（必要に応じて）
                try:
                    data = json.loads(message)
                    self.logger.info(f"クライアントメッセージ受信: {data}")
                except json.JSONDecodeError:
                    self.logger.warning(f"不正なJSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start_server(self):
        """WebSocketサーバーを開始"""
        async with websockets.serve(self.handle_client, self.host, self.port):
            self.logger.info(f"コメント表示WebSocketサーバー開始: ws://{self.host}:{self.port}")
            await asyncio.Future()  # 無限ループ
    
    def process_comment(self, raw_comment: str, user_id: str = None):
        """コメントを処理してWebSocketで送信"""
        try:
            # コメントを解析
            parsed = parse_comment(raw_comment)
            
            # ユーザー設定を解決
            if user_id:
                final_settings = self.settings_manager.resolve_user_settings(user_id, parsed)
            else:
                final_settings = {
                    "name": parsed.get("name"),
                    "voice": parsed.get("voice", 2),
                    "skin": parsed.get("skin"),
                    "font": parsed.get("font", 0),
                    "sound": parsed.get("sound")
                }
            
            # 表示用データを作成
            comment_data = {
                "text": parsed.get("text", raw_comment),
                "skin": final_settings.get("skin"),
                "font": final_settings.get("font", 0),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 非同期で送信
            asyncio.create_task(self.send_comment(comment_data))
            
            self.logger.info(f"コメント送信: {comment_data}")
            
        except Exception as e:
            self.logger.error(f"コメント処理エラー: {e}")

# グローバルインスタンス
comment_server = None

def get_comment_server():
    """コメントサーバーのインスタンスを取得"""
    global comment_server
    if comment_server is None:
        comment_server = CommentWebSocketServer()
    return comment_server

def start_comment_server():
    """コメントサーバーを開始"""
    global comment_server
    if comment_server is None:
        comment_server = CommentWebSocketServer()
    
    try:
        asyncio.run(comment_server.start_server())
    except KeyboardInterrupt:
        print("サーバー停止")
    except Exception as e:
        print(f"サーバーエラー: {e}")

if __name__ == "__main__":
    start_comment_server()
