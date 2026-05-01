# effects.py
from constants import (
    EFFECT_SPEED_MULT, EFFECT_JUMP_MULT, EFFECT_DAMAGE_MULT,
    EFFECT_DURATION, EFFECT_COLOURS
)


class Effect:
    """A single timed buff on the player."""

    DEFINITIONS = {
        # name : (walk_mult, jump_mult, dmg_mult)
        "speed":  (EFFECT_SPEED_MULT,  1.0,               1.0),
        "jump":   (1.0,                EFFECT_JUMP_MULT,  1.0),
        "damage": (1.0,                1.0,               EFFECT_DAMAGE_MULT),
    }

    def __init__(self, effect_type: str, duration: float = EFFECT_DURATION):
        if effect_type not in self.DEFINITIONS:
            raise ValueError(f"Unknown effect type: {effect_type!r}")
        self.effect_type = effect_type
        self.duration    = duration
        self.timer       = 0.0
        self.finished    = False

        mults = self.DEFINITIONS[effect_type]
        self.walk_mult = mults[0]
        self.jump_mult = mults[1]
        self.dmg_mult  = mults[2]

    def update(self, dt: float):
        self.timer += dt
        if self.timer >= self.duration:
            self.finished = True

    @property
    def progress(self) -> float:
        """0.0 → 1.0 fraction of time elapsed."""
        return min(self.timer / self.duration, 1.0)


class EffectsSystem:
    """
    Manages all active player effects.
    Call apply(type) when the player touches a plant.
    Call update(dt) every frame.
    Read get_multipliers() when computing movement / damage.
    """

    def __init__(self):
        self.active: list[Effect] = []

    # ------------------------------------------------------------------
    def apply(self, effect_type: str, duration: float = EFFECT_DURATION):
        # Refresh if already active, else add new
        for e in self.active:
            if e.effect_type == effect_type:
                e.timer = 0.0
                e.duration = duration
                return
        self.active.append(Effect(effect_type, duration))

    # ------------------------------------------------------------------
    def update(self, dt: float):
        for e in self.active:
            e.update(dt)
        self.active = [e for e in self.active if not e.finished]

    # ------------------------------------------------------------------
    def get_multipliers(self) -> tuple[float, float, float]:
        """Returns (walk_mult, jump_mult, dmg_mult) as product of all effects."""
        walk = jump = dmg = 1.0
        for e in self.active:
            walk *= e.walk_mult
            jump *= e.jump_mult
            dmg  *= e.dmg_mult
        return walk, jump, dmg

    # ------------------------------------------------------------------
    @property
    def active_types(self) -> list[str]:
        return [e.effect_type for e in self.active]

    def outline_colour(self):
        """Returns the outline colour for the topmost effect, or None."""
        if not self.active:
            return None
        return EFFECT_COLOURS.get(self.active[-1].effect_type)

    def has(self, effect_type: str) -> bool:
        return any(e.effect_type == effect_type for e in self.active)

    # ------------------------------------------------------------------
    def __repr__(self):
        return f"<EffectsSystem active={self.active_types}>"
