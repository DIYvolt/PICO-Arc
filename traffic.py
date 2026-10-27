import time
import random

# PICO Arc - Traffic Car
# OLED: 128 x 64
# LEFT/RIGHT: change lanes
# UP/DOWN: move car vertically
# OK: pause/resume
# DOWN while paused: return to menu

LANES = [16, 40, 64, 88, 112]

ROAD_TOP = 10
PLAYER_H = 13
FRAME_MS = 45


def fill_rect(oled, x, y, w, h, color=1):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < 128 and 0 <= yy < 64:
                oled.pixel(xx, yy, color)


def load_best():
    try:
        with open("traffic_best.txt", "r") as f:
            return int(f.read())
    except:
        return 0


def save_best(score):
    try:
        with open("traffic_best.txt", "w") as f:
            f.write(str(score))
    except:
        pass


def new_vehicle(traffic, skip_index=-1):
    # Pick a lane and a safe starting position.
    for attempt in range(40):
        lane = random.randrange(5)
        y = -random.randint(18, 54)
        safe = True

        for i, v in enumerate(traffic):
            if i == skip_index:
                continue

            if v[0] == lane and abs(v[1] - y) < 21:
                safe = False
                break

        if safe:
            truck = 1 if random.random() < 0.35 else 0
            return [lane, y, truck, False]

    return [
        random.randrange(5),
        -random.randint(20, 50),
        random.randrange(2),
        False
    ]


def draw_road(oled, offset):
    # Road boundaries.
    fill_rect(oled, 4, ROAD_TOP, 1, 54, 1)
    fill_rect(oled, 123, ROAD_TOP, 1, 54, 1)

    # FOUR animated lane divider lines.
    # Five lanes are created by these four lines.
    for x in (28, 52, 76, 100):
        for start_y in range(-16, 64, 16):
            y = ROAD_TOP + start_y + offset
            fill_rect(oled, x, y, 2, 7, 1)


def draw_car(oled, cx, y, truck=False, player=False):
    if truck:
        # Truck body
        fill_rect(oled, cx - 7, y, 15, 16, 1)

        # Truck windows and cargo separation
        fill_rect(oled, cx - 5, y + 2, 11, 4, 0)
        fill_rect(oled, cx - 5, y + 10, 11, 3, 0)

        # Headlights / details
        oled.pixel(cx - 5, y + 1, 1)
        oled.pixel(cx + 5, y + 1, 1)

        # Wheels
        fill_rect(oled, cx - 8, y + 4, 2, 4, 1)
        fill_rect(oled, cx + 7, y + 4, 2, 4, 1)

    else:
        # Car body
        fill_rect(oled, cx - 5, y, 11, 13, 1)

        # Front and rear windows
        fill_rect(oled, cx - 3, y + 2, 7, 3, 0)
        fill_rect(oled, cx - 3, y + 8, 7, 2, 0)

        # Wheels
        fill_rect(oled, cx - 6, y + 3, 2, 3, 1)
        fill_rect(oled, cx + 6, y + 3, 2, 3, 1)

        if player:
            # Distinct driver car details
            oled.pixel(cx - 3, y + 1, 1)
            oled.pixel(cx + 3, y + 1, 1)


def draw_scene(oled, traffic, lane, player_y,
               score, best, road_offset):
    oled.fill(0)

    # Score bar
    oled.text("S:" + str(score), 0, 0, 1)
    oled.text("B:" + str(best), 88, 0, 1)

    draw_road(oled, road_offset)

    # Draw enemy cars and trucks
    for v in traffic:
        enemy_lane = v[0]
        enemy_y = v[1]
        truck = v[2]

        draw_car(
            oled,
            LANES[enemy_lane],
            enemy_y,
            truck,
            False
        )

    # Draw the player's car
    draw_car(
        oled,
        LANES[lane],
        player_y,
        False,
        True
    )

    oled.show()


def run(oled, buttons, beep):
    best = load_best()

    while True:
        lane = 2
        player_y = 46

        score = 0
        speed = 2
        road_offset = 0
        paused = False
        crashed = False

        traffic = []

        # Start with three separated vehicles.
        for i in range(3):
            traffic.append(new_vehicle(traffic))

        # Track button presses without waiting for button release.
        keys = ["LEFT", "RIGHT", "UP", "DOWN", "OK"]
        previous = {}

        for k in keys:
            previous[k] = buttons[k].value() == 0

        last_frame = time.ticks_ms()

        while not crashed:
            now = time.ticks_ms()

            # Read buttons every loop.
            just_pressed = {}

            for k in keys:
                pressed = buttons[k].value() == 0
                just_pressed[k] = pressed and not previous[k]
                previous[k] = pressed

            # PAUSED mode
            if paused:
                if just_pressed["OK"]:
                    paused = False
                    last_frame = now

                elif just_pressed["DOWN"]:
                    return

                time.sleep_ms(8)
                continue

            # LEFT: immediately move one lane left.
            if just_pressed["LEFT"]:
                if lane > 0:
                    lane -= 1
                    beep(10)

            # RIGHT: immediately move one lane right.
            if just_pressed["RIGHT"]:
                if lane < 4:
                    lane += 1
                    beep(10)

            # UP/DOWN move the player's car vertically.
            if just_pressed["UP"]:
                player_y = max(ROAD_TOP + 1, player_y - 4)

            if just_pressed["DOWN"]:
                player_y = min(63 - PLAYER_H, player_y + 4)

            # Pause or resume.
            if just_pressed["OK"]:
                paused = True

                oled.fill(0)
                oled.text("PAUSED", 39, 19, 1)
                oled.text("OK: RESUME", 23, 34, 1)
                oled.text("DOWN: MENU", 23, 46, 1)
                oled.show()

                time.sleep_ms(8)
                continue

            # Update traffic and draw at a controlled speed.
            if time.ticks_diff(now, last_frame) >= FRAME_MS:
                last_frame = now

                road_offset = (road_offset + speed) % 16

                for i, v in enumerate(traffic):
                    v[1] += speed

                    enemy_h = 16 if v[2] else 13

                    # Award a point when a vehicle is passed.
                    if v[1] > player_y + PLAYER_H and not v[3]:
                        score += 1
                        v[3] = True
                        speed = min(5, 2 + score // 4)

                    # Recycle vehicles that leave the screen.
                    if v[1] > 64:
                        replacement = new_vehicle(traffic, i)

                        v[0] = replacement[0]
                        v[1] = replacement[1]
                        v[2] = replacement[2]
                        v[3] = False

                    # Collision: same lane and overlapping vertically.
                    if v[0] == lane:
                        if (v[1] < player_y + PLAYER_H and
                                v[1] + enemy_h > player_y):
                            crashed = True
                            break

                if not crashed:
                    draw_scene(
                        oled,
                        traffic,
                        lane,
                        player_y,
                        score,
                        best,
                        road_offset
                    )

            # Keep checking button presses frequently.
            time.sleep_ms(8)

        # GAME OVER
        if score > best:
            best = score
            save_best(best)

        oled.fill(0)
        oled.text("CRASH!", 42, 8, 1)
        oled.text("SCORE: " + str(score), 25, 23, 1)
        oled.text("BEST: " + str(best), 29, 34, 1)
        oled.text("OK: RETRY", 28, 48, 1)
        oled.text("DOWN: MENU", 24, 57, 1)
        oled.show()

        # Wait for the player to release any held buttons.
        while (buttons["OK"].value() == 0 or
               buttons["DOWN"].value() == 0):
            time.sleep_ms(8)

        # Quick button presses work on the result screen too.
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