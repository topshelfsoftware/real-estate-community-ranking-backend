import base64
import os
import sys

import pytest

from topshelfsoftware_util.log import get_logger

from conftest import get_test_excel_files
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __setup__ import LAMBDAS_PATH, TEST_DATA_PATH
MODULE = "validate_community_data"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"test_{MODULE}")

# ----------------------------------------------------------------------------#
#                           --- Lambda Imports ---                            #
# ----------------------------------------------------------------------------#
sys.path.append(os.path.join(LAMBDAS_PATH, MODULE))
from service.lambdas.validate_community_data.src.app import lambda_handler

# ----------------------------------------------------------------------------#
#                                --- TESTS ---                                #
# ----------------------------------------------------------------------------#
@pytest.mark.parametrize("excel_file", get_test_excel_files("v1"))
def test_01_lambda_handler_valid(get_excel_as_encoded_bin):
    event = {
        "xlsx_base64_encoded": get_excel_as_encoded_bin
    }
    resp = lambda_handler(event, None)
    assert(resp is not None)


@pytest.mark.parametrize("excel_file", get_test_excel_files("v0"))
def test_02_lambda_handler_invalid(get_excel_as_encoded_bin):
    event = {
        "xlsx_base64_encoded": get_excel_as_encoded_bin
    }
    with pytest.raises(AssertionError):
        lambda_handler(event, None)


# ----------------------------------------------------------------------------#
#                             --- Fixtures ---                                #
# ----------------------------------------------------------------------------#
@pytest.fixture
def get_excel_as_encoded_bin(excel_file: str) -> bytes:
    """Read an Excel file into binary (base64 encoded)."""
    excel_fp = os.path.join(TEST_DATA_PATH, excel_file)
    logger.info(f"reading Excel file {excel_file} into bytes")
    with open(excel_fp, "rb") as fx:
        blob = fx.read()
    yield base64.encodebytes(blob)
