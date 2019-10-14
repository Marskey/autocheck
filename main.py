from Ichecker import IChecker
from checker_mgr import CheckerMgr
from db_mgr import EasySqlite
import config
import os
import re
import time
import printer
import src_controller_factory
import progressbar

source_controller = src_controller_factory.getSrcController(
    "svn",
    config.get_url_svn(),
    config.get_dir_src())

checker_mgr = CheckerMgr()

def do_auto_check(dic_min_rev):
    dic_min_rev_error = {}
    rev_start = config.get_check_revision_start()
    rev_end   = 'head'
    check_names = get_checker_name_list()

    progressbar.set_total(1)
    # 更新代码
    printer.aprint('更新代码...')
    rev_end = source_controller.updateTo(rev_end)
    progressbar.add(1)
    printer.aprint('已更新代码至r{0}'.format(rev_end))

    for check_name in check_names:
        if check_name in dic_min_rev:
            rev_start = dic_min_rev[check_name]
            min_rev_error = do_check(rev_start, rev_end, check_name)
            dic_min_rev_error[check_name] = min_rev_error
    printer.aprint('全部检查完毕.')
    return dic_min_rev_error

def do_check(rev_start, rev_end, checker_name) -> int:
    global source_controller, checker_mgr
    if checker_name == "":
        return 0

    progressbar.set_total(1)
    # 获取版本变化文件集合
    printer.aprint('获取区间版本r{0}至r{1}的差异文件...'.format(rev_start, rev_end))
    changed_files = source_controller.get_versions_changed(rev_start, rev_end)
    progressbar.add(1)
    printer.aprint('获取区间版本r{0}至r{1}的差异文件完成'.format(rev_start, rev_end))

    # 总数乘以2是因为要先准备一次文件
    progressbar.set_total(len(changed_files) * 2 * len(checker_mgr.get_checker_name_list()))
    # 检查代码
    printer.aprint('检查r{0}至r{1}代码中...'.format(rev_start, rev_end))

    checker = checker_mgr.get_checker(checker_name)
    min_error_rev = checker.check(changed_files)

    printer.aprint('{0}检查结束...'.format(checker.get_name()))
    return min_error_rev

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

def get_checker_name_list():
    return checker_mgr.get_checker_name_list()