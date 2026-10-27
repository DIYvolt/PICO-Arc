
import time
import random

# PICO Arc - Snake
GRID_W = 16
GRID_H = 6
CELL = 8
TOP = 10

BEST_FILE = "snake_best.txt"


def pressed(button):
    return button.value() == 0


def rect(oled, x, y, w, h):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < 128 and 0 <= yy < 64:
                oled.pixel(xx, yy, 1)


def line(oled, x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= x1 < 128 and 0 <= y1 < 64:
            oled.pixel(x1, y1, 1)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x1 += sx

        if e2 < dx:
            err += dx
            y1 += sy


def new_cell(blocked):
    free = []

    for y in range(GRID_H):
        for x in range(GRID_W):
            if (x, y) not in blocked:
                free.append((x, y))

    if not free:
        return None

    return random.choice(free)


def load_best():
    try:
        with open(BEST_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0


def save_best(best):
    try:
        with open(BEST_FILE, "w") as f:
            f.write(str(best))
    except:
        pass


def draw_diamond(oled, x, y):
    cx = x * CELL + 4
    cy = TOP + y * CELL + 4

    line(oled, cx, cy - 3, cx + 3, cy)
    line(oled, cx + 3, cy, cx, cy + 3)
    line(oled, cx, cy + 3, cx - 3, cy)
    line(oled, cx - 3, cy, cx, cy - 3)


def draw_game(oled, snake, food, diamond, score, best):
    oled.fill(0)

    # Current score on the left, best score on the right
    oled.text("S:" + str(score), 0, 0, 1)
    oled.text("B:" + str(best), 82, 0, 1)

    # Tiny food
    if food is not None:
        rect(
            oled,
            food[0] * CELL + 3,
            TOP + food[1] * CELL + 3,
            2, 2
        )

    # Diamond only inside the playfield
    if diamond is not None:
        draw_diamond(oled, diamond[0], diamond[1])

    # Small snake segments
    for sx, sy in snake:
        rect(
            oled,
            sx * CELL + 1,
            TOP + sy * CELL + 1,
            5, 5
        )

    oled.show()


def pause_screen(oled, buttons, beep):
    oled.fill(0)
    oled.text("PAUSED", 36, 8, 1)
    oled.text("OK: RESUME", 24, 27, 1)
    oled.text("DOWN: MENU", 24, 44, 1)
    oled.show()

    # Avoid treating the click that opened pause as a new click
    last_ok = pressed(buttons["OK"])
    last_down = pressed(buttons["DOWN"])

    while True:
        ok_now = pressed(buttons["OK"])
        down_now = pressed(buttons["DOWN"])

        if ok_now and not last_ok:
            beep(35)
            return True

        if down_now and not last_down:
            return False

        last_ok = ok_now
        last_down = down_now
        time.sleep_ms(8)


def game_over_screen(oled, buttons, score, beep):
    oled.fill(0)
    oled.text("GAME OVER", 28, 7, 1)
    oled.text("SCORE:" + str(score), 24, 22, 1)
    oled.text("OK: RETRY", 28, 38, 1)
    oled.text("DOWN: MENU", 24, 51, 1)
    oled.show()

    last_ok = pressed(buttons["OK"])
    last_down = pressed(buttons["DOWN"])

    while True:
        ok_now = pressed(buttons["OK"])
        down_now = pressed(buttons["DOWN"])

        if ok_now and not last_ok:
            beep(50)
            return True

        if down_now and not last_down:
            return False

        last_ok = ok_now
        last_down = down_now
        time.sleep_ms(8)


def run(oled, buttons, beep):
    best = load_best()

    while True:
        snake = [(7, 3), (6, 3), (5, 3)]
        direction = (1, 0)

        score = 0
        food = new_cell(snake)
        diamond = None

        foods_since_diamond = 0
        over = False
        turn_locked = False

        previous = {
            "UP": False,
            "DOWN": False,
            "LEFT": False,
            "RIGHT": False,
            "OK": False
        }

        # Slightly slower movement
        move_delay = 300
        last_move = time.ticks_ms() - move_delay

        draw_game(oled, snake, food, diamond, score, best)

        while not over:
            # Scan buttons frequently for quick clicks
            current = {
                "UP": pressed(buttons["UP"]),
                "DOWN": pressed(buttons["DOWN"]),
                "LEFT": pressed(buttons["LEFT"]),
                "RIGHT": pressed(buttons["RIGHT"]),
                "OK": pressed(buttons["OK"])
            }

            # OK pauses the game
            if current["OK"] and not previous["OK"]:
                resume = pause_screen(oled, buttons, beep)

                if not resume:
                    save_best(best)
                    return

                # Reset input history and movement timer
                previous = {
                    "UP": pressed(buttons["UP"]),
                    "DOWN": pressed(buttons["DOWN"]),
                    "LEFT": pressed(buttons["LEFT"]),
                    "RIGHT": pressed(buttons["RIGHT"]),
                    "OK": pressed(buttons["OK"])
                }

                last_move = time.ticks_ms()
                continue

            # One direction change per movement step
            if not turn_locked:
                new_direction = None

                if current["UP"] and not previous["UP"]:
                    new_direction = (0, -1)
                elif current["DOWN"] and not previous["DOWN"]:
                    new_direction = (0, 1)
                elif current["LEFT"] and not previous["LEFT"]:
                    new_direction = (-1, 0)
                elif current["RIGHT"] and not previous["RIGHT"]:
                    new_direction = (1, 0)

                if new_direction is not None:
                    opposite = (-direction[0], -direction[1])

                    if new_direction != opposite:
                        direction = new_direction
                        turn_locked = True

            previous = current

            now = time.ticks_ms()

            if time.ticks_diff(now, last_move) >= move_delay:
                last_move = now
                turn_locked = False

                head = (
                    snake[0][0] + direction[0],
                    snake[0][1] + direction[1]
                )

                eating = head == food
                taking_diamond = (
                    diamond is not None and head == diamond
                )

                # Wall collision
                if (
                    head[0] < 0 or head[0] >= GRID_W
                    or head[1] < 0 or head[1] >= GRID_H
                ):
                    over = True

                # Self collision
                elif head in (snake if eating else snake[:-1]):
                    over = True

                else:
                    snake.insert(0, head)

                    # Normal food: grow and score
                    if eating:
                        score += 1
                        beep(25)

                        if score > best:
                            best = score

                        blocked = list(snake)
                        if diamond is not None:
                            blocked.append(diamond)

                        food = new_cell(blocked)

                        # Spawn a diamond after 9 normal foods
                        # collected since the previous diamond spawned
                        if diamond is None:
                            foods_since_diamond += 1

                            if (
                                foods_since_diamond >= 9
                                and food is not None
                            ):
                                diamond = new_cell(snake + [food])
                                foods_since_diamond = 0

                        if food is None:
                            over = True

                    # Diamond: shrink by up to 3 segments
                    elif taking_diamond:
                        beep(80)
                        diamond = None

                        for _ in range(4):
                            if len(snake) > 2:
                                snake.pop()

                    else:
                        snake.pop()

                # Make the game gradually faster, but keep it
                # a little slower than the previous version
                move_delay = max(190, 300 - score)

                draw_game(
                    oled, snake, food, diamond, score, best
                )

            # Keep checking buttons while waiting for movement
            time.sleep_ms(8)

        save_best(best)

        # OK retries; DOWN returns to PICO Arc menu
        if not game_over_screen(oled, buttons, score, beep):
            return
