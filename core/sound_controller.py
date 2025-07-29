import pygame
import io
import time
import threading
from typing import Optional

class SoundController:
    def __init__(self):
        self.sound_lock = threading.Lock()
        print("[INIT] SoundController initialized")
        
        # pygame mixer初期化確認（VoiceControllerと共用）
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
        
        # コマンド別サウンドマッピング
        self.command_sounds = {
            "info": self._generate_info_sound(),
            "gift": self._generate_gift_sound(), 
            "ad": self._generate_ad_sound(),
            "disconnect": self._generate_disconnect_sound(),
            "connect": self._generate_connect_sound(),
            "default": self._generate_default_sound()
        }

    def _generate_info_sound(self) -> bytes:
        """INFO用音データ生成（ピコーン）"""
        # 簡単なビープ音を生成
        import numpy as np
        sample_rate = 24000
        duration = 0.3
        frequency = 800
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = np.sin(2 * np.pi * frequency * t) * 0.3
        wave = (wave * 32767).astype(np.int16)
        
        # ステレオからモノラルに
        sound_array = np.array([wave, wave]).T
        return sound_array.tobytes()

    def _generate_gift_sound(self) -> bytes:
        """GIFT用音データ生成（キラキラ音）"""
        import numpy as np
        sample_rate = 24000
        duration = 0.5
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        # 複数の周波数を重ねる
        wave = (np.sin(2 * np.pi * 1000 * t) * 0.2 + 
                np.sin(2 * np.pi * 1200 * t) * 0.2 +
                np.sin(2 * np.pi * 1500 * t) * 0.1)
        wave = (wave * 32767).astype(np.int16)
        
        sound_array = np.array([wave, wave]).T
        return sound_array.tobytes()

    def _generate_ad_sound(self) -> bytes:
        """AD用音データ生成（低い音）"""
        import numpy as np
        sample_rate = 24000
        duration = 0.4
        frequency = 400
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = np.sin(2 * np.pi * frequency * t) * 0.3
        wave = (wave * 32767).astype(np.int16)
        
        sound_array = np.array([wave, wave]).T
        return sound_array.tobytes()

    def _generate_disconnect_sound(self) -> bytes:
        """DISCONNECT用音データ生成（下降音）"""
        import numpy as np
        sample_rate = 24000
        duration = 0.6
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        # 周波数を時間と共に下降
        frequency = 600 * (1 - t / duration)
        wave = np.sin(2 * np.pi * frequency * t) * 0.3
        wave = (wave * 32767).astype(np.int16)
        
        sound_array = np.array([wave, wave]).T
        return sound_array.tobytes()

    def _generate_connect_sound(self) -> bytes:
        """CONNECT用音データ生成（上昇音）"""
        import numpy as np
        sample_rate = 24000
        duration = 0.5
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        # 周波数を時間と共に上昇
        frequency = 400 + 400 * (t / duration)
        wave = np.sin(2 * np.pi * frequency * t) * 0.3
        wave = (wave * 32767).astype(np.int16)
        
        sound_array = np.array([wave, wave]).T
        return sound_array.tobytes()

    def _generate_default_sound(self) -> bytes:
        """デフォルト音データ生成"""
        import numpy as np
        sample_rate = 24000
        duration = 0.2
        frequency = 600
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = np.sin(2 * np.pi * frequency * t) * 0.2
        wave = (wave * 32767).astype(np.int16)
        
        sound_array = np.array([wave, wave]).T
        return sound_array.tobytes()

    def get_command_sound(self, command_type: str) -> Optional[bytes]:
        """コマンドタイプに対応する音データを取得"""
        sound_data = self.command_sounds.get(command_type)
        if not sound_data:
            sound_data = self.command_sounds["default"]
        
        print(f"[SOUND] 🔊 {command_type.upper()}用サウンド取得")
        return sound_data

    def play_sound_data(self, sound_data: bytes) -> bool:
        """音データを直接再生（テスト用）"""
        try:
            with self.sound_lock:
                pygame.mixer.stop()
                
                audio_io = io.BytesIO(sound_data)
                sound = pygame.mixer.Sound(audio_io)
                sound.play()
                
                while pygame.mixer.get_busy():
                    time.sleep(0.01)
                
                time.sleep(0.05)
                return True
                
        except Exception as e:
            print(f"[SOUND ERROR] サウンド再生エラー: {e}")
            return False