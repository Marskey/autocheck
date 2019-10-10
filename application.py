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

recheck_rev = 0
recheck_checker = ""

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
        last_rev = db.execute("SELECT MAX(rev) FROM commit_log", [], False, False)[0][0]

        if last_rev is None:
            last_rev = 'base'
        else:
            last_rev += 1

        main.do_check(last_rev, 'head', "")
    except Exception as ex:
        printer.aprint(ex)
        printer.aprint("检查意外结束")
    with thread_lock:
        checker_thread = None
        socketio.emit('checker_state', 0)

def background_thread_recheck():
    global checker_thread
    try:
        main.do_check(recheck_rev, recheck_rev, recheck_checker)
    except Exception as ex:
        printer.aprint(ex)
        printer.aprint("检查意外结束")
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

    msg = main.get_checker_name_list()
    emit('ack_checker_list', msg)

    for log in message_logs:
        socketio.emit('server_log', log)

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected\n')

@socketio.on('stop_check')
def on_stop_check():
    global checker_thread
    if checker_thread is not None:
        printer.aprint('客户停止了自检\n')
        stop_thread(checker_thread)
        checker_thread = None
        socketio.emit('checker_state', 0)
    else:
        printer.aprint('后台并没有正在自检\n')

@socketio.on('start_check')
def on_start_check():
    global checker_thread
    if checker_thread is None:
        printer.aprint('开始自检\n')
        socketio.emit('checker_state', 1)
        checker_thread = socketio.start_background_task(target=background_thread)
    else:
        printer.aprint('正在自检\n')

@socketio.on('req_revision_info')
def req_revision_info(checker_name, offset, count):
    # 一页个数最大不超过20个
    if count > 20:
        count = 20

    total = main.get_report_total_cnt(checker_name)
    rev_list = main.get_revisions_list(checker_name, offset, count)
    msg = {"offset": offset, "total": total, "data": rev_list, "cur_time": time.time()}
    emit('ack_revision_info', msg)

@socketio.on('recheck')
def recheck(rev, checker_name):
    global checker_thread, recheck_rev, recheck_checker
    if checker_thread is None:
        printer.aprint('开始自检\n')
        socketio.emit('checker_state', 1)
        recheck_rev = rev
        recheck_checker = checker_name
        checker_thread = socketio.start_background_task(target=background_thread_recheck)
    else:
        printer.aprint('正在自检\n')

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

    # 如果没有表格创建表格
    db = EasySqlite('rfp.db')
    db.execute("create table if not exists commit_log (rev integer primary key, author text, msg text) ", [], False, False)

    job = scheduler.get_job("auto_check")
    if job is not None:
        scheduler.remove_job("auto_check")
    # 定时9点， 12点， 15点， 18点， 21点的时候开始检查。
    job = scheduler.add_job(auto_check, 'cron', hour='9, 12, 15, 18, 21', id="auto_check")
    scheduler.start()
    socketio.run(app, debug=True, host="0.0.0.0", port=5001)
