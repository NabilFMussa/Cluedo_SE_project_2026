"""Quick board viewer for checking the colour mask against the image. It is mainly a dev helper, not the actual game.
"""

import pygame
import sys

pygame.init()

BOARD_IMG = "Assets_images/game board.png"
MASK_IMG = "Assets_images/board_mask.png"

CELL_SIZE = 20
GRID_COLOR = (100, 100, 100)
HIGHLIGHT_COLOR = (255, 255, 0)

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

ROOM_DISPLAY_COLORS = {
    "HALLWAY": (220, 220, 220, 128),
    "STUDY": (144, 238, 144, 128),
    "LIBRARY": (173, 216, 230, 128),
    "BILLIARD ROOM": (255, 182, 193, 128),
    "CONSERVATORY": (224, 255, 255, 128),
    "BALL ROOM": (255, 182, 255, 128),
    "KITCHEN": (255, 255, 224, 128),
    "DINING ROOM": (210, 180, 140, 128),
    "LOUNGE": (221, 160, 221, 128),
    "HALL": (255, 218, 185, 128),
    "CENTER": (211, 211, 211, 128),
    "DOOR": (255, 105, 180, 128),
    "START": (255, 160, 122, 128),
    "WALL": (0, 0, 0, 128),
}

class CluedoBoardGUI:
    """Tiny utility window for inspecting board cells and overlays."""

    def __init__(self):
        self.board_img = pygame.image.load(BOARD_IMG)
        self.mask_img = pygame.image.load(MASK_IMG)

        self.width_pixels, self.height_pixels = self.board_img.get_size()
        self.grid_width = self.width_pixels // CELL_SIZE
        self.grid_height = self.height_pixels // CELL_SIZE

        self.grid = self.create_grid()

        self.screen = pygame.display.set_mode((self.width_pixels, self.height_pixels))
        pygame.display.set_caption("Cluedo Board - Grid Setup")

        self.font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 12)

        self.show_grid = True
        self.show_rooms = True
        self.selected_cell = None
        self.characters = {}

    def create_grid(self):
        """Read the mask image into cell data the rest of the UI can use."""
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

                row.append({
                    "type": room_type,
                    "walkable": room_type != "WALL",
                    "is_room": room_type not in ["HALLWAY", "WALL", "DOOR", "START", "CENTER"],
                    "position": (gx, gy),
                    "pixel_pos": (px, py),
                })
            grid.append(row)
        return grid

    def draw_board(self):
        """Paint the raw board image first."""
        self.screen.blit(self.board_img, (0, 0))

    def draw_grid_overlay(self):
        """Draw the debug grid if that toggle is on."""
        if not self.show_grid:
            return

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                x = gx * CELL_SIZE
                y = gy * CELL_SIZE
                pygame.draw.rect(self.screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def draw_room_overlay(self):
        """Drop a light colour tint over non-wall cells."""
        if not self.show_rooms:
            return

        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                cell = self.grid[gy][gx]
                if cell["type"] == "WALL":
                    continue

                x = gx * CELL_SIZE
                y = gy * CELL_SIZE
                color = ROOM_DISPLAY_COLORS.get(cell["type"], (255, 0, 255, 128))
                box = pygame.Surface((CELL_SIZE, CELL_SIZE))
                box.set_alpha(color[3])
                box.fill(color[:3])
                self.screen.blit(box, (x, y))

    def draw_selected_cell(self):
        """Outline the currently picked cell, if there is one."""
        if not self.selected_cell:
            return
        gx, gy = self.selected_cell["position"]
        x = gx * CELL_SIZE
        y = gy * CELL_SIZE
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 3)

    def draw_ui(self):
        """Show a small status strip and a couple of controls."""
        status_bg = pygame.Surface((self.width_pixels, 40))
        status_bg.fill((0, 0, 0))
        status_bg.set_alpha(180)
        self.screen.blit(status_bg, (0, 0))

        status_text = f"Grid: {self.grid_width}x{self.grid_height} | Cell Size: {CELL_SIZE}px"
        if self.selected_cell:
            status_text += f" | Selected: {self.selected_cell['type']} at {self.selected_cell['position']}"

        text_surface = self.font.render(status_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))

        help_lines = [
            "G: Toggle Grid | R: Toggle Rooms | ESC: Quit",
            "Click: Select Cell | Mouse wheel: Zoom (future)"
        ]

        for i, line in enumerate(help_lines):
            txt = self.small_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt, (10, 25 + i * 15))

    def get_cell_at_pixel(self, pixel_x, pixel_y):
        """Translate mouse coords into a grid cell."""
        gx = pixel_x // CELL_SIZE
        gy = pixel_y // CELL_SIZE

        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return self.grid[gy][gx]
        return None

    def handle_input(self, event):
        """Handle the handful of keys and clicks this viewer needs."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
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
        """Main loop for the viewer."""
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
                elif running:
                    running = self.handle_input(event)

            self.draw_board()
            self.draw_room_overlay()
            self.draw_grid_overlay()
            self.draw_selected_cell()
            self.draw_ui()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

def main():
    """Start the board viewer and fail loudly if the images are missing."""
    try:
        gui = CluedoBoardGUI()
        gui.run()
    except pygame.error as e:
        print(f"Error loading images: {e}")
        print("Make sure board_mask.png exists in Assets_images/")
        sys.exit(1)

if __name__ == "__main__":
    main()
