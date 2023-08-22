import argparse
import json

from topshelfsoftware_util.log import get_logger

from src.app import lambda_handler
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from src.__init__ import MODULE_NAME

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", dest="event_file", type=str, required=True,
                        help="JSON file containing the Lambda event object")
    args = parser.parse_args()

    with open(args.event_file, "r") as fp:
        event = json.load(fp)
    resp = lambda_handler(event, None)
    logger.debug(f"resp: {resp}")