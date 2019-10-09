from Ichecker import IChecker
import printer

from pvs_studio import PVSStudioChecker
from cppcheck import CppChecker

checkers = {}

class CheckerMgr:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__register_checker(PVSStudioChecker())
        self.__register_checker(CppChecker())

    def check(self, changed_files):
        global checkers
        for name, checker in checkers.items():
            checker.check(changed_files)
            printer.aprint('{0}检查结束...'.format(checker.get_name()))
    
    def get_checker(self, name)->IChecker:
        if name in checkers:
            return checkers[name]
        return None

    def get_checker_name_list(self)->list:
        name_list = []
        for name in checkers:
            name_list.append(name)
        return name_list

    def __register_checker(self, IChecker):
        global checkers
        checkers[IChecker.get_name()] = IChecker
