#!/usr/bin/env python3
"""
コメント表示用WebSocketサーバー（FastAPI版）
確実に動作するWebSocketサーバー
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
import sys
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import time

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
        self.clients: Set[WebSocket] = set()
        self.settings_manager = SettingsManager(UserManager())
        self.app = FastAPI()
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # FastAPIルートを設定
        self.setup_routes()
    
    def setup_routes(self):
        """FastAPIルートを設定"""
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_client(websocket)
        
        # ルートパスでHTMLファイルを配信
        @self.app.get("/")
        async def root():
            from fastapi.responses import FileResponse
            html_path = os.path.join(parent_dir, "gui", "comment_display.html")
            if os.path.exists(html_path):
                return FileResponse(html_path, media_type="text/html")
            else:
                from fastapi.responses import HTMLResponse
                return HTMLResponse(f"<h1>HTMLファイルが見つかりません: {html_path}</h1>")
        
        # 静的ファイル配信（CSS、JS、画像ファイル用）
        # GUIディレクトリを静的ファイルとして配信
        gui_dir = os.path.join(parent_dir, "gui")
        if os.path.exists(gui_dir):
            self.app.mount("/gui", StaticFiles(directory=gui_dir), name="gui")
        
        # スキン画像用の静的ファイル配信
        skin_dir = os.path.join(parent_dir, "skin")
        self.logger.info(f"スキンディレクトリ: {skin_dir}")
        if os.path.exists(skin_dir):
            self.app.mount("/skin", StaticFiles(directory=skin_dir), name="skin")
            self.logger.info(f"✅ スキン静的ファイル配信設定完了: /skin -> {skin_dir}")
        else:
            self.logger.error(f"❌ スキンディレクトリが見つかりません: {skin_dir}")
    
    async def register(self, websocket: WebSocket):
        """クライアント接続を登録"""
        self.clients.add(websocket)
        self.logger.info(f"クライアント接続: {len(self.clients)} 接続中")
    
    async def unregister(self, websocket: WebSocket):
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
        
        # デバッグログ追加
        self.logger.info(f"送信データ詳細: skin={display_data['skin']}, font={display_data['font']}, text='{display_data['text']}'")
        
        message = json.dumps(display_data, ensure_ascii=False)
        
        # 全クライアントに送信
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send_text(message)
            except WebSocketDisconnect:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"送信エラー: {e}")
                disconnected_clients.add(client)
        
        # 切断されたクライアントを削除
        for client in disconnected_clients:
            await self.unregister(client)
    
    async def handle_client(self, websocket: WebSocket):
        """クライアント接続を処理"""
        await websocket.accept()
        await self.register(websocket)
        
        try:
            while True:
                # クライアントからのメッセージを処理
                message = await websocket.receive_text()
                try:
                    data = json.loads(message)
                    self.logger.info(f"クライアントメッセージ受信: {data}")
                except json.JSONDecodeError:
                    self.logger.warning(f"不正なJSON: {message}")
        except WebSocketDisconnect:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start_server(self):
        """FastAPIサーバーを開始"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        self.logger.info(f"コメント表示WebSocketサーバー開始: http://{self.host}:{self.port}")
        self.logger.info(f"WebSocket接続: ws://{self.host}:{self.port}/ws")
        
        await server.serve()
    
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
                "timestamp": time.time()
            }
            
            # 確実に送信するために、新しいイベントループを作成して実行
            import threading
            def send_comment_sync():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.send_comment(comment_data))
                    loop.close()
                except Exception as e:
                    self.logger.error(f"同期的送信エラー: {e}")
            
            # 別スレッドで送信
            thread = threading.Thread(target=send_comment_sync)
            thread.start()
            
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
    comment_server = CommentWebSocketServer()
    
    try:
        asyncio.run(comment_server.start_server())
    except KeyboardInterrupt:
        print("サーバー停止")
    except Exception as e:
        print(f"サーバーエラー: {e}")

if __name__ == "__main__":
    start_comment_server()
