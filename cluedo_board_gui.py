import pygame
import sys

# Initialize Pygame
pygame.init()

# Configuration
BOARD_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/game board.png"
MASK_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/board_mask.png"

# Grid settings
CELL_SIZE = 20  # Size of each grid cell in pixels
GRID_COLOR = (100, 100, 100)  # Dark gray for grid lines
HIGHLIGHT_COLOR = (255, 255, 0)  # Yellow for highlighting

# Color to room mapping (matches the mask creation script)
COLOR_TO_ROOM = {
    (255, 255, 255): "HALLWAY",     # White
    (0, 255, 0): "STUDY",           # Lime Green
    (0, 0, 255): "LIBRARY",         # Blue
    (255, 0, 0): "BILLIARD ROOM",   # Red
    (0, 255, 255): "CONSERVATORY",  # Cyan
    (255, 0, 255): "BALL ROOM",     # Magenta
    (255, 255, 0): "KITCHEN",       # Yellow
    (128, 64, 0): "DINING ROOM",    # Brown
    (128, 0, 128): "LOUNGE",        # Purple
    (255, 128, 0): "HALL",          # Orange
    (128, 128, 128): "CENTER",      # Grey
    (255, 20, 147): "DOOR",         # Neon Pink
    (150, 0, 0): "START",           # Dark Red
    (0, 0, 0): "WALL",              # Black
}

# Room display colors (semi-transparent for overlay)
ROOM_DISPLAY_COLORS = {
    "HALLWAY": (220, 220, 220, 128),     # Light gray
    "STUDY": (144, 238, 144, 128),       # Light green
    "LIBRARY": (173, 216, 230, 128),     # Light blue
    "BILLIARD ROOM": (255, 182, 193, 128), # Light red
    "CONSERVATORY": (224, 255, 255, 128), # Light cyan
    "BALL ROOM": (255, 182, 255, 128),   # Light magenta
    "KITCHEN": (255, 255, 224, 128),     # Light yellow
    "DINING ROOM": (210, 180, 140, 128), # Light brown
    "LOUNGE": (221, 160, 221, 128),      # Light purple
    "HALL": (255, 218, 185, 128),        # Light orange
    "CENTER": (211, 211, 211, 128),      # Light grey
    "DOOR": (255, 105, 180, 128),        # Hot pink
    "START": (255, 160, 122, 128),       # Light coral
    "WALL": (0, 0, 0, 128),              # Black
}

class CluedoBoardGUI:
    def __init__(self):
        # Load images
        self.board_img = pygame.image.load(BOARD_IMG)
        self.mask_img = pygame.image.load(MASK_IMG)

        # Get dimensions from board image
        self.width_pixels, self.height_pixels = self.board_img.get_size()
        self.grid_width = self.width_pixels // CELL_SIZE
        self.grid_height = self.height_pixels // CELL_SIZE

        # Create the grid data
        self.grid = self._create_grid()

        # Screen setup (use board image size)
        self.screen = pygame.display.set_mode((self.width_pixels, self.height_pixels))
        pygame.display.set_caption("Cluedo Board - Grid Setup")

        # UI elements
        self.font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 12)

        # Game state
        self.show_grid = True
        self.show_rooms = True
        self.selected_cell = None
        self.characters = {}  # Will store character positions

    def _create_grid(self):
        """Create the game grid from the mask image"""
        grid = []

        for gy in range(self.grid_height):
            row = []
            for gx in range(self.grid_width):
                # Sample the center of each cell
                px = gx * CELL_SIZE + CELL_SIZE // 2
                py = gy * CELL_SIZE + CELL_SIZE // 2

                if px < self.width_pixels and py < self.height_pixels:
                    # Get color from mask
                    color = self.mask_img.get_at((px, py))[:3]  # RGB only
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

    def draw_board(self):
        """Draw the board image as background"""
        self.screen.blit(self.board_img, (0, 0))

    def draw_grid_overlay(self):
        """Draw the grid overlay"""
        if not self.show_grid:
            return

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                x = gx * CELL_SIZE
                y = gy * CELL_SIZE
                pygame.draw.rect(self.screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def draw_room_overlay(self):
        """Draw room color overlays"""
        if not self.show_rooms:
            return

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                cell = self.grid[gy][gx]
                if cell['type'] != "WALL":  # Don't overlay walls
                    x = gx * CELL_SIZE
                    y = gy * CELL_SIZE

                    color = ROOM_DISPLAY_COLORS.get(cell['type'], (255, 0, 255, 128))
                    overlay = pygame.Surface((CELL_SIZE, CELL_SIZE))
                    overlay.set_alpha(color[3])
                    overlay.fill(color[:3])
                    self.screen.blit(overlay, (x, y))

    def draw_selected_cell(self):
        """Highlight the selected cell"""
        if self.selected_cell:
            gx, gy = self.selected_cell['position']
            x = gx * CELL_SIZE
            y = gy * CELL_SIZE
            pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 3)

    def draw_ui(self):
        """Draw UI information"""
        # Top status bar
        status_bg = pygame.Surface((self.width_pixels, 40))
        status_bg.fill((0, 0, 0))
        status_bg.set_alpha(180)
        self.screen.blit(status_bg, (0, 0))

        # Status text
        status_text = f"Grid: {self.grid_width}x{self.grid_height} | Cell Size: {CELL_SIZE}px"
        if self.selected_cell:
            status_text += f" | Selected: {self.selected_cell['type']} at {self.selected_cell['position']}"

        text_surface = self.font.render(status_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))

        # Controls help
        controls = [
            "G: Toggle Grid | R: Toggle Rooms | ESC: Quit",
            "Click: Select Cell | Mouse wheel: Zoom (future)"
        ]

        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, (255, 255, 255))
            self.screen.blit(control_text, (10, 25 + i * 15))

    def get_cell_at_pixel(self, pixel_x, pixel_y):
        """Get grid cell at pixel coordinates"""
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
                if self.selected_cell:
                    print(f"Selected: {self.selected_cell['type']} at {self.selected_cell['position']}")
                    print(f"Walkable: {self.selected_cell['walkable']}, Is room: {self.selected_cell['is_room']}")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self.show_grid = not self.show_grid
                print(f"Grid overlay: {'ON' if self.show_grid else 'OFF'}")
            elif event.key == pygame.K_r:
                self.show_rooms = not self.show_rooms
                print(f"Room overlay: {'ON' if self.show_rooms else 'OFF'}")
            elif event.key == pygame.K_ESCAPE:
                return False
        return True

    def run(self):
        """Main game loop"""
        print(f"Cluedo Board GUI started: {self.grid_width}x{self.grid_height} grid")
        print("Controls:")
        print("- G: Toggle grid overlay")
        print("- R: Toggle room color overlay")
        print("- Click: Select cells for information")
        print("- ESC: Quit")

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
            self.draw_room_overlay()
            self.draw_grid_overlay()
            self.draw_selected_cell()
            self.draw_ui()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

def main():
    try:
        gui = CluedoBoardGUI()
        gui.run()
    except pygame.error as e:
        print(f"Error loading images: {e}")
        print("Make sure board_mask.png exists in Assets_images/")
        sys.exit(1)

if __name__ == "__main__":
    main()