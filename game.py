import pygame
import random
import os

import app
from player import Player
from enemy import Enemy
from coin import Coin
from powerup import PowerUp
from healthpack import HealthPack
from boss import Boss
import math


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

        self.coins = []
        self.healthpacks = []

        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 60
        self.enemies_per_spawn = 1
        self.enemy_health_multiplier = 1.0

        self.powerups = []
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 300

        self.in_level_up_menu = False
        self.upgrade_options = []

        self.boss = None
        self.boss_spawned = False
        self.should_spawn_boss = False

        self.reset_game()


    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1
        self.enemy_health_multiplier = 1.0
        self.coins = []
        self.powerups = []
        self.healthpacks = []
        self.boss = None
        self.boss_spawned = False
        self.should_spawn_boss = False  # Add this flag

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

            if (not self.game_over and not self.in_level_up_menu):
                self.update()
    
            self.draw()     

        pygame.quit()

    def handle_events(self):
        """Process user input (keyboard, mouse, quitting)."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False  
                else:
                    if not self.in_level_up_menu:
                        if event.key == pygame.K_SPACE:
                            nearest_enemy = self.find_nearest_enemy()
                            if nearest_enemy:
                                self.player.shoot_toward_enemy(nearest_enemy)
                    else:
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            index = event.key - pygame.K_1  # 0,1,2,3
                            if 0 <= index < len(self.upgrade_options):
                                upgrade = self.upgrade_options[index]
                                self.apply_upgrade(self.player, upgrade)
                                self.in_level_up_menu = False
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.player.shoot_toward_mouse(event.pos)         

    def update(self):
        if self.in_level_up_menu:
            return

        self.player.handle_input()
        self.player.update()

        for enemy in self.enemies:
            enemy.update(self.player)

        self.attract_coins()

        self.check_player_enemy_collisions()
        self.check_bullet_enemy_collisions()
        self.check_player_coin_collisions()
        self.check_player_powerup_collisions()
        self.check_player_healthpack_collisions()

        if self.player.health <= 0:
            self.game_over = True
            return
        
        if self.should_spawn_boss and not self.in_level_up_menu:
            self.spawn_boss()
            self.should_spawn_boss = False
        
        if hasattr(self, 'should_spawn_boss') and self.should_spawn_boss and not self.in_level_up_menu:
            self.spawn_boss()
            self.should_spawn_boss = False

        self.spawn_enemies()
        self.check_for_level_up()

        if self.boss:
            self.boss.update(self.player)
            self.check_boss_player_collisions()
            self.check_bullet_boss_collisions()

        self.spawn_powerups()
        

    def draw(self):
        """Render all game elements to the screen."""
        self.screen.blit(self.background, (0, 0))

        for coin in self.coins:
            coin.draw(self.screen)

        for powerup in self.powerups:
            powerup.draw(self.screen)        

        # Draw boss before player and UI elements (so it appears behind overlays)
        if self.boss:
            self.boss.draw(self.screen)

        if not self.game_over:
            self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for healthpack in self.healthpacks:  # Draw health packs
            healthpack.draw(self.screen) 

        hp = max(0, min(self.player.health, 5))
        health_img = self.assets["health"][hp]
        self.screen.blit(health_img, (10, 10))

        xp_text_surf = self.font_small.render(f"XP: {self.player.xp}", True, (255, 255, 255))
        self.screen.blit(xp_text_surf, (10, 70))

        next_level_xp = self.player.level * self.player.level * 6
        xp_to_next = max(0, next_level_xp - self.player.xp)
        xp_next_surf = self.font_small.render(f"Next Lvl XP: {xp_to_next}", True, (255, 255, 255))
        self.screen.blit(xp_next_surf, (10, 100))

        level_surf = self.font_small.render(f"Level: {self.player.level}", True, (255, 255, 0))
        self.screen.blit(level_surf, (10, 130))

        # Draw overlays after game elements
        if self.game_over:
            self.draw_game_over_screen()

        if self.in_level_up_menu:
            self.draw_upgrade_menu()

        pygame.display.flip()
    
    def spawn_enemies(self):
        if not self.boss_spawned:
            for _ in range(self.enemies_per_spawn):
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
                        enemy = Enemy(x, y, enemy_type, self.assets["enemies"], health_multiplier=self.enemy_health_multiplier)
                        self.enemies.append(enemy)

    def check_player_enemy_collisions(self):
        collided = False
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                collided = True
                break

        if collided:
            if self.player.has_shield:
                # Shield absorbs the damage
                self.player.has_shield = False
                self.player.shield_timer = 0
                
                # Still apply knockback to enemies
                px, py = self.player.x, self.player.y
                for enemy in self.enemies:
                    enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)
            else:
                self.player.take_damage(1)
                px, py = self.player.x, self.player.y
                for enemy in self.enemies:
                    enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)

    def draw_game_over_screen(self):
            # Dark overlay
            overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            # Game Over text
            game_over_surf = self.font_large.render("GAME OVER!", True, (255, 0, 0))
            game_over_rect = game_over_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 50))
            self.screen.blit(game_over_surf, game_over_rect)

            # Prompt to restart or quit
            prompt_surf = self.font_small.render("Press R to Play Again or ESC to Quit", True, (255, 255, 255))
            prompt_rect = prompt_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 + 20))
            self.screen.blit(prompt_surf, prompt_rect)

    def find_nearest_enemy(self):
        if not self.enemies:
            return None
        nearest = None
        min_dist = float('inf')
        px, py = self.player.x, self.player.y
        for enemy in self.enemies:
            dist = math.sqrt((enemy.x - px)**2 + (enemy.y - py)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = enemy
        
        if self.boss:
            boss_dist = math.sqrt((self.boss.x - px)**2 + (self.boss.y - py)**2)
            if boss_dist < min_dist:
                min_dist = boss_dist
                nearest = self.boss

        return nearest
    
    def check_bullet_enemy_collisions(self):
        bullets_to_remove = []
        enemies_to_remove = []

        for bullet in self.player.bullets:

            for enemy in self.enemies:

                if bullet.rect.colliderect(enemy.rect):
                    if bullet.can_hit_enemy(enemy):
                        # Mark this enemy as hit by this bullet
                        bullet.hit_enemies.add(enemy)
                        
                        # Apply damage with damage multiplier
                        enemy_killed = enemy.take_damage(bullet.damage * self.player.damage_multiplier)
                    
                        # Increment pierce count
                        bullet.pierce_count += 1

                        if enemy_killed:
                            # Enemy is dead, drop a coin
                            new_coin = Coin(enemy.x, enemy.y)
                            self.coins.append(new_coin) 

                            if random.randint(1, 45) == 1:
                                new_healthpack = HealthPack(enemy.x, enemy.y)
                                self.healthpacks.append(new_healthpack)
                            enemies_to_remove.append(enemy)

                        # Check if bullet should be removed based on pierce count
                        if bullet.pierce_count > bullet.max_pierce:
                            bullets_to_remove.append(bullet)
                            break

        for bullet in bullets_to_remove:
            if bullet in self.player.bullets:
                self.player.bullets.remove(bullet)
    
        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)

    def check_player_coin_collisions(self):
        coins_collected = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                coins_collected.append(coin)
                self.player.add_xp(1)

        for c in coins_collected:
            if c in self.coins:
                self.coins.remove(c) 

    def check_player_healthpack_collisions(self):
        """Check if player collides with any health packs and collect them."""
        healthpacks_collected = []
        for healthpack in self.healthpacks:
            if healthpack.rect.colliderect(self.player.rect):
                healthpacks_collected.append(healthpack)
                # Restore 1 health point but don't exceed max health (5)
                if self.player.health < 5:
                    self.player.health += 1
                    
        for x in healthpacks_collected:
            if x in self.healthpacks:
                self.healthpacks.remove(x)

    def check_boss_player_collisions(self):
        if self.boss and self.boss.rect.colliderect(self.player.rect):
            self.player.take_damage(1)

    def pick_random_upgrades(self, num):
        possible_upgrades = [
            {"name": "Bigger Bullet",  "desc": "Bullet size +5"},
            {"name": "Faster Bullet",  "desc": "Bullet speed +2"},
            {"name": "Extra Bullet",   "desc": "Fire additional bullet"},
            {"name": "Shorter Cooldown", "desc": "Shoot more frequently"},
            {"name": "Increased Damage", "desc": "Bullet damage +1"},
            {"name": "Bullet Pierce", "desc": "Bullets pierce +1"},
        ]
        return random.sample(possible_upgrades, k=num)
    
    def apply_upgrade(self, player, upgrade):
        name = upgrade["name"]
        if name == "Bigger Bullet":
            player.bullet_size += 5
        elif name == "Faster Bullet":
            player.bullet_speed += 2
        elif name == "Extra Bullet":
            player.bullet_count += 1
        elif name == "Shorter Cooldown":
            player.shoot_cooldown = max(1, int(player.shoot_cooldown * 0.8))
        elif name == "Increased Damage":
            player.bullet_base_damage += 1
        elif name == "Bullet Pierce":
            player.bullet_pierce += 1

    def draw_upgrade_menu(self):
        # Dark overlay behind the menu
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("Choose an Upgrade!", True, (255, 255, 0))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 3 - 50))
        self.screen.blit(title_surf, title_rect)

        # Options
        for i, upgrade in enumerate(self.upgrade_options):
            text_str = f"{i+1}. {upgrade['name']} - {upgrade['desc']}"
            option_surf = self.font_small.render(text_str, True, (255, 255, 255))
            line_y = app.HEIGHT // 3 + i * 40
            option_rect = option_surf.get_rect(center=(app.WIDTH // 2, line_y))
            self.screen.blit(option_surf, option_rect)

    def check_for_level_up(self):
        xp_needed = self.player.level * self.player.level * 1
        if self.player.xp >= xp_needed:
            # Leveled up
            self.player.level += 1
            self.in_level_up_menu = True
            self.upgrade_options = self.pick_random_upgrades(4)

            # Increase enemy spawns each time we level up
            if self.player.level % 2 == 0:
                self.enemies_per_spawn += 1

                # Increase enemy health each time we level up
            if self.enemy_health_multiplier <= 4.0:
                # Increase enemy health multiplier by 25% each level
                # but cap it at 3.0
                # This means that at level 5, enemy health will be 2.0
                # and at level 10, it will be 3.0
                # This is to prevent enemies from becoming too strong
                # too quickly
                # and to keep the game balanced
                # and fun to play
                # and to keep the game challenging
                self.enemy_health_multiplier += 0.25

            if self.player.level % 5 == 0:
                self.should_spawn_boss = True

    def spawn_boss(self):
        # Prevent boss from spawning during upgrade menu
        if not self.in_level_up_menu:
            self.boss = Boss(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
            self.boss_spawned = True


    def check_bullet_boss_collisions(self):
        if not self.boss:
            return
        
        bullets_to_check = self.player.bullets.copy()

        for bullet in bullets_to_check:
            # Ensure the bullet and boss rect still exist
            if (bullet in self.player.bullets and 
                hasattr(bullet, 'rect') and 
                hasattr(self.boss, 'rect')):
                
                if bullet.rect.colliderect(self.boss.rect):
                    enemy_killed = self.boss.take_damage(bullet.damage * self.player.damage_multiplier)
                    
                    if enemy_killed:
                        # Boss defeated
                        new_coin = Coin(self.boss.x, self.boss.y)
                        self.coins.append(new_coin)
                        self.boss = None
                        self.boss_spawned = False
                        break  # Exit loop after boss is defeated

    def spawn_powerups(self):
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.powerup_spawn_interval:
            self.powerup_spawn_timer = 0
            
            # Random chance to spawn a power-up (25% chance)
            if random.random() < 0.25:
                x = random.randint(50, app.WIDTH - 50)
                y = random.randint(50, app.HEIGHT - 50)
                powerup_type = PowerUp.get_random_type()
                powerup = PowerUp(x, y, powerup_type)
                self.powerups.append(powerup)

    def check_player_powerup_collisions(self):
        powerups_collected = []
        for powerup in self.powerups:
            if powerup.rect.colliderect(self.player.rect):
                powerups_collected.append(powerup)
                self.player.apply_powerup(powerup.type, powerup.duration)
        
        for p in powerups_collected:
            if p in self.powerups:
                self.powerups.remove(p)

        
    def attract_coins(self):
        magnet_radius = self.player.magnet_radius
        if not self.player.magnet_active:
            return
        attraction_speed = 7
        
        for coin in self.coins:
            # Calculate distance between player and coin
            dx = self.player.x - coin.x
            dy = self.player.y - coin.y
            distance = (dx**2 + dy**2)**0.5
            
            # If coin is within magnet radius, move it toward player
            if distance <= magnet_radius and distance > 0:
                # Calculate movement vector
                move_x = (dx / distance) * attraction_speed
                move_y = (dy / distance) * attraction_speed
                
                # Move the coin toward player
                coin.x += move_x
                coin.y += move_y 
                coin.rect.center = (coin.x, coin.y)