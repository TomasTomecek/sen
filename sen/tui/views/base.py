"""
Base class for views, the API.
"""


class View:
    # TODO: views should have API for searching and filtering
    #       there should be a map between widgets and their searchable content
    def refresh(self):
        raise NotImplementedError()
