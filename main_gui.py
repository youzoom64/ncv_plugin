import sys
import os
import threading
import subprocess
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.comment_viewer import main as gui_main
from plugin_manager import PluginManager
from gui.comment_websocket_server import get_comment_server

def start_plugins():
    manager = PluginManager()
    result = manager.auto_load_plugins()
    print(f"[INFO] プラグイン起動完了: {result['loaded']}")

def start_comment_display_system():
    """コメント表示システムを自動起動"""
    try:
        print("🖥️ コメント表示システムを起動中...")
        
        # コメント表示WebSocketサーバーを起動
        print("🔌 コメント表示WebSocketサーバーを起動中...")
        comment_server = get_comment_server()
        
        # WebSocketサーバーを実際に起動
        import asyncio
        def run_server():
            try:
                asyncio.run(comment_server.start_server())
            except Exception as e:
                print(f"❌ WebSocketサーバー起動エラー: {e}")
        
        # WebSocketサーバーを別スレッドで起動
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        print("✅ コメント表示WebSocketサーバー起動完了")
        
        # 3秒待機
        time.sleep(3)
        
        # HTMLファイルをブラウザで開く
        html_path = os.path.join(current_dir, "gui", "comment_display.html")
        if os.path.exists(html_path):
            try:
                # Windowsの場合
                if os.name == 'nt':
                    subprocess.Popen(['start', html_path], shell=True)
                # macOSの場合
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', html_path])
                # Linuxの場合
                else:
                    subprocess.Popen(['xdg-open', html_path])
                print("✅ コメント表示HTMLをブラウザで開きました")
            except Exception as e:
                print(f"⚠️ HTMLファイル起動エラー: {e}")
        else:
            print(f"⚠️ HTMLファイルが見つかりません: {html_path}")
            
    except Exception as e:
        print(f"❌ コメント表示システム起動エラー: {e}")

def main():
    # プラグインを別スレッドで起動
    threading.Thread(target=start_plugins, daemon=True).start()
    
    # コメント表示システムを別スレッドで起動
    threading.Thread(target=start_comment_display_system, daemon=True).start()
    
    # GUIを起動
    gui_main()

if __name__ == "__main__":
    main()