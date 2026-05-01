# ui.py
import pygame
import math
from constants import (
    BAR_W, BAR_H, BAR_PADDING, HUD_X, HUD_Y,
    COL_WATER, COL_CHLORO, COL_BAR_BG, COL_WHITE, COL_BLACK, COL_PSYCHOSIS,
    MAX_WATER, MAX_CHLOROPHYLL, PSYCHOSIS_KILL_TIME,
    SCREEN_W, SCREEN_H,
)


class UI:
    """
    Draws HUD: water bar, chlorophyll bar, effect icons,
    psychosis vfx overlay, day/night indicator, bench hints.
    """

    def __init__(self):
        self.font_sm   = None   # initialised after pygame.font.init()
        self.font_md   = None
        self.font_lg   = None

        self._hint_text    = ""
        self._hint_timer   = 0.0
        self.HINT_DURATION = 5.0

        self._death_alpha  = 0.0
        self._death_active = False

        # Psychosis vfx
        self._psych_surf   = None
        self._psych_time   = 0.0

    # ------------------------------------------------------------------
    def init_fonts(self):
        """Call after pygame.font.init()."""
        pygame.font.init()
        self._psych_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        try:
            self.font_sm = pygame.font.SysFont("monospace", 14)
            self.font_md = pygame.font.SysFont("monospace", 20)
            self.font_lg = pygame.font.SysFont("monospace", 36, bold=True)
        except Exception:
            self.font_sm = pygame.font.Font(None, 18)
            self.font_md = pygame.font.Font(None, 24)
            self.font_lg = pygame.font.Font(None, 42)

    # ------------------------------------------------------------------
    def show_hint(self, text: str):
        self._hint_text  = text
        self._hint_timer = self.HINT_DURATION

    def trigger_death(self):
        self._death_active = True
        self._death_alpha  = 0.0

    # ------------------------------------------------------------------
    def update(self, dt: float, player):
        if self._hint_timer > 0:
            self._hint_timer -= dt

        if player.psychosis_active:
            self._psych_time += dt
        else:
            self._psych_time = max(0.0, self._psych_time - dt * 2)

        if self._death_active:
            self._death_alpha = min(255, self._death_alpha + 120 * dt)

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, player, world):
        if not self.font_sm:
            self.init_fonts()

        self._draw_bars(surface, player)
        self._draw_effects(surface, player)
        self._draw_day_night(surface, world)
        self._draw_psychosis_vfx(surface, player)
        self._draw_hint(surface)
        self._draw_death_screen(surface, player)

    # ------------------------------------------------------------------
    def _draw_bars(self, surface, player):
        x, y = HUD_X, HUD_Y

        # --- Water bar ---
        label = self.font_sm.render("WATER", True, COL_WHITE)
        surface.blit(label, (x, y))
        y += 16
        pygame.draw.rect(surface, COL_BAR_BG, (x, y, BAR_W, BAR_H), border_radius=4)
        water_w = int(BAR_W * (player.water / MAX_WATER))
        pygame.draw.rect(surface, COL_WATER, (x, y, max(water_w, 0), BAR_H), border_radius=4)
        pygame.draw.rect(surface, COL_WHITE, (x, y, BAR_W, BAR_H), 1, border_radius=4)
        y += BAR_H + BAR_PADDING

        # --- Chlorophyll bar ---
        label = self.font_sm.render("CHLOROPHYLL", True, COL_WHITE)
        surface.blit(label, (x, y))
        y += 16
        pygame.draw.rect(surface, COL_BAR_BG, (x, y, BAR_W, BAR_H), border_radius=4)
        chloro_w = int(BAR_W * (player.chlorophyll / MAX_CHLOROPHYLL))
        pygame.draw.rect(surface, COL_CHLORO, (x, y, max(chloro_w, 0), BAR_H), border_radius=4)
        pygame.draw.rect(surface, COL_WHITE, (x, y, BAR_W, BAR_H), 1, border_radius=4)
        y += BAR_H + BAR_PADDING

        # Psychosis timer sub-bar
        if player.psychosis_active:
            frac  = player.psychosis_timer / PSYCHOSIS_KILL_TIME
            label = self.font_sm.render("PSYCHOSIS", True, COL_PSYCHOSIS)
            surface.blit(label, (x, y))
            y += 16
            pygame.draw.rect(surface, COL_BAR_BG, (x, y, BAR_W, BAR_H), border_radius=4)
            psy_w = int(BAR_W * frac)
            pygame.draw.rect(surface, COL_PSYCHOSIS, (x, y, psy_w, BAR_H), border_radius=4)
            pygame.draw.rect(surface, COL_WHITE, (x, y, BAR_W, BAR_H), 1, border_radius=4)

    # ------------------------------------------------------------------
    def _draw_effects(self, surface, player):
        if not player.effects.active:
            return
        x = HUD_X
        y = HUD_Y + 120
        label = self.font_sm.render("EFFECTS:", True, COL_WHITE)
        surface.blit(label, (x, y))
        y += 18
        for eff in player.effects.active:
            from constants import EFFECT_COLOURS
            col  = EFFECT_COLOURS.get(eff.effect_type, COL_WHITE)
            prog = 1.0 - eff.progress          # bar empties as time runs out
            pygame.draw.rect(surface, COL_BAR_BG, (x, y, 80, 8), border_radius=3)
            pygame.draw.rect(surface, col, (x, y, int(80 * prog), 8), border_radius=3)
            txt = self.font_sm.render(eff.effect_type.upper()[:3], True, col)
            surface.blit(txt, (x + 84, y - 2))
            y += 14

    # ------------------------------------------------------------------
    def _draw_day_night(self, surface, world):
        indicator = "● NIGHT" if world.is_night else "○ DAY"
        col       = (160, 160, 220) if world.is_night else (255, 220, 80)
        txt       = self.font_sm.render(indicator, True, col)
        surface.blit(txt, (SCREEN_W - txt.get_width() - 12, 12))

        # Level indicator
        lvl_txt = self.font_sm.render(
            f"LVL {world.level}  RGN {world.region}", True, COL_WHITE)
        surface.blit(lvl_txt, (SCREEN_W - lvl_txt.get_width() - 12, 30))

    # ------------------------------------------------------------------
    def _draw_psychosis_vfx(self, surface, player):
        if self._psych_time <= 0:
            return

        intensity = min(self._psych_time / PSYCHOSIS_KILL_TIME, 1.0)

        # Edge vignette
        alpha = int(intensity * 180)
        self._psych_surf.fill((0, 0, 0, 0))
        vignette_size = int(SCREEN_W * 0.35 * intensity)
        for i in range(vignette_size, 0, -4):
            a = int(alpha * (1 - i / vignette_size))
            col = (int(120 * intensity), 0, int(160 * intensity), a)
            pygame.draw.rect(self._psych_surf, col,
                             (i, i, SCREEN_W - i*2, SCREEN_H - i*2), 4)
        surface.blit(self._psych_surf, (0, 0))

        # Pulsing warning text
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
        if intensity > 0.3 and pulse > 0.5:
            warn = self.font_md.render("FIND WATER — FIND LIGHT", True, COL_PSYCHOSIS)
            surface.blit(warn, (SCREEN_W // 2 - warn.get_width() // 2,
                                SCREEN_H - 60))

    # ------------------------------------------------------------------
    def _draw_hint(self, surface):
        if self._hint_timer <= 0 or not self._hint_text:
            return
        alpha = min(255, int(self._hint_timer / self.HINT_DURATION * 400))
        txt   = self.font_md.render(self._hint_text, True, (200, 200, 160))
        x     = SCREEN_W // 2 - txt.get_width() // 2
        y     = SCREEN_H - 100
        # Dark backing
        pad   = 8
        bg    = pygame.Surface((txt.get_width() + pad*2, txt.get_height() + pad*2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (x - pad, y - pad))
        surface.blit(txt, (x, y))

    # ------------------------------------------------------------------
    def _draw_death_screen(self, surface, player):
        if not self._death_active or player.is_alive:
            self._death_active = False
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self._death_alpha)))
        surface.blit(overlay, (0, 0))

        if self._death_alpha > 180:
            msg = self.font_lg.render("you withered.", True, (180, 100, 180))
            sub = self.font_md.render("returning to last bench...", True, (120, 80, 120))
            surface.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H//2 - 30))
            surface.blit(sub, (SCREEN_W//2 - sub.get_width()//2, SCREEN_H//2 + 20))
