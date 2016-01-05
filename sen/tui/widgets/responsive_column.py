import logging

import urwid


logger = logging.getLogger(__name__)


class ResponsiveColumns(urwid.Columns):
    """
    Widgets arranged horizontally in columns from left to right
    """

    def column_widths(self, size, focus=False):
        """
        Return a list of column widths.

        0 values in the list mean hide corresponding column completely
        """
        maxcol = size[0]
        self._cache_maxcol = maxcol
        widths = [width for i, (w, (t, width, b)) in enumerate(self.contents)]
        self._cache_column_widths = widths

        return widths
