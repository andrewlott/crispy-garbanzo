from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFont,
    ImageOps
)
from TP_lib import epd2in13_V4, gt1151
import atexit
import cairosvg
import os
import threading
import time
from button import Button
from screen import Screen
from data import get_stats_summary

WIDTH, HEIGHT = 250, 122
flag_t = 1

epd = epd2in13_V4.EPD()
gt = gt1151.GT1151()
GT_Dev = gt1151.GT_Development()
GT_Old = gt1151.GT_Development()
epd.init(epd.FULL_UPDATE)
gt.GT_Init()
epd.Clear(0xFF)  # Clear the display to white

active_screen = None

def pthread_irq() :
    print("pthread running")
    while flag_t == 1 :
        if(gt.digital_read(gt.INT) == 0) :
            GT_Dev.Touch = 1
        else :
            GT_Dev.Touch = 0
    print("thread:exit")

t = threading.Thread(target = pthread_irq)
t.setDaemon(True)
t.start()


def wait_for_button_press():
    global active_screen
    print("Waiting for button press...")
    while True:
        gt.GT_Scan(GT_Dev, GT_Old)
        if(not GT_Dev.TouchpointFlag):
            time.sleep(0.05)
            continue  # No touch detected

        GT_Dev.TouchpointFlag = 0
        x = WIDTH - GT_Dev.Y[0] # flipped
        y = GT_Dev.X[0]

        if (x == WIDTH or x == 0) and (y == HEIGHT or y == 0):
            # Randomly get tap right at the corners, so ignore
            time.sleep(0.05)
            continue
        # Optional: avoid duplicate detection
        if GT_Dev.X[0] == y and GT_Dev.Y[0] == WIDTH - x and GT_Dev.S == GT_Old.S:
            time.sleep(0.05)
            continue

        print(f"Touched at ({x}, {y})")
        if active_screen is not None:
            active_screen.check_touch(x, y)
        time.sleep(0.1)

def show_pihole_logo():
    print("Displaying Pi-hole logo...")
    image = pihole_image()
    display_image(image)

def pihole_image():
    image_path = "pihole_logo.png"
    if not os.path.exists(image_path):
        print("Downloading pihole logo")
        svg_url = "https://pi-hole.github.io/graphics/Vortex/Vortex_with_Wordmark.svg"
        # Convert SVG to PNG (temporary in-memory image)
        cairosvg.svg2png(
            url=svg_url,
            write_to=image_path,
            output_width=WIDTH,
            output_height=HEIGHT,
        )

    # Load and convert to 1-bit image
    logo = Image.open(image_path).convert("L")

    logo = ImageOps.invert(logo)
    logo = logo.convert('1')

    # Create a blank white background
    image = Image.new("1", (WIDTH, HEIGHT), 1)

    # Get position to center the logo
    logo_w, logo_h = logo.size
    pos_x = (WIDTH - logo_w) // 2
    pos_y = (HEIGHT - logo_h) // 2

    # Paste the logo onto the background
    image.paste(logo, (pos_x, pos_y))
    return image

def data_image(d, title):
    img = Image.new('1', (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(img)
    font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
    font_medium = ImageFont.truetype("DejaVuSans.ttf", 12)
    font_small = ImageFont.truetype("DejaVuSans.ttf", 10)

    offset = 30
    y = 20
    draw.text((5, 0), title, font=font_medium, fill=0)
    draw.line((0, 18, WIDTH, 18), fill=0)

    for key, value in d.items():
        draw.text((5, y), str(" ".join(key.split("_")).title()), font=font_small, fill=0)
        draw.text((150, y), str(value), font=font_large, fill=0)
        y += offset

    return img

def screen1():
    button0 = Button(
        action=lambda: show_screen(screens[1]),
        image=pihole_image(),
        button_width=WIDTH,
        button_height=HEIGHT,
        button_x=0,
        button_y=0,
    )
    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button0],
    )
    return screen

def screen2():
    button1 = Button(
        text="😪",
        action=lambda: show_screen(screens[2]),
        button_width=120,
        button_height=51,
        button_x=5,
        button_y=5,
    )
    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button1],
        image=pihole_image(),
    )
    return screen

def screen3():
    title = "Pihole Stats Summary"
    d = get_stats_summary()
    button0 = Button(
        action=lambda: show_screen(screens[1]),
        image=data_image(d, title),
        button_width=WIDTH,
        button_height=HEIGHT,
        button_x=0,
        button_y=0,
    )
    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button0],
    )
    return screen

def show_screen(screen):
    global active_screen
    print(f"showing screen {screen}")
    active_screen = screen
    screen.draw(epd)

screens = [
    screen1(),
    screen2(),
    screen3(),
]
if __name__ == '__main__':
    # Register to run when script exits
    #show_pihole_logo()
    #atexit.register(show_pihole_logo)
    #display_image_with_path('pihole_stats_epaper_compact.png')
    #draw_button_screen()
    show_screen(screens[0])
    #screen.draw(epd)
    wait_for_button_press()

    while True:
        time.sleep(1)
