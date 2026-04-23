import os

global_temperature = 0


def _is_openai_model(model_name):
    normalized = (model_name or "").lower()
    return normalized.startswith("gpt-") or normalized.startswith("o1") or normalized.startswith("o3") or normalized.startswith("o4")


def get_api_config(model_name):
    if _is_openai_model(model_name):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI-hosted models.")
        return {
            "api_key": api_key,
            "base_url": os.getenv("OPENAI_BASE_URL") or None,
            "provider": "openai",
        }

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for non-OpenAI hosted models.")
    return {
        "api_key": api_key,
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "provider": "openrouter",
    }
