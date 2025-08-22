from typing import Dict, Any, Optional
from core.user_manager import UserManager

class SettingsManager:
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
    
    def resolve_user_settings(self, user_id: str, parsed_settings: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザー設定を解決（解析結果 + DB設定 → 最終設定）"""
        # デフォルト設定
        default_settings = {
            "name": None,
            "voice": 2,  # デフォルト音声ID
            "skin": None,
            "font": None,
            "sound": None
        }
        
        # DBからユーザー設定取得
        user_settings = self.user_manager.get_user_settings(user_id, default_settings)
        
        # 解析結果とユーザー設定をマージして最終設定を決定
        final_settings = {
            "voice": parsed_settings["voice"] if parsed_settings["voice"] is not None else user_settings["voice"],
            "name": parsed_settings["name"] if parsed_settings["name"] is not None else user_settings["name"],
            "skin": parsed_settings["skin"] if parsed_settings["skin"] is not None else user_settings["skin"],
            "font": parsed_settings["font"] if parsed_settings["font"] is not None else user_settings["font"],
            "sound": parsed_settings["sound"] if parsed_settings["sound"] is not None else user_settings.get("sound")
        }
        
        return final_settings
    
    def save_new_settings(self, user_id: str, parsed_settings: Dict[str, Any], current_settings: Dict[str, Any]) -> bool:
        """新しい設定がある場合は保存"""
        if not any([parsed_settings["name"], parsed_settings["voice"], 
                   parsed_settings["skin"], parsed_settings["font"], parsed_settings["sound"]]):
            return False  # 新しい設定なし
        
        print(f"🎯 新しい設定検出: 名前={parsed_settings['name']}, 音声ID={parsed_settings['voice']}, "
              f"スキン={parsed_settings['skin']}, フォント={parsed_settings['font']}, サウンド={parsed_settings['sound']}")
        
        # 現在のDB設定を取得して上書き
        save_name = parsed_settings["name"] if parsed_settings["name"] is not None else current_settings["name"]
        save_voice = parsed_settings["voice"] if parsed_settings["voice"] is not None else current_settings["voice"]
        save_skin = parsed_settings["skin"] if parsed_settings["skin"] is not None else current_settings["skin"]
        save_font = parsed_settings["font"] if parsed_settings["font"] is not None else current_settings["font"]
        save_sound = parsed_settings["sound"] if parsed_settings["sound"] is not None else current_settings.get("sound")
        
        # DB保存実行
        success = self.user_manager.save_user_settings(
            user_id=user_id,
            name=save_name,
            voice=save_voice,
            skin=save_skin,
            font=save_font,
            sound=save_sound
        )
        
        if success:
            print(f"💾 {user_id} の設定を更新しました")
        
        return success
    
    def format_settings_info(self, final_settings: Dict[str, Any]) -> str:
        """設定情報を表示用フォーマットに変換"""
        settings_info = []
        if final_settings["name"]:
            settings_info.append(f"名前={final_settings['name']}")
        settings_info.append(f"音声ID={final_settings['voice']}")
        if final_settings["skin"]:
            settings_info.append(f"スキン={final_settings['skin']}")
        if final_settings["font"]:
            settings_info.append(f"フォント={final_settings['font']}")
        if final_settings["sound"]:
            settings_info.append(f"サウンド={final_settings['sound']}")
        
        return ', '.join(settings_info)