import pygame
import io
import time
import threading
import os
import requests
from typing import Optional
import numpy as np

from core.sound_config_manager import SoundConfigManager, SoundConfig

class SoundController:
    def __init__(self, config_path: str = "config/sound_config.yaml"):
        self.sound_lock = threading.Lock()
        self.config_manager = SoundConfigManager(config_path)
        self.sound_cache = {}
        
        print("[INIT] SoundController initialized with config")
        
        # pygame mixer初期化（複数チャンネル対応）
        if not pygame.mixer.get_init():
            gen_settings = self.config_manager.get_generation_settings()
            pygame.mixer.init(
                frequency=gen_settings.get('sample_rate', 24000),
                size=-16,
                channels=gen_settings.get('channels', 2),
                buffer=512
            )
        
        # 複数チャンネル設定（音声用とサウンド用を分離）
        pygame.mixer.set_num_channels(8)  # チャンネル数を増やす
        
        # 利用可能なコマンドを表示
        commands = self.config_manager.list_commands()
        print(f"[SOUND] {len(commands)}個のサウンドコマンドが利用可能:")
        for cmd, desc in commands.items():
            print(f"  /{cmd}: {desc}")

    def get_command_sound(self, command_type: str) -> Optional[bytes]:
        """コマンドタイプに対応する音データを取得"""
        # キャッシュから取得
        if command_type in self.sound_cache:
            print(f"[SOUND] 🔊 {command_type.upper()}用サウンド取得（キャッシュ）")
            return self.sound_cache[command_type]
        
        # 設定を取得
        config = self.config_manager.get_sound_config(command_type)
        print(f"[SOUND] 🔊 {command_type.upper()}用サウンド生成: {config.description}")
        
        # タイプに応じて音声データを生成・取得
        sound_data = None
        
        if config.type == "generated":
            sound_data = self._generate_sound(config)
        elif config.type == "file":
            sound_data = self._load_sound_file(config)
        elif config.type == "url":
            sound_data = self._download_sound(config)
        
        # キャッシュに保存
        if sound_data and self.config_manager.global_settings.get('cache_sounds', True):
            self.sound_cache[command_type] = sound_data
        
        return sound_data

    def play_sound_immediately(self, sound_data: bytes) -> bool:
        """音データを即座に並行再生（音声と重ねて再生）"""
        try:
            print(f"[SOUND] 🔊 サウンド即座再生開始（並行再生）")
            
            # 新しいスレッドで即座に再生
            def play_in_thread():
                try:
                    audio_io = io.BytesIO(sound_data)
                    sound = pygame.mixer.Sound(audio_io)
                    
                    # サウンド専用チャンネルで再生（音声と並行）
                    sound_channel = pygame.mixer.Channel(6)  # チャンネル6をサウンド専用に
                    sound_channel.play(sound)
                    
                    # サウンドの再生完了まで待機
                    while sound_channel.get_busy():
                        time.sleep(0.01)
                    
                    print(f"[SOUND] ✅ サウンド並行再生完了")
                    
                except Exception as e:
                    print(f"[SOUND ERROR] 並行再生エラー: {e}")
            
            # 別スレッドで即座に開始
            threading.Thread(target=play_in_thread, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"[SOUND ERROR] サウンド即座再生エラー: {e}")
            return False

    def play_sound_data(self, sound_data: bytes) -> bool:
        """音データを直接再生（テスト用・従来の同期再生）"""
        try:
            with self.sound_lock:
                # 既存の音声を停止せず、並行再生
                audio_io = io.BytesIO(sound_data)
                sound = pygame.mixer.Sound(audio_io)
                
                # 空いているチャンネルで再生
                channel = pygame.mixer.find_channel()
                if channel:
                    channel.play(sound)
                else:
                    # 全チャンネルが使用中の場合はチャンネル7を強制使用
                    pygame.mixer.Channel(7).play(sound)
                
                while pygame.mixer.get_busy():
                    time.sleep(0.01)
                
                time.sleep(0.05)
                return True
                
        except Exception as e:
            print(f"[SOUND ERROR] サウンド再生エラー: {e}")
            return False

    def _generate_sound(self, config: SoundConfig) -> bytes:
        """設定に基づいて音を生成"""
        gen_settings = self.config_manager.get_generation_settings()
        sample_rate = gen_settings.get('sample_rate', 24000)
        
        duration = config.duration
        volume = config.volume * self.config_manager.get_master_volume()
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        if config.sound_type == "chime" and config.frequencies:
            # 複数周波数の重ね合わせ
            wave = np.zeros_like(t)
            for freq in config.frequencies:
                wave += np.sin(2 * np.pi * freq * t) * (volume / len(config.frequencies))
        
        elif config.sound_type == "ascending":
            # 上昇音
            start_freq = config.start_frequency or 400
            end_freq = config.end_frequency or 800
            frequency = start_freq + (end_freq - start_freq) * (t / duration)
            wave = np.sin(2 * np.pi * frequency * t) * volume
        
        elif config.sound_type == "descending":
            # 下降音
            start_freq = config.start_frequency or 600
            end_freq = config.end_frequency or 200
            frequency = start_freq - (start_freq - end_freq) * (t / duration)
            wave = np.sin(2 * np.pi * frequency * t) * volume
        
        else:  # "beep" or default
            # 基本的なビープ音
            frequency = config.frequency or 600
            wave = np.sin(2 * np.pi * frequency * t) * volume
        
        # 16bit整数に変換
        wave = (wave * 32767).astype(np.int16)
        
        # ステレオ対応
        channels = gen_settings.get('channels', 2)
        if channels == 2:
            sound_array = np.array([wave, wave]).T
        else:
            sound_array = wave
        
        return sound_array.tobytes()

    def _load_sound_file(self, config: SoundConfig) -> Optional[bytes]:
        """ファイルから音声データを読み込み"""
        if not config.file_path or not os.path.exists(config.file_path):
            print(f"[SOUND ERROR] ファイルが見つかりません: {config.file_path}")
            return None
        
        try:
            with open(config.file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"[SOUND ERROR] ファイル読み込みエラー: {e}")
            return None

    def _download_sound(self, config: SoundConfig) -> Optional[bytes]:
        """URLから音声データをダウンロード"""
        if not config.url:
            return None
        
        try:
            print(f"[SOUND] ダウンロード中: {config.url}")
            response = requests.get(config.url, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                print(f"[SOUND ERROR] ダウンロード失敗: {response.status_code}")
                return None
        except Exception as e:
            print(f"[SOUND ERROR] ダウンロードエラー: {e}")
            return None

    def reload_config(self):
        """設定を再読み込み"""
        self.config_manager.reload_config()
        self.sound_cache.clear()
        print("[SOUND] 設定とキャッシュを再読み込みしました")

    def add_custom_command(self, command: str, sound_config: dict):
        """カスタムコマンドを追加"""
        self.config_manager.add_command_config(command, sound_config)
        
        if command in self.sound_cache:
            del self.sound_cache[command]