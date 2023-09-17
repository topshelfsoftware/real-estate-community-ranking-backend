import topshelfsoftware_aws_util
import topshelfsoftware_util
from topshelfsoftware_util.log import add_log_stream
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
MODULE_NAME = "validate_community_data"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
[add_log_stream(logger) for logger in topshelfsoftware_aws_util.get_package_loggers()]
[add_log_stream(logger) for logger in topshelfsoftware_util.get_package_loggers()]
