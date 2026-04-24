"""Small tool for painting the board mask by hand. when the room mask needs fixing or rebuilding.
"""

import pygame
import os

pygame.init()

# file paths (might move these later)
BOARD_IMG = "Assets_images/game board.png"
MASK_OUTPUT = "Assets_images/board_mask.png"

# quick mapping for rooms (keys → name + colour)
ROOMS = {
    pygame.K_1: ("HALLWAY", (255, 255, 255)),
    pygame.K_2: ("STUDY", (0, 255, 0)),
    pygame.K_3: ("LIBRARY", (0, 0, 255)),
    pygame.K_4: ("BILLIARD ROOM", (255, 0, 0)),
    pygame.K_5: ("CONSERVATORY", (0, 255, 255)),
    pygame.K_6: ("BALL ROOM", (255, 0, 255)),
    pygame.K_7: ("KITCHEN", (255, 255, 0)),
    pygame.K_8: ("DINING ROOM", (128, 64, 0)),
    pygame.K_9: ("LOUNGE", (128, 0, 128)),

    # extras
    pygame.K_0: ("HALL TOP", (255, 128, 0)),
    pygame.K_x: ("CENTER", (128, 128, 128)),
    pygame.K_d: ("DOORS", (255, 20, 147)),
    pygame.K_p: ("START", (150, 0, 0)),
}

# load board
img = pygame.image.load(BOARD_IMG)
screen = pygame.display.set_mode(img.get_size())

# load or create mask
if os.path.exists(MASK_OUTPUT):
    print("Loading existing mask...")
    mask = pygame.image.load(MASK_OUTPUT).convert()
else:
    print("No mask found, starting new one")
    mask = pygame.Surface(img.get_size())
    mask.fill((0, 0, 0))  # default = wall

# current tool
current_name = "STUDY"
current_color = (0, 255, 0)

points = []
font = pygame.font.SysFont("Arial", 18)

print("Keys 1–9 change room")
print("Click to add points, SPACE to fill")
print("S = save, Z = clear points")

running = True

while running:
    screen.blit(img, (0, 0))

    # draw mask (transparent)
    overlay = mask.copy()
    overlay.set_alpha(0)   # might tweak this later
    screen.blit(overlay, (0, 0))

    # show current tool
    text = font.render(f"{current_name} {current_color}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            points.append(event.pos)

        elif event.type == pygame.KEYDOWN:
            # switch tool
            if event.key in ROOMS:
                current_name, current_color = ROOMS[event.key]
                print("Now using:", current_name)

            elif event.key == pygame.K_SPACE:
                if len(points) > 2:
                    pygame.draw.polygon(mask, current_color, points)
                    points = []

            elif event.key == pygame.K_z:
                points = []  # just reset current shape

            elif event.key == pygame.K_s:
                pygame.image.save(mask, MASK_OUTPUT)
                print("Saved.")

    # draw points (rough preview)
    if points:
        for p in points:
            pygame.draw.circle(screen, (255, 0, 0), p, 4)

        if len(points) > 1:
            pygame.draw.lines(screen, (255, 255, 0), False, points, 2)

    pygame.display.flip()

# save on exit just in case
pygame.image.save(mask, MASK_OUTPUT)
pygame.quit()
