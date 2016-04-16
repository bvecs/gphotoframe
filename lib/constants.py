import os
import getpass
from os.path import abspath, dirname
from stat import S_IMODE

from xdg.BaseDirectory import *

VERSION = '2.0-a3'
APP_NAME = 'gphotoframe'

SHARED_DATA_DIR = abspath(os.path.join(dirname(__file__), '../share'))
if not os.access(os.path.join(SHARED_DATA_DIR, 'gphotoframe.ui'), os.R_OK):
    SHARED_DATA_DIR = '/usr/share/gphotoframe'
UI_FILE = os.path.join(SHARED_DATA_DIR, 'gphotoframe.ui')

CACHE_DIR = "/tmp/gphotoframe-%s" % getpass.getuser()
DATA_HOME = os.path.join(xdg_data_home, APP_NAME)
CACHE_HOME = os.path.join(xdg_cache_home, APP_NAME)
CONFIG_HOME = os.path.join(xdg_config_home, APP_NAME)
PLUGIN_HOME = os.path.join(DATA_HOME, 'plugins')

for dir in [CACHE_DIR, DATA_HOME, CACHE_HOME, CONFIG_HOME, PLUGIN_HOME]:
    if not os.path.isdir(dir):
        os.makedirs(dir, 0700)
    elif S_IMODE(os.stat(dir).st_mode) != 0700:
        os.chmod(dir, 0700)

def SHARED_DATA_FILE(file):
    return os.path.join(SHARED_DATA_DIR, file)
