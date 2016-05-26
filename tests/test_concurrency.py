"""
This suite should test whether sen is capable of running in concurrent high load environment
"""
import random
import threading

from sen.tui.ui import UI
from sen.tui.widgets.list.base import WidgetBase

import urwid

from .utils import get_random_text_widget, get_random_text


class MockUI:
    buffers = []

    def refresh(self):
        pass

    def set_alarm_in(self, *args, **kwargs):
        pass


def test_main_frame():
    lower_bound = 5
    upper_bound = 10
    list_count = 50

    def loop_skeleton(greater_f, less_f, l, l_b, u_b, l_c):
        # we could do while True, but then we need to clean the threads
        for _ in range(100):
            if len(l) > l_c:
                for _ in range(random.randint(l_b, u_b)):
                    greater_f()
            else:
                for _ in range(random.randint(l_b, u_b)):
                    less_f()

    body_widgets = [get_random_text_widget() for _ in range(100)]
    ui = MockUI()
    frame = WidgetBase(ui, urwid.SimpleFocusListWalker(body_widgets))

    def add_and_remove_random():
        widgets = []

        def less_f():
            if random.randint(1, 2) % 2:
                w = get_random_text_widget()
                frame.notify_widget(w)
                widgets.append(w)
            else:
                widgets.append(frame.notify_message(get_random_text()))

        def greater_f():
            w = random.choice(widgets)
            frame.remove_widget(w)
            widgets.remove(w)
        loop_skeleton(greater_f, less_f, widgets, lower_bound, upper_bound, list_count)

    def change_body():

        def less_f():
            body_widgets.insert(0, get_random_text_widget())

        def greater_f():
            body_widgets.remove(random.choice(body_widgets))
        loop_skeleton(greater_f, less_f, body_widgets, lower_bound, upper_bound, list_count)

    nt = threading.Thread(target=add_and_remove_random, daemon=True)
    bt = threading.Thread(target=change_body, daemon=True)
    nt.start()
    bt.start()
    for x in range(50):
        frame.render((70, 70))
    nt.join()
    bt.join()
