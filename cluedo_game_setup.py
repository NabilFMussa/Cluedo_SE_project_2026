import pygame
import sys

# Initialize Pygame
pygame.init()

# --- CONFIGURATION ---
BOARD_IMG = "Assets_images/game board.png"
MASK_IMG = "Assets_images/board_mask.png"

CELL_SIZE = 20
UI_BAR_HEIGHT = 30  # Height of the black bar at the top
GRID_COLOR = (100, 100, 100)

# --- HARDCODED STARTING POSITIONS (gx, gy) ---
CHARACTERS = {
    "Miss Scarlett": {"color": (255, 0, 0),    "position": (22, 1)},
    "Col. Mustard":  {"color": (255, 215, 0),  "position": (31, 9)},
    "Mrs. White":    {"color": (240, 240, 240),"position": (19, 30)},
    "Rev. Green":    {"color": (0, 128, 0),    "position": (13, 30)},
    "Mrs. Peacock":  {"color": (0, 0, 255),    "position": (2, 22)},
    "Prof. Plum":    {"color": (128, 0, 128),  "position": (2, 7)},
}

SECRET_PASSAGES = {
    (2, 4): (25, 28), (25, 28): (2, 4),
    (31, 7): (3, 24), (3, 24): (31, 7),
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

# Temporary fix for mask tiles that should be doors but are not colored as DOOR.
# Study entrance at (9, 5) is currently painted as wall in board_mask.png.
FORCED_DOOR_CELLS = {(9, 5)}

class CluedoGame:
    def __init__(self):
        try:
            self.board_image = pygame.image.load(BOARD_IMG)
            self.mask_image = pygame.image.load(MASK_IMG)
        except pygame.error:
            print("Error: Could not load images. Check your Assets_images folder.")
            sys.exit()
        
        self.board_width, self.board_height = self.board_image.get_size()
        
        # Increase window height by UI_BAR_HEIGHT so the bar doesn't cover the board
        self.screen = pygame.display.set_mode((self.board_width, self.board_height + UI_BAR_HEIGHT))
        pygame.display.set_caption("Cluedo Game Engine")

        self.grid_width = self.board_width // CELL_SIZE
        self.grid_height = self.board_height // CELL_SIZE
        
        self.grid = self._create_grid()
        self.door_to_rooms = self._build_door_room_map()
        self.characters = CHARACTERS
        self.show_rooms = False
        self.show_grid = True  # Added state for grid toggle
        self.current_turn = "Miss Scarlett"

    def _create_grid(self):
        grid = []
        for gy in range(self.grid_height):
            row = []
            for gx in range(self.grid_width):
                pixel_x = gx * CELL_SIZE + CELL_SIZE // 2
                pixel_y = gy * CELL_SIZE + CELL_SIZE // 2
                color = self.mask_image.get_at((pixel_x, pixel_y))[:3]
                room_type = COLOR_TO_ROOM.get(color, "WALL")

                if (gx, gy) in FORCED_DOOR_CELLS:
                    room_type = "DOOR"

                row.append({
                    "type": room_type,
                    "walkable": room_type in ["HALLWAY", "DOOR", "START"],
                    "is_room": room_type not in ["HALLWAY", "WALL", "DOOR", "START", "CENTER"]
                })
            grid.append(row)
        return grid

    def _build_door_room_map(self):
        """Map each door cell to the room(s) it actually connects to by adjacency."""
        door_map = {}
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                if self.grid[gy][gx]["type"] != "DOOR":
                    continue

                connected_rooms = set()
                for dx, dy in directions:
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        neighbor = self.grid[ny][nx]
                        if neighbor["is_room"]:
                            connected_rooms.add(neighbor["type"])

                door_map[(gx, gy)] = connected_rooms

        return door_map

    def handle_move(self, target_gx, target_gy):
        if not (0 <= target_gx < self.grid_width and 0 <= target_gy < self.grid_height):
            return

        char = self.characters[self.current_turn]
        current_gx, current_gy = char["position"]
        current_cell = self.grid[current_gy][current_gx]
        target_cell = self.grid[target_gy][target_gx]

        # --- CORRECTED SECRET PASSAGE LOGIC ---
        # 1. Check if the player is currently standing on a secret passage tile
        if (current_gx, current_gy) in SECRET_PASSAGES:
            dest_gx, dest_gy = SECRET_PASSAGES[(current_gx, current_gy)]
            
            # 2. ONLY teleport if they click the EXACT destination tile
            # (Or click anywhere inside the destination room)
            if (target_gx, target_gy) == (dest_gx, dest_gy):
                char["position"] = (dest_gx, dest_gy)
                print(f"{self.current_turn} used the Secret Passage to {target_cell['type']}!")
                # In Cluedo, using a passage ends your movement turn
                self.next_turn() 
                return 

        # --- STANDARD MOVEMENT LOGIC ---
        # If we didn't teleport, check if the click was a valid walk move
        if target_cell["type"] == "WALL": 
            return
        
        # Room Entry Logic (Must be on a DOOR to enter)
        if target_cell["is_room"]:
            if current_cell["type"] != "DOOR":
                print("You must use a door to enter a room!")
                return

            connected_rooms = self.door_to_rooms.get((current_gx, current_gy), set())
            if target_cell["type"] not in connected_rooms:
                print(f"This door does not lead to {target_cell['type']}!")
                return

        # Update position
        char["position"] = (target_gx, target_gy)
        print(f"Moved {self.current_turn} to {target_cell['type']}")

    def draw(self):
        self.screen.fill((0, 0, 0))
        
        # All board elements are offset by UI_BAR_HEIGHT (30px)
        y_off = UI_BAR_HEIGHT
        
        self.screen.blit(self.board_image, (0, y_off))

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

        self.draw_ui()

    def draw_ui(self):
        font = pygame.font.SysFont("Arial", 16)
        pygame.draw.rect(self.screen, (20, 20, 20), (0, 0, self.board_width, UI_BAR_HEIGHT))
        pygame.draw.line(self.screen, (100, 100, 100), (0, UI_BAR_HEIGHT), (self.board_width, UI_BAR_HEIGHT))
        
        turn_text = font.render(f"Turn: {self.current_turn}", True, (255, 255, 255))
        self.screen.blit(turn_text, (15, 7))
        
        controls = font.render("G: Toggle Grid | R: Toggle Rooms | ESC: Quit", True, (180, 180, 180))
        self.screen.blit(controls, (self.board_width - 320, 7))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Adjust mouse click by subtracting the UI bar height
                gx, gy = mx // CELL_SIZE, (my - UI_BAR_HEIGHT) // CELL_SIZE
                self.handle_move(gx, gy)
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    self.show_grid = not self.show_grid  # Toggle logic
                elif event.key == pygame.K_r:
                    self.show_rooms = not self.show_rooms
                elif event.key == pygame.K_ESCAPE:
                    return False
        return True

    def run(self):
        clock = pygame.time.Clock()
        while True:
            if not self.handle_input(): break
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    CluedoGame().run()