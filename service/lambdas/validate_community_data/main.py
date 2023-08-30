import argparse
import base64

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
    parser.add_argument("--excel-file", dest="excel_file", type=str, required=False,
                        help="Excel file containing community spreadsheet data")
    args = parser.parse_args()

    event = {}
    if args.excel_file is not None:
        # read excel file as binary string
        with open(args.excel_file, "rb") as fx:
            blob = fx.read()
        blob_encoded = base64.encodebytes(blob)
        event["xlsx_blob_encoded"] = blob_encoded

    resp = lambda_handler(event, None)
    logger.debug(f"resp: {resp}")
