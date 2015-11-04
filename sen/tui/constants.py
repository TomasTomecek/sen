

MAIN_LIST_FOCUS = "main_list_focus"

STATUS_BG = "#06a"
STATUS_BG_FOCUS = "#08d"

# name, fg, bg, mono, fg_h, bg_h
PALLETE = [
    (MAIN_LIST_FOCUS, 'default', 'brown', "default", "white", "#060"),  # a60
    ('main_list_lg', 'light gray', 'default', "default", "g100", "default"),
    ('main_list_dg', 'dark gray', 'default', "default", "g78", "default"),
    ('main_list_ddg', 'dark gray', 'default', "default", "g56", "default"),
    ('main_list_white', 'white', 'default', "default", "white", "default"),
    ('main_list_green', 'dark green', 'default', "default", "#0f0", "default"),
    ('main_list_yellow', 'brown', 'default', "default", "#ff0", "default"),
    ('main_list_orange', 'light red', 'default', "default", "#fa0", "default"),
    ('main_list_red', 'dark red', 'default', "default", "#f00", "default"),
    ('image_names', 'light magenta', 'default', "default", "#F0F", "default"),
    ('status_box', 'default', 'black', "default", "g100", STATUS_BG),
    ('status_box_focus', 'default', 'black', "default", "white", STATUS_BG_FOCUS),
    ('status', 'default', 'default', "default", "default", STATUS_BG),
    ('status_text', 'default', 'default', "default", "g100", STATUS_BG),
    ('status_text_green', 'default', 'default', "default", "#0f0", STATUS_BG),
    ('status_text_yellow', 'default', 'default', "default", "#ff0", STATUS_BG),
    ('status_text_orange', 'default', 'default', "default", "#f80", STATUS_BG),
    ('status_text_red', 'default', 'default', "default", "#f66", STATUS_BG),
    ('notif_error', "white", 'dark red', "default", "white", "#f00",),
    ('notif_info', 'white', 'default', "default", "g100", "default"),
    ('notif_important', 'white', 'default', "default", "white", "default"),
    ('notif_text_green', 'white', 'default', "white", "#0f0", "default"),
    ('notif_text_yellow', 'white', 'default', "white", "#ff0", "default"),
    ('notif_text_orange', 'white', 'default', "white", "#f80", "default"),
    ('notif_text_red', 'white', 'default', "white", "#f66", "default"),
]

STATUS_BAR_REFRESH_SECONDS = 5
CLEAR_NOTIF_BAR_MESSAGE_IN = 5

HELP_TEXT = """\
# Keybindings

Since I am a heavy `vim` user, these keybindings are trying to stay close to vim.

## Global

/      search (provide empty query to disable searching)
n      next search occurrence
N      previous search occurrence
f4     filter items in list (provide empty query to clear filtering)
        * in main listing, this is a space-separated list of query strings,
          currently supported filters are:
           * c[ontainer[s]]
           * i[mage[s]]
           * r[unning])
          example query may be: "c" -- show only containers
        * in other buffers, this will only display lines with provided string
ctrl o next buffer
ctrl i previous buffer
x      remove buffer
h, ?   show help

## Movement

gg     go to first item
G      go to last item
j      go one line down
k      go one line up
pg up
ctrl u go 10 lines up
pg down
ctrl d go 10 lines down

## Listing

@      refresh listing

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
r      restart container
p      pause container
u      unpause container
X      kill container
"""
