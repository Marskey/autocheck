import xml.etree.ElementTree as etree
import os
import ap_config
import re
import time
import sqlite3
from ap_sqlite3 import EasySqlite

class PVSStudioHandler:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def check(self, changed_files):
        # 生成要检查源码文件集合的xml文件
        self.__gen_src_filters(changed_files)
        # 生成检查结果plog格式
        self.__gen_plog()
        # 转换plog成html格式
        # self.__convert_to_html(plogs)

    def convert_to_html(self, revisions = [])->bool:
        os.system("if not exist {0} mkdir {0}".format(ap_config.get_dir_pvs_report()))
        input_plogs = ""
        revision_min = 99999999
        revision_max = 0
        for revision in revisions:
            input_plogs += "{0}\\r{1}.plog".format(ap_config.get_dir_pvs_plogs(), revision) + " "
            revision_min = min(revision_min, int(revision))
            revision_max = max(revision_max, int(revision))

        output_name = "r{0}-r{1}".format(revision_min, revision_max)
        if len(revisions) == 1:
            output_name = "r{0}".format(revision_min)

        ret = os.system("PlogConverter.exe {0} -o {1} -t Html -n {2}".format(input_plogs
            , ap_config.get_dir_pvs_report()
            , output_name))
        if ret != 0:
            return False
        return  True

    def get_revision_list(self)->{}:
        rev_list = {}
        for parent, dirnames, filenames in os.walk(ap_config.get_dir_pvs_plogs(),  followlinks=True):
            for file in filenames:
                revision = int(re.search('r(\d+)', file).group(1))
                file_path = os.path.join(parent, file)
                report_file_path = "{0}\\r{1}.html".format(ap_config.get_dir_pvs_report(), revision)

                if not os.path.exists(report_file_path):
                    revs = []
                    revs.append(revision)
                    self.convert_to_html(revs)
                ltime = time.localtime(os.path.getctime(file_path))
                str_time = time.strftime("%Y-%m-%d %H:%M:%S", ltime)
                rev_list[revision] = { "rev": "r{0}".format(revision), "time": str_time, "report_path": report_file_path }
        return rev_list

    def __gen_src_filters(self, changes):
        os.system("if not exist temp ( mkdir temp ) else ( del /s/q temp )")
        for revision, paths in changes.items():
            xmlRoot = etree.Element('SourceFilesFilters')
            source_files = etree.SubElement(xmlRoot, 'SourceFiles')
            for relPath in paths:
                path = etree.SubElement(source_files, 'Path')
                path.text = relPath
            sourcesRoot = etree.SubElement(xmlRoot, 'SourcesRoot')
            sourcesRoot.text = ap_config.get_dir_src()

            data = etree.tostring(xmlRoot).decode('utf-8')
            file = open("temp/r{}.xml".format(revision), "w")
            file.write(data)

    def __gen_plog(self):
        os.system("if not exist {0} mkdir {0}".format(ap_config.get_dir_pvs_plogs()))
        db = EasySqlite('test.db')
        for parent, dirnames, filenames in os.walk("temp",  followlinks=True):
            for file in filenames:
                file_path = os.path.join(parent, file)
                filename = file[0:file.find(".")]
                output_file_path = "{0}\\{1}.plog".format(
                    ap_config.get_dir_pvs_plogs()
                    , filename)
                ret = os.system('pvs-studio_cmd.exe --target "{0}" --output "{1}" --configuration "Release" -f "{2}"'.format(ap_config.get_dir_sln()
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
                db.execute("insert or replace into reports values ({0}, '{1}', current_timestamp);".format(revision, output_file_path), [], False, True)
