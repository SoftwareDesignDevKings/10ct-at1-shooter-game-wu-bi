import app
import pygame

class HealthPack:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
        # Create a red cross for the health pack
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 0, 0), (8, 2, 4, 16))  # Vertical line
        pygame.draw.rect(self.image, (255, 0, 0), (2, 8, 16, 4))  # Horizontal line
        
        # Add a white border around the health pack
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, 20, 20), 2)
        
        self.rect = self.image.get_rect(center=(self.x, self.y))
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)