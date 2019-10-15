from Ichecker import IChecker
from db_mgr import EasySqlite
import xml.etree.ElementTree as etree
import os
import config
import re
import time
import json
import progressbar
import printer

class PVSStudioChecker(IChecker):
    CONST_TABLE_NAME = "pvs_reports"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db = EasySqlite('rfp.db')
        db.execute("create table if not exists " + self.CONST_TABLE_NAME +
                   "(project text NOT NULL, file text, file_path text, time timestamp default current_timestamp not null, report_path text, log text); ")
    
    def get_name(self)->str:
        return "PVS-Studio"

    def check(self, changed_files)->int:
        # 生成要检查源码文件集合的xml文件
        self.__gen_src_filters(changed_files)
        # 生成检查结果plog格式
        printer.aprint(self.get_name() + '生成plog...')
        # 返回有错误的最小版本号
        return self.__gen_plog()

    def get_result(self, offset, count)->list:
        rev_list = []
        db = EasySqlite('rfp.db')
        for row in db.execute("SELECT * FROM " + self.CONST_TABLE_NAME + " WHERE report_path <> '' LIMIT {0}, {1}".format(offset, count), [], False, False):
            project = row[0]
            file_name = row[1]
            file_path = row[2]
            time = row[3]
            report_path = row[4]
            log = row[5]

            html_file_path = ""
            if not report_path == "":
                if not os.path.exists(report_path): 
                    print("cannot find report file: " + report_path)
                    continue
                report_filename = os.path.splitext(report_path)[0].split("\\")[-1]
                html_file_path = "{0}\\{1}\\index.html".format(config.get_dir_pvs_report(), report_filename)
                # 如果没有网页报告则创建一个
                if not os.path.exists(html_file_path):
                    self.__convert_to_html(report_path)

            rev_list.append({
                  "project": project
                , "file": file_name
                , "time": time
                , "html_path" : html_file_path
                , "report_path": "download\\" + report_path
                , "log": [log]
                })

        return rev_list

    def get_result_total_cnt(self)->int:
        db = EasySqlite('rfp.db')
        return db.execute("select count(rowid) from " + self.CONST_TABLE_NAME, [], False, False)

    # 转换plog成html格式
    def __convert_to_html(self, plog_path)->bool:
        os.system("if not exist {0} mkdir {0}".format(config.get_dir_pvs_report()))
        filename = os.path.splitext(plog_path)[0].split("\\")[-1]
        ret = os.system("PlogConverter.exe {0} -o {1} -t fullHtml -n {2}".format(plog_path
            , config.get_dir_pvs_report()
            , filename))
        if ret != 0:
            return False

        for parent, dirnames, filenames in os.walk(config.get_dir_pvs_report() + "\\" + filename + "\\sources\\",  followlinks=True):
            for file in filenames:
                if file.endswith(".html"):
                    file_path = os.path.join(parent, file)
                    self.__convert_gbk_to_utf8(file_path, parent)

        return  True

    def __gen_src_filters(self, changes):
        os.system("if not exist temp ( mkdir temp ) else ( del /s/q temp )")
        num = 0
        for file_path, logs in changes.items():
            printer.aprint('准备文件:' + file_path)
            xmlRoot = etree.Element('SourceFilesFilters')
            source_files = etree.SubElement(xmlRoot, 'SourceFiles')
            path = etree.SubElement(source_files, 'Path')
            path.text = file_path
            sourcesRoot = etree.SubElement(xmlRoot, 'SourcesRoot')
            sourcesRoot.text = config.get_dir_src()
            logsXml = etree.SubElement(xmlRoot, 'logs')
            for log in logs:
                logXml = etree.SubElement(logsXml, 'log')
                logXml.set('rev', log['rev'])
                logXml.set('author', log['author'])
                logXml.set('msg', log['msg'])

            tree = etree.ElementTree(xmlRoot)
            tree.write("temp/{0}.xml".format(num), encoding='utf-8')
            num += 1
            # 更新进度条用
            progressbar.add(1)

    def __gen_plog(self):
        # 最早一个拥有错误的版本，用来以后检查的起始点
        min_rev_has_error = 9999999
        os.system("if not exist {0} mkdir {0}".format(config.get_dir_pvs_plogs()))
        db = EasySqlite('rfp.db')
        for parent, dirnames, filenames in os.walk("temp",  followlinks=True):
            for file in filenames:
                file_path = os.path.join(parent, file)
                filename = os.path.splitext(file)[0]
                output_file_path = "{0}\\file{1}.plog".format(
                    config.get_dir_pvs_plogs()
                    , filename)

                if os.path.exists(output_file_path):
                    os.remove(output_file_path)

                ret = os.system('pvs-studio_cmd.exe --target "{0}" --output "{1}" --platform "win32" --configuration "Release" -f "{2}"'.format(config.get_dir_sln()
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

                has_error = True
                if ret == 0:
                    has_error = False

                cur_file_min_rev = 9999999
                logs_json = []
                xmlRoot = etree.parse(file_path)
                logsRoot = xmlRoot.find('logs')
                for log in logsRoot.iter('log'):
                    log_json = {"rev": log.attrib["rev"], "author": log.attrib["author"], "msg": log.attrib["msg"]}
                    logs_json.append(log_json)
                    revision = int(log.attrib["rev"])
                    if cur_file_min_rev > revision:
                        cur_file_min_rev = revision

                pathEle = xmlRoot.find('./SourceFiles/Path')
                src_path = pathEle.text

                db.execute("delete from "
                           + self.CONST_TABLE_NAME
                           + " where file_path = ?"
                           , [src_path]
                           , False
                           , True
                    )

                if has_error:
                    plogXmlRoot = etree.parse(output_file_path)
                    analysisLog = plogXmlRoot.find('PVS-Studio_Analysis_Log')
                    project = analysisLog.find('Project').text
                    filename = analysisLog.find('ShortFile').text

                    db.execute("insert into "
                               + self.CONST_TABLE_NAME
                               + " values (?, ?, ?, current_timestamp, ?, ?);", (project, filename, src_path, output_file_path, json.dumps(log_json)), False, True)
                    if min_rev_has_error > cur_file_min_rev:
                        min_rev_has_error = cur_file_min_rev
                    
                    printer.aprint(self.get_name() + '生成 {0} 的网页报告...'.format(src_path))
                    self.__convert_to_html(output_file_path)

                # 更新进度条用
                progressbar.add(1)
                printer.aprint(self.get_name() + '完成文件{0}检查'.format(src_path))

        return min_rev_has_error

    # 为了解决代码源文件是gbk格式，导致显示乱码的问题
    def __convert_gbk_to_utf8(self, file, dir):
        target_file = os.path.join(dir, 'tmp')
        try: 
            with open(file, 'r', encoding='gbk') as f, open(target_file, 'w', encoding='utf-8') as e:
                text = f.read() # for small files, for big use chunks
                e.write(text)

            os.remove(file) # remove old encoding file
            os.rename(target_file, file) # rename new encoding
        except UnicodeDecodeError:
            print('Decode Error')
        except UnicodeEncodeError:
            print('Encode Error')
