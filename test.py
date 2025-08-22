import requests
import xml.etree.ElementTree as ET
import os
from urllib.parse import urlparse

def get_user_icon_url(user_id: str) -> str:
    """ユーザーIDからアイコンURLを生成"""
    if len(user_id) >= 3:
        prefix = user_id[:3]
        return f"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/{prefix}/{user_id}.jpg"
    else:
        # 3桁未満の場合の処理
        return f"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/{user_id.zfill(3)[:3]}/{user_id}.jpg"

def download_user_icon(user_id: str, icon_dir: str = "icon") -> bool:
    """ユーザーアイコンをダウンロードして保存"""
    try:
        # iconディレクトリを作成
        os.makedirs(icon_dir, exist_ok=True)
        
        # 既にファイルが存在する場合はスキップ
        icon_path = os.path.join(icon_dir, f"{user_id}.jpg")
        if os.path.exists(icon_path):
            print(f"✅ アイコン既存: {icon_path}")
            return True
        
        # アイコンURLを生成
        icon_url = get_user_icon_url(user_id)
        print(f"アイコンURL: {icon_url}")
        
        # ヘッダーを追加してアイコンをダウンロード
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.nicovideo.jp/'
        }
        
        response = requests.get(icon_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # ファイルに保存
            with open(icon_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ アイコン保存成功: {icon_path}")
            return True
        else:
            print(f"❌ アイコン取得失敗: ステータスコード {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ アイコンダウンロードエラー: {e}")
        return False

def get_user_nickname(user_id: str) -> str:
    """静画APIからユーザーのニックネームを取得（複数の方法を試行）"""
    
    # 方法1: 元の静画API（ヘッダー付き）
    try:
        url = f"http://seiga.nicovideo.jp/api/user/info?id={user_id}"
        print(f"方法1 - 静画API: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://seiga.nicovideo.jp/',
            'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            response_text = response.text
            print(f"レスポンス: {response_text[:200]}...")
            
            root = ET.fromstring(response_text)
            nickname_elem = root.find('.//nickname')
            
            if nickname_elem is not None:
                nickname = nickname_elem.text
                print(f"✅ 方法1成功 - ニックネーム: '{nickname}'")
                return nickname
        else:
            print(f"❌ 方法1失敗: ステータスコード {response.status_code}")
            
    except Exception as e:
        print(f"❌ 方法1エラー: {e}")
    
    # 方法2: HTTPS版を試行
    try:
        url = f"https://seiga.nicovideo.jp/api/user/info?id={user_id}"
        print(f"方法2 - HTTPS静画API: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://seiga.nicovideo.jp/',
            'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            response_text = response.text
            print(f"レスポンス: {response_text[:200]}...")
            
            root = ET.fromstring(response_text)
            nickname_elem = root.find('.//nickname')
            
            if nickname_elem is not None:
                nickname = nickname_elem.text
                print(f"✅ 方法2成功 - ニックネーム: '{nickname}'")
                return nickname
        else:
            print(f"❌ 方法2失敗: ステータスコード {response.status_code}")
            
    except Exception as e:
        print(f"❌ 方法2エラー: {e}")
    
    # 方法3: ユーザーページスクレイピング（最後の手段）
    try:
        url = f"https://www.nicovideo.jp/user/{user_id}"
        print(f"方法3 - ユーザーページ: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            # 簡易的にタイトルタグからニックネームを抽出
            html_content = response.text
            if '<title>' in html_content and '</title>' in html_content:
                title_start = html_content.find('<title>') + 7
                title_end = html_content.find('</title>')
                title = html_content[title_start:title_end].strip()
                
                # "ユーザー名さんのユーザーページ - ニコニコ" のようなフォーマットから抽出
                if 'さんのユーザーページ' in title:
                    nickname = title.split('さんのユーザーページ')[0].strip()
                    print(f"✅ 方法3成功 - ニックネーム: '{nickname}'")
                    return nickname
                    
        print(f"❌ 方法3失敗: ニックネーム抽出できず")
            
    except Exception as e:
        print(f"❌ 方法3エラー: {e}")
    
    print("❌ 全ての方法が失敗しました")
    return None

def test_user_info(user_id: str):
    """ユーザー情報テスト（ニックネーム + アイコン取得）"""
    print(f"ユーザーID: {user_id} をテスト中...")
    
    print("=== ユーザー名取得テスト ===")
    nickname = get_user_nickname(user_id)
    
    print("\n=== アイコン取得テスト ===")
    icon_success = download_user_icon(user_id)
    
    print("\n=== 結果まとめ ===")
    if nickname:
        print(f"✅ ユーザー名取得成功: {nickname}")
    else:
        print("❌ ユーザー名取得失敗")
    
    if icon_success:
        print(f"✅ アイコン取得成功: icon/{user_id}.jpg")
    else:
        print("❌ アイコン取得失敗")
    
    print()

def main():
    """メインテストループ"""
    print("ニコニコユーザー情報取得テスト")
    print("=" * 50)
    
    while True:
        user_input = input("ユーザーIDを入力 (終了: q): ").strip()
        
        if user_input.lower() == 'q':
            print("テスト終了")
            break
        
        if not user_input:
            print("ユーザーIDを入力してください")
            continue
        
        # 184ユーザー（a:で始まる）の場合は警告
        if user_input.startswith('a:'):
            print("⚠️  184ユーザーは取得できません")
            continue
        
        test_user_info(user_input)

if __name__ == "__main__":
    main()