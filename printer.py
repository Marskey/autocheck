import time
from threading import Lock

_handler = None

_ap_lock = Lock()

def set_handler(handler):
    global _handler
    _handler = handler

def aprint(*msg):
    with _ap_lock:
        str_time = time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))
        if _handler is not None:
            ret_str = ''
            for item in msg:
                ret_str += str(item)
            _handler("<strong>{0}</strong><span>{1}</span>".format(str_time, ret_str))

def errprint(*msg):
    with _ap_lock:
        str_time = time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))
        if _handler is not None:
            ret_str = ''
            for item in msg:
                ret_str += str(item)
            _handler("<strong>{0}</strong><span class='err-log'>{1}</span>".format(str_time, ret_str))

def warnprint(*msg):
    with _ap_lock:
        str_time = time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))
        if _handler is not None:
            ret_str = ''
            for item in msg:
                ret_str += str(item)
            _handler("<strong>{0}</strong><span class='warn-log'>{1}</span>".format(str_time, ret_str))