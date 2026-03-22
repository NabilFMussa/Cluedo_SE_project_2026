import pygame
import sys

# Initialize Pygame
pygame.init()

# Configuration
BOARD_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/game board.png"
MASK_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/board_mask.png"

# Grid settings
CELL_SIZE = 20  # Size of each grid cell in pixels
GRID_COLOR = (200, 200, 200)  # Light gray for grid lines
WALL_COLOR = (0, 0, 0)  # Black for walls

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

# Room display colors (for visualization)
ROOM_DISPLAY_COLORS = {
    "HALLWAY": (220, 220, 220),     # Light gray
    "STUDY": (144, 238, 144),       # Light green
    "LIBRARY": (173, 216, 230),     # Light blue
    "BILLIARD ROOM": (255, 182, 193), # Light red
    "CONSERVATORY": (224, 255, 255), # Light cyan
    "BALL ROOM": (255, 182, 255),   # Light magenta
    "KITCHEN": (255, 255, 224),     # Light yellow
    "DINING ROOM": (210, 180, 140), # Light brown
    "LOUNGE": (221, 160, 221),      # Light purple
    "HALL": (255, 218, 185),        # Light orange
    "CENTER": (211, 211, 211),      # Light grey
    "DOOR": (255, 105, 180),        # Hot pink
    "START": (255, 160, 122),       # Light coral
    "WALL": (0, 0, 0),              # Black
}

class CluedoGrid:
    def __init__(self, mask_path):
        # Load the mask image
        self.mask_img = pygame.image.load(mask_path)
        self.mask_pixels = pygame.PixelArray(self.mask_img)

        # Get dimensions
        self.width_pixels, self.height_pixels = self.mask_img.get_size()
        self.grid_width = self.width_pixels // CELL_SIZE
        self.grid_height = self.height_pixels // CELL_SIZE

        # Create the grid
        self.grid = self._create_grid()

        # Screen setup
        self.screen_width = self.grid_width * CELL_SIZE
        self.screen_height = self.grid_height * CELL_SIZE
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cluedo Board Grid")

        # Font for UI
        self.font = pygame.font.SysFont("Arial", 16)

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
                    'position': (gx, gy)
                }
                row.append(cell)
            grid.append(row)

        return grid

    def draw_grid(self):
        """Draw the grid on the screen"""
        self.screen.fill((255, 255, 255))  # White background

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                cell = self.grid[gy][gx]

                # Calculate cell position
                x = gx * CELL_SIZE
                y = gy * CELL_SIZE

                # Draw cell background
                color = ROOM_DISPLAY_COLORS.get(cell['type'], (255, 0, 255))  # Magenta for unknown
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE))

                # Draw grid lines
                pygame.draw.rect(self.screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def draw_ui(self):
        """Draw UI information"""
        # Room legend
        y_offset = 10
        self.screen.blit(self.font.render("Room Legend:", True, (0, 0, 0)), (self.screen_width + 10, y_offset))

        y_offset += 30
        for room_type, color in ROOM_DISPLAY_COLORS.items():
            # Draw color swatch
            pygame.draw.rect(self.screen, color, (self.screen_width + 10, y_offset, 20, 20))
            pygame.draw.rect(self.screen, (0, 0, 0), (self.screen_width + 10, y_offset, 20, 20), 1)

            # Draw text
            text = self.font.render(room_type, True, (0, 0, 0))
            self.screen.blit(text, (self.screen_width + 40, y_offset))

            y_offset += 25

    def get_cell_at_pixel(self, pixel_x, pixel_y):
        """Get grid cell at pixel coordinates"""
        gx = pixel_x // CELL_SIZE
        gy = pixel_y // CELL_SIZE

        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return self.grid[gy][gx]
        return None

    def is_walkable(self, gx, gy):
        """Check if grid position is walkable"""
        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return self.grid[gy][gx]['walkable']
        return False

    def get_neighbors(self, gx, gy):
        """Get walkable neighboring cells"""
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # left, right, up, down

        for dx, dy in directions:
            nx, ny = gx + dx, gy + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))

        return neighbors

def main():
    # Check if mask exists
    try:
        grid = CluedoGrid(MASK_IMG)
    except pygame.error:
        print(f"Error: Could not load mask image at {MASK_IMG}")
        print("Please run board_mask_script.py first to create the mask.")
        sys.exit(1)

    print(f"Grid created: {grid.grid_width}x{grid.grid_height}")
    print("Controls:")
    print("- Click on cells to see information")
    print("- Press ESC to quit")

    # Mouse info
    selected_cell = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                selected_cell = grid.get_cell_at_pixel(mouse_x, mouse_y)
                if selected_cell:
                    print(f"Selected cell: {selected_cell['type']} at {selected_cell['position']}")
                    print(f"Walkable: {selected_cell['walkable']}, Is room: {selected_cell['is_room']}")

        # Draw everything
        grid.draw_grid()

        # Highlight selected cell
        if selected_cell:
            gx, gy = selected_cell['position']
            x = gx * CELL_SIZE
            y = gy * CELL_SIZE
            pygame.draw.rect(grid.screen, (255, 255, 0), (x, y, CELL_SIZE, CELL_SIZE), 3)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()