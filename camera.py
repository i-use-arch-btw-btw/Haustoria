# camera.py
from constants import SCREEN_W, SCREEN_H


class Camera:
    """
    Smoothly follows the player.
    offset_x / offset_y are subtracted from world coords when drawing.
    """

    LERP = 0.10   # smoothing factor (0 = no movement, 1 = instant snap)

    def __init__(self, world_w: int = 2000, world_h: int = 700):
        self.x       = 0.0
        self.y       = 0.0
        self.world_w = world_w
        self.world_h = world_h

    def update(self, player_rect):
        # Target: centre player on screen
        target_x = player_rect.centerx - SCREEN_W // 2
        target_y = player_rect.centery - SCREEN_H // 2

        # Smooth follow
        self.x += (target_x - self.x) * self.LERP
        self.y += (target_y - self.y) * self.LERP

        # Clamp to world bounds
        self.x = max(0, min(self.x, self.world_w - SCREEN_W))
        self.y = max(0, min(self.y, self.world_h - SCREEN_H))

    @property
    def offset(self) -> tuple[int, int]:
        return int(self.x), int(self.y)
