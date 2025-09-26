import deepl
from flask import current_app

def translate_text(text, target_lang):
    auth_key = current_app.config['DEEPL_API_KEY']

    translator = deepl.Translator(auth_key)
    result = translator.translate_text(text, target_lang = target_lang)
    return result.text