import re

# 例: こんにちは@ロータス{s:01,f:03,v:05}
FULL_PATTERN = re.compile(r"^(.*?)@(.+?)\{([^}]+)\}$")
KV_PATTERN = re.compile(r"(s|f|v):(\d+)")

# システムコマンドパターン
SYSTEM_COMMAND_PATTERN = re.compile(r"^/(\w+(?:\s+\d+)?)")

def parse_comment(raw_comment):
    """
    コメントを解析して名前・スキン・フォント・ボイス設定を抽出。
    システムコマンド（/info, /gift, /ad など）も検出。
    """
    result = {
        "text": raw_comment,
        "name": None,
        "skin": None,
        "font": None,
        "voice": None,
        "sound": None,
        "is_system_command": False,
        "command_type": None
    }

    # システムコマンドチェック
    system_match = SYSTEM_COMMAND_PATTERN.match(raw_comment)
    if system_match:
        command_type = system_match.group(1).lower()
        result.update({
            "is_system_command": True,
            "command_type": command_type,
            "text": raw_comment  # コマンド全体をテキストとして保持
        })
        return result

    # 通常の設定構文チェック
    match = FULL_PATTERN.match(raw_comment)
    if not match:
        return result  # 構文なしでもtextのみ返す

    body, name, settings_str = match.groups()
    settings = dict(KV_PATTERN.findall(settings_str))

    result.update({
        "text": body.strip(),
        "name": name.strip(),
        "skin": int(settings.get("s")) if "s" in settings else None,
        "font": int(settings.get("f")) if "f" in settings else None,
        "voice": int(settings.get("v")) if "v" in settings else None,
    })

    return result