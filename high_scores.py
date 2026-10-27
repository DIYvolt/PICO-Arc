import time

# PICO Arc - High Scores

GAMES = [
    ("Dragon", "dragon_score.txt"),
    ("Snake", "snake_best.txt"),
    ("Traffic", "traffic_best.txt"),
    ("Pong", "pong_best.txt"),
    ("Bomb", "bomb_best.txt"),
    ("Space", "space_best.txt")
]


def read_score(filename):
    try:
        with open(filename, "r") as f:
            return max(0, int(f.read()))
    except:
        return 0


def run(oled, buttons, beep):
    top = 0
    count = len(GAMES)

    old_up = buttons["UP"].value()
    old_down = buttons["DOWN"].value()
    old_ok = buttons["OK"].value()

    while True:
        oled.fill(0)

        oled.text("HIGH SCORES", 0, 0)
        oled.text("----------------", 0, 10)

        # Show up to five rows at a time
        visible = 5

        for i in range(visible):
            index = top + i

            if index >= count:
                break

            name, filename = GAMES[index]
            score = read_score(filename)

            y = 19 + i * 9
            oled.text(name, 0, y)
            oled.text(str(score), 90, y)

        oled.show()

        up = buttons["UP"].value()
        down = buttons["DOWN"].value()
        ok = buttons["OK"].value()

        # Buttons are active-low
        if up == 0 and old_up != 0:
            if top > 0:
                top -= 1
                beep(20)

        if down == 0 and old_down != 0:
            if top < count - visible:
                top += 1
                beep(20)

        if ok == 0 and old_ok != 0:
            beep(25)

            while buttons["OK"].value() == 0:
                time.sleep_ms(8)

            return

        old_up = up
        old_down = down
        old_ok = ok

        time.sleep_ms(15)