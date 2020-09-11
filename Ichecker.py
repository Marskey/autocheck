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
    def get_result(self, offset, count, search)->list:
        pass

    @abstractmethod
    def get_result_total_cnt(self, search)->int:
        pass

    @abstractmethod
    def get_config(self)->str:
        pass

    @abstractmethod
    def set_config(self, json_data):
        pass