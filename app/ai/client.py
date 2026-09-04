from openai import OpenAI

from app.config import settings

# O Gemini expõe um endpoint compatível com a API da OpenAI, então dá para
# reaproveitar o mesmo client/SDK apenas trocando a base_url e a chave.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def get_llm_client() -> tuple[OpenAI, str] | None:
    """Retorna (client, nome_do_modelo) para o provedor de IA configurado,
    ou None se nenhuma chave de API estiver disponível (cai no modo mock)."""
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAI(api_key=settings.openai_api_key), settings.openai_model

    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        return OpenAI(api_key=settings.gemini_api_key, base_url=GEMINI_BASE_URL), settings.gemini_model

    return None
