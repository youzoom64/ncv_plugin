import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugins.base_plugin import BasePlugin
import subprocess

class WebAppPlugin(BasePlugin):
    def __init__(self):
        super().__init__("webapp")
        self.process = None
    
    def run(self):
        self.running = True
        webapp_path = os.path.join(os.path.dirname(__file__), "..", "..", "comegeneskingenerator", "app.py")
        
        try:
            self.process = subprocess.Popen([sys.executable, webapp_path])
            self.process.wait()
        except Exception as e:
            print(f"WebApp Plugin error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()

def create_plugin():
    return WebAppPlugin()
