"""Main pygame version of the Cluedo project.

This file handles the board, turns, menus, movement, and most of the UI.
It ended up being the big one.
"""

import pygame
import sys
import random
import textwrap
from collections import deque

from cluedo_card_setup import ROOMS, SUSPECTS, WEAPONS, setup_game
from guess_cluedo import ai_turn, make_accusation, make_suggestion

pygame.init()

BOARD_IMG = "Assets_images/game board.png"
MASK_IMG = "Assets_images/board_mask.png"

CELL_SIZE = 20
UI_BAR_HEIGHT = 30
GRID_COLOR = (60, 60, 60)
SIDE_PANEL_WIDTH = 360
PANEL_BG = (28, 28, 28)
PANEL_ACCENT = (75, 75, 75)
TEXT_COLOR = (235, 235, 235)
MUTED_TEXT = (170, 170, 170)
DEFAULT_HUMAN_PLAYERS = {"Miss Scarlett"}
ENABLE_AI_PLAYERS = False
AI_TURN_DELAY_MS = 900

CHARACTER_ORDER = [
    "Miss Scarlett",
    "Col. Mustard",
    "Mrs. White",
    "Rev. Green",
    "Mrs. Peacock",
    "Prof. Plum"
]

CHARACTERS = {
    "Miss Scarlett": {"color": (255, 0, 0),    "position": (22, 1)},
    "Col. Mustard":  {"color": (255, 215, 0),  "position": (31, 9)},
    "Mrs. White":    {"color": (240, 240, 240),"position": (19, 30)},
    "Rev. Green":    {"color": (0, 128, 0),    "position": (13, 30)},
    "Mrs. Peacock":  {"color": (0, 0, 255),    "position": (2, 22)},
    "Prof. Plum":    {"color": (128, 0, 128),  "position": (2, 7)},
}

SECRET_PASSAGES = {
    "STUDY": "KITCHEN",
    "KITCHEN": "STUDY",
    "LOUNGE": "CONSERVATORY",
    "CONSERVATORY": "LOUNGE",
}

WEAPON_TOKEN_COLORS = {
    "Candlestick": (255, 215, 0),
    "Knife": (210, 210, 210),
    "Lead Pipe": (120, 140, 160),
    "Revolver": (90, 90, 90),
    "Rope": (170, 130, 85),
    "Wrench": (120, 220, 255),
}

WEAPON_TOKEN_LABELS = {
    "Candlestick": "Ca",
    "Knife": "Kn",
    "Lead Pipe": "LP",
    "Revolver": "Re",
    "Rope": "Ro",
    "Wrench": "Wr",
}

COLOR_TO_ROOM = {
    (255, 255, 255): "HALLWAY", (0, 255, 0): "STUDY",
    (0, 0, 255): "LIBRARY", (255, 0, 0): "BILLIARD ROOM",
    (0, 255, 255): "CONSERVATORY", (255, 0, 255): "BALL ROOM",
    (255, 255, 0): "KITCHEN", (128, 64, 0): "DINING ROOM",
    (128, 0, 128): "LOUNGE", (255, 128, 0): "HALL",
    (128, 128, 128): "CENTER", (255, 20, 147): "DOOR",
    (150, 0, 0): "START"
}

class CluedoGame:
    """Main controller for the pygame board game."""

    def __init__(self):
        try:
            self.board_image = pygame.image.load(BOARD_IMG)
            self.mask_image = pygame.image.load(MASK_IMG)
        except pygame.error:
            print("Error: Could not load images. Check your Assets_images folder.")
            sys.exit()
        
        self.board_width, self.board_height = self.board_image.get_size()
        self.screen = pygame.display.set_mode((self.board_width + SIDE_PANEL_WIDTH, self.board_height + UI_BAR_HEIGHT))
        pygame.display.set_caption("Cluedo Game Engine")

        self.grid_width = self.board_width // CELL_SIZE
        self.grid_height = self.board_height // CELL_SIZE

        self.font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 13)
        self.tiny_font = pygame.font.SysFont("Arial", 12)
        
        self.grid = self.create_grid()
        self.door_to_rooms = self.build_door_room_map()
        self.room_slots_by_type = self.build_room_slot_map()
        self.room_anchor_by_type = self.build_room_anchor_map()
        self.characters = {name: data.copy() for name, data in CHARACTERS.items()}
        self.active_character_names = CHARACTER_ORDER[:]
        self.show_rooms = False
        self.show_grid = False

        self.players = []
        self.player_by_name = {}
        self.turn_order = []
        self.current_turn_index = 0
        self.current_turn = CHARACTER_ORDER[0]
        self.envelope = None
        self.weapon_locations = {}
        self.message_log = []
        self.modal_state = None
        self.game_over = False
        self.winner = None
        self.pending_ai_turn = False
        self.ai_action_due_at = 0
        self.ai_enabled = False
        self.show_help_overlay = True
        self.has_suggested_this_turn = False
        self.awaiting_turn_handoff = False
        self.private_info_visible = False
        self.note_scroll_offset = 0
        self.game_state = "MENU"
        self.menu_player_count = 4
        self.menu_human_flags = {
            name: ((not ENABLE_AI_PLAYERS) or (name in DEFAULT_HUMAN_PLAYERS))
            for name in CHARACTER_ORDER
        }
        self.menu_cursor = 0

        self.reset_turn_state()

        self.sync_menu_selection()
        self.log_message("Choose players in the setup menu and press Enter to start.")

    def hide_private_view(self):
        """Hide hand/checklist info between turns."""
        self.awaiting_turn_handoff = False
        self.private_info_visible = False
        self.note_scroll_offset = 0

    def reset_turn_state(self):
        """Reset movement stuff for a fresh turn."""
        self.phase = "ROLL"
        self.dice_result = (0, 0)
        self.steps = 0
        self.reachable = set()
        self.reachable_rooms = set()

    def sync_menu_selection(self):
        """Clamp menu state so it stays in a sensible range."""
        self.menu_player_count = max(2, min(len(CHARACTER_ORDER), self.menu_player_count))
        self.menu_cursor = max(0, min(self.menu_cursor, self.menu_player_count + 1))
        for name in CHARACTER_ORDER:
            self.menu_human_flags.setdefault(name, True)

    def prepare_private_view(self):
        """Set up whether the next turn should begin with a handoff screen."""
        if not self.players or self.game_over:
            self.hide_private_view()
            return

        if self.current_player().is_human:
            self.awaiting_turn_handoff = True
            self.private_info_visible = False
        else:
            self.hide_private_view()

    def start_selected_game(self):
        """Start a new board game using whatever is picked in the menu."""
        self.sync_menu_selection()
        self.active_character_names = CHARACTER_ORDER[:self.menu_player_count]
        self.characters = {name: data.copy() for name, data in CHARACTERS.items()}
        self.players = []
        self.player_by_name = {}
        self.turn_order = []
        self.current_turn_index = 0
        self.current_turn = self.active_character_names[0]
        self.envelope = None
        self.weapon_locations = {}
        self.message_log = []
        self.modal_state = None
        self.game_over = False
        self.winner = None
        self.pending_ai_turn = False
        self.ai_action_due_at = 0
        self.has_suggested_this_turn = False
        self.reset_turn_state()
        self.hide_private_view()
        self.game_state = "PLAYING"
        self.place_spare_characters()
        self.setup_card_game()

    def return_to_menu(self):
        """Drop out of a running game and go back to setup."""
        self.game_state = "MENU"
        self.modal_state = None
        self.pending_ai_turn = False
        self.ai_action_due_at = 0
        self.reset_turn_state()
        self.hide_private_view()
        self.message_log = []
        self.log_message("Back in the setup menu. Adjust the players and press Enter to start.")

    def setup_card_game(self):
        """Create players, deal cards, and sync the board-side state."""
        names = CHARACTER_ORDER[:self.menu_player_count]
        human_flags = [self.menu_human_flags.get(name, True) for name in names]
        self.ai_enabled = any(not flag for flag in human_flags)
        self.players, self.envelope = setup_game(names, human_flags)

        player_map = {player.name: player for player in self.players}
        ordered_names = [name for name in CHARACTER_ORDER if name in player_map]
        self.players = [player_map[name] for name in ordered_names]
        self.player_by_name = {player.name: player for player in self.players}
        self.turn_order = ordered_names
        self.current_turn_index = 0
        self.current_turn = self.turn_order[0]
        self.setup_weapon_tokens()
        self.schedule_ai_turn()
        self.prepare_private_view()
        self.log_message("Miss Scarlett goes first.")

        humans = [player.name for player in self.players if player.is_human]
        ai_players = [player.name for player in self.players if not player.is_human]
        self.log_message("Card setup complete.")
        self.log_message(f"Players: {', '.join(names)}")
        self.log_message(f"Humans: {', '.join(humans) if humans else 'none'}")
        self.log_message(f"AI players: {', '.join(ai_players) if ai_players else 'none'}")
        self.log_message(f"Turn order: {' -> '.join(self.turn_order)}")
        self.log_message("Goal: solve the suspect, weapon, and room in the envelope.")
        self.log_message("Press H to show or hide the play guide.")
        self.log_message(f"It is now {self.current_turn}'s turn.")

    def roll_for_order(self, players):
        """Roll dice for turn order.

        Not used in the current board flow, but handy to keep around.
        """
        self.log_message("Rolling to decide turn order...")
        rolls = {}
        for player in players:
            rolls[player.name] = random.randint(1, 6)
            self.log_message(f"{player.name} rolled {rolls[player.name]}")
        return self.resolve_turn_ties(rolls)

    def resolve_turn_ties(self, roll_dict):
        """Re-roll tied turn order results until the tie is gone."""
        by_roll = {}
        for name, value in roll_dict.items():
            by_roll.setdefault(value, []).append(name)

        final_order = []
        for value in sorted(by_roll.keys(), reverse=True):
            group = by_roll[value]
            if len(group) == 1:
                final_order.append(group[0])
                continue

            self.log_message(f"Tie between {', '.join(group)}. Re-rolling...")
            reroll = {}
            for name in group:
                reroll[name] = random.randint(1, 6)
                self.log_message(f"{name} rolled {reroll[name]}")
            final_order.extend(self.resolve_turn_ties(reroll))

        return final_order

    def current_player(self):
        """Return the player whose turn it is right now."""
        return self.player_by_name[self.current_turn]

    def human_viewer(self):
        """Return a human player for UI fallbacks, if one exists."""
        for player in self.players:
            if player.is_human:
                return player
        return self.current_player()

    def players_from_current_turn(self):
        """Return players starting from the current turn order position."""
        ordered_names = self.turn_order[self.current_turn_index:] + self.turn_order[:self.current_turn_index]
        return [self.player_by_name[name] for name in ordered_names]

    def current_room_name(self, name=None):
        """Return the room a character is standing in, if any."""
        actor_name = name or self.current_turn
        gx, gy = self.characters[actor_name]["position"]
        cell = self.grid[gy][gx]
        return cell["type"] if cell["is_room"] else None

    def can_accuse_now(self):
        """Accusations are only allowed after a suggestion in this version."""
        return self.phase == "ACTION" and self.has_suggested_this_turn

    def schedule_ai_turn(self):
        """Queue the next AI turn with a small delay so it feels less abrupt."""
        if not self.ai_enabled or not self.players:
            self.pending_ai_turn = False
            self.ai_action_due_at = 0
            return

        self.pending_ai_turn = (not self.game_over) and (not self.current_player().is_human)
        self.ai_action_due_at = pygame.time.get_ticks() + AI_TURN_DELAY_MS if self.pending_ai_turn else 0

    def should_log_message(self, message):
        """Filter out noisy events from the side log."""
        text = str(message)
        quiet_prefixes = (
            "Rolling to decide turn order",
            "Players:",
            "Humans:",
            "AI players:",
            "Turn order:",
            "Goal:",
            "Press H to show or hide the play guide.",
            "It is now ",
        )
        quiet_contains = (
            " rolled ",
            " moved to (",
            " entered ",
            "Door options:",
            " ends their turn.",
            " used secret passage:",
            " could not move this turn.",
            "Press A to accuse or S to end your turn.",
        )

        if any(text.startswith(prefix) for prefix in quiet_prefixes):
            return False
        if any(token in text for token in quiet_contains):
            return False
        return True

    def log_style(self, message):
        """Pick a label and colour for a log line."""
        text = str(message)
        if "suggests:" in text:
            return "Suggestion", (120, 220, 255)
        if "disproved" in text or "Nobody could disprove" in text:
            return "Clue", (180, 220, 120)
        if "accuses:" in text:
            return "Accusation", (255, 205, 120)
        if "CORRECT!" in text:
            return "Win", (120, 240, 150)
        if "WRONG!" in text or "Game over" in text:
            return "Result", (255, 150, 150)
        return "Info", TEXT_COLOR

    def log_message(self, message):
        """Store one message in the short rolling event log."""
        text = str(message)
        if not self.should_log_message(text):
            return
        label, color = self.log_style(text)
        self.message_log.append({"label": label, "text": text, "color": color})
        self.message_log = self.message_log[-10:]

    def classify_cell(self, gx, gy):
        """Classify a grid cell by sampling the whole block, not one pixel."""
        color_counts = {}
        start_x = gx * CELL_SIZE
        start_y = gy * CELL_SIZE

        for py in range(start_y, min(start_y + CELL_SIZE, self.board_height)):
            for px in range(start_x, min(start_x + CELL_SIZE, self.board_width)):
                color = self.mask_image.get_at((px, py))[:3]
                color_counts[color] = color_counts.get(color, 0) + 1

        door_pixels = color_counts.get((255, 20, 147), 0)
        start_pixels = color_counts.get((150, 0, 0), 0)

        if door_pixels >= 100:
            return "DOOR"
        if start_pixels >= 100:
            return "START"

        ranked_colors = sorted(
            (
                (count, color)
                for color, count in color_counts.items()
                if color in COLOR_TO_ROOM and color != (0, 0, 0)
            ),
            reverse=True,
        )
        if ranked_colors:
            return COLOR_TO_ROOM[ranked_colors[0][1]]
        return "WALL"

    def create_grid(self):
        """Build the board grid from the painted mask image."""
        grid = []
        for gy in range(self.grid_height):
            row = []
            for gx in range(self.grid_width):
                room_type = self.classify_cell(gx, gy)
                row.append({
                    "type": room_type,
                    "walkable": room_type in ["HALLWAY", "DOOR", "START"],
                    "is_room": room_type not in ["HALLWAY", "WALL", "DOOR", "START", "CENTER"]
                })
            grid.append(row)
        return grid

    def next_turn(self):
        """Advance to the next active player and reset the turn state."""
        active_players = [player for player in self.players if not player.eliminated]
        if len(active_players) <= 1:
            self.game_over = True
            self.winner = active_players[0] if active_players else None
            if self.winner:
                self.log_message(f"{self.winner.name} is the last player standing.")
            else:
                self.log_message("No active players remain. Game over.")
            return

        for _ in range(len(self.turn_order)):
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            next_name = self.turn_order[self.current_turn_index]
            if not self.player_by_name[next_name].eliminated:
                self.current_turn = next_name
                break

        self.phase = "ROLL"
        self.dice_result = (0, 0)
        self.steps = 0
        self.reachable = set()
        self.reachable_rooms = set()
        self.modal_state = None
        self.has_suggested_this_turn = False
        self.schedule_ai_turn()
        self.prepare_private_view()
        self.log_message(f"It is now {self.current_turn}'s turn.")

    def build_door_room_map(self):
        """Work out which rooms each door tile connects to."""
        door_map = {}
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                if self.grid[gy][gx]["type"] != "DOOR":
                    continue
                connected = set()
                for dx, dy in directions:
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        cell = self.grid[ny][nx]
                        if cell["is_room"]:
                            connected.add(cell["type"])
                door_map[(gx, gy)] = connected
        return door_map

    def build_room_slot_map(self):
        """Pick a few room tiles that are decent for players and weapons."""
        room_cells = {}
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                cell = self.grid[gy][gx]
                if cell["is_room"]:
                    room_cells.setdefault(cell["type"], []).append((gx, gy))

        slot_map = {}
        for room_name, cells in room_cells.items():
            center_x = sum(gx for gx, _ in cells) / len(cells)
            center_y = sum(gy for _, gy in cells) / len(cells)
            ranked = sorted(
                cells,
                key=lambda pos: (
                    abs(pos[0] - center_x) + abs(pos[1] - center_y),
                    abs(pos[0] - center_x),
                    abs(pos[1] - center_y),
                ),
            )

            chosen = []
            for cell in ranked:
                if all(abs(cell[0] - sx) + abs(cell[1] - sy) >= 2 for sx, sy in chosen):
                    chosen.append(cell)
                if len(chosen) >= 8:
                    break

            for cell in ranked:
                if len(chosen) >= 8:
                    break
                if cell not in chosen:
                    chosen.append(cell)

            slot_map[room_name] = chosen or ranked[:1]

        return slot_map

    def build_room_anchor_map(self):
        """Keep one fallback tile per room."""
        return {room_name: slots[0] for room_name, slots in self.room_slots_by_type.items()}

    def get_available_room_slot(self, room_name, moving_name=None):
        """Find a free-ish slot in a room for a character token."""
        slots = self.room_slots_by_type.get(room_name, [self.room_anchor_by_type.get(room_name)])
        occupied = set()
        for name, data in self.characters.items():
            if name == moving_name:
                continue
            gx, gy = data["position"]
            cell = self.grid[gy][gx]
            if cell["is_room"] and cell["type"] == room_name:
                occupied.add((gx, gy))

        for slot in slots:
            if slot not in occupied:
                return slot
        return slots[0]

    def place_character_in_room(self, character_name, room_name):
        """Move a character token into one of the chosen room slots."""
        if character_name in self.characters and room_name in self.room_anchor_by_type:
            self.characters[character_name]["position"] = self.get_available_room_slot(room_name, moving_name=character_name)

    def place_spare_characters(self):
        """Park unused characters in rooms so the board does not look empty."""
        spare_names = [name for name in CHARACTER_ORDER if name not in self.active_character_names]
        spare_rooms = ROOMS[:]
        random.shuffle(spare_rooms)

        for index, name in enumerate(spare_names):
            room_name = spare_rooms[index % len(spare_rooms)]
            self.place_character_in_room(name, room_name)

    def setup_weapon_tokens(self):
        """Scatter weapon tokens into rooms at the start of the game."""
        available_rooms = ROOMS[:]
        random.shuffle(available_rooms)
        self.weapon_locations = {
            weapon: room_name for weapon, room_name in zip(WEAPONS, available_rooms)
        }

    def move_suggestion_tokens(self, suspect_name, weapon_name, room_name):
        """Move the suggested suspect and weapon into the named room."""
        self.move_suspect_into_room(suspect_name, room_name)
        self.weapon_locations[weapon_name] = room_name

    def draw_weapons(self, y_off):
        """Draw little weapon markers inside the rooms."""
        for room_name in ROOMS:
            weapons_here = [weapon for weapon in WEAPONS if self.weapon_locations.get(weapon) == room_name]
            if not weapons_here:
                continue

            slots = list(reversed(self.room_slots_by_type.get(room_name, [self.room_anchor_by_type.get(room_name)])))
            for idx, weapon_name in enumerate(weapons_here):
                slot = slots[idx % len(slots)]
                center = (
                    slot[0] * CELL_SIZE + CELL_SIZE // 2,
                    slot[1] * CELL_SIZE + CELL_SIZE // 2 + y_off,
                )
                color = WEAPON_TOKEN_COLORS.get(weapon_name, (220, 220, 220))
                pygame.draw.circle(self.screen, color, center, 7)
                pygame.draw.circle(self.screen, (20, 20, 20), center, 7, 1)

                label = WEAPON_TOKEN_LABELS.get(weapon_name, weapon_name[:2])
                text = self.tiny_font.render(label, True, (20, 20, 20))
                self.screen.blit(text, (center[0] - text.get_width() // 2, center[1] - text.get_height() // 2))

    def is_occupied_by_other(self, gx, gy):
        """Return True when another active player is already on that tile."""
        for name in self.active_character_names:
            data = self.characters[name]
            if name != self.current_turn and data["position"] == (gx, gy):
                return True
        return False

    def current_door_rooms(self):
        """Return rooms reachable right now from the current door tile."""
        gx, gy = self.characters[self.current_turn]["position"]
        if self.steps < 1:
            return set()
        if self.grid[gy][gx]["type"] != "DOOR":
            return set()
        return set(self.door_to_rooms.get((gx, gy), set()))

    def current_secret_passage_destination(self):
        """Return the paired room if the player is in a passage room."""
        gx, gy = self.characters[self.current_turn]["position"]
        current_cell = self.grid[gy][gx]
        if not current_cell["is_room"]:
            return None
        return SECRET_PASSAGES.get(current_cell["type"])

    def shortest_walk_distance(self, start, goal, max_steps):
        """Find a shortest hallway path, including stepping out of a room."""
        if start == goal:
            return 0

        occupied = {
            self.characters[name]["position"]
            for name in self.active_character_names
            if name != self.current_turn
        }

        queue = deque()
        visited = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        start_gx, start_gy = start
        start_cell = self.grid[start_gy][start_gx]

        if start_cell["is_room"]:
            room_type = start_cell["type"]
            for (dgx, dgy), rooms in self.door_to_rooms.items():
                if room_type not in rooms or (dgx, dgy) in occupied:
                    continue
                if max_steps < 1:
                    continue
                if (dgx, dgy) == goal:
                    return 1
                visited.add((dgx, dgy))
                queue.append((dgx, dgy, 1))
        else:
            visited.add(start)
            queue.append((start_gx, start_gy, 0))

        while queue:
            gx, gy, dist = queue.popleft()
            if dist >= max_steps:
                continue

            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                    continue
                if (nx, ny) in visited:
                    continue

                cell = self.grid[ny][nx]
                if not cell["walkable"]:
                    continue
                if (nx, ny) in occupied:
                    continue

                ndist = dist + 1
                if (nx, ny) == goal:
                    return ndist

                visited.add((nx, ny))
                queue.append((nx, ny, ndist))

        return None

    def open_suggestion_dialog(self, room_name=None):
        """Open the suggestion modal for the current room."""
        room_name = room_name or self.current_room_name()
        if not room_name:
            self.log_message("You need to be inside a room to make a suggestion.")
            return
        if self.has_suggested_this_turn:
            self.log_message("You can only make one suggestion per turn.")
            return

        self.modal_state = {
            "type": "suggestion",
            "field": 0,
            "room": room_name,
            "suspect_index": 0,
            "weapon_index": 0,
        }

    def open_accusation_dialog(self):
        """Open the accusation modal if the current turn allows it."""
        if not self.can_accuse_now():
            self.log_message("You can only accuse right after making a suggestion.")
            return

        self.modal_state = {
            "type": "accusation",
            "field": 0,
            "suspect_index": 0,
            "weapon_index": 0,
            "room_index": 0,
        }

    def move_suspect_into_room(self, suspect_name, room_name):
        """Pull the named suspect token into a room after a suggestion."""
        self.place_character_in_room(suspect_name, room_name)

    def submit_suggestion(self):
        """Send the current suggestion through the card logic."""
        if not self.modal_state or self.modal_state["type"] != "suggestion":
            return

        player = self.current_player()
        room_name = self.modal_state["room"]
        suspect = SUSPECTS[self.modal_state["suspect_index"]]
        weapon = WEAPONS[self.modal_state["weapon_index"]]

        self.move_suggestion_tokens(suspect, weapon, room_name)
        make_suggestion(
            player,
            suspect,
            weapon,
            room_name,
            self.players_from_current_turn(),
            logger=self.log_message,
        )
        self.has_suggested_this_turn = True
        self.modal_state = None
        self.phase = "ACTION"
        self.log_message("Press A to accuse or S to end your turn.")

    def submit_accusation(self):
        """Resolve the accusation currently selected in the modal."""
        if not self.modal_state or self.modal_state["type"] != "accusation":
            return

        player = self.current_player()
        suspect = SUSPECTS[self.modal_state["suspect_index"]]
        weapon = WEAPONS[self.modal_state["weapon_index"]]
        room_name = ROOMS[self.modal_state["room_index"]]

        won = make_accusation(player, suspect, weapon, room_name, self.envelope, logger=self.log_message)
        self.modal_state = None

        if won:
            self.game_over = True
            self.winner = player
            self.log_message(
                f"Solution: {self.envelope.suspect.name} | {self.envelope.weapon.name} | {self.envelope.room.name}"
            )
            return

        self.next_turn()

    def pick_ai_room(self, player, reachable_rooms):
        """Have the AI prefer rooms it still knows less about."""
        unknown_rooms = [
            entry.card.name
            for entry in player.checklist
            if entry.card.category == "room" and not entry.marked
        ]
        preferred = [room for room in reachable_rooms if room in unknown_rooms]
        return random.choice(preferred or list(reachable_rooms))

    def run_ai_turn(self):
        """Handle one full AI turn on the board."""
        if self.game_over:
            return

        player = self.current_player()
        if player.eliminated:
            self.next_turn()
            return

        room_name = self.current_room_name(player.name)
        if room_name:
            won = ai_turn(
                player,
                self.players_from_current_turn(),
                self.envelope,
                current_room=room_name,
                logger=self.log_message,
                on_suggestion=self.move_suggestion_tokens,
            )
            self.has_suggested_this_turn = True
            if won:
                self.game_over = True
                self.winner = player
                self.log_message(
                    f"Solution: {self.envelope.suspect.name} | {self.envelope.weapon.name} | {self.envelope.room.name}"
                )
                return
            self.next_turn()
            return

        self.roll_dice()
        gx, gy = self.characters[self.current_turn]["position"]
        reachable, reachable_rooms = self.compute_reachable(gx, gy, self.steps)

        if reachable_rooms:
            chosen_room = self.pick_ai_room(player, reachable_rooms)
            destination = self.room_anchor_by_type.get(chosen_room)
            if destination:
                self.characters[self.current_turn]["position"] = destination
                self.phase = "ACTION"
                self.steps = 0
                self.reachable = set()
                self.reachable_rooms = set()
                self.log_message(f"{player.name} entered {chosen_room}.")
                won = ai_turn(
                    player,
                    self.players_from_current_turn(),
                    self.envelope,
                    current_room=chosen_room,
                    logger=self.log_message,
                    on_suggestion=self.move_suggestion_tokens,
                )
                self.has_suggested_this_turn = True
                if won:
                    self.game_over = True
                    self.winner = player
                    self.log_message(
                        f"Solution: {self.envelope.suspect.name} | {self.envelope.weapon.name} | {self.envelope.room.name}"
                    )
                    return
                self.next_turn()
                return

        if reachable:
            door_targets = [pos for pos in reachable if self.grid[pos[1]][pos[0]]["type"] == "DOOR"]
            target = random.choice(door_targets or list(reachable))
            distance = self.shortest_walk_distance((gx, gy), target, self.steps) or 0
            self.characters[self.current_turn]["position"] = target
            self.steps = max(self.steps - distance, 0)
            cell_type = self.grid[target[1]][target[0]]["type"]
            self.log_message(f"{player.name} moved to ({target[0]},{target[1]}) [{cell_type}].")
        else:
            self.log_message(f"{player.name} could not move this turn.")

        self.next_turn()

    def roll_dice(self):
        """Roll two dice and switch the turn into move mode."""
        if self.phase != "ROLL":
            return
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        self.dice_result = (d1, d2)
        self.steps = d1 + d2
        gx, gy = self.characters[self.current_turn]["position"]
        self.reachable, _ = self.compute_reachable(gx, gy, self.steps)
        self.reachable_rooms = self.current_door_rooms()
        self.phase = "MOVE"
        self.log_message(f"{self.current_turn} rolled {d1} + {d2} = {self.steps}")

    def compute_reachable(self, start_gx, start_gy, steps):
        """Work out reachable hallway tiles and room entries for this move."""
        occupied = {
            self.characters[name]["position"]
            for name in self.active_character_names
            if name != self.current_turn
        }

        reachable = set()
        reachable_rooms = set()
        visited = {}  # (gx, gy) -> max steps_remaining when reached
        queue = deque()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        start_cell = self.grid[start_gy][start_gx]

        if start_cell["is_room"]:
            room_type = start_cell["type"]
            for (dgx, dgy), rooms in self.door_to_rooms.items():
                if room_type in rooms and steps >= 1 and (dgx, dgy) not in occupied:
                    rem = steps - 1
                    if (dgx, dgy) not in visited or visited[(dgx, dgy)] < rem:
                        visited[(dgx, dgy)] = rem
                        queue.append((dgx, dgy, rem))
                        reachable.add((dgx, dgy))
        else:
            # Otherwise just start from the tile they're already on.
            visited[(start_gx, start_gy)] = steps
            queue.append((start_gx, start_gy, steps))

        while queue:
            gx, gy, remaining = queue.popleft()

            if visited.get((gx, gy), -1) > remaining:
                continue

            cell = self.grid[gy][gx]

            if cell["type"] == "DOOR" and remaining >= 1:
                for room_type in self.door_to_rooms.get((gx, gy), set()):
                    reachable_rooms.add(room_type)

            if remaining == 0:
                continue

            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                    continue
                ncell = self.grid[ny][nx]
                if not ncell["walkable"]:
                    continue
                if (nx, ny) in occupied:
                    continue
                rem = remaining - 1
                if (nx, ny) not in visited or visited[(nx, ny)] < rem:
                    visited[(nx, ny)] = rem
                    queue.append((nx, ny, rem))
                    reachable.add((nx, ny))

        return reachable, reachable_rooms

    def skip_move(self):
        """End the turn early or skip the rest of movement."""
        if self.phase not in ["ROLL", "MOVE", "ACTION"]:
            return
        self.log_message(f"{self.current_turn} ends their turn.")
        self.next_turn()

    def use_secret_passage(self):
        """Use a corner-room secret passage if the player can."""
        if self.phase not in ["ROLL", "MOVE"]:
            self.log_message("Use the secret passage before ending your turn.")
            return

        gx, gy = self.characters[self.current_turn]["position"]
        current_cell = self.grid[gy][gx]
        if not current_cell["is_room"]:
            self.log_message("You must be inside Study, Kitchen, Lounge, or Conservatory to use a secret passage.")
            return

        source_room = current_cell["type"]
        destination_room = self.current_secret_passage_destination()
        if not destination_room:
            self.log_message("This room has no secret passage.")
            return

        destination_pos = self.get_available_room_slot(destination_room, moving_name=self.current_turn)
        if not destination_pos:
            self.log_message(f"Could not find destination room tile for {destination_room}.")
            return

        self.characters[self.current_turn]["position"] = destination_pos
        self.reachable = set()
        self.reachable_rooms = set()
        self.steps = 0
        self.log_message(f"{self.current_turn} used secret passage: {source_room} -> {destination_room}")
        self.next_turn()

    def handle_move(self, target_gx, target_gy):
        """Try to move the current player to the chosen board cell."""
        if self.phase != "MOVE":
            if self.phase == "ACTION":
                self.log_message("Use J to suggest, A to accuse, or S to end your turn.")
            else:
                self.log_message("Roll the dice first! (Press SPACE)")
            return

        if not (0 <= target_gx < self.grid_width and 0 <= target_gy < self.grid_height):
            return

        char = self.characters[self.current_turn]
        current_gx, current_gy = char["position"]
        current_cell = self.grid[current_gy][current_gx]
        target_cell = self.grid[target_gy][target_gx]

        if target_cell["is_room"]:
            if self.steps < 1:
                self.log_message("No movement left to enter a room.")
                return
            if current_cell["type"] != "DOOR":
                self.log_message("You must stand on a door tile before entering a room.")
                return
            connected_rooms = self.door_to_rooms.get((current_gx, current_gy), set())
            if target_cell["type"] not in connected_rooms:
                self.log_message(f"This door does not lead to {target_cell['type']}!")
                return

            destination = self.get_available_room_slot(target_cell["type"], moving_name=self.current_turn)
            char["position"] = destination or (target_gx, target_gy)
            self.steps = 0
            self.reachable = set()
            self.reachable_rooms = set()
            self.phase = "ACTION"
            self.log_message(f"Moved {self.current_turn} into {target_cell['type']}")
            if self.current_player().is_human:
                self.open_suggestion_dialog(target_cell["type"])
            return

        if not target_cell["walkable"]:
            self.log_message("That tile is not walkable.")
            return
        if self.is_occupied_by_other(target_gx, target_gy):
            self.log_message("That square is occupied.")
            return
        if (target_gx, target_gy) not in self.reachable:
            self.log_message("Target is out of range for your remaining movement.")
            return

        distance = self.shortest_walk_distance((current_gx, current_gy), (target_gx, target_gy), self.steps)
        if distance is None:
            self.log_message("No valid path to that tile.")
            return

        char["position"] = (target_gx, target_gy)
        self.steps -= distance
        self.log_message(f"{self.current_turn} moved {distance} step(s).")

        if self.steps <= 0:
            self.reachable = set()
            self.reachable_rooms = set()
            self.phase = "ACTION"
            if self.current_room_name():
                self.open_suggestion_dialog(self.current_room_name())
            else:
                self.log_message("Use J to suggest, A to accuse, or S to end your turn.")
            return

        next_gx, next_gy = char["position"]
        self.reachable, self.reachable_rooms = self.compute_reachable(next_gx, next_gy, self.steps)

    def draw_event_log_panel(self, log_rect, accent_color):
        """Draw the compact event log in the side panel."""
        pygame.draw.rect(self.screen, (22, 22, 22), log_rect, border_radius=6)
        pygame.draw.rect(self.screen, PANEL_ACCENT, log_rect, 1, border_radius=6)
        self.screen.blit(self.small_font.render("Event Log", True, accent_color), (log_rect.x + 8, log_rect.y + 6))

        if not self.message_log:
            self.screen.blit(self.tiny_font.render("No key events yet.", True, MUTED_TEXT), (log_rect.x + 8, log_rect.y + 28))
            return

        wrap_width = max(18, (log_rect.width - 24) // 7)
        rendered_entries = []
        for entry in self.message_log[-8:]:
            if isinstance(entry, dict):
                label = entry.get("label", "Info")
                text = entry.get("text", "")
                color = entry.get("color", TEXT_COLOR)
            else:
                label, text, color = "Info", str(entry), TEXT_COLOR
            rendered_entries.append((label, textwrap.wrap(text, width=wrap_width) or [text], color))

        max_lines = max(1, (log_rect.height - 34) // 14)
        selected = []
        used = 0
        for label, lines, color in reversed(rendered_entries):
            needed = 1 + len(lines) + 1
            if selected and used + needed > max_lines:
                break
            selected.append((label, lines, color))
            used += needed

        y = log_rect.y + 28
        for label, lines, color in reversed(selected):
            self.screen.blit(self.tiny_font.render(label, True, color), (log_rect.x + 8, y))
            y += 14
            for line in lines:
                self.screen.blit(self.tiny_font.render(line, True, TEXT_COLOR), (log_rect.x + 12, y))
                y += 13
            y += 4

    def draw_private_info_panel(self, current_player, left_x, y, panel_height, accent_color):
        """Draw hand and checklist info for the active human player."""
        if self.awaiting_turn_handoff and current_player.is_human:
            handoff_lines = [
                f"Pass to {current_player.name}.",
                "Press Enter when they are ready.",
                "Private info stays hidden until V is pressed.",
            ]
            for line in handoff_lines:
                for wrapped in textwrap.wrap(line, width=40):
                    self.screen.blit(self.small_font.render(wrapped, True, TEXT_COLOR), (left_x, y))
                    y += 18
            return

        if not current_player.is_human:
            self.screen.blit(self.small_font.render("AI turn in progress.", True, TEXT_COLOR), (left_x, y))
            y += 20
            self.screen.blit(self.tiny_font.render("Private notes stay hidden on AI turns.", True, MUTED_TEXT), (left_x, y))
            return

        if not self.private_info_visible:
            hidden_lines = [
                "Private info is hidden.",
                "Press V to reveal this player's hand and notes.",
            ]
            for line in hidden_lines:
                for wrapped in textwrap.wrap(line, width=40):
                    self.screen.blit(self.small_font.render(wrapped, True, TEXT_COLOR), (left_x, y))
                    y += 18
            return

        viewer = current_player
        self.screen.blit(self.small_font.render(f"{viewer.name}'s Hand", True, accent_color), (left_x, y))
        y += 18
        for card in viewer.hand:
            self.screen.blit(self.tiny_font.render(f"- {card.name}", True, TEXT_COLOR), (left_x + 4, y))
            y += 14

        y += 6
        self.screen.blit(self.small_font.render("Detective Notes", True, accent_color), (left_x, y))
        y += 18

        notes_top = y
        notes_bottom = panel_height - 18
        available_note_lines = max(1, (notes_bottom - notes_top - 10) // 13)
        note_lines = []
        for category in ("suspect", "weapon", "room"):
            note_lines.append((category.title() + "s", MUTED_TEXT, 0))
            for entry in viewer.checklist:
                if entry.card.category != category:
                    continue
                status = "x" if entry.marked else " "
                note = f" - {entry.note}" if entry.note else ""
                line = f"[{status}] {entry.card.name}{note}"
                for wrapped in textwrap.wrap(line, width=36):
                    note_lines.append((wrapped, TEXT_COLOR, 6))

        max_offset = max(0, len(note_lines) - available_note_lines)
        self.note_scroll_offset = max(0, min(self.note_scroll_offset, max_offset))
        visible_lines = note_lines[self.note_scroll_offset:self.note_scroll_offset + available_note_lines]

        for text, color, indent in visible_lines:
            self.screen.blit(self.tiny_font.render(text, True, color), (left_x + indent, y))
            y += 13

        if max_offset > 0:
            scroll_hint = f"Notes scroll: {self.note_scroll_offset + 1}-{self.note_scroll_offset + len(visible_lines)} / {len(note_lines)}"
            self.screen.blit(self.tiny_font.render(scroll_hint, True, MUTED_TEXT), (left_x, notes_bottom - 12))

    def draw_side_panel(self):
        """Draw the right-side gameplay panel."""
        panel_x = self.board_width
        panel_height = self.board_height + UI_BAR_HEIGHT
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, SIDE_PANEL_WIDTH, panel_height))
        pygame.draw.line(self.screen, PANEL_ACCENT, (panel_x, 0), (panel_x, panel_height), 2)

        y = 10
        accent_color = (255, 215, 0)

        header = self.font.render("Gameplay Panel", True, accent_color)
        self.screen.blit(header, (panel_x + 12, y))
        y += 26

        if not self.players:
            self.screen.blit(self.small_font.render("Set up the players to begin.", True, TEXT_COLOR), (panel_x + 12, y))
            return

        current_player = self.current_player()
        info_lines = [
            f"Current: {current_player.name}",
            f"Role: {'Human' if current_player.is_human else 'AI'}",
            f"Phase: {self.phase}",
            f"Room: {self.current_room_name() or 'Hallway'}",
        ]
        for line in info_lines:
            self.screen.blit(self.small_font.render(line, True, TEXT_COLOR), (panel_x + 12, y))
            y += 18

        y += 4
        self.screen.blit(self.small_font.render("Controls", True, accent_color), (panel_x + 12, y))
        y += 18
        controls = [
            "SPACE roll   S end turn",
            "J suggest    A accuse",
            "P passage    V private info",
            "G/R overlays H help guide",
        ]
        for line in controls:
            self.screen.blit(self.tiny_font.render(line, True, MUTED_TEXT), (panel_x + 12, y))
            y += 16

        left_x = panel_x + 12
        column_top = y + 6
        log_height = 180
        log_rect = pygame.Rect(panel_x + 12, panel_height - log_height - 10, SIDE_PANEL_WIDTH - 24, log_height)

        self.draw_event_log_panel(log_rect, accent_color)
        self.draw_private_info_panel(current_player, left_x, column_top, log_rect.y - 4, accent_color)

    def draw_modal(self):
        """Draw the suggestion or accusation modal when one is open."""
        if not self.modal_state:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        box_w = 430
        box_h = 220 if self.modal_state["type"] == "accusation" else 190
        box_x = (self.board_width - box_w) // 2
        box_y = UI_BAR_HEIGHT + (self.board_height - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (36, 36, 36), box_rect)
        pygame.draw.rect(self.screen, (210, 210, 210), box_rect, 2)

        title = "Make a Suggestion" if self.modal_state["type"] == "suggestion" else "Make an Accusation"
        self.screen.blit(self.font.render(title, True, (255, 215, 0)), (box_x + 16, box_y + 14))
        self.screen.blit(
            self.tiny_font.render("Use arrow keys, Enter to confirm, Esc to cancel", True, TEXT_COLOR),
            (box_x + 16, box_y + 42),
        )

        lines = []
        if self.modal_state["type"] == "suggestion":
            lines = [
                ("Suspect", SUSPECTS[self.modal_state["suspect_index"]]),
                ("Weapon", WEAPONS[self.modal_state["weapon_index"]]),
                ("Room", self.modal_state["room"] + " (current room)"),
            ]
        else:
            lines = [
                ("Suspect", SUSPECTS[self.modal_state["suspect_index"]]),
                ("Weapon", WEAPONS[self.modal_state["weapon_index"]]),
                ("Room", ROOMS[self.modal_state["room_index"]]),
            ]

        y = box_y + 78
        selectable_fields = 2 if self.modal_state["type"] == "suggestion" else 3
        for idx, (label, value) in enumerate(lines):
            is_selected = idx == self.modal_state["field"] and idx < selectable_fields
            color = (120, 220, 255) if is_selected else TEXT_COLOR
            prefix = "> " if is_selected else "  "
            text = self.small_font.render(f"{prefix}{label}: {value}", True, color)
            self.screen.blit(text, (box_x + 20, y))
            y += 28

    def draw_menu_overlay(self):
        """Draw the setup menu over the board."""
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        box_w = 560
        box_h = 320
        box_x = (self.board_width - box_w) // 2
        box_y = UI_BAR_HEIGHT + 28
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (34, 34, 34), box_rect)
        pygame.draw.rect(self.screen, (210, 210, 210), box_rect, 2)

        self.screen.blit(self.font.render("Cluedo Setup", True, (255, 215, 0)), (box_x + 16, box_y + 14))
        self.screen.blit(
            self.tiny_font.render("Up/Down: select  Left/Right: change  Enter: start  Esc: quit", True, TEXT_COLOR),
            (box_x + 16, box_y + 42),
        )

        lines = [("Player count", str(self.menu_player_count))]
        for name in CHARACTER_ORDER[:self.menu_player_count]:
            role = "Human" if self.menu_human_flags.get(name, True) else "AI"
            lines.append((name, role))
        lines.append(("Start Game", ""))

        y = box_y + 78
        for idx, (label, value) in enumerate(lines):
            is_selected = idx == self.menu_cursor
            color = (120, 220, 255) if is_selected else TEXT_COLOR
            prefix = "> " if is_selected else "  "
            line = f"{prefix}{label}: {value}" if value else f"{prefix}{label}"
            self.screen.blit(self.small_font.render(line, True, color), (box_x + 20, y))
            y += 28

        selected_names = CHARACTER_ORDER[:self.menu_player_count]
        humans = [name for name in selected_names if self.menu_human_flags.get(name, True)]
        ai_players = [name for name in selected_names if not self.menu_human_flags.get(name, True)]
        summary = [
            f"Humans: {', '.join(humans) if humans else 'none'}",
            f"AI players: {', '.join(ai_players) if ai_players else 'none'}",
            "Tip: choose all AI for a simulation or all human for pass-and-play testing.",
        ]

        y += 8
        for line in summary:
            for wrapped in textwrap.wrap(line, width=66):
                self.screen.blit(self.tiny_font.render(wrapped, True, MUTED_TEXT), (box_x + 20, y))
                y += 18

    def draw_handoff_overlay(self):
        """Draw the screen used to pass the device between human turns."""
        if not self.awaiting_turn_handoff or not self.players or self.game_over:
            return

        current_player = self.current_player()
        if not current_player.is_human:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        box_w = 460
        box_h = 180
        box_x = (self.board_width - box_w) // 2
        box_y = UI_BAR_HEIGHT + (self.board_height - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (34, 34, 34), box_rect)
        pygame.draw.rect(self.screen, (210, 210, 210), box_rect, 2)

        lines = [
            f"Pass to {current_player.name}",
            "Make sure the other players are not looking.",
            "Press Enter when ready to start the turn.",
        ]

        y = box_y + 20
        for idx, line in enumerate(lines):
            font = self.font if idx == 0 else self.small_font
            color = (255, 215, 0) if idx == 0 else TEXT_COLOR
            text = font.render(line, True, color)
            x = box_x + (box_w - text.get_width()) // 2
            self.screen.blit(text, (x, y))
            y += 38 if idx == 0 else 28

    def draw_help_overlay(self):
        """Draw the quick how-to-play panel."""
        if not self.show_help_overlay:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        box_w = 560
        box_h = 270
        box_x = (self.board_width - box_w) // 2
        box_y = UI_BAR_HEIGHT + 28
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (34, 34, 34), box_rect)
        pygame.draw.rect(self.screen, (210, 210, 210), box_rect, 2)

        self.screen.blit(self.font.render("How to Play", True, (255, 215, 0)), (box_x + 16, box_y + 14))
        guide_lines = [
            "Goal: work out the suspect, weapon, and room hidden in the envelope.",
            "1. At the start of a human turn, pass the device over and press Enter.",
            "2. Press V to reveal or hide that player's hand and detective notes.",
            "3. Press SPACE to roll, then click a green tile to move around the board.",
            "4. Use door tiles to enter rooms. P uses a secret passage in corner rooms.",
            "5. Press J to make a suggestion and A only when you're ready to accuse.",
            "6. Press S to end the turn whenever you are finished.",
            "Press H to hide/show this guide.",
        ]

        y = box_y + 50
        for line in guide_lines:
            for wrapped in textwrap.wrap(line, width=70):
                self.screen.blit(self.small_font.render(wrapped, True, TEXT_COLOR), (box_x + 16, y))
                y += 22

    def draw_game_over_overlay(self):
        """Draw the game over summary overlay."""
        if not self.game_over:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        solution = f"Solution: {self.envelope.suspect.name} | {self.envelope.weapon.name} | {self.envelope.room.name}"
        winner_text = self.winner.name if self.winner else "No winner"
        lines = [
            "GAME OVER",
            f"Winner: {winner_text}",
            solution,
            "Press Enter to play again, M for menu, or ESC to quit",
        ]

        start_y = self.screen.get_height() // 2 - 60
        for idx, line in enumerate(lines):
            font = self.font if idx == 0 else self.small_font
            text = font.render(line, True, (255, 255, 255))
            x = (self.screen.get_width() - text.get_width()) // 2
            self.screen.blit(text, (x, start_y + idx * 28))

    def draw(self):
        """Draw the board and whichever overlays are active."""
        self.screen.fill((0, 0, 0))
        y_off = UI_BAR_HEIGHT

        self.screen.blit(self.board_image, (0, y_off))

        if self.game_state == "MENU":
            self.draw_menu_overlay()
            return

        self.draw_weapons(y_off)

        if self.reachable or self.reachable_rooms:
            tile_hl = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            tile_hl.fill((0, 220, 0, 80))
            room_hl = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            room_hl.fill((0, 220, 0, 55))
            for (gx, gy) in self.reachable:
                self.screen.blit(tile_hl, (gx * CELL_SIZE, gy * CELL_SIZE + y_off))
            if self.reachable_rooms:
                for gy in range(self.grid_height):
                    for gx in range(self.grid_width):
                        if self.grid[gy][gx]["type"] in self.reachable_rooms:
                            self.screen.blit(room_hl, (gx * CELL_SIZE, gy * CELL_SIZE + y_off))

        if self.show_rooms:
            for gy in range(self.grid_height):
                for gx in range(self.grid_width):
                    room_type = self.grid[gy][gx]["type"]
                    color = next((c for c, name in COLOR_TO_ROOM.items() if name == room_type), None)
                    if color and room_type != "WALL":
                        s = pygame.Surface((CELL_SIZE, CELL_SIZE))
                        s.set_alpha(80)
                        s.fill(color)
                        self.screen.blit(s, (gx * CELL_SIZE, gy * CELL_SIZE + y_off))

        if self.show_grid:
            for x in range(0, self.board_width, CELL_SIZE):
                pygame.draw.line(self.screen, GRID_COLOR, (x, y_off), (x, self.board_height + y_off))
            for y in range(0, self.board_height + CELL_SIZE, CELL_SIZE):
                pygame.draw.line(self.screen, GRID_COLOR, (0, y + y_off), (self.board_width, y + y_off))

        for name, data in self.characters.items():
            gx, gy = data["position"]
            center = (gx * CELL_SIZE + CELL_SIZE // 2, gy * CELL_SIZE + CELL_SIZE // 2 + y_off)
            pygame.draw.circle(self.screen, (0, 0, 0), center, (CELL_SIZE // 2) - 2)
            pygame.draw.circle(self.screen, data["color"], center, (CELL_SIZE // 2) - 4)
            if name == self.current_turn:
                pygame.draw.circle(self.screen, (255, 255, 255), center, (CELL_SIZE // 2) - 1, 2)

        self.draw_ui()
        self.draw_side_panel()
        self.draw_modal()
        self.draw_help_overlay()
        self.draw_handoff_overlay()
        self.draw_game_over_overlay()

    def draw_ui(self):
        """Draw the top strip with turn and control info."""
        font = pygame.font.SysFont("Arial", 16, bold=True)
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.board_width, UI_BAR_HEIGHT))
        pygame.draw.line(self.screen, (80, 80, 80), (0, UI_BAR_HEIGHT), (self.board_width, UI_BAR_HEIGHT))

        current_player = self.current_player()
        room_name = self.current_room_name()
        can_suggest = current_player.is_human and room_name and not self.has_suggested_this_turn
        passage_hint = "  P: Passage" if current_player.is_human and self.current_secret_passage_destination() else ""

        turn_label = font.render("Turn: ", True, (200, 200, 200))
        role_suffix = " [AI]" if not current_player.is_human else ""
        name_text = font.render(self.current_turn + role_suffix, True, self.characters[self.current_turn]["color"])
        self.screen.blit(turn_label, (8, 7))
        self.screen.blit(name_text, (52, 7))

        can_accuse = current_player.is_human and self.can_accuse_now()

        if self.phase == "ROLL":
            suggestion_hint = "  J: Suggest" if can_suggest else ""
            dice_text = font.render(
                f"| SPACE: Roll  S: End{suggestion_hint}{passage_hint}",
                True,
                (180, 180, 60),
            )
        elif self.phase == "ACTION":
            action_bits = [f"| Room: {room_name}"]
            if can_suggest:
                action_bits.append("J: Suggest")
            if can_accuse:
                action_bits.append("A: Accuse")
            action_bits.append("S: End")
            dice_text = font.render(
                "  ".join(action_bits),
                True,
                (120, 220, 255),
            )
        else:
            d1, d2 = self.dice_result
            dice_text = font.render(
                f"| Rolled: {d1}+{d2} | Steps left: {self.steps} | Click to move  S: End{passage_hint}",
                True,
                (60, 220, 60),
            )
        hint = self.tiny_font.render("G: Grid  R: Rooms  V: Private  H: Help  ESC: Quit", True, (120, 120, 120))
        hint_x = self.board_width - hint.get_width() - 8
        max_dice_width = max(80, hint_x - 190)
        if dice_text.get_width() > max_dice_width:
            cropped = dice_text.get_rect().copy()
            cropped.width = max_dice_width
            self.screen.blit(dice_text, (180, 7), cropped)
        else:
            self.screen.blit(dice_text, (180, 7))

        self.screen.blit(hint, (hint_x, 7))

    def handle_input(self):
        """Read keyboard and mouse input for the current game state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.modal_state:
                    self.modal_state = None
                    continue
                return False

            if self.game_state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.menu_cursor = (self.menu_cursor - 1) % (self.menu_player_count + 2)
                    elif event.key == pygame.K_DOWN:
                        self.menu_cursor = (self.menu_cursor + 1) % (self.menu_player_count + 2)
                    elif event.key == pygame.K_LEFT and self.menu_cursor == 0:
                        self.menu_player_count = max(2, self.menu_player_count - 1)
                        self.sync_menu_selection()
                    elif event.key == pygame.K_RIGHT and self.menu_cursor == 0:
                        self.menu_player_count = min(len(CHARACTER_ORDER), self.menu_player_count + 1)
                        self.sync_menu_selection()
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE, pygame.K_RETURN):
                        if 1 <= self.menu_cursor <= self.menu_player_count:
                            name = CHARACTER_ORDER[self.menu_cursor - 1]
                            self.menu_human_flags[name] = not self.menu_human_flags.get(name, True)
                        elif event.key == pygame.K_RETURN and self.menu_cursor == self.menu_player_count + 1:
                            self.start_selected_game()
                continue

            if self.game_over:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.start_selected_game()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.return_to_menu()
                continue

            if self.awaiting_turn_handoff:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.awaiting_turn_handoff = False
                    elif event.key == pygame.K_h:
                        self.show_help_overlay = not self.show_help_overlay
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                self.show_grid = not self.show_grid
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.show_rooms = not self.show_rooms
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                self.show_help_overlay = not self.show_help_overlay
                continue

            if self.modal_state and event.type == pygame.KEYDOWN:
                field_count = 2 if self.modal_state["type"] == "suggestion" else 3
                if event.key == pygame.K_UP:
                    self.modal_state["field"] = (self.modal_state["field"] - 1) % field_count
                elif event.key == pygame.K_DOWN:
                    self.modal_state["field"] = (self.modal_state["field"] + 1) % field_count
                elif event.key == pygame.K_LEFT:
                    if self.modal_state["field"] == 0:
                        self.modal_state["suspect_index"] = (self.modal_state["suspect_index"] - 1) % len(SUSPECTS)
                    elif self.modal_state["field"] == 1:
                        self.modal_state["weapon_index"] = (self.modal_state["weapon_index"] - 1) % len(WEAPONS)
                    elif self.modal_state["field"] == 2 and self.modal_state["type"] == "accusation":
                        self.modal_state["room_index"] = (self.modal_state["room_index"] - 1) % len(ROOMS)
                elif event.key == pygame.K_RIGHT:
                    if self.modal_state["field"] == 0:
                        self.modal_state["suspect_index"] = (self.modal_state["suspect_index"] + 1) % len(SUSPECTS)
                    elif self.modal_state["field"] == 1:
                        self.modal_state["weapon_index"] = (self.modal_state["weapon_index"] + 1) % len(WEAPONS)
                    elif self.modal_state["field"] == 2 and self.modal_state["type"] == "accusation":
                        self.modal_state["room_index"] = (self.modal_state["room_index"] + 1) % len(ROOMS)
                elif event.key == pygame.K_RETURN:
                    if self.modal_state["type"] == "suggestion":
                        self.submit_suggestion()
                    else:
                        self.submit_accusation()
                elif event.key == pygame.K_ESCAPE:
                    self.modal_state = None
                continue

            current_player = self.current_player()
            if not current_player.is_human:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if mx < self.board_width and my >= UI_BAR_HEIGHT:
                    gx, gy = mx // CELL_SIZE, (my - UI_BAR_HEIGHT) // CELL_SIZE
                    self.handle_move(gx, gy)

            if event.type == pygame.MOUSEWHEEL and self.private_info_visible:
                self.note_scroll_offset = max(0, self.note_scroll_offset - event.y)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.roll_dice()
                elif event.key == pygame.K_s:
                    self.skip_move()
                elif event.key == pygame.K_p:
                    self.use_secret_passage()
                elif event.key == pygame.K_j:
                    self.open_suggestion_dialog()
                elif event.key == pygame.K_a:
                    self.open_accusation_dialog()
                elif event.key == pygame.K_v:
                    self.private_info_visible = not self.private_info_visible
                    if self.private_info_visible:
                        self.note_scroll_offset = 0
                elif event.key == pygame.K_UP and self.private_info_visible:
                    self.note_scroll_offset = max(0, self.note_scroll_offset - 1)
                elif event.key == pygame.K_DOWN and self.private_info_visible:
                    self.note_scroll_offset += 1
        return True

    def run(self):
        """Main pygame loop."""
        clock = pygame.time.Clock()
        while True:
            if not self.handle_input():
                break
            if self.pending_ai_turn and not self.modal_state and not self.game_over:
                if pygame.time.get_ticks() >= self.ai_action_due_at:
                    self.pending_ai_turn = False
                    self.ai_action_due_at = 0
                    self.run_ai_turn()
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    CluedoGame().run()
