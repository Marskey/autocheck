_handler = None
_total = 0
_cur   = 0

def set_handler(handler):
    global _handler
    _handler = handler

def set_total(total):
    global _total, _cur
    _total = total
    _cur = 0
    update(_cur, _total)

def add(cnt):
    global _total, _cur
    _cur += cnt
    update(_cur, _total)

def update(cur, total):
    if _handler is not None:
        _handler(cur, total)
