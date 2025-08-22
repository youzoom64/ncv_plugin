# core/text_converter.py
import json
import os
import re
from typing import Dict, Any, Optional, List

class TextConverter:
    def __init__(self, config_path: str = "config/text_conversion.json"):
        self.config_path = config_path
        self.conversion_rules = {}
        self.regex_rules = {}
        self._load_config()
    
    def _load_config(self):
        """変換設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversion_rules = data.get("simple_rules", {})
                    self.regex_rules = data.get("regex_rules", {})
                print(f"[CONVERTER] 設定ファイル読み込み完了: {len(self.conversion_rules)}個の単純ルール, {len(self.regex_rules)}個の正規表現ルール")
            else:
                print(f"[CONVERTER] 設定ファイルが見つかりません。デフォルト設定を作成: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            print(f"[CONVERTER ERROR] 設定ファイル読み込みエラー: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """デフォルト変換設定を作成"""
        default_data = {
            "simple_rules": {
                "www": "わらわらわら",
                "ｗｗｗ": "わらわらわら",
                "wwww": "わらわらわらわら",
                "ｗｗｗｗ": "わらわらわらわら",
                "草": "わら",
                "888": "ぱちぱちぱち",
                "８８８": "ぱちぱちぱち",
                "おつ": "お疲れさまでした",
                "乙": "お疲れさまでした",
                "うp": "アップロード",
                "うｐ": "アップロード",
                "ktkr": "きたこれ",
                "キタコレ": "きたこれ",
                "wktk": "わくわくてかてか",
                "ワクテカ": "わくわくてかてか"
            },
            "regex_rules": {
                "w{3,}": "わらわらわら",
                "ｗ{3,}": "わらわらわら",
                "8{3,}": "ぱちぱちぱち",
                "８{3,}": "ぱちぱちぱち"
            }
        }
        
        self.conversion_rules = default_data["simple_rules"]
        self.regex_rules = default_data["regex_rules"]
        self._save_config()
    
    def _save_config(self):
        """設定ファイルを保存"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                "simple_rules": self.conversion_rules,
                "regex_rules": self.regex_rules
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[CONVERTER] 設定ファイル保存完了: {self.config_path}")
        except Exception as e:
            print(f"[CONVERTER ERROR] 設定ファイル保存エラー: {e}")
    
    def convert_text(self, text: str) -> str:
        """テキストを変換ルールに従って変換"""
        if not text:
            return text
            
        original_text = text
        converted_text = text
        
        # 1. 単純な置換ルールを適用
        for original, replacement in self.conversion_rules.items():
            if original in converted_text:
                converted_text = converted_text.replace(original, replacement)
        
        # 2. 正規表現ルールを適用
        for pattern, replacement in self.regex_rules.items():
            try:
                converted_text = re.sub(pattern, replacement, converted_text)
            except re.error as e:
                print(f"[CONVERTER ERROR] 正規表現エラー '{pattern}': {e}")
        
        # 変換があった場合はログ出力
        if converted_text != original_text:
            print(f"[CONVERTER] 🔄 テキスト変換: '{original_text}' → '{converted_text}'")
        
        return converted_text
    
    def add_simple_rule(self, original: str, replacement: str):
        """単純な置換ルールを追加"""
        self.conversion_rules[original] = replacement
        self._save_config()
        print(f"[CONVERTER] ✅ 単純ルール追加: '{original}' → '{replacement}'")
    
    def add_regex_rule(self, pattern: str, replacement: str):
        """正規表現ルールを追加"""
        try:
            # パターンの妥当性をチェック
            re.compile(pattern)
            self.regex_rules[pattern] = replacement
            self._save_config()
            print(f"[CONVERTER] ✅ 正規表現ルール追加: '{pattern}' → '{replacement}'")
        except re.error as e:
            print(f"[CONVERTER ERROR] 無効な正規表現パターン '{pattern}': {e}")
            raise
    
    def remove_simple_rule(self, original: str):
        """単純な置換ルールを削除"""
        if original in self.conversion_rules:
            del self.conversion_rules[original]
            self._save_config()
            print(f"[CONVERTER] 🗑️ 単純ルール削除: '{original}'")
        else:
            print(f"[CONVERTER] ⚠️ ルールが見つかりません: '{original}'")
    
    def remove_regex_rule(self, pattern: str):
        """正規表現ルールを削除"""
        if pattern in self.regex_rules:
            del self.regex_rules[pattern]
            self._save_config()
            print(f"[CONVERTER] 🗑️ 正規表現ルール削除: '{pattern}'")
        else:
            print(f"[CONVERTER] ⚠️ ルールが見つかりません: '{pattern}'")
    
    def get_all_rules(self) -> Dict[str, Any]:
        """全ての変換ルールを取得"""
        return {
            "simple_rules": self.conversion_rules.copy(),
            "regex_rules": self.regex_rules.copy()
        }
    
    def reload_config(self):
        """設定を再読み込み"""
        print("[CONVERTER] 🔄 設定を再読み込みします...")
        self._load_config()