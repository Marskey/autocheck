from abc import ABCMeta, abstractmethod

class IChecker:
    lists = []
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_name(self)->str:
        pass

    @abstractmethod
    def check(self, changed_files)->int:
        pass

    @abstractmethod
    def get_result(self, offset, count)->list:
        pass

    @abstractmethod
    def get_result_total_cnt(self)->int:
        pass