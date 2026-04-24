import random
from cluedo_card_setup import SUSPECTS, WEAPONS, ROOMS, setup_game
from guess_cluedo import make_suggestion, make_accusation, ai_turn


def pick(prompt, options):
    print(f"\n{prompt}")
    for i, o in enumerate(options):
        print(f"  {i+1}. {o}")
    while True:
        c = input("Enter number: ").strip()
        if c.isdigit() and 1 <= int(c) <= len(options):
            return options[int(c) - 1]
        print("  invalid")


def human_turn(human, all_players, envelope, label=None):
    print(f"\n--- {label or human.name}'s turn ---")

    action = pick("What do you want to do?", [
        "Make a suggestion",
        "Make an accusation",
        "View checklist",
        "End turn"
    ])

    if action == "View checklist":
        human.show_checklist()
        return False

    if action == "End turn":
        return False

    s = pick("Suspect:", SUSPECTS)
    w = pick("Weapon:", WEAPONS)
    r = pick("Room:", ROOMS)

    if action == "Make a suggestion":
        make_suggestion(human, s, w, r, all_players)
        human.show_checklist()
        return False

    # must be accusation at this point
    confirm = input("\nAre you sure? Type YES to confirm: ").strip()
    if confirm != "YES":
        print("Accusation cancelled.")
        return False

    return make_accusation(human, s, w, r, envelope)


def roll_for_order(players):
    print("\nRolling to decide turn order...")
    rolls = {}
    for p in players:
        rolls[p.name] = random.randint(1, 6)
        print(f"  {p.name} rolled: {rolls[p.name]}")
    return rolls


def resolve_ties(roll_dict):
    by_roll = {}
    for name, val in roll_dict.items():
        if val not in by_roll:
            by_roll[val] = []
        by_roll[val].append(name)

    final_order = []
    for val in sorted(by_roll.keys(), reverse=True):
        group = by_roll[val]
        if len(group) == 1:
            final_order.append(group[0])
        else:
            print(f"\n  Tie between {', '.join(group)}, re-rolling...")
            reroll = {}
            for name in group:
                reroll[name] = random.randint(1, 6)
                print(f"    {name} rolled: {reroll[name]}")
            final_order.extend(resolve_ties(reroll))

    return final_order


# Start of the main game loop

print("\nWelcome to Cluedo!\n")

while True:
    n = input("How many human players? (1-6): ").strip()
    if n.isdigit() and 1 <= int(n) <= 6:
        break
    print("  invalid")
num_humans = int(n)

chosen = []
for i in range(num_humans):
    available = [s for s in SUSPECTS if s not in chosen]
    chosen.append(pick(f"Player {i+1} pick your character:", available))

remaining = [s for s in SUSPECTS if s not in chosen]
random.shuffle(remaining)

if num_humans == 1:
    num_ai = 1
    print(f"\n  1 AI added ({remaining[0]}) so you have someone to play against.")
else:
    max_ai = min(len(remaining), 6 - num_humans)
    while True:
        a = input(f"How many AI opponents? (0-{max_ai}): ").strip()
        if a.isdigit() and 0 <= int(a) <= max_ai:
            break
        print("  invalid")
    num_ai = int(a)

all_names = chosen + remaining[:num_ai]
human_flags = [True] * num_humans + [False] * num_ai

players, envelope = setup_game(all_names, human_flags)

# give human players numbers if there's more than 1
human_numbers = {}
count = 1
for p in players:
    if p.is_human:
        human_numbers[p.name] = count
        count += 1

# show each human their hand
for p in players:
    if p.is_human:
        p.show_hand()

# dice roll for turn order
rolls = roll_for_order(players)
order = resolve_ties(rolls)
print(f"\nTurn order: {' -> '.join(order)}")

player_map = {p.name: p for p in players}
players = [player_map[n] for n in order]

# main loop
turn = 0
total_turns = 0
winner = None

while True:
    active = [p for p in players if not p.eliminated]
    if len(active) <= 1:
        print("\nNo more players left. Game over.")
        break

    current = players[turn % len(players)]
    turn += 1

    if current.eliminated:
        continue

    total_turns += 1

    if current.is_human:
        num = human_numbers.get(current.name)
        label = f"Player {num} - {current.name}" if num_humans > 1 else current.name
        won = human_turn(current, players, envelope, label=label)
    else:
        won = ai_turn(current, players, envelope)

    if won:
        winner = current
        break

print("\nGAME OVER")
print(f"Solution was: {envelope.suspect.name} | {envelope.weapon.name} | {envelope.room.name}")
print(f"Total turns: {total_turns}")
if winner:
    print(f"Winner: {winner.name}")

eliminated = [p.name for p in players if p.eliminated]
if eliminated:
    print(f"Eliminated: {', '.join(eliminated)}")
