import os

import topshelfsoftware_aws_util
import topshelfsoftware_util
from topshelfsoftware_util.log import add_log_stream
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
MODULE_NAME = "run_update_community_data"
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
[add_log_stream(logger) for logger in topshelfsoftware_aws_util.get_package_loggers()]
[add_log_stream(logger) for logger in topshelfsoftware_util.get_package_loggers()]
