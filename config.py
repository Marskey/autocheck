import urllib

DIR_SLN  = "e:\\igg\\star2\source\\star2.sln"
DIR_SRC  = "e:\\igg\\star2\\source"
URL_SVN  = 'https://10.0.3.3/svn/Star/01. Develop/05. Source/02. Server/Star2'

DIR_PVS_PLOGS = 'check_results\\pvs_plogs'
DIR_PVS_REPORTS = 'static\\reports\\pvs_reports'

DIR_CPP_CHECK_RES = 'check_results\\cppcheck_res'
DIR_CPP_CHECK_REPORTS = 'static\\reports\\cppcheck_reports'

REVISION_START = 45263

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

def get_dir_cpp_check_res():
    return DIR_CPP_CHECK_RES

def get_dir_cpp_check_report():
    return DIR_CPP_CHECK_REPORTS

def get_check_revision_start():
    return REVISION_START