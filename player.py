import pygame
import app
import math
from bullet import Bullet

class Player:
    def __init__(self, x, y, assets):
        """Initialise the player with position and image assets."""
        # Base position coordinates
        self.x = x
        self.y = y

        # Movement settings
        self.speed = app.PLAYER_SPEED
        
        # Animation properties
        self.animations = assets["player"]
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        
        # Invulnerability properties (after taking damage)
        self.invulnerable = False
        self.invulnerable_time = 60
        self.invulnerable_timer = 0
        
        # Initialise sprite properties
        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.facing_left = False
        
        # Player stats
        self.xp = 0
        self.health = 5
        self.level = 1
        
        # Bullet/weapon properties
        self.bullet_speed = 10
        self.bullet_size = 10
        self.bullet_count = 1
        self.shoot_cooldown = 20
        self.shoot_timer = 0
        self.bullets = []
        self.bullet_base_damage = 1
        self.bullet_pierce = 0
        
        # Power-up states
        self.has_shield = False
        self.shield_timer = 0
        self.original_speed = app.PLAYER_SPEED
        self.speed_boost_active = False
        self.speed_boost_timer = 0
        self.damage_multiplier = 1
        self.damage_boost_timer = 0
        self.magnet_active = False
        self.magnet_timer = 0
        self.magnet_radius = 175

    def handle_input(self):
        """Check and respond to keyboard/mouse input for player movement."""
        # Get all currently pressed keys
        keys = pygame.key.get_pressed()

        # Initialise velocity components
        vel_x, vel_y = 0, 0

        # Update velocity based on directional keys (supports both WASD and arrow keys)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vel_x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vel_x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            vel_y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            vel_y += self.speed

        # Apply velocity to position
        self.x += vel_x
        self.y += vel_y

        # Constrain player position to screen boundaries, both vertically and horizontally
        self.x = max(0, min(self.x, app.WIDTH))
        self.y = max(0, min(self.y, app.HEIGHT))
        self.rect.center = (self.x, self.y)

        # Set animation state based on movement
        if vel_x != 0 or vel_y != 0:
            self.state = "run"
        else:
            self.state = "idle"

        # Update facing direction based on horizontal movement
        if vel_x < 0:
            self.facing_left = True
        elif vel_x > 0:
            self.facing_left = False

    def update(self):
        """Update player state, bullets, animations and power-ups."""
        # Handle invulnerability countdown
        if self.invulnerable:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False  # Turn off invulnerability when timer expires
        
        # Update all active bullets and remove those that go off-screen
        for bullet in self.bullets:
            bullet.update()
            # Remove bullets that leave the screen
            if bullet.y < 0 or bullet.y > app.HEIGHT or bullet.x < 0 or bullet.x > app.WIDTH:
                self.bullets.remove(bullet)

        # Animation handling
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            
            # Preserve center position when changing animation frame
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

        # Handle shield power-up countdown
        if self.has_shield:
            self.shield_timer -= 1
        if self.shield_timer <= 0:
            self.has_shield = False
    
        # Handle speed boost power-up countdown
        if self.speed_boost_active:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost_active = False
                self.speed = self.original_speed
        
        # Handle damage boost power-up countdown
        if self.damage_multiplier > 1:
            self.damage_boost_timer -= 1
            if self.damage_boost_timer <= 0:
                self.damage_multiplier = 1
        
        # Handle magnet power-up countdown
        if self.magnet_active:
            self.magnet_timer -= 1
            if self.magnet_timer <= 0:
                self.magnet_active = False

    def draw(self, surface):
        """Draw the player, bullets, and active power-up effects on the screen."""
        # Draw the player sprite (flipped if facing left)
        if self.facing_left:
            flipped_img = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_img, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        # Draw shield effect if active
        if self.has_shield:
            shield_surface = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
            # Draw blue circle on shield surface
            pygame.draw.circle(shield_surface, (0, 0, 255, 128),
                            (shield_surface.get_width() // 2, shield_surface.get_height() // 2),
                            max(self.rect.width, self.rect.height) // 2 + 5)
            # Position shield around player and draw it
            shield_rect = shield_surface.get_rect(center=self.rect.center)
            surface.blit(shield_surface, shield_rect)

        # Draw magnet effect if active
        if self.magnet_active:
            # Create semi-transparent magnet field surface
            magnet_surface = pygame.Surface((self.magnet_radius * 2, self.magnet_radius * 2), pygame.SRCALPHA)
            # Draw yellow circle on magnet surface
            pygame.draw.circle(magnet_surface, (255, 255, 0, 30),
                            (magnet_surface.get_width() // 2, magnet_surface.get_height() // 2),
                            self.magnet_radius)
            # Position magnet field around player and draw it
            magnet_rect = magnet_surface.get_rect(center=self.rect.center)
            surface.blit(magnet_surface, magnet_rect)

        # Draw all active bullets
        for bullet in self.bullets:
            bullet.draw(surface)

    def take_damage(self, amount):
        """Handle player taking damage, accounting for shield and invulnerability."""
        # Skip damage if player is currently invulnerable
        if self.invulnerable:
            return
            
        # Handle damage absorption
        if self.has_shield:
            self.has_shield = False
            self.shield_timer = 0
        else:
            # Reduce health by damage amount (not below zero)
            self.health = max(0, self.health - amount)
            self.invulnerable_timer = self.invulnerable_time
            self.invulnerable = True

    def shoot_toward_position(self, tx, ty):
        """Fire bullet(s) toward a specific target position."""
        # Check if shooting is on cooldown
        if self.shoot_timer >= self.shoot_cooldown:
            return

        # Calculate direction vector from player to target
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return

        # Normalise direction vector and scale by bullet speed
        vx = (dx / dist) * self.bullet_speed
        vy = (dy / dist) * self.bullet_speed

        # Calculate spread angle for multiple bullets by calculating radians
        angle_spread = 10
        base_angle = math.atan2(vy, vx)
        mid = (self.bullet_count - 1) / 2  

        # Create bullets with appropriate spread
        for i in range(self.bullet_count):
            offset = i - mid
            spread_radians = math.radians(angle_spread * offset)
            angle = base_angle + spread_radians

            # Calculate final velocity components with spread
            final_vx = math.cos(angle) * self.bullet_speed
            final_vy = math.sin(angle) * self.bullet_speed

            # Create and configure bullet
            bullet = Bullet(self.x, self.y, final_vx, final_vy, self.bullet_size)
            bullet.damage = self.bullet_base_damage * self.damage_multiplier
            bullet.max_pierce = self.bullet_pierce
            self.bullets.append(bullet)
            
        self.shoot_timer = 0

    def shoot_toward_mouse(self, pos):
        """Fire bullet(s) toward the mouse cursor position."""
        mx, my = pos  # Mouse coords
        self.shoot_toward_position(mx, my)

    def shoot_toward_enemy(self, enemy):
        """Fire bullet(s) toward a specific enemy."""
        self.shoot_toward_position(enemy.x, enemy.y)

    def add_xp(self, amount):
        """Add experience points to the player."""
        self.xp += amount

    def apply_powerup(self, powerup_type, duration):
        """Apply various power-up effects to the player."""
        if powerup_type == "shield":
            # Activate shield protection
            self.has_shield = True
            self.shield_timer = duration
        elif powerup_type == "speed":
            # Activate speed boost
            self.speed_boost_active = True
            self.speed = self.original_speed * 1.5
            self.speed_boost_timer = duration
        elif powerup_type == "damage":
            # Activate damage boost
            self.damage_multiplier = 2
            self.damage_boost_timer = duration
        elif powerup_type == "magnet":
            # Activate XP magnet effect
            self.magnet_active = True
            self.magnet_timer = duration