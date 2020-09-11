import urllib
from db_mgr import EasySqlite

DIR_SLN  = "E:\\IGG\\COLX\\src\\Server\\Develop\\Project\\COLX.sln"
DIR_SRC  = "E:\\IGG\\COLX\\src\\Server\\Develop\\Project"
URL_SVN  = "https://10.0.3.3/svn/colx/Server/Develop/Project"

DIR_PVS_PLOGS = 'check_results\\pvs_plogs'
DIR_PVS_REPORTS = 'static\\reports\\pvs_reports'
PATH_PVS_SETTING = 'setting\\pvs_studio\\Settings.xml'

DIR_CPP_CHECK_RES = 'check_results\\cppcheck_res'
DIR_CPP_CHECK_REPORTS = 'static\\reports\\cppcheck_reports'

REVISION_START = 3837

def get_url_svn():
    return URL_SVN

def get_dir_sln():
    return DIR_SLN

def get_dir_src():
    return DIR_SRC

def get_dir_pvs_plogs():
    return DIR_PVS_PLOGS

def get_dir_pvs_report():
    return DIR_PVS_REPORTS

def get_path_pvs_setting():
    return PATH_PVS_SETTING

def get_dir_cpp_check_res():
    return DIR_CPP_CHECK_RES

def get_dir_cpp_check_report():
    return DIR_CPP_CHECK_REPORTS

def get_check_revision_start():
    return REVISION_START

def get_exclude_projects():
    excludeProject = (
    "libProto"
    , "libThirdParty"
    , "CsvCheck"
    , "RobotClient"
    )
    return ";".join(excludeProject)
