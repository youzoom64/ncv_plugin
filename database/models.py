from dataclasses import dataclass
from typing import Optional
import sqlite3
from datetime import datetime

@dataclass
class UserSettings:
    user_id: str
    name: Optional[str] = None
    voice_id: Optional[int] = None
    skin_id: Optional[int] = None
    font_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserSettingsDB:
    def __init__(self, db_path: str = "database/user_settings.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """データベース・テーブル初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    voice_id INTEGER,
                    skin_id INTEGER,
                    font_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 更新日時を自動更新するトリガー
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS update_timestamp 
                AFTER UPDATE ON user_settings
                BEGIN
                    UPDATE user_settings 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = NEW.user_id;
                END
            """)
    
    def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """ユーザー設定取得"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM user_settings WHERE user_id = ?", 
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return UserSettings(**dict(row))
            return None
    
    def save_user_settings(self, user_id: str, name: str = None, 
                          voice_id: int = None, skin_id: int = None, 
                          font_id: int = None) -> bool:
        """ユーザー設定保存・更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_settings 
                    (user_id, name, voice_id, skin_id, font_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, name, voice_id, skin_id, font_id))
                return True
        except Exception as e:
            print(f"[DB ERROR] 設定保存失敗: {e}")
            return False
    
    def get_all_users(self) -> list[UserSettings]:
        """全ユーザー設定取得"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM user_settings ORDER BY updated_at DESC")
            return [UserSettings(**dict(row)) for row in cursor.fetchall()]
    
    def delete_user(self, user_id: str) -> bool:
        """ユーザー設定削除"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
                return True
        except Exception as e:
            print(f"[DB ERROR] ユーザー削除失敗: {e}")
            return False