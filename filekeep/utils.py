from datetime import datetime, timedelta, timezone
import time

def format_size(size):
    if size >= 1073741824:
        return '{:.1f} GB'.format(size/1073741824)
    elif size >= 1048576:
        return '{:.1f} MB'.format(size/1048576)
    elif size >= 1024:
        return '{:.1f} KB'.format(size/1024)
    elif size == 1:
        return str(size) + ' byte'
    else:
        return str(size) + ' bytes'

def format_timestamp(t):
    dt = datetime.fromtimestamp(t, timezone(timedelta(seconds=-time.altzone)))
    return dt.isoformat()
