import asyncio
import websockets
import json
import queue
import threading
import time
from typing import Dict, Any, Optional

from core.voice_controller import VoiceController
from core.user_manager import UserManager
from core.sound_controller import SoundController
from core.queue_manager import QueueManager
from core.settings_manager import SettingsManager
from core.comment_processor import CommentProcessor
from gui.comment_websocket_server import get_comment_server

class WebSocketHandler:
    def __init__(self):
        # コアコンポーネント初期化
        self.voice_controller = VoiceController()
        self.user_manager = UserManager()
        self.sound_controller = SoundController()
        self.queue_manager = QueueManager()
        
        # 管理コンポーネント初期化
        self.settings_manager = SettingsManager(self.user_manager)
        self.comment_processor = CommentProcessor(
            self.settings_manager, 
            self.queue_manager, 
            self.sound_controller
        )
        
        # コメント表示WebSocketサーバー
        self.comment_server = get_comment_server()
        
        # 送信用キュー
        self.send_queue = queue.Queue()
        
        print("🎤 音声合成システム開始")
        print("🔊 サウンドシステム開始")
        print("🖥️ コメント表示システム開始")
    
    async def connect_and_run(self, uri: str = "ws://localhost:8765"):
        """WebSocketサーバーに接続して実行"""
        # ワーカー開始
        self.queue_manager.start_workers(self.voice_controller)
        
        # コメント表示用WebSocketサーバーを起動
        print("🔌 コメント表示用WebSocketサーバーを起動中...")
        try:
            # コメント表示用WebSocketサーバーを非同期で起動
            server_task = asyncio.create_task(self.comment_server.start_server())
            print("✅ コメント表示用WebSocketサーバー起動完了")
            
            # サーバーが起動するまで少し待機
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"[ERROR] コメント表示用WebSocketサーバー起動エラー: {e}")
        
        print("🔌 WebSocketサーバー接続中...")
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✅ 接続完了")
                print("💬 コメント送信: 'send:メッセージ' と入力してEnter")
                print("=" * 80)
                
                # 入力処理スレッド開始
                self._start_input_worker()
                
                # 送信処理タスク開始
                send_task = asyncio.create_task(self._send_worker(websocket))
                
                # メッセージ受信ループ
                async for message in websocket:
                    await self._handle_message(message)
                    
        except Exception as e:
            print(f"[ERROR] WebSocket接続エラー: {e}")
        finally:
            self.queue_manager.shutdown()
    
    def _start_input_worker(self):
        """キーボード入力処理スレッド"""
        def input_worker():
            while True:
                try:
                    user_input = input()
                    if user_input.startswith("send:"):
                        message = user_input[5:]
                        send_data = json.dumps({"action": "send_comment", "message": message})
                        self.send_queue.put(send_data)
                        print(f"[送信] {message}")
                except:
                    break
        
        threading.Thread(target=input_worker, daemon=True).start()
    
    async def _send_worker(self, websocket):
        """送信処理ワーカー"""
        while True:
            try:
                if not self.send_queue.empty():
                    send_data = self.send_queue.get()
                    await websocket.send(send_data)
                await asyncio.sleep(0.1)
            except:
                break
    
    async def _handle_message(self, message: str):
        """受信メッセージ処理"""
        try:
            data = self._parse_json_message(message)
            if not data:
                return
            
            # コメント処理
            success = self.comment_processor.process_comment(data)
            
            # コメント表示用WebSocketで送信
            if "comment" in data:
                comment_text = data.get("comment", "")
                user_id = data.get("user_id", "")
                print(f"[DISPLAY] コメント表示用WebSocketに送信: {comment_text}")
                try:
                    # コメント表示用WebSocketサーバーに送信
                    if self.comment_server:
                        # 非同期で送信
                        asyncio.create_task(self.comment_server.send_comment({
                            "text": comment_text,
                            "user_id": user_id,
                            "timestamp": time.time()
                        }))
                        print(f"[DISPLAY] ✅ コメント表示用WebSocketに送信完了: {comment_text}")
                    else:
                        print(f"[DISPLAY] ❌ コメント表示用WebSocketサーバーが利用できません")
                except Exception as e:
                    print(f"[DISPLAY ERROR] コメント表示送信エラー: {e}")
            elif "text" in data:  # 別の形式のコメントデータ
                comment_text = data.get("text", "")
                user_id = data.get("user_id", "")
                print(f"[DISPLAY] コメント表示用WebSocketに送信（text形式）: {comment_text}")
                try:
                    # コメント表示用WebSocketサーバーに送信
                    if self.comment_server:
                        # 非同期で送信
                        asyncio.create_task(self.comment_server.send_comment({
                            "text": comment_text,
                            "user_id": user_id,
                            "timestamp": time.time()
                        }))
                        print(f"[DISPLAY] ✅ コメント表示用WebSocketに送信完了（text形式）: {comment_text}")
                    else:
                        print(f"[DISPLAY] ❌ コメント表示用WebSocketサーバーが利用できません")
                except Exception as e:
                    print(f"[DISPLAY ERROR] コメント表示送信エラー（text形式）: {e}")
            
            # 統計情報表示
            self._show_stats_if_needed(data)
            
            print("=" * 80)
            
        except KeyboardInterrupt:
            print("[INFO] 👋 ユーザーによる中断")
            raise
        except Exception as e:
            print(f"[ERROR] ❌ メッセージ処理エラー: {e}")
            print(f"[ERROR] 📝 問題のメッセージ: {message}")
            import traceback
            traceback.print_exc()
            print("=" * 80)
    
    def _parse_json_message(self, message: str) -> Optional[Dict[str, Any]]:
        """JSONメッセージをパース"""
        try:
            return json.loads(message)
        except json.JSONDecodeError as e:
            print(f"[JSON ERROR] 不正なJSON: {message}")
            return None
    
    def _show_stats_if_needed(self, data: Dict[str, Any]):
        """必要に応じて統計情報を表示"""
        comment_no = data.get("comment_no", "")
        if comment_no and isinstance(comment_no, int) and comment_no % 100 == 0:
            stats = self.user_manager.get_user_stats()
            print(f"[STATS] 📊 総ユーザー数: {stats['total_users']}, 最近のユーザー: {stats['recent_users']}")
    
    def test_system(self):
        """システムテスト"""
        print("[DEBUG] テスト開始")
        print(f"[DEBUG] VOICEVOX利用可能: {self.voice_controller.is_voicevox_available}")
        
        print("[DEBUG] 手動接続テスト開始")
        result = self.voice_controller.reconnect()
        print(f"[DEBUG] 接続結果: {result}")
        
        # 音声テスト
        self.voice_controller.enqueue("テスト音声です。ずんだもんだっぽ！", speaker_id=3)
        
        # サウンドテスト
        info_sound = self.sound_controller.get_command_sound("info")
        if info_sound:
            self.sound_controller.play_sound_data(info_sound)