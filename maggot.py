# enemies/maggot.py
# Level 3 Boss — Daikon Maggot.
import pygame
import math
from enemies.base import BaseEnemy


class DaikonMaggot(BaseEnemy):
    """
    Enormous, slow, devastating.  Near-kills the player on contact.
    Burrows, squirms toward player, erupts beneath them.
    Haustoria is the primary way to weaken it.
    """

    CRAWL_SPEED   = 45
    LUNGE_SPEED   = 280
    LUNGE_CD      = 4.0

    def __init__(self, x: int, y: int):
        super().__init__(x, y, width=100, height=80,
                         hp=600, damage=90,
                         water=150.0, chlorophyll=120.0)
        self.image.fill((200, 180, 160))
        self.lunge_cd  = self.LUNGE_CD
        self.state     = "crawl"

    def update_ai(self, dt: float, player, tiles):
        self.lunge_cd -= dt
        px, py = player.rect.centerx, player.rect.centery
        to_player = pygame.math.Vector2(px, py) - self.pos

        if self.state == "crawl":
            # Slow crawl toward player
            if to_player.length() > 0:
                self.vel.x = to_player.normalize().x * self.CRAWL_SPEED

            if self.lunge_cd <= 0:
                self.state    = "lunge"
                self.attacking = True
                self.lunge_cd  = self.LUNGE_CD

        elif self.state == "lunge":
            if to_player.length() > 0:
                self.vel = to_player.normalize() * self.LUNGE_SPEED
            # Return to crawl after 0.4s of lunge
            if not hasattr(self, "_lunge_timer"):
                self._lunge_timer = 0.4
            self._lunge_timer -= dt
            if self._lunge_timer <= 0:
                self.state        = "crawl"
                self.attacking    = False
                del self._lunge_timer

    def draw_custom(self, surface, draw_rect):
        # Segmented body indicator
        seg_w = draw_rect.width // 5
        for i in range(5):
            colour = (180 + i * 8, 160 + i * 5, 140)
            pygame.draw.rect(surface, colour,
                             (draw_rect.x + i * seg_w, draw_rect.y + 20,
                              seg_w - 2, draw_rect.height - 20),
                             border_radius=6)
