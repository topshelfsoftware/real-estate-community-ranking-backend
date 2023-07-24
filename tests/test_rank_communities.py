import os
import sys

import pytest

from topshelfsoftware_util.log import get_logger

from conftest import get_test_event_files, get_test_excel_files
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __setup__ import LAMBDAS_PATH, TEST_DATA_PATH
MODULE = "rank_communities"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"test_{MODULE}")

# ----------------------------------------------------------------------------#
#                              --- Env Vars ---                               #
# ----------------------------------------------------------------------------#
os.environ["COMMUNITY_DATA_BUCKET_NAME"] = ""
os.environ["COMMUNITY_DATA_OBJECT_NAME"] = ""

# ----------------------------------------------------------------------------#
#                           --- Lambda Imports ---                            #
# ----------------------------------------------------------------------------#
sys.path.append(os.path.join(LAMBDAS_PATH, MODULE))
from service.lambdas.rank_communities.src.app import (
    SHEET_NUM_NEEDS, SHEET_NUM_WANTS, lambda_handler
)
from service.lambdas.rank_communities.src.communities import (
    pd, SCORE_KEY,
    read_excel_sheet, filter_communities, score_communities, rank_communities
)
from service.lambdas.rank_communities.src.exceptions import (
    UnprocessableContentError
)

# ----------------------------------------------------------------------------#
#                                --- TESTS ---                                #
# ----------------------------------------------------------------------------#
@pytest.mark.parametrize("excel_file", get_test_excel_files("v1"))
def test_01_read_excel(excel_file: str):
    sheet_nums = [SHEET_NUM_NEEDS, SHEET_NUM_WANTS]
    excel_fp = os.path.join(TEST_DATA_PATH, excel_file)
    expected_value = 28  # number of communities in the v1 dataset
    for sheet_num in sheet_nums:
        df = read_excel_sheet(excel_fp, sheet_num)
        n_rows = len(df.index)
        assert n_rows == expected_value


@pytest.mark.parametrize("excel_file, sheet_num", zip(get_test_excel_files("v1"), [SHEET_NUM_NEEDS]))
@pytest.mark.parametrize("event_file", get_test_event_files("valid"))
def test_02_filter_communities(event_file, get_excel_as_df, get_event_as_dict):
    hb_needs = get_event_as_dict["needs"]
    df_needs = filter_communities(get_excel_as_df, hb_needs)
    n_rows = len(df_needs.index)
    expected_values = {      # values are the number of communties after filtering
        "01_valid_event.json": 6,
        "02_valid_event.json": 12,
        "03_valid_event.json": 16,
    }
    assert n_rows == expected_values[event_file]


@pytest.mark.parametrize("excel_file, sheet_num", zip(get_test_excel_files("v1"), [SHEET_NUM_WANTS]))
@pytest.mark.parametrize("event_file", get_test_event_files("valid"))
def test_03_score_communities(event_file, get_excel_as_df, get_event_as_dict):
    hb_wants = get_event_as_dict["wants"]
    df_wants = score_communities(get_excel_as_df, hb_wants)
    expected_values = {      # values represent the community score
        "01_valid_event.json": {
            "Cantamia": 3.71875
        },
        "02_valid_event.json": {
            "Johnson Ranch": 0
        },
        "03_valid_event.json": {
            "Trilogy at Vistancia": 5.067308
        }
    }
    expected: dict = expected_values[event_file]
    for pk,expected_score in expected.items():
        score = df_wants[df_wants.index==pk][SCORE_KEY].values[0]
        assert score == pytest.approx(expected_score)


@pytest.mark.parametrize("excel_file, sheet_num", zip(get_test_excel_files("v1"), [SHEET_NUM_WANTS]))
@pytest.mark.parametrize("event_file", get_test_event_files("valid"))
def test_04_rank_communities(get_excel_as_df, get_event_as_dict):
    hb_wants = get_event_as_dict["wants"]
    df_wants = score_communities(get_excel_as_df, hb_wants)
    df_wants = rank_communities(df_wants)
    
    # ranked scores are expected to be sorted in descending order
    prev_score = df_wants[SCORE_KEY].values.max()
    for idx,row in df_wants.iterrows():
        new_score = row[SCORE_KEY]
        assert prev_score >= new_score
        prev_score = new_score


@pytest.mark.parametrize("excel_file", get_test_excel_files("v1"))
@pytest.mark.parametrize("event_file", get_test_event_files("unprocessable"))
def test_05_lambda_handler_unprocessable(excel_file, event_file, get_event_as_dict):
    event = get_event_as_dict
    event["excel_file"] = os.path.join(TEST_DATA_PATH, excel_file)
    try:
        lambda_handler(event, None)
    except UnprocessableContentError as e:
        logger.error(e)


@pytest.mark.parametrize("excel_file", get_test_excel_files("v1"))
@pytest.mark.parametrize("event_file", get_test_event_files("valid"))
def test_06_lambda_handler_local_data(excel_file, event_file, get_event_as_dict):
    event = get_event_as_dict
    event["excel_file"] = os.path.join(TEST_DATA_PATH, excel_file)
    resp = lambda_handler(event, None)
    expected_values = {      # values represent the top communities
        "01_valid_event.json": ["Cantamia", "Trilogy at Vistancia", "Sterling Grove"],
        "02_valid_event.json": ["Johnson Ranch", "Encore at Eastmark", "Springfield Lakes"],
        "03_valid_event.json": ["Trilogy at Vistancia", "Johnson Ranch", "Cantamia"]
    }
    top_communities: dict = resp["top_communities"] 
    for actual,expected in zip(top_communities.keys(),expected_values[event_file]):
        assert actual == expected


# ----------------------------------------------------------------------------#
#                             --- Fixtures ---                                #
# ----------------------------------------------------------------------------#
@pytest.fixture
def get_excel_as_df(excel_file: str, sheet_num: int) -> pd.DataFrame:
    """Read an Excel file sheet into a pandas DataFrame."""
    excel_fp = os.path.join(TEST_DATA_PATH, excel_file)
    logger.info(f"reading Excel file {excel_file} (sheet {sheet_num}) into pandas DataFrame")
    yield read_excel_sheet(excel_fp, sheet_num)
