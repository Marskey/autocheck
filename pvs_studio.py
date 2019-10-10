from Ichecker import IChecker
import xml.etree.ElementTree as etree
import os
import config
import re
import time
from db_mgr import EasySqlite
import printer

class PVSStudioChecker(IChecker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db = EasySqlite('rfp.db')
        db.execute("create table if not exists pvs_reports (rev integer primary key, path text, time timestamp default current_timestamp not null) ")
    
    def get_name(self)->str:
        return "PVS-Studio"

    def check(self, changed_files)->None:
        # 生成要检查源码文件集合的xml文件
        self.__gen_src_filters(changed_files)
        # 生成检查结果plog格式
        printer.aprint(self.get_name() + '生成plog...')
        self.__gen_plog()

    def get_result(self, offset, count)->dict:
        rev_list = {} 
        db = EasySqlite('rfp.db')
        for row in db.execute("SELECT * FROM pvs_reports left JOIN commit_log using (rev) ORDER BY rev DESC LIMIT {0}, {1}".format(offset, count), [], False, False):
            revision       = row[0]
            plog_file_path = row[1]
            str_time       = row[2]
            author         = row[3]
            msg            = row[4]

            report_file_path = ""
            if not plog_file_path == "":
                if os.path.exists(plog_file_path): 
                    report_file_path = "{0}\\r{1}\\index.html".format(config.get_dir_pvs_report(), revision)
                    if not os.path.exists(report_file_path):
                        revs = []
                        revs.append(revision)
                        self.__convert_to_html(revs)

            rev_list[revision] = {"rev": revision
                , "time": str_time
                , "report_path": report_file_path
                , "plog_path": "download\\" + plog_file_path
                , "author": author
                , "msg": msg
                }

        return rev_list

    def get_result_total_cnt(self)->int:
        db = EasySqlite('rfp.db')
        return db.execute("select count(rev) from pvs_reports", [], False, False)

    # 转换plog成html格式
    def __convert_to_html(self, revisions = [])->bool:
        os.system("if not exist {0} mkdir {0}".format(config.get_dir_pvs_report()))
        input_plogs = ""
        revision_min = 99999999
        revision_max = 0
        for revision in revisions:
            input_plogs += "{0}\\r{1}.plog".format(config.get_dir_pvs_plogs(), revision) + " "
            revision_min = min(revision_min, int(revision))
            revision_max = max(revision_max, int(revision))

        output_name = "r{0}-r{1}".format(revision_min, revision_max)
        if len(revisions) == 1:
            output_name = "r{0}".format(revision_min)

        ret = os.system("PlogConverter.exe {0} -o {1} -t fullHtml -n {2}".format(input_plogs
            , config.get_dir_pvs_report()
            , output_name))
        if ret != 0:
            return False
        return  True

    def __gen_src_filters(self, changes):
        os.system("if not exist temp ( mkdir temp ) else ( del /s/q temp )")
        for revision, paths in changes.items():
            xmlRoot = etree.Element('SourceFilesFilters')
            source_files = etree.SubElement(xmlRoot, 'SourceFiles')
            for relPath in paths:
                ext = os.path.splitext(relPath)[-1]
                if ext == ".h" or ext == ".cpp" or ext == ".hpp":
                    path = etree.SubElement(source_files, 'Path')
                    path.text = relPath
            sourcesRoot = etree.SubElement(xmlRoot, 'SourcesRoot')
            sourcesRoot.text = config.get_dir_src()

            data = etree.tostring(xmlRoot).decode('utf-8')
            file = open("temp/r{}.xml".format(revision), "w")
            file.write(data)
            file.close

    def __gen_plog(self):
        res = []
        os.system("if not exist {0} mkdir {0}".format(config.get_dir_pvs_plogs()))
        db = EasySqlite('rfp.db')
        for parent, dirnames, filenames in os.walk("temp",  followlinks=True):
            for file in filenames:
                file_path = os.path.join(parent, file)
                filename = os.path.splitext(file)[0]
                output_file_path = "{0}\\{1}.plog".format(
                    config.get_dir_pvs_plogs()
                    , filename)
                ret = os.system('pvs-studio_cmd.exe --target "{0}" --output "{1}" --configuration "Release" -f "{2}"'.format(config.get_dir_sln()
                    , output_file_path
                    , file_path))

                # if (ret & 1) / 1 == 1:
                #     print("FilesFail")
                # if (ret & 2) / 2 == 1:
                #     print("GeneralExeption")
                # if (ret & 4) / 4 == 1:
                #     print("IncorrectArguments")
                # if (ret & 8) / 8 == 1:
                #     print("FileNotFound")
                # if (ret & 16) / 16 == 1:
                #     print("IncorrectCfg")
                # if (ret & 32) / 32 == 1:
                #     print("InvalidSolution")
                # if (ret & 64) / 64 == 1:
                #     print("IncorrectExtension")
                # if (ret & 128) / 128 == 1:
                #     print("IncorrectLicense")
                # if (ret & 256) / 256 == 1:
                #     print("AnalysisDiff")
                # if (ret & 512) / 512 == 1:
                #     print("SuppressFail")
                # if (ret & 1024) / 1024 == 1:
                #     print("LicenseRenewal")

                if ret == 0:
                    output_file_path = ""

                revision = int(filename[1:])
                db.execute("insert or replace into pvs_reports values ({0}, '{1}', current_timestamp);".format(revision, output_file_path), [], False, True)
        return res
