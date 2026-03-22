import pygame
import os

# --- CONFIGURATION ---
BOARD_IMG = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/game board.png"
MASK_OUTPUT = "/home/nabil-faizal-mussa/Desktop/Cluedo_SE_project_2026/Assets_images/board_mask.png"

# Room Palette mapping keys to (Name, Color)
# --- COMPLETE ROOM PALETTE ---
ROOMS = {
    # Numbers 1-9
    pygame.K_1: ("HALLWAY", (255, 255, 255)),     # White
    pygame.K_2: ("STUDY", (0, 255, 0)),           # Lime Green
    pygame.K_3: ("LIBRARY", (0, 0, 255)),         # Blue
    pygame.K_4: ("BILLIARD ROOM", (255, 0, 0)),   # Red
    pygame.K_5: ("CONSERVATORY", (0, 255, 255)),  # Cyan
    pygame.K_6: ("BALL ROOM", (255, 0, 255)),     # Magenta
    pygame.K_7: ("KITCHEN", (255, 255, 0)),       # Yellow
    pygame.K_8: ("DINING ROOM", (128, 64, 0)),    # Brown
    pygame.K_9: ("LOUNGE", (128, 0, 128)),        # Purple
    
    # Extra Keys
    pygame.K_0: ("HALL (TOP)", (255, 128, 0)),    # Orange
    pygame.K_x: ("THE CENTER X", (128, 128, 128)),# Grey
    pygame.K_d: ("DOORS", (255, 20, 147)),        # Neon Pink
    pygame.K_p: ("START SLOTS", (150, 0, 0)),     # Dark Red
}
pygame.init()
img = pygame.image.load(BOARD_IMG)
screen = pygame.display.set_mode(img.get_size())

# --- PERSISTENCE LOGIC ---
if os.path.exists(MASK_OUTPUT):
    print("Found existing mask! Loading progress...")
    mask_surface = pygame.image.load(MASK_OUTPUT).convert()
else:
    print("No mask found. Starting fresh.")
    mask_surface = pygame.Surface(img.get_size())
    mask_surface.fill((0, 0, 0)) # Default to Black (Walls)

# Default starting state
current_room_name = "STUDY"
current_color = (0, 255, 0)
points = []
font = pygame.font.SysFont("Arial", 18)

print(f"Current Tool: {current_room_name}. Use 1-9 to switch rooms.")
print("SPACE to fill. 'S' to save. 'Z' to clear current points.")

running = True
while running:
    screen.blit(img, (0, 0))
    
    # Draw mask with transparency so you can see the board underneath
    overlay = mask_surface.copy()
    overlay.set_alpha(160) 
    screen.blit(overlay, (0, 0))
    
    # UI Overlay
    status_text = font.render(f"Tool: {current_room_name} | Color: {current_color}", True, (255, 255, 255))
    pygame.draw.rect(screen, (0,0,0), (5, 5, 400, 30))
    screen.blit(status_text, (10, 10))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            points.append(event.pos)
            
        if event.type == pygame.KEYDOWN:
            # Switch Colors/Rooms
            if event.key in ROOMS:
                current_room_name, current_color = ROOMS[event.key]
                print(f"Switched to: {current_room_name}")
            
            # Fill Area
            if event.key == pygame.K_SPACE and len(points) > 2:
                pygame.draw.polygon(mask_surface, current_color, points)
                points = []
            
            # Undo current point set
            if event.key == pygame.K_z:
                points = []
                
            # Manual Save
            if event.key == pygame.K_s:
                pygame.image.save(mask_surface, MASK_OUTPUT)
                print("Mask Saved!")

    # Visualization of points being clicked
    if len(points) > 0:
        for p in points: pygame.draw.circle(screen, (255, 0, 0), p, 4)
        if len(points) > 1: pygame.draw.lines(screen, (255, 255, 0), False, points, 2)

    pygame.display.flip()

pygame.image.save(mask_surface, MASK_OUTPUT)
pygame.quit()