"""POST /chat: relay text to the Lex V2 bot. Owner: Member C."""
import os

from ecoguard_common import responses

_lex = None


def _client():
    global _lex
    if _lex is None:
        import boto3

        _lex = boto3.client("lexv2-runtime")
    return _lex


def _chat(event):
    body = responses.json_body(event)
    text = str(body.get("text", "")).strip()
    if not text:
        raise ValueError("text is required")
    bot_id = os.environ.get("LEX_BOT_ID")
    alias_id = os.environ.get("LEX_BOT_ALIAS_ID")
    if not bot_id or not alias_id:
        raise ConnectionError("chatbot is not configured yet (LexBotId / LexBotAliasId)")

    session_id = str(body.get("session_id") or responses.claims(event).get("sub") or "anonymous")
    reply = _client().recognize_text(
        botId=bot_id,
        botAliasId=alias_id,
        localeId=os.environ.get("LEX_LOCALE_ID", "en_US"),
        sessionId=session_id,
        text=text[:1000],
    )
    return {
        "messages": [m.get("content", "") for m in reply.get("messages", [])],
        "intent": reply.get("sessionState", {}).get("intent", {}).get("name"),
        "session_id": session_id,
    }


def handler(event, context):
    return responses.run(_chat, event)
