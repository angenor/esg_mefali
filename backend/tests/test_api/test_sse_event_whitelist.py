"""Anti-regression : la whitelist d'events SSE de `send_message` doit
forwarder tous les types emis par `stream_graph_events`.

Contexte (bug 2026-04-15, correction initiale) : `stream_graph_events`
emettait bien un event `{type: "guided_tour", ...}` quand le tool
`trigger_guided_tour` etait appele, mais le filtre elif dans
`generate_sse` (fonction interne a `send_message` dans `app/api/chat.py`)
ne contenait que `token`, `tool_call_*`, `interactive_question*` et
`error`. L'event `guided_tour` etait silencieusement drop, jamais
forwarde au frontend — driver.js ne se lancait pas alors que les
tool_call_logs montraient un status success.

Extension BUG-2 post-fix (2026-04-15) : meme classe de bug pour
`profile_update` et `profile_completion`, yielded par `stream_graph_events`
lignes 258-262 quand le tool `update_company_profile` est appele, mais
absents de la whitelist. Consequence : les mises a jour de profil via le
chat ne propageaient pas d'event au frontend (cote client, `useChat.ts`
ecoute pourtant ces 2 types lignes 407 et 416 pour mettre a jour le
companyStore). Ajoutes a la whitelist + verrouilles ici.

Ce test verrouille la presence de tous les types critiques dans la
whitelist pour couper court a la re-apparition silencieuse de cette
classe de bug.
"""

from pathlib import Path

CHAT_API_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "api"
    / "chat.py"
)

_REQUIRED_EVENT_TYPES = (
    "token",
    "tool_call_start",
    "tool_call_end",
    "tool_call_error",
    "interactive_question",
    "interactive_question_resolved",
    "guided_tour",
    "profile_update",
    "profile_completion",
    "error",
)


def test_send_message_sse_whitelist_contains_required_event_types():
    """La fonction `generate_sse` doit forwarder tous les types d'events
    emis par `stream_graph_events`. Sans `guided_tour`, driver.js ne se
    lance pas alors que le backend logue un tool_call success — symptome
    muet tres difficile a diagnostiquer.
    """
    source = CHAT_API_PATH.read_text(encoding="utf-8")
    for event_type in _REQUIRED_EVENT_TYPES:
        token = f'"{event_type}"'
        assert token in source, (
            f"Type d'event SSE `{event_type}` absent de app/api/chat.py. "
            f"Verifie la whitelist dans `generate_sse` (fonction interne a "
            f"`send_message`) — un event emis par `stream_graph_events` "
            f"mais absent de cette whitelist est silencieusement drop."
        )
