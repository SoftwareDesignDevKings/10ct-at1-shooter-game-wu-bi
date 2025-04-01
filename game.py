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
    """
    Main game class that handles initialisation, game loop, rendering,
    and all game mechanics including collisions, spawning, and upgrades.
    """
    def __init__(self):
        """
        Initialise the game, setting up the display, loading assets,
        and initialising game state variables.
        """
        # Initialise pygame library
        pygame.init()  

        # Create game window with dimensions from app config
        self.screen = pygame.display.set_mode((app.WIDTH, app.HEIGHT))
        pygame.display.set_caption("Shooter")

        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()

        # Load all game assets (images, sounds, etc.)
        self.assets = app.load_assets()

        # Load and create font objects for UI text
        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)

        # Create tiled background using random floor tiles
        self.background = self.create_random_background(
        app.WIDTH, app.HEIGHT, self.assets["floor_tiles"]
        )

        # Game state flags
        self.running = True  # Controls main game loop
        self.game_over = False  # Tracks if player has died

        # Initialise collectible item lists
        self.coins = []
        self.healthpacks = []

        # Enemy spawning configuration
        self.enemies = []
        self.enemy_spawn_timer = 0  # Tracks time until next spawn
        self.enemy_spawn_interval = 60  # Frames between enemy spawns
        self.enemies_per_spawn = 1  # Number of enemies to spawn at once
        self.enemy_health_multiplier = 1.0  # Scales enemy health based on level

        # Power-up spawning configuration
        self.powerups = []
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 300  # Frames between power-up spawns

        # Level-up system variables
        self.in_level_up_menu = False  # Tracks if upgrade menu is active
        self.upgrade_options = []  # Stores available upgrades when leveling up

        # Boss enemy variables
        self.boss = None  # Reference to current boss (if any)
        self.boss_spawned = False  # Tracks if a boss is currently active
        self.should_spawn_boss = False  # Flag to trigger boss spawn
        self.boss_count = 0

        # Reset game to initial state
        self.reset_game()


    def reset_game(self):
        """
        Reset all game variables to their starting values for a new game.
        Creates a new player at the center of the screen.
        """
        # Create player at center of screen
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        
        # Reset all entity lists and spawn variables
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1
        self.enemy_health_multiplier = 1.0
        self.coins = []
        self.powerups = []
        self.healthpacks = []
        self.boss = None
        self.boss_spawned = False
        self.should_spawn_boss = False
        self.boss_count = 0
        
        # Reset game state flags
        self.game_over = False

    def create_random_background(self, width, height, floor_tiles):
        """
        Create a randomly tiled background surface using provided floor tile images.
        
        Args:
            width: Width of the background
            height: Height of the background
            floor_tiles: List of tile image surfaces
            
        Returns:
            A pygame Surface with randomly placed floor tiles
        """
        # Create empty surface for background
        bg = pygame.Surface((width, height))
        
        # Get dimensions of tile images
        tile_w = floor_tiles[0].get_width()
        tile_h = floor_tiles[0].get_height()

        # Place random tiles in a grid pattern to cover entire background
        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y))

        return bg

    def run(self):
        """
        Main game loop that runs until the game is exited.
        Handles timing, events, updates, and rendering.
        """
        # Continue running until self.running is set to False
        while self.running:
            # Limit frame rate to FPS defined in app config
            self.clock.tick(app.FPS)    
            
            # Process user input
            self.handle_events()  

            # Update game state if not paused by game over or level-up menu
            if (not self.game_over and not self.in_level_up_menu):
                self.update()
    
            # Render game elements to screen
            self.draw()     

        # Clean up pygame resources when exiting
        pygame.quit()

    def handle_events(self):
        """
        Process user input (keyboard, mouse, quitting).
        Handles different input contexts based on game state.
        """
        # Process all pending pygame events
        for event in pygame.event.get():
            # Check if user closed the window
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle keyboard input
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    # Game over context: restart or quit
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False  
                else:
                    if not self.in_level_up_menu:
                        # Normal gameplay context
                        if event.key == pygame.K_SPACE:
                            # Auto-aim at nearest enemy when spacebar is pressed
                            nearest_enemy = self.find_nearest_enemy()
                            if nearest_enemy:
                                self.player.shoot_toward_enemy(nearest_enemy)
                    else:
                        # Level-up menu context: select upgrade using number keys
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            index = event.key - pygame.K_1  # Convert key to index (0-3)
                            if 0 <= index < len(self.upgrade_options):
                                upgrade = self.upgrade_options[index]
                                self.apply_upgrade(self.player, upgrade)
                                self.in_level_up_menu = False
                    
            # Handle mouse input for manual aiming
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.player.shoot_toward_mouse(event.pos)         

    def update(self):
        """
        Update all game objects and check for collisions.
        This function handles the core game logic for each frame.
        """
        # Skip updates if level-up menu is active
        if self.in_level_up_menu:
            return

        # Update player movement and state
        self.player.handle_input()
        self.player.update()

        # Update all enemies' position and behavior
        for enemy in self.enemies:
            enemy.update(self.player)

        # Apply coin magnetism if player has magnet power-up
        self.attract_coins()

        # Check for all types of collisions
        self.check_player_enemy_collisions()
        self.check_bullet_enemy_collisions()
        self.check_player_coin_collisions()
        self.check_player_powerup_collisions()
        self.check_player_healthpack_collisions()

        # Check for player death
        if self.player.health <= 0:
            self.game_over = True
            return
        
        # Spawn boss if flagged and not in level-up menu
        if self.should_spawn_boss and not self.in_level_up_menu:
            self.spawn_boss()
            self.should_spawn_boss = False
        
        # Redundant boss spawn check (likely a bug or leftover code)
        if hasattr(self, 'should_spawn_boss') and self.should_spawn_boss and not self.in_level_up_menu:
            self.spawn_boss()
            self.should_spawn_boss = False

        # Spawn new enemies based on timer
        self.spawn_enemies()
        
        # Check if player has enough XP to level up
        self.check_for_level_up()

        # Update boss and check for boss-related collisions
        if self.boss:
            self.boss.update(self.player)
            self.check_boss_player_collisions()
            self.check_bullet_boss_collisions()

        # Spawn power-ups based on timer
        self.spawn_powerups()
        

    def draw(self):
        """
        Render all game elements to the screen.
        Draws background, entities, UI, and any overlay screens.
        """
        # Draw tiled background
        self.screen.blit(self.background, (0, 0))

        # Draw collectible items
        for coin in self.coins:
            coin.draw(self.screen)

        for powerup in self.powerups:
            powerup.draw(self.screen)        

        # Draw boss before player and UI elements (so it appears behind overlays)
        if self.boss:
            self.boss.draw(self.screen)

        # Draw player if game is still active
        if not self.game_over:
            self.player.draw(self.screen)

        # Draw all enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw health packs
        for healthpack in self.healthpacks:
            healthpack.draw(self.screen) 

        # Draw UI: Health display
        hp = max(0, min(self.player.health, 5))
        health_img = self.assets["health"][hp]
        self.screen.blit(health_img, (10, 10))

        # Draw UI: XP counter
        xp_text_surf = self.font_small.render(f"XP: {self.player.xp}", True, (255, 255, 255))
        self.screen.blit(xp_text_surf, (10, 70))

        # Draw UI: XP needed for next level
        next_level_xp = self.player.level * self.player.level * 6
        xp_to_next = max(0, next_level_xp - self.player.xp)
        xp_next_surf = self.font_small.render(f"Next Lvl XP: {xp_to_next}", True, (255, 255, 255))
        self.screen.blit(xp_next_surf, (10, 100))

        # Draw UI: Current level
        level_surf = self.font_small.render(f"Level: {self.player.level}", True, (255, 255, 0))
        self.screen.blit(level_surf, (10, 130))

        # Draw game over screen if player has died
        if self.game_over:
            self.draw_game_over_screen()

        # Draw level-up menu if active
        if self.in_level_up_menu:
            self.draw_upgrade_menu()

        # Update the display to show all drawn elements
        pygame.display.flip()
    
    def spawn_enemies(self):
        """
        Spawn new enemies from outside the screen at regular intervals.
        Enemies appear from random edges of the screen.
        Only spawns if boss is not active.
        """
        if not self.boss_spawned:
            for _ in range(self.enemies_per_spawn):
                # Increment spawn timer
                self.enemy_spawn_timer += 1
                
                # Check if it's time to spawn enemies
                if self.enemy_spawn_timer >= self.enemy_spawn_interval:
                    self.enemy_spawn_timer = 0

                    # Spawn multiple enemies based on enemies_per_spawn
                    for _ in range(self.enemies_per_spawn):
                        # Choose a random side of the screen to spawn from
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

                        # Choose random enemy type and create enemy
                        enemy_type = random.choice(list(self.assets["enemies"].keys()))
                        enemy = Enemy(x, y, enemy_type, self.assets["enemies"], health_multiplier=self.enemy_health_multiplier)
                        self.enemies.append(enemy)

    def check_player_enemy_collisions(self):
        """
        Check if player is colliding with any enemies.
        Applies damage to player if no shield is active.
        Applies knockback to enemies on collision.
        """
        # Check if any enemy is colliding with player
        collided = False
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                collided = True
                break

        if collided:
            if self.player.has_shield:
                # Shield absorbs the damage and gets depleted
                self.player.has_shield = False
                self.player.shield_timer = 0
                
                # Still apply knockback to enemies even with shield
                px, py = self.player.x, self.player.y
                for enemy in self.enemies:
                    enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)
            else:
                # No shield, player takes damage
                self.player.take_damage(1)
                
                # Apply knockback to all enemies
                px, py = self.player.x, self.player.y
                for enemy in self.enemies:
                    enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)

    def draw_game_over_screen(self):
        """
        Draw the game over screen overlay with restart instructions.
        """
        # Dark semi-transparent overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Game Over text in large font
        game_over_surf = self.font_large.render("GAME OVER!", True, (255, 0, 0))
        game_over_rect = game_over_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 50))
        self.screen.blit(game_over_surf, game_over_rect)

        # Restart instructions in small font
        prompt_surf = self.font_small.render("Press R to Play Again or ESC to Quit", True, (255, 255, 255))
        prompt_rect = prompt_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 + 20))
        self.screen.blit(prompt_surf, prompt_rect)

    def find_nearest_enemy(self):
        """
        Find the enemy closest to the player.
        Used for auto-aim functionality when pressing space.
        
        Returns:
            The nearest Enemy or Boss object, or None if no enemies exist
        """
        if not self.enemies:
            return None
            
        # Start with no nearest enemy and infinite distance
        nearest = None
        min_dist = float('inf')
        px, py = self.player.x, self.player.y
        
        # Check all regular enemies
        for enemy in self.enemies:
            dist = math.sqrt((enemy.x - px)**2 + (enemy.y - py)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = enemy
        
        # Also check boss if present
        if self.boss:
            boss_dist = math.sqrt((self.boss.x - px)**2 + (self.boss.y - py)**2)
            if boss_dist < min_dist:
                min_dist = boss_dist
                nearest = self.boss

        return nearest
    
    def check_bullet_enemy_collisions(self):
        """
        Check for collisions between player bullets and enemies.
        Handles bullet pierce mechanic, damage application, and enemy death.
        Spawns coins and occasional health packs when enemies die.
        """
        bullets_to_remove = []
        enemies_to_remove = []

        for bullet in self.player.bullets:
            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    # Check if this bullet has already hit this enemy (for pierce mechanic)
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

                            # Small chance (1/45) to drop a health pack
                            if random.randint(1, 45) == 1:
                                new_healthpack = HealthPack(enemy.x, enemy.y)
                                self.healthpacks.append(new_healthpack)
                                
                            enemies_to_remove.append(enemy)

                        # Check if bullet should be removed based on pierce count
                        if bullet.pierce_count > bullet.max_pierce:
                            bullets_to_remove.append(bullet)
                            break

        # Remove all bullets that have reached max pierce
        for bullet in bullets_to_remove:
            if bullet in self.player.bullets:
                self.player.bullets.remove(bullet)
    
        # Remove all enemies that have been killed
        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)

    def check_player_coin_collisions(self):
        """
        Check if player collides with any coins and collect them.
        Each coin adds 1 XP to the player.
        """
        coins_collected = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                coins_collected.append(coin)
                self.player.add_xp(1)

        # Remove collected coins
        for c in coins_collected:
            if c in self.coins:
                self.coins.remove(c) 

    def check_player_healthpack_collisions(self):
        """
        Check if player collides with any health packs and collect them.
        Each health pack restores 1 health point (up to max of 5).
        """
        healthpacks_collected = []
        for healthpack in self.healthpacks:
            if healthpack.rect.colliderect(self.player.rect):
                healthpacks_collected.append(healthpack)
                # Restore 1 health point but don't exceed max health (5)
                if self.player.health < 5:
                    self.player.health += 1
                    
        # Remove collected health packs
        for x in healthpacks_collected:
            if x in self.healthpacks:
                self.healthpacks.remove(x)

    def check_boss_player_collisions(self):
        """
        Check if player collides with the boss and apply damage.
        """
        if self.boss and self.boss.rect.colliderect(self.player.rect):
            self.player.take_damage(1)

    def pick_random_upgrades(self, num):
        """
        Select a random set of upgrades to offer the player when leveling up.
        
        Args:
            num: Number of upgrades to select
            
        Returns:
            List of selected upgrade dictionaries
        """
        possible_upgrades = [
            {"name": "Bigger Bullet",  "desc": "Bullet size +5"},
            {"name": "Faster Bullet",  "desc": "Bullet speed +2"},
            {"name": "Extra Bullet",   "desc": "Fire additional bullet"},
            {"name": "Shorter Cooldown", "desc": "Shoot more frequently"},
            {"name": "Increased Damage", "desc": "Bullet damage +1"},
            {"name": "Bullet Pierce", "desc": "Bullets pierce +1"},
        ]
        # Return random selection of upgrades without duplicates
        return random.sample(possible_upgrades, k=num)
    
    def apply_upgrade(self, player, upgrade):
        """
        Apply the selected upgrade to the player.
        """
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
        """
        Draw the level-up menu with upgrade options.
        Shows title and numbered upgrade options.
        """
        # Dark semi-transparent overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("Choose an Upgrade!", True, (255, 255, 0))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 3 - 50))
        self.screen.blit(title_surf, title_rect)

        # Draw each upgrade option
        for i, upgrade in enumerate(self.upgrade_options):
            text_str = f"{i+1}. {upgrade['name']} - {upgrade['desc']}"
            option_surf = self.font_small.render(text_str, True, (255, 255, 255))
            line_y = app.HEIGHT // 3 + i * 40
            option_rect = option_surf.get_rect(center=(app.WIDTH // 2, line_y))
            self.screen.blit(option_surf, option_rect)

    def check_for_level_up(self):
        """
        Check if player has enough XP to level up.
        If so, increase level, show upgrade menu, and increase game difficulty.
        """
        # Calculate XP needed for next level based on current level
        xp_needed = self.player.level * self.player.level * 6
        if self.player.xp >= xp_needed:
            # Leveled up
            self.player.level += 1
            self.in_level_up_menu = True
            self.upgrade_options = self.pick_random_upgrades(4)

            # Increase enemy spawn rate every 2 levels
            if self.player.level % 2 == 0:
                self.enemies_per_spawn += 1

            # Gradually increase enemy health up to a cap of 4.0
            if self.enemy_health_multiplier <= 4.0:
                # Increase enemy health multiplier by 25% each level
                self.enemy_health_multiplier += 0.25

            # Spawn a boss every 5 levels
            if self.player.level % 5 == 0:
                self.should_spawn_boss = True

    def spawn_boss(self):
        """
        Spawn a boss enemy at the center of the screen.
        Only spawns if not currently in upgrade menu.
        """
        # Prevent boss from spawning during upgrade menu
        if not self.in_level_up_menu:
            self.boss_count += 1
            
            # Create the boss
            self.boss = Boss(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
            
            # Scale the boss health based on how many bosses have been spawned
            # First boss has base health, each subsequent boss has double the health
            health_multiplier = 1.3 ** (self.boss_count - 1)
            self.boss.health = self.boss.base_health * health_multiplier
            self.boss.max_health = self.boss.health
            
            self.boss_spawned = True


    def check_bullet_boss_collisions(self):
        """
        Check for collisions between player bullets and the boss.
        Handles boss damage and death, spawning a coin when defeated.
        """
        if not self.boss:
            return
        
        # Create a copy to avoid modification during iteration
        bullets_to_check = self.player.bullets.copy()

        for bullet in bullets_to_check:
            # Ensure the bullet and boss rect still exist
            if (bullet in self.player.bullets and 
                hasattr(bullet, 'rect') and 
                hasattr(self.boss, 'rect')):
                
                if bullet.rect.colliderect(self.boss.rect):
                    # Apply damage to boss with player's damage multiplier
                    enemy_killed = self.boss.take_damage(bullet.damage * self.player.damage_multiplier)
                    
                    if enemy_killed:
                        # Boss defeated, drop a coin
                        new_coin = Coin(self.boss.x, self.boss.y)
                        self.coins.append(new_coin)
                        self.boss = None
                        self.boss_spawned = False
                        break  # Exit loop after boss is defeated

    def spawn_powerups(self):
        """
        Randomly spawn power-ups over time.
        Has a 25% chance to spawn a power-up when timer expires.
        """
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.powerup_spawn_interval:
            self.powerup_spawn_timer = 0
            
            # Random chance to spawn a power-up (25% chance)
            if random.random() < 0.25:
                # Choose random position away from edges
                x = random.randint(50, app.WIDTH - 50)
                y = random.randint(50, app.HEIGHT - 50)
                
                # Get random power-up type
                powerup_type = PowerUp.get_random_type()
                powerup = PowerUp(x, y, powerup_type)
                self.powerups.append(powerup)

    def check_player_powerup_collisions(self):
        """
        Check if player collides with any power-ups and apply their effects.
        """
        powerups_collected = []
        for powerup in self.powerups:
            if powerup.rect.colliderect(self.player.rect):
                powerups_collected.append(powerup)
                # Apply power-up effect to player
                self.player.apply_powerup(powerup.type, powerup.duration)
        
        # Remove collected power-ups
        for p in powerups_collected:
            if p in self.powerups:
                self.powerups.remove(p)

        
    def attract_coins(self):
        """
        Move coins toward the player if magnet power-up is active.
        Coins within the magnet radius are drawn toward the player.
        """
        # Get current magnet radius from player
        magnet_radius = self.player.magnet_radius
        if not self.player.magnet_active:
            return
            
        # Speed at which coins move toward player
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