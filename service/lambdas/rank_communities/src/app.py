from botocore.exceptions import ClientError as BotoClientError
import pandas as pd

from topshelfsoftware_util.aws import create_boto3_client
from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.io import cdtmp
from topshelfsoftware_util.log import get_logger

from .communities import (
    compile_top_communities, filter_communities,
    rank_communities, score_communities
)
from .excel import read_excel_sheet
from .exceptions import UnprocessableContentError
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import (
    MODULE_NAME, COMMUNITY_DATA_BUCKET_NAME, COMMUNITY_DATA_OBJECT_NAME
)
from .communities import PRIMARY_KEY, SHEET_NAME_NEEDS, SHEET_NAME_WANTS
s3_client = create_boto3_client("s3")

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")
    hb_needs: dict = event["needs"]
    hb_wants: dict = event["wants"]

    with cdtmp():
        if "excel_file" in event:
            xlsx_fn = event["excel_file"]
        else:
            xlsx_fn = COMMUNITY_DATA_OBJECT_NAME
            try:
                logger.info(f"downloading s3 obj {COMMUNITY_DATA_OBJECT_NAME} " \
                            f"from bucket {COMMUNITY_DATA_BUCKET_NAME}")
                s3_client.download_file(COMMUNITY_DATA_BUCKET_NAME,
                                        COMMUNITY_DATA_OBJECT_NAME,
                                        xlsx_fn)
            except BotoClientError as e:
                logger.error(e)
                raise e
        
        # read excel sheets into memory
        df_needs = read_excel_sheet(xlsx_fn, SHEET_NAME_NEEDS, PRIMARY_KEY)
        df_wants = read_excel_sheet(xlsx_fn, SHEET_NAME_WANTS, PRIMARY_KEY)

    response = {
        "email_address": event["email_address"]
    }

    # filter communties by needs
    df_needs = filter_communities(df_needs, hb_needs)
    n_communities_total = len(df_wants.index)
    n_communities_filtered = len(df_needs.index)
    response["n_communities_total"] = n_communities_total
    response["n_communities_filtered"] = n_communities_filtered
    if n_communities_filtered == 0:
        # payload has filtered out all communities so
        # the client (CPU) should modify the request
        err_msg = "All communities have been filtered out leaving none to rank. " \
                  "Modify homebuyer needs in request payload."
        logger.error(err_msg)
        raise UnprocessableContentError(err_msg)

    # score communities by wants
    df_wants = score_communities(df_wants, hb_wants)

    # apply filter and sort scores to rank
    df = pd.merge(df_needs, df_wants, left_index=True, right_index=True)
    df = rank_communities(df)

    # get the top 3 communities (at most)
    response["top_communities"] = compile_top_communities(df, n=3)
    logger.info(fmt_json(response))

    return response
