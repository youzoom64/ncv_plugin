# core/voice_controller.py
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
        self.speakers_info = {}  # スピーカー情報を保存
        print("[INIT] VoiceController initialized")
        
        # pygameの音声モジュールを初期化
        try:
            pygame.mixer.quit()
            pygame.mixer.pre_init(frequency=24000, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)  # 複数チャンネル対応
            print("[VOICE] 🔊 pygame音声システム初期化完了（8チャンネル対応）")
        except Exception as e:
            print(f"[VOICE ERROR] pygame初期化失敗: {e}")
        
        self._check_voicevox_connection()
        self._load_speakers_info()  # スピーカー情報を取得
    
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
    
    def _load_speakers_info(self):
        """VOICEVOXからスピーカー情報を取得"""
        if not self.is_voicevox_available:
            return
        
        try:
            response = requests.get(f"{self.base_url}/speakers", timeout=5)
            if response.status_code == 200:
                speakers_data = response.json()
                
                for speaker in speakers_data:
                    speaker_name = speaker.get("name", "不明")
                    for style in speaker.get("styles", []):
                        style_id = style.get("id")
                        style_name = style.get("name", "ノーマル")
                        full_name = f"{speaker_name}({style_name})"
                        
                        self.speakers_info[style_id] = {
                            "speaker_name": speaker_name,
                            "style_name": style_name,
                            "full_name": full_name
                        }
                
                print(f"[VOICE] 📋 {len(self.speakers_info)}個のボイススタイルを取得")
        except Exception as e:
            print(f"[VOICE ERROR] スピーカー情報取得エラー: {e}")
    
    def get_available_speaker_ids(self) -> list:
        """利用可能なスピーカーIDのリストを取得"""
        return sorted(list(self.speakers_info.keys()))
    
    def get_voice_name(self, speaker_id: int) -> str:
        """スピーカーIDからボイス名を取得"""
        if speaker_id in self.speakers_info:
            return self.speakers_info[speaker_id]["full_name"]
        return f"不明なボイス(ID:{speaker_id})"
    
    def get_speaker_name(self, speaker_id: int) -> str:
        """スピーカーIDからキャラクター名のみを取得"""
        if speaker_id in self.speakers_info:
            return self.speakers_info[speaker_id]["speaker_name"]
        return f"不明(ID:{speaker_id})"

    def synthesize_only(self, text: str, speaker_id: int = 2, speed_scale: float = 1.0):
        """音声合成のみ実行（再生はしない）"""
        print(f"[DEBUG] synthesize_only開始: text='{text}', speaker_id={speaker_id}")
        
        if not self.is_voicevox_available:
            print(f"[DEBUG] VOICEVOX利用不可")
            return None
            
        if not text or not text.strip():
            print(f"[DEBUG] テキストが空")
            return None
            
        if len(text) > 200:
            text = text[:197] + "..."
            
        try:
            # 1. 音声合成用クエリを作成
            print(f"[DEBUG] クエリ作成中...")
            query_data = self._create_audio_query(text, speaker_id, speed_scale)
            if not query_data:
                print(f"[DEBUG] クエリ作成失敗")
                return None
            
            print(f"[DEBUG] クエリ作成成功")
            
            # 2. 音声合成
            print(f"[DEBUG] 音声合成中...")
            audio_data = self._synthesize_audio(query_data, speaker_id)
            
            if audio_data:
                print(f"[DEBUG] 音声合成成功: {len(audio_data)}バイト")
            else:
                print(f"[DEBUG] 音声合成失敗")
            
            return audio_data
            
        except Exception as e:
            print(f"[SYNTHESIS ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def play_only(self, audio_data: bytes) -> bool:
        """音声再生のみ実行（音声専用チャンネル使用）"""
        try:
            # サウンドと干渉しないよう音声専用チャンネルを使用
            audio_io = io.BytesIO(audio_data)
            sound = pygame.mixer.Sound(audio_io)
            
            # チャンネル0-3を音声専用に予約
            voice_channel = None
            for i in range(4):  # チャンネル0-3を音声用として確保
                channel = pygame.mixer.Channel(i)
                if not channel.get_busy():
                    voice_channel = channel
                    break
            
            if voice_channel:
                voice_channel.play(sound)
                print(f"[VOICE] 🎤 音声再生開始（チャンネル{voice_channel}）")
            else:
                # 全ての音声チャンネルが使用中の場合はチャンネル0を強制使用
                voice_channel = pygame.mixer.Channel(0)
                voice_channel.stop()  # 既存の音声を停止
                voice_channel.play(sound)
                print(f"[VOICE] 🎤 音声再生開始（チャンネル0強制使用）")
            
            # 再生完了まで待機
            while voice_channel.get_busy():
                time.sleep(0.01)
            
            time.sleep(0.05)  # 安全マージン
            print(f"[VOICE] ✅ 音声再生完了")
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
        if self.is_voicevox_available:
            self._load_speakers_info()
        return self.is_voicevox_available

    def test_voice(self, text: str = "こんにちは、音声テストです", speaker_id: int = 2):
        """音声テスト用メソッド"""
        print(f"[TEST] 音声テスト開始: '{text}' (speaker:{speaker_id})")
        self.enqueue(text, speaker_id)

    def get_voice_controller_instance(self):
        """外部からVoiceControllerインスタンスにアクセス"""
        return self