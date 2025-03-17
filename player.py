import pygame
import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.
import math

from bullet import Bullet

class Player:
    def __init__(self, x, y, assets):
        """Initialize the player with position and image assets."""
        self.x = x
        self.y = y

        self.speed = app.PLAYER_SPEED
        self.animations = assets["player"]
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8


        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.facing_left = False


        # TODO: 4. Add player health 
        self.xp = 0
        self.health = 5
        
        self.bullet_speed = 10
        self.bullet_size = 10
        self.bullet_count = 1
        self.shoot_cooldown = 20
        self.shoot_timer = 0
        self.bullets = []

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

        self.level = 1

    def handle_input(self):
        """Check and respond to keyboard/mouse input."""

        # TODO: 1. Capture Keyboard Input
        keys = pygame.key.get_pressed()

        # velocity in X, Y direction
        vel_x, vel_y = 0, 0

        # TODO: 2. Adjust player position with keys pressed, updating the player position to vel_x and vel_y
        if keys[pygame.K_LEFT]:
            vel_x -= self.speed
        if keys[pygame.K_RIGHT]:
            vel_x += self.speed
        if keys[pygame.K_UP]:
            vel_y -= self.speed
        if keys[pygame.K_DOWN]:
            vel_y += self.speed

        self.x += vel_x
        self.y += vel_y

        self.x = max(0, min(self.x, app.WIDTH))
        self.y = max(0, min(self.y, app.HEIGHT))
        self.rect.center = (self.x, self.y)

        # Determine animation state
        if vel_x != 0 or vel_y != 0:
            self.state = "run"
        else:
            self.state = "idle"

        # Facing direction
        if vel_x < 0:
            self.facing_left = True
        elif vel_x > 0:
            self.facing_left = False

    def update(self):
        for bullet in self.bullets:
            bullet.update()
            if bullet.y < 0 or bullet.y > app.HEIGHT or bullet.x < 0 or bullet.x > app.WIDTH:
                self.bullets.remove(bullet)

        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

        if self.has_shield:
            self.shield_timer -= 1
        if self.shield_timer <= 0:
            self.has_shield = False
    
        if self.speed_boost_active:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost_active = False
                self.speed = self.original_speed
        
        if self.damage_multiplier > 1:
            self.damage_boost_timer -= 1
            if self.damage_boost_timer <= 0:
                self.damage_multiplier = 1
        
        if self.magnet_active:
            self.magnet_timer -= 1
            if self.magnet_timer <= 0:
                self.magnet_active = False

    def draw(self, surface):
        """Draw the player on the screen."""
        
        if self.facing_left:
            flipped_img = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_img, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        if self.has_shield:
            shield_surface = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (0, 0, 255, 128), 
                            (shield_surface.get_width() // 2, shield_surface.get_height() // 2),
                            max(self.rect.width, self.rect.height) // 2 + 5)
            shield_rect = shield_surface.get_rect(center=self.rect.center)
            surface.blit(shield_surface, shield_rect)

        if self.magnet_active:
            magnet_surface = pygame.Surface((self.magnet_radius * 2, self.magnet_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(magnet_surface, (255, 255, 0, 30), 
                            (magnet_surface.get_width() // 2, magnet_surface.get_height() // 2),
                            self.magnet_radius)
            magnet_rect = magnet_surface.get_rect(center=self.rect.center)
            surface.blit(magnet_surface, magnet_rect)

        for bullet in self.bullets:
            bullet.draw(surface)

    def take_damage(self, amount):
        """Reduce the player's health by a given amount, not going below zero."""
        # TODO: self.health = max(0, self.health - amount)
        self.health = max(0, self.health - amount)
        if self.has_shield:
            # Shield absorbs the damage
            self.has_shield = False
            self.shield_timer = 0
        else:
            self.health = max(0, self.health - amount)

    def shoot_toward_position(self, tx, ty):
        if self.shoot_timer >= self.shoot_cooldown:
            return

        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return

        vx = (dx / dist) * self.bullet_speed
        vy = (dy / dist) * self.bullet_speed

        angle_spread = 10
        base_angle = math.atan2(vy, vx)
        mid = (self.bullet_count - 1) / 2

        for i in range(self.bullet_count):
            offset = i - mid
            spread_radians = math.radians(angle_spread * offset)
            angle = base_angle + spread_radians

            final_vx = math.cos(angle) * self.bullet_speed
            final_vy = math.sin(angle) * self.bullet_speed

            bullet = Bullet(self.x, self.y, final_vx, final_vy, self.bullet_size)
            bullet.damage = bullet.damage * self.damage_multiplier
            self.bullets.append(bullet)
        self.shoot_timer = 0
    
    def shoot_toward_mouse(self, pos):
        mx, my = pos # m denotes mouse
        self.shoot_toward_position(mx, my)

    def shoot_toward_enemy(self, enemy):
        self.shoot_toward_position(enemy.x, enemy.y)

    def add_xp(self, amount):
        self.xp += amount


    def apply_powerup(self, powerup_type, duration):
        if powerup_type == "shield":
            self.has_shield = True
            self.shield_timer = duration
        elif powerup_type == "speed":
            self.speed_boost_active = True
            self.speed = self.original_speed * 1.5  # 50% speed boost
            self.speed_boost_timer = duration
        elif powerup_type == "damage":
            self.damage_multiplier = 2  # Double damage
            self.damage_boost_timer = duration
        elif powerup_type == "magnet":
            self.magnet_active = True
            self.magnet_timer = duration