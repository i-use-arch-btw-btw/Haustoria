# enemies/dragonfly.py
# Level 1 Boss — Dragonfly.  2× bigger than the Burrowyrm.
import pygame
import math
from enemies.base import BaseEnemy


class Dragonfly(BaseEnemy):
    """
    Aerial boss. Hovers, dives at player, fires wing-gust projectiles.
    Size: ~112 × 56 px (twice the Burrowyrm footprint).
    """

    HOVER_SPEED  = 90
    DIVE_SPEED   = 420
    GUST_COOLDOWN = 2.2   # seconds between gusts
    DIVE_COOLDOWN = 3.0

    def __init__(self, x: int, y: int):
        super().__init__(x, y, width=112, height=56,
                         hp=280, damage=28,
                         water=80.0, chlorophyll=60.0)
        self.image.fill((40, 160, 120))

        self.state         = "hover"   # hover | dive | recover
        self.hover_target  = pygame.math.Vector2(x, y - 160)
        self.gust_timer    = 0.0
        self.dive_timer    = 0.0
        self.recover_timer = 0.0

    def update_ai(self, dt: float, player, tiles):
        self.gust_timer  -= dt
        self.dive_timer  -= dt

        px, py = player.rect.centerx, player.rect.centery

        if self.state == "hover":
            # Float above player
            self.hover_target.x = px
            self.hover_target.y = py - 160

            to_hover = self.hover_target - self.pos
            dist     = to_hover.length()
            if dist > 5:
                self.vel = to_hover.normalize() * self.HOVER_SPEED
            else:
                self.vel.x = 0
                self.vel.y = 0   # override gravity while hovering

            # Trigger dive
            if self.dive_timer <= 0:
                self.state      = "dive"
                self.attacking  = True
                self.dive_timer = self.DIVE_COOLDOWN

        elif self.state == "dive":
            # Plunge straight down toward player
            to_player = pygame.math.Vector2(px, py) - self.pos
            if to_player.length() > 0:
                self.vel = to_player.normalize() * self.DIVE_SPEED

            # If we've passed or hit ground, recover
            if self.pos.y >= py or self.vel.y == 0:
                self.state         = "recover"
                self.attacking     = False
                self.recover_timer = 0.8
                self.vel.y         = -200   # small bounce up

        elif self.state == "recover":
            self.recover_timer -= dt
            self.vel.x = 0
            self.vel.y = -60   # drift upward slowly
            if self.recover_timer <= 0:
                self.state = "hover"

        # Gravity is suppressed while hovering
        if self.state == "hover":
            pass   # BaseEnemy._move_and_collide adds gravity; compensate below

    def _move_and_collide(self, dt, tiles):
        # Dragonfly ignores gravity while hovering / recovering
        if self.state in ("hover", "recover"):
            self.pos += self.vel * dt
            self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        else:
            super()._move_and_collide(dt, tiles)

    def draw_custom(self, surface, draw_rect):
        # Simple wing indicators
        wc = (100, 220, 180, 160)
        wing_surf = pygame.Surface((50, 20), pygame.SRCALPHA)
        wing_surf.fill(wc)
        surface.blit(wing_surf, (draw_rect.x - 50, draw_rect.y + 10))
        surface.blit(wing_surf, (draw_rect.right,  draw_rect.y + 10))
