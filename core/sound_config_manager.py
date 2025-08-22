import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SoundConfig:
    type: str  # generated, file, url
    sound_type: Optional[str] = None
    frequency: Optional[int] = None
    frequencies: Optional[list] = None
    start_frequency: Optional[int] = None
    end_frequency: Optional[int] = None
    duration: float = 0.3
    volume: float = 0.3
    file_path: Optional[str] = None
    url: Optional[str] = None
    description: str = ""

class SoundConfigManager:
    def __init__(self, config_path: str = "config/sound_config.yaml"):
        self.config_path = config_path
        self.config_data = {}
        self.sound_configs = {}
        self.global_settings = {}
        self.generation_settings = {}
        
        self._load_config()
        self._parse_config()
    
    def _load_config(self):
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config_data = yaml.safe_load(file)
                print(f"[CONFIG] 設定ファイル読み込み完了: {self.config_path}")
            else:
                print(f"[CONFIG] 設定ファイルが見つかりません: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            print(f"[CONFIG ERROR] 設定ファイル読み込みエラー: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """デフォルト設定を作成"""
        self.config_data = {
            'sound_settings': {
                'commands': {
                    'info': {
                        'type': 'generated',
                        'sound_type': 'beep',
                        'frequency': 800,
                        'duration': 0.3,
                        'volume': 0.3,
                        'description': 'インフォメーション音'
                    },
                    'gift': {
                        'type': 'generated',
                        'sound_type': 'chime',
                        'frequencies': [1000, 1200, 1500],
                        'duration': 0.5,
                        'volume': 0.2,
                        'description': 'ギフト音'
                    },
                    'default': {
                        'type': 'generated',
                        'sound_type': 'beep',
                        'frequency': 600,
                        'duration': 0.2,
                        'volume': 0.2,
                        'description': 'デフォルト音'
                    }
                }
            },
            'global_settings': {
                'master_volume': 1.0,
                'cache_sounds': True
            },
            'generation_settings': {
                'sample_rate': 24000,
                'bit_depth': 16,
                'channels': 2
            }
        }
        
        # デフォルト設定ファイルを保存
        self._save_config()
    
    def _save_config(self):
        """設定ファイルを保存"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config_data, file, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            print(f"[CONFIG] 設定ファイル保存完了: {self.config_path}")
        except Exception as e:
            print(f"[CONFIG ERROR] 設定ファイル保存エラー: {e}")
    
    def _parse_config(self):
        """設定データを解析"""
        # サウンド設定
        sound_settings = self.config_data.get('sound_settings', {})
        commands = sound_settings.get('commands', {})
        
        for command, config in commands.items():
            self.sound_configs[command] = SoundConfig(
                type=config.get('type', 'generated'),
                sound_type=config.get('sound_type'),
                frequency=config.get('frequency'),
                frequencies=config.get('frequencies'),
                start_frequency=config.get('start_frequency'),
                end_frequency=config.get('end_frequency'),
                duration=config.get('duration', 0.3),
                volume=config.get('volume', 0.3),
                file_path=config.get('file_path'),
                url=config.get('url'),
                description=config.get('description', '')
            )
        
        # グローバル設定
        self.global_settings = self.config_data.get('global_settings', {})
        
        # 生成設定
        self.generation_settings = self.config_data.get('generation_settings', {})
        
        print(f"[CONFIG] {len(self.sound_configs)}個のサウンド設定を読み込みました")
        for command, config in self.sound_configs.items():
            print(f"  - {command}: {config.description}")
    
    def get_sound_config(self, command: str) -> SoundConfig:
        """コマンドに対応するサウンド設定を取得"""
        config = self.sound_configs.get(command)
        if not config:
            config = self.sound_configs.get('default')
        
        if not config:
            # フォールバック設定
            config = SoundConfig(
                type='generated',
                sound_type='beep',
                frequency=600,
                duration=0.2,
                volume=0.2,
                description='フォールバック音'
            )
        
        return config
    
    def get_master_volume(self) -> float:
        """マスター音量を取得"""
        return self.global_settings.get('master_volume', 1.0)
    
    def get_generation_settings(self) -> Dict[str, Any]:
        """音声生成設定を取得"""
        return self.generation_settings
    
    def reload_config(self):
        """設定を再読み込み"""
        print("[CONFIG] 設定ファイルを再読み込みします...")
        self._load_config()
        self._parse_config()
    
    def list_commands(self) -> Dict[str, str]:
        """利用可能なコマンドとその説明を取得"""
        return {command: config.description for command, config in self.sound_configs.items()}
    
    def add_command_config(self, command: str, config: Dict[str, Any]):
        """新しいコマンド設定を追加"""
        if 'sound_settings' not in self.config_data:
            self.config_data['sound_settings'] = {'commands': {}}
        
        self.config_data['sound_settings']['commands'][command] = config
        self._save_config()
        self._parse_config()
        print(f"[CONFIG] 新しいコマンド設定を追加: {command}")