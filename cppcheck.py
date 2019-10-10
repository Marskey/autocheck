from Ichecker import IChecker
import xml.etree.ElementTree as etree
import os
import config
import re
import time
from db_mgr import EasySqlite
import printer

class CppChecker(IChecker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db = EasySqlite('rfp.db')
        db.execute("create table if not exists cppcheck_reports (rev integer primary key, path text, time timestamp default current_timestamp not null) ")
    
    def get_name(self)->str:
        return "cppcheck"

    def check(self, changed_files)->None:
        self.__gen_src_filters(changed_files)
        printer.aprint(self.get_name() + '生成xml...')
        self.__gen_res()

    def get_result(self, offset, count)->dict:
        rev_list = {} 
        db = EasySqlite('rfp.db')
        for row in db.execute("SELECT * FROM cppcheck_reports left JOIN commit_log using (rev) ORDER BY rev DESC LIMIT {0}, {1}".format(offset, count), [], False, False):
            revision       = row[0]
            xml_path       = row[1]
            str_time       = row[2]
            author         = row[3]
            msg            = row[4]

            report_file_path = ""
            if not xml_path == "":
                if os.path.exists(xml_path): 
                    report_file_path = "{0}\\r{1}\\index.html".format(config.get_dir_cpp_check_report(), revision)
                    if not os.path.exists(report_file_path):
                        revs = []
                        revs.append(revision)
                        self.__convert_to_html(revs)

            rev_list[revision] = {"rev": revision
                , "time": str_time
                , "report_path": report_file_path
                , "plog_path": "download\\" + xml_path
                , "author": author
                , "msg": msg
                }

        return rev_list

    def get_result_total_cnt(self)->int:
        db = EasySqlite('rfp.db')
        return db.execute("select count(rev) from cppcheck_reports", [], False, False)

    # 转换结果成html格式
    def __convert_to_html(self, revisions = [])->bool:
        os.system("if not exist {0} mkdir {0}".format(config.get_dir_cpp_check_report()))
        input_file = ""
        revision_min = 99999999
        revision_max = 0
        for revision in revisions:
            input_file += "{0}\\r{1}.xml".format(config.get_dir_cpp_check_res(), revision) + " "
            revision_min = min(revision_min, int(revision))
            revision_max = max(revision_max, int(revision))

        output_name = "r{0}-r{1}".format(revision_min, revision_max)
        if len(revisions) == 1:
            output_name = "r{0}".format(revision_min)

        ret = os.system("python cppcheck\\htmlreport\\cppcheck-htmlreport --file={0} --report-dir={1}\\{2}".format(input_file
            , config.get_dir_cpp_check_report()
            , output_name
            ))
        if ret != 0:
            return False
        return  True

    def __gen_src_filters(self, changes):
        os.system("if not exist temp ( mkdir temp ) else ( del /s/q temp )")
        for revision, paths in changes.items():
            file = open("temp/r{}.txt".format(revision), "w")
            for relPath in paths:
                ext = os.path.splitext(relPath)[-1]
                if ext == ".h" or ext == ".cpp" or ext == ".hpp":
                    file.write(config.get_dir_src() + relPath)
                    file.write('\n')
            file.close()

    def __gen_res(self):
        res = []
        os.system("if not exist {0} mkdir {0}".format(config.get_dir_cpp_check_res()))
        db = EasySqlite('rfp.db')
        for parent, dirnames, filenames in os.walk("temp",  followlinks=True):
            for file in filenames:
                file_path = os.path.join(parent, file)
                filename = os.path.splitext(file)[0]
                output_file_path = "{0}\\{1}.xml".format(
                    config.get_dir_cpp_check_res()
                    , filename)
                ret = os.system('cppcheck --file-list={0} --language=c++ -q --xml 2>{1}'.format(file_path
                    , output_file_path))

                if ret != 0:
                    output_file_path = ""

                revision = int(filename[1:])
                db.execute("insert or replace into cppcheck_reports values ({0}, '{1}', current_timestamp);".format(revision, output_file_path), [], False, True)
        return res
