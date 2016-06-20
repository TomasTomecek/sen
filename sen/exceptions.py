class NotAvailableAnymore(Exception):
    """
    This object was available but isn't anymore.
    """


class NotifyError(Exception):
    """
    There was an error, we should notify user.
    """


class TerminateApplication(Exception):
    """
    Close application gracefully.
    """
