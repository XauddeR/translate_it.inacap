import deepl
from flask import current_app

class TranslationError(Exception):
    pass

def translate_text(text, target_lang):
    try:
        auth_key = current_app.config['DEEPL_API_KEY']
        if not auth_key:
            raise TranslationError('No se encontró la clave de API de DeepL.')

        translator = deepl.Translator(auth_key)
        result = translator.translate_text(text, target_lang = target_lang)

        translated = getattr(result, 'text', None)
        if not translated:
            raise TranslationError('La API de DeepL no devolvió texto traducido.')

        return translated

    except deepl.exceptions.AuthorizationException as e:
        raise TranslationError(f'[ERROR] Autenticación con DeepL: {e}') from e

    except deepl.exceptions.DeepLException as e:
        raise TranslationError(f'[ERROR] API DeepL: {e}') from e

    except Exception as e:
        raise TranslationError(f'[ERROR] Fallo inesperado en la traducción: {e}') from e
