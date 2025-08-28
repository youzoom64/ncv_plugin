from typing import Dict, Any, Optional
from core.comment_parser import parse_comment
from core.settings_manager import SettingsManager
from core.queue_manager import QueueManager
from core.sound_controller import SoundController
from core.text_converter import TextConverter
import shlex
import numpy as np
import time
import json
import os
import re
import requests
import xml.etree.ElementTree as ET

def get_user_type(user_id: str) -> str:
    print(f"[USER_TYPE] ユーザーID: '{user_id}' -> ", end="")
    
    if user_id is None or user_id == "":
        result = "不明"
    elif user_id.startswith("a:"):
        result = "184"
    elif user_id.startswith("o:"):
        result = "運営"
    elif user_id.isdigit():
        result = "生ID"
    else:
        result = "その他"
    
    print(result)
    return result

class UserInfoManager:
    def __init__(self):
        self.cache = {}  # ユーザー情報キャッシュ
    
    def get_user_icon_url(self, user_id: str) -> str:
        """ユーザーIDからアイコンURLを生成"""
        if len(user_id) <= 4:
            # 4桁以下はディレクトリなし
            return f"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/{user_id}.jpg"
        else:
            # 5桁以上は最後の4桁を残して前の部分をディレクトリに
            prefix = user_id[:-4]
            return f"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/{prefix}/{user_id}.jpg"
    
    def download_user_icon(self, user_id: str, icon_dir: str = "icon") -> bool:
        """ユーザーアイコンをダウンロードして保存"""
        try:
            os.makedirs(icon_dir, exist_ok=True)
            icon_path = os.path.join(icon_dir, f"{user_id}.jpg")
            
            if os.path.exists(icon_path):
                return True
            
            icon_url = self.get_user_icon_url(user_id)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.nicovideo.jp/'
            }
            
            response = requests.get(icon_url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                print(f"[ICON] アイコン保存: {user_id}")
                return True
            
        except Exception as e:
            print(f"[ICON ERROR] {user_id}: {e}")
        return False
    
    def get_user_nickname(self, user_id: str) -> Optional[str]:
        """ユーザーのニックネームを取得"""
        # キャッシュチェック
        if user_id in self.cache:
            return self.cache[user_id]
        
        # 静画API
        nickname = self._try_seiga_api(user_id)
        if nickname:
            self.cache[user_id] = nickname
            return nickname
        
        return None
    
    def _try_seiga_api(self, user_id: str) -> Optional[str]:
        """静画APIでニックネーム取得"""
        try:
            url = f"http://seiga.nicovideo.jp/api/user/info?id={user_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://seiga.nicovideo.jp/',
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                nickname_elem = root.find('.//nickname')
                if nickname_elem is not None:
                    nickname = nickname_elem.text
                    print(f"[API] ニックネーム取得: {user_id} -> {nickname}")
                    return nickname
        except Exception as e:
            print(f"[API ERROR] {user_id}: {e}")
        return None

class WordReplacer:
    def __init__(self, config_path: str = "config/replacements.json"):
        self.config_path = config_path
        self.replacements = {}
        self.skip_long_numbers = True
        self.number_limit = 6
        self.skip_urls = True
        self.load_config()
    
    def load_config(self):
        """設定読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.replacements = config.get("replacements", {})
                self.skip_long_numbers = config.get("skip_long_numbers", True)
                self.number_limit = config.get("number_limit", 6)
                self.skip_urls = config.get("skip_urls", True)
            else:
                self.replacements = {
                    "www": "ワラワラワラ",
                    "草": "くさ"
                }
                self.save_config()
        except:
            self.replacements = {}
    
    def save_config(self):
        """設定保存"""
        config = {
            "replacements": self.replacements,
            "skip_long_numbers": self.skip_long_numbers,
            "number_limit": self.number_limit,
            "skip_urls": self.skip_urls
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def replace_text(self, text: str) -> str:
        """テキスト置換"""
        # 888の連続をパチパチパチに
        text = re.sub(r'8{3,}', lambda m: 'パチ' * len(m.group()), text)
        
        # URL省略
        if self.skip_urls:
            text = re.sub(r'https?://[^\s]+', 'URL省略', text)
        
        # 長い数字を省略
        if self.skip_long_numbers:
            pattern = fr'\d{{{self.number_limit},}}'
            text = re.sub(pattern, '数字省略', text)
        
        # 通常の置換
        for original, replacement in self.replacements.items():
            text = text.replace(original, replacement)
        
        return text

class CommentProcessor:
    def __init__(self, settings_manager: SettingsManager, queue_manager: QueueManager, sound_controller: SoundController):
        self.settings_manager = settings_manager
        self.queue_manager = queue_manager
        self.sound_controller = sound_controller
        
        # VoiceControllerインスタンスを直接保持
        from core.voice_controller import VoiceController
        self.voice_controller = VoiceController()
        
        # 機能追加
        self.word_replacer = WordReplacer()
        self.text_converter = TextConverter()
        self.user_info_manager = UserInfoManager()
    
    def process_comment(self, data: Dict[str, Any]) -> bool:
        """コメントを処理（運営コメント対応版）"""
        comment = data.get("comment", "")
        user_id = data.get("user_id", "")
        mail = data.get("mail", "")
        comment_no = data.get("comment_no", "")
        premium = data.get("premium", 0)
        date = data.get("date", "")
        timestamp = data.get("timestamp", "")
        
        # 全コメントをログ出力（デバッグ用）
        print(f"[ALL_COMMENTS] '{comment}' from {user_id}")
        
        # 運営コメントの詳細ログ
        if user_id and user_id.startswith("o:"):
            print(f"[OPERATOR] 運営コメント確認: {data}")
        
        if not comment.strip():
            return False
        
        self._log_comment_info(comment, user_id, mail, comment_no, premium, date, timestamp)
        
        # コメント解析
        parsed = parse_comment(comment)
        print(f"[PARSER] 解析結果: {parsed}")
        
        # 運営コマンド処理
        if parsed.get("is_system_command", False):
            print(f"[SYSTEM] 運営コマンド処理開始: {parsed['command_type']}")
            return self._handle_system_command(parsed, user_id)
        
        # 通常コメント処理
        return self._handle_normal_comment(user_id, mail, parsed)
    
    def _log_comment_info(self, comment: str, user_id: str, mail: str, 
                        comment_no: str, premium: int, date: str, timestamp: str):
        """コメント情報をログ出力（運営コメント対応版）"""
        user_type = get_user_type(user_id)
        premium_text = "プレミアム" if premium == 1 else "一般"
        
        print(f"📝 コメント: {comment}")
        print(f"👤 ユーザー: {user_id} ({user_type})")
        print(f"💎 アカウント: {premium_text}")
        print(f"📧 メール欄: {mail}")
        print(f"🔢 コメント番号: {comment_no if comment_no else '運営コメント(番号なし)'}")
        print(f"⏰ 日時: {date}")
        print(f"🕒 受信時刻: {timestamp}")

    def _handle_system_command(self, parsed: Dict[str, Any], user_id: str) -> bool:
        """運営コマンド処理（順序保持 + 同時再生）"""
        command_type = parsed["command_type"]
        full_text = parsed["text"]
        
        settings = self._load_system_settings()
        
        print(f"🎵 運営コマンド検出: /{command_type}")
        print(f"📝 内容: {full_text}")
        
        # コマンド部分を除去した文章を抽出
        clean_text = full_text[len(f"/{command_type}"):].strip()

        # コマンド別テンプレ整形（設定テンプレを優先）
        formatted_text = self._format_system_tts(command_type, clean_text, settings)
        
        if settings.get("sound_enabled", True):
            if formatted_text and len(formatted_text) > 1:
                # 効果音+音声を合成してキューに追加
                self._queue_combined_audio(command_type, formatted_text, settings, user_id)
            else:
                # 効果音のみをキューに追加
                self._queue_sound_only(command_type, settings)
        else:
            # 音声のみをキューに追加
            if formatted_text and len(formatted_text) > 1:
                voice_id = self._get_user_voice_id(user_id)
                self.queue_manager.add_to_synthesis_queue(formatted_text, voice_id)
        
        return True

    def _queue_combined_audio(self, command_type: str, text: str, settings: dict, user_id: str):
        """効果音+音声を合成してキューに追加"""
        try:
            # 1. 音声合成
            voice_id = self._get_user_voice_id(user_id)
            voice_data = self.voice_controller.synthesize_only(text, voice_id, 1.0)
            
            # 2. 効果音取得
            sound_data = self._get_sound_data(command_type, settings)
            
            # 3. 合成（現在は音声のみ、将来的に効果音とミックス可能）
            if voice_data:
                self.queue_manager.add_to_playback_queue(f"[運営]{command_type}: {text}", voice_data)
                
                # 効果音を別途即座に再生（簡易実装）
                if sound_data:
                    self._play_sound_immediately(sound_data)
                    
        except Exception as e:
            print(f"[QUEUE ERROR] 合成エラー: {e}")

    def _queue_sound_only(self, command_type: str, settings: dict):
        """効果音のみをキューに追加"""
        sound_data = self._get_sound_data(command_type, settings)
        if sound_data:
            self.queue_manager.add_to_playback_queue(f"[効果音]{command_type}", sound_data)

    def _get_sound_data(self, command_type: str, settings: dict) -> Optional[bytes]:
        """効果音データを取得"""
        sound_files = settings.get("sound_files", {})
        # エイリアス（例: nicoad -> ad）
        alias_map = settings.get("sound_alias", {})
        resolved_command = alias_map.get(command_type, command_type)
        
        if resolved_command in sound_files:
            # カスタムファイル
            try:
                with open(sound_files[resolved_command], 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"[SOUND ERROR] ファイル読み込みエラー: {e}")
                return None
        else:
            # デフォルト効果音
            return self.sound_controller.get_command_sound(resolved_command)

    def _play_sound_immediately(self, sound_data: bytes):
        """効果音を即座に再生（非ブロッキング）"""
        def play():
            try:
                import pygame
                import io
                audio_io = io.BytesIO(sound_data)
                sound = pygame.mixer.Sound(audio_io)
                pygame.mixer.Channel(6).play(sound)
            except Exception as e:
                print(f"[SOUND ERROR] 即座再生エラー: {e}")
        
        import threading
        threading.Thread(target=play, daemon=True).start()

    def _get_user_voice_id(self, user_id: str) -> int:
        """ユーザーの音声IDを取得"""
        if user_id.startswith("o:"):
            # 運営の場合は設定ファイルから取得
            settings = self._load_system_settings()
            voice_id = settings.get("operator_voice_id", 2)
            print(f"[DEBUG] 運営音声ID: {voice_id}")
            return voice_id
        else:
            # 通常ユーザー
            final_settings = self.settings_manager.resolve_user_settings(user_id, {
                "name": None, "voice": None, "skin": None, "font": None, "sound": None
            })
            voice_id = final_settings.get("voice", 2)
            print(f"[DEBUG] {user_id} の音声ID: {voice_id}")
            return voice_id
    
    def _load_system_settings(self) -> dict:
        """運営設定を読み込み"""
        try:
            with open("config/system_commands.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"sound_enabled": True, "sound_files": {}}

    def _format_system_tts(self, command_type: str, clean_text: str, settings: dict) -> str:
        """コマンド別に読み上げ文を整形（テンプレ適用）"""
        try:
            templates = settings.get("templates", {})
            if command_type == "gift":
                # /gift nicolive_audition_orange 126050768 "ゲスト" 15 "" "応援 メガホン オレンジ "
                # 想定: parts = [service, id, name, point, empty, gift with spaces]
                display_name = None
                gift_name = None
                point = None
                try:
                    parts = shlex.split(clean_text)
                except Exception:
                    parts = []
                # shlex.split は引用符を除去する
                if parts:
                    # name
                    if len(parts) >= 3 and parts[2]:
                        display_name = parts[2].strip()
                    # point (数字)
                    if len(parts) >= 4 and re.fullmatch(r"\d+", parts[3] or ""):
                        point = parts[3]
                    # gift 名（最後のトークンを優先）
                    if len(parts) >= 6 and parts[5]:
                        gift_name = parts[5]
                # 補助: 引用抽出
                if display_name is None or gift_name is None or point is None:
                    dq = re.findall(r'"([^"]+)"', clean_text)
                    if display_name is None and dq:
                        display_name = dq[0].strip()
                    if gift_name is None and len(dq) >= 2:
                        gift_name = dq[-1].strip()
                    if point is None:
                        mpt = re.search(r'\s(\d{1,6})(?:\s|\"|$)', clean_text)
                        if mpt:
                            point = mpt.group(1)
                # フォールバック
                if not display_name:
                    display_name = "ゲスト"
                if not gift_name:
                    # 日本語スペースや全角空白を統一
                    normalized = re.sub(r"\s+", " ", clean_text).strip()
                    tokens = normalized.split(" ")
                    if tokens:
                        gift_name = tokens[-1].strip('"')
                if not point:
                    point = ""
                # 見栄え調整: ギフト名の空白除去
                gift_name = re.sub(r"\s+", "", gift_name)
                template = templates.get("gift", "{name}さんが{point}ポイント{gift}をギフトしました")
                return template.format(name=display_name, point=point, gift=gift_name)
            elif command_type == "nicoad":
                # /nicoad {json}
                total = None
                name = None
                point = None
                # JSON部分を抽出
                json_str_match = re.search(r'(\{.*\})', clean_text)
                if json_str_match:
                    json_str = json_str_match.group(1)
                    try:
                        obj = json.loads(json_str)
                        total = obj.get("totalAdPoint")
                        message = obj.get("message", "")
                        # メッセージから「◯◯さんがNNNpt」抽出
                        msg = re.sub(r'【[^】]*】', '', message)
                        m = re.search(r'(.+?)さんが\s*(\d+)\s*pt', msg)
                        if m:
                            name = m.group(1).strip()
                            point = m.group(2)
                    except Exception as e:
                        print(f"[PARSER] nicoad JSON解析エラー: {e}")
                if not name:
                    name = "ゲスト"
                if not point:
                    # メッセージ中の数値を最後の候補として
                    m2 = re.search(r'(\d+)\s*pt', clean_text)
                    if m2:
                        point = m2.group(1)
                if not total:
                    # 合計値フォールバック
                    m3 = re.search(r'"totalAdPoint"\s*:\s*(\d+)', clean_text)
                    if m3:
                        total = int(m3.group(1))
                template = templates.get("nicoad", "合計{total}ポイント　{name}さんが{point}ポイント広告しました")
                try:
                    return template.format(total=total if total is not None else 0, name=name, point=point if point is not None else 0)
                except Exception:
                    return f"合計{total if total is not None else 0}ポイント　{name}さんが{point if point is not None else 0}ポイント広告しました"
            else:
                # その他のコマンドは本文をそのまま（ただし技術的トークンをなるべく省く場合はここで拡張）
                return clean_text
        except Exception as e:
            print(f"[FORMAT ERROR] /{command_type}: {e}")
            return clean_text

    def _handle_normal_comment(self, user_id: str, mail: str, parsed: Dict[str, Any]) -> bool:
        """通常コメントを処理"""
        text_body = parsed["text"]
        
        # 置換処理を追加
        original_text = text_body
        text_body = self.word_replacer.replace_text(text_body)
        if original_text != text_body:
            print(f"[REPLACE] '{original_text}' → '{text_body}'")

        # 文字変換処理を追加
        text_body = self.text_converter.convert_text(text_body)
        
        # 生IDの場合はユーザー情報を自動取得・保存
        print(f"[DEBUG] ユーザーID: '{user_id}', isdigit: {user_id.isdigit()}")
        if user_id.isdigit():
            print(f"[DEBUG] 生IDと判定、_auto_save_user_info呼び出し: {user_id}")
            self._auto_save_user_info(user_id)
        
        # ユーザー設定を解決
        final_settings = self.settings_manager.resolve_user_settings(user_id, parsed)
        
        # 新しい設定があれば保存
        current_settings = self.settings_manager.user_manager.get_user_settings(user_id, {
            "name": None, "voice": 2, "skin": None, "font": None, "sound": None
        })
        
        settings_saved = self.settings_manager.save_new_settings(user_id, parsed, current_settings)
        if not settings_saved:
            print(f"🎯 保存済み設定使用: 音声ID={final_settings['voice']}")
            if final_settings["name"]:
                print(f"     名前: {final_settings['name']}")
        
        # 最終設定表示
        settings_info = self.settings_manager.format_settings_info(final_settings)
        print(f"🎵 最終設定: {settings_info}")
        
        # 読み上げ対象外チェック
        if self._should_skip_voice(mail, text_body):
            return False
        
        # 音声合成キューに追加
        self.queue_manager.add_to_synthesis_queue(text_body, final_settings["voice"])
        
        return True
        
    def _auto_save_user_info(self, user_id: str):
        """生IDの場合、ユーザー情報を自動取得・保存"""
        try:
            # 既に名前が保存されているかチェック
            current_settings = self.settings_manager.user_manager.get_user_settings(user_id, {})
            if not (current_settings and current_settings.get("name")):
                # ニックネーム取得
                nickname = self.user_info_manager.get_user_nickname(user_id)
                if nickname:
                    # 名前を自動保存
                    success = self.settings_manager.user_manager.save_user_settings(
                        user_id=user_id,
                        name=nickname
                    )
                    if success:
                        print(f"[AUTO_SAVE] {user_id} の名前を自動保存: {nickname}")
            
            # アイコンファイルが存在しない場合のみダウンロード
            icon_path = f"icon/{user_id}.jpg"
            if not os.path.exists(icon_path):
                print(f"[AUTO_SAVE] アイコンなし、ダウンロード開始: {user_id}")
                success = self.user_info_manager.download_user_icon(user_id)
                if success:
                    print(f"[AUTO_SAVE] アイコンダウンロード成功: {user_id}")
                else:
                    print(f"[AUTO_SAVE] アイコンダウンロード失敗: {user_id}")
            else:
                print(f"[AUTO_SAVE] アイコン既存: {user_id}")
            
        except Exception as e:
            print(f"[AUTO_SAVE ERROR] {user_id}: {e}")
    
    def _should_skip_voice(self, mail: str, text_body: str) -> bool:
        """読み上げをスキップするかどうか判定"""
        if mail and any(skip_word in mail.lower() for skip_word in ["184", "sage", "ngs"]):
            print(f"[SKIP] メール欄設定により読み上げスキップ: {mail}")
            return True
        
        if not text_body.strip() or len(text_body.strip()) < 2:
            print(f"[SKIP] テキストが短すぎる: '{text_body}'")
            return True
        
        return False