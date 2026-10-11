"""Lex V2 fulfilment code hook. Owner: Member C.

Intents and slots are specified in docs/lex-bot.md.
"""
from ecoguard_common import search, tags as taglib

MAX_LINKS = 5


def _slot(slots, name):
    slot = (slots or {}).get(name)
    return ((slot or {}).get("value") or {}).get("interpretedValue")


def _describe(results, what):
    if not results:
        return f"I could not find any files for {what}."
    lines = [f"Found {len(results)} file(s) for {what}. Here are the most recent:"]
    for r in results[:MAX_LINKS]:
        tags = ", ".join(f"{k} x{v}" for k, v in sorted(r["tags"].items())) or "no tags"
        lines.append(f"- {tags}: {r['thumb_url'] or r['url']}")
    return "\n".join(lines)


def _find_species(slots):
    species = taglib.normalise_tag(_slot(slots, "Species") or "")
    count = int(float(_slot(slots, "MinCount") or 1))
    since = until = None
    day = _slot(slots, "Date")
    if day:
        since, until = search.day_range(day)
    results = search.find_by_tags({species: max(1, count)}, since, until)
    what = f"{species}" + (f" (at least {count})" if count > 1 else "") + (f" on {day}" if day else "")
    return _describe(results, what)


def _lost_pet(slots):
    species = taglib.normalise_tag(_slot(slots, "Species") or "")
    extra = [taglib.normalise_tag(v) for v in (_slot(slots, "Colour"), _slot(slots, "Breed")) if v]
    results = search.find_lost_pet([species], extra)
    return _describe(results, "a lost " + " ".join(extra + [species]))


def _close(event, intent, message, state="Fulfilled"):
    return {
        "sessionState": {
            "sessionAttributes": event.get("sessionState", {}).get("sessionAttributes", {}),
            "dialogAction": {"type": "Close"},
            "intent": {"name": intent.get("name"), "slots": intent.get("slots"), "state": state},
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }


def handler(event, context):
    intent = event["sessionState"]["intent"]
    slots = intent.get("slots") or {}
    try:
        if intent["name"] == "FindSpecies":
            return _close(event, intent, _find_species(slots))
        if intent["name"] == "LostPet":
            return _close(event, intent, _lost_pet(slots))
        return _close(event, intent, "Sorry, I can only search for species or lost pets.", "Failed")
    except ValueError as exc:
        return _close(event, intent, f"Sorry, I could not understand that: {exc}", "Failed")
