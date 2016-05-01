import string
import random

import urwid


characters = string.digits + string.ascii_letters + string.punctuation


def get_random_text(length=32):
    return "".join([random.choice(characters) for _ in range(length)])


def get_random_text_widget(length=32):
    return urwid.Text(get_random_text(length=length))
