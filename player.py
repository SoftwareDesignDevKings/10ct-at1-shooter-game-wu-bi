import pygame
import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.

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
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

    def draw(self, surface):
        """Draw the player on the screen."""
        
        if self.facing_left:
            flipped_img = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_img, self.rect)
        else:
            surface.blit(self.image, self.rect)

    def take_damage(self, amount):
        """Reduce the player's health by a given amount, not going below zero."""
        # TODO: self.health = max(0, self.health - amount)
        pass