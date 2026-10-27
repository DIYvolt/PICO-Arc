
import time
import random

# PICO Arc - Pong
# LEFT / RIGHT: move paddle
# OK: pause / resume
# DOWN while paused: return to menu

WIDTH = 128
HEIGHT = 64
TOP = 10

PADDLE_W = 23
PADDLE_H = 3
PADDLE_Y = 58
BALL_SIZE = 3

START_LIVES = 3
MAX_LIVES = 5
EXTRA_LIFE_MS = 20000


def load_best():
    try:
        with open("pong_best.txt", "r") as f:
            return int(f.read())
    except:
        return 0


def save_best(value):
    try:
        with open("pong_best.txt", "w") as f:
            f.write(str(value))
    except:
        pass


def draw_box(oled, x, y, w, h, color=1):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < WIDTH and 0 <= yy < HEIGHT:
                oled.pixel(xx, yy, color)


def reset_ball():
    return (
        62.0,
        30.0,
        random.choice([-1.0, 1.0]) * 0.8,
        1.6
    )


def draw_game(oled, paddle_x, ball_x, ball_y,
              score, best, lives, speed_level):
    oled.fill(0)

    # Top status bar
    oled.text("S:" + str(score), 0, 0)
    oled.text("L:" + str(lives), 49, 0)
    oled.text("B:" + str(best), 83, 0)

    # Playfield border and divider
    draw_box(oled, 0, TOP, WIDTH, 1)
    draw_box(oled, 0, 63, WIDTH, 1)

    # Paddle
    draw_box(
        oled,
        int(paddle_x),
        PADDLE_Y,
        PADDLE_W,
        PADDLE_H
    )

    # Ball
    draw_box(
        oled,
        int(ball_x),
        int(ball_y),
        BALL_SIZE,
        BALL_SIZE
    )

    # Speed indicator
    for i in range(min(speed_level, 5)):
        draw_box(oled, 105 + i * 4, 12, 2, 2)

    oled.show()


def run(oled, buttons, beep):
    best = load_best()

    while True:
        score = 0
        lives = START_LIVES

        paddle_x = (WIDTH - PADDLE_W) / 2
        ball_x, ball_y, vx, vy = reset_ball()

        speed = 1.0
        speed_level = 1

        started_at = time.ticks_ms()
        last_frame = started_at
        last_paddle_move = started_at
        last_extra_life = started_at

        paused = False
        game_over = False

        keys = ["LEFT", "RIGHT", "OK", "DOWN"]
        previous = {
            k: buttons[k].value() == 0 for k in keys
        }

        while not game_over:
            now = time.ticks_ms()

            # Detect quick button presses.
            pressed_now = {}
            for k in keys:
                current = buttons[k].value() == 0
                pressed_now[k] = current and not previous[k]
                previous[k] = current

            if paused:
                if pressed_now["OK"]:
                    paused = False
                    last_frame = now
                    last_paddle_move = now
                    started_at = time.ticks_add(
                        started_at,
                        time.ticks_diff(now, pause_started)
                    )
                    last_extra_life = time.ticks_add(
                        last_extra_life,
                        time.ticks_diff(now, pause_started)
                    )

                elif pressed_now["DOWN"]:
                    return

                time.sleep_ms(8)
                continue

            # Pause the game.
            if pressed_now["OK"]:
                paused = True
                pause_started = now

                oled.fill(0)
                oled.text("PONG PAUSED", 24, 15)
                oled.text("OK: RESUME", 24, 30)
                oled.text("DOWN: MENU", 24, 44)
                oled.show()

                time.sleep_ms(8)
                continue

            # Paddle movement works with short taps or holding.
            if time.ticks_diff(now, last_paddle_move) >= 35:
                moved = False

                if buttons["LEFT"].value() == 0:
                    paddle_x -= 4
                    moved = True

                if buttons["RIGHT"].value() == 0:
                    paddle_x += 4
                    moved = True

                paddle_x = max(
                    1,
                    min(WIDTH - PADDLE_W - 1, paddle_x)
                )

                if moved:
                    last_paddle_move = now

            # Update game at a steady rate.
            if time.ticks_diff(now, last_frame) < 25:
                time.sleep_ms(5)
                continue

            last_frame = now

            # Increase ball speed gradually during survival.
            elapsed = time.ticks_diff(now, started_at)
            new_level = 1 + elapsed // 12000
            new_level = min(5, new_level)

            if new_level > speed_level:
                speed_level = new_level
                speed = 1.0 + (speed_level - 1) * 0.22

            # Give one extra life every 20 seconds survived.
            life_elapsed = time.ticks_diff(now, last_extra_life)

            if life_elapsed >= EXTRA_LIFE_MS:
                last_extra_life = now

                if lives < MAX_LIVES:
                    lives += 1
                    beep(100)

            # Move ball.
            ball_x += vx * speed
            ball_y += vy * speed

            # Left and right walls.
            if ball_x <= 1:
                ball_x = 1
                vx = abs(vx)

            if ball_x >= WIDTH - BALL_SIZE - 1:
                ball_x = WIDTH - BALL_SIZE - 1
                vx = -abs(vx)

            # Top wall.
            if ball_y <= TOP + 1:
                ball_y = TOP + 1
                vy = abs(vy)

            # Paddle collision.
            if (
                vy > 0
                and ball_y + BALL_SIZE >= PADDLE_Y
                and ball_y + BALL_SIZE <= PADDLE_Y + PADDLE_H + 3
                and ball_x + BALL_SIZE >= paddle_x
                and ball_x <= paddle_x + PADDLE_W
            ):
                ball_y = PADDLE_Y - BALL_SIZE

                # Change bounce angle depending on hit position.
                paddle_center = paddle_x + PADDLE_W / 2
                ball_center = ball_x + BALL_SIZE / 2
                offset = (ball_center - paddle_center) / (PADDLE_W / 2)

                vx = offset * 1.8
                vy = -1.8

                score += 1
                beep(20)

                if score > best:
                    best = score
                    save_best(best)

            # Ball missed: lose one life.
            if ball_y > HEIGHT:
                lives -= 1
                beep(100)

                if lives <= 0:
                    game_over = True
                    break

                ball_x, ball_y, vx, vy = reset_ball()

                # Short reset pause after losing a life.
                draw_game(
                    oled, paddle_x, ball_x, ball_y,
                    score, best, lives, speed_level
                )

                reset_at = time.ticks_ms()
                while time.ticks_diff(
                    time.ticks_ms(), reset_at
                ) < 500:
                    time.sleep_ms(8)

                last_frame = time.ticks_ms()

            draw_game(
                oled, paddle_x, ball_x, ball_y,
                score, best, lives, speed_level
            )

        # Game over screen.
        oled.fill(0)
        oled.text("GAME OVER", 28, 8)
        oled.text("SCORE: " + str(score), 25, 22)
        oled.text("BEST: " + str(best), 29, 33)
        oled.text("LIVES: 0", 34, 42)
        oled.text("OK: RETRY", 28, 53)
        oled.show()

        # Wait until buttons are released.
        while any(buttons[k].value() == 0 for k in keys):
            time.sleep_ms(8)

        # Retry or return to launcher.
        while True:
            if buttons["OK"].value() == 0:
                while buttons["OK"].value() == 0:
                    time.sleep_ms(8)
                break

            if buttons["DOWN"].value() == 0:
                while buttons["DOWN"].value() == 0:
                    time.sleep_ms(8)
                return

            time.sleep_ms(8)
