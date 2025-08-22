from typing import Dict, Any
from database.models import UserSettingsDB, UserSettings

class UserManager:
    def __init__(self):
        self.db = UserSettingsDB()
        print("[INIT] UserManager initialized with database")

    def get_user_settings(self, user_id: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザー設定取得（デフォルト値付き）"""
        if not user_id or user_id == "":
            return default
            
        settings = self.db.get_user_settings(user_id)
        if settings:
            result = default.copy()
            if settings.name is not None:
                result["name"] = settings.name
            if settings.voice_id is not None:
                result["voice"] = settings.voice_id
            if settings.skin_id is not None:
                result["skin"] = settings.skin_id
            if settings.font_id is not None:
                result["font"] = settings.font_id
            if hasattr(settings, 'sound_id') and settings.sound_id is not None:
                result["sound"] = settings.sound_id
            
            print(f"[DB] 🔍 保存済み設定使用: {user_id}")
            if settings.name:
                print(f"     名前: {settings.name}")
            if settings.voice_id:
                print(f"     音声ID: {settings.voice_id}")
            return result
        else:
            print(f"[DB] 📝 新規ユーザー: {user_id} -> デフォルト設定使用")
            return default

    def save_user_settings(self, user_id: str, name: str = None, 
                          skin: int = None, font: int = None, voice: int = None,
                          sound: int = None):
        """ユーザー設定保存（soundパラメータ追加）"""
        if not user_id or user_id == "":
            print("[DB] ⚠️  無効なユーザーID: 保存スキップ")
            return False
            
        success = self.db.save_user_settings(
            user_id=user_id,
            name=name,
            voice_id=voice,
            skin_id=skin,
            font_id=font,
            sound_id=sound
        )
        
        if success:
            print(f"[DB] 💾 設定保存成功: {user_id}")
            if name:
                print(f"     名前: {name}")
            if voice:
                print(f"     音声ID: {voice}")
            if skin:
                print(f"     スキンID: {skin}")
            if font:
                print(f"     フォントID: {font}")
            if sound:
                print(f"     サウンドID: {sound}")
        else:
            print(f"[DB] ❌ 設定保存失敗: {user_id}")
        
        return success
    
    def get_user_stats(self) -> Dict[str, Any]:
        """ユーザー統計情報"""
        users = self.db.get_all_users()
        return {
            "total_users": len(users),
            "recent_users": [u.user_id for u in users[:5]]
        }