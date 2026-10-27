# PICO Arc - Dragon Runner
# Raspberry Pi Pico + SSD1306 128x64
#
# UP       = Jump
# OK       = Pause / Resume
# DOWN     = Return to menu (during pause or gameplay)
#
# Best score is saved in dragon_score.txt when possible.

import time
import random

WIDTH = 128
HEIGHT = 64
GROUND_Y = 54
PLAYER_X = 14
PLAYER_H = 13

FRAME_MS = 20
START_SPEED = 4
MAX_SPEED = 8

SCORE_FILE = "dragon_score.txt"


def pressed(buttons, name):
    try:
        return buttons[name].value() == 0
    except Exception:
        return False


def wait_release(buttons, name):
    start = time.ticks_ms()

    while pressed(buttons, name):
        time.sleep_ms(10)

        if time.ticks_diff(time.ticks_ms(), start) > 1000:
            break


def rect(oled, x, y, w, h, color=1):
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(WIDTH, x + w)
    y2 = min(HEIGHT, y + h)

    for py in range(y1, y2):
        for px in range(x1, x2):
            oled.pixel(px, py, color)


def hline(oled, x, y, w, color=1):
    if 0 <= y < HEIGHT:
        for px in range(max(0, x), min(WIDTH, x + w)):
            oled.pixel(px, y, color)


def load_best():
    try:
        with open(SCORE_FILE, "r") as f:
            return max(0, int(f.read().strip()))
    except Exception:
        return 0


def save_best(score):
    try:
        with open(SCORE_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        # Game still works if file writing is unavailable.
        pass


def draw_dragon(oled, x, feet, frame, jumping):
    top = feet - PLAYER_H

    # Body
    rect(oled, x + 2, top + 4, 6, 7)

    # Head and snout
    rect(oled, x + 6, top, 5, 6)
    rect(oled, x + 9, top + 3, 3, 2)

    # Eye
    oled.pixel(x + 9, top + 1, 0)
    oled.pixel(x + 10, top + 1, 1)

    # Tail
    rect(oled, x, top + 6, 3, 2)

    # Legs
    if jumping:
        hline(oled, x + 3, top + 5, 5)
        oled.pixel(x + 4, top + 4, 1)
        oled.pixel(x + 5, top + 3, 1)
    elif frame % 2 == 0:
        rect(oled, x + 2, feet - 2, 3, 2)
        rect(oled, x + 7, feet - 1, 3, 1)
    else:
        rect(oled, x + 2, feet - 1, 3, 1)
        rect(oled, x + 7, feet - 2, 3, 2)


def draw_cactus(oled, x, height):
    rect(oled, x + 3, GROUND_Y - height, 4, height)

    # DOWN branch
    if height >= 10:
        rect(oled, x, GROUND_Y - height + 5, 3, 3)
        rect(oled, x + 1, GROUND_Y - height + 3, 2, 4)

    # Right branch
    if height >= 13:
        rect(oled, x + 7, GROUND_Y - height + 8, 3, 3)
        rect(oled, x + 8, GROUND_Y - height + 6, 2, 5)


def draw_scene(oled, player_y, jumping, frame,
               cactus_x, cactus_h, pair, pair_gap,
               score, best, speed):

    oled.fill(0)

    # Live score: top-DOWN; best score: top-right
    oled.text("S:%03d" % min(score, 999), 0, 0, 1)
    oled.text("B:%03d" % min(best, 999), 88, 0, 1)

    # Small clouds
    cloud_x = WIDTH - ((frame // 3) % (WIDTH + 10))
    hline(oled, cloud_x, 13, 7)
    oled.pixel(cloud_x + 2, 12, 1)
    oled.pixel(cloud_x + 5, 11, 1)

    hline(oled, (cloud_x + 55) % WIDTH, 18, 6)

    # Ground
    hline(oled, 0, GROUND_Y, WIDTH)

    # Moving ground marks
    shift = (frame * speed) % 32

    for i in range(5):
        mark_x = i * 32 - shift
        hline(oled, mark_x, GROUND_Y + 4, 4)

    # Player
    draw_dragon(oled, PLAYER_X, player_y, frame, jumping)

    # First cactus
    draw_cactus(oled, cactus_x, cactus_h)

    # Sometimes a second cactus follows the first
    if pair:
        second_height = cactus_h
        if cactus_h <= 13:
            second_height = random.choice((10, 13, 16))
        draw_cactus(
            oled,
            cactus_x + pair_gap,
            second_height
        )

    oled.show()


def pause_screen(oled, buttons):
    # Call only after the OK button has been pressed.
    while True:
        oled.fill(0)
        oled.text("GAME PAUSED", 16, 7, 1)
        oled.text("OK = RESUME", 16, 27, 1)
        oled.text("DOWN = MENU", 16, 43, 1)
        oled.show()

        if pressed(buttons, "OK"):
            wait_release(buttons, "OK")
            return True

        if pressed(buttons, "DOWN"):
            wait_release(buttons, "DOWN")
            return False

        time.sleep_ms(20)


def game_over(oled, buttons, beep, score):
    try:
        beep(90)
        time.sleep_ms(60)
        beep(140)
    except Exception:
        pass

    while True:
        oled.fill(0)
        oled.text("GAME OVER", 28, 6, 1)
        oled.text("SCORE: %d" % score, 24, 21, 1)
        oled.text("OK = RETRY", 20, 38, 1)
        oled.text("DOWN = MENU", 16, 52, 1)
        oled.show()

        if pressed(buttons, "OK"):
            wait_release(buttons, "OK")
            return True

        if pressed(buttons, "DOWN"):
            wait_release(buttons, "DOWN")
            return False

        time.sleep_ms(20)


def run(oled, buttons, beep):
    best = load_best()

    while True:
        player_y = GROUND_Y
        velocity = 0
        jumping = False

        cactus_x = WIDTH + 12
        cactus_h = random.choice((10, 13, 16, 18))

        # Roughly half of obstacle groups contain two cacti
        pair = random.random() < 0.45
        pair_gap = random.randint(12, 18)

        score = 0
        frame = 0
        speed = START_SPEED

        last_jump = False
        last_ok = False

        while True:
            frame += 1

            # OK pauses the game.
            ok_now = pressed(buttons, "OK")

            if ok_now and not last_ok:
                wait_release(buttons, "OK")

                if not pause_screen(oled, buttons):
                    return

                # Prevent accidental jump immediately after resuming.
                last_jump = pressed(buttons, "UP")
                last_ok = False
                continue

            last_ok = ok_now

            # DOWN also exits directly during gameplay.
            if pressed(buttons, "DOWN"):
                wait_release(buttons, "DOWN")
                return

            # Jump using UP.
            jump_now = pressed(buttons, "UP")

            if jump_now and not last_jump and not jumping:
                jumping = True
                velocity = -8

                try:
                    beep(20)
                except Exception:
                    pass

            last_jump = jump_now

            # Jump physics
            if jumping:
                player_y += velocity
                velocity += 1

                if player_y >= GROUND_Y:
                    player_y = GROUND_Y
                    velocity = 0
                    jumping = False

            # Move obstacle group
            cactus_x -= speed

            group_width = 10
            if pair:
                group_width = pair_gap + 10

            # Count the group after it passes the screen.
            if cactus_x + group_width < 0:
                score += 1

                if score > best:
                    best = score
                    save_best(best)

                # Increase speed gradually
                if score % 4 == 0 and speed < MAX_SPEED:
                    speed += 1

                cactus_x = WIDTH + random.randint(20, 42)
                cactus_h = random.choice((10, 13, 16, 18))
                pair = random.random() < 0.45
                pair_gap = random.randint(12, 18)

            # Collision detection for both cacti
            player_DOWN = PLAYER_X + 3
            player_right = PLAYER_X + 11
            player_top = player_y - PLAYER_H + 4
            player_bottom = player_y - 1

            collision = False
            obstacle_count = 2 if pair else 1

            for i in range(obstacle_count):
                obstacle_x = cactus_x

                if i == 1:
                    obstacle_x += pair_gap

                obstacle_DOWN = obstacle_x
                obstacle_right = obstacle_x + 10
                obstacle_top = GROUND_Y - cactus_h

                if (
                    player_right > obstacle_DOWN
                    and player_DOWN < obstacle_right
                    and player_bottom > obstacle_top
                    and player_top < GROUND_Y
                ):
                    collision = True
                    break

            if collision:
                if score > best:
                    best = score
                    save_best(best)

                if not game_over(oled, buttons, beep, score):
                    return

                break

            draw_scene(
                oled, player_y, jumping, frame,
                cactus_x, cactus_h, pair, pair_gap,
                score, best, speed
            )

            time.sleep_ms(FRAME_MS)
