import ap_config
from ap_svn import TinySvnHandler
from ap_pvs_studio import PVSStudioHandler
import os
from ap_sqlite3 import EasySqlite
import re
import time


def do_check(rev_start, rev_end):
    source_controller = TinySvnHandler(
        ap_config.get_url_svn(), ap_config.get_dir_src())
    # 先更新
    source_controller.update()
    # 获取版本变化文件集合
    changed_files = source_controller.get_versions_changed(rev_start, rev_end)

    code_checker = PVSStudioHandler()
    code_checker.check(changed_files)


def get_revisions_list(offset, count):
    code_checker = PVSStudioHandler()

    db_connect = sqlite3.connect('test.db')
    cur = db_connect.cursor()
    rev_list = {}
    for row in cur.execute("select * from reports limit {0}, {1}".format(offset, count)):
        revision = row[0]
        plog_file_path = row[1]
        if not os.path.exists(plog_file_path):
            do_check(revision, revision)

        report_file_path = "{0}\\r{1}.html".format(ap_config.get_dir_pvs_report(), revision)
        if not os.path.exists(report_file_path):
            revs = []
            revs.append(revision)
            code_checker.convert_to_html(revs)
        str_time = row[2]
        rev_list[revision] = {"rev": "r{0}".format(revision), "time": str_time, "report_path": report_file_path}

    db_connect.close()
    rev_list = []
    return rev_list


def get_report_total_cnt():
    db = EasySqlite('test.db')
    db.execute("create table if not exists reports (rev integer primary key, path text, time timestamp default current_timestamp not null) ")
    return db.execute("select count(rev) from reports", [], False, False)