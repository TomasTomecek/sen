import urwid


class ContainerInfoGraph(urwid.BarGraph):
    def __init__(self, fg, bg, graph_bg="graph_bg", bar_width=None, val_count=30, max_val=100):
        """
        create a very simple graph

        :param fg: attr for smoothing (fg needs to be set)
        :param bg: attr for bars (bg needs to be set)
        :param graph_bg: attr for graph background
        :param bar_width: int, width of bars
        :param val_count: int, # of initial bars
        :param max_val: int, maximum value
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
        d = []
        for y in range(1, val_count):
            d.append([0])
        self.set_data(d[:], max_val)


