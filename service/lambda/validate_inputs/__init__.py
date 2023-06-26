from topshelfsoftware_util import get_package_loggers
from topshelfsoftware_util.log import add_console_handler
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
MODULE_NAME = "validate-inputs"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
loggers = get_package_loggers()
for logger in loggers:
    add_console_handler(logger)
