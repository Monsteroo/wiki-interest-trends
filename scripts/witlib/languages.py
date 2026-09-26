"""Wikipedia language editions known by name: code -> (English, Ukrainian, native)."""
from __future__ import annotations

import difflib

LANGUAGES: dict[str, tuple[str, str, str]] = {
    "en": ("English", "англійська", "English"),
    "de": ("German", "німецька", "Deutsch"),
    "fr": ("French", "французька", "Français"),
    "es": ("Spanish", "іспанська", "Español"),
    "it": ("Italian", "італійська", "Italiano"),
    "pl": ("Polish", "польська", "Polski"),
    "pt": ("Portuguese", "португальська", "Português"),
    "ru": ("Russian", "російська", "Русский"),
    "uk": ("Ukrainian", "українська", "Українська"),
    "nl": ("Dutch", "нідерландська", "Nederlands"),
    "sv": ("Swedish", "шведська", "Svenska"),
    "ja": ("Japanese", "японська", "日本語"),
    "zh": ("Chinese", "китайська", "中文"),
    "ar": ("Arabic", "арабська", "العربية"),
    "fa": ("Persian", "перська", "فارسی"),
    "cs": ("Czech", "чеська", "Čeština"),
    "sk": ("Slovak", "словацька", "Slovenčina"),
    "hu": ("Hungarian", "угорська", "Magyar"),
    "ro": ("Romanian", "румунська", "Română"),
    "tr": ("Turkish", "турецька", "Türkçe"),
    "id": ("Indonesian", "індонезійська", "Bahasa Indonesia"),
    "vi": ("Vietnamese", "в'єтнамська", "Tiếng Việt"),
    "ko": ("Korean", "корейська", "한국어"),
    "he": ("Hebrew", "іврит", "עברית"),
    "fi": ("Finnish", "фінська", "Suomi"),
    "no": ("Norwegian", "норвезька", "Norsk"),
    "da": ("Danish", "данська", "Dansk"),
    "el": ("Greek", "грецька", "Ελληνικά"),
    "bg": ("Bulgarian", "болгарська", "Български"),
    "sr": ("Serbian", "сербська", "Српски"),
    "hr": ("Croatian", "хорватська", "Hrvatski"),
    "sl": ("Slovenian", "словенська", "Slovenščina"),
    "lt": ("Lithuanian", "литовська", "Lietuvių"),
    "lv": ("Latvian", "латиська", "Latviešu"),
    "et": ("Estonian", "естонська", "Eesti"),
    "be": ("Belarusian", "білоруська", "Беларуская"),
    "kk": ("Kazakh", "казахська", "Қазақша"),
    "ka": ("Georgian", "грузинська", "ქართული"),
    "hy": ("Armenian", "вірменська", "Հայերեն"),
    "az": ("Azerbaijani", "азербайджанська", "Azərbaycanca"),
    "uz": ("Uzbek", "узбецька", "Oʻzbekcha"),
    "hi": ("Hindi", "гінді", "हिन्दी"),
    "bn": ("Bengali", "бенгальська", "বাংলা"),
    "ta": ("Tamil", "тамільська", "தமிழ்"),
    "th": ("Thai", "тайська", "ไทย"),
    "ms": ("Malay", "малайська", "Bahasa Melayu"),
    "ca": ("Catalan", "каталанська", "Català"),
    "eu": ("Basque", "баскська", "Euskara"),
    "gl": ("Galician", "галісійська", "Galego"),
    "ur": ("Urdu", "урду", "اردو"),
    "mr": ("Marathi", "маратхі", "मराठी"),
    "te": ("Telugu", "телугу", "తెలుగు"),
    "ml": ("Malayalam", "малаялам", "മലയാളം"),
    "af": ("Afrikaans", "африкаанс", "Afrikaans"),
    "sq": ("Albanian", "албанська", "Shqip"),
    "mk": ("Macedonian", "македонська", "Македонски"),
    "is": ("Icelandic", "ісландська", "Íslenska"),
    "ga": ("Irish", "ірландська", "Gaeilge"),
    "cy": ("Welsh", "валлійська", "Cymraeg"),
    "eo": ("Esperanto", "есперанто", "Esperanto"),
}

_ALIASES: dict[str, str] = {}
for _code, _names in LANGUAGES.items():
    _ALIASES[_code] = _code
    for _name in _names:
        _ALIASES[_name.casefold()] = _code


def normalize_language(value: str) -> str:
    """Return the Wikipedia code for a code or a language name; raise ValueError with a hint."""
    key = value.strip().casefold()
    if key in _ALIASES:
        return _ALIASES[key]
    close = difflib.get_close_matches(key, list(_ALIASES), n=1, cutoff=0.6)
    hint = f"; did you mean '{_ALIASES[close[0]]}'?" if close else ""
    raise ValueError(f"unknown language '{value}'{hint}")


def language_name(code: str, lang: str) -> str:
    english, ukrainian, _native = LANGUAGES[code]
    return ukrainian if lang == "uk" else english
