
import time
import random

# PICO Arc - Bomb Defuse
# LEFT / RIGHT = select wire
# OK = cut selected wire
# No pause!

W = 128
H = 64

WIRES = ["RED", "BLUE", "PINK"]
WIRE_X = [3, 43, 87]
WIRE_W = [35, 41, 38]

START_TIME = 12000
MIN_TIME = 5000


def rect(oled, x, y, w, h, color=1):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < W and 0 <= yy < H:
                oled.pixel(xx, yy, color)


def outline(oled, x, y, w, h):
    for xx in range(x, x + w):
        oled.pixel(xx, y, 1)
        oled.pixel(xx, y + h - 1, 1)

    for yy in range(y, y + h):
        oled.pixel(x, yy, 1)
        oled.pixel(x + w - 1, yy, 1)


def load_best():
    try:
        with open("bomb_best.txt", "r") as f:
            return int(f.read())
    except:
        return 0


def save_best(score):
    try:
        with open("bomb_best.txt", "w") as f:
            f.write(str(score))
    except:
        pass


def draw_screen(oled, score, best, remaining,
                limit_ms, selected):
    oled.fill(0)

    # Scores
    oled.text("S:" + str(score), 0, 0)
    oled.text("B:" + str(best), 84, 0)

    # Countdown
    seconds = max(0, (remaining + 999) // 1000)
    oled.text("TIME: " + str(seconds) + "s", 0, 10)

    # Countdown bar
    rect(oled, 2, 21, 124, 3)
    bar = int(124 * max(0, remaining) / limit_ms)
    rect(oled, 2, 21, bar, 3, 0)

    oled.text("CHOOSE A WIRE!", 13, 27)

    # Three wire choices
    for i in range(3):
        x = WIRE_X[i]
        width = WIRE_W[i]

        # Wire illustration
        rect(oled, x + width // 2, 34, 3, 5)

        # Selection frame
        if selected == i:
            outline(oled, x, 38, width, 15)
        else:
            outline(oled, x + 2, 40, width - 4, 11)

        label_x = x + 4
        oled.text(WIRES[i], label_x, 43)

    oled.text("OK: CUT", 40, 56)

    oled.show()


def blast(oled, beep):
    # Game-only explosion effect
    for i in range(5):
        oled.fill(1)
        oled.text("B L A S T !", 25, 19, 0)
        oled.text("BOMB EXPLODED", 12, 34, 0)
        oled.show()

        if i == 0:
            beep(150)

        time.sleep_ms(100)

        oled.fill(0)
        oled.text("B L A S T !", 25, 19, 1)
        oled.text("BOMB EXPLODED", 12, 34, 1)
        oled.show()
        time.sleep_ms(70)


def run(oled, buttons, beep):
    best = load_best()
    keys = ["LEFT", "RIGHT", "OK", "DOWN"]

    previous = {
        k: buttons[k].value() == 0 for k in keys
    }

    while True:
        score = 0
        game_over = False

        while not game_over:
            selected = 0

            # The correct wire is random on each bomb.
            correct_wire = random.randrange(3)

            # Reduce the time limit as the score increases.
            limit_ms = max(
                MIN_TIME,
                START_TIME - score * 700
            )

            round_start = time.ticks_ms()
            last_beep_second = -1
            next_fast_beep = round_start

            beep(40)

            defused = False

            while True:
                now = time.ticks_ms()
                elapsed = time.ticks_diff(now, round_start)
                remaining = limit_ms - elapsed

                just = {}

                for k in keys:
                    down = buttons[k].value() == 0
                    just[k] = down and not previous[k]
                    previous[k] = down

                # Time expired!
                if remaining <= 0:
                    game_over = True
                    break

                # Normal one-second countdown beeps.
                seconds = (remaining + 999) // 1000

                if remaining > 3000:
                    if seconds != last_beep_second:
                        beep(25)
                        last_beep_second = seconds

                # Urgent beeping during the last three seconds.
                else:
                    if time.ticks_diff(now, next_fast_beep) >= 220:
                        beep(35)
                        next_fast_beep = time.ticks_add(now, 220)

                # Move the wire selector.
                if just["LEFT"]:
                    selected = (selected - 1) % 3
                    beep(8)

                if just["RIGHT"]:
                    selected = (selected + 1) % 3
                    beep(8)

                # Cut the selected wire.
                if just["OK"]:
                    if selected == correct_wire:
                        score += 1

                        if score > best:
                            best = score
                            save_best(best)

                        oled.fill(0)
                        oled.text("WIRE CUT!", 29, 12)
                        oled.text("BOMB DEFUSED!", 12, 27)
                        oled.text("SCORE: " + str(score), 25, 43)
                        oled.show()

                        beep(35)
                        time.sleep_ms(100)
                        beep(65)
                        time.sleep_ms(450)

                        defused = True
                        break

                    else:
                        # Wrong wire means immediate game over.
                        game_over = True
                        break

                draw_screen(
                    oled, score, best, remaining,
                    limit_ms, selected
                )

                time.sleep_ms(8)

            if game_over:
                blast(oled, beep)
                break

            if defused:
                continue

        # Game over screen
        oled.fill(0)
        oled.text("BOMB EXPLODED!", 12, 7)
        oled.text("SCORE: " + str(score), 25, 21)
        oled.text("BEST: " + str(best), 29, 32)
        oled.text("OK: RETRY", 28, 46)
        oled.text("DOWN: MENU", 24, 56)
        oled.show()

        # Release buttons before accepting a new choice.
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
