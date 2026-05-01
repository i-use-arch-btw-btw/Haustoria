# constants.py
# All tunable values live here so Zak/Ame can tweak without touching logic.

# --- Window ---
SCREEN_W = 1280
SCREEN_H = 720
FPS      = 60
TITLE    = "Haustoria Respiration Apparatus"

# --- Physics ---
GRAVITY         = 900   # px/s²
TERMINAL_VEL    = 1200  # px/s max fall speed

# --- Player movement ---
WALK_SPEED       = 220   # px/s
RUN_SPEED        = 320   # px/s  (unused tier, hook for effects)
JUMP_FORCE       = -530  # px/s  (negative = up)
DASH_SPEED       = 650   # px/s
DASH_DURATION    = 0.14  # seconds
DASH_COOLDOWN    = 0.45  # seconds
WALL_SLIDE_SPEED = 65    # px/s downward while wall-clinging
WALL_JUMP_X_MULT = 1.5   # horizontal boost on wall jump
WALL_JUMP_Y_MULT = 0.88  # vertical fraction of normal jump
COYOTE_TIME      = 0.10  # seconds of grace after leaving ground
JUMP_BUFFER_TIME = 0.12  # seconds of buffered jump input
WALL_KICK_VEL    = 90    # px/s knockback on hitting a wall (for tech)

# Landing roll thresholds
ROLL_FALL_THRESHOLD = 350  # px/s downward velocity that triggers roll
ROLL_DURATION       = 0.18 # seconds

# Slide
SLIDE_SPEED    = 300  # px/s
SLIDE_DURATION = 0.22 # seconds

# --- Player stats ---
MAX_WATER       = 100.0
MAX_CHLOROPHYLL = 100.0
START_WATER     = 100.0
START_CHLOROPHYLL = 100.0

# Depletion per second (base, day)
WATER_DRAIN_DAY   = 0.40
CHLORO_DRAIN_DAY  = 0.18
# Night multiplier
NIGHT_DRAIN_MULT  = 1.6

# Psychosis
PSYCHOSIS_KILL_TIME = 30.0  # seconds from 0-stat to death screen

# --- Haustoria ---
HAUSTORIA_RANGE      = 52   # px radius to latch
HAUSTORIA_DRAIN_RATE = 12.0 # stat points per second drained from enemy

# --- Combat ---
SPEAR_DAMAGE    = 20
SPEAR_RANGE     = 60   # px from player centre
SPEAR_COOLDOWN  = 0.35 # seconds
THROW_SPEED     = 520  # px/s
ROCK_STUN_TIME  = 1.5  # seconds
PARRY_WINDOW    = 0.15 # seconds
PARRY_EDGE_TOL  = 12   # px — how close to hitbox edge counts as a parry

# --- Effects ---
EFFECT_SPEED_MULT  = 1.5
EFFECT_JUMP_MULT   = 1.35
EFFECT_DAMAGE_MULT = 2.0
EFFECT_DURATION    = 15.0  # seconds (default; individual plants can override)

# --- Day / Night timing (seconds) ---
# Level 1:  10 min cycle, 6 day / 4 night
LVL1_CYCLE    = 600
LVL1_DAY_END  = 360

# Level 2:  10 min cycle, 3 day / 7 night
LVL2_CYCLE    = 600
LVL2_DAY_END  = 180

# Level 3:  no day. Enemy wave every 5 min
LVL3_WAVE_INTERVAL = 300

# --- Save ---
SAVE_FILE = "daikon_save.json"

# --- UI ---
BAR_W          = 180
BAR_H          = 18
BAR_PADDING    = 8
HUD_X          = 20
HUD_Y          = 20

# --- Colours (RGB) ---
COL_WATER      = (80,  160, 230)
COL_CHLORO     = (80,  200, 100)
COL_BAR_BG     = (30,  30,  30)
COL_PSYCHOSIS  = (160, 40,  200)
COL_WHITE      = (255, 255, 255)
COL_BLACK      = (0,   0,   0)
COL_DAIKON     = (230, 230, 245)  # player base tint
COL_DEBUG      = (255, 80,  80)

# Effect outline colours
EFFECT_COLOURS = {
    "speed":  (80,  220, 255),
    "jump":   (180, 255, 80),
    "damage": (255, 100, 60),
}
