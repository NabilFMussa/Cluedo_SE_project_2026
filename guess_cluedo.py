import random
from cluedo_card_setup import SUSPECTS, WEAPONS, ROOMS


def _emit(message, logger=None):
    if logger:
        logger(message)
    else:
        print(message)


def make_suggestion(suggester, s, w, r, all_players, logger=None):
    _emit(f"{suggester.name} suggests: {s} | {w} | {r}", logger)

    for p in all_players:
        if p.name == suggester.name or p.eliminated:
            continue

        matching = []
        for c in p.hand:
            if c.name.lower() in (s.lower(), w.lower(), r.lower()):
                matching.append(c)

        if not matching:
            continue

        shown = matching[0]
        _emit(f"{p.name} disproved the suggestion.", logger)
        suggester.mark(shown.name, note=f"held by {p.name}")
        return shown

    _emit("Nobody could disprove the suggestion.", logger)
    return None


def make_accusation(accuser, s, w, r, envelope, logger=None):
    _emit(f"{accuser.name} accuses: {s} | {w} | {r}", logger)

    if envelope.check(s, w, r):
        _emit(f"CORRECT! {accuser.name} wins!", logger)
        return True

    _emit(f"WRONG! {accuser.name} is eliminated.", logger)
    accuser.eliminated = True
    return False


def _unknown_cards(ai):
    unknown = {"suspect": [], "weapon": [], "room": []}
    for entry in ai.checklist:
        if not entry.marked:
            unknown[entry.card.category].append(entry.card.name)
    return unknown


def ai_turn(ai, all_players, envelope, current_room=None, logger=None, on_suggestion=None):
    _emit(f"--- {ai.name}'s turn (AI) ---", logger)

    unknown = _unknown_cards(ai)
    if len(unknown["suspect"]) == 1 and len(unknown["weapon"]) == 1 and len(unknown["room"]) == 1:
        return make_accusation(
            ai,
            unknown["suspect"][0],
            unknown["weapon"][0],
            unknown["room"][0],
            envelope,
            logger=logger,
        )

    suspect = random.choice(unknown["suspect"] or SUSPECTS)
    weapon = random.choice(unknown["weapon"] or WEAPONS)
    room = current_room or random.choice(unknown["room"] or ROOMS)

    if on_suggestion:
        on_suggestion(suspect, weapon, room)
    make_suggestion(ai, suspect, weapon, room, all_players, logger=logger)
    return False
