import hashlib
import time
from datetime import datetime, timedelta, timezone


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


def sha1_file(path, logger=None):
    sha1 = hashlib.sha1()
    with open(path, 'rb', buffering=0) as f:
        while True:
            data = f.read(65536)
            if data:
                sha1.update(data)
                if logger:
                    logger.progress(len(data))
            else:
                return sha1.hexdigest()


def compare_times(a, b, flexible):
    if flexible:
        return a//1000000000 == b//1000000000
    return a == b
