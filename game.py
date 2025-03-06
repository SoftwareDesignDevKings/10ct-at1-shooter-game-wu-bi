# game.py
import pygame
import random
import os

import app
from player import Player
from enemy import Enemy

class Game:
    def __init__(self):
        pygame.init()  

        self.screen = pygame.display.set_mode((app.WIDTH, app.HEIGHT))
        pygame.display.set_caption("Shooter")

        self.clock = pygame.time.Clock()

        self.assets = app.load_assets()

        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)

        self.background = self.create_random_background(
        app.WIDTH, app.HEIGHT, self.assets["floor_tiles"]
        )

        self.running = True
        self.game_over = False

        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 60
        self.enemies_per_spawn = 1

        self.reset_game()


    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1

        self.game_over = False

    def create_random_background(self, width, height, floor_tiles):
        bg = pygame.Surface((width, height))
        tile_w = floor_tiles[0].get_width()
        tile_h = floor_tiles[0].get_height()

        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y))

        return bg

    def run(self):
        while self.running:
            self.clock.tick(app.FPS)    
            self.handle_events()  
            if (not self.game_over):
                self.update()      
            self.draw()     

        pygame.quit()

    def handle_events(self):
        """Process user input (keyboard, mouse, quitting)."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        self.player.handle_input()
        self.player.update()

        for enemy in self.enemies:
            enemy.update(self.player)

        self.check_player_enemy_collisions()
        self.spawn_enemies()
        

    def draw(self):
        """Render all game elements to the screen."""
        self.screen.blit(self.background, (0, 0))

        if not self.game_over:
            self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        pygame.display.flip()
    
    def spawn_enemies(self):
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0

            for _ in range(self.enemies_per_spawn):
                side = random.choice(["top", "bottom", "left", "right"])
                if side == "top":
                    x = random.randint(0, app.WIDTH)
                    y = -app.SPAWN_MARGIN
                elif side == "bottom":
                    x = random.randint(0, app.WIDTH)
                    y = app.HEIGHT + app.SPAWN_MARGIN
                elif side == "left":
                    x = -app.SPAWN_MARGIN
                    y = random.randint(0, app.HEIGHT)
                else:
                    x = app.WIDTH + app.SPAWN_MARGIN
                    y = random.randint(0, app.HEIGHT)

                enemy_type = random.choice(list(self.assets["enemies"].keys()))
                enemy = Enemy(x, y, enemy_type, self.assets["enemies"])
                self.enemies.append(enemy)

    def check_player_enemy_collisions(self):
        collided = False
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                collided = True
                break

        if collided:
            # self.player.take_damage(1)
            px, py = self.player.x, self.player.y
            for enemy in self.enemies:
                enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)