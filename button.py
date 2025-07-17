#!/usr/bin/env python3
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)
import os

class Button(object):

    def __init__(
        self,
        action,
        button_width,
        button_height,
        button_x,
        button_y,
        text=None,
        image=None,
        refresh_function=None,
        hidden=False,
        show_badge_function=None,
    ):

        self.button_width = button_width
        self.button_height = button_height
        self.button_x = button_x
        self.button_y = button_y

        self.image = image
        self.text = text
        self.action = action
        self.refresh_function = refresh_function
        self.hidden = hidden
        self.show_badge_function = show_badge_function

    def draw(self, screen_image):
        if self.hidden:
            return

        draw = ImageDraw.Draw(screen_image)

        # Draw button rectangle
        draw.rectangle(
            [
                (self.button_x, self.button_y),
                (self.button_x + self.button_width, self.button_y + self.button_height)
            ],
            fill=1,
            outline=0,
        )

        if self.image is not None:
            screen_image.paste(self.image, (0, 0)) # assume full screen button

        if self.text is not None:
            # Add centered label inside button
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    16,
                )
            except:
                font = ImageFont.load_default()

            text_width, text_height = draw.textsize(self.text, font=font)
            text_x = self.button_x + (self.button_width - text_width) // 2
            text_y = self.button_y + (self.button_height - text_height) // 2
            draw.text((text_x, text_y), self.text, font=font, fill=0)

        if self.show_badge_function is not None and self.show_badge_function():
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    24,
                )
            except:
                font = ImageFont.load_default()

            badge_text = "⚫️️"
            text_width, text_height = draw.textsize(badge_text, font=font)
            text_x = self.button_x + (self.button_width - text_width)
            text_y = self.button_y
            draw.text((text_x, text_y), badge_text, font=font, fill=0)


    def check_touch(self, touch_x, touch_y):
        if self.hidden:
            return None

        print("Checking")
        if (
            self.button_x <= touch_x <= self.button_x + self.button_width
            and self.button_y <= touch_y <= self.button_y + self.button_height
        ):
            print("Clicked!")
            return self.action
            if self.action is not None:
                self.action()


    def refresh(self):
        if self.hidden:
            return

        if self.refresh_function is not None:
            self.image = self.refresh_function()
