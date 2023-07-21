import os
import sys

import pytest

from topshelfsoftware_util.log import get_logger

from conftest import get_test_event_files
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __setup__ import LAMBDAS_PATH
MODULE = "validate_inputs"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"test_{MODULE}")

# ----------------------------------------------------------------------------#
#                           --- Lambda Imports ---                            #
# ----------------------------------------------------------------------------#
sys.path.append(os.path.join(LAMBDAS_PATH, MODULE))
from service.lambdas.validate_inputs.src.app import lambda_handler
from service.lambdas.validate_inputs.src.validate import (
    jsonschema, validate_payload
)

# ----------------------------------------------------------------------------#
#                                --- TESTS ---                                #
# ----------------------------------------------------------------------------#
@pytest.mark.parametrize("event_file", get_test_event_files("valid"))
def test_01_validate_payload_valid(get_event_as_dict):
    assert validate_payload(get_event_as_dict) == None


@pytest.mark.parametrize("event_file", get_test_event_files("invalid"))
def test_02_validate_payload_invalid(get_event_as_dict):
    with pytest.raises(jsonschema.ValidationError):
        validate_payload(get_event_as_dict)


@pytest.mark.parametrize("event_file", get_test_event_files("valid"))
def test_03_lambda_handler_valid(get_event_as_dict, get_event_as_str):
    assert lambda_handler(get_event_as_dict, None) == get_event_as_dict
    assert lambda_handler(get_event_as_str, None) == get_event_as_dict


@pytest.mark.parametrize("event_file", get_test_event_files("invalid"))
def test_04_lambda_handler_invalid(get_event_as_dict, get_event_as_str):
    with pytest.raises(jsonschema.ValidationError):
        lambda_handler(get_event_as_dict, None)
    
    with pytest.raises(jsonschema.ValidationError):
        lambda_handler(get_event_as_str, None)
