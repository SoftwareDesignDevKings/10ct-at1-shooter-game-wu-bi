import app
import random

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type
        self.image = app.pygame.Surface((20, 20), app.pygame.SRCALPHA)
        
        # Set color based on power-up type
        if type == "shield":
            self.color = (0, 0, 255)  # Blue for shield
        elif type == "speed":
            self.color = (0, 255, 0)  # Green for speed
        elif type == "damage":
            self.color = (255, 0, 0)  # Red for damage multiplier
        else:
            self.color = (255, 255, 255)  # White for unknown
        
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.duration = 300  # Power-up effect duration (5 seconds at 60 FPS)
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
    
    def get_random_type():
        return random.choice(["shield", "speed", "damage"])