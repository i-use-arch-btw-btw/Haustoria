# combat.py
import pygame
import math
from constants import (
    SPEAR_DAMAGE, SPEAR_RANGE, SPEAR_COOLDOWN,
    THROW_SPEED, ROCK_STUN_TIME,
    PARRY_EDGE_TOL, PARRY_WINDOW,
)


# ------------------------------------------------------------------
class Projectile(pygame.sprite.Sprite):
    """A thrown spear or rock flying through the air."""

    def __init__(self, pos, direction, speed, damage,
                 stuns=False, stun_time=0.0, pierces=False):
        super().__init__()
        self.pos       = pygame.math.Vector2(pos)
        self.vel       = pygame.math.Vector2(direction).normalize() * speed
        self.damage    = damage
        self.stuns     = stuns
        self.stun_time = stun_time
        self.pierces   = pierces
        self.alive     = True

        # Placeholder rect — replace with sprite image later
        self.image = pygame.Surface((12, 4), pygame.SRCALPHA)
        self.image.fill((220, 200, 120))
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt, tiles):
        self.pos  += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Destroy on tile collision
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                self.alive = False
                return

    def hit_enemy(self, enemy) -> bool:
        """Returns True if this projectile hits the enemy."""
        if not self.alive:
            return False
        if self.rect.colliderect(enemy.rect):
            enemy.take_damage(self.damage)
            if self.stuns:
                enemy.stunned    = True
                enemy.stun_timer = self.stun_time
            if not self.pierces:
                self.alive = False
            return True
        return False


# ------------------------------------------------------------------
class CombatSystem:
    """
    Handles all combat interactions: melee, throw, parry, enemy attacks.
    Owned by the Game object; receives player + enemy refs each frame.
    """

    def __init__(self):
        self.spear_cooldown_timer = 0.0
        self.projectiles: list[Projectile] = []

    # ------------------------------------------------------------------
    # Timers
    # ------------------------------------------------------------------
    def update(self, dt, player, enemies, tiles):
        self.spear_cooldown_timer = max(0.0, self.spear_cooldown_timer - dt)

        # Update projectiles
        for p in self.projectiles:
            p.update(dt, tiles)
            for enemy in enemies:
                p.hit_enemy(enemy)
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Enemy attacks vs player
        for enemy in enemies:
            self._enemy_attack(enemy, player)

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------
    def player_melee(self, player, enemies) -> bool:
        """
        Player swings the spear.
        Returns True if attack was executed (cooldown allows it).
        """
        if self.spear_cooldown_timer > 0:
            return False

        self.spear_cooldown_timer = SPEAR_COOLDOWN

        # Build attack hitbox in front of the player
        px, py = player.rect.centerx, player.rect.centery
        fx     = player.face_direction  # +1 right, -1 left
        _, _, dmg_mult = player.effects.get_multipliers()

        # The hitbox extends SPEAR_RANGE px in the facing direction
        atk_rect = pygame.Rect(
            px + (fx * 4),            # slight forward offset
            py - SPEAR_RANGE // 2,
            SPEAR_RANGE,
            SPEAR_RANGE,
        )
        if fx < 0:
            atk_rect.x = px - SPEAR_RANGE - 4

        hit_any = False
        for enemy in enemies:
            if atk_rect.colliderect(enemy.rect):
                # Parry check: did we hit right at the edge of enemy's attack?
                if self._check_parry(player, enemy, atk_rect):
                    self._do_parry(player, enemy)
                else:
                    enemy.take_damage(int(SPEAR_DAMAGE * dmg_mult))
                    hit_any = True

        # Spear-bounce off wall / ceiling
        if player.on_wall or player.on_ceiling:
            player.vel.y = -abs(player.vel.y) * 0.7

        return True

    # ------------------------------------------------------------------
    def player_throw(self, player, held_object):
        """
        Throw whatever the player is holding.
        held_object: an InteractableObject instance.
        """
        if held_object is None:
            return

        _, _, dmg_mult = player.effects.get_multipliers()
        direction      = pygame.math.Vector2(player.face_direction, -0.2)

        if held_object.obj_type == "spear":
            proj = Projectile(
                pos       = player.rect.center,
                direction = direction,
                speed     = THROW_SPEED,
                damage    = int(SPEAR_DAMAGE * dmg_mult),
                pierces   = True,
            )
        elif held_object.obj_type == "rock":
            proj = Projectile(
                pos       = player.rect.center,
                direction = direction,
                speed     = THROW_SPEED * 0.75,
                damage    = int(SPEAR_DAMAGE * 0.5 * dmg_mult),
                stuns     = True,
                stun_time = ROCK_STUN_TIME,
            )
        else:
            # Generic throwable
            proj = Projectile(
                pos       = player.rect.center,
                direction = direction,
                speed     = THROW_SPEED * 0.6,
                damage    = int(SPEAR_DAMAGE * 0.4 * dmg_mult),
            )

        self.projectiles.append(proj)
        player.held_object = None

    # ------------------------------------------------------------------
    # Parry helpers
    # ------------------------------------------------------------------
    def _check_parry(self, player, enemy, atk_rect: pygame.Rect) -> bool:
        """
        A parry triggers when:
          - the enemy is currently in an attack animation
          - AND our attack hitbox overlaps the *edge* of the enemy hitbox
            (within PARRY_EDGE_TOL pixels of the border)
        """
        if not enemy.attacking:
            return False

        er = enemy.rect
        # Check if atk_rect overlaps within PARRY_EDGE_TOL of any edge
        left_edge   = abs(atk_rect.right  - er.left)   < PARRY_EDGE_TOL
        right_edge  = abs(atk_rect.left   - er.right)  < PARRY_EDGE_TOL
        top_edge    = abs(atk_rect.bottom - er.top)    < PARRY_EDGE_TOL
        bottom_edge = abs(atk_rect.top    - er.bottom) < PARRY_EDGE_TOL

        return left_edge or right_edge or top_edge or bottom_edge

    def _do_parry(self, player, enemy):
        enemy.stunned    = True
        enemy.stun_timer = 1.2
        enemy.attacking  = False
        # Small upward bounce for the player
        player.vel.y = -200
        print(f"[Combat] Parry! {enemy}")

    # ------------------------------------------------------------------
    # Enemy attack vs player
    # ------------------------------------------------------------------
    def _enemy_attack(self, enemy, player):
        if not enemy.attacking:
            return
        if enemy.rect.colliderect(player.rect):
            player.water       -= enemy.damage * 0.6
            player.chlorophyll -= enemy.damage * 0.4
            player.water       = max(0.0, player.water)
            player.chlorophyll = max(0.0, player.chlorophyll)

    # ------------------------------------------------------------------
    def draw(self, surface, camera_offset):
        for p in self.projectiles:
            r = p.rect.move(-camera_offset[0], -camera_offset[1])
            pygame.draw.rect(surface, (220, 200, 120), r)
