#!/usr/bin/env python3
"""
main.py — Haustoria Respiration Apparatus (Daikon game)
Entry point. Run:  python main.py
"""
import sys
import pygame

from constants import SCREEN_W, SCREEN_H, FPS, TITLE
from player   import Player
from world    import World
from combat   import CombatSystem
from camera   import Camera
from ui       import UI
from save     import SaveSystem
from effects  import EffectsSystem

from enemies.dragonfly import Dragonfly
from enemies.burrowyrm import Burrowyrm
from enemies.aphid      import Aphid
from enemies.wasp       import Wasp
from enemies.maggot     import DaikonMaggot


# ======================================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock  = pygame.time.Clock()

        # Core systems
        self.world   = World(level=1, region=1)
        self.player  = Player(x=140, y=500)
        self.combat  = CombatSystem()
        self.camera  = Camera(world_w=2000, world_h=700)
        self.ui      = UI()
        self.save    = SaveSystem()

        self.ui.init_fonts()

        # Spawn starter enemies
        self.enemies = self._spawn_level_enemies()

        # Debug flag (toggle with F1)
        self.debug = False

        # Death cooldown (so we don't respawn instantly)
        self._death_timer   = 0.0
        self._prev_wave_num = 0

    # ------------------------------------------------------------------
    def _spawn_level_enemies(self) -> list:
        if self.world.level == 1:
            return [
                Aphid(500, 520),
                Aphid(700, 520),
                Aphid(900, 520),
            ]
        elif self.world.level == 2:
            return [
                Aphid(400, 520),
                Aphid(600, 520),
                Wasp(800, 300),
                Wasp(950, 260),
                Burrowyrm(1100, 400, ground_y=550),
            ]
        elif self.world.level == 3:
            return [
                DaikonMaggot(600, 460),
            ]
        return []

    # ------------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0   # seconds
            dt = min(dt, 0.05)                    # cap to avoid physics explosion

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.debug = not self.debug

            self._update(dt, events)
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    def _update(self, dt: float, events):
        keys = pygame.key.get_pressed()

        # --- Death handling ---
        if not self.player.is_alive:
            self._death_timer += dt
            self.ui.trigger_death()
            if self._death_timer >= 2.5:
                self._death_timer = 0.0
                self.save.respawn(self.player, self.world)
                self.enemies = self._spawn_level_enemies()
                self.world._build_level()
            return

        # --- Input ---
        self.player.handle_input(keys, events)

        # --- Interact (pickup / bench) ---
        if keys[pygame.K_f] or keys[pygame.K_UP]:
            # Bench
            bench = self.world.nearest_bench(self.player.pos)
            if bench:
                hint = self.save.save(bench.pos, self.player, self.world)
                if hint:
                    self.ui.show_hint(hint)
            else:
                # Pickup
                self.player.try_pickup(self.world.objects)

        # --- Use held object ---
        if keys[pygame.K_e]:
            self.player.try_use()

        # --- Melee attack ---
        if keys[pygame.K_c]:
            self.combat.player_melee(self.player, self.enemies)

        # --- Throw ---
        if keys[pygame.K_v] and self.player.held_object:
            self.combat.player_throw(self.player, self.player.held_object)

        # --- World update ---
        self.world.update(dt)

        # --- Night wave (level 3) ---
        if self.world.spawn_wave > self._prev_wave_num:
            self._prev_wave_num = self.world.spawn_wave
            self._on_night_wave()

        # --- Player update ---
        nearby = [e for e in self.enemies if e.is_alive]
        self.player.update(
            dt       = dt,
            world    = self.world,
            combat_system  = self.combat,
            nearby_enemies = nearby,
            tiles          = self.world.tiles,
        )

        # --- Enemies update ---
        for enemy in self.enemies:
            if enemy.is_alive:
                enemy.update(dt, self.player, self.world.tiles)

        # Prune dead enemies
        self.enemies = [e for e in self.enemies if e.is_alive]

        # --- Combat projectiles ---
        self.combat.update(dt, self.player, self.enemies, self.world.tiles)

        # --- Camera ---
        self.camera.update(self.player.rect)

        # --- UI ---
        self.ui.update(dt, self.player)

    # ------------------------------------------------------------------
    def _on_night_wave(self):
        """Spawn an extra wave of enemies in level 3."""
        import random
        spawn_x = random.choice([300, 700, 1100, 1500])
        self.enemies.append(DaikonMaggot(spawn_x, 460))
        print(f"[Game] Night wave {self.world.spawn_wave} spawned.")

    # ------------------------------------------------------------------
    def _draw(self):
        cam_x, cam_y = self.camera.offset

        # World (background, tiles, objects, benches)
        self.world.draw(self.screen, cam_x, cam_y)

        # Enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x, cam_y)

        # Player
        self.player.draw(self.screen, cam_x, cam_y)

        # Combat projectiles
        self.combat.draw(self.screen, self.camera.offset)

        # HUD
        self.ui.draw(self.screen, self.player, self.world)

        # Debug overlay
        if self.debug:
            self._draw_debug(cam_x, cam_y)

    # ------------------------------------------------------------------
    def _draw_debug(self, cam_x, cam_y):
        from constants import COL_DEBUG
        font = self.ui.font_sm
        lines = [
            f"pos  ({self.player.pos.x:.0f}, {self.player.pos.y:.0f})",
            f"vel  ({self.player.vel.x:.0f}, {self.player.vel.y:.0f})",
            f"grnd {self.player.on_ground}  wall {self.player.on_wall}",
            f"dash {self.player._is_dashing}  slide {self.player._is_sliding}  roll {self.player._is_rolling}",
            f"night {self.world.is_night}  wave {self.world.spawn_wave}",
            f"enemies {len(self.enemies)}",
            f"haustoria {self.player.haustoria_active}",
            f"effects {self.player.effects.active_types}",
        ]
        for i, line in enumerate(lines):
            surf = font.render(line, True, COL_DEBUG)
            self.screen.blit(surf, (SCREEN_W - surf.get_width() - 10, 60 + i * 18))

        # Player hitbox
        pr = self.player.rect.move(-cam_x, -cam_y)
        pygame.draw.rect(self.screen, COL_DEBUG, pr, 1)

        # Enemy hitboxes
        for e in self.enemies:
            er = e.rect.move(-cam_x, -cam_y)
            pygame.draw.rect(self.screen, (255, 160, 0), er, 1)


# ======================================================================
if __name__ == "__main__":
    Game().run()
