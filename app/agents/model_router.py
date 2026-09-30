from app.core.config import settings


def resolve_model_name(requested_model: str | None) -> str:
    configured_models = settings.llm_models
    default_model = settings.llm_model_default
    normalized_model = (requested_model or "").strip()

    if not normalized_model:
        return default_model

    alias_match = configured_models.get(normalized_model.lower())
    if alias_match:
        return alias_match

    configured_values = set(configured_models.values())
    if normalized_model in configured_values:
        return normalized_model

    return default_model
