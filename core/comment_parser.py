import re

# 例: こんにちは@ロータス{s:01,f:03,v:05}
FULL_PATTERN = re.compile(r"^(.*?)@(.+?)\{([^}]+)\}$")
KV_PATTERN = re.compile(r"(s|f|v):(\d+)")

def parse_comment(raw_comment):
    """
    コメントを解析して名前・スキン・フォント・ボイス設定を抽出。
    該当しない場合でもtextは常に返す。
    """
    result = {
        "text": raw_comment,
        "name": None,
        "skin": None,
        "font": None,
        "voice": None
    }

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