

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
    #("image_names", "light red", "default"),
    #('root', "light gray", "default"),
]

HELP_TEXT = """\
# Keybindings

## Listing

p   previous buffer
n   next buffer
x   remove buffer

### Image

i   inspect image
d   remove image (irreversible!)

### Container

i   inspect container
l   display logs of container
d   remove container (irreversible!)
"""
