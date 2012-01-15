# logging init - this options should be overriden somewhere
LOGGING_CONFIG_FILE = None

# load base configuration for whole app
from medlemssys.settings.base import *

# load some dev env configuration options
from medlemssys.settings.config import *

# try to import some settings from /etc/
import sys
sys.path.insert(0, '/etc/ella')
try:
    from nynorskno_config import *
except ImportError:
    pass
del sys.path[0]

# load any settings for local development
try:
    from medlemssys.settings.local import *
except ImportError:
    pass

if LOGGING_CONFIG_FILE:
    import logging.config
    logging.config.fileConfig(LOGGING_CONFIG_FILE)
