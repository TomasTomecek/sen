

MAIN_LIST_FOCUS = "main_list_focus"

# name, fg, bg, mono, fg_h, bg_h
PALLETE = [
    (MAIN_LIST_FOCUS, 'default', 'brown', "default", "white", "#da0"),
    ('main_list_lg', 'light gray', 'default', "default", "g100", "default"),
    ('main_list_dg', 'dark gray', 'default', "default", "g78", "default"),
    ('main_list_ddg', 'dark gray', 'default', "default", "g56", "default"),
    ('main_list_white', 'white', 'default', "default", "white", "default"),
    ('main_list_green', 'dark green', 'default', "default", "#0f0", "default"),
    ('main_list_yellow', 'brown', 'default', "default", "#ff0", "default"),
    ('main_list_orange', 'light red', 'default', "default", "#f60", "default"),
    ('main_list_red', 'dark red', 'default', "default", "#f00", "default"),
    ('image_names', 'light magenta', 'default', "default", "#F0F", "default"),
    ('status_box', 'default', 'black', "default", "default", "default"),
    ('status_box_focus', 'default', 'black', "default", "g100", "default"),
    ('status', 'default', 'default', "default", "default", "black"),
    ('status_text', 'default', 'default', "default", "g56", "black"),
    ('status_text_green', 'default', 'default', "default", "#6d6", "black"),
    ('status_text_yellow', 'default', 'default', "default", "#dd6", "black"),
    ('status_text_orange', 'default', 'default', "default", "#fa0", "black"),
    ('status_text_red', 'default', 'default', "default", "#d66", "black"),
    ('notif_error', "white", 'dark red', "default", "white", "#f00",),
    ('notif_info', 'white', 'default', "default", "white", "default"),
    #("image_names", "light red", "default"),
    #('root', "light gray", "default"),
]

HELP_TEXT = """\
# Keybindings

## Global

N      previous buffer
n      next buffer
x      remove buffer
h, ?   show help

## Image commands in listing

i      inspect image
d      remove image (irreversible!)

## Container commands in listing

i      inspect container
l      display logs of container
f      follow logs of container
d      remove container (irreversible!)
s      stop container
t      start container
p      pause container
u      unpause container
X      kill container
"""
