# enemies/base.py
import pygame
import math
from constants import MAX_WATER, MAX_CHLOROPHYLL


class BaseEnemy(pygame.sprite.Sprite):
    """
    All enemies inherit from this.
    Subclasses override: update_ai(), draw_custom().
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 hp: int = 60, damage: int = 15,
                 water: float = 40.0, chlorophyll: float = 30.0):
        super().__init__()
        self.rect      = pygame.Rect(x, y, width, height)
        self.pos       = pygame.math.Vector2(x, y)
        self.vel       = pygame.math.Vector2(0, 0)

        self.max_hp    = hp
        self.hp        = hp
        self.damage    = damage

        # Haustoria drainable resources
        self.water       = water
        self.chlorophyll = chlorophyll

        self.is_alive  = True
        self.attacking = False
        self.stunned   = False
        self.stun_timer = 0.0

        self.face_direction = -1   # start facing left (toward player)

        # Placeholder image — replace with sprite sheet in full build
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((180, 60, 60))

    # ------------------------------------------------------------------
    def update(self, dt: float, player, tiles):
        if not self.is_alive:
            return

        # Stun
        if self.stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.stunned   = False
                self.attacking = False
            return

        self.update_ai(dt, player, tiles)
        self._move_and_collide(dt, tiles)

    # ------------------------------------------------------------------
    def update_ai(self, dt: float, player, tiles):
        """Override in subclass for specific enemy behaviour."""
        pass

    # ------------------------------------------------------------------
    def take_damage(self, amount: int):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        self.is_alive  = False
        self.water     = 0
        self.chlorophyll = 0
        self.kill()   # remove from sprite groups
        print(f"[Enemy] {self.__class__.__name__} died.")

    # ------------------------------------------------------------------
    def _move_and_collide(self, dt: float, tiles):
        from constants import GRAVITY, TERMINAL_VEL
        self.vel.y += GRAVITY * dt
        self.vel.y  = min(self.vel.y, TERMINAL_VEL)

        self.pos   += self.vel * dt
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel.y       = 0
                elif self.vel.y < 0:
                    self.rect.top    = tile.rect.bottom
                    self.vel.y       = 0
                if self.vel.x > 0:
                    self.rect.right  = tile.rect.left
                    self.vel.x       = 0
                elif self.vel.x < 0:
                    self.rect.left   = tile.rect.right
                    self.vel.x       = 0
        self.pos.x = float(self.rect.x)
        self.pos.y = float(self.rect.y)

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        if not self.is_alive:
            return
        draw_rect = self.rect.move(-cam_x, -cam_y)

        colour = (180, 60, 60) if not self.stunned else (220, 180, 60)
        pygame.draw.rect(surface, colour, draw_rect, border_radius=4)

        # HP bar
        bar_w = self.rect.width
        hp_frac = max(self.hp / self.max_hp, 0.0)
        pygame.draw.rect(surface, (60, 0, 0),   (draw_rect.x, draw_rect.y - 8, bar_w, 5))
        pygame.draw.rect(surface, (220, 60, 60), (draw_rect.x, draw_rect.y - 8, int(bar_w * hp_frac), 5))

        self.draw_custom(surface, draw_rect)

    def draw_custom(self, surface, draw_rect):
        """Override for extra visuals."""
        pass

    # ------------------------------------------------------------------
    @property
    def center(self):
        return pygame.math.Vector2(self.rect.center)
