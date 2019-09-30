from abc import ABCMeta, abstractmethod

class TinySrcController:
    # __metaclass__ = ABCMeta

    def __init__(self, svn_url, local_path):
        self.svn_url = svn_url
        self.local_path = local_path
        return

    @abstractmethod
    def updateTo(self, revision) -> bool:
        pass

    @abstractmethod
    def get_versions_changed(self, start, end):
        pass

    @abstractmethod
    def get_version_log(self, start, end):
        pass