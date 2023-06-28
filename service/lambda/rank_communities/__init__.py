import os

from topshelfsoftware_util import get_package_loggers
from topshelfsoftware_util.log import add_console_handler
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
MODULE_NAME = "rank-communities"
COMMUNITY_DATA_BUCKET_NAME = os.environ["COMMUNITY_DATA_BUCKET_NAME"]
COMMUNITY_DATA_OBJECT_NAME = os.environ["COMMUNITY_DATA_OBJECT_NAME"]

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
loggers = get_package_loggers()
for logger in loggers:
    add_console_handler(logger)
