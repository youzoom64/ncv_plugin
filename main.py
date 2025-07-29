import asyncio
import websockets
import json
import sys
import os
import queue
import threading
import time

# 現在のスクリプトのディレクトリを取得してPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"[DEBUG] Script directory: {current_dir}")
print(f"[DEBUG] Python path includes: {current_dir in sys.path}")

from core.comment_parser import parse_comment
from core.voice_controller import VoiceController
from core.user_manager import UserManager
from core.sound_controller import SoundController

# 2段階キューシステム
text_queue = queue.Queue()      # テキスト→音声合成用
audio_queue = queue.Queue()     # 音声データ→再生用（音声・サウンド共用）

def calculate_speed(qsize):
    """キューサイズに応じて読み上げ速度を動的調整"""
    if qsize <= 0:
        return 1.0
    elif qsize <= 5:
        return 1.0
    elif qsize <= 10:
        return 1.2
    elif qsize <= 20:
        return 1.5
    elif qsize <= 30:
        return 2.0
    elif qsize <= 40:
        return 2.5
    else:
        return 3.0

def synthesis_worker(voice_controller):
    """音声合成専用ワーカー（並行実行）"""
    print("[SYNTHESIS] 音声合成ワーカー開始")
    while True:
        try:
            item = text_queue.get(timeout=5)
            comment_text, voice_id = item
            
            # 現在のキューサイズで速度を決定
            total_qsize = text_queue.qsize() + audio_queue.qsize()
            speed = calculate_speed(total_qsize)
            
            print(f"[SYNTHESIS] 🔄 合成開始: '{comment_text}' (voice:{voice_id}, speed:{speed:.1f}x)")
            
            # 音声合成のみ実行
            audio_data = voice_controller.synthesize_only(comment_text, voice_id, speed)
            if audio_data:
                # 合成完了したら再生キューに追加
                audio_queue.put((comment_text, audio_data))
                print(f"[SYNTHESIS] ✅ 合成完了: '{comment_text}' → 再生キューに追加")
            else:
                print(f"[SYNTHESIS] ❌ 合成失敗: '{comment_text}'")
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[SYNTHESIS ERROR] 音声合成エラー: {e}")
        finally:
            try:
                text_queue.task_done()
            except:
                pass

def playback_worker(voice_controller):
    """音声再生専用ワーカー（順番実行）- 音声とサウンド両方対応"""
    print("[PLAYBACK] 音声再生ワーカー開始")
    while True:
        try:
            item = audio_queue.get(timeout=5)
            comment_text, audio_data = item
            
            print(f"[PLAYBACK] 🔊 再生開始: '{comment_text}'")
            
            # 音声再生のみ実行（音声・サウンド共通）
            success = voice_controller.play_only(audio_data)
            if success:
                print(f"[PLAYBACK] ✅ 再生完了: '{comment_text}'")
            else:
                print(f"[PLAYBACK] ❌ 再生失敗: '{comment_text}'")
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[PLAYBACK ERROR] 音声再生エラー: {e}")
        finally:
            try:
                audio_queue.task_done()
            except:
                pass

def get_user_type(user_id):
    if user_id is None or user_id == "":
        return "不明"
    elif user_id.startswith("a:"):
        return "184"
    elif user_id.startswith("o:"):
        return "運営"
    elif user_id.isdigit():
        return "生ID"
    else:
        return "その他"

async def websocket_client():
    voice_controller = VoiceController()
    user_manager = UserManager()
    sound_controller = SoundController()  # サウンドコントローラー追加
    
    # 音声合成ワーカー開始（5つ並行）
    for i in range(5):
        threading.Thread(target=synthesis_worker, args=(voice_controller,), daemon=True).start()
        print(f"[INFO] 音声合成ワーカー {i+1} 開始")
    
    # 音声再生ワーカー開始（1つのみ）- 音声・サウンド共用
    threading.Thread(target=playback_worker, args=(voice_controller,), daemon=True).start()
    
    print("🎤 音声合成システム開始")
    print("🔊 サウンドシステム開始")
    print("🔌 WebSocketサーバー接続中...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("✅ 接続完了")
            print("💬 コメント送信: 'send:メッセージ' と入力してEnter")
            print("=" * 80)
            
            # 送信用の通常のキュー（同期）
            send_queue = queue.Queue()
            
            # キーボード入力用スレッド
            def input_worker():
                while True:
                    try:
                        user_input = input()
                        if user_input.startswith("send:"):
                            message = user_input[5:]
                            send_data = json.dumps({"action": "send_comment", "message": message})
                            send_queue.put(send_data)
                            print(f"[送信] {message}")
                    except:
                        break
            
            threading.Thread(target=input_worker, daemon=True).start()
            
            # 送信処理用タスク
            async def send_worker():
                while True:
                    try:
                        if not send_queue.empty():
                            send_data = send_queue.get()
                            await websocket.send(send_data)
                        await asyncio.sleep(0.1)
                    except:
                        break
            
            send_task = asyncio.create_task(send_worker())
            
            async for message in websocket:
                try:
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError as e:
                        print(f"[JSON ERROR] 不正なJSON: {message}")
                        continue
                    
                    comment = data.get("comment", "")
                    user_id = data.get("user_id", "")
                    mail = data.get("mail", "")
                    comment_no = data.get("comment_no", "")
                    premium = data.get("premium", 0)
                    date = data.get("date", "")
                    timestamp = data.get("timestamp", "")
                    
                    if not comment.strip():
                        continue
                    
                    user_type = get_user_type(user_id)
                    premium_text = "プレミアム" if premium == 1 else "一般"
                    
                    print(f"📝 コメント: {comment}")
                    print(f"👤 ユーザー: {user_id} ({user_type})")
                    print(f"💎 アカウント: {premium_text}")
                    print(f"📧 メール欄: {mail}")
                    print(f"🔢 コメント番号: {comment_no}")
                    print(f"⏰ 日時: {date}")
                    print(f"🕒 受信時刻: {timestamp}")
                    
                    # コメント解析
                    parsed = parse_comment(comment)
                    
                    # 運営コマンド処理（/info, /gift, /ad など）
                    if parsed["is_system_command"]:
                        command_type = parsed["command_type"]
                        print(f"🎵 運営コマンド検出: /{command_type}")
                        print(f"📝 内容: {parsed['text']}")
                        
                        # コマンドに対応するサウンドを取得
                        sound_data = sound_controller.get_command_sound(command_type)
                        if sound_data:
                            # サウンドを再生キューに追加
                            audio_queue.put((f"[{command_type.upper()}音]", sound_data))
                            print(f"[SOUND] 🔊 {command_type.upper()}音 → 再生キューに追加")
                            
                            # キュー状況表示
                            total_queue_size = text_queue.qsize() + audio_queue.qsize()
                            print(f"[QUEUE] 合成待ち:{text_queue.qsize()}, 再生待ち:{audio_queue.qsize()}")
                        
                        # 統計情報は処理するが、通常の音声読み上げはスキップ
                        if comment_no and isinstance(comment_no, int) and comment_no % 100 == 0:
                            stats = user_manager.get_user_stats()
                            print(f"[STATS] 📊 総ユーザー数: {stats['total_users']}, 最近のユーザー: {stats['recent_users']}")
                        
                        print("=" * 80)
                        continue  # 通常の読み上げ処理をスキップ
                    
                    # 通常コメント処理
                    text_body = parsed["text"]
                    
                    # ユーザー設定をDBから取得
                    default_settings = {
                        "name": None,
                        "voice": 2,  # デフォルト音声ID
                        "skin": None,
                        "font": None,
                        "sound": None
                    }
                    
                    # DBからユーザー設定取得
                    user_settings = user_manager.get_user_settings(user_id, default_settings)
                    
                    # 解析結果とユーザー設定をマージして最終設定を決定
                    final_voice_id = parsed["voice"] if parsed["voice"] is not None else user_settings["voice"]
                    final_name = parsed["name"] if parsed["name"] is not None else user_settings["name"]
                    final_skin = parsed["skin"] if parsed["skin"] is not None else user_settings["skin"]
                    final_font = parsed["font"] if parsed["font"] is not None else user_settings["font"]
                    final_sound = parsed["sound"] if parsed["sound"] is not None else user_settings.get("sound")
                    
                    # 新しい設定がコメントに含まれている場合は保存
                    if parsed["name"] or parsed["voice"] or parsed["skin"] or parsed["font"] or parsed["sound"]:
                        print(f"🎯 新しい設定検出: 名前={parsed['name']}, 音声ID={parsed['voice']}, スキン={parsed['skin']}, フォント={parsed['font']}, サウンド={parsed['sound']}")
                        
                        # 現在のDB設定を取得
                        current_name = user_settings["name"]
                        current_voice = user_settings["voice"]
                        current_skin = user_settings["skin"]
                        current_font = user_settings["font"]
                        current_sound = user_settings.get("sound")
                        
                        # 新しい設定で上書き（Noneでない場合のみ）
                        save_name = parsed["name"] if parsed["name"] is not None else current_name
                        save_voice = parsed["voice"] if parsed["voice"] is not None else current_voice
                        save_skin = parsed["skin"] if parsed["skin"] is not None else current_skin
                        save_font = parsed["font"] if parsed["font"] is not None else current_font
                        save_sound = parsed["sound"] if parsed["sound"] is not None else current_sound
                        
                        # DB保存実行
                        user_manager.save_user_settings(
                            user_id=user_id,
                            name=save_name,
                            voice=save_voice,
                            skin=save_skin,
                            font=save_font,
                            sound=save_sound
                        )
                        print(f"💾 {user_id} の設定を更新しました")
                    else:
                        print(f"🎯 保存済み設定使用: 音声ID={final_voice_id}")
                        if final_name:
                            print(f"     名前: {final_name}")
                    
                    # 最終設定表示
                    settings_info = []
                    if final_name:
                        settings_info.append(f"名前={final_name}")
                    settings_info.append(f"音声ID={final_voice_id}")
                    if final_skin:
                        settings_info.append(f"スキン={final_skin}")
                    if final_font:
                        settings_info.append(f"フォント={final_font}")
                    if final_sound:
                        settings_info.append(f"サウンド={final_sound}")
                    
                    print(f"🎵 最終設定: {', '.join(settings_info)}")
                    
                    # 読み上げ対象外チェック
                    skip_voice = False
                    
                    # 運営コメントは既に上で処理済みなので、ここでは通常ユーザーのみ
                    if mail and any(skip_word in mail.lower() for skip_word in ["184", "sage", "ngs"]):
                        print(f"[SKIP] メール欄設定により読み上げスキップ: {mail}")
                        skip_voice = True
                    
                    if not text_body.strip() or len(text_body.strip()) < 2:
                        print(f"[SKIP] テキストが短すぎる: '{text_body}'")
                        skip_voice = True
                    
                    # 音声合成キューに追加
                    if not skip_voice:
                        # テキストキューに追加（合成用）
                        text_queue.put((text_body, final_voice_id))
                        
                        # ログ出力
                        total_queue_size = text_queue.qsize() + audio_queue.qsize()
                        current_speed = calculate_speed(total_queue_size)
                        
                        print(f"[VOICE] 📥 '{text_body}' → 合成キューに追加")
                        print(f"[QUEUE] 合成待ち:{text_queue.qsize()}, 再生待ち:{audio_queue.qsize()}, 速度:{current_speed:.1f}x")
                        
                        if total_queue_size <= 5:
                            print(f"[QUEUE] 🟢 通常速度")
                        elif total_queue_size <= 10:
                            print(f"[QUEUE] 🟡 少し速め")
                        elif total_queue_size <= 20:
                            print(f"[QUEUE] 🟠 高速モード")
                        elif total_queue_size <= 30:
                            print(f"[QUEUE] 🔴 超高速モード")
                        else:
                            print(f"[QUEUE] 🚨 最高速モード")
                    
                    if comment_no and isinstance(comment_no, int) and comment_no % 100 == 0:
                        stats = user_manager.get_user_stats()
                        print(f"[STATS] 📊 総ユーザー数: {stats['total_users']}, 最近のユーザー: {stats['recent_users']}")
                    
                    print("=" * 80)
                    
                except KeyboardInterrupt:
                    print("[INFO] 👋 ユーザーによる中断")
                    break
                except Exception as e:
                    print(f"[ERROR] ❌ メッセージ処理エラー: {e}")
                    print(f"[ERROR] 📝 問題のメッセージ: {message}")
                    import traceback
                    traceback.print_exc()
                    print("=" * 80)
                    
    except Exception as e:
        print(f"[ERROR] WebSocket接続エラー: {e}")
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("[DEBUG] テスト開始")
        voice_controller = VoiceController()
        sound_controller = SoundController()
        print("[DEBUG] VoiceController作成完了")
        print(f"[DEBUG] VOICEVOX利用可能: {voice_controller.is_voicevox_available}")
        
        print("[DEBUG] 手動接続テスト開始")
        result = voice_controller.reconnect()
        print(f"[DEBUG] 接続結果: {result}")
        
        # 音声テスト
        voice_controller.enqueue("テスト音声です。ずんだもんだっぽ！", speaker_id=3)
        
        # サウンドテスト
        info_sound = sound_controller.get_command_sound("info")
        if info_sound:
            sound_controller.play_sound_data(info_sound)
        
        exit()
    
    asyncio.run(websocket_client())