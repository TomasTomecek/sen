import string
import random

import urwid


def get_random_text(length=32):
    return "".join([random.choice(string.printable) for _ in range(length)])


def get_random_text_widget(length=32):
    return urwid.Text(get_random_text(length=length))
