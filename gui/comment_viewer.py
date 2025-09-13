# gui/comment_viewer.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
import websockets
import json
from typing import Dict, Any, Optional

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
  sys.path.insert(0, parent_dir)

from core.user_manager import UserManager
from core.voice_controller import VoiceController
from handlers.websocket_handler import WebSocketHandler

class CommentViewerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎤 ニコ生コメントビューア & 音声設定")
        self.root.geometry("1400x900")
        
        # コアコンポーネント
        self.user_manager = UserManager()
        self.voice_controller = VoiceController()
        self.websocket_handler = None
        
        # データ管理
        self.comments_data = []
        self.users_data = {}
        self.selected_user_id = None
        
        # GUI初期化
        self.setup_gui()
        self.start_websocket_connection()
        
    def setup_gui(self):
        """GUI画面を構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左側: コメント一覧
        self.setup_comment_area(main_frame)
        
        # 右側: ユーザー設定
        self.setup_user_settings_area(main_frame)
        
        # 下部: ステータス
        self.setup_status_area(main_frame)
        
        # レスポンシブ対応
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
    
    def setup_comment_area(self, parent):
        """コメント一覧エリア"""
        # コメント一覧フレーム
        comment_frame = ttk.LabelFrame(parent, text="💬 コメント一覧", padding="5")
        comment_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # コメント一覧ツリービュー
        columns = ("時刻", "ユーザー", "コメント", "設定")
        self.comment_tree = ttk.Treeview(comment_frame, columns=columns, show="headings", height=25)
        
        # カラム設定
        self.comment_tree.heading("時刻", text="時刻")
        self.comment_tree.heading("ユーザー", text="ユーザー")
        self.comment_tree.heading("コメント", text="コメント")
        self.comment_tree.heading("設定", text="設定")
        
        self.comment_tree.column("時刻", width=80)
        self.comment_tree.column("ユーザー", width=150)
        self.comment_tree.column("コメント", width=300)
        self.comment_tree.column("設定", width=200)
        
        # スクロールバー
        comment_scroll = ttk.Scrollbar(comment_frame, orient=tk.VERTICAL, command=self.comment_tree.yview)
        self.comment_tree.configure(yscrollcommand=comment_scroll.set)
        
        # 配置
        self.comment_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        comment_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # イベントバインド
        self.comment_tree.bind("<<TreeviewSelect>>", self.on_comment_select)
        
        comment_frame.columnconfigure(0, weight=1)
        comment_frame.rowconfigure(0, weight=1)
    
    def setup_user_settings_area(self, parent):
        """ユーザー設定エリア"""
        # 設定フレーム
        settings_frame = ttk.LabelFrame(parent, text="⚙️ ユーザー設定", padding="5")
        settings_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # ユーザー情報表示
        user_info_frame = ttk.LabelFrame(settings_frame, text="👤 選択中のユーザー", padding="5")
        user_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.user_id_label = ttk.Label(user_info_frame, text="ユーザーID: 未選択", font=("", 10, "bold"))
        self.user_id_label.grid(row=0, column=0, sticky=tk.W)
        
        self.user_type_label = ttk.Label(user_info_frame, text="種別: -")
        self.user_type_label.grid(row=1, column=0, sticky=tk.W)
        
        # 設定項目
        # 名前設定
        ttk.Label(settings_frame, text="表示名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(settings_frame, textvariable=self.name_var, width=25)
        self.name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # 音声ID設定
        ttk.Label(settings_frame, text="音声:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # 音声選択用フレーム
        voice_frame = ttk.Frame(settings_frame)
        voice_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, width=30, height=30, state="readonly")
        self.voice_combo.grid(row=0, column=0, sticky=tk.W)
        
        # ボイス名表示ラベル
        self.voice_name_label = ttk.Label(voice_frame, text="", foreground="blue", font=("", 9))
        self.voice_name_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 音声選択イベント
        self.voice_combo.bind("<<ComboboxSelected>>", self.on_voice_changed)
        
        voice_frame.columnconfigure(1, weight=1)
        
        # スキンID設定
        ttk.Label(settings_frame, text="スキンID:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.skin_var = tk.StringVar()
        self.skin_entry = ttk.Entry(settings_frame, textvariable=self.skin_var, width=25)
        self.skin_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # フォントID設定
        ttk.Label(settings_frame, text="フォントID:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.font_var = tk.StringVar()
        self.font_entry = ttk.Entry(settings_frame, textvariable=self.font_var, width=25)
        self.font_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # ボタン
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        self.save_button = ttk.Button(button_frame, text="💾 設定保存", command=self.save_user_settings)
        self.save_button.grid(row=0, column=0, padx=(0, 10))
        
        self.test_button = ttk.Button(button_frame, text="🎤 テスト再生", command=self.test_voice)
        self.test_button.grid(row=0, column=1, padx=(10, 0))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ 設定クリア", command=self.clear_settings)
        self.clear_button.grid(row=0, column=2, padx=(10, 0))
        
        # 運営コマンド設定フレーム
        system_frame = ttk.LabelFrame(settings_frame, text="🏢 運営コマンド設定", padding="5")
        system_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 10))

        # 運営コマンド効果音変換設定
        self.system_sound_enabled_var = tk.BooleanVar(value=True)
        system_sound_checkbox = ttk.Checkbutton(system_frame, text="運営コマンドを効果音に変換", variable=self.system_sound_enabled_var)
        system_sound_checkbox.grid(row=0, column=0, sticky=tk.W, pady=5)

        # 運営音声設定追加
        operator_voice_frame = ttk.LabelFrame(system_frame, text="🎤 運営音声設定", padding="5")
        operator_voice_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))

        ttk.Label(operator_voice_frame, text="運営音声:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.operator_voice_var = tk.StringVar()
        self.operator_voice_combo = ttk.Combobox(operator_voice_frame, textvariable=self.operator_voice_var, 
                                                width=30, height=30, state="readonly")
        self.operator_voice_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        # 運営ボイス名表示
        self.operator_voice_name_label = ttk.Label(operator_voice_frame, text="", foreground="blue", font=("", 9))
        self.operator_voice_name_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))

        # 運営音声選択イベント
        self.operator_voice_combo.bind("<<ComboboxSelected>>", self.on_operator_voice_changed)

        operator_voice_frame.columnconfigure(1, weight=1)

        # 効果音ファイル設定エリア
        sound_files_frame = ttk.LabelFrame(system_frame, text="🎵 効果音ファイル設定", padding="5")
        sound_files_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        # 効果音ファイル管理
        self.sound_file_vars = {}
        self.sound_file_labels = {}

        # 設定可能なコマンド
        commands = ["info 10", "gift", "ad"]

        for i, cmd in enumerate(commands):
            # コマンド名ラベル
            ttk.Label(sound_files_frame, text=f"/{cmd}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            
            # ファイルパス表示
            self.sound_file_vars[cmd] = tk.StringVar()
            self.sound_file_labels[cmd] = ttk.Label(sound_files_frame, textvariable=self.sound_file_vars[cmd], 
                                                    foreground="blue", width=30)
            self.sound_file_labels[cmd].grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
            
            # ファイル選択ボタン
            select_btn = ttk.Button(sound_files_frame, text="📁", width=3,
                                    command=lambda c=cmd: self.select_sound_file(c))
            select_btn.grid(row=i, column=2, pady=2, padx=(5, 0))
            
            # 再生テストボタン
            play_btn = ttk.Button(sound_files_frame, text="▶️", width=3,
                                    command=lambda c=cmd: self.test_sound_file(c))
            play_btn.grid(row=i, column=3, pady=2, padx=(5, 0))

        # 設定保存ボタン
        save_system_btn = ttk.Button(system_frame, text="💾 運営設定保存", command=self.save_system_settings)
        save_system_btn.grid(row=3, column=0, columnspan=2, pady=10)

        sound_files_frame.columnconfigure(1, weight=1)
        system_frame.columnconfigure(1, weight=1)

        # ユーザー一覧
        users_list_frame = ttk.LabelFrame(settings_frame, text="👥 全ユーザー一覧", padding="5")
        users_list_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        # ユーザー一覧ツリービュー
        user_columns = ("ユーザーID", "名前", "音声", "種別")
        self.user_tree = ttk.Treeview(users_list_frame, columns=user_columns, show="headings", height=8)

        self.user_tree.heading("ユーザーID", text="ユーザーID")
        self.user_tree.heading("名前", text="名前")
        self.user_tree.heading("音声", text="音声")
        self.user_tree.heading("種別", text="種別")

        self.user_tree.column("ユーザーID", width=120)
        self.user_tree.column("名前", width=100)
        self.user_tree.column("音声", width=120)
        self.user_tree.column("種別", width=60)

        user_scroll = ttk.Scrollbar(users_list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=user_scroll.set)

        self.user_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        user_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # イベントバインド
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)

        # 利用可能な音声IDとボイス名を設定
        self.update_voice_list()

        # レスポンシブ対応
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.rowconfigure(7, weight=1)
        users_list_frame.columnconfigure(0, weight=1)
        users_list_frame.rowconfigure(0, weight=1)

    def on_operator_voice_changed(self, event=None):
        """運営音声選択変更時の処理"""
        try:
            selected_text = self.operator_voice_var.get()
            selected_id = int(selected_text.split(':')[0])
            voice_name = self.voice_controller.get_voice_name(selected_id)
            self.operator_voice_name_label.config(text=voice_name)
        except (ValueError, TypeError, IndexError):
            self.operator_voice_name_label.config(text="")

    def select_sound_file(self, command: str):
        """効果音ファイルを選択"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title=f"/{command} 用の効果音ファイルを選択",
            filetypes=[
                ("音声ファイル", "*.wav *.mp3 *.ogg"),
                ("WAVファイル", "*.wav"),
                ("MP3ファイル", "*.mp3"),
                ("OGGファイル", "*.ogg"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            # 相対パスに変換（プロジェクトフォルダ基準）
            import os
            try:
                rel_path = os.path.relpath(file_path)
                self.sound_file_vars[command].set(rel_path)
                print(f"[SOUND] /{command} に効果音ファイル設定: {rel_path}")
            except:
                self.sound_file_vars[command].set(file_path)

    def test_sound_file(self, command: str):
        """効果音ファイルのテスト再生"""
        file_path = self.sound_file_vars[command].get()
        if not file_path:
            messagebox.showwarning("警告", f"/{command} の効果音ファイルが設定されていません")
            return
        
        def test_play():
            try:
                import pygame
                pygame.mixer.init()
                sound = pygame.mixer.Sound(file_path)
                sound.play()
                self.root.after(0, lambda: self.update_status(f"🎵 /{command} 効果音テスト完了", "green"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"❌ 効果音エラー: {str(e)}", "red"))
        
        threading.Thread(target=test_play, daemon=True).start()
        self.update_status(f"🎵 /{command} 効果音テスト中...", "blue")

    def save_system_settings(self):
        """運営設定を保存（音声ID追加版）"""
        try:
            # configディレクトリが存在しない場合は作成
            import os
            os.makedirs("config", exist_ok=True)
            
            # 効果音ファイル設定
            sound_files = {}
            for cmd, var in self.sound_file_vars.items():
                if var.get():
                    sound_files[cmd] = var.get()
            
            # 運営音声ID取得
            operator_voice_id = 2  # デフォルト
            if hasattr(self, 'operator_voice_var') and self.operator_voice_var.get():
                try:
                    operator_voice_id = int(self.operator_voice_var.get().split(':')[0])
                except:
                    pass
            
            # 設定をJSONファイルに保存
            settings = {
                "sound_enabled": self.system_sound_enabled_var.get(),
                "operator_voice_id": operator_voice_id,
                "sound_files": sound_files
            }
            
            import json
            with open("config/system_commands.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "運営コマンド設定を保存しました")
            print(f"[SYSTEM] 設定保存: {settings}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存に失敗しました: {e}")

    def load_system_settings(self):
        """運営設定を読み込み（音声ID対応版）"""
        try:
            import json
            with open("config/system_commands.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # GUIに設定を反映
            self.system_sound_enabled_var.set(settings.get("sound_enabled", True))
            
            # 運営音声設定を反映
            operator_voice_id = settings.get("operator_voice_id", 2)
            if hasattr(self, 'operator_voice_combo'):
                voice_name = self.voice_controller.get_voice_name(operator_voice_id)
                voice_display = f"{operator_voice_id}: {voice_name}"
                self.operator_voice_var.set(voice_display)
            
            # 効果音ファイル設定を反映
            sound_files = settings.get("sound_files", {})
            for cmd, var in self.sound_file_vars.items():
                var.set(sound_files.get(cmd, ""))
            
            print(f"[SYSTEM] 設定読み込み: {settings}")
            
        except FileNotFoundError:
            print("[SYSTEM] 設定ファイルが見つかりません。デフォルト設定を使用")
        except Exception as e:
            print(f"[SYSTEM ERROR] 設定読み込みエラー: {e}")

    def setup_status_area(self, parent):
        """ステータスエリア"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="🔌 WebSocket接続中...", font=("", 10))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.connection_button = ttk.Button(status_frame, text="🔄 再接続", command=self.reconnect_websocket)
        self.connection_button.grid(row=0, column=1, sticky=tk.E)
        
        status_frame.columnconfigure(0, weight=1)
    
    def update_voice_list(self):
        """音声リストを更新（運営用も追加）"""
        try:
            # VOICEVOXから利用可能な音声IDを取得
            speaker_ids = self.voice_controller.get_available_speaker_ids()
            
            if speaker_ids:
                # ボイス名付きの表示用リストを作成
                voice_options = []
                for speaker_id in sorted(speaker_ids):
                    voice_name = self.voice_controller.get_voice_name(speaker_id)
                    voice_options.append(f"{speaker_id}: {voice_name}")
                
                self.voice_combo['values'] = voice_options
                
                # 運営用音声リストも更新
                if hasattr(self, 'operator_voice_combo'):
                    self.operator_voice_combo['values'] = voice_options
                    if not self.operator_voice_var.get():
                        self.operator_voice_var.set("2: 四国めたん(ノーマル)")
                
                # デフォルト値設定
                default_id = 2 if 2 in speaker_ids else speaker_ids[0]
                default_display = f"{default_id}: {self.voice_controller.get_voice_name(default_id)}"
                self.voice_combo.set(default_display)
                self.voice_name_label.config(text="")
            else:
                # VOICEVOXが利用できない場合のフォールバック
                fallback_options = [f"{i}: 音声ID{i}" for i in range(1, 21)]
                self.voice_combo['values'] = fallback_options
                self.voice_combo.set("2: 音声ID2")
                self.voice_name_label.config(text="VOICEVOXに接続できません")
                
                if hasattr(self, 'operator_voice_combo'):
                    self.operator_voice_combo['values'] = fallback_options
                    self.operator_voice_var.set("2: 音声ID2")
                
        except Exception as e:
            print(f"[GUI ERROR] 音声リスト更新エラー: {e}")
            # エラー時のフォールバック
            fallback_options = [f"{i}: 音声ID{i}" for i in range(1, 21)]
            self.voice_combo['values'] = fallback_options
            self.voice_combo.set("2: 音声ID2")
            self.voice_name_label.config(text="音声情報取得エラー")
    
    def on_voice_changed(self, event=None):
        """音声選択変更時の処理（修正版）"""
        try:
            # "ID: ボイス名" 形式から ID部分を抽出
            selected_text = self.voice_var.get()
            selected_id = int(selected_text.split(':')[0])
            # ボイス名はすでにコンボボックスに表示されているので、ラベルは空に
            self.voice_name_label.config(text="")
        except (ValueError, TypeError, IndexError):
            self.voice_name_label.config(text="")
    
    def update_voice_name_display(self, speaker_id: int):
        """ボイス名表示を更新"""
        try:
            voice_name = self.voice_controller.get_voice_name(speaker_id)
            self.voice_name_label.config(text=voice_name)
        except Exception as e:
            print(f"[GUI ERROR] ボイス名表示エラー: {e}")
            self.voice_name_label.config(text="")
    
    def start_websocket_connection(self):
        """WebSocket接続を開始"""
        def run_websocket():
            try:
                # カスタムWebSocketハンドラー
                self.websocket_handler = CustomWebSocketHandler(self)
                self.websocket_handler.connect_and_run()
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"❌ 接続エラー: {str(e)}", "red"))
        
        # 別スレッドで実行
        self.websocket_thread = threading.Thread(target=run_websocket, daemon=True)
        self.websocket_thread.start()
        
        self.update_status("🔌 WebSocket接続中...", "blue")
    
    def on_comment_select(self, event):
        """コメント選択時の処理"""
        selection = self.comment_tree.selection()
        if selection:
            item = self.comment_tree.item(selection[0])
            comment_data = item['values']
            if len(comment_data) >= 2:
                user_display = comment_data[1]
                print(f"[DEBUG] 選択されたユーザー表示: '{user_display}'")
                
                # 修正：絵文字を除去してユーザーIDを抽出
                if "(" in user_display and ")" in user_display:
                    # "🏢 o:Visited (運営)" から "o:Visited" を抽出
                    user_part = user_display.split("(")[0].strip()
                    # 絵文字を除去（最初の非英数字文字を除去）
                    import re
                    user_id = re.sub(r'^[^\w:]+\s*', '', user_part)
                    print(f"[DEBUG] 抽出されたユーザーID: '{user_id}'")
                else:
                    user_id = user_display.split(' ')[0]
                    
                self.load_user_settings(user_id)
    
    def on_user_select(self, event):
        """ユーザー一覧選択時の処理"""
        selection = self.user_tree.selection()
        if selection:
            item = self.user_tree.item(selection[0])
            user_data = item['values']
            if user_data:
                user_id = user_data[0]
                self.load_user_settings(user_id)
    
    def load_user_settings(self, user_id):
        """ユーザー設定を読み込み（修正版）"""
        # user_idを文字列に変換
        user_id = str(user_id)
        self.selected_user_id = user_id
        
        # ユーザー情報を表示
        self.user_id_label.config(text=f"ユーザーID: {user_id}")
        
        user_type = self.get_user_type(user_id)
        self.user_type_label.config(text=f"種別: {user_type}")
        
        # 設定を取得
        default_settings = {"name": "", "voice": 2, "skin": "", "font": "", "sound": ""}
        settings = self.user_manager.get_user_settings(user_id, default_settings)
        
        # フォームに設定
        self.name_var.set(settings.get("name", ""))
        
        # 音声ID設定（修正版）
        voice_id = settings.get("voice", 2)
        try:
            voice_name = self.voice_controller.get_voice_name(voice_id)
            voice_display = f"{voice_id}: {voice_name}"
            self.voice_var.set(voice_display)
        except:
            self.voice_var.set(f"{voice_id}: 音声ID{voice_id}")
        
        self.skin_var.set(str(settings.get("skin", "")) if settings.get("skin") else "")
        self.font_var.set(str(settings.get("font", "")) if settings.get("font") else "")

    def save_user_settings(self):
        """ユーザー設定を保存（修正版）"""
        if not self.selected_user_id:
            messagebox.showwarning("警告", "ユーザーが選択されていません")
            return

    # 設定値を取得
        name = self.name_var.get().strip() if self.name_var.get().strip() else None
        
        # 音声IDを抽出（修正版）
        try:
            voice_text = self.voice_var.get()
            voice = int(voice_text.split(':')[0])
        except (ValueError, IndexError):
            voice = None
        
        skin = int(self.skin_var.get()) if self.skin_var.get().isdigit() else None
        font = int(self.font_var.get()) if self.font_var.get().isdigit() else None
        
        # データベースに保存
        success = self.user_manager.save_user_settings(
            user_id=self.selected_user_id,
            name=name,
            voice=voice,
            skin=skin,
            font=font
        )
        
        if success:
            messagebox.showinfo("成功", f"ユーザー設定を保存しました\nユーザーID: {self.selected_user_id}")
            self.refresh_user_list()
        else:
            messagebox.showerror("エラー", "設定の保存に失敗しました")
        
    def test_voice(self):
        """音声テスト再生（修正版）"""
        try:
            voice_text = self.voice_var.get()
            voice_id = int(voice_text.split(':')[0])
        except (ValueError, IndexError):
            messagebox.showwarning("警告", "音声IDを正しく選択してください")
            return
        
        voice_name = self.voice_controller.get_voice_name(voice_id)
        test_text = f"音声テストです。{voice_name}で読み上げています。"
        
        # 音声合成・再生
        def test_play():
            try:
                self.voice_controller.enqueue(test_text, voice_id)
                self.root.after(0, lambda: self.update_status("🎤 テスト音声再生完了", "green"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"❌ 音声エラー: {str(e)}", "red"))
        
        threading.Thread(target=test_play, daemon=True).start()
        self.update_status("🎤 テスト音声再生中...", "blue")
    
    def clear_settings(self):
        """設定をクリア"""
        if messagebox.askyesno("確認", "設定をクリアしますか？"):
            self.name_var.set("")
            # 音声IDをデフォルトに戻す（修正版）
            try:
                available_ids = self.voice_controller.get_available_speaker_ids()
                if available_ids:
                    default_voice = 2 if 2 in available_ids else available_ids[0]
                else:
                    default_voice = 2  # フォールバック
                voice_name = self.voice_controller.get_voice_name(default_voice)
                self.voice_var.set(f"{default_voice}: {voice_name}")
                self.voice_name_label.config(text="")
            except:
                self.voice_var.set("2: 音声ID2")
                self.voice_name_label.config(text="デフォルト")
            
            self.skin_var.set("")
            self.font_var.set("")
    
    def add_comment(self, comment_data: Dict[str, Any]):
        """コメントを一覧に追加（運営コメント対応版）"""
        try:
            comment = comment_data.get("comment", "")
            user_id = comment_data.get("user_id", "")
            timestamp = comment_data.get("timestamp", "")
            comment_no = comment_data.get("comment_no", "")
            
            # 時刻表示用
            time_str = timestamp.split()[-1][:8] if timestamp else ""
            
            # ユーザー種別
            user_type = self.get_user_type(user_id)
            user_display = f"{user_id} ({user_type})"
            
            # 運営コメントの特別表示
            if user_type == "運営" or not comment_no:
                user_display = f"🏢 {user_id} (運営)"
            
            # 設定情報
            settings_info = self.get_user_settings_display(user_id)
            
            # ツリービューに追加
            self.comment_tree.insert("", "end", values=(time_str, user_display, comment, settings_info))
            
            # 自動スクロール
            children = self.comment_tree.get_children()
            if children:
                self.comment_tree.see(children[-1])
            
            # ユーザー一覧を更新
            self.add_user_to_list(user_id, user_type)
            
        except Exception as e:
            print(f"[GUI ERROR] コメント追加エラー: {e}")
    
    def get_user_type(self, user_id) -> str:
        """ユーザータイプを判定"""
        # user_idを文字列に変換
        user_id = str(user_id)
        
        if not user_id:
            return "不明"
        elif user_id.startswith("a:"):
            return "184"
        elif user_id.startswith("o:"):
            return "運営"
        elif user_id.isdigit():
            return "生ID"
        else:
            return "その他"
    
    def get_user_settings_display(self, user_id: str) -> str:
        """ユーザー設定を表示用文字列で取得（ボイス名対応版）"""
        default_settings = {"name": None, "voice": 2, "skin": None, "font": None}
        settings = self.user_manager.get_user_settings(user_id, default_settings)
        
        parts = []
        if settings.get("name"):
            parts.append(f"名前:{settings['name']}")
        
        # ボイス名を表示
        voice_id = settings.get("voice", 2)
        if voice_id and voice_id != 2:
            voice_name = self.voice_controller.get_speaker_name(voice_id)
            parts.append(f"音声:{voice_name}")
        
        if settings.get("skin"):
            parts.append(f"スキン:{settings['skin']}")
        if settings.get("font"):
            parts.append(f"フォント:{settings['font']}")
        
        return ", ".join(parts) if parts else "デフォルト"
    
    def add_user_to_list(self, user_id: str, user_type: str):
        """ユーザーを一覧に追加"""
        # 既存チェック
        for item in self.user_tree.get_children():
            if self.user_tree.item(item)['values'][0] == user_id:
                return
        
        # 設定取得
        default_settings = {"name": "", "voice": 2}
        settings = self.user_manager.get_user_settings(user_id, default_settings)
        
        name = settings.get("name", "")
        voice_id = settings.get("voice", 2)
        voice_name = self.voice_controller.get_speaker_name(voice_id)
        
        # user_idを文字列として保存
        self.user_tree.insert("", "end", values=(str(user_id), name, voice_name, user_type))
        
    def refresh_user_list(self):
        """ユーザー一覧を更新"""
        # 一覧をクリア
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # データベースから全ユーザーを取得
        users = self.user_manager.db.get_all_users()
        for user in users:
            user_type = self.get_user_type(user.user_id)
            name = user.name or ""
            voice_id = user.voice_id or 2
            voice_name = self.voice_controller.get_speaker_name(voice_id)
            self.user_tree.insert("", "end", values=(user.user_id, name, voice_name, user_type))
    
    def update_status(self, message: str, color: str = "black"):
        """ステータスを更新"""
        self.status_label.config(text=message, foreground=color)
    
    def reconnect_websocket(self):
        """WebSocket再接続"""
        self.update_status("🔄 再接続中...", "blue")
        self.start_websocket_connection()
    
    def run(self):
        """GUI実行（設定読み込み追加）"""
        self.refresh_user_list()
        self.load_system_settings()
        self.root.mainloop()

class CustomWebSocketHandler(WebSocketHandler):
  """GUI用カスタムWebSocketハンドラー"""
  
  def __init__(self, gui):
      super().__init__()
      self.gui = gui
  
  def connect_and_run(self):
      """WebSocketサーバーに接続して実行（GUI用同期版）"""
      try:
          # 非同期関数を同期的に実行
          asyncio.run(self._async_connect_and_run("ws://localhost:8765"))
      except Exception as e:
          error_msg = f"❌ WebSocket接続エラー: {e}"
          self.gui.root.after(0, lambda: self.gui.update_status(error_msg, "red"))
  
  async def _async_connect_and_run(self, uri: str):
      """実際の非同期接続処理"""
      # ワーカー開始
      self.queue_manager.start_workers(self.voice_controller)
      
      print(f"[GUI] WebSocket接続試行: {uri}")
      
      try:
          async with websockets.connect(uri) as websocket:
              print("[GUI] ✅ WebSocket接続成功")
              self.gui.root.after(0, lambda: self.gui.update_status("✅ 接続完了", "green"))
              
              # メッセージ受信ループ
              async for message in websocket:
                  await self._handle_message(message)
                  
      except Exception as e:
          error_msg = f"❌ WebSocket接続エラー: {e}"
          print(f"[GUI] {error_msg}")
          self.gui.root.after(0, lambda: self.gui.update_status(error_msg, "red"))
      finally:
          self.queue_manager.shutdown()
  
  async def _handle_message(self, message: str):
      """受信メッセージ処理（GUI版）"""
      try:
          data = self._parse_json_message(message)
          if not data:
              return
          
          # GUIにコメントを追加
          self.gui.root.after(0, lambda: self.gui.add_comment(data))
          
          # 元の処理も実行
          success = self.comment_processor.process_comment(data)
          
          # ステータス更新
          if success:
              comment = data.get("comment", "")[:20] + "..." if len(data.get("comment", "")) > 20 else data.get("comment", "")
              self.gui.root.after(0, lambda: self.gui.update_status(f"✅ 処理完了: {comment}", "green"))
          
      except Exception as e:
          error_msg = f"❌ メッセージ処理エラー: {str(e)}"
          self.gui.root.after(0, lambda: self.gui.update_status(error_msg, "red"))
          print(f"[ERROR] {error_msg}")


def main():
  """メインエントリポイント"""
  try:
      app = CommentViewerGUI()
      app.run()
  except KeyboardInterrupt:
      print("\n[INFO] 👋 プログラムを終了します")
  except Exception as e:
      print(f"[ERROR] 予期しないエラー: {e}")


if __name__ == "__main__":
  main()