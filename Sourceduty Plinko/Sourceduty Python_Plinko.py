# Sourceduty Plinko v1.0

import arcade
import random
import math

WIDTH = 750
HEIGHT = 750
TITLE = "Sourceduty Plinko"
BALL_RADIUS = 20
PEG_RADIUS = 5
SLOT_COUNT = 5
BALL_COUNT = 5
INITIAL_SLOT_SCORE = 100
USED_SLOT_SCORE = -50
FLASH_LIMIT = 60

MENU = 0
GAME = 1

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = 0
        self.active = True

    def update(self, pegs):
        self.vy -= 0.3
        self.x += self.vx
        self.y += self.vy

        for peg_x, peg_y in pegs:
            dx = self.x - peg_x
            dy = self.y - peg_y
            dist = math.hypot(dx, dy)
            if dist < BALL_RADIUS + PEG_RADIUS:
                angle = math.atan2(dy, dx)
                self.x = peg_x + math.cos(angle) * (BALL_RADIUS + PEG_RADIUS)
                self.y = peg_y + math.sin(angle) * (BALL_RADIUS + PEG_RADIUS)
                normal = (math.cos(angle), math.sin(angle))
                dot = self.vx * normal[0] + self.vy * normal[1]
                self.vx -= 2 * dot * normal[0]
                self.vy -= 2 * dot * normal[1]
                self.vx *= 0.8
                self.vy *= 0.8

        if self.x <= BALL_RADIUS or self.x >= WIDTH - BALL_RADIUS:
            self.vx *= -1

        if self.y <= 60:
            self.active = False

class PlinkoGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        self.set_update_rate(1/60)
        arcade.set_background_color(arcade.color.BLACK)
        self.state = MENU

        self.ball_preview_x = WIDTH // 2
        self.ball_vx = 3
        self.moving_right = True

        self.pegs = self.create_pegs()
        self.slots = [(i * (WIDTH // SLOT_COUNT), 0, WIDTH // SLOT_COUNT, 50) for i in range(SLOT_COUNT)]
        self.slot_scores = [INITIAL_SLOT_SCORE] * SLOT_COUNT
        self.slot_flash_timer = [0] * SLOT_COUNT

        self.balls = []
        self.score = 0
        self.dropped_balls = 0
        self.game_over = False
        self.current_ball = None

        self.text_score = arcade.Text(f"Score: {self.score}", 10, HEIGHT - 30, arcade.color.AQUA, 16)
        self.text_game_over = arcade.Text("", WIDTH // 2 - 150, HEIGHT // 2, arcade.color.LIME, 24)
        self.slot_texts = [arcade.Text(str(INITIAL_SLOT_SCORE), x + w // 2 - 10, y + 10, arcade.color.PINK, 14)
                           for (x, y, w, h) in self.slots]

        self.menu_text = arcade.Text("Welcome to Sourceduty Plinko", WIDTH // 2 - 170, HEIGHT // 2 + 120, arcade.color.CYAN, 24)
        self.instruction_text = arcade.Text("Press SPACE to start.", WIDTH // 2 - 90, HEIGHT // 2 + 80, arcade.color.LIGHT_GREEN, 16)
        self.rules_text = arcade.Text(
            "Rules:.\n"
            "- Drop five balls into slots to score points.\n"
            "- Each slot starts at 100 points but turns to -50 after use.\n"
            "- Balls bounce off pegs and land in one of five slots.\n"
            "- Press ENTER to drop when ready.\n",
            WIDTH // 2 - 300, HEIGHT // 2 - 20, arcade.color.LIGHT_GRAY, 14, multiline=True, width=600)

    def create_pegs(self):
        pegs = []
        rows, cols = 10, 6
        spacing_x = (WIDTH - 100) // (cols - 1)
        spacing_y = (HEIGHT - 250) // rows
        offset_x = 50
        for row in range(rows):
            for col in range(cols):
                offset = spacing_x // 2 if row % 2 == 1 else 0
                x = offset_x + col * spacing_x + offset
                y = HEIGHT - (row * spacing_y + 150)
                pegs.append((x, y))
        return pegs

    def on_draw(self):
        self.clear()
        if self.state == MENU:
            self.menu_text.draw()
            self.instruction_text.draw()
            self.rules_text.draw()
            return

        for x, y in self.pegs:
            arcade.draw_circle_filled(x, y, PEG_RADIUS, arcade.color.YELLOW)

        for i, (x, y, w, h) in enumerate(self.slots):
            if self.slot_flash_timer[i] < FLASH_LIMIT:
                color = arcade.color.ORANGE if self.slot_flash_timer[i] % 20 < 10 else arcade.color.YELLOW
            else:
                color = arcade.color.YELLOW
            arcade.draw_line(x, y, x + w, y, color, 2)
            arcade.draw_line(x + w, y, x + w, y + h, color, 2)
            arcade.draw_line(x + w, y + h, x, y + h, color, 2)
            arcade.draw_line(x, y + h, x, y, color, 2)
            self.slot_texts[i].draw()

        if not self.current_ball and self.dropped_balls < BALL_COUNT:
            arcade.draw_circle_filled(self.ball_preview_x, HEIGHT - 30, BALL_RADIUS, arcade.color.FUCHSIA)
            arcade.draw_circle_outline(self.ball_preview_x, HEIGHT - 30, BALL_RADIUS, arcade.color.WHITE, 2)

        for ball in self.balls:
            arcade.draw_circle_filled(ball.x, ball.y, BALL_RADIUS, arcade.color.FUCHSIA)
            arcade.draw_circle_outline(ball.x, ball.y, BALL_RADIUS, arcade.color.WHITE, 2)

        if self.current_ball:
            arcade.draw_circle_filled(self.current_ball.x, self.current_ball.y, BALL_RADIUS, arcade.color.FUCHSIA)
            arcade.draw_circle_outline(self.current_ball.x, self.current_ball.y, BALL_RADIUS, arcade.color.WHITE, 2)

        self.text_score.draw()
        self.text_game_over.draw()

    def on_update(self, delta_time):
        if self.state != GAME:
            return

        for i in range(SLOT_COUNT):
            if self.slot_scores[i] == USED_SLOT_SCORE and self.slot_flash_timer[i] < FLASH_LIMIT:
                self.slot_flash_timer[i] += 1

        if not self.current_ball and self.dropped_balls < BALL_COUNT:
            if self.moving_right:
                self.ball_preview_x += self.ball_vx
                if self.ball_preview_x >= WIDTH - BALL_RADIUS:
                    self.moving_right = False
            else:
                self.ball_preview_x -= self.ball_vx
                if self.ball_preview_x <= BALL_RADIUS:
                    self.moving_right = True

        if self.current_ball:
            self.current_ball.update(self.pegs)
            if not self.current_ball.active:
                slot_index = int(self.current_ball.x // (WIDTH // SLOT_COUNT))
                self.score += self.slot_scores[slot_index]
                self.slot_scores[slot_index] = USED_SLOT_SCORE
                self.slot_texts[slot_index].text = str(USED_SLOT_SCORE)
                self.dropped_balls += 1
                self.balls.append(self.current_ball)
                self.current_ball = None
                self.text_score.text = f"Score: {self.score}"

                if self.dropped_balls == BALL_COUNT:
                    self.game_over = True
                    self.text_game_over.text = f"Game Over! Final Score: {self.score}"

    def on_key_press(self, symbol, modifiers):
        if self.state == MENU and symbol == arcade.key.SPACE:
            self.state = GAME
        elif self.state == GAME and symbol == arcade.key.ENTER and not self.current_ball and self.dropped_balls < BALL_COUNT:
            self.current_ball = Ball(self.ball_preview_x, HEIGHT - 30)

if __name__ == "__main__":
    game = PlinkoGame()
    arcade.run()
