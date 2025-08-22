import sys
import os
import threading

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.comment_viewer import main as gui_main
from plugin_manager import PluginManager

def start_plugins():
    manager = PluginManager()
    result = manager.auto_load_plugins()
    print(f"[INFO] プラグイン起動完了: {result['loaded']}")

def main():
    # プラグインを別スレッドで起動
    threading.Thread(target=start_plugins, daemon=True).start()
    
    # GUIを起動
    gui_main()

if __name__ == "__main__":
    main()