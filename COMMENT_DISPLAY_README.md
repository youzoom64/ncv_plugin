# ニコ生コメント表示システム

## 概要

このシステムは、ニコ生のコメントをリアルタイムで表示し、スキンとフォントを適用した美しいアニメーション付きコメント表示を提供します。

## 機能

- 🎨 **スキン表示**: 512x32 ピクセルの PNG/JPG 画像を背景として使用
- 🔤 **フォント表示**: 20 種類の日本語 Google Fonts をサポート
- 🎬 **滑らかなアニメーション**: 右から左へのスライドイン、上移動
- ⚡ **リアルタイム更新**: WebSocket による即座のコメント表示
- 🔄 **自動スクロール**: 20 秒ごとの自動上移動
- 🎯 **OBS 対応**: 背景透過で OBS に表示可能

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. スキン画像の配置

`skin/`フォルダに 512x32 ピクセルの PNG/JPG 画像を配置：

- `154.png` → スキン ID: 154
- `6.png` → スキン ID: 6
- など

### 3. システム起動

```bash
# バッチファイルで起動（推奨）
start_comment_display.bat

# または手動で起動
python gui/comment_websocket_server.py
```

## 使用方法

### 1. システム起動

1. `start_comment_display.bat`を実行
2. コメント表示 WebSocket サーバーが起動
3. ブラウザで`gui/comment_display.html`が自動で開く

### 2. OBS での表示

1. OBS で「ブラウザソース」を追加
2. URL に`gui/comment_display.html`の絶対パスを設定
3. 幅: 512px, 高さ: 適宜設定
4. 「背景を透明にする」にチェック

### 3. コメント設定

コメントに設定を追加：

```
こんにちは@ユーザー名{s:154,f:5,v:3}
```

- `s:154` → スキン ID 154
- `f:5` → フォント ID 5 (New Tegomin)
- `v:3` → ボイス ID 3

## フォント一覧

| ID  | フォント名       | 説明           |
| --- | ---------------- | -------------- |
| 0   | DotGothic16      | デフォルト     |
| 1   | Dela Gothic One  | ゴシック       |
| 2   | Hachi Maru Pop   | 丸ゴシック     |
| 3   | Klee One         | 手書き風       |
| 4   | RocknRoll One    | ロック風       |
| 5   | New Tegomin      | 明朝体         |
| 6   | Train One        | 電車風         |
| 7   | DotGothic16      | ドット風       |
| 8   | Reggae One       | レゲエ風       |
| 9   | Yuji Syuku       | 行書体         |
| 10  | Yuji Boku        | 楷書体         |
| 11  | Mochiy Pop One   | ポップ風       |
| 12  | Kaisei HarunoUmi | 海風明朝       |
| 13  | Shippori Antique | アンティーク   |
| 14  | Stick            | スティック風   |
| 15  | Rampart One      | 城壁風         |
| 16  | Zen Antique      | 禅アンティーク |
| 17  | Mochiy Pop P One | ポップ P 風    |
| 18  | Zen Kurenaido    | 禅紅雷堂       |
| 19  | Yusei Magic      | 夕星マジック   |

## テスト

システムの動作確認：

```bash
python test_comment_display.py
```

## ファイル構成

```
gui/
├── comment_display.html          # 表示用HTML
├── comment_display.js            # アニメーション制御
└── comment_websocket_server.py   # WebSocketサーバー

handlers/
└── websocket_handler.py          # 既存WebSocketハンドラー（統合済み）

start_comment_display.bat         # 起動スクリプト
test_comment_display.py           # テストスクリプト
```

## 技術仕様

- **WebSocket**: リアルタイム通信
- **CSS3**: アニメーション・トランジション
- **Google Fonts**: 日本語フォント
- **背景透過**: OBS 対応
- **レスポンシブ**: 512x32 固定サイズ

## トラブルシューティング

### WebSocket 接続エラー

- ポート 8080 が使用中でないか確認
- ファイアウォール設定を確認

### フォントが表示されない

- インターネット接続を確認
- ブラウザのキャッシュをクリア

### スキンが表示されない

- `skin/`フォルダ内の画像ファイルを確認
- ファイル名とスキン ID の対応を確認

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
