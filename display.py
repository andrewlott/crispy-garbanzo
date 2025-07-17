from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFont,
    ImageOps
)
from TP_lib import epd2in13_V4, gt1151
from datetime import datetime, timedelta
import atexit
import cairosvg
import os
import threading
import time
from button import Button
from screen import Screen
from data import (
    get_stats_summary,
    get_daily_stats_summary,
    get_status,
    enable_blocking,
    disable_blocking_for_duration,
    update_gravity,
)

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
now = datetime.now()
screen_show_time = now
sleep_time = 0.1 # seconds

def pthread_irq() :
    print("pthread running")
    while flag_t == 1:
        if gt.digital_read(gt.INT) == 0:
            GT_Dev.Touch = 1
        else:
            GT_Dev.Touch = 0
        time.sleep(sleep_time)

    print("thread:exit")

t = threading.Thread(target=pthread_irq)
t.setDaemon(True)
t.start()

touch_actions = []

def check_touch():
    global active_screen
    global touch_actions

    last_x = None
    last_y = None
    print("Checking touch...")
    while True:
        if active_screen is None:
            time.sleep(sleep_time)
            continue

        gt.GT_Scan(GT_Dev, GT_Old)
        if(not GT_Dev.TouchpointFlag):
            time.sleep(sleep_time)
            continue  # No touch detected

        GT_Dev.TouchpointFlag = 0
        x = WIDTH - GT_Dev.Y[0] # flipped
        y = GT_Dev.X[0]

        if (x == WIDTH or x == 0) and (y == HEIGHT or y == 0):
            # Randomly get tap right at the corners, so ignore
            time.sleep(sleep_time)
            continue
        # Optional: avoid duplicate detection
        if GT_Dev.X[0] == last_y and GT_Dev.Y[0] == WIDTH - last_x:
            time.sleep(sleep_time)
            continue

        print(f"Touched at ({x}, {y})")
        action = active_screen.check_touch(x, y)
        if action is not None and action not in touch_actions:
            print(f"Clicked {active_screen.name}")
            touch_actions.append(action)
        last_x = x
        last_y = y
        time.sleep(sleep_time)

t2 = threading.Thread(target=check_touch)
t2.setDaemon(True)
t2.start()

def render():
    global active_screen
    global touch_actions
    print("Rendering...")
    while True:
        if active_screen is None:
            time.sleep(sleep_time)
            continue

        if len(touch_actions) > 0:
            action = touch_actions.pop(0)
            print(f"Touch Action 0 of {len(touch_actions)}, for {active_screen.name}")
            action()

        now = datetime.now()
        if (
                active_screen.refresh_frequency is not None
                and now - active_screen.last_refresh_time >= active_screen.refresh_frequency
        ):
            print("Refreshing...")
            active_screen.refresh()
            active_screen.draw(epd)
            time.sleep(sleep_time)
            continue

        if (
                active_screen.idle_timeout is not None
                and now - screen_show_time >= active_screen.idle_timeout
        ):
            print("Idling...")
            show_screen(screens[0])
            time.sleep(sleep_time)
            continue

        time.sleep(sleep_time)

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
    font_large = ImageFont.truetype("DejaVuSans.ttf", 16)
    font_medium = ImageFont.truetype("DejaVuSans.ttf", 12)
    font_small = ImageFont.truetype("DejaVuSans.ttf", 10)

    draw.text((5, 0), title, font=font_medium, fill=0)
    draw.line((0, 18, WIDTH, 18), fill=0)

    if len(d.keys()) == 0:
        return img

    offset = 20
    y = HEIGHT / len(d.keys())
    x = 5
    longest_key_len = len(
        sorted(d.keys(), key=lambda s: len(s))[-1]
    )
    for key, value in d.items():
        row_name = str(" ".join(key.split("_")).title())
        row_value = value
        font_pixels = 10

        draw.text(
            (x, y),
            f"{row_name}:",
            font=font_large,
            fill=0
        )
        draw.text(
            (x + (longest_key_len * font_pixels), y),
            row_value,
            font=font_large,
            fill=0
        )
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
        text="Daily Stats",
        action=lambda: show_screen(screens[2]), # Daily Stats Screen
        button_width=115,
        button_height=50,
        button_x=5,
        button_y=5,
    )
    button2 = Button(
        text="Status",
        action=lambda: show_screen(screens[3]), # Status
        button_width=115,
        button_height=50,
        button_x=WIDTH - 10 - 115,
        button_y=5,
    )
    button3 = Button(
        text="Disable\nBlocking",
        action=lambda: show_screen(screens[4]), # Disable Blocking
        button_width=115,
        button_height=50,
        button_x=5,
        button_y=60,
    )
    button4 = Button(
        text="Update\nGravity",
        action=lambda: update_gravity(),
        button_width=115,
        button_height=50,
        button_x=WIDTH - 10 - 115,
        button_y=60,
    )
    button5 = Button(
        text="Enable\nBlocking",
        action=lambda: enable_blocking(),
        button_width=115,
        button_height=50,
        button_x=5,
        button_y=60,
        hidden=True,
    )

    def refresh():
        status = get_status()
        if "enabled" in status["active"].lower():
            button3.hidden = False
            button5.hidden = True
        else:
            button5.hidden = False
            button3.hidden = True

        return pihole_image()

    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button1, button2, button3, button4, button5],
        image=pihole_image(),
        idle_timeout=timedelta(seconds=60),
        refresh_function=refresh,
        refresh_frequency=timedelta(seconds=15),

    )
    return screen

def daily_stats_screen():
    title = "Pihole Daily Stats Summary"
    d = get_daily_stats_summary()
    button0 = Button(
        action=lambda: show_screen(screens[1]),
        image=data_image(d, title),
        button_width=WIDTH,
        button_height=HEIGHT,
        button_x=0,
        button_y=0,
        refresh_function=lambda: data_image(get_daily_stats_summary(), title)
    )
    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button0],
        refresh_frequency=timedelta(seconds=15),
        idle_timeout=timedelta(seconds=60),
    )
    return screen

def status_screen():
    title = "Status"
    d = get_status()
    button0 = Button(
        action=lambda: show_screen(screens[1]),
        image=data_image(d, title),
        button_width=WIDTH,
        button_height=HEIGHT,
        button_x=0,
        button_y=0,
        refresh_function=lambda: data_image(get_status(), title)
    )
    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button0],
        refresh_frequency=timedelta(seconds=15),
        idle_timeout=timedelta(seconds=60),
    )
    return screen

def disable_screen():
    title = "Disable Blocking"

    def disable_for(duration=None):
        disable_blocking_for_duration(duration)
        show_screen(screens[1]) # Main menu

    button1 = Button(
        text="30 seconds",
        action=lambda: disable_for(timedelta(seconds=30)),
        button_width=120,
        button_height=51,
        button_x=5,
        button_y=5,
    )
    button2 = Button(
        text="5 minutes",
        action=lambda: disable_for(timedelta(minutes=5)),
        button_width=120,
        button_height=51,
        button_x=WIDTH - 5 - 120,
        button_y=5,
    )
    button3 = Button(
        text="Indefinitely",
        action=lambda: disable_for(None),
        button_width=120,
        button_height=51,
        button_x=5,
        button_y=60,
    )
    button4 = Button(
        text="Back",
        action=lambda: show_screen(screens[1]), # Main menu
        button_width=120,
        button_height=51,
        button_x=WIDTH - 5 - 120,
        button_y=60,
    )
    screen = Screen(
        width=WIDTH,
        height=HEIGHT,
        buttons=[button1, button2, button3, button4],
        image=data_image({}, title)
    )
    return screen

def show_screen(screen):
    global active_screen
    global screen_show_time

    print(f"showing screen {screen.name}")
    active_screen = screen
    screen_show_time = datetime.now()
    screen.reset_refresh_time()
    screen.draw(epd)

screens = [
    screen1(),
    screen2(),
    daily_stats_screen(),
    status_screen(),
    disable_screen(),
]
if __name__ == '__main__':
    # Register to run when script exits
    #show_pihole_logo()
    #atexit.register(show_pihole_logo)
    #display_image_with_path('pihole_stats_epaper_compact.png')
    #draw_button_screen()
    show_screen(screens[0])
    #screen.draw(epd)
    try:
        render()
    except KeyboardInterrupt:
        print("ctrl + c:")
        Flag_t = 0
        epd.sleep()
        time.sleep(2)
        t.join()
        epd.Dev_exit()
        exit()
