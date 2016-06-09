

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
    ('tree', 'dark green', 'default', "default", "dark green", "default"),

    ('graph_bg', "default", 'default', "default", "default", "default"),

    ('graph_lines_cpu', "default", 'default', "default", "default", "#d63"),
    ('graph_lines_cpu_tips', "default", 'default', "default", "#d63", "default"),
    ('graph_lines_cpu_legend', "default", 'default', "default", "#f96", "default"),

    ('graph_lines_mem', "default", 'default', "default", "default", "#39f"),
    ('graph_lines_mem_tips', "default", 'default', "default", "#39f", "default"),
    ('graph_lines_mem_legend', "default", 'default', "default", "#6af", "default"),

    ('graph_lines_blkio_r', "default", 'default', "default", "default", "#9b0"),
    ('graph_lines_blkio_r_tips', "default", 'default', "default", "#9b0", "default"),
    ('graph_lines_blkio_r_legend', "default", 'default', "default", "#cf0", "default"),
    ('graph_lines_blkio_w', "default", 'default', "default", "default", "#b90"),
    ('graph_lines_blkio_w_tips', "default", 'default', "default", "#b90", "default"),
    ('graph_lines_blkio_w_legend', "default", 'default', "default", "#fc0", "default"),

    ('graph_lines_net_r', "default", 'default', "default", "default", "#3ca"),
    ('graph_lines_net_r_tips', "default", 'default', "default", "#3ca", "default"),
    ('graph_lines_net_r_legend', "default", 'default', "default", "#6fc", "default"),
    ('graph_lines_net_w', "default", 'default', "default", "default", "#3ac"),
    ('graph_lines_net_w_tips', "default", 'default', "default", "#3ac", "default"),
    ('graph_lines_net_w_legend', "default", 'default', "default", "#6cf", "default"),
]

STATUS_BAR_REFRESH_SECONDS = 5
CLEAR_NOTIF_BAR_MESSAGE_IN = 5
