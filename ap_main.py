import ap_config
from ap_svn import TinySvnHandler
from ap_pvs_studio import PVSStudioHandler
import os
from ap_sqlite3 import EasySqlite
import re
import time
import ap_print


def do_check(rev_start, rev_end):
    source_controller = TinySvnHandler(
        ap_config.get_url_svn(), ap_config.get_dir_src())
    # 先更新
    ap_print.aprint('更新代码...')
    source_controller.update()
    # 获取版本变化文件集合
    ap_print.aprint('获取版本差异...')
    changed_files = source_controller.get_versions_changed(rev_start, rev_end)

    ap_print.aprint('PVS-Studio 检查中...')
    code_checker = PVSStudioHandler()
    code_checker.check(changed_files)
    ap_print.aprint('PVS-Studio 检查结束')


def get_revisions_list(offset, count):
    code_checker = PVSStudioHandler()

    db = EasySqlite('rfp.db')
    rev_list = {}
    for row in db.execute("SELECT * FROM reports ORDER BY rev DESC LIMIT {0}, {1}".format(offset, count), [], False, False):
        revision       = row[0]
        plog_file_path = row[1]
        str_time       = row[2]

        report_file_path = ""
        if not plog_file_path == "":
            if not os.path.exists(plog_file_path): 
                do_check(revision, revision)

            # report_file_path = "{0}\\r{1}.html".format(ap_config.get_dir_pvs_report(), revision)
            report_file_path = "{0}\\r{1}\\index.html".format(ap_config.get_dir_pvs_report(), revision)
            if not os.path.exists(report_file_path):
                revs = []
                revs.append(revision)
                code_checker.convert_to_html(revs)

        rev_list[revision] = {"rev": "r{0}".format(revision), "time": str_time, "report_path": report_file_path}

    return rev_list

def get_report_total_cnt():
    db = EasySqlite('rfp.db')
    db.execute("create table if not exists reports (rev integer primary key, path text, time timestamp default current_timestamp not null) ")
    return db.execute("select count(rev) from reports", [], False, False)
