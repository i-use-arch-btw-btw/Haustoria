# world.py
import pygame
import random
from constants import (
    LVL1_CYCLE, LVL1_DAY_END,
    LVL2_CYCLE, LVL2_DAY_END,
    LVL3_WAVE_INTERVAL,
    COL_BLACK, COL_WHITE,
    SCREEN_W, SCREEN_H,
)
from player import InteractableObject


# ------------------------------------------------------------------
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, colour=(80, 60, 40)):
        super().__init__()
        self.rect  = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h))
        self.image.fill(colour)

    def draw(self, surface, cam_x, cam_y):
        r = self.rect.move(-cam_x, -cam_y)
        surface.blit(self.image, r)


class SaveBench:
    def __init__(self, x, y):
        self.pos  = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x, y, 32, 16)

    def draw(self, surface, cam_x, cam_y):
        r = self.rect.move(-cam_x, -cam_y)
        pygame.draw.rect(surface, (140, 100, 60), r, border_radius=4)
        pygame.draw.rect(surface, (200, 160, 100), r, 2, border_radius=4)


# ------------------------------------------------------------------
class World:
    """
    Manages level geometry, day/night, enemy spawning, and world objects.
    The level layout is placeholder tiles — replace with tilemap loading later.
    """

    def __init__(self, level: int = 1, region: int = 1):
        self.level  = level
        self.region = region

        self.time_elapsed  = 0.0
        self.is_night      = False
        self.spawn_wave    = 0
        self._wave_timer   = 0.0

        self.tiles:    list[Tile]               = []
        self.objects:  list[InteractableObject] = []
        self.benches:  list[SaveBench]          = []
        self.enemies:  list                     = []   # filled by Game

        # Darkness overlay alpha (0 = day, 200 = deep night)
        self._dark_alpha = 0
        self._dark_surf  = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        self._build_level()

    # ==================================================================
    # BUILD PLACEHOLDER LEVEL GEOMETRY
    # ==================================================================
    def _build_level(self):
        self.tiles   = []
        self.objects = []
        self.benches = []

        if self.level == 1:
            self._build_level1()
        elif self.level == 2:
            self._build_level2()
        elif self.level == 3:
            self._build_level3()

    # ----- Level 1 : Garden -----
    def _build_level1(self):
        # Ground
        self.tiles.append(Tile(0,   550, 2000, 60,  (80, 120, 60)))   # grass
        # Platforms
        self.tiles.append(Tile(200, 440,  160, 20,  (60, 100, 40)))
        self.tiles.append(Tile(480, 360,  160, 20,  (60, 100, 40)))
        self.tiles.append(Tile(760, 440,  160, 20,  (60, 100, 40)))
        self.tiles.append(Tile(1000,320,  160, 20,  (60, 100, 40)))
        # Wall
        self.tiles.append(Tile(1400, 350, 20, 200,  (60, 80, 40)))
        # Objects
        self.objects.append(InteractableObject((300, 530), "rock"))
        self.objects.append(InteractableObject((600, 530), "spear"))
        # Save bench
        self.benches.append(SaveBench(100, 534))
        self.benches.append(SaveBench(900, 534))

    # ----- Level 2 : Underground -----
    def _build_level2(self):
        self.tiles.append(Tile(0,   550, 2400, 60,  (60, 45, 30)))   # dirt floor
        self.tiles.append(Tile(0,   0,   2400, 30,  (40, 30, 20)))   # ceiling
        # Platforms & ledges
        self.tiles.append(Tile(300, 460,  120, 20,  (50, 40, 25)))
        self.tiles.append(Tile(550, 380,  120, 20,  (50, 40, 25)))
        self.tiles.append(Tile(800, 460,  120, 20,  (50, 40, 25)))
        self.tiles.append(Tile(1100,300,  120, 20,  (50, 40, 25)))
        # Wall sections (for wall-jump practice)
        self.tiles.append(Tile(700, 370, 20, 180,   (45, 35, 20)))
        self.tiles.append(Tile(960, 370, 20, 180,   (45, 35, 20)))
        # Objects
        self.objects.append(InteractableObject((400, 530), "rock"))
        self.objects.append(InteractableObject((700, 530), "spear"))
        # Benches
        self.benches.append(SaveBench(120, 534))
        self.benches.append(SaveBench(1200,534))

    # ----- Level 3 : Flesh tunnels -----
    def _build_level3(self):
        self.tiles.append(Tile(0,   560, 2800, 60,  (140, 60, 60)))   # flesh floor
        self.tiles.append(Tile(0,   0,   2800, 30,  (120, 50, 50)))   # ceiling
        # Uneven walls, tight corridors
        self.tiles.append(Tile(400, 380,  80, 180,  (130, 55, 55)))
        self.tiles.append(Tile(650, 440,  80, 120,  (130, 55, 55)))
        self.tiles.append(Tile(900, 360,  80, 200,  (130, 55, 55)))
        self.tiles.append(Tile(1150,400,  80, 160,  (130, 55, 55)))
        self.tiles.append(Tile(1400,320,  80, 240,  (130, 55, 55)))
        # Narrow platforms requiring advanced movement
        self.tiles.append(Tile(500, 460,  60, 16,   (160, 70, 70)))
        self.tiles.append(Tile(760, 400,  60, 16,   (160, 70, 70)))
        self.tiles.append(Tile(1020,340,  60, 16,   (160, 70, 70)))
        # Objects
        self.objects.append(InteractableObject((200, 540), "rock"))
        self.objects.append(InteractableObject((800, 540), "spear"))
        # Single bench per region — hard-earned
        self.benches.append(SaveBench(100, 544))
        self.benches.append(SaveBench(1600,544))

    # ==================================================================
    # UPDATE
    # ==================================================================
    def update(self, dt: float):
        self.time_elapsed += dt
        self._update_day_night()
        self._update_objects(dt)
        self._update_darkness()

    def _update_day_night(self):
        if self.level == 1:
            cycle_pos    = self.time_elapsed % LVL1_CYCLE
            self.is_night = cycle_pos >= LVL1_DAY_END

        elif self.level == 2:
            if self.region in (1, 2):
                cycle_pos    = self.time_elapsed % LVL2_CYCLE
                self.is_night = cycle_pos >= LVL2_DAY_END
            else:
                self.is_night = True

        elif self.level == 3:
            self.is_night  = True
            self._wave_timer += dt
            if self._wave_timer >= LVL3_WAVE_INTERVAL:
                self._wave_timer = 0.0
                self.spawn_wave += 1
                self._trigger_night_wave()

    def _trigger_night_wave(self):
        """Signal that a new enemy wave should spawn (Game handles actual instantiation)."""
        print(f"[World] Night wave {self.spawn_wave} triggered in level 3!")
        # Game.on_night_wave() is called by Game each frame when world.spawn_wave changes

    def _update_objects(self, dt: float):
        for obj in self.objects:
            if not obj.is_held:
                obj.update(dt, self.tiles)

    def _update_darkness(self):
        if self.level == 3:
            target = 190
        elif self.is_night:
            target = 140
        else:
            target = 0
        # Smooth transition
        diff = target - self._dark_alpha
        self._dark_alpha += diff * 0.02
        self._dark_alpha  = max(0, min(220, self._dark_alpha))

    # ==================================================================
    # BENCH INTERACTION
    # ==================================================================
    def nearest_bench(self, player_pos) -> SaveBench | None:
        for bench in self.benches:
            if bench.rect.collidepoint(int(player_pos.x), int(player_pos.y)):
                return bench
            dist = (pygame.math.Vector2(bench.pos) - player_pos).length()
            if dist < 30:
                return bench
        return None

    # ==================================================================
    # DRAW
    # ==================================================================
    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        # Sky / background
        bg = (20, 20, 30) if self.is_night else (160, 200, 240)
        surface.fill(bg)

        for tile in self.tiles:
            tile.draw(surface, cam_x, cam_y)

        for obj in self.objects:
            obj.draw(surface, cam_x, cam_y)

        for bench in self.benches:
            bench.draw(surface, cam_x, cam_y)

        # Darkness overlay
        if self._dark_alpha > 1:
            self._dark_surf.fill((0, 0, 0, int(self._dark_alpha)))
            surface.blit(self._dark_surf, (0, 0))
