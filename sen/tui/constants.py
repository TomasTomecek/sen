

MAIN_LIST_FOCUS = "main_list_focus"

STATUS_BG = "#06a"
STATUS_BG_FOCUS = "#08d"

# default color for monochromatic display
# https://urwid.org/manual/displaymodules.html#setting-a-palette
MONO_DEFAULT = None

# name, fg, bg, mono, fg_h, bg_h
PALLETE = [
    (MAIN_LIST_FOCUS, 'default', 'brown', MONO_DEFAULT, "white", "#060"),  # a60
    ('main_list_lg', 'light gray', 'default', MONO_DEFAULT, "g100", "default"),
    ('main_list_dg', 'dark gray', 'default', MONO_DEFAULT, "g78", "default"),
    ('main_list_ddg', 'dark gray', 'default', MONO_DEFAULT, "g56", "default"),
    ('main_list_white', 'white', 'default', MONO_DEFAULT, "white", "default"),
    ('main_list_green', 'dark green', 'default', MONO_DEFAULT, "#0f0", "default"),
    ('main_list_yellow', 'brown', 'default', MONO_DEFAULT, "#ff0", "default"),
    ('main_list_orange', 'light red', 'default', MONO_DEFAULT, "#fa0", "default"),
    ('main_list_red', 'dark red', 'default', MONO_DEFAULT, "#f00", "default"),
    ('image_names', 'light magenta', 'default', MONO_DEFAULT, "#F0F", "default"),
    ('status_box', 'default', 'black', MONO_DEFAULT, "g100", STATUS_BG),
    ('status_box_focus', 'default', 'black', "bold", "white", STATUS_BG_FOCUS),
    ('status', 'default', 'default', MONO_DEFAULT, "default", STATUS_BG),
    ('status_text', 'default', 'default', MONO_DEFAULT, "g100", STATUS_BG),
    ('status_text_green', 'default', 'default', MONO_DEFAULT, "#0f0", STATUS_BG),
    ('status_text_yellow', 'default', 'default', MONO_DEFAULT, "#ff0", STATUS_BG),
    ('status_text_orange', 'default', 'default', MONO_DEFAULT, "#f80", STATUS_BG),
    ('status_text_red', 'default', 'default', MONO_DEFAULT, "#f66", STATUS_BG),
    ('notif_error', "white", 'dark red', "bold", "white", "#f00",),
    ('notif_info', 'white', 'default', "bold", "g100", "default"),
    ('notif_important', 'white', 'default', "bold", "white", "default"),
    ('notif_text_green', 'white', 'default', "bold", "#0f0", "default"),
    ('notif_text_yellow', 'white', 'default', "bold", "#ff0", "default"),
    ('notif_text_orange', 'white', 'default', "bold", "#f80", "default"),
    ('notif_text_red', 'white', 'default', "bold", "#f66", "default"),
    ('tree', 'dark green', 'default', MONO_DEFAULT, "dark green", "default"),

    ('graph_bg', "default", 'default', MONO_DEFAULT, "default", "default"),

    ('graph_lines_cpu', "default", 'default', MONO_DEFAULT, "default", "#d63"),
    ('graph_lines_cpu_tips', "default", 'default', MONO_DEFAULT, "#d63", "default"),
    ('graph_lines_cpu_legend', "default", 'default', MONO_DEFAULT, "#f96", "default"),

    ('graph_lines_mem', "default", 'default', MONO_DEFAULT, "default", "#39f"),
    ('graph_lines_mem_tips', "default", 'default', MONO_DEFAULT, "#39f", "default"),
    ('graph_lines_mem_legend', "default", 'default', MONO_DEFAULT, "#6af", "default"),

    ('graph_lines_blkio_r', "default", 'default', MONO_DEFAULT, "default", "#9b0"),
    ('graph_lines_blkio_r_tips', "default", 'default', MONO_DEFAULT, "#9b0", "default"),
    ('graph_lines_blkio_r_legend', "default", 'default', MONO_DEFAULT, "#cf0", "default"),
    ('graph_lines_blkio_w', "default", 'default', MONO_DEFAULT, "default", "#b90"),
    ('graph_lines_blkio_w_tips', "default", 'default', MONO_DEFAULT, "#b90", "default"),
    ('graph_lines_blkio_w_legend', "default", 'default', MONO_DEFAULT, "#fc0", "default"),

    ('graph_lines_net_r', "default", 'default', MONO_DEFAULT, "default", "#3ca"),
    ('graph_lines_net_r_tips', "default", 'default', MONO_DEFAULT, "#3ca", "default"),
    ('graph_lines_net_r_legend', "default", 'default', MONO_DEFAULT, "#6fc", "default"),
    ('graph_lines_net_w', "default", 'default', MONO_DEFAULT, "default", "#3ac"),
    ('graph_lines_net_w_tips', "default", 'default', MONO_DEFAULT, "#3ac", "default"),
    ('graph_lines_net_w_legend', "default", 'default', MONO_DEFAULT, "#6cf", "default"),
]

STATUS_BAR_REFRESH_SECONDS = 5
CLEAR_NOTIF_BAR_MESSAGE_IN = 5
