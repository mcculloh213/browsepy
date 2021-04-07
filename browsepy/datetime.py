from datetime import datetime as _dt, timezone as _tz


def now(tz=_tz.utc):
    return _dt.now(tz)


def timestamp(tz=_tz.utc, strfmt='%Y%m%d-%H%M%S'):
    return now(tz).strftime(strfmt)
