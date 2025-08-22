import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from plugins.base_plugin import BasePlugin
from handlers.websocket_handler import WebSocketHandler
import asyncio

class NCVWebSocketPlugin(BasePlugin):
    def __init__(self):
        super().__init__("ncv_websocket")
        self.handler = WebSocketHandler()
        self.loop = None
    
    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(
                self.handler.connect_and_run("ws://localhost:8765")
            )
        except Exception as e:
            print(f"NCV WebSocket Plugin error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

def create_plugin():
    return NCVWebSocketPlugin()
