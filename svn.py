import subprocess
import xml.etree.ElementTree as etree
import os
from src_controller import TinySrcController

class TinySvn(TinySrcController):
    def __init__(self, svn_url, local_path):
        super().__init__(svn_url, local_path)
        self.url_root = self.__get_url_root()
        return

    def update(self) -> bool:
        ret = os.system("svn update {0}".format(self.local_path))
        if ret == 0:
            print('更新完成')
        print(ret)
        return True

    def get_versions_changed(self, start, end):
        ret = subprocess.check_output('svn log -v -r {0}:{1} "{2}" --xml --incremental'.format(start, end, self.local_path))
        strRet = "<root>" + ret.decode("utf-8") + "</root>"
        root = etree.fromstring(strRet)
        res = {}
        for logentry in root.iter('logentry'):
            revision = logentry.attrib['revision']
            res[revision] = []
            for svnPath in logentry.iter('path'):
                local_fpath = self.__get_local_relative_path(svnPath.text)
                if len(local_fpath) != 0:
                    res[revision].append(local_fpath)
        return res

    def __get_url_root(self):
        ret = subprocess.check_output('svn info "{}" --xml'.format(self.local_path))
        root = etree.fromstring(ret.decode("utf-8"))
        entry = root.find('entry')
        if entry is None:
            print("element 'entry' not found.")
            return ""

        e_repository = entry.find('repository')
        if e_repository is None:
            print("element 'repository' not found.")
            return ""

        e_url_root = e_repository.find('root')
        if e_url_root is None:
            print("element 'root' not found.")
            return ""

        return e_url_root.text

    def __get_local_relative_path(self, changedPath):
        url_path = self.url_root + changedPath
        if url_path.startswith(self.svn_url):
            return url_path[len(self.svn_url):]
        return ""
