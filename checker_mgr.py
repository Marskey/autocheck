from Ichecker import IChecker
import printer

from pvs_studio import PVSStudioChecker
from cppcheck import CppChecker

checkers = {}

class CheckerMgr:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__register_checker(PVSStudioChecker())
        # self.__register_checker(CppChecker())

    def get_checker(self, name)->IChecker:
        if name in checkers:
            return checkers[name]
        return None

    def get_checker_name_list(self)->list:
        name_list = []
        for name in checkers:
            name_list.append(name)
        return name_list

    def get_checker_config(self, name)->str:
        if name in checkers:
            return checkers[name].get_config()
        return ""

    def set_checker_config(self, name, json_data) -> str:
        if name in checkers:
            checkers[name].set_config(json_data)

    def ignore_report(self, name, file_path):
        if name in checkers:
            checkers[name].ignore_report(file_path)

    def __register_checker(self, IChecker):
        global checkers
        checkers[IChecker.get_name()] = IChecker
