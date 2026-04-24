"""
cluedo_card_setup.py

Handles all the card and player setup for the game.
This includes creating the cards, dealing them out,
building each player's checklist, and picking the
secret envelope at the start of the game.
"""

import random
from dataclasses import dataclass, field

SUSPECTS = ["Miss Scarlett", "Col. Mustard", "Mrs. White", "Rev. Green", "Mrs. Peacock", "Prof. Plum"]
WEAPONS = ["Candlestick", "Knife", "Lead Pipe", "Revolver", "Rope", "Wrench"]
ROOMS = ["STUDY", "LIBRARY", "BILLIARD ROOM", "CONSERVATORY", "BALL ROOM", "KITCHEN", "DINING ROOM", "LOUNGE", "HALL"]


@dataclass
class Card:
    """Represents a single Cluedo card. Category is one of: suspect, weapon, room."""
    name: str
    category: str


@dataclass
class ChecklistEntry:
    """One row on a player's notepad. Marked means the card is accounted for."""
    card: Card
    marked: bool = False
    note: str = ""


@dataclass
class Player:
    """
    Represents a player in the game, human or AI.

    Attributes:
        name: the character name e.g. Miss Scarlett
        hand: cards dealt to this player
        checklist: the player's notepad tracking known/unknown cards
        is_human: False if this player is AI controlled
        eliminated: True if they made a wrong accusation
    """
    name: str
    hand: list = field(default_factory=list)
    checklist: list = field(default_factory=list)
    is_human: bool = True
    eliminated: bool = False

    def build_checklist(self, all_cards):
        """
        Sets up the checklist at the start of the game.
        Cards already in the player's hand get marked straight away.
        """
        hand_names = {c.name for c in self.hand}
        self.checklist = []
        for c in all_cards:
            already_have = c.name in hand_names
            self.checklist.append(ChecklistEntry(c, marked=already_have))

    def mark(self, name, note=""):
        """Marks a card on the checklist as known, with an optional note."""
        for e in self.checklist:
            if e.card.name.lower() == name.lower():
                e.marked = True
                e.note = note

    def show_checklist(self):
        """Prints the player's notepad to the terminal."""
        print(f"\n{self.name}'s Notepad")
        for cat in ("suspect", "weapon", "room"):
            print(f"  {cat.upper()}S")
            for e in self.checklist:
                if e.card.category == cat:
                    mark = "x" if e.marked else " "
                    note = f" <- {e.note}" if e.note else ""
                    print(f"    [{mark}] {e.card.name}{note}")
        print()

    def show_hand(self):
        """Prints the cards in this player's hand."""
        names = [c.name for c in self.hand]
        print(f"\n{self.name}'s cards: {', '.join(names)}")


@dataclass
class Envelope:
    """
    The secret solution envelope containing the murder suspect, weapon and room.
    Only revealed at the end of the game or when a correct accusation is made.
    """
    suspect: Card
    weapon: Card
    room: Card

    def check(self, s, w, r):
        """Returns True if the given suspect, weapon and room match the envelope."""
        return (self.suspect.name.lower() == s.lower()
            and self.weapon.name.lower() == w.lower()
            and self.room.name.lower() == r.lower())


def get_all_cards():
    """Builds and returns a full list of all Cluedo cards across all three categories."""
    all_cards = []
    for n in SUSPECTS:
        all_cards.append(Card(n, "suspect"))
    for n in WEAPONS:
        all_cards.append(Card(n, "weapon"))
    for n in ROOMS:
        all_cards.append(Card(n, "room"))
    return all_cards


def setup_game(names, human_flags):
    """
    Sets up a full game from scratch.

    Picks the three envelope cards randomly, shuffles the rest
    and deals them evenly to all players. Each player then gets
    a checklist built from the full card list.

    Args:
        names: list of player name strings
        human_flags: list of booleans, True means human, False means AI

    Returns:
        players: list of Player objects with hands and checklists filled in
        env: the Envelope containing the secret solution
    """
    all_cards = get_all_cards()

    suspects = [c for c in all_cards if c.category == "suspect"]
    weapons = [c for c in all_cards if c.category == "weapon"]
    rooms = [c for c in all_cards if c.category == "room"]

    # pick the 3 murder cards and stick em in the envelope
    env = Envelope(random.choice(suspects), random.choice(weapons), random.choice(rooms))

    # everything thats not in the envelope gets dealt out
    deck = [c for c in all_cards if c.name not in (env.suspect.name, env.weapon.name, env.room.name)]
    random.shuffle(deck)

    players = []
    for i in range(len(names)):
        players.append(Player(names[i], is_human=human_flags[i]))

    for i, card in enumerate(deck):
        players[i % len(players)].hand.append(card)

    for p in players:
        p.build_checklist(all_cards)

    return players, env
