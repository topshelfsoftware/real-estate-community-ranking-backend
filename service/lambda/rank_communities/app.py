import boto3
from botocore.exceptions import ClientError as BotoClientError
import pandas as pd

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.io import cdtmp
from topshelfsoftware_util.log import add_console_handler, get_logger

from communities import (
    compile_top_communities, filter_communities, rank_communities,
    read_excel_sheet, score_communities
)
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __init__ import MODULE_NAME
s3_client = boto3.client("s3")

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")
add_console_handler(logger)

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")
    hb_needs: dict = event["needs"]
    hb_wants: dict = event["wants"]

    with cdtmp():
        # TODO: download .xlsx file from s3
        xlsx_fn = ""

        # read excel sheets into memory
        df_needs = read_excel_sheet(xlsx_fn, sheet_num=0)
        df_wants = read_excel_sheet(xlsx_fn, sheet_num=1)

    status_code = 200
    body = {"metadata": {}}

    # filter communties by needs
    df_needs = filter_communities(df_needs, hb_needs)
    n_communities_total = len(df_wants.index)
    n_communities_filtered = len(df_needs.index)
    body["metadata"]["n_communities_total"] = n_communities_total
    body["metadata"]["n_communities_filtered"] = n_communities_filtered
    if n_communities_filtered == 0:
        # payload has filtered out all communities so
        # the client (CPU) should modify the request
        status_code = 422
        body["error"] = "Unprocessable Content"
        body["error_msg"] = "All communities have been filtered out leaving none to rank. " \
                            "Modify homebuyer needs in request payload."
        return {
            "statusCode": status_code,
            "body": body
        }

    # score communities by wants
    df_wants = score_communities(df_wants, hb_wants)

    # apply filter and sort scores to rank
    df = pd.merge(df_needs, df_wants, left_index=True, right_index=True)
    df = rank_communities(df)

    # get the top 3 communities (at most)
    body["top_communities"] = compile_top_communities(df, n=3)
    logger.info(fmt_json(body))

    return {
        "statusCode": status_code,
        "body": body
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", dest="event_file", type=str, required=True,
                        help="JSON file containing the Lambda event object")
    parser.add_argument("--out-file", dest="out_file", type=str, required=True,
                        help="JSON file to write the Lambda response body")
    args = parser.parse_args()

    with open(args.event_file, "r") as fp:
        event = json.load(fp)
    resp = lambda_handler(event, None)
    with open(args.out_file, "w") as fp:
        json.dump(resp["body"], fp, indent=4)