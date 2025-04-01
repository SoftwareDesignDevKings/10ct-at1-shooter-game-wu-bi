import pygame
import app
import math
import random

class BossBullet:
    def __init__(self, x, y, vx, vy):
        """
        Initialise a boss bullet with position and velocity.
        """
        # Position and movement properties
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = 30
        
        # Combat properties
        self.damage = 2 
        self.has_hit_player = False
        
        # Visual representation
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
    def update(self):
        """
        Update bullet position.
        """
        # Update position
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)
        
    def draw(self, surface):
        """
        Draw the bullet on the given surface.
        """
        surface.blit(self.image, self.rect)

class Boss:
    def __init__(self, x, y, assets):
        """
        Initialise the boss enemy with position and assets.
        """
        # Position properties
        self.x = x
        self.y = y
        
        # Combat stats
        self.base_health = 2000
        self.health = self.base_health
        self.max_health = self.base_health
        self.speed = 3
        
        # Animation properties
        self.frames = assets.get("boss", assets["enemies"]["demon"])
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
        # Attack system
        self.attack_timer = 0
        self.attack_interval = 180 
        self.boss_bullets = []
        
        # Movement pattern system
        self.movement_timer = 0
        self.movement_interval = 120
        self.movement_direction = [0, 0]
        
    def update(self, player):
        """
        Update boss state, movement, attacks and bullets.
        """
        # Update animation
        self.animate()
        
        # Update movement pattern
        self.movement_timer += 1
        if self.movement_timer >= self.movement_interval:
            self.movement_timer = 0
            # Randomly change movement direction
            self.movement_direction = [
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            ]
        
        # Apply movement
        self.x += self.movement_direction[0] * self.speed
        self.y += self.movement_direction[1] * self.speed
        
        # Keep boss within screen bounds
        self.x = max(50, min(self.x, app.WIDTH - 50))
        self.y = max(50, min(self.y, app.HEIGHT - 50))
        
        # Update collision rectangle position
        self.rect.center = (self.x, self.y)
        
        # Attack system
        self.attack_timer += 1
        if self.attack_timer >= self.attack_interval:
            self.shoot_at_player(player)
            self.attack_timer = 0
        
        # Update all bullets and handle collisions
        for bullet in self.boss_bullets[:]:
            bullet.update()
            
            if bullet.rect.colliderect(player.rect):
                if not bullet.has_hit_player:
                    player.take_damage(bullet.damage)
                    bullet.has_hit_player = True
            
            # Remove bullets that are off-screen and haven't hit the player
            if ((bullet.x < 0 or bullet.x > app.WIDTH or 
                bullet.y < 0 or bullet.y > app.HEIGHT) and not bullet.has_hit_player):
                self.boss_bullets.remove(bullet)
        
    def shoot_at_player(self, player):
        """
        Fire a spread of bullets toward the player.
        
        Parameters:
            player: The player object to target
        """
        # Calculate direction vector to player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist == 0:
            return
        
        # Normalise and scale velocity so that bullets are slower than player bullets
        vx = (dx / dist) * 5
        vy = (dy / dist) * 5
        
        # Create a spread of bullets at different angles
        spread_angles = [-15, 0, 15]
        for angle in spread_angles:
            rotated_vx = vx * math.cos(math.radians(angle)) - vy * math.sin(math.radians(angle))
            rotated_vy = vx * math.sin(math.radians(angle)) + vy * math.cos(math.radians(angle))
            
            # Create and add the bullet
            bullet = BossBullet(self.x, self.y, rotated_vx, rotated_vy)
            self.boss_bullets.append(bullet)
        
    def animate(self):
        """
        Update the boss animation frame.
        """
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
            # Preserve center position when changing animation frame
            center = self.rect.center
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect()
            self.rect.center = center
        
    def draw(self, surface):
        """
        Draw the boss, health bar, and all active bullets on the screen.
        """
        # Draw boss sprite
        surface.blit(self.image, self.rect)
        
        # Draw health bar
        bar_width = 100
        bar_height = 10
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 20
        
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        current_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))
        
        # Draw all active boss bullets
        for bullet in self.boss_bullets:
            bullet.draw(surface)
            
    def take_damage(self, amount):
        """
        Reduce boss health and check if defeated.
        """
        self.health -= amount
        return self.health <= 0