import app

class Coin:
    """
    "Coin class representing collectible items in the game."
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = app.pygame.Surface((15, 15), app.pygame.SRCALPHA)
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect(center=(self.x, self.y))
    
    # Draw the coin on the screen
    def draw(self, surface):
        surface.blit(self.image, self.rect)