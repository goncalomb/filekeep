import sys

class BasicLogger:
    def __init__(self, total):
        pass
    def progress(self, value):
        pass
    def print(self, obj):
        print(obj, file=sys.stderr)
    def error(self, obj):
        print(obj, file=sys.stderr)

class LoggerWithProgress:
    def __init__(self, total):
        self.total = total
        self.value = 0
        self.throttle = 0

    def progress(self, value):
        self.value += value
        if self.total and (self.throttle%500 == 0 or self.value == self.total):
            p = self.value*100/self.total
            print("\r\033[K  " + "{0:.2f}".format(p) + "% (" + str(self.value) + "/" + str(self.total) + ")", end="\r", file=sys.stderr)
            if self.value == self.total:
                print(file=sys.stderr)
        self.throttle += 1

    def print(self, obj):
        print("\r\033[K" + str(obj), file=sys.stderr)

    def error(self, obj):
        print("\r\033[K\033[93m" + str(obj) + "\033[0m", file=sys.stderr)

def create(total):
    if sys.stderr.isatty():
        return LoggerWithProgress(total)
    else:
        return BasicLogger(total)
