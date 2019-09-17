import urllib

DIR_SLN  = "e:/igg/star2/source/star2.sln"
DIR_SRC  = "e:/igg/star2/source/"
URL_SVN  = 'https://10.0.3.3/svn/Star/01. Develop/05. Source/02. Server/Star2'
URL_ROOT = ''
DIR_PVS_PLOGS = 'pvs_plogs'
DIR_PVS_REPORTS = 'static\\pvs_reports'

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