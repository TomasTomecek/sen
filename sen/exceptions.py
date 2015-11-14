class NotifyError(Exception):
    """
    There was an error, we should notify user.
    """


class TerminateApplication(Exception):
    """
    Close application gracefully.
    """
