"""
guess_cluedo.py

Handles the suggestion and accusation logic for the game.
Also contains the AI turn logic which decides whether to
suggest or accuse based on what the AI has figured out so far.
"""

import random
from cluedo_card_setup import SUSPECTS, WEAPONS, ROOMS


def _emit(message, logger=None):
    """Prints a message to the terminal, or passes it to a logger if one is provided."""
    if logger:
        logger(message)
    else:
        print(message)


def make_suggestion(suggester, s, w, r, all_players, logger=None):
    """
    Makes a suggestion and goes around the table asking if anyone can disprove it.

    The first player (in turn order) who holds one of the suggested cards shows it
    to the suggester. That card then gets marked on the suggester's checklist.
    If nobody can disprove, nothing gets marked.

    Args:
        suggester: the Player making the suggestion
        s: suspected character name
        w: suspected weapon name
        r: suspected room name
        all_players: full list of all players in the game
        logger: optional function to redirect output (used by the UI layer)

    Returns:
        The Card that was shown, or None if nobody disproved.
    """
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
    """
    Makes a final accusation and checks it against the envelope.

    If correct, the accuser wins and the game ends.
    If wrong, the accuser is eliminated and can no longer take turns.

    Args:
        accuser: the Player making the accusation
        s: accused suspect name
        w: accused weapon name
        r: accused room name
        envelope: the Envelope object holding the real solution
        logger: optional function to redirect output

    Returns:
        True if the accusation was correct, False if not.
    """
    _emit(f"{accuser.name} accuses: {s} | {w} | {r}", logger)

    if envelope.check(s, w, r):
        _emit(f"CORRECT! {accuser.name} wins!", logger)
        return True

    _emit(f"WRONG! {accuser.name} is eliminated.", logger)
    accuser.eliminated = True
    return False


def _unknown_cards(ai):
    """
    Returns a dict of all unmarked cards on the AI's checklist, grouped by category.
    Used to figure out what the AI still doesn't know.
    """
    unknown = {"suspect": [], "weapon": [], "room": []}
    for entry in ai.checklist:
        if not entry.marked:
            unknown[entry.card.category].append(entry.card.name)
    return unknown


def ai_turn(ai, all_players, envelope, current_room=None, logger=None, on_suggestion=None):
    """
    Runs a single turn for an AI player.

    The AI checks its checklist to see what it still doesn't know.
    If there's only one option left in each category it goes for the accusation.
    Otherwise it makes a random suggestion from its remaining unknowns to narrow things down.

    Args:
        ai: the AI Player taking their turn
        all_players: full list of players in the game
        envelope: the Envelope with the real solution
        current_room: optional, the room the AI is currently in (not used in terminal version)
        logger: optional function to redirect output
        on_suggestion: optional callback before a suggestion is made (used by UI layer)

    Returns:
        True if the AI won, False otherwise.
    """
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
