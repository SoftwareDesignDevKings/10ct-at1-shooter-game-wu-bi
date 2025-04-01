import pygame
import app
import math

class Enemy:
    def __init__(self, x, y, enemy_type, enemy_assets, speed=app.DEFAULT_ENEMY_SPEED, health_multiplier=1):
        """
        Initialise the enemy with position, type, and attributes.
        Parameters:
            x, y: Initial position coordinates
            enemy_type: Type of enemy, used to select the right sprites
            enemy_assets: Dictionary of animation frames for different enemy types
            speed: Movement speed, defaults to app.DEFAULT_ENEMY_SPEED
            health_multiplier: Multiplier for enemy health, for scaling difficulty
        """
        # Position and movement properties
        self.x = x
        self.y = y
        self.speed = speed       

        # Animation properties
        self.frames = enemy_assets[enemy_type]
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
        self.enemy_type = enemy_type 
        self.facing_left = False

        # Knockback system - used when enemy is hit by player's attack
        self.knockback_dist_remaining = 0
        self.knockback_dx = 0
        self.knockback_dy = 0

        # Health and UI display properties
        self.base_health = 2
        self.max_health = int(self.base_health * health_multiplier)
        self.health = self.max_health
        self.health_bar_width = 40
        self.health_bar_height = 5
        self.health_bar_padding = 2

        
    def update(self, player):
        """
        Main update function called each frame.
        Handles movement, knockback, and animation.
        """
        # Handle knockback if active, otherwise move toward player
        if self.knockback_dist_remaining > 0:
            self.apply_knockback()
        else:
            self.move_toward_player(player)
        
        # Update animation frames
        self.animate()


    def move_toward_player(self, player):
        """
        Calculate direction toward player and move enemy in that direction.
        """
        # Calculates direction vector toward player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = (dx**2 + dy**2) ** 0.5
        
        if dist != 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        
        self.facing_left = dx < 0
        
        # Updates enemy position
        self.rect.center = (self.x, self.y)


    def apply_knockback(self):
        """
        Apply knockback effect when enemy is hit.
        Moves enemy away from the source of damage.
        """
        step = min(app.ENEMY_KNOCKBACK_SPEED, self.knockback_dist_remaining)
        self.knockback_dist_remaining -= step
        
        # Apply knockback movement and direction with knockback
        self.x += self.knockback_dx * step
        self.y += self.knockback_dy * step

        if self.knockback_dx < 0:
            self.facing_left = True
        else:
            self.facing_left = False

        self.rect.center = (self.x, self.y)


    def animate(self):
        """
        Handle animation cycling through enemy sprite frames.
        """
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            center = self.rect.center
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect()
            self.rect.center = center


    def draw(self, surface):
        """
        Draw the enemy sprite and health bar on the game surface.
        Handles sprite flipping based on direction.
        """
        # Draw enemy sprite (flipped if facing left)
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        # Draw health bar above enemy
        self.draw_health_bar(surface)

        
    def draw_health_bar(self, surface):
        """
        Draw a health bar above the enemy showing current health as a proportion of max health.
        """
        # Health bar position (above the enemy)
        bar_x = self.rect.centerx - self.health_bar_width // 2
        bar_y = self.rect.top - 10  # 10 pixels above the enemy
        

        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, self.health_bar_width, self.health_bar_height))
        
        # Draw filled portion of health bar (green)
        fill_width = int((self.health / self.max_health) * self.health_bar_width)
        
        if fill_width > 0:
            pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, fill_width, self.health_bar_height))


    def set_knockback(self, px, py, dist):
        """
        Set up knockback effect when enemy takes damage.
        """
        # Calculate knockback direction (away from damage source)
        dx = self.x - px
        dy = self.y - py
        length = math.sqrt(dx*dx + dy*dy)
        if length != 0:
            self.knockback_dx = dx / length
            self.knockback_dy = dy / length
            self.knockback_dist_remaining = dist

    def take_damage(self, amount):
        """
        Reduce enemy health by given amount and check if enemy is defeated.
        """
        self.health -= amount
        return self.health <= 0