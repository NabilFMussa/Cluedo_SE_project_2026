import pygame
import sys
import random
from collections import deque

# Initialize Pygame
pygame.init()

# --- CONFIGURATION ---
BOARD_IMG = "Assets_images/game board.png"
MASK_IMG = "Assets_images/board_mask.png"

CELL_SIZE = 20
UI_BAR_HEIGHT = 30 
GRID_COLOR = (60, 60, 60) # Slightly darker for better visibility

# --- CHARACTER ORDER & DATA ---
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

# --- SECRET PASSAGES ---
# Room-to-room mapping so passage works anywhere inside the source room.
SECRET_PASSAGES = {
    "STUDY": "KITCHEN",
    "KITCHEN": "STUDY",
    "LOUNGE": "CONSERVATORY",
    "CONSERVATORY": "LOUNGE",
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
    def __init__(self):
        try:
            self.board_image = pygame.image.load(BOARD_IMG)
            self.mask_image = pygame.image.load(MASK_IMG)
        except pygame.error:
            print("Error: Could not load images. Check your Assets_images folder.")
            sys.exit()
        
        self.board_width, self.board_height = self.board_image.get_size()
        # Create screen with extra height for UI
        self.screen = pygame.display.set_mode((self.board_width, self.board_height + UI_BAR_HEIGHT))
        pygame.display.set_caption("Cluedo Game Engine")

        self.grid_width = self.board_width // CELL_SIZE
        self.grid_height = self.board_height // CELL_SIZE
        
        self.grid = self._create_grid()
        self.door_to_rooms = self._build_door_room_map()
        self.room_anchor_by_type = self._build_room_anchor_map()
        self.characters = CHARACTERS
        self.show_rooms = False
        self.show_grid = True

        # Turn management
        self.current_turn_index = 0
        self.current_turn = CHARACTER_ORDER[self.current_turn_index]

        # Movement state
        self.phase = "ROLL"       # "ROLL" = waiting to roll | "MOVE" = pick a destination
        self.dice_result = (0, 0)
        self.steps = 0
        self.reachable = set()        # (gx, gy) walkable tiles the player can move to
        self.reachable_rooms = set()  # room type strings the player can enter this turn

    def _create_grid(self):
        grid = []
        for gy in range(self.grid_height):
            row = []
            for gx in range(self.grid_width):
                pixel_x = gx * CELL_SIZE + CELL_SIZE // 2
                pixel_y = gy * CELL_SIZE + CELL_SIZE // 2
                color = self.mask_image.get_at((pixel_x, pixel_y))[:3]
                room_type = COLOR_TO_ROOM.get(color, "WALL")
                row.append({
                    "type": room_type,
                    "walkable": room_type in ["HALLWAY", "DOOR", "START"],
                    "is_room": room_type not in ["HALLWAY", "WALL", "DOOR", "START", "CENTER"]
                })
            grid.append(row)
        return grid

    def next_turn(self):
        """Switches to the next player and resets movement state."""
        self.current_turn_index = (self.current_turn_index + 1) % len(CHARACTER_ORDER)
        self.current_turn = CHARACTER_ORDER[self.current_turn_index]
        self.phase = "ROLL"
        self.dice_result = (0, 0)
        self.steps = 0
        self.reachable = set()
        self.reachable_rooms = set()
        print(f"It is now {self.current_turn}'s turn.")

    # ------------------------------------------------------------------
    # MOVEMENT SYSTEM
    # ------------------------------------------------------------------

    def _build_door_room_map(self):
        """Map each DOOR cell to the set of room types it is adjacent to."""
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

    def _build_room_anchor_map(self):
        """Pick one stable tile per room type for teleports (e.g., secret passages)."""
        anchors = {}
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                cell = self.grid[gy][gx]
                if cell["is_room"] and cell["type"] not in anchors:
                    anchors[cell["type"]] = (gx, gy)
        return anchors

    def _is_occupied_by_other(self, gx, gy):
        """True if another player occupies this walkable tile."""
        for name, data in self.characters.items():
            if name != self.current_turn and data["position"] == (gx, gy):
                return True
        return False

    def _current_door_rooms(self):
        """Rooms that can be entered right now from the current tile."""
        gx, gy = self.characters[self.current_turn]["position"]
        if self.steps < 1:
            return set()
        if self.grid[gy][gx]["type"] != "DOOR":
            return set()
        return set(self.door_to_rooms.get((gx, gy), set()))

    def _shortest_walk_distance(self, start, goal, max_steps):
        """Shortest distance through walkable tiles only, bounded by max_steps."""
        if start == goal:
            return 0

        occupied = {
            data["position"]
            for name, data in self.characters.items()
            if name != self.current_turn
        }

        queue = deque([(start[0], start[1], 0)])
        visited = {start}
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

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

    def roll_dice(self):
        """Roll two dice, compute reachable cells, and enter MOVE phase."""
        if self.phase != "ROLL":
            return
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        self.dice_result = (d1, d2)
        self.steps = d1 + d2
        gx, gy = self.characters[self.current_turn]["position"]
        self.reachable, _ = self._compute_reachable(gx, gy, self.steps)
        self.reachable_rooms = self._current_door_rooms()
        self.phase = "MOVE"
        print(f"{self.current_turn} rolled {d1} + {d2} = {self.steps}")

    def _compute_reachable(self, start_gx, start_gy, steps):
        """
        BFS that finds every walkable tile reachable in up to `steps` moves and
        every room reachable by entering through an adjacent door.
        Returns (reachable_cells: set, reachable_rooms: set).
        """
        occupied = {
            data["position"]
            for name, data in self.characters.items()
            if name != self.current_turn
        }

        reachable = set()
        reachable_rooms = set()
        visited = {}  # (gx, gy) -> max steps_remaining when reached
        queue = deque()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        start_cell = self.grid[start_gy][start_gx]

        if start_cell["is_room"]:
            # Player is inside a room — seed BFS from every exit door
            room_type = start_cell["type"]
            for (dgx, dgy), rooms in self.door_to_rooms.items():
                if room_type in rooms and steps >= 1 and (dgx, dgy) not in occupied:
                    rem = steps - 1
                    if (dgx, dgy) not in visited or visited[(dgx, dgy)] < rem:
                        visited[(dgx, dgy)] = rem
                        queue.append((dgx, dgy, rem))
                        reachable.add((dgx, dgy))
        else:
            # Player is on a hallway / door / start tile
            visited[(start_gx, start_gy)] = steps
            queue.append((start_gx, start_gy, steps))

        while queue:
            gx, gy, remaining = queue.popleft()

            # Discard stale entries
            if visited.get((gx, gy), -1) > remaining:
                continue

            cell = self.grid[gy][gx]

            # From a door tile with at least 1 move left, rooms can be entered.
            if cell["type"] == "DOOR" and remaining >= 1:
                for room_type in self.door_to_rooms.get((gx, gy), set()):
                    reachable_rooms.add(room_type)

            if remaining == 0:
                continue

            # Expand to adjacent walkable tiles
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
        """Player stays stationary this turn (rule 15)."""
        if self.phase not in ["ROLL", "MOVE"]:
            return
        print(f"{self.current_turn} stays put.")
        self.next_turn()

    def use_secret_passage(self):
        """Use a secret passage if the player's current room has one (rule 16)."""
        if self.phase != "ROLL":
            print("Use secret passage before rolling.")
            return

        gx, gy = self.characters[self.current_turn]["position"]
        current_cell = self.grid[gy][gx]
        if not current_cell["is_room"]:
            print("You must be inside a room to use a secret passage.")
            return

        source_room = current_cell["type"]
        if source_room not in SECRET_PASSAGES:
            print("This room has no secret passage.")
            return

        destination_room = SECRET_PASSAGES[source_room]
        destination_pos = self.room_anchor_by_type.get(destination_room)
        if not destination_pos:
            print(f"Could not find destination room tile for {destination_room}.")
            return

        self.characters[self.current_turn]["position"] = destination_pos
        print(f"{self.current_turn} used secret passage: {source_room} -> {destination_room}")
        self.next_turn()

    def handle_move(self, target_gx, target_gy):
        """Validate and execute movement while preserving remaining steps."""
        if self.phase != "MOVE":
            print("Roll the dice first! (Press SPACE)")
            return

        if not (0 <= target_gx < self.grid_width and 0 <= target_gy < self.grid_height):
            return

        char = self.characters[self.current_turn]
        current_gx, current_gy = char["position"]
        current_cell = self.grid[current_gy][current_gx]
        target_cell = self.grid[target_gy][target_gx]

        # Room entry: must currently be standing on the specific door.
        if target_cell["is_room"]:
            if self.steps < 1:
                print("No movement left to enter a room.")
                return
            if current_cell["type"] != "DOOR":
                print("You must stand on a door tile before entering a room.")
                return
            connected_rooms = self.door_to_rooms.get((current_gx, current_gy), set())
            if target_cell["type"] not in connected_rooms:
                print(f"This door does not lead to {target_cell['type']}!")
                return

            # Entering a room ends movement for the turn (rule 14).
            char["position"] = (target_gx, target_gy)
            print(f"Moved {self.current_turn} into {target_cell['type']}")
            self.next_turn()
            return

        # Standard hallway movement.
        if not target_cell["walkable"]:
            print("That tile is not walkable.")
            return
        if self._is_occupied_by_other(target_gx, target_gy):
            print("That square is occupied.")
            return
        if (target_gx, target_gy) not in self.reachable:
            print("Target is out of range for your remaining movement.")
            return

        distance = self._shortest_walk_distance((current_gx, current_gy), (target_gx, target_gy), self.steps)
        if distance is None:
            print("No valid path to that tile.")
            return

        char["position"] = (target_gx, target_gy)
        self.steps -= distance
        print(f"Moved {self.current_turn} to ({target_gx},{target_gy}) [{target_cell['type']}], {self.steps} step(s) left")

        if self.steps <= 0:
            self.next_turn()
            return

        # Keep turn active with updated movement budget.
        self.reachable, _ = self._compute_reachable(target_gx, target_gy, self.steps)
        self.reachable_rooms = self._current_door_rooms()

        # If standing on a door after moving, show room-entry options for the next click.
        self.reachable_rooms = self._current_door_rooms()

    def draw(self):
        """Main rendering method."""
        self.screen.fill((0, 0, 0)) # Clear screen
        y_off = UI_BAR_HEIGHT # Offset for board drawing
        
        # Draw the physical board
        self.screen.blit(self.board_image, (0, y_off))

        # Draw reachable-cell highlights
        if self.reachable or self.reachable_rooms:
            tile_hl = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            tile_hl.fill((0, 220, 0, 80))     # green tint for walkable tiles
            room_hl = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            room_hl.fill((0, 220, 0, 55))     # lighter green for room areas
            for (gx, gy) in self.reachable:
                self.screen.blit(tile_hl, (gx * CELL_SIZE, gy * CELL_SIZE + y_off))
            if self.reachable_rooms:
                for gy in range(self.grid_height):
                    for gx in range(self.grid_width):
                        if self.grid[gy][gx]["type"] in self.reachable_rooms:
                            self.screen.blit(room_hl, (gx * CELL_SIZE, gy * CELL_SIZE + y_off))

        # Draw Room Overlays (Toggleable)
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

        # Draw Grid (Toggleable)
        if self.show_grid:
            for x in range(0, self.board_width, CELL_SIZE):
                pygame.draw.line(self.screen, GRID_COLOR, (x, y_off), (x, self.board_height + y_off))
            for y in range(0, self.board_height + CELL_SIZE, CELL_SIZE):
                pygame.draw.line(self.screen, GRID_COLOR, (0, y + y_off), (self.board_width, y + y_off))

        # Draw Players
        for name, data in self.characters.items():
            gx, gy = data["position"]
            center = (gx * CELL_SIZE + CELL_SIZE // 2, gy * CELL_SIZE + CELL_SIZE // 2 + y_off)
            
            # Draw Token
            pygame.draw.circle(self.screen, (0, 0, 0), center, (CELL_SIZE // 2) - 2) # Shadow/Border
            pygame.draw.circle(self.screen, data["color"], center, (CELL_SIZE // 2) - 4)
            
            # Highlight current player with a white ring
            if name == self.current_turn:
                pygame.draw.circle(self.screen, (255, 255, 255), center, (CELL_SIZE // 2) - 1, 2)

        self.draw_ui()

    def draw_ui(self):
        """Draws the top status bar: turn, dice, phase, and key hints."""
        font = pygame.font.SysFont("Arial", 16, bold=True)
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.board_width, UI_BAR_HEIGHT))
        pygame.draw.line(self.screen, (80, 80, 80), (0, UI_BAR_HEIGHT), (self.board_width, UI_BAR_HEIGHT))

        # Turn indicator
        turn_label = font.render("Turn: ", True, (200, 200, 200))
        name_text  = font.render(self.current_turn, True, self.characters[self.current_turn]["color"])
        self.screen.blit(turn_label, (8, 7))
        self.screen.blit(name_text,  (52, 7))

        # Dice display
        if self.phase == "ROLL":
            dice_text = font.render("  |  SPACE: Roll dice   S: Stay   P: Passage", True, (180, 180, 60))
        else:
            d1, d2 = self.dice_result
            dice_text = font.render(
                f"  |  Rolled: {d1}+{d2} | Steps left: {self.steps} | Click to move   S: Stay",
                True, (60, 220, 60)
            )
        self.screen.blit(dice_text, (180, 7))

        # Right-hand controls hint
        hint = font.render("G: Grid  R: Rooms  ESC: Quit", True, (120, 120, 120))
        self.screen.blit(hint, (self.board_width - hint.get_width() - 8, 7))

    def handle_input(self):
        """Processes keyboard and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Subtract UI height from mouse Y coordinate to align with grid
                gx, gy = mx // CELL_SIZE, (my - UI_BAR_HEIGHT) // CELL_SIZE
                self.handle_move(gx, gy)
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.roll_dice()
                elif event.key == pygame.K_s:
                    self.skip_move()
                elif event.key == pygame.K_p:
                    self.use_secret_passage()
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_r:
                    self.show_rooms = not self.show_rooms
                elif event.key == pygame.K_ESCAPE:
                    return False
        return True

    def run(self):
        """Game loop."""
        clock = pygame.time.Clock()
        while True:
            if not self.handle_input(): 
                break
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    CluedoGame().run()