from Ichecker import IChecker
from checker_mgr import CheckerMgr
from db_mgr import EasySqlite
import config
import os
import re
import time
import printer
import src_controller_factory

source_controller = src_controller_factory.getSrcController(
    "svn",
    config.get_url_svn(),
    config.get_dir_src())

checker_mgr = CheckerMgr()

def do_check(rev_start, rev_end, checker_name):
    global source_controller, checker_mgr

    # 获取版本变化文件集合
    printer.aprint('获取区间版本差异...')
    changed_files = source_controller.get_versions_changed(rev_start, rev_end)
    print(changed_files)

    # 更新代码
    for revision, values in changed_files.items():
        printer.aprint('更新r{0}代码...'.format(revision))
        source_controller.updateTo(revision)

        #检查代码
        printer.aprint('检查r{0}代码中...'.format(revision))
        if checker_name == "":
            checker_mgr.check(changed_files)
        else:
            checker = checker_mgr.get_checker(checker_name)
            checker.check(changed_files)
        printer.aprint('检查r{0}代码结束'.format(revision))
        save_commit_log(revision, revision)

    printer.aprint('更新代码至最新.')
    source_controller.updateTo('head')
    printer.aprint('全部检查完毕.')

def get_revisions_list(checker_name, offset, count):
    if checker_mgr.get_checker(checker_name) is None:
        printer.aprint('找不到该检查机：{0}'.format(checker_name))
        return {}

    code_checker = checker_mgr.get_checker(checker_name)
    rev_list = code_checker.get_result(offset, count)
    return rev_list

def get_report_total_cnt(checker_name):
    code_checker = checker_mgr.get_checker(checker_name)
    if code_checker is None:
        return 0
    return code_checker.get_result_total_cnt()

def save_commit_log(rev_start, rev_end):
    global source_controller
    res = source_controller.get_version_log(rev_start, rev_end)
    db = EasySqlite('rfp.db')
    for revision, values in res.items():
        db.execute("insert or replace into commit_log values ({0}, '{1}', '{2}');".format(
            revision, values['author'], values['msg']), [], False, True)

def get_checker_name_list():
    return checker_mgr.get_checker_name_list()
