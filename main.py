
from machine import Pin, SoftI2C
import ssd1306
import time

# ==========================================
# PICO Arc - Raspberry Pi Pico Game Console
# OLED: SDA GP4, SCL GP5
# Buttons: GP10-GP14
# Active buzzer: GP15
# ==========================================

i2c = SoftI2C(
    scl=Pin(5),
    sda=Pin(4),
    freq=200000
)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)

buttons = {
    "UP": Pin(10, Pin.IN, Pin.PULL_UP),
    "DOWN": Pin(11, Pin.IN, Pin.PULL_UP),
    "LEFT": Pin(12, Pin.IN, Pin.PULL_UP),
    "RIGHT": Pin(13, Pin.IN, Pin.PULL_UP),
    "OK": Pin(14, Pin.IN, Pin.PULL_UP)
}

buzzer = Pin(15, Pin.OUT)
buzzer.value(0)

GAMES = [
    "Snake",
    "Dragon",
    "Traffic Car",
    "Pong",
    "Bomb Defuse",
    "Space Survival",
    "High Scores"
]

TOTAL_GAMES = len(GAMES)


# ==========================================
# BASIC DRAWING FUNCTIONS
# Only uses pixel(), text(), fill(), show()
# ==========================================

def pixel(x, y, color=1):
    if 0 <= x < 128 and 0 <= y < 64:
        oled.pixel(int(x), int(y), color)


def hline(x, y, width, color=1):
    for px in range(x, x + width):
        pixel(px, y, color)


def vline(x, y, height, color=1):
    for py in range(y, y + height):
        pixel(x, py, color)


def rect(x, y, width, height, color=1):
    for py in range(y, y + height):
        hline(x, py, width, color)


def outline(x, y, width, height, color=1):
    hline(x, y, width, color)
    hline(x, y + height - 1, width, color)
    vline(x, y, height, color)
    vline(x + width - 1, y, height, color)


def line(x1, y1, x2, y2, color=1):
    # Bresenham line drawing
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        pixel(x1, y1, color)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x1 += sx

        if e2 < dx:
            err += dx
            y1 += sy


def circle(cx, cy, radius, filled=False, color=1):
    radius_sq = radius * radius
    inner_sq = (radius - 1) * (radius - 1)

    for yy in range(-radius, radius + 1):
        for xx in range(-radius, radius + 1):
            distance = xx * xx + yy * yy

            if distance <= radius_sq:
                if filled or distance >= inner_sq:
                    pixel(cx + xx, cy + yy, color)


# ==========================================
# BUZZER
# Active buzzers make one pitch, so we use
# different rhythms instead of different notes.
# ==========================================

def beep(duration=35):
    buzzer.value(1)
    time.sleep_ms(duration)
    buzzer.value(0)


def startup_music():
    pattern = [
        (45, 50),
        (45, 50),
        (90, 70),
        (40, 45),
        (65, 50),
        (120, 100)
    ]

    for duration, pause in pattern:
        beep(duration)
        time.sleep_ms(pause)


def wait_release(button):
    while button.value() == 0:
        time.sleep_ms(12)


# ==========================================
# BIG PICO Arc LOGO FONT
# ==========================================

FONT = {
    "P": [
        "11110", "10001", "10001", "11110",
        "10000", "10000", "10000"
    ],
    "I": [
        "11111", "00100", "00100", "00100",
        "00100", "00100", "11111"
    ],
    "C": [
        "01111", "10000", "10000", "10000",
        "10000", "10000", "01111"
    ],
    "O": [
        "01110", "10001", "10001", "10001",
        "10001", "10001", "01110"
    ],
    "A": [
        "01110", "10001", "10001", "11111",
        "10001", "10001", "10001"
    ],
    "R": [
        "11110", "10001", "10001", "11110",
        "10100", "10010", "10001"
    ],
    "r": [
        "00000", "00000", "10110", "11001",
        "10000", "10000", "10000"
    ],
    "c": [
        "00000", "00000", "01110", "10000",
        "10000", "10000", "01110"
    ],
    " ": [
        "00000", "00000", "00000", "00000",
        "00000", "00000", "00000"
    ]
}

def draw_big_text(text, x, y, scale):
    cursor_x = x

    for char in text:
        if char == " ":
            cursor_x += 4 * scale
            continue

        pattern = FONT.get(char)

        if pattern is None:
            cursor_x += 6 * scale
            continue

        for row in range(7):
            for col in range(5):
                if pattern[row][col] == "1":
                    rect(
                        cursor_x + col * scale,
                        y + row * scale,
                        scale,
                        scale
                    )

        cursor_x += 6 * scale


# ==========================================
# STARTUP ANIMATION
# ==========================================

def startup_screen():
    oled.fill(1)
    oled.show()
    time.sleep_ms(70)

    oled.fill(0)
    oled.show()

    # Logo slides in from the right
    for x in range(128, 9, -8):
        oled.fill(0)

        draw_big_text("PICO", x, 10, 3)
        draw_big_text("Arc", x+78, 15, 2)

        pixel(5, 8)
        pixel(121, 10)
        pixel(8, 54)
        pixel(118, 52)

        oled.show()
        time.sleep_ms(25)

    # Final logo
    oled.fill(0)
    draw_big_text("PICO", 10, 10, 3)
    draw_big_text("Arc", 90, 15, 2)
    oled.text("POCKET ARCADE", 20, 34, 1)
    oled.text("POWERING UP...", 17, 52, 1)
    oled.show()

    startup_music()
    time.sleep_ms(250)


def loading_screen():
    for progress in range(0, 101, 5):
        oled.fill(0)

        draw_big_text("PICO Arc", 28, 3, 2)
        oled.text("SYSTEM LOADING", 16, 22, 1)

        # Loading bar outline
        outline(9, 35, 110, 11)

        # Loading bar fill
        fill_width = progress * 106 // 100

        if fill_width > 0:
            rect(11, 37, fill_width, 7)

        oled.text(str(progress) + "%", 52, 51, 1)
        oled.show()

        time.sleep_ms(4)


# ==========================================
# GAME LOGOS - CUSTOM PIXEL ART
# Each logo fits inside the OLED screen.
# ==========================================

def draw_icon(game, x, y, frame):

    # ---------- SNAKE ----------
    if game == "Snake":
        # Food
        pixel(x + 5, y + 4)
        pixel(x + 4, y + 5)
        pixel(x + 6, y + 5)
        pixel(x + 5, y + 6)
        line(x + 5, y + 3, x + 7, y + 1)

        # Snake body
        rect(x + 5, y + 15, 7, 5)
        rect(x + 11, y + 10, 7, 6)
        rect(x + 17, y + 10, 7, 5)
        rect(x + 23, y + 10, 7, 6)
        rect(x + 23, y + 16, 7, 5)

        # Head
        rect(x + 29, y + 16, 8, 7)
        pixel(x + 34, y + 18, 0)

        # Animated tongue
        if frame % 8 < 4:
            line(x + 36, y + 21, x + 39, y + 21)
        else:
            line(x + 36, y + 21, x + 38, y + 23)

    # ---------- DRAGON ----------
    elif game == "Dragon":
        # Wings
        line(x + 19, y + 13, x + 7, y + 4)
        line(x + 7, y + 4, x + 11, y + 15)
        line(x + 11, y + 15, x + 19, y + 17)

        line(x + 22, y + 13, x + 33, y + 4)
        line(x + 33, y + 4, x + 30, y + 15)
        line(x + 30, y + 15, x + 22, y + 17)

        # Tail and body
        line(x + 18, y + 17, x + 5, y + 21)
        line(x + 5, y + 21, x + 10, y + 19)
        rect(x + 13, y + 14, 15, 7)

        # Head and horns
        rect(x + 23, y + 8, 11, 10)
        rect(x + 23, y + 4, 3, 6)
        rect(x + 29, y + 4, 3, 5)
        rect(x + 32, y + 12, 7, 4)

        # Eye and nostril
        pixel(x + 30, y + 11, 0)
        pixel(x + 36, y + 13, 0)

        # Fire
        if frame % 6 < 3:
            line(x + 38, y + 15, x + 40, y + 18)
        else:
            line(x + 38, y + 15, x + 40, y + 13)

    # ---------- TRAFFIC CAR ----------
    elif game == "Traffic Car":
        # Road
        outline(x + 6, y + 0, 29, 25)

        # Moving road markings
        for yy in range(-4, 28, 8):
            mark_y = y + ((yy + frame * 2) % 28)
            rect(x + 19, mark_y, 3, 4)

        # Car wheels
        rect(x + 13, y + 7, 4, 5)
        rect(x + 25, y + 7, 4, 5)
        rect(x + 13, y + 17, 4, 5)
        rect(x + 25, y + 17, 4, 5)

        # Car body and windscreen
        rect(x + 15, y + 5, 12, 17)
        rect(x + 17, y + 7, 8, 4, 0)
        rect(x + 17, y + 16, 8, 3, 0)

        pixel(x + 17, y + 5)
        pixel(x + 24, y + 5)

    # ---------- PONG ----------
    elif game == "Pong":
        # Center dashed line
        for yy in range(y + 2, y + 25, 6):
            vline(x + 20, yy, 3)

        # Paddles
        rect(x + 5, y + 5, 3, 8)
        rect(x + 34, y + 13, 3, 8)

        # Moving ball
        ball_x = x + 15 + (frame % 8)
        ball_y = y + 8 + (frame % 5)
        rect(ball_x, ball_y, 4, 4)

    # ---------- BOMB DEFUSE ----------
    elif game == "Bomb Defuse":
        # Bomb
        circle(x + 20, y + 15, 9, True)

        # Shine and fuse
        pixel(x + 17, y + 11, 0)
        line(x + 20, y + 6, x + 26, y + 2)
        line(x + 26, y + 2, x + 30, y + 4)

        # Animated fuse spark
        if frame % 6 < 3:
            pixel(x + 31, y + 1)
            pixel(x + 28, y + 0)
            pixel(x + 32, y + 5)
        else:
            pixel(x + 30, y + 2)
            pixel(x + 34, y + 1)
            pixel(x + 32, y + 4)

    # ---------- SPACE SURVIVAL ----------
    elif game == "Space Survival":
        # Stars
        pixel(x + 5, y + 4)
        pixel(x + 34, y + 5)
        pixel(x + 8, y + 19)
        pixel(x + 32, y + 21)

        # Spaceship
        line(x + 20, y + 2, x + 10, y + 20)
        line(x + 20, y + 2, x + 30, y + 20)
        line(x + 10, y + 20, x + 30, y + 20)
        line(x + 14, y + 14, x + 26, y + 14)
        line(x + 15, y + 20, x + 13, y + 23)
        line(x + 25, y + 20, x + 27, y + 23)

        # Animated engine
        if frame % 6 < 3:
            line(x + 17, y + 21, x + 17, y + 24)
            line(x + 23, y + 21, x + 23, y + 24)

    # ---------- HIGH SCORES ----------
    elif game == "High Scores":
        # Trophy cup
        outline(x + 13, y + 3, 15, 12)
        line(x + 13, y + 6, x + 7, y + 5)
        line(x + 7, y + 5, x + 7, y + 12)
        line(x + 7, y + 12, x + 14, y + 12)

        line(x + 27, y + 6, x + 34, y + 5)
        line(x + 34, y + 5, x + 34, y + 12)
        line(x + 34, y + 12, x + 27, y + 12)

        vline(x + 20, y + 15, 5)
        hline(x + 15, y + 20, 11)
        hline(x + 12, y + 23, 17)

        # Star on trophy
        pixel(x + 20, y + 6)
        pixel(x + 19, y + 8)
        pixel(x + 21, y + 8)


# ==========================================
# GAME SELECT SCREEN
# ==========================================

def draw_header(index):
    oled.text("PICO Arc", 4, 0, 1)

    number = "{:02d}/{:02d}".format(
        index + 1,
        TOTAL_GAMES
    )
    oled.text(number, 88, 0, 1)

    hline(0, 9, 128)


def draw_footer():
    hline(0, 53, 128)


def draw_card(index, offset, frame, sway=0):
    game = GAMES[index]

    # Logo area
    icon_x = 44 + offset + sway
    icon_y = 13
    draw_icon(game, icon_x, icon_y, frame)

    # Center title on the screen
    title_x = (128 - len(game) * 8) // 2
    oled.text(game, title_x + offset, 42, 1)


def draw_menu(index, frame):
    cycle = frame % 24

    # Slow side-to-side logo motion, from -3 to +3 pixels
    if cycle < 12:
        sway = (cycle // 2) - 3
    else:
        sway = 9 - (cycle // 2)

    oled.fill(0)
    draw_header(index)
    draw_card(index, 0, frame, sway)
    draw_footer()
    oled.show()


def animate_selection(old_index, new_index, direction, frame):
    # 16 steps x 8 pixels = 128-pixel screen width.
    # Right: old game exits left, new game enters right.
    # Left: old game exits right, new game enters left.

    for step in range(17):
        distance = step * 8

        old_offset = -direction * distance
        new_offset = direction * (128 - distance)

        oled.fill(0)
        draw_header(new_index)

        draw_card(old_index, old_offset, frame + step)
        draw_card(new_index, new_offset, frame + step)

        draw_footer()
        oled.show()

        time.sleep_ms(5)


# ==========================================
# MESSAGE / GAME LAUNCHER
# ==========================================

def show_message(title, message):
    oled.fill(0)
    oled.text(title[:16], 0, 10, 1)
    oled.text(message[:16], 0, 30, 1)
    oled.text("OK = BACK", 20, 52, 1)
    oled.show()

    while buttons["OK"].value() == 1:
        time.sleep_ms(20)

    wait_release(buttons["OK"])


def show_scores():
    # High-score storage can be connected here later.
    show_message("HIGH SCORES", "Score file soon")


def launch_game(name):
    try:
        if name == "Snake":
            import snake
            snake.run(oled, buttons, beep)

        elif name == "Traffic Car":
            import traffic
            traffic.run(oled, buttons, beep)
        elif name == "Pong":
            import pong
            pong.run(oled, buttons, beep)
        elif name == "Bomb Defuse":
            import bomb_defuse
            bomb_defuse.run(oled, buttons, beep)
        elif name == "Dragon":
            import dragon
            dragon.run(oled, buttons, beep)
        elif name == "Space Survival":
            import space_survival
            space_survival.run(oled, buttons, beep)
        elif name == "High Scores":
            import high_scores
            high_scores.run(oled, buttons, beep)
        else:
            show_message(name, "Coming soon!")
 
    except Exception as error:
        oled.fill(0)
        oled.text("GAME ERROR", 15, 8, 1)
        oled.text(name[:16], 0, 23, 1)
        oled.text(str(error)[:16], 0, 38, 1)
        oled.text("OK = BACK", 20, 54, 1)
        oled.show()

        while buttons["OK"].value() == 1:
            time.sleep_ms(20)

        wait_release(buttons["OK"])


# ==========================================
# START R-CADE
# ==========================================

startup_screen()
loading_screen()

selected = 0
frame = 0

draw_menu(selected, frame)

while True:
    direction = 0

    if buttons["LEFT"].value() == 0:
        direction = -1
        wait_release(buttons["LEFT"])

    elif buttons["RIGHT"].value() == 0:
        direction = 1
        wait_release(buttons["RIGHT"])

    elif buttons["UP"].value() == 0:
        direction = -1
        wait_release(buttons["UP"])

    elif buttons["DOWN"].value() == 0:
        direction = 1
        wait_release(buttons["DOWN"])

    elif buttons["OK"].value() == 0:
        wait_release(buttons["OK"])
        beep(75)

        launch_game(GAMES[selected])
        draw_menu(selected, frame)

        time.sleep_ms(50)
        continue

    if direction != 0:
        old_selected = selected
        selected = (selected + direction) % TOTAL_GAMES

        beep(30)

        animate_selection(
            old_selected,
            selected,
            direction,
            frame
        )

    frame += 1
    draw_menu(selected, frame)
    time.sleep_ms(45)
