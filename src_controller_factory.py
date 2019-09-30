from Isrc_controller import TinySrcController
from svn import TinySvn
import config

def getSrcController(name, svn_url, local_path)->TinySrcController:
    src_controller = None
    if name == "svn":
        src_controller = TinySvn(svn_url, local_path)
    elif name == "git":
        return None
    return src_controller