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
    parser.add_argument("--out-file", dest="out_file", type=str, required=True,
                        help="JSON file to write the Lambda response body")
    parser.add_argument("--excel-file", dest="excel_file", type=str, required=False,
                        help="Excel file containing community spreadsheet data")
    args = parser.parse_args()

    with open(args.event_file, "r") as fp:
        event = json.load(fp)
    if args.excel_file is not None:
        event["excel_file"] = args.excel_file
    resp = lambda_handler(event, None)
    logger.debug(f"resp: {resp}")
    with open(args.out_file, "w") as fp:
        json.dump(resp, fp, indent=4)
