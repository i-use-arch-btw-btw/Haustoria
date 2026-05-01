# player.py
import pygame
import math
from constants import *
from effects import EffectsSystem


class InteractableObject:
    """A pickupable/throwable world object."""

    def __init__(self, pos, obj_type="rock"):
        self.pos      = pygame.math.Vector2(pos)
        self.obj_type = obj_type   # "rock", "spear", "plant", "platform"
        self.held_by  = None
        self.is_held  = False
        self.vel      = pygame.math.Vector2(0, 0)
        self.on_ground = False

        w, h = (8, 8) if obj_type == "rock" else (20, 6)
        self.rect  = pygame.Rect(int(self.pos.x), int(self.pos.y), w, h)
        self.image = pygame.Surface((w, h))
        self.image.fill((160, 140, 100) if obj_type == "rock" else (200, 180, 80))

    def on_pickup(self, player):
        self.held_by  = player
        self.is_held  = True
        self.vel      = pygame.math.Vector2(0, 0)

    def on_throw(self):
        self.is_held = False
        self.held_by = None

    def update(self, dt, tiles):
        if self.is_held:
            self.pos.x = self.held_by.rect.centerx + self.held_by.face_direction * 20
            self.pos.y = self.held_by.rect.centery
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            return

        self.vel.y += GRAVITY * dt
        self.vel.y  = min(self.vel.y, TERMINAL_VEL)
        self.pos   += self.vel * dt
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

        self.on_ground = False
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                self.vel.x  = 0
                self.vel.y  = 0
                self.pos.y  = tile.rect.top - self.rect.height
                self.rect.y = int(self.pos.y)
                self.on_ground = True

    def draw(self, surface, cam_x, cam_y):
        r = self.rect.move(-cam_x, -cam_y)
        surface.blit(self.image, r)


# ======================================================================
class Player:
    """
    The main Daikon player character.

    Coordinate system: +x right, +y DOWN (pygame standard).
    face_direction: +1 = right, -1 = left.
    """

    def __init__(self, x: int, y: int):
        # --- Sprite / rect ---
        self.rect  = pygame.Rect(x, y, 28, 44)
        self.pos   = pygame.math.Vector2(x, y)    # float pos, rect synced each frame
        self.image = pygame.Surface((28, 44), pygame.SRCALPHA)
        self.image.fill(COL_DAIKON)

        # --- Physics state ---
        self.vel            = pygame.math.Vector2(0, 0)
        self.face_direction = 1          # +1 right, -1 left
        self.on_ground      = False
        self.on_wall        = False
        self.on_ceiling     = False
        self.wall_side      = 0          # +1 right wall, -1 left wall

        # Coyote / jump buffer
        self._coyote_timer      = 0.0
        self._jump_buffer_timer = 0.0

        # Dash
        self._is_dashing    = False
        self._dash_timer    = 0.0
        self._dash_cooldown = 0.0
        self._dash_dir      = 1

        # Slide
        self._is_sliding    = False
        self._slide_timer   = 0.0

        # Roll
        self._is_rolling    = False
        self._roll_timer    = 0.0
        self._pre_land_vel  = 0.0       # downward vel recorded just before landing

        # --- Stats ---
        self.water       = START_WATER
        self.chlorophyll = START_CHLOROPHYLL
        self.is_alive    = True

        # Psychosis
        self.psychosis_active = False
        self.psychosis_timer  = 0.0

        # --- Haustoria ---
        self.haustoria_active = False
        self.haustoria_target = None
        self.invincible       = False

        # --- Combat ---
        self.held_object = None

        # --- Effects ---
        self.effects = EffectsSystem()

        # --- Input state snapshots (set by handle_input each frame) ---
        self._input = {
            "left": False, "right": False, "up": False, "down": False,
            "jump": False, "dash": False, "attack": False, "throw": False,
            "interact": False, "haustoria": False,
        }

    # ==================================================================
    # INPUT
    # ==================================================================
    def handle_input(self, keys, events):
        i = self._input
        i["left"]      = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        i["right"]     = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        i["up"]        = keys[pygame.K_UP]    or keys[pygame.K_w]
        i["down"]      = keys[pygame.K_DOWN]  or keys[pygame.K_s]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_z):
                    i["jump"]      = True
                    self._jump_buffer_timer = JUMP_BUFFER_TIME
                if event.key == pygame.K_x:
                    i["dash"]      = True
                if event.key == pygame.K_c:
                    i["attack"]    = True
                if event.key == pygame.K_v:
                    i["throw"]     = True
                if event.key == pygame.K_f:
                    i["interact"]  = True
                if event.key == pygame.K_g:
                    i["haustoria"] = True
            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_z):
                    i["jump"] = False

    def _consume(self, key: str) -> bool:
        """Read a one-shot input flag and clear it."""
        val = self._input[key]
        self._input[key] = False
        return val

    # ==================================================================
    # UPDATE (called once per frame)
    # ==================================================================
    def update(self, dt: float, world, combat_system, nearby_enemies, tiles):
        if not self.is_alive:
            return

        # --- Haustoria overrides everything ---
        if self.haustoria_active:
            self._update_haustoria(dt)
            self.effects.update(dt)
            self._sync_rect()
            return

        # --- Timers ---
        self._dash_cooldown = max(0.0, self._dash_cooldown - dt)
        if self._jump_buffer_timer > 0:
            self._jump_buffer_timer -= dt
        if not self.on_ground:
            self._coyote_timer = max(0.0, self._coyote_timer - dt)

        # --- Movement ---
        walk_mult, jump_mult, _ = self.effects.get_multipliers()

        self._handle_horizontal(dt, walk_mult)
        self._handle_dash(dt)
        self._handle_jump(jump_mult)
        self._handle_wall_mechanics()
        self._apply_gravity(dt)
        self._handle_slide(dt, walk_mult)

        # --- Move & collide ---
        self._move_and_collide(dt, tiles)

        # --- Roll on hard landing ---
        self._handle_roll(dt)

        # --- Stats depletion ---
        self._deplete_stats(dt, world.is_night)

        # --- Psychosis ---
        self._update_psychosis(dt)

        # --- Haustoria trigger ---
        if self._consume("haustoria"):
            self._try_haustoria(nearby_enemies)

        # --- Effects ---
        self.effects.update(dt)

        # --- Face direction ---
        if self._input["right"]:
            self.face_direction = 1
        elif self._input["left"]:
            self.face_direction = -1

        self._sync_rect()

    # ==================================================================
    # HORIZONTAL MOVEMENT
    # ==================================================================
    def _handle_horizontal(self, dt: float, walk_mult: float):
        if self._is_dashing or self._is_sliding:
            return   # dash/slide controls velocity directly

        target_vx = 0.0
        if self._input["right"]:
            target_vx =  WALK_SPEED * walk_mult
        if self._input["left"]:
            target_vx = -WALK_SPEED * walk_mult

        # Simple instant response (no acceleration yet; add lerp here if desired)
        self.vel.x = target_vx

    # ==================================================================
    # DASH
    # ==================================================================
    def _handle_dash(self, dt: float):
        if self._is_dashing:
            self.vel.x = self._dash_dir * DASH_SPEED
            self.vel.y = 0
            self._dash_timer -= dt
            if self._dash_timer <= 0:
                self._is_dashing = False
            return

        if self._consume("dash") and self._dash_cooldown <= 0:
            self._is_dashing    = True
            self._dash_timer    = DASH_DURATION
            self._dash_cooldown = DASH_COOLDOWN
            self._dash_dir      = self.face_direction

    # ==================================================================
    # JUMP
    # ==================================================================
    def _handle_jump(self, jump_mult: float):
        can_jump = self.on_ground or self._coyote_timer > 0
        buffered = self._jump_buffer_timer > 0

        if buffered and can_jump:
            self.vel.y = JUMP_FORCE * jump_mult
            self._jump_buffer_timer = 0
            self._coyote_timer      = 0

        elif buffered and self.on_wall and not self.on_ground:
            # Wall jump
            self.vel.y = JUMP_FORCE * WALL_JUMP_Y_MULT * jump_mult
            self.vel.x = -self.wall_side * WALK_SPEED * WALL_JUMP_X_MULT
            self._jump_buffer_timer = 0
            self.on_wall = False

    # ==================================================================
    # WALL MECHANICS
    # ==================================================================
    def _handle_wall_mechanics(self):
        if self.on_wall and not self.on_ground and self.vel.y > 0:
            # Clamp downward slide speed
            self.vel.y = min(self.vel.y, WALL_SLIDE_SPEED)

    # ==================================================================
    # GRAVITY
    # ==================================================================
    def _apply_gravity(self, dt: float):
        if self._is_dashing:
            return
        if not self.on_ground:
            self.vel.y += GRAVITY * dt
            self.vel.y  = min(self.vel.y, TERMINAL_VEL)

    # ==================================================================
    # SLIDE
    # ==================================================================
    def _handle_slide(self, dt: float, walk_mult: float):
        # Trigger: left/right + down
        if (self._input["down"] and
                (self._input["left"] or self._input["right"]) and
                self.on_ground and not self._is_sliding):
            self._is_sliding  = True
            self._slide_timer = SLIDE_DURATION
            self.vel.x        = self.face_direction * SLIDE_SPEED * walk_mult

        if self._is_sliding:
            self._slide_timer -= dt
            if self._slide_timer <= 0:
                self._is_sliding = False

    # ==================================================================
    # MOVE & COLLIDE
    # ==================================================================
    def _move_and_collide(self, dt: float, tiles):
        prev_on_ground = self.on_ground
        self._pre_land_vel = self.vel.y   # remember for roll check

        self.on_ground  = False
        self.on_wall    = False
        self.on_ceiling = False

        # --- Horizontal ---
        self.pos.x += self.vel.x * dt
        self.rect.x = int(self.pos.x)
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.x > 0:   # moving right
                    self.rect.right = tile.rect.left
                    self.on_wall    = True
                    self.wall_side  = 1
                    # Wall-kick knockback (enables movement tech)
                    self.vel.x      = -WALL_KICK_VEL
                elif self.vel.x < 0: # moving left
                    self.rect.left  = tile.rect.right
                    self.on_wall    = True
                    self.wall_side  = -1
                    self.vel.x      = WALL_KICK_VEL
                self.pos.x = float(self.rect.x)

        # --- Vertical ---
        self.pos.y += self.vel.y * dt
        self.rect.y = int(self.pos.y)
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.y > 0:   # falling
                    self.rect.bottom = tile.rect.top
                    self.on_ground   = True
                    if not prev_on_ground:
                        self._coyote_timer = COYOTE_TIME
                    self.vel.y = 0
                elif self.vel.y < 0: # jumping into ceiling
                    self.rect.top  = tile.rect.bottom
                    self.on_ceiling = True
                    self.vel.y = 0
                self.pos.y = float(self.rect.y)

        # Reset coyote when grounded
        if self.on_ground:
            self._coyote_timer = COYOTE_TIME

    # ==================================================================
    # ROLL
    # ==================================================================
    def _handle_roll(self, dt: float):
        # Trigger on hard landing while holding left or right
        if (self.on_ground and
                self._pre_land_vel > ROLL_FALL_THRESHOLD and
                not self._is_rolling and
                (self._input["left"] or self._input["right"])):
            self._is_rolling  = True
            self._roll_timer  = ROLL_DURATION
            # Carry momentum into a forward roll
            self.vel.x = self.face_direction * WALK_SPEED * 1.3

        if self._is_rolling:
            self._roll_timer -= dt
            if self._roll_timer <= 0:
                self._is_rolling = False

    # ==================================================================
    # STAT DEPLETION
    # ==================================================================
    def _deplete_stats(self, dt: float, is_night: bool):
        mult = NIGHT_DRAIN_MULT if is_night else 1.0
        self.water       -= WATER_DRAIN_DAY  * mult * dt
        self.chlorophyll -= CHLORO_DRAIN_DAY * mult * dt
        self.water       = max(0.0, self.water)
        self.chlorophyll = max(0.0, self.chlorophyll)

        if self.water <= 0 or self.chlorophyll <= 0:
            if not self.psychosis_active:
                self._trigger_psychosis()

    # ==================================================================
    # PSYCHOSIS
    # ==================================================================
    def _trigger_psychosis(self):
        self.psychosis_active = True
        print("[Player] Psychosis triggered!")

    def _update_psychosis(self, dt: float):
        if not self.psychosis_active:
            return
        # If stats recover, cure psychosis
        if self.water > 0 and self.chlorophyll > 0:
            self.cure_psychosis()
            return
        self.psychosis_timer += dt
        if self.psychosis_timer >= PSYCHOSIS_KILL_TIME:
            self.is_alive = False
            print("[Player] Died — psychosis.")

    def cure_psychosis(self):
        self.psychosis_active = False
        self.psychosis_timer  = 0.0

    # ==================================================================
    # HAUSTORIA
    # ==================================================================
    def _try_haustoria(self, nearby_enemies):
        for enemy in nearby_enemies:
            dist = self.pos.distance_to(
                pygame.math.Vector2(enemy.rect.center)
            )
            if dist <= HAUSTORIA_RANGE:
                self.haustoria_active = True
                self.haustoria_target = enemy
                self.vel.x = 0
                self.vel.y = 0
                self.invincible = True
                print(f"[Haustoria] Latched onto {enemy}")
                return

    def _update_haustoria(self, dt: float):
        enemy = self.haustoria_target
        if enemy is None or not getattr(enemy, "is_alive", True):
            self._release_haustoria()
            return

        drain = HAUSTORIA_DRAIN_RATE * dt
        self.water          = min(MAX_WATER,       self.water       + drain)
        self.chlorophyll    = min(MAX_CHLOROPHYLL, self.chlorophyll + drain)
        enemy.water        -= drain
        enemy.chlorophyll  -= drain

        if enemy.water <= 0 and enemy.chlorophyll <= 0:
            enemy.die()
            self._release_haustoria()
            return

        # Player releases manually
        if self._consume("haustoria") or self._consume("jump"):
            self._release_haustoria()

        # Cure psychosis if stats recovered
        if self.psychosis_active and self.water > 5 and self.chlorophyll > 5:
            self.cure_psychosis()

    def _release_haustoria(self):
        self.haustoria_active = False
        self.haustoria_target = None
        self.invincible       = False

    # ==================================================================
    # OBJECT INTERACTION
    # ==================================================================
    def try_pickup(self, world_objects):
        for obj in world_objects:
            if obj.is_held:
                continue
            dist = self.pos.distance_to(obj.pos)
            if dist <= 40:
                self.held_object = obj
                obj.on_pickup(self)
                print(f"[Player] Picked up {obj.obj_type}")
                return

    def try_use(self):
        if self.held_object and self.held_object.obj_type == "plant":
            # Plants grant effects when used
            effect_map = {"speed_plant": "speed", "jump_plant": "jump", "dmg_plant": "damage"}
            eff = effect_map.get(self.held_object.subtype, "speed")
            self.effects.apply(eff)
            self.held_object = None

    # ==================================================================
    # DRAW
    # ==================================================================
    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        draw_rect = self.rect.move(-cam_x, -cam_y)

        # Base colour
        colour = COL_DAIKON

        # Effect outline
        outline_col = self.effects.outline_colour()
        if outline_col:
            outline_rect = draw_rect.inflate(4, 4)
            pygame.draw.rect(surface, outline_col, outline_rect, 2, border_radius=4)

        # Psychosis flicker
        if self.psychosis_active:
            intensity = min(self.psychosis_timer / PSYCHOSIS_KILL_TIME, 1.0)
            r = int(COL_DAIKON[0] * (1 - intensity) + COL_PSYCHOSIS[0] * intensity)
            g = int(COL_DAIKON[1] * (1 - intensity) + COL_PSYCHOSIS[1] * intensity)
            b = int(COL_DAIKON[2] * (1 - intensity) + COL_PSYCHOSIS[2] * intensity)
            colour = (r, g, b)

        # Haustoria flash
        if self.haustoria_active:
            colour = (220, 255, 220)

        pygame.draw.rect(surface, colour, draw_rect, border_radius=4)

        # Face indicator (tiny dot)
        dot_x = draw_rect.centerx + self.face_direction * 10
        dot_y = draw_rect.centery - 6
        pygame.draw.circle(surface, COL_BLACK, (dot_x, dot_y), 3)

        # Held object indicator
        if self.held_object:
            hx = draw_rect.centerx + self.face_direction * 20
            hy = draw_rect.centery
            pygame.draw.circle(surface, (200, 180, 80), (hx, hy), 5)

    # ==================================================================
    # HELPERS
    # ==================================================================
    def _sync_rect(self):
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

    def restore_stats(self, water: float, chlorophyll: float):
        self.water       = min(MAX_WATER,       self.water       + water)
        self.chlorophyll = min(MAX_CHLOROPHYLL, self.chlorophyll + chlorophyll)
        if self.psychosis_active and self.water > 0 and self.chlorophyll > 0:
            self.cure_psychosis()

    def __repr__(self):
        return (f"<Player pos=({self.pos.x:.0f},{self.pos.y:.0f}) "
                f"w={self.water:.1f} ch={self.chlorophyll:.1f} "
                f"alive={self.is_alive}>")
