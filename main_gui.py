# main_gui.py (新規作成)
import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.comment_viewer import main as gui_main

if __name__ == "__main__":
    gui_main()