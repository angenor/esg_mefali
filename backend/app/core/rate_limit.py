"""Configuration du rate limiting SlowAPI pour l'API chat (FR-013).

Limite l'envoi de messages chat a 30 requetes par minute par utilisateur authentifie.
La cle est basee sur l'identifiant utilisateur (pas l'IP) pour eviter les faux positifs
lies aux NAT/partages de connexion frequents dans le contexte PME africaines.
"""

from fastapi import Request
from slowapi import Limiter


def get_user_id_from_request(request: Request) -> str:
    """Extraire l'identifiant utilisateur pour la cle de rate limiting.

    Invariant : tout endpoint decore par `@limiter.limit(...)` DOIT aussi
    declarer une dependance `Depends(get_current_user)`. `get_current_user`
    depose l'utilisateur dans `request.state.user` avant que le decorateur
    SlowAPI ne soit evalue. Si l'utilisateur est absent, on leve
    explicitement `RuntimeError` pour detecter au plus tot toute mauvaise
    configuration (pas de fallback IP silencieux — voir story 9.1
    « Pieges a eviter » : faux positifs garantis en NAT/connexions partagees).
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise RuntimeError(
            "get_user_id_from_request appele sans utilisateur authentifie. "
            "Les endpoints decores par @limiter.limit doivent declarer "
            "Depends(get_current_user) pour peupler request.state.user."
        )
    uid = getattr(user, "id", None)
    if uid is None:
        raise RuntimeError(
            "Utilisateur authentifie sans attribut `id` — invariant viole."
        )
    return str(uid)


limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=[],
    headers_enabled=True,
)
