# coding=utf-8
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, Response
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
from db_mgr import EasySqlite
from datetime import timedelta
import inspect
import ctypes
import config
import main
import printer
import progressbar
import time
import os
import re
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
app.debug = True

# turn the flask app into a socketio app
socketio = SocketIO(app)

checker_thread = None
thread_lock = Lock()
message_logs = []
is_checking = False
# 当前检查进度
cur_progress = 100
dic_min_error_rev = {}

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

def progressbar_handler(percent):
    global cur_progress
    cur_progress = percent
    socketio.emit('checking_progress', cur_progress)

def stop_thread(_thread):
    _async_raise(_thread.ident, SystemExit)

# 后台线程 产生数据，即刻推送至前端
def background_thread_check():
    global checker_thread, dic_min_error_rev, thread_lock
    try:
        dic_min_error_rev = main.do_auto_check(dic_min_error_rev)
        file = open("./dic_min_error_rev", "w")
        file.write(json.dumps(dic_min_error_rev))
        file.close()
    except Exception as ex:
        printer.errprint(ex)
        printer.errprint("检查意外结束")
    with thread_lock:
        checker_thread = None
        socketio.emit('checker_state', 0)

@app.route('/')
def index():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@app.route('/download/<path:filename>')
def download(filename):
    local_dir = request.args.get('local_dir')
    file_path = os.path.join(app.root_path, filename)

    file_origin = open(file_path, "r")
    content = file_origin.read()
    file_origin.close()

    dir_change = re.compile(re.escape(config.get_dir_src()), re.IGNORECASE)

    return Response(dir_change.sub(re.escape(local_dir), content), content_type='application/x-msdownload')

@socketio.on('connect')
def on_connect():
    global cur_progress, dic_min_error_rev, checker_thread, thread_lock

    print('Client connected\n')
    for log in message_logs:
        socketio.emit('server_log', log)
    checker_state = 0

    with thread_lock:
        if checker_thread is not None:
            checker_state = 1

    checker_list = main.get_checker_name_list()
    progressbar.update(cur_progress)
    data = {'checker_list': checker_list, 'checker_state': checker_state, 'dic_err_revs': dic_min_error_rev}
    emit('ack_init_data', data)

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected\n')

@socketio.on('stop_check')
def on_stop_check():
    global checker_thread, thread_lock
    with thread_lock:
        if checker_thread is not None:
            printer.errprint('客户停止了自检\n')
            stop_thread(checker_thread)
            checker_thread = None
            socketio.emit('checker_state', 0)
            progressbar.update(-100)
        else:
            printer.errprint('后台并没有正在自检\n')

@socketio.on('req_revision_info')
def req_revision_info(checker_name, offset, count, search):
    # 一页个数最大不超过20个
    if count > 20:
        count = 20

    total = main.get_report_total_cnt(checker_name, search)
    emit('ack_report_total', {'offset': offset, 'total': total, 'time': time.time()})
    rev_list = main.get_revisions_list(checker_name, offset, count, search)
    msg = {"offset": offset, "data": rev_list}
    emit('ack_revision_info', msg)

@socketio.on('start_check')
def start_check():
    global thread_lock, checker_thread
    with thread_lock:
        if checker_thread is None:
            printer.aprint('立即检查\n')
            socketio.emit('checker_state', 1)
            checker_thread = socketio.start_background_task(target=background_thread_check)
        else:
            printer.aprint('正在自检\n')

def auto_check():
    global thread_lock, checker_thread
    with thread_lock:
        if checker_thread is None:
            printer.aprint('立即检查\n')
            socketio.emit('checker_state', 1)
            checker_thread = socketio.start_background_task(target=background_thread_check)
        else:
            printer.aprint('正在自检\n')

def load_min_err_rev_dic():
    global dic_min_error_rev
    # 读取上之前检查的没有错误的最小版本号
    if os.path.exists("./dic_min_error_rev"): 
        file = open("./dic_min_error_rev", "r")
        file_content = file.read()
        if file_content != "":
            dic_min_error_rev= json.loads(file_content)
        file.close()

    if len(dic_min_error_rev) == 0:
        checker_list = main.get_checker_name_list()
        for checker_name in checker_list:
            dic_min_error_rev[checker_name] = 0

    for key, value in dic_min_error_rev.items():
        if value == 0:
            dic_min_error_rev[key] = config.get_check_revision_start()

def init():
    printer.set_handler(print_handler)
    progressbar.set_handler(progressbar_handler)
    scheduler = BackgroundScheduler()

    load_min_err_rev_dic()
    
    job = scheduler.get_job("auto_check")
    if job is not None:
        scheduler.remove_job("auto_check")
    # 定时9点， 12点， 15点， 18点， 21点的时候开始检查。
    job = scheduler.add_job(auto_check, 'cron', hour='9, 12, 15, 18, 21', id="auto_check")
    scheduler.start()

if __name__ == '__main__':
    init()
    socketio.run(app, debug=True, host="0.0.0.0", port=5001)
