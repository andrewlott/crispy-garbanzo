#!/usr/bin/env python3
from PIL import Image

class Screen(object):

    def __init__(
        self,
        width,
        height,
        buttons=None,
        image=None,
        refresh_frequency=None,
        refresh_function=None,
    ):
        self.width = width
        self.height = height

        self.image = image
        if self.image is None:
            self.image = Image.new('1', (self.width, self.height), 1)  # 1 = white background

        self.buttons = buttons
        if self.buttons is None:
            self.buttons = []

        self.refresh_frequency = refresh_frequency
        self.refresh_function = refresh_function

    def draw(self, epd):
        #epd.displayPartBaseImage(epd.getbuffer(self.image))

        for button in self.buttons:
            button.draw(self.image)

        # Display the image
        epd.displayPartial(epd.getbuffer(self.image))
        print("Image size:", self.image.size)
        print("Display size:", (epd.height, epd.width))  # some drivers swap w/h

        # Put the display to sleep to save power
        epd.sleep()


    def check_touch(self, x, y):
        for button in self.buttons:
            button.check_touch(x, y)

    def refresh(self):
        for button in self.buttons:
            button.refresh()

        if self.refresh_function is not None:
            self.image = self.refresh_function()
