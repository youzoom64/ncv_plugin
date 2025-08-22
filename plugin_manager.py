import os
import importlib
import threading
import time
from flask import Flask, jsonify, request
from typing import Dict, Any

class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.plugin_threads = {}
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/plugins', methods=['GET'])
        def list_plugins():
            return jsonify({
                "loaded": list(self.plugins.keys()),
                "status": {name: plugin.is_running() for name, plugin in self.plugins.items()}
            })
        
        @self.app.route('/plugins/load/<plugin_name>', methods=['POST'])
        def load_plugin(plugin_name):
            return jsonify(self.load_plugin(plugin_name))
        
        @self.app.route('/plugins/unload/<plugin_name>', methods=['POST'])
        def unload_plugin(plugin_name):
            return jsonify(self.unload_plugin(plugin_name))
        
        @self.app.route('/plugins/restart/<plugin_name>', methods=['POST'])
        def restart_plugin(plugin_name):
            self.unload_plugin(plugin_name)
            return jsonify(self.load_plugin(plugin_name))
        
        @self.app.route('/plugins/autoload', methods=['POST'])
        def autoload_plugins():
            return jsonify(self.auto_load_plugins())
    
    def load_plugin(self, plugin_name: str) -> Dict[str, Any]:
        try:
            # プラグインディレクトリから動的インポート
            plugin_path = f"plugins.{plugin_name}.main"
            plugin_module = importlib.import_module(plugin_path)
            
            # プラグインインスタンス作成
            plugin_instance = plugin_module.create_plugin()
            self.plugins[plugin_name] = plugin_instance
            
            # 別スレッドで実行
            thread = threading.Thread(target=plugin_instance.run, daemon=True)
            thread.start()
            self.plugin_threads[plugin_name] = thread
            
            return {"status": "success", "message": f"Plugin {plugin_name} loaded"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        if plugin_name in self.plugins:
            self.plugins[plugin_name].stop()
            del self.plugins[plugin_name]
            if plugin_name in self.plugin_threads:
                del self.plugin_threads[plugin_name]
            return {"status": "success", "message": f"Plugin {plugin_name} unloaded"}
        return {"status": "error", "message": f"Plugin {plugin_name} not found"}
    
    def auto_load_plugins(self) -> Dict[str, Any]:
        """pluginsディレクトリから自動でプラグインをロード"""
        loaded = []
        errors = []
        
        plugins_dir = "plugins"
        if os.path.exists(plugins_dir):
            for item in os.listdir(plugins_dir):
                plugin_path = os.path.join(plugins_dir, item)
                if os.path.isdir(plugin_path) and not item.startswith('__'):
                    # main.pyがあるかチェック
                    main_file = os.path.join(plugin_path, "main.py")
                    if os.path.exists(main_file):
                        result = self.load_plugin(item)
                        if result["status"] == "success":
                            loaded.append(item)
                        else:
                            errors.append(f"{item}: {result['message']}")
        
        return {"loaded": loaded, "errors": errors}
    
    def run(self, host="localhost", port=8080):
        print(f"[INFO] プラグインマネージャー起動: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    manager = PluginManager()
    manager.run()