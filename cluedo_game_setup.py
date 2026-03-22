import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Configuration
BOARD_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/game board.png"
MASK_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/board_mask.png"

# Grid settings
CELL_SIZE = 20
GRID_COLOR = (100, 100, 100)
HIGHLIGHT_COLOR = (255, 255, 0)

# Character definitions
CHARACTERS = {
    "Miss Scarlett": {"color": (255, 20, 147), "start_pos": None},  # Deep Pink
    "Col. Mustard": {"color": (255, 215, 0), "start_pos": None},    # Gold
    "Mrs. White": {"color": (255, 255, 255), "start_pos": None},    # White
    "Rev. Green": {"color": (0, 128, 0), "start_pos": None},        # Green
    "Mrs. Peacock": {"color": (0, 191, 255), "start_pos": None},    # Deep Sky Blue
    "Prof. Plum": {"color": (128, 0, 128), "start_pos": None},      # Purple
}

# Color to room mapping
COLOR_TO_ROOM = {
    (255, 255, 255): "HALLWAY",
    (0, 255, 0): "STUDY",
    (0, 0, 255): "LIBRARY",
    (255, 0, 0): "BILLIARD ROOM",
    (0, 255, 255): "CONSERVATORY",
    (255, 0, 255): "BALL ROOM",
    (255, 255, 0): "KITCHEN",
    (128, 64, 0): "DINING ROOM",
    (128, 0, 128): "LOUNGE",
    (255, 128, 0): "HALL",
    (128, 128, 128): "CENTER",
    (255, 20, 147): "DOOR",
    (150, 0, 0): "START",
    (0, 0, 0): "WALL",
}

class CluedoGame:
    def __init__(self):
        # Load images
        self.board_img = pygame.image.load(BOARD_IMG)
        self.mask_img = pygame.image.load(MASK_IMG)

        # Get dimensions
        self.width_pixels, self.height_pixels = self.board_img.get_size()
        self.grid_width = self.width_pixels // CELL_SIZE
        self.grid_height = self.height_pixels // CELL_SIZE

        # Create grid
        self.grid = self._create_grid()

        # Screen setup
        self.screen = pygame.display.set_mode((self.width_pixels, self.height_pixels + 100))  # Extra space for UI
        pygame.display.set_caption("Cluedo Board Setup")

        # UI
        self.font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 12)

        # Game state
        self.show_grid = True
        self.show_rooms = False
        self.selected_cell = None
        self.characters = {}  # Will store placed characters
        self.find_starting_positions()

    def _create_grid(self):
        """Create the game grid from mask"""
        grid = []
        for gy in range(self.grid_height):
            row = []
            for gx in range(self.grid_width):
                px = gx * CELL_SIZE + CELL_SIZE // 2
                py = gy * CELL_SIZE + CELL_SIZE // 2

                if px < self.width_pixels and py < self.height_pixels:
                    color = self.mask_img.get_at((px, py))[:3]
                    room_type = COLOR_TO_ROOM.get(color, "UNKNOWN")
                else:
                    room_type = "WALL"

                cell = {
                    'type': room_type,
                    'walkable': room_type not in ["WALL"],
                    'is_room': room_type not in ["HALLWAY", "WALL", "DOOR", "START", "CENTER"],
                    'position': (gx, gy),
                    'pixel_pos': (px, py)
                }
                row.append(cell)
            grid.append(row)
        return grid

    def find_starting_positions(self):
        """Find all START positions in the grid and assign to characters"""
        start_positions = []
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                if self.grid[gy][gx]['type'] == "START":
                    start_positions.append((gx, gy))

        print(f"Found {len(start_positions)} starting positions: {start_positions}")

        # Assign unique starting positions to characters
        character_names = list(CHARACTERS.keys())

        # If we have more positions than characters, randomly select 6 unique positions
        if len(start_positions) > len(character_names):
            selected_positions = random.sample(start_positions, len(character_names))
        else:
            # If we have fewer or equal positions, use all of them
            selected_positions = start_positions.copy()
            random.shuffle(selected_positions)

        # Assign positions to characters
        for i, char_name in enumerate(character_names):
            if i < len(selected_positions):
                position = selected_positions[i]
                CHARACTERS[char_name]["start_pos"] = position
                self.characters[char_name] = {
                    "position": position,
                    "color": CHARACTERS[char_name]["color"]
                }
                print(f"  {char_name}: {position}")
            else:
                print(f"  {char_name}: No starting position available")

        print(f"Assigned {len(self.characters)} characters to starting positions")

    def draw_board(self):
        """Draw the board image"""
        self.screen.blit(self.board_img, (0, 0))

    def draw_grid_overlay(self):
        """Draw grid lines"""
        if not self.show_grid:
            return

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                x = gx * CELL_SIZE
                y = gy * CELL_SIZE
                pygame.draw.rect(self.screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def draw_characters(self):
        """Draw character tokens"""
        for char_name, char_data in self.characters.items():
            gx, gy = char_data["position"]
            x = gx * CELL_SIZE + CELL_SIZE // 2
            y = gy * CELL_SIZE + CELL_SIZE // 2

            # Draw character circle
            pygame.draw.circle(self.screen, char_data["color"], (x, y), CELL_SIZE // 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (x, y), CELL_SIZE // 3, 2)

            # Draw character initial
            initial = char_name[0] if char_name != "Mrs. White" else "W"
            text = self.small_font.render(initial, True, (0, 0, 0))
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)

    def draw_selected_cell(self):
        """Highlight selected cell"""
        if self.selected_cell:
            gx, gy = self.selected_cell['position']
            x = gx * CELL_SIZE
            y = gy * CELL_SIZE
            pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 3)

    def draw_ui(self):
        """Draw UI panel"""
        ui_y = self.height_pixels
        ui_height = 100

        # UI background
        ui_bg = pygame.Surface((self.width_pixels, ui_height))
        ui_bg.fill((50, 50, 50))
        self.screen.blit(ui_bg, (0, ui_y))

        # Status text
        status_lines = []
        if self.selected_cell:
            cell = self.selected_cell
            status_lines.append(f"Selected: {cell['type']} at {cell['position']}")
            status_lines.append(f"Walkable: {cell['walkable']}, Room: {cell['is_room']}")

            # Check if character is here
            char_here = None
            for char_name, char_data in self.characters.items():
                if char_data["position"] == cell["position"]:
                    char_here = char_name
                    break
            if char_here:
                status_lines.append(f"Character: {char_here}")
        else:
            status_lines.append("Click on board to select cells")

        # Draw status text
        for i, line in enumerate(status_lines):
            text = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (10, ui_y + 10 + i * 20))

        # Controls
        controls = [
            "G: Toggle Grid | R: Toggle Rooms | C: Toggle Characters",
            "Click: Select Cell | ESC: Quit"
        ]

        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, (200, 200, 200))
            self.screen.blit(text, (10, ui_y + 60 + i * 15))

    def get_cell_at_pixel(self, pixel_x, pixel_y):
        """Get cell at pixel position"""
        if pixel_y >= self.height_pixels:  # Clicked in UI area
            return None

        gx = pixel_x // CELL_SIZE
        gy = pixel_y // CELL_SIZE

        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return self.grid[gy][gx]
        return None

    def handle_input(self, event):
        """Handle user input"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.selected_cell = self.get_cell_at_pixel(mouse_x, mouse_y)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self.show_grid = not self.show_grid
            elif event.key == pygame.K_r:
                self.show_rooms = not self.show_rooms
            elif event.key == pygame.K_c:
                # Toggle character visibility (for now just print)
                print("Characters:", list(self.characters.keys()))
            elif event.key == pygame.K_ESCAPE:
                return False
        return True

    def run(self):
        """Main game loop"""
        print("Cluedo Board Setup GUI")
        print(f"Grid: {self.grid_width}x{self.grid_height}")
        print("Characters placed at starting positions")

        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    running = self.handle_input(event)

            # Draw everything
            self.draw_board()
            if self.show_rooms:
                self.draw_room_overlay()
            self.draw_grid_overlay()
            self.draw_characters()
            self.draw_selected_cell()
            self.draw_ui()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def draw_room_overlay(self):
        """Draw room color overlays (simplified)"""
        # This would be similar to the previous version
        pass

def main():
    try:
        game = CluedoGame()
        game.run()
    except pygame.error as e:
        print(f"Error: {e}")
        print("Make sure board_mask.png exists in Assets_images/")
        sys.exit(1)

if __name__ == "__main__":
    main()