# 🚀 自動起動機能付きニコ生コメント表示システム

## ✨ 新機能：自動起動

**メイン GUI を起動するだけで、コメント表示システムも自動的に起動します！**

## 🎯 使用方法

### 従来の方法（手動）

```bash
# 個別に起動が必要だった
start_comment_display.bat
```

### 新しい方法（自動）

```bash
# これだけで全部起動！
python main_gui.py
```

## 🔄 自動起動されるもの

1. **🎤 音声合成システム**
2. **🔊 サウンドシステム**
3. **🖥️ コメント表示システム**
   - WebSocket サーバー起動
   - HTML ファイルをブラウザで自動オープン
4. **🔌 プラグインシステム**

## 📁 ファイル構成

```
main_gui.py                    # メイン起動ファイル（統合済み）
├── gui/
│   ├── comment_viewer.py      # メインGUI
│   ├── comment_display.html   # コメント表示HTML
│   ├── comment_display.js     # アニメーション制御
│   └── comment_websocket_server.py  # WebSocketサーバー
└── core/                      # コアシステム
```

## 🚀 起動手順

### 1. メイン GUI 起動

```bash
python main_gui.py
```

### 2. 自動起動されるもの

- ✅ コメント表示 WebSocket サーバー（ポート 8080）
- ✅ コメント表示 HTML（ブラウザで自動オープン）
- ✅ 音声・サウンドシステム
- ✅ プラグインシステム

### 3. OBS 設定

1. OBS で「ブラウザソース」を追加
2. URL に表示された HTML ファイルのパスを設定
3. 幅: 512px, 高さ: 適宜設定
4. 「背景を透明にする」にチェック

## 🔧 カスタマイズ

### 起動順序の変更

`main_gui.py`の`main()`関数で起動順序を調整可能：

```python
def main():
    # プラグイン起動
    threading.Thread(target=start_plugins, daemon=True).start()

    # コメント表示システム起動
    threading.Thread(target=start_comment_display_system, daemon=True).start()

    # メインGUI起動
    gui_main()
```

### 待機時間の調整

`start_comment_display_system()`関数内の`time.sleep(3)`で調整可能

## 🐛 トラブルシューティング

### コメント表示が起動しない

1. コンソールでエラーメッセージを確認
2. ポート 8080 が使用中でないか確認
3. `skin/`フォルダ内の画像ファイルを確認

### HTML ファイルが開かない

1. ブラウザの設定を確認
2. ファイルパスが正しいか確認
3. 手動で`gui/comment_display.html`を開いてテスト

## 📝 ログ出力

起動時に以下のログが表示されます：

```
[INFO] プラグイン起動完了: X
🖥️ コメント表示システムを起動中...
✅ コメント表示HTMLをブラウザで開きました
```

## 🎉 メリット

- **🚀 ワンクリック起動**: 複数のスクリプトを個別に起動する必要なし
- **⏰ 自動化**: 起動順序とタイミングを自動制御
- **🔧 統合管理**: 全システムを一元管理
- **📱 クロスプラットフォーム**: Windows/macOS/Linux 対応

これで、メイン GUI を起動するだけで全てのシステムが自動的に起動します！
