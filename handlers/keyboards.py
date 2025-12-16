from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = [
        [
            InlineKeyboardButton(text="🌀 Add a bot to the chat", url="https://t.me/DownloaderMikitabot?startgroup=true")
        ],
        [
            InlineKeyboardButton(text="🛟 Support", url="https://t.me/blehhhhhhhhhhhhhhhhhhhhhhhh"),
            InlineKeyboardButton(text="🌍 Change language", callback_data="language")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def download_success_menu(file_id=None):
    kb = []
    if file_id:
        kb.append([
            InlineKeyboardButton(text="🎵 Convert to MP3", callback_data=f"convert_mp3:{file_id}")
        ])
    
    
    kb.extend([
        [
            InlineKeyboardButton(text="🎵 FindMusic Spotify", callback_data="find_music_spotify"),
        ],
        [
            InlineKeyboardButton(text="🛑 YouTube download bot", callback_data="coming_soon")
        ]
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def language_menu():
    kb = [
        [
            InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇰🇭 Khmer", callback_data="lang_km")
        ],
        [
            InlineKeyboardButton(text="🇻🇳 Vietnamese", callback_data="lang_vi"),
            InlineKeyboardButton(text="🇮🇩 Indonesian", callback_data="lang_id")
        ],
        [
            InlineKeyboardButton(text="🇮🇳 Hindi", callback_data="lang_hi"),
            InlineKeyboardButton(text="🇨🇳 Chinese", callback_data="lang_zh")
        ],
        [
            InlineKeyboardButton(text="🇯🇵 Japanese", callback_data="lang_ja"),
            InlineKeyboardButton(text="🇰🇷 Korean", callback_data="lang_ko")
        ],
        [
            InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def platforms_menu():
    kb = [
        [
            InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
