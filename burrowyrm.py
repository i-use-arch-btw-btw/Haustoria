# enemies/burrowyrm.py
# Level 2 Boss — Daikon Burrowing Worm.  3× bigger than player.
import pygame
import math
import random
from enemies.base import BaseEnemy


class Burrowyrm(BaseEnemy):
    """
    Burrows underground, erupts under the player.
    Size: ~84 × 132 px (3× the 28×44 player).
    Phases: underground → erupting → above-ground slam → burrow again.
    """

    BURROW_DELAY  = 2.0
    ERUPT_LINGER  = 1.2
    SLAM_SPEED    = 500

    def __init__(self, x: int, y: int, ground_y: int):
        super().__init__(x, y, width=84, height=132,
                         hp=420, damage=35,
                         water=100.0, chlorophyll=80.0)
        self.image.fill((100, 80, 50))
        self.ground_y    = ground_y   # y where ground surface sits
        self.state       = "burrowed"
        self.state_timer = self.BURROW_DELAY
        self.target_x    = x

    def update_ai(self, dt: float, player, tiles):
        self.state_timer -= dt

        if self.state == "burrowed":
            # Track player X while underground (invisible)
            self.target_x = player.rect.centerx
            self.pos.y    = self.ground_y + 200  # hidden below ground
            self.rect.topleft = (int(self.pos.x), int(self.pos.y))

            if self.state_timer <= 0:
                # Snap X, then erupt
                self.pos.x   = self.target_x - self.rect.width // 2
                self.pos.y   = self.ground_y  # start at surface
                self.state   = "erupting"
                self.state_timer = self.ERUPT_LINGER
                self.attacking   = True
                self.vel.y       = -self.SLAM_SPEED

        elif self.state == "erupting":
            self.vel.y = max(self.vel.y - 20, 0)   # decelerate
            if self.state_timer <= 0:
                self.state       = "above"
                self.state_timer = 1.0
                self.attacking   = False

        elif self.state == "above":
            # Slam back down
            self.vel.y = self.SLAM_SPEED
            if self.state_timer <= 0:
                self.state       = "burrowed"
                self.state_timer = self.BURROW_DELAY + random.uniform(-0.5, 0.5)
                self.vel.y       = 0

    def draw(self, surface, cam_x, cam_y):
        # Don't draw while burrowed
        if self.state == "burrowed":
            return
        super().draw(surface, cam_x, cam_y)
