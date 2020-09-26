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
import hashlib


class PVSStudioChecker(IChecker):
    CONST_TABLE_NAME = "pvs_reports"
    excludedCodes = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db = EasySqlite('rfp.db')
        db.execute("create table if not exists " + self.CONST_TABLE_NAME +
                   "(project text NOT NULL, file text, file_path text, time timestamp default current_timestamp not null, report_path text, log text); ")
        db.execute("create table if not exists " + self.CONST_TABLE_NAME + "_ignore " +
                   "(rev integer, project text NOT NULL, file text, file_path text, time timestamp default current_timestamp not null, report_path text, log text); ")
        db.execute("CREATE VIRTUAL TABLE if not exists " +
                   self.CONST_TABLE_NAME + "_fts USING fts4(file_path, body);")
        db.execute("create table if not exists " + self.CONST_TABLE_NAME + "_config"
                   "(json_data text);")
        self.get_config()

    def get_name(self) -> str:
        return "PVS-Studio"

    def check(self, changed_files) -> int:
        # 生成要检查源码文件集合的xml文件
        printer.aprint('准备文件中...')
        self.__gen_src_filters(changed_files)
        # 生成检查结果plog格式
        printer.aprint(self.get_name() + '生成plog...')
        # 返回有错误的最小版本号
        return self.__gen_plog()

    def get_result(self, offset, count, search) -> list:
        rev_list = []
        db = EasySqlite('rfp.db')

        sql = "SELECT * FROM " + self.CONST_TABLE_NAME + " LIMIT ?, ?"
        if search != "":
            db_res = db.execute("select file_path from "
                                + self.CONST_TABLE_NAME
                                + "_fts where body like '%{0}%'".format(search), [], False, False)
            condition = '\'' + '\',\''.join(fp[0] for fp in db_res) + '\''
            sql = "SELECT * FROM " + self.CONST_TABLE_NAME + \
                " WHERE file_path in ({0}) LIMIT ?, ?".format(condition)

        for row in db.execute(sql, (offset, count), False, False):
            project = row[0]
            file_name = row[1]
            file_path = row[2]
            time = row[3]
            report_path = row[4]
            log = row[5]

            html_file_path = ""
            if not report_path == "":
                if not os.path.exists(report_path):
                    printer.errprint("cannot find report file: " +
                                     report_path + ", src_file: " + file_path)
                    continue
                report_filename = os.path.splitext(
                    report_path)[0].split("\\")[-1]
                html_file_path = "{0}\\{1}\\index.html".format(
                    config.get_dir_pvs_report(), report_filename)
                # 如果没有网页报告则创建一个
                if not os.path.exists(html_file_path):
                    self.__convert_to_html(report_path)

            rev_list.append({
                "project": project, "file": file_name, "file_path": file_path, "time": time, "html_path": html_file_path, "report_path": "download\\" + report_path, "log": [log]
            })

        return rev_list

    def get_result_total_cnt(self, search) -> int:
        db = EasySqlite('rfp.db')
        if search != "":
            return db.execute("select count(file_path) from "
                              + self.CONST_TABLE_NAME
                              + "_fts where body like '%{0}%'".format(search), [], False, False)[0][0]

        return db.execute("select count(rowid) from " + self.CONST_TABLE_NAME, [], False, False)[0][0]

    def get_config(self) -> str:
        db = EasySqlite('rfp.db')
        res = db.execute("select json_data from " + self.CONST_TABLE_NAME + "_config", [], False, False)
        raw_jason_data = ""
        if len(res) == 0:
            defaultData = '{"excludedCodes":"V001 V104 V106 V108 V122 V126 V201 V202 V203 V2001 V2002 V2003 V2004 V2005 V2006 V2007 V2008 V2009 V2010 V2011 V2012 V2013 V2501 V2502 V2503 V2504 V2505 V2506 V2507 V2508 V2509 V2510 V2511 V2512 V2513 V2514 V2515 V2516 V2517 V2518 V2519 V2520 V2521 V2522 V2523 V2524 V2525 V820 V802 V112 v807"}'
            self.set_config(defaultData)
            raw_jason_data = defaultData
        else:
            raw_jason_data=res[0][0]
        jsonData = json.loads(raw_jason_data)
        self.excludedCodes = jsonData["excludedCodes"].split()
        return raw_jason_data


    def set_config(self, json_data):
        db = EasySqlite('rfp.db')
        db.execute("delete from " + self.CONST_TABLE_NAME + "_config", [], False, True)
        db.execute("insert into " + self.CONST_TABLE_NAME + "_config values(?)", [json_data], False, True)
        self.excludedCodes = json.loads(json_data)["excludedCodes"].split()

    def ignore_report(self, file_path):
        db = EasySqlite('rfp.db')
        row = db.execute("select * from " + self.CONST_TABLE_NAME + " where file_path = ? limit 1", [file_path], False, True)[0]
        #db.execute("delete from " + self.CONST_TABLE_NAME + " where file_path = ?", [file_path], False, True)
        logJsonData = json.loads(row[5])
        db.execute("insert into "
                   + self.CONST_TABLE_NAME + "_ignore "
                   + " values (?, ?, ?, ?, ?, ?, ?);", (int(logJsonData['rev']), row[0], row[1], row[2], row[3], row[4], row[5]), False, True)

    # 转换plog成html格式
    def __convert_to_html(self, plog_path) -> bool:
        os.system("if not exist {0} mkdir {0}".format(
            config.get_dir_pvs_report()))
        filename = os.path.splitext(plog_path)[0].split("\\")[-1]
        cmd = 'PlogConverter.exe {0} -o {1} -t fullHtml -n {2}'.format(
            plog_path, config.get_dir_pvs_report(), filename)
        ret = os.system(cmd)
        if ret != 0:
            return False

        for parent, dirnames, filenames in os.walk(config.get_dir_pvs_report() + "\\" + filename + "\\sources\\",  followlinks=True):
            for file in filenames:
                if file.endswith(".html"):
                    file_path = os.path.join(parent, file)
                    self.__convert_gbk_to_utf8(file_path, parent)

        return True

    def __gen_src_filters(self, changes):
        progressbar.set_total(len(changes))
        os.system("if not exist temp ( mkdir temp ) else ( del /s/q temp )")
        for file_path, logs in changes.items():
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
                if log['msg'] != None:
                    logXml.set('msg', log['msg'])
                else:
                    logXml.set('msg', '')

            tree = etree.ElementTree(xmlRoot)
            tree.write(
                "temp/{0}.xml".format(hashlib.sha1(file_path.encode()).hexdigest()), encoding='utf-8')
            progressbar.add(1)

    def __gen_plog(self):
        # 最早一个拥有错误的版本，用来以后检查的起始点
        min_rev_has_error = 9999999
        os.system("if not exist {0} mkdir {0}".format(
            config.get_dir_pvs_plogs()))
        db = EasySqlite('rfp.db')
        for parent, dirnames, filenames in os.walk("temp",  followlinks=True):
            progressbar.set_total(len(filenames))
            for file in filenames:
                file_path = os.path.join(parent, file)
                filename = os.path.splitext(file)[0]
                output_file_path = "{0}\\{1}.plog".format(
                    config.get_dir_pvs_plogs(), filename)

                if os.path.exists(output_file_path):
                    os.remove(output_file_path)

                xmlRoot = etree.parse(file_path)
                pathEle = xmlRoot.find('./SourceFiles/Path')
                src_path = pathEle.text
                printer.aprint(self.get_name() + '文件{0}检查开始'.format(src_path))

                cmd = 'pvs-studio_cmd.exe --target "{0}" --output "{1}" --platform "x64" --configuration "Release" --sourceFiles "{2}" --settings "{3}" --excludeProjects {4} 2>>pvs_err.log'.format(
                    config.get_dir_sln(), output_file_path, file_path, config.get_path_pvs_setting(), config.get_exclude_projects())
                ret = os.system(cmd)

                if (ret & 1) / 1 == 1:
                    printer.errprint(
                        "PVS-Studio: error (crash) during analysis of some source file(s)")
                if (ret & 2) / 2 == 1:
                    printer.errprint("PVS-Studio: GeneralExeption")
                if (ret & 4) / 4 == 1:
                    printer.errprint(
                        "PVS-Studio: some of the command line arguments passed to the tool were incorrect")
                if (ret & 8) / 8 == 1:
                    printer.errprint(
                        "PVS-Studio: specified project, solution or analyzer settings file were not found")
                if (ret & 16) / 16 == 1:
                    printer.errprint(
                        "PVS-Studio: specified configuration and (or) platform were not found in a solution file")
                if (ret & 32) / 32 == 1:
                    printer.errprint(
                        "PVS-Studio: solution file or project is not supported or contains errors")
                if (ret & 64) / 64 == 1:
                    printer.errprint(
                        "PVS-Studio: incorrect extension of analyzed project or solution")
                if (ret & 128) / 128 == 1:
                    printer.errprint(
                        "PVS-Studio: incorrect or out-of-date analyzer license")
                if (ret & 256) / 256 == 1:
                    has_error = True
                    printer.warnprint(
                        "PVS-Studio: some issues were found in the source code")
                if (ret & 512) / 512 == 1:
                    printer.errprint(
                        "PVS-Studio: some issues were encountered while performing analyzer message suppression")
                if (ret & 1024) / 1024 == 1:
                    printer.errprint(
                        "PVS-Studio: indicates that analyzer license will expire in less than a month")

                if ret == 0:
                    has_error = False
                print("pvs-studio ret: " + str(ret))

                cur_file_min_rev = 9999999
                logs_json = []
                logsRoot = xmlRoot.find('logs')
                for log in logsRoot.iter('log'):
                    log_json = {
                        "rev": log.attrib["rev"], "author": log.attrib["author"], "msg": log.attrib["msg"]
                        }
                    logs_json.append(log_json)
                    revision = int(log.attrib["rev"])
                    if cur_file_min_rev > revision:
                        cur_file_min_rev = revision

                db.execute("delete from "
                           + self.CONST_TABLE_NAME
                           + " where file_path = ?", [src_path], False, True
                           )

                db.execute("delete from " + self.CONST_TABLE_NAME + "_fts where file_path = ?", [src_path], False, True
                           )

                if has_error:
                    plogXmlRoot = etree.parse(output_file_path)
                    analysisLogs = plogXmlRoot.findall('PVS-Studio_Analysis_Log')
                    ignoreCnt = 0
                    for analysisLog in analysisLogs:
                        errCode = analysisLog.find('ErrorCode').text
                        if errCode is None:
                            progressbar.add(1)
                            continue
                        if errCode.lower() in (code.lower() for code in self.excludedCodes):
                            plogXmlRoot.getroot().remove(analysisLog)
                            ignoreCnt = ignoreCnt + 1

                    if len(analysisLogs) == ignoreCnt:
                        os.remove(output_file_path)
                        progressbar.add(1)
                        if min_rev_has_error > cur_file_min_rev:
                            min_rev_has_error = cur_file_min_rev
                        continue

                    plogXmlRoot.write(output_file_path)

                    project = analysisLogs[0].find('Project').text
                    filename = analysisLogs[0].find('ShortFile').text
                    log_str = json.dumps(log_json)

                    db.execute("insert into "
                               + self.CONST_TABLE_NAME
                               + " values (?, ?, ?, current_timestamp, ?, ?);", (project, filename, src_path, output_file_path, log_str), False, True)
                    if min_rev_has_error > cur_file_min_rev:
                        min_rev_has_error = cur_file_min_rev

                    body_str = '{0} {1} {2}'.format(project, filename, log_str)
                    db.execute("insert into "
                               + self.CONST_TABLE_NAME
                               + "_fts values (?, ?);", (src_path, body_str), False, True)

                    printer.aprint(self.get_name() +
                                   '生成 {0} 的网页报告...'.format(src_path))
                    self.__convert_to_html(output_file_path)
                else:
                    min_rev_has_error = cur_file_min_rev

                # 更新进度条用
                progressbar.add(1)
                printer.aprint(self.get_name() + '文件{0}检查结束'.format(src_path))

        return min_rev_has_error

    # 为了解决代码源文件是gbk格式，导致显示乱码的问题
    def __convert_gbk_to_utf8(self, file, dir):
        target_file = os.path.join(dir, 'tmp')
        try:
            with open(file, 'r', encoding='gbk') as f, open(target_file, 'w', encoding='utf-8') as e:
                text = f.read()  # for small files, for big use chunks
                e.write(text)

            os.remove(file)  # remove old encoding file
            os.rename(target_file, file)  # rename new encoding
        except UnicodeDecodeError:
            print('Decode Error')
        except UnicodeEncodeError:
            print('Encode Error')
