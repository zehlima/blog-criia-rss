"""Farza operates with RSS and storage only until a reviewed code change."""


class AIDisabled(RuntimeError):
    code = 'FARZA_AI_DISABLED'


def require_ai():
    # Credentials or old environment flags must not silently re-enable inference.
    raise AIDisabled('FARZA_AI_DISABLED: IA desativada; RSS e consultas permanecem disponíveis.')
