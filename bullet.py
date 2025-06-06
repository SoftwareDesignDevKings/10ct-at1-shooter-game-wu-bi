import app

class Bullet:
    """
    Bullet class representing projectiles fired by the boss.
    It handles movement, collision detection, and damage application.
    """
    def __init__(self, x, y, vx, vy, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.damage = 1
        self.pierce_count = 0
        self.max_pierce = 0
        self.hit_enemies = set()


        self.image = app.pygame.Surface((self.size, self.size), app.pygame.SRCALPHA)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(center=(self.x, self.y))
    
    # Update the bullet's position based on its velocity
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)
    
    # Draw the bullet on the screen
    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def can_hit_enemy(self, enemy):
        return enemy not in self.hit_enemies