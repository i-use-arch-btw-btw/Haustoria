# save.py
import json
import os
from constants import SAVE_FILE, MAX_WATER, MAX_CHLOROPHYLL

# Hints shown at save benches in level 3
HINTS = {
    1: [
        "Haustoria works on anything that bleeds sap.",
        "The walls remember your momentum.",
        "Slide into a wall jump — the flesh yields.",
    ],
    2: [
        "Bell beasts are blind. Sound is your enemy.",
        "Chlorophyll from above. Always from above.",
        "A parry here sends shockwaves.",
    ],
    3: [
        "You are almost through.",
        "The last light is inside you.",
        "Don't stop moving.",
    ],
}

_hint_indices = {1: 0, 2: 0, 3: 0}


def next_hint(region: int) -> str:
    hints = HINTS.get(region, ["..."])
    idx   = _hint_indices.get(region, 0)
    hint  = hints[idx % len(hints)]
    _hint_indices[region] = idx + 1
    return hint


# ------------------------------------------------------------------
class SaveSystem:
    def __init__(self):
        self.last_bench_pos  = None
        self.last_bench_data = None

    # ------------------------------------------------------------------
    def save(self, bench_pos, player, world):
        data = {
            "bench_pos":   list(bench_pos),
            "water":       player.water,
            "chlorophyll": player.chlorophyll,
            "level":       world.level,
            "region":      world.region,
        }
        self.last_bench_pos  = bench_pos
        self.last_bench_data = data

        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[Save] Saved at bench {bench_pos}")
        except OSError as e:
            print(f"[Save] Could not write save file: {e}")

        if world.level == 3:
            hint = next_hint(world.region)
            return hint
        return None

    # ------------------------------------------------------------------
    def load(self):
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Save] Could not read save file: {e}")
            return None

    # ------------------------------------------------------------------
    def apply_to(self, data: dict, player, world):
        """Push loaded data back into live objects."""
        player.pos.x       = data["bench_pos"][0]
        player.pos.y       = data["bench_pos"][1]
        player.water       = data["water"]
        player.chlorophyll = data["chlorophyll"]
        player.vel.x       = 0
        player.vel.y       = 0
        player.is_alive    = True
        player.psychosis_active = False
        player.psychosis_timer  = 0.0
        world.level  = data["level"]
        world.region = data["region"]
        print(f"[Save] Loaded — level {world.level} region {world.region}")

    # ------------------------------------------------------------------
    def respawn(self, player, world):
        """Called on player death — load last bench or fall back to defaults."""
        data = self.load()
        if data:
            self.apply_to(data, player, world)
        else:
            # First death, no save — reset to level 1 start
            player.pos.x = 100
            player.pos.y = 300
            player.water       = MAX_WATER
            player.chlorophyll = MAX_CHLOROPHYLL
            player.is_alive    = True
            player.psychosis_active = False
            player.psychosis_timer  = 0.0
            world.level  = 1
            world.region = 1
