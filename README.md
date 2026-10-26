# PICO Arc
**A DIY handheld game console powered by the Raspberry Pi Pico.**

PICO Arc is a small, homemade gaming console built around the Raspberry Pi Pico and a 128×64 SSD1306 OLED display. It uses physical buttons for controls and supports multiple mini-games, all running on MicroPython.

The goal is to create a simple, affordable, and customizable game console that makers and electronics enthusiasts can build themselves.

## ✨ Features

- Raspberry Pi Pico with MicroPython
- 128×64 SSD1306 OLED display
- Physical button controls
- Buzzer for sound effects
- Main menu to launch games
- High-score board
- Automatic startup using `main.py`
- Simple Python code that can be modified to create new games

## 🎮 Games

- **Dragon** — Jump and avoid obstacles.
- **Snake** — Eat food, grow, and collect special items.
- **Traffic** — Change lanes and avoid vehicles.
- **Pong** — Keep the ball in play.
- **Shooter** — Shoot enemies and survive.
- **Bomb Defuse** — Choose the correct wire before time runs out.
- **Space Survival** — Navigate through space and avoid asteroids.
- **High Scores** — View saved records for supported games.

## 🧰 Hardware Required

- Raspberry Pi Pico
- SSD1306 128×64 I2C OLED display
- 5 push buttons
- Active buzzer
- Breadboard or custom PCB
- Jumper wires
- USB power supply or suitable portable power source

## 🔌 Wiring

| Component | Pico GPIO |
|---|---|
| OLED SDA | GP4 |
| OLED SCL | GP5 |
| UP button | GP10 |
| DOWN button | GP11 |
| LEFT button | GP12 |
| RIGHT button | GP13 |
| OK button | GP14 |
| Buzzer | GP15 |

The buttons use active-low inputs with pull-up resistors enabled in software. Connect each button between its assigned GPIO and GND.

The OLED I2C address is `0x3C`.

## 💻 Software

- MicroPython for Raspberry Pi Pico
- Thonny IDE
- SSD1306 OLED driver

## 🚀 Installation

1. Install MicroPython on the Raspberry Pi Pico.
2. Connect the Pico to your computer and open Thonny.
3. Copy `ssd1306.py`, `main.py`, and the game files to the Pico.
4. Make sure all filenames match the imports in `main.py`.
5. Save the main launcher as `main.py` on the Pico.
6. Restart the Pico. The game menu should start automatically.

## 🕹️ Controls

Controls may differ slightly between games.

- **UP / DOWN / LEFT / RIGHT:** Move or select, depending on the game.
- **OK:** Start, confirm, shoot, or pause/resume, depending on the game.
- **DOWN:** Return to the menu when supported by the current game.

## 🏆 High Scores

PICO Arc stores game records in text files on the Pico's filesystem. The high-score board reads the score files for the supported games.

## 🛠️ Customization

You can modify the existing games, change the controls, add sound effects, or create your own game using the same game interface.

## 📸 Project Photos

Add photos of the completed console, wiring, OLED menu, and gameplay here.

## 📄 License

This project is intended for learning, experimentation, and DIY electronics.

See the `LICENSE` file for the terms of reuse.

---

**Built with curiosity and electronics — PICO Arc.**
