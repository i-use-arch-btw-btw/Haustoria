# enemies/wasp.py
# Level 2 Boss — Wasp (comes in pairs).
import pygame
import math
from enemies.base import BaseEnemy


class Wasp(BaseEnemy):
    """
    Aerial. Charges straight at the player, retreats, charges again.
    Slightly larger than Aphid, significantly faster.
    """

    PATROL_SPEED  = 110
    CHARGE_SPEED  = 380
    CHARGE_DIST   = 300   # px — triggers charge when player within this
    RETREAT_DIST  = 200   # px — retreat target offset from player
    CHARGE_CD     = 2.5

    def __init__(self, x: int, y: int):
        super().__init__(x, y, width=28, height=22,
                         hp=55, damage=20,
                         water=20.0, chlorophyll=16.0)
        self.image.fill((240, 200, 30))
        self.state      = "patrol"
        self.charge_cd  = self.CHARGE_CD
        self.retreat_target = pygame.math.Vector2(x, y)

    def update_ai(self, dt: float, player, tiles):
        self.charge_cd -= dt
        px, py = player.rect.centerx, player.rect.centery
        to_player = pygame.math.Vector2(px, py) - self.pos
        dist      = to_player.length()

        if self.state == "patrol":
            # Hover in place with slight drift
            self.vel.y = math.sin(pygame.time.get_ticks() * 0.003) * 40

            if dist < self.CHARGE_DIST and self.charge_cd <= 0:
                self.state     = "charge"
                self.attacking = True
                self.charge_cd = self.CHARGE_CD

        elif self.state == "charge":
            if to_player.length() > 0:
                self.vel = to_player.normalize() * self.CHARGE_SPEED
            if dist < 20 or dist > self.CHARGE_DIST * 1.5:
                self.state     = "retreat"
                self.attacking = False
                # Retreat to offset position
                offset = to_player.normalize() * -self.RETREAT_DIST if to_player.length() > 0 else pygame.math.Vector2(-100, 0)
                self.retreat_target = pygame.math.Vector2(px, py) + offset

        elif self.state == "retreat":
            to_retreat = self.retreat_target - self.pos
            if to_retreat.length() > 10:
                self.vel = to_retreat.normalize() * self.PATROL_SPEED
            else:
                self.vel  = pygame.math.Vector2(0, 0)
                self.state = "patrol"

    def _move_and_collide(self, dt, tiles):
        # Wasps fly — ignore gravity
        self.pos += self.vel * dt
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
