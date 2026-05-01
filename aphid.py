# enemies/aphid.py
# Level 2 Boss — Aphid swarm (many small enemies).
import pygame
import random
from enemies.base import BaseEnemy


class Aphid(BaseEnemy):
    """
    Small, weak, but comes in large numbers.
    Wanders toward player; jumps occasionally.
    """

    WANDER_SPEED  = 70
    JUMP_FORCE    = -320
    JUMP_INTERVAL = 2.0

    def __init__(self, x: int, y: int):
        super().__init__(x, y, width=14, height=12,
                         hp=18, damage=8,
                         water=8.0, chlorophyll=6.0)
        self.image.fill((80, 200, 60))
        self.jump_timer  = random.uniform(0.5, self.JUMP_INTERVAL)
        self.on_ground   = False

    def update_ai(self, dt: float, player, tiles):
        self.jump_timer -= dt

        # Walk toward player
        dx = player.rect.centerx - self.rect.centerx
        self.vel.x = self.WANDER_SPEED if dx > 0 else -self.WANDER_SPEED

        # Random jumps
        if self.jump_timer <= 0 and self.on_ground:
            self.vel.y      = self.JUMP_FORCE
            self.jump_timer = self.JUMP_INTERVAL + random.uniform(-0.3, 0.5)

    def _move_and_collide(self, dt, tiles):
        from constants import GRAVITY, TERMINAL_VEL
        self.vel.y += GRAVITY * dt
        self.vel.y  = min(self.vel.y, TERMINAL_VEL)

        self.pos   += self.vel * dt
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.on_ground = False

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel.y       = 0
                    self.on_ground   = True
                self.pos.x = float(self.rect.x)
                self.pos.y = float(self.rect.y)
