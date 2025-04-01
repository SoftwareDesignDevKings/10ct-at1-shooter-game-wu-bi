import pygame
import app
import math
import random

class BossBullet:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = 30  # Larger bullet size
        self.damage = 2  # Initial damage
        self.poison_damage = 2  # Poison damage
        self.poison_timer = 0
        self.poison_interval = 120  # 2 seconds at 60 FPS
        self.has_hit_player = False  # Track if bullet has hit player
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.image.fill((0, 255, 0))  # Green color
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)
        
        # Increment poison timer only if the bullet has hit the player
        if self.has_hit_player:
            self.poison_timer += 1
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def apply_poison_damage(self, player):
        if self.has_hit_player and self.poison_timer >= self.poison_interval:
            player.take_damage(self.poison_damage)
            self.poison_timer = 0
            return True  # Indicate damage was applied
        return False  # No damage applied

class Boss:
    def __init__(self, x, y, assets):
        self.x = x
        self.y = y
        
        # Boss-specific attributes
        self.base_health = 2000  # Base health value that will be scaled
        self.health = self.base_health  # Initial health equals base health
        self.max_health = self.base_health
        self.speed = 3  # Slightly faster movement
        
        # Use a unique enemy type or create a specific boss sprite
        self.frames = assets.get("boss", assets["enemies"]["demon"])  # Placeholder, you might want a unique boss sprite
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
        # Boss-specific attack variables
        self.attack_timer = 0
        self.attack_interval = 180  # 3 seconds at 60 FPS
        self.boss_bullets = []
        
        # Movement pattern
        self.movement_timer = 0
        self.movement_interval = 120  # Change direction every 2 seconds
        self.movement_direction = [0, 0]
        
    def update(self, player):
        # Animate
        self.animate()
        
        # Move in a random pattern
        self.movement_timer += 1
        if self.movement_timer >= self.movement_interval:
            self.movement_timer = 0
            # Randomly change movement direction
            self.movement_direction = [
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            ]
        
        # Move with current direction
        self.x += self.movement_direction[0] * self.speed
        self.y += self.movement_direction[1] * self.speed
        
        # Keep boss within screen bounds
        self.x = max(50, min(self.x, app.WIDTH - 50))
        self.y = max(50, min(self.y, app.HEIGHT - 50))
        
        # Update rect position
        self.rect.center = (self.x, self.y)
        
        # Attack pattern
        self.attack_timer += 1
        if self.attack_timer >= self.attack_interval:
            self.shoot_at_player(player)
            self.attack_timer = 0
        
        # Update boss bullets and check for collisions
        for bullet in self.boss_bullets[:]:
            bullet.update()
            
            # Check for collision with player
            if bullet.rect.colliderect(player.rect):
                # Apply direct damage on hit if bullet hasn't hit player yet
                if not bullet.has_hit_player:
                    player.take_damage(bullet.damage)
                    bullet.has_hit_player = True
                
                # Apply poison damage periodically
                # The bullet will now apply poison damage over time as long as it has hit the player
                bullet.apply_poison_damage(player)
            
            # If the bullet has hit the player, keep it around for poison damage
            # Only remove it if it's out of screen and hasn't hit the player
            if ((bullet.x < 0 or bullet.x > app.WIDTH or 
                bullet.y < 0 or bullet.y > app.HEIGHT) and not bullet.has_hit_player):
                self.boss_bullets.remove(bullet)
        
    def shoot_at_player(self, player):
        # Calculate direction to player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist == 0:
            return
        
        # Normalize and scale velocity
        vx = (dx / dist) * 5  # Slower bullet speed
        vy = (dy / dist) * 5
        
        # Spread multiple bullets
        spread_angles = [-15, 0, 15]
        for angle in spread_angles:
            # Rotate velocity vector
            rotated_vx = vx * math.cos(math.radians(angle)) - vy * math.sin(math.radians(angle))
            rotated_vy = vx * math.sin(math.radians(angle)) + vy * math.cos(math.radians(angle))
            
            bullet = BossBullet(self.x, self.y, rotated_vx, rotated_vy)
            self.boss_bullets.append(bullet)
        
    def animate(self):
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            center = self.rect.center
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect()
            self.rect.center = center
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
        # Draw health bar
        bar_width = 100
        bar_height = 10
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 20
        
        # Background (red)
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Health (green)
        current_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))
        
        # Draw boss bullets
        for bullet in self.boss_bullets:
            bullet.draw(surface)
            
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0