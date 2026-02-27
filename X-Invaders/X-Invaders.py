"""
Space Invaders (X Edition) - Python + Pygame
Smaller barriers with improved spacing. Score + lives restored.

Controls
Left / Right Arrow: Move
Up / Down Arrow: Optional small vertical movement
Space: Shoot
Esc: Quit
R: Restart after game over
"""

import math
import random
import sys
import pygame

WIDTH = 900
HEIGHT = 600
FPS = 60

PLAYER_SPEED = 420
BULLET_SPEED = 720
ALIEN_BULLET_SPEED = 360

ALIEN_ROWS = 4
ALIEN_COLS = 10
ALIEN_X_GAP = 70
ALIEN_Y_GAP = 50
ALIEN_MARGIN_TOP = 90
ALIEN_MARGIN_LEFT = 110

ALIEN_STEP_X = 18
ALIEN_STEP_Y = 22
ALIEN_MOVE_INTERVAL_START = 0.55
ALIEN_MOVE_INTERVAL_MIN = 0.18

ALIEN_DROP_CHANCE_PER_STEP = 0.05
ALIEN_DROP_CHANCE_RAMP = 0.0009

PLAYER_LIVES = 3

BARRIER_COUNT = 4
BARRIER_W = 110
BARRIER_H = 24
BARRIER_HP = 16
BARRIER_BOTTOM_PADDING = 120
BARRIER_SIDE_PADDING = 110

BACKGROUND = (10, 10, 16)
WHITE = (245, 245, 250)
GREEN = (70, 230, 140)
RED = (240, 80, 90)
CYAN = (100, 210, 245)

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

class Bullet:
    def __init__(self, x, y, vy, color, radius=4, from_player=True):
        self.x = float(x)
        self.y = float(y)
        self.vy = float(vy)
        self.color = color
        self.radius = radius
        self.from_player = from_player
        self.alive = True

    def update(self, dt):
        self.y += self.vy * dt
        if self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)

    def rect(self):
        r = self.radius
        return pygame.Rect(int(self.x - r), int(self.y - r), int(r * 2), int(r * 2))

class Player:
    def __init__(self, font):
        self.font = font
        self.x = WIDTH * 0.5
        self.y = HEIGHT - 60
        self.cooldown = 0.0
        self.lives = PLAYER_LIVES
        self.score = 0
        self.invuln = 0.0

    def update(self, dt, keys):
        dx = 0.0
        dy = 0.0

        if keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_RIGHT]:
            dx += 1.0
        if keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_DOWN]:
            dy += 1.0

        if dx != 0.0 or dy != 0.0:
            mag = math.hypot(dx, dy)
            dx /= mag
            dy /= mag

        self.x += dx * PLAYER_SPEED * dt
        self.y += dy * (PLAYER_SPEED * 0.35) * dt

        self.x = clamp(self.x, 40, WIDTH - 40)
        self.y = clamp(self.y, HEIGHT - 110, HEIGHT - 35)

        if self.cooldown > 0.0:
            self.cooldown -= dt
        if self.invuln > 0.0:
            self.invuln -= dt

    def shoot(self):
        if self.cooldown > 0.0:
            return None
        self.cooldown = 0.18
        return Bullet(self.x, self.y - 20, -BULLET_SPEED, CYAN, radius=4, from_player=True)

    def draw(self, surf):
        blink = self.invuln > 0.0 and (int(self.invuln * 18) % 2 == 0)
        if blink:
            return
        text = self.font.render("^", True, GREEN)
        rect = text.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(text, rect)

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 16), 32, 32)

class Alien:
    def __init__(self, x, y, font):
        self.x = float(x)
        self.y = float(y)
        self.font = font
        self.alive = True

    def draw(self, surf):
        text = self.font.render("X", True, WHITE)
        rect = text.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(text, rect)

    def rect(self):
        return pygame.Rect(int(self.x - 13), int(self.y - 13), 26, 26)

class Barrier:
    def __init__(self, x, y, w, h, hp):
        self.rect_obj = pygame.Rect(int(x), int(y), int(w), int(h))
        self.max_hp = int(hp)
        self.hp = int(hp)
        self.alive = True

    def hit(self, dmg=1):
        if not self.alive:
            return
        self.hp -= int(dmg)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        t = clamp(self.hp / self.max_hp, 0.0, 1.0)
        shade = int(70 + 160 * t)
        color = (shade, shade, shade + 10)
        pygame.draw.rect(surf, color, self.rect_obj, border_radius=8)
        pygame.draw.rect(surf, (38, 38, 55), self.rect_obj, 2, border_radius=8)

class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(90):
            self.stars.append([random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1), random.randint(1, 3)])

    def update(self, dt):
        for s in self.stars:
            s[1] += (28 + s[2] * 18) * dt
            if s[1] >= HEIGHT:
                s[0] = random.randint(0, WIDTH - 1)
                s[1] = -2
                s[2] = random.randint(1, 3)

    def draw(self, surf):
        for x, y, r in self.stars:
            pygame.draw.circle(surf, (40 + r * 45, 40 + r * 45, 60 + r * 55), (int(x), int(y)), r)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("X Invaders")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("consolas", 40, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 20, bold=False)
        self.font_mid = pygame.font.SysFont("consolas", 26, bold=True)

        self.starfield = Starfield()
        self.player = Player(self.font_big)

        self.aliens = []
        self.player_bullets = []
        self.alien_bullets = []
        self.barriers = []

        self.direction = 1
        self.alien_move_timer = 0.0
        self.alien_move_interval = ALIEN_MOVE_INTERVAL_START
        self.step_count = 0

        self.game_over = False
        self.win = False

        self.spawn_wave()

    def spawn_barriers(self):
        self.barriers.clear()

        y = HEIGHT - BARRIER_BOTTOM_PADDING
        usable_w = WIDTH - (BARRIER_SIDE_PADDING * 2)
        if BARRIER_COUNT <= 1:
            centers = [WIDTH * 0.5]
        else:
            step = usable_w / (BARRIER_COUNT - 1)
            centers = [BARRIER_SIDE_PADDING + i * step for i in range(BARRIER_COUNT)]

        for cx in centers:
            x = int(cx - (BARRIER_W * 0.5))
            self.barriers.append(Barrier(x, y, BARRIER_W, BARRIER_H, BARRIER_HP))

    def spawn_wave(self):
        self.aliens.clear()
        self.player_bullets.clear()
        self.alien_bullets.clear()

        for r in range(ALIEN_ROWS):
            for c in range(ALIEN_COLS):
                x = ALIEN_MARGIN_LEFT + c * ALIEN_X_GAP
                y = ALIEN_MARGIN_TOP + r * ALIEN_Y_GAP
                self.aliens.append(Alien(x, y, self.font_big))

        self.spawn_barriers()

        self.direction = 1
        self.alien_move_timer = 0.0
        self.alien_move_interval = ALIEN_MOVE_INTERVAL_START
        self.step_count = 0
        self.game_over = False
        self.win = False

    def alive_aliens(self):
        return [a for a in self.aliens if a.alive]

    def lowest_aliens_by_column(self):
        cols = {}
        for a in self.alive_aliens():
            col_key = int(round((a.x - ALIEN_MARGIN_LEFT) / ALIEN_X_GAP))
            if col_key not in cols or a.y > cols[col_key].y:
                cols[col_key] = a
        return list(cols.values())

    def maybe_drop_bullets(self):
        shooters = self.lowest_aliens_by_column()
        if not shooters:
            return
        chance = ALIEN_DROP_CHANCE_PER_STEP + self.step_count * ALIEN_DROP_CHANCE_RAMP
        chance = min(chance, 0.25)
        if random.random() < chance:
            shooter = random.choice(shooters)
            self.alien_bullets.append(Bullet(shooter.x, shooter.y + 18, ALIEN_BULLET_SPEED, RED, radius=3, from_player=False))

    def move_aliens_step(self):
        alive = self.alive_aliens()
        if not alive:
            return

        hit_edge = False
        for a in alive:
            nx = a.x + self.direction * ALIEN_STEP_X
            if nx < 30 or nx > WIDTH - 30:
                hit_edge = True
                break

        if hit_edge:
            self.direction *= -1
            for a in alive:
                a.y += ALIEN_STEP_Y
            if any(a.y > HEIGHT - 210 for a in alive):
                self.game_over = True
                self.win = False
        else:
            for a in alive:
                a.x += self.direction * ALIEN_STEP_X

        self.step_count += 1
        alive_count = len(alive)
        total = ALIEN_ROWS * ALIEN_COLS
        speedup = (1.0 - (alive_count / total)) * 0.42
        self.alien_move_interval = clamp(ALIEN_MOVE_INTERVAL_START - speedup, ALIEN_MOVE_INTERVAL_MIN, ALIEN_MOVE_INTERVAL_START)

        self.maybe_drop_bullets()

    def bullet_hits_barriers(self, bullet, dmg=1):
        if not bullet.alive:
            return False
        br = bullet.rect()
        for barrier in self.barriers:
            if not barrier.alive:
                continue
            if br.colliderect(barrier.rect_obj):
                bullet.alive = False
                barrier.hit(dmg)
                return True
        return False

    def handle_collisions(self):
        for b in self.player_bullets:
            if not b.alive:
                continue
            if self.bullet_hits_barriers(b, dmg=1):
                continue

            br = b.rect()
            for a in self.aliens:
                if not a.alive:
                    continue
                if br.colliderect(a.rect()):
                    b.alive = False
                    a.alive = False
                    self.player.score += 100
                    break

        for b in self.alien_bullets:
            if not b.alive:
                continue
            self.bullet_hits_barriers(b, dmg=1)

        if self.player.invuln <= 0.0:
            pr = self.player.rect()
            for b in self.alien_bullets:
                if not b.alive:
                    continue
                if pr.colliderect(b.rect()):
                    b.alive = False
                    self.player.lives -= 1
                    self.player.invuln = 1.2
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.win = False
                    break

    def draw_hud(self):
        score_text = self.font_small.render(f"Score  {self.player.score}", True, WHITE)
        lives_text = self.font_small.render(f"Lives  {self.player.lives}", True, WHITE)
        self.screen.blit(score_text, (18, 14))
        self.screen.blit(lives_text, (18, 38))

        alive = len(self.alive_aliens())
        aliens_text = self.font_small.render(f"Aliens  {alive}", True, WHITE)
        self.screen.blit(aliens_text, (WIDTH - aliens_text.get_width() - 18, 14))

    def draw_banner(self, title, subtitle):
        t = self.font_mid.render(title, True, WHITE)
        s = self.font_small.render(subtitle, True, WHITE)

        box_w = max(t.get_width(), s.get_width()) + 44
        box_h = t.get_height() + s.get_height() + 38
        x = (WIDTH - box_w) // 2
        y = (HEIGHT - box_h) // 2

        overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (x, y))

        self.screen.blit(t, (x + (box_w - t.get_width()) // 2, y + 16))
        self.screen.blit(s, (x + (box_w - s.get_width()) // 2, y + 16 + t.get_height() + 10))

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)
        self.starfield.update(dt)

        if not self.game_over:
            self.alien_move_timer += dt
            if self.alien_move_timer >= self.alien_move_interval:
                self.alien_move_timer -= self.alien_move_interval
                self.move_aliens_step()

            for b in self.player_bullets:
                b.update(dt)
            for b in self.alien_bullets:
                b.update(dt)

            self.handle_collisions()

            self.player_bullets = [b for b in self.player_bullets if b.alive]
            self.alien_bullets = [b for b in self.alien_bullets if b.alive]

            if len(self.alive_aliens()) == 0:
                self.game_over = True
                self.win = True

    def draw(self):
        self.screen.fill(BACKGROUND)
        self.starfield.draw(self.screen)

        for a in self.aliens:
            if a.alive:
                a.draw(self.screen)

        for barrier in self.barriers:
            barrier.draw(self.screen)

        for b in self.player_bullets:
            b.draw(self.screen)
        for b in self.alien_bullets:
            b.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_hud()

        if self.game_over:
            if self.win:
                self.draw_banner("YOU WIN", "Press R to play again, Esc to quit")
            else:
                self.draw_banner("GAME OVER", "Press R to retry, Esc to quit")

        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)

                    if not self.game_over and event.key == pygame.K_SPACE:
                        shot = self.player.shoot()
                        if shot is not None:
                            self.player_bullets.append(shot)

                    if self.game_over and event.key == pygame.K_r:
                        self.player.score = 0
                        self.player.lives = PLAYER_LIVES
                        self.spawn_wave()

            self.update(dt)
            self.draw()

def main():
    random.seed()
    Game().run()

if __name__ == "__main__":
    main()
