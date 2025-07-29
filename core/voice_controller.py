import requests
import json
import io
import pygame
import threading
import time
from typing import Optional

VOICEVOX_URL = "http://localhost:50021"

class VoiceController:
    def __init__(self, base_url=VOICEVOX_URL):
        self.base_url = base_url
        self.is_voicevox_available = False
        print("[INIT] VoiceController initialized")
        
        # pygameの音声モジュールを初期化
        try:
            pygame.mixer.quit()
            pygame.mixer.pre_init(frequency=24000, size=-16, channels=1, buffer=512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(1)
            print("[VOICE] 🔊 pygame音声システム初期化完了")
        except Exception as e:
            print(f"[VOICE ERROR] pygame初期化失敗: {e}")
        
        self._check_voicevox_connection()
    
    def _check_voicevox_connection(self):
        """VOICEVOXエンジンの接続確認"""
        try:
            response = requests.get(f"{self.base_url}/speakers", timeout=5)
            if response.status_code == 200:
                self.is_voicevox_available = True
                speakers = response.json()
                print(f"[VOICE] ✅ VOICEVOXエンジン接続成功 ({len(speakers)}人のキャラクター利用可能)")
                return True
            else:
                print(f"[VOICE] ❌ VOICEVOXエンジン応答エラー: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"[VOICE] ❌ VOICEVOXエンジンに接続できません ({self.base_url})")
            print(f"[VOICE] 💡 VOICEVOXを起動してから再度お試しください")
        except Exception as e:
            print(f"[VOICE] ❌ VOICEVOX接続確認エラー: {e}")
        
        self.is_voicevox_available = False
        return False

    def synthesize_only(self, text: str, speaker_id: int = 2, speed_scale: float = 1.0):
        """音声合成のみ実行（再生はしない）"""
        if not self.is_voicevox_available:
            return None
            
        if not text or not text.strip():
            return None
            
        if len(text) > 200:
            text = text[:197] + "..."
            
        try:
            # 1. 音声合成用クエリを作成
            query_data = self._create_audio_query(text, speaker_id, speed_scale)
            if not query_data:
                return None
            
            # 2. 音声合成
            audio_data = self._synthesize_audio(query_data, speaker_id)
            return audio_data
            
        except Exception as e:
            print(f"[SYNTHESIS ERROR] {e}")
            return None

    def play_only(self, audio_data: bytes) -> bool:
        """音声再生のみ実行"""
        try:
            pygame.mixer.stop()  # 前の音声を停止
            
            audio_io = io.BytesIO(audio_data)
            sound = pygame.mixer.Sound(audio_io)
            sound.play()
            
            # 再生完了まで待機
            while pygame.mixer.get_busy():
                time.sleep(0.01)
            
            time.sleep(0.05)  # 安全マージン
            return True
            
        except Exception as e:
            print(f"[PLAYBACK ERROR] {e}")
            return False

    def enqueue(self, text: str, speaker_id: int = 2, speed_scale: float = 1.0):
        """従来の音声合成と再生（テスト用）"""
        print(f"[VOICE] 📥 {text} (speaker:{speaker_id}, speed:{speed_scale:.1f}x)")
        
        if not self.is_voicevox_available:
            print(f"[VOICE] ⚠️  VOICEVOXエンジンが利用できません")
            return
        
        audio_data = self.synthesize_only(text, speaker_id, speed_scale)
        if audio_data:
            self.play_only(audio_data)
            print(f"[VOICE] ✅ 完了: {text}")

    def _create_audio_query(self, text: str, speaker_id: int, speed_scale: float = 1.0) -> Optional[dict]:
        """音声合成用クエリを作成"""
        try:
            response = requests.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=10
            )
            
            if response.status_code == 200:
                query_data = response.json()
                query_data["speedScale"] = speed_scale
                return query_data
            else:
                return None
                
        except Exception as e:
            return None

    def _synthesize_audio(self, query_data: dict, speaker_id: int) -> Optional[bytes]:
        """音声合成実行"""
        try:
            response = requests.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker_id},
                json=query_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                return None
                
        except Exception as e:
            return None

    def reconnect(self):
        """VOICEVOX再接続試行"""
        print("[VOICE] 🔄 VOICEVOX再接続試行中...")
        self._check_voicevox_connection()
        return self.is_voicevox_available

    def test_voice(self, text: str = "こんにちは、音声テストです", speaker_id: int = 2):
        """音声テスト用メソッド"""
        print(f"[TEST] 音声テスト開始: '{text}' (speaker:{speaker_id})")
        self.enqueue(text, speaker_id)