
import time
import random

# PICO Arc - SPACE SURVIVAL
# LEFT / RIGHT / UP / DOWN: fly
# OK: pause / resume
# DOWN while paused: return to menu

W = 128
H = 64
TOP = 12

SHIP_W = 11
SHIP_H = 12

MAX_LIVES = 5
EXTRA_LIFE_MS = 20000


SMALL_ROCK = [
    "0011100",
    "0111110",
    "1111111",
    "1111011",
    "1111111",
    "0111110",
    "0011000"
]

BIG_ROCK = [
    "000111000",
    "001111100",
    "011111110",
    "111111111",
    "111101111",
    "111111111",
    "011111110",
    "001111100",
    "000110000"
]


def rect(oled, x, y, w, h, color=1):
    x = int(x)
    y = int(y)

    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < W and TOP <= yy < H:
                oled.pixel(xx, yy, color)


def load_best():
    try:
        with open("space_best.txt", "r") as f:
            return int(f.read())
    except:
        return 0


def save_best(score):
    try:
        with open("space_best.txt", "w") as f:
            f.write(str(score))
    except:
        pass


def make_stars():
    stars = []

    for i in range(25):
        stars.append([
            random.randrange(W),
            random.randrange(TOP, H),
            random.choice([1, 1, 1, 2])
        ])

    return stars


def update_stars(stars, level):
    for s in stars:
        # Stars scroll down to simulate forward flight.
        s[1] += s[2] + (1 if level >= 4 else 0)

        if s[1] >= H:
            s[0] = random.randrange(W)
            s[1] = random.randrange(TOP, TOP + 8)
            s[2] = random.choice([1, 1, 1, 2])


def draw_stars(oled, stars, frame):
    for s in stars:
        x = s[0]
        y = s[1]
        speed = s[2]

        oled.pixel(x, y, 1)

        # Faster stars have a visible trail.
        if speed >= 2 and y > TOP + 1:
            oled.pixel(x, y - 1, 1)

        # Occasional twinkle.
        if frame % 5 == 0 and speed == 2:
            if x + 1 < W:
                oled.pixel(x + 1, y, 1)


def draw_ship(oled, x, y, frame):
    x = int(x)
    y = int(y)

    # Main spacecraft hull.
    rect(oled, x + 4, y, 3, 2)
    rect(oled, x + 3, y + 2, 5, 4)
    rect(oled, x + 2, y + 4, 7, 3)
    rect(oled, x + 1, y + 6, 9, 2)
    rect(oled, x + 3, y + 8, 5, 1)

    # Wing tips.
    oled.pixel(x, y + 7, 1)
    oled.pixel(x + 10, y + 7, 1)
    oled.pixel(x + 1, y + 8, 1)
    oled.pixel(x + 9, y + 8, 1)

    # Cockpit.
    rect(oled, x + 4, y + 2, 3, 3, 0)
    oled.pixel(x + 5, y + 2, 1)

    # Rear engines.
    rect(oled, x + 3, y + 9, 2, 1)
    rect(oled, x + 6, y + 9, 2, 1)

    # Animated engine flames.
    if frame % 2 == 0:
        rect(oled, x + 3, y + 10, 2, 2)
        rect(oled, x + 6, y + 10, 2, 2)
    elif frame % 3 == 0:
        oled.pixel(x + 4, y + 10, 1)
        oled.pixel(x + 6, y + 11, 1)
    else:
        rect(oled, x + 4, y + 10, 3, 1)


def draw_asteroid(oled, asteroid):
    x = int(asteroid[0])
    y = int(asteroid[1])
    kind = asteroid[2]
    rotation = asteroid[4]

    pattern = BIG_ROCK if kind else SMALL_ROCK
    size = len(pattern)

    # Rotate the pixel-art asteroid to animate it.
    for yy in range(size):
        for xx in range(size):
            sx = xx
            sy = yy

            if rotation == 1:
                sx = yy
                sy = size - 1 - xx
            elif rotation == 2:
                sx = size - 1 - xx
                sy = size - 1 - yy
            elif rotation == 3:
                sx = size - 1 - yy
                sy = xx

            if pattern[sy][sx] == "1":
                rect(oled, x + xx, y + yy, 1, 1)

    # Dark crater marks.
    if size == 9:
        rect(oled, x + 3, y + 3, 2, 1, 0)
        rect(oled, x + 6, y + 5, 1, 2, 0)
    else:
        rect(oled, x + 3, y + 2, 1, 1, 0)


def new_asteroid():
    kind = 1 if random.random() < 0.30 else 0
    size = 9 if kind else 7

    return [
        random.randint(1, W - size - 1),
        TOP + 1,
        kind,
        random.choice([-1, 0, 0, 0, 1]),
        random.randrange(4),
        0
    ]


def draw_game(oled, ship_x, ship_y, stars, rocks,
              score, best, lives, level, frame,
              invulnerable, life_notice):
    oled.fill(0)

    # HUD: score, lives, high score.
    oled.text("S:" + str(score), 0, 0)
    oled.text("L:" + str(lives), 47, 0)
    oled.text("B:" + str(best), 82, 0)

    # Separate dashboard from the space scene.
    rect(oled, 0, 10, W, 1)

    # Moving starfield background.
    draw_stars(oled, stars, frame)

    # Asteroid field.
    for asteroid in rocks:
        draw_asteroid(oled, asteroid)

    # Flash the ship briefly after taking a hit.
    if not invulnerable or frame % 4 < 2:
        draw_ship(oled, ship_x, ship_y, frame)

    # Temporary extra-life message.
    if life_notice:
        oled.text("+1 LIFE!", 42, 13)

    # Tiny flight-level indicator at the bottom.
    oled.text("WARP:" + str(level), 0, 56)

    oled.show()


def run(oled, buttons, beep):
    best = load_best()

    keys = ["LEFT", "RIGHT", "UP", "DOWN", "OK"]

    while True:
        score = 0
        lives = 3
        level = 1

        ship_x = 58
        ship_y = 42

        stars = make_stars()
        rocks = []

        frame = 0
        paused = False
        game_over = False

        start_time = time.ticks_ms()
        last_frame = start_time
        last_spawn = start_time
        last_score = start_time
        last_life = start_time

        invulnerable_until = start_time
        life_notice_until = start_time
        pause_started = start_time

        previous = {
            k: buttons[k].value() == 0 for k in keys
        }

        while not game_over:
            now = time.ticks_ms()

            just = {}

            for k in keys:
                down = buttons[k].value() == 0
                just[k] = down and not previous[k]
                previous[k] = down

            # Pause screen.
            if paused:
                if just["OK"]:
                    paused = False

                    pause_duration = time.ticks_diff(
                        now, pause_started
                    )

                    start_time = time.ticks_add(
                        start_time, pause_duration
                    )
                    last_spawn = time.ticks_add(
                        last_spawn, pause_duration
                    )
                    last_score = time.ticks_add(
                        last_score, pause_duration
                    )
                    last_life = time.ticks_add(
                        last_life, pause_duration
                    )
                    last_frame = time.ticks_add(
                        last_frame, pause_duration
                    )
                    invulnerable_until = time.ticks_add(
                        invulnerable_until, pause_duration
                    )
                    life_notice_until = time.ticks_add(
                        life_notice_until, pause_duration
                    )

                elif just["DOWN"]:
                    return

                time.sleep_ms(8)
                continue

            # OK pauses the game.
            if just["OK"]:
                paused = True
                pause_started = now

                oled.fill(0)
                oled.text("SPACE PAUSED", 20, 14)
                oled.text("OK: RESUME", 24, 30)
                oled.text("DOWN: MENU", 24, 44)
                oled.show()

                continue

            # Move the spacecraft.
            if buttons["LEFT"].value() == 0:
                ship_x -= 2

            if buttons["RIGHT"].value() == 0:
                ship_x += 2

            if buttons["UP"].value() == 0:
                ship_y -= 2

            if buttons["DOWN"].value() == 0:
                ship_y += 2

            ship_x = max(1, min(W - SHIP_W - 1, ship_x))
            ship_y = max(TOP + 1, min(H - SHIP_H - 1, ship_y))

            # Draw and update at a steady rate.
            if time.ticks_diff(now, last_frame) < 35:
                time.sleep_ms(5)
                continue

            last_frame = now
            frame += 1

            # Survival score: one point per second.
            if time.ticks_diff(now, last_score) >= 1000:
                last_score = now
                score += 1

                if score > best:
                    best = score
                    save_best(best)

            # Difficulty increases every 12 seconds.
            elapsed = time.ticks_diff(now, start_time)
            level = min(5, 1 + elapsed // 12000)

            # Extra life every 20 seconds, up to 5 lives.
            if time.ticks_diff(now, last_life) >= EXTRA_LIFE_MS:
                last_life = now

                if lives < MAX_LIVES:
                    lives += 1
                    life_notice_until = time.ticks_add(now, 1200)
                    beep(70)

            show_life = (
                time.ticks_diff(life_notice_until, now) > 0
            )

            # Scroll the background.
            update_stars(stars, level)

            # Spawn asteroids faster at higher levels.
            spawn_delay = max(340, 900 - (level - 1) * 140)

            if time.ticks_diff(now, last_spawn) >= spawn_delay:
                last_spawn = now
                rocks.append(new_asteroid())

            # Move and spin the asteroids.
            for a in rocks:
                a[0] += a[3]
                a[1] += 1 + level * 0.22 + a[2] * 0.15

                a[5] += 1
                if a[5] >= 5:
                    a[5] = 0
                    a[4] = (a[4] + 1) % 4

                size = 9 if a[2] else 7

                if a[0] <= 1:
                    a[0] = 1
                    a[3] = abs(a[3])

                if a[0] >= W - size - 1:
                    a[0] = W - size - 1
                    a[3] = -abs(a[3])

            # Ship collision box.
            ship_cx = ship_x + 5
            ship_cy = ship_y + 5

            can_hit = (
                time.ticks_diff(now, invulnerable_until) >= 0
            )

            remaining_rocks = []

            for a in rocks:
                size = 9 if a[2] else 7
                rock_cx = a[0] + size / 2
                rock_cy = a[1] + size / 2

                collided = (
                    abs(ship_cx - rock_cx) < size / 2 + 3
                    and
                    abs(ship_cy - rock_cy) < size / 2 + 3
                )

                if collided and can_hit:
                    lives -= 1
                    beep(100)

                    invulnerable_until = time.ticks_add(
                        now, 1000
                    )

                    # Remove the rock that hit the ship.
                    continue

                # Remove asteroids that have passed the screen.
                if a[1] < H:
                    remaining_rocks.append(a)

            rocks = remaining_rocks

            if lives <= 0:
                game_over = True
                break

            invulnerable = (
                time.ticks_diff(invulnerable_until, now) > 0
            )

            draw_game(
                oled, ship_x, ship_y, stars, rocks,
                score, best, lives, level, frame,
                invulnerable, show_life
            )

            time.sleep_ms(3)

        # Final explosion effect.
        for i in range(5):
            oled.fill(0)

            if i % 2 == 0:
                for j in range(18):
                    ex = ship_x + random.randint(-7, 15)
                    ey = ship_y + random.randint(-5, 15)
                    oled.pixel(ex, ey, 1)

            oled.text("SHIP DESTROYED", 8, 25)
            oled.show()

            beep(60) if i == 0 else None
            time.sleep_ms(90)

        # Game over screen.
        oled.fill(0)
        oled.text("SPACE GAME OVER", 4, 7)
        oled.text("SCORE: " + str(score), 25, 22)
        oled.text("BEST: " + str(best), 29, 33)
        oled.text("OK: RETRY", 28, 47)
        oled.text("DOWN: MENU", 24, 56)
        oled.show()

        # Wait for all game buttons to be released.
        while any(buttons[k].value() == 0 for k in keys):
            time.sleep_ms(8)

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
