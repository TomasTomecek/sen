"""
this package contains widgets which provide a complete view which usually fills whole buffer
"""


class View:
    def refresh(self):
        raise NotImplementedError()
