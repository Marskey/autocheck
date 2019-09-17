# coding=utf-8
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request
from threading import Lock
import inspect
import ctypes
import ap_config
import ap_main

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(_thread):
    _async_raise(_thread.ident, SystemExit)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug = True

# turn the flask app into a socketio app
socketio = SocketIO(app)

thread = None
thread_lock = Lock()

# 后台线程 产生数据，即刻推送至前端
def background_thread():
    global thread
    # try:
    #     ap_windows.do_auto_build()
    #     ap_print.aprint('构建已完成')
    #     socketio.emit('btn_state', can_package, namespace='/test')
    # except Exception as ex:
    #     ap_print.aprint(str(ex))
    #     ap_print.aprint('构建意外终止，构建失败')
    #     socketio.emit('btn_state', can_package, namespace='/test')
    # with thread_lock:
    #     thread = None

@app.route('/')
def index():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    print('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')


@socketio.on('request_for_response')
def give_response(data):
    global thread

    with thread_lock:
        if data['msg'] == 'start_package':
            if thread is None:
                ap_config.current_pkg_version = data['ver']
                log = data['log']
                if isinstance(log, str):
                    ap_config.current_svn_log = log
                emit('response', {'code': '200', 'msg': '开始构建'})
                thread = socketio.start_background_task(target=background_thread)
            else:
                emit('response', {'code': '200', 'msg': '包已经在打了'})
        elif data['msg'] == 'stop_package':
            if thread is not None:
                emit('response', {'code': '200', 'msg': '已经停止了构建'})
                stop_thread(thread)
                thread = None
            else:
                emit('response', {'code': '200', 'msg': '后台并没有正在构建'})

@socketio.on('req_revision_info')
def req_revision_info(offset):
    rev_list = ap_main.get_revisions_list(offset, 20)
    total = ap_main.get_report_total_cnt()
    msg = {"offset": offset, "total": ap_main.get_report_total_cnt(), "data": rev_list}
    emit('ack_revision_info', msg)

if __name__ == '__main__':
    socketio.run(app, debug=True)
