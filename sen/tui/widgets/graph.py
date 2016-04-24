import math
import logging

import urwid


logger = logging.getLogger(__name__)


def find_max(list_of_lists):
    list_of_ints = [x[0] for x in list_of_lists]
    m = max(list_of_ints)
    try:
        return 2 ** int(math.log2(m) + 1)
    except ValueError:
        return 1


class ContainerInfoGraph(urwid.BarGraph):
    def __init__(self, fg, bg, graph_bg="graph_bg", bar_width=None):
        """
        create a very simple graph

        :param fg: attr for smoothing (fg needs to be set)
        :param bg: attr for bars (bg needs to be set)
        :param graph_bg: attr for graph background
        :param bar_width: int, width of bars
        """
        # satt smoothes graph lines
        satt = {(1, 0): fg}

        super().__init__(
            [graph_bg, bg],
            hatt=[fg],
            satt=satt,
        )
        if bar_width is not None:
            # breaks badly when set too high
            self.set_bar_width(bar_width)

    def render(self, size, focus=False):
        data, top, hlines = self._get_data(size)
        maxcol, maxrow = size
        if len(data) < maxcol:
            data += [[0] for x in range(maxcol - len(data))]
            self.set_data(data, top, hlines)
            logger.debug(data)
        return super().render(size, focus)

    def rotate_value(self, val, max_val=None, adaptive_max=False):
        """

        """
        data, _, _ = self.data
        data = data[1:] + [[int(val)]]
        if adaptive_max:
            max_val = find_max(data)

        self.set_data(data, max_val)
        return max_val

    def set_max(self, value):
        data, top, hlines = self.data
        self.set_data(data, value, hlines)

