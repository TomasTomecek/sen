def _ensure_unicode(s):
    try:
        return s.decode("utf-8")
    except AttributeError:
        return s
