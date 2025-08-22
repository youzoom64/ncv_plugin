import queue
import threading
import time
from typing import Callable, Any, Optional

class QueueManager:
    def __init__(self):
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.workers = []
        self.running = True
        
    def calculate_speed(self, qsize: int) -> float:
        """キューサイズに応じて読み上げ速度を動的調整"""
        if qsize <= 0:
            return 1.0
        elif qsize <= 5:
            return 1.0
        elif qsize <= 10:
            return 1.2
        elif qsize <= 20:
            return 1.5
        elif qsize <= 30:
            return 2.0
        elif qsize <= 40:
            return 2.5
        else:
            return 3.0
    
    def start_workers(self, voice_controller, num_synthesis_workers: int = 5):
        """ワーカースレッドを開始"""
        # 音声合成ワーカー（複数並行）
        for i in range(num_synthesis_workers):
            worker = threading.Thread(
                target=self._synthesis_worker, 
                args=(voice_controller,), 
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            print(f"[QUEUE] 音声合成ワーカー {i+1} 開始")
        
        # 音声再生ワーカー（1つのみ）
        playback_worker = threading.Thread(
            target=self._playback_worker, 
            args=(voice_controller,), 
            daemon=True
        )
        playback_worker.start()
        self.workers.append(playback_worker)
        print(f"[QUEUE] 音声再生ワーカー開始")
    
    def _synthesis_worker(self, voice_controller):
        """音声合成専用ワーカー"""
        print("[SYNTHESIS] 音声合成ワーカー開始")
        while self.running:
            try:
                item = self.text_queue.get(timeout=0.1)
                if item is None:  # 終了シグナル
                    break
                    
                comment_text, voice_id = item
                
                # 現在のキューサイズで速度を決定
                total_qsize = self.text_queue.qsize() + self.audio_queue.qsize()
                speed = self.calculate_speed(total_qsize)
                
                print(f"[SYNTHESIS] 🔄 合成開始: '{comment_text}' (voice:{voice_id}, speed:{speed:.1f}x)")
                
                # 音声合成のみ実行
                audio_data = voice_controller.synthesize_only(comment_text, voice_id, speed)
                if audio_data:
                    # 合成完了したら再生キューに追加
                    self.audio_queue.put((comment_text, audio_data))
                    print(f"[SYNTHESIS] ✅ 合成完了: '{comment_text}' → 再生キューに追加")
                else:
                    print(f"[SYNTHESIS] ❌ 合成失敗: '{comment_text}'")
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[SYNTHESIS ERROR] 音声合成エラー: {e}")
            finally:
                try:
                    self.text_queue.task_done()
                except:
                    pass
    
    def _playback_worker(self, voice_controller):
        """音声再生専用ワーカー"""
        print("[PLAYBACK] 音声再生ワーカー開始")
        while self.running:
            try:
                item = self.audio_queue.get(timeout=0.1)
                if item is None:  # 終了シグナル
                    break
                    
                comment_text, audio_data = item
                
                print(f"[PLAYBACK] 🔊 再生開始: '{comment_text}'")
                
                # 音声再生のみ実行（音声・サウンド共通）
                success = voice_controller.play_only(audio_data)
                if success:
                    print(f"[PLAYBACK] ✅ 再生完了: '{comment_text}'")
                else:
                    print(f"[PLAYBACK] ❌ 再生失敗: '{comment_text}'")
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[PLAYBACK ERROR] 音声再生エラー: {e}")
            finally:
                try:
                    self.audio_queue.task_done()
                except:
                    pass
    
    def add_to_synthesis_queue(self, text: str, voice_id: int):
        """音声合成キューに追加"""
        self.text_queue.put((text, voice_id))
        
        # ログ出力
        total_queue_size = self.text_queue.qsize() + self.audio_queue.qsize()
        current_speed = self.calculate_speed(total_queue_size)
        
        print(f"[VOICE] 📥 '{text}' → 合成キューに追加")
        print(f"[QUEUE] 合成待ち:{self.text_queue.qsize()}, 再生待ち:{self.audio_queue.qsize()}, 速度:{current_speed:.1f}x")
        
        if total_queue_size <= 5:
            print(f"[QUEUE] 🟢 通常速度")
        elif total_queue_size <= 10:
            print(f"[QUEUE] 🟡 少し速め")
        elif total_queue_size <= 20:
            print(f"[QUEUE] 🟠 高速モード")
        elif total_queue_size <= 30:
            print(f"[QUEUE] 🔴 超高速モード")
        else:
            print(f"[QUEUE] 🚨 最高速モード")
    
    def add_to_playback_queue(self, comment_text: str, audio_data: bytes):
        """音声再生キューに追加（サウンド用）"""
        self.audio_queue.put((comment_text, audio_data))
        print(f"[QUEUE] 🔊 '{comment_text}' → 再生キューに追加")
        print(f"[QUEUE] 合成待ち:{self.text_queue.qsize()}, 再生待ち:{self.audio_queue.qsize()}")
    
    def get_queue_status(self) -> dict:
        """キューの状態を取得"""
        return {
            "synthesis_queue": self.text_queue.qsize(),
            "playback_queue": self.audio_queue.qsize(),
            "total_queue": self.text_queue.qsize() + self.audio_queue.qsize(),
            "current_speed": self.calculate_speed(self.text_queue.qsize() + self.audio_queue.qsize())
        }
    
    def shutdown(self):
        """ワーカーを安全に終了"""
        self.running = False
        
        # 終了シグナルを送信
        for _ in self.workers:
            self.text_queue.put(None)
            self.audio_queue.put(None)
        
        # ワーカーの終了を待機
        for worker in self.workers:
            worker.join(timeout=2)
        
        print("[QUEUE] すべてのワーカーが終了しました")