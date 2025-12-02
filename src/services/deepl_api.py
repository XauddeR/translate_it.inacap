import deepl
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

class TranslationError(Exception):
    pass

@retry(
    stop = stop_after_attempt(3),
    wait = wait_exponential(multiplier = 1, min = 1, max = 10),
    retry = retry_if_exception(
        lambda e: (
            isinstance(e, (deepl.exceptions.DeepLException, TimeoutError))
            and not isinstance(e, deepl.exceptions.AuthorizationException)
        )
    ),
    reraise = True,
)

def _retry_deepl_request(translator, text, target_lang):
    return translator.translate_text(text, target_lang = target_lang)


def translate_text(text, target_lang):
    try:
        auth_key = current_app.config.get("DEEPL_API_KEY")
        if not auth_key:
            raise TranslationError("No se encontró la API de DeepL.")

        translator = deepl.Translator(auth_key)

        result = _retry_deepl_request(translator, text, target_lang)
        translated = getattr(result, "text", None)

        if not translated:
            raise TranslationError("API de DeepL no devolvió texto traducido.")

        return translated

    except deepl.exceptions.AuthorizationException as e:
        raise TranslationError(f"Error de autenticación con DeepL: {e}") from e

    except (deepl.exceptions.DeepLException, TimeoutError) as e:
        raise TranslationError(f"Fallo en DeepL tras varios intentos: {e}") from e

    except Exception as e:
        if isinstance(e, TranslationError):
            raise
        raise TranslationError(f"Fallo inesperado en la traducción: {e}") from e
