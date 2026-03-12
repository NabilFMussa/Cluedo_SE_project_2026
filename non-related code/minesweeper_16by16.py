import pygame
import sys
import random
from os import path
import time
import subprocess


pygame.init()
clock = time.time()

GRID_SIZE = 16
CELL_SIZE = min(1280,720)//GRID_SIZE
NUMBER_OF_MINES = (GRID_SIZE * GRID_SIZE) * 0.13
LOSE = False
WIN = False
FLAGS = 0
GENERATED = False

#loading images
tile1 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile1.png")
tile2 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile2.png")
tile3 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile3.png")
tile4 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile4.png")
tile5 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile5.png")
tile6 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile6.png")
tile7 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile7.png")
tile8 = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\Tile8.png")
tileempty = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\TileEmpty.png")
tileexploded = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\TileExploded.png")
tileflag = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\TileFlag.png")
tilemine = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\TileMine.png")
tilenotmine = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\TileNotMine.png")
tileunknown = pygame.image.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\TileUnknown.png")

#scale the images
tile1 = pygame.transform.scale(tile1, (CELL_SIZE, CELL_SIZE))
tile2 = pygame.transform.scale(tile2, (CELL_SIZE, CELL_SIZE))
tile3 = pygame.transform.scale(tile3, (CELL_SIZE, CELL_SIZE))
tile4 = pygame.transform.scale(tile4, (CELL_SIZE, CELL_SIZE))
tile5 = pygame.transform.scale(tile5, (CELL_SIZE, CELL_SIZE))
tile6 = pygame.transform.scale(tile6, (CELL_SIZE, CELL_SIZE))
tile7 = pygame.transform.scale(tile7, (CELL_SIZE, CELL_SIZE))
tile8 = pygame.transform.scale(tile8, (CELL_SIZE, CELL_SIZE))
tileflag = pygame.transform.scale(tileflag, (CELL_SIZE, CELL_SIZE))
tileempty = pygame.transform.scale(tileempty, (CELL_SIZE, CELL_SIZE))
tileunknown = pygame.transform.scale(tileunknown, (CELL_SIZE, CELL_SIZE))
tilemine = pygame.transform.scale(tilemine, (CELL_SIZE, CELL_SIZE))
tileexploded = pygame.transform.scale(tileexploded, (CELL_SIZE, CELL_SIZE))


#surfaces
WINDOW_SIZE = (GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE)
window = pygame.display.set_mode(WINDOW_SIZE)
window_width, window_height = window.get_size()

font = pygame.font.Font(None, 20)

font2 = pygame.font.Font(None, 100)
gameover = font2.render("Game Over", True, "red")
gameover_width, gameover_height = gameover.get_size()

font3 = pygame.font.Font(None, 100)
win = font2.render("You Win", True, "blue")
win_width, win_height = win.get_size()

#create grids
grid = []
for i in range(GRID_SIZE):
    row = []
    for j in range(GRID_SIZE):
        row.append(0)
    grid.append(row)

revealed = []
for i in range(GRID_SIZE):
    row = []
    for j in range(GRID_SIZE):
        row.append(False)
    revealed.append(row)

flag_cells = []
for i in range(GRID_SIZE):
    row = []
    for j in range(GRID_SIZE):
        row.append(False)
    flag_cells.append(row)

def timer():

    with open("leaderboard data\\userTemp.txt", "r") as file:
        user = file.read()

    end_time = time.time()
    elapsed_time = end_time - clock
    elapsed_time = round(elapsed_time, 2)

    import json
    
    
    if WIN == True: 
        data = {user: elapsed_time} 
        with open('C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\leaderboard data\\leaderboard.txt', 'a') as f: 
            json.dump(data, f)
            f.write('\n')

#places mines randomly across the grid
def mine_creation():    
    mines = 0
    while mines < NUMBER_OF_MINES:
        row = random.randint(0 , GRID_SIZE-1)
        col = random.randint(0 , GRID_SIZE-1)
        if grid[row][col] == 0:
            grid[row][col] = 10
            mines += 1

#updates the games grids after each move
def draw_grid():
    #gets the sizes of the scaled images so I can center the sprite properly 
    #really only need one of these since all images are the same size
    tile1_width, tile_height = tile1.get_size()

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if revealed[i][j]:
                window.blit(tileempty, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                pygame.draw.rect(window, "black", pygame.Rect(i*CELL_SIZE, j*CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
                if grid[i][j] == 10:
                    pygame.draw.circle(window, "black", (i*CELL_SIZE + CELL_SIZE // 2, j*CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2)
                elif grid[i][j] == 1:
                    window.blit(tile1, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 2:
                    window.blit(tile2, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 3:
                    window.blit(tile3, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 4:
                    window.blit(tile4, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 5:
                    window.blit(tile5, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 6:
                    window.blit(tile6, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 7:
                    window.blit(tile7, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                elif grid[i][j] == 8:
                    window.blit(tile8, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                
            else:
                window.blit(tileunknown, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                pygame.draw.rect(window, "black", pygame.Rect(i*CELL_SIZE, j*CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
            if flag_cells[i][j]:
                window.blit(tileflag, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
            
            if LOSE == True:
                timer()
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        
                        if grid[i][j] == 10:
                            if i == grid_x and j == grid_y:
                                window.blit(tileexploded, (grid_x*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, grid_y*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                            else: 
                                window.blit(tilemine, (i*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, j*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))


                pygame.mixer.music.load("assets\\retro-explosion-102364.mp3")
                pygame.mixer.music.play(loops=1, start=0, fade_ms=0)
                #displays game over screen
                window.blit(gameover, ((window_width - gameover_width)//2,(window_height - gameover_height)//2))
                pygame.display.update()

                #closes game
                pygame.time.delay(3000)
                pygame.quit()
                sys.exit()

            if WIN == True:
                timer()
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        if flag_cells and revealed:
                            if i == grid_x and j == grid_y:
                                window.blit(tileempty, (grid_x*CELL_SIZE + CELL_SIZE // 2 - tile1_width // 2, grid_y*CELL_SIZE + CELL_SIZE // 2 - tile_height // 2))
                
                pygame.mixer.music.load("C:\\Users\\youip\\Desktop\\uni classes year 0\\Computing Project\\Minesweeper\\assets\\8-bit-video-game-win-level-sound-version-1-145827.mp3")
                pygame.mixer.music.play(loops=1, start=0, fade_ms=0)
                #displays game over screen
                window.blit(win, ((window_width - win_width)//2,(window_height - win_height)//2))
                pygame.display.update()

                #closes game
                pygame.time.delay(3000)
                pygame.quit()
                sys.exit()

#finds all the bombs near the empty cells
def find_close_bombs():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if grid[row][col] != 10:  
                neighbours = 0
                for i in range(max(0, row - 1), min(GRID_SIZE, row + 2)):  
                     for j in range(max(0, col - 1), min(GRID_SIZE, col + 2)):  
                        if grid[i][j] == 10:  
                            neighbours += 1
                grid[row][col] = neighbours

#recursive function
def reveal_all_cells(x, y):
    if x < 0 or y < 0 or x >= GRID_SIZE or y >= GRID_SIZE:
        return
    if revealed[x][y]:
        return
    revealed[x][y] = True
    if grid[x][y] == 0 or flag_cells == True:
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                reveal_all_cells(x+dx, y+dy)

def win_condition():
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if not revealed[i][j] and not flag_cells[i][j]:
                return False
    return True

# Game loop
minesGenerated = False
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit() 
        

        #handles mouse/trackpad input
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            grid_x, grid_y = mouse_x // CELL_SIZE, mouse_y // CELL_SIZE


            if event.button == 1:
                if minesGenerated == False:
                    mine_creation()
                    find_close_bombs()
                    minesGenerated = True
            
            if event.button == 1:
                if not flag_cells[grid_x][grid_y]:
                    reveal_all_cells(grid_x, grid_y)
                    if grid[grid_x][grid_y] == 10:
                        LOSE = True


        
            elif event.button == 3:
                if not revealed[grid_x][grid_y] and flag_cells[grid_x][grid_y]:
                    flag_cells[grid_x][grid_y] = False
                    FLAGS -= 1
                elif not revealed[grid_x][grid_y] and not flag_cells[grid_x][grid_y] and FLAGS < NUMBER_OF_MINES:
                    flag_cells[grid_x][grid_y] = True
                    FLAGS += 1
            
        if win_condition():
            WIN = True

    draw_grid()

    pygame.display.update()