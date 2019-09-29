# coding=utf-8
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, send_file, send_from_directory
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
from db_mgr import EasySqlite
import inspect
import ctypes
import config
import main
import printer
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug = True

# turn the flask app into a socketio app
socketio = SocketIO(app)

checker_thread = None
thread_lock = Lock()

message_logs = []

is_checking = False

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

def print_handler(msg):
    socketio.emit('server_log', msg)
    socketio.sleep(0.1)
    if len(message_logs) >= 12:
        message_logs.pop(0)
    message_logs.append(msg)
    

def stop_thread(_thread):
    _async_raise(_thread.ident, SystemExit)

# 后台线程 产生数据，即刻推送至前端
def background_thread():
    global checker_thread
    try:
        db = EasySqlite('rfp.db')
        last_rev = db.execute("SELECT MAX(rev) FROM reports", [], False, False)

        main.do_check(last_rev[0][0], 'head')
    except Exception as ex:
        print(ex)
    with thread_lock:
        checker_thread = None
        socketio.emit('checker_state', 0)

@app.route('/')
def index():
    offset = request.args.get('offset')
    if offset is None:
        offset = 0
    # only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html') + '<script> var offset=' + str(offset) + ' </script>'

@app.route('/download/<path:filename>')
def download(filename):
    file_path = os.path.join(app.root_path, filename)
    directory = os.getcwd()  # 假设在当前目录
    return send_from_directory(directory, filename, as_attachment=True)

@socketio.on('connect')
def on_connect():
    print('Client connected\n')
    if checker_thread is not None:
        socketio.emit('checker_state', 1)
    else:
        socketio.emit('checker_state', 0)

    for log in message_logs:
        socketio.emit('server_log', log)

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected\n')

@socketio.on('stop_check')
def on_stop_check():
    global checker_thread
    if checker_thread is not None:
        printer.aprint('已经停止了自检\n')
        stop_thread(checker_thread)
        checker_thread = None
        socketio.emit('checker_state', 0)
    else:
        printer.aprint('后台并没有正在自检\n')

@socketio.on('start_check')
def on_stop_check():
    global checker_thread
    if checker_thread is None:
        printer.aprint('开始自检\n')
        socketio.emit('checker_state', 1)
        checker_thread = socketio.start_background_task(target=background_thread)
    else:
        printer.aprint('正在自检\n')

@socketio.on('req_revision_info')
def req_revision_info(offset, count):
    # 一页个数最大不超过20个
    if count > 20:
        count = 20

    rev_list = main.get_revisions_list(offset, count)
    total = main.get_report_total_cnt()
    msg = {"offset": offset, "total": main.get_report_total_cnt(), "data": rev_list, "cur_time": time.time()}
    emit('ack_revision_info', msg)

def auto_check():
    with thread_lock:
        global checker_thread
        print(checker_thread)
        if checker_thread is None:
            printer.aprint('开始自检\n')
            socketio.emit('checker_state', 1)
            checker_thread = socketio.start_background_task(target=background_thread)
            print(checker_thread)
        else:
            printer.aprint('正在自检\n')

if __name__ == '__main__':
    printer.set_handler(print_handler)
    scheduler = BackgroundScheduler()
    job = scheduler.get_job("auto_check")
    if job is not None:
        scheduler.remove_job("auto_check")
    job = scheduler.add_job(auto_check, 'cron', hour='9, 12, 15, 18, 21', id="auto_check")
    scheduler.start()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
