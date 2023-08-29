import base64
import io
import numbers

import pandas as pd

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import get_logger

from . import communities
from .enum_needs import Location
from .enum_wants import HasFeature, GolfCourseQuality, TrailsQuality
from .excel import read_excel_sheet
from .helpers import ignore_space_and_case, lists_equal
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import MODULE_NAME
from .communities import (
    PRIMARY_KEY, SHEET_NAME_NEEDS, SHEET_NAME_WANTS, MIN_RATING, MAX_RATING
)
LOCATION_ALLOWED_VALS = [l.value for l in Location]
HAS_FEATURE_ALLOWED_VALS = [hf.value for hf in HasFeature]
GOLF_COURSE_QLTY_ALLOWED_VALS = [
    ignore_space_and_case(gcq.value) for gcq in GolfCourseQuality
]
TRAILS_QLTY_ALLOWED_VALS = [
    ignore_space_and_case(tq.value) for tq in TrailsQuality
]

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")
    
    xlsx_blob_encoded: str = event["xlsx_blob_encoded"]
    logger.info(f"encoded: {xlsx_blob_encoded}")
    
    # decode the base64 encoded blob and read into memory
    xlsx_blob = base64.b64decode(xlsx_blob_encoded)
    logger.info(f"decoded: {xlsx_blob}")
    xls_filelike = io.BytesIO(xlsx_blob)
    df_needs = read_excel_sheet(xls_filelike, SHEET_NAME_NEEDS, PRIMARY_KEY)
    df_wants = read_excel_sheet(xls_filelike, SHEET_NAME_WANTS, PRIMARY_KEY)

    # validate the excel file using assertions
    # invalid conditions will raise an AssertionError
    assert(lists_equal(df_needs.index.values.tolist(), df_wants.index.values.tolist())), \
        f"'{PRIMARY_KEY}' column must be the same for sheet '{SHEET_NAME_NEEDS}' and sheet '{SHEET_NAME_WANTS}'"
    logger.info(f"'{PRIMARY_KEY}' column is the same for sheet '{SHEET_NAME_NEEDS}' and sheet '{SHEET_NAME_WANTS}'")
    
    # homebuyer needs
    hb_needs_data_types = {
        communities.CITY_KEY: { "type_": str },
        communities.LOC_KEY: { "type_": str },
        communities.PRICE_AVG_KEY: { "type_": numbers.Number },
        communities.PRICE_LOW_KEY: { "type_": numbers.Number },
        communities.PRICE_HIGH_KEY: { "type_": numbers.Number },
        communities.HOA_KEY: { "type_": numbers.Number },
        communities.HOME_TOT_KEY: { "type_": numbers.Number },
        communities.HOME_AGE_KEY: { "type_": int },
        # communities.PRES_KEY: { "type_": numbers.Number }  # this column allows multiple data types
        communities.LINK_KEY: { "type_": str, "nan_allowed": True },
    }

    assert(validate_data(communities.HEADERS_NEEDS, df_needs.columns.values)), \
        f"sheet '{SHEET_NAME_NEEDS}' is missing necessary column(s)"
    logger.info(f"sheet '{SHEET_NAME_NEEDS}' contains at least the following columns: {communities.HEADERS_NEEDS}")

    for col,data_types in hb_needs_data_types.items():
        assert(validate_data_types(df_needs[col].values.tolist(), **data_types)), \
            f"sheet '{SHEET_NAME_NEEDS}', column '{col}' data must be of type {str(data_types['type_'])}"
        logger.info(f"sheet '{SHEET_NAME_NEEDS}', column '{col}' data is of type {str(data_types['type_'])}")
    
    for loc in df_needs[communities.LOC_KEY].values.tolist():
        loc_list = loc.split('/')
        assert(validate_data(loc_list, LOCATION_ALLOWED_VALS)), \
            f"sheet '{SHEET_NAME_NEEDS}', column '{communities.LOC_KEY}' does not contain allowed values: {LOCATION_ALLOWED_VALS}"
    logger.info(f"sheet '{SHEET_NAME_NEEDS}', column '{communities.LOC_KEY}' data contains only allowed values: {LOCATION_ALLOWED_VALS}")

    # homebuyer wants
    hb_wants_data_types = {
        communities.N_GOLF_COURSE_KEY: { "type_": numbers.Number },
        # communities.N_CLUBS_KEY: { "type_": numbers.Number }  # this column allows multiple data types
        communities.N_REC_CENTER_KEY: { "type_": numbers.Number },
        communities.GOLF_COURSE_QLTY_KEY: { "type_": str, "nan_allowed": True },
        communities.TRAILS_QLTY_KEY: { "type_": str, "nan_allowed": True },
        communities.FISH_KEY: { "type_": str },
        communities.DOG_PARK_KEY: { "type_": str },
        communities.GATE_KEY: { "type_": str },
        communities.POOL_KEY: { "type_": str },
        communities.WOODWORK_KEY: { "type_": str },
        communities.MTN_VIEW_KEY: { "type_": str },
        communities.SOFTBALL_KEY: { "type_": str },
        communities.ISOLATED_KEY: { "type_": str },
        communities.PICKLEBALL_KEY: { "type_": numbers.Number },
    }

    assert(validate_data(communities.HEADERS_WANTS, df_wants.columns.values)), \
        f"sheet '{SHEET_NAME_WANTS}' is missing necessary column(s)"
    logger.info(f"sheet '{SHEET_NAME_WANTS}' contains at least the following columns: {communities.HEADERS_WANTS}")

    for col,data_types in hb_wants_data_types.items():
        assert(validate_data_types(df_wants[col].values.tolist(), **data_types)), \
            f"sheet '{SHEET_NAME_WANTS}', column '{col}' data must be of type {str(data_types['type_'])}"
        logger.info(f"sheet '{SHEET_NAME_WANTS}', column '{col}' data is of type {str(data_types['type_'])}")

    for val in df_wants[communities.GOLF_COURSE_QLTY_KEY].values.tolist():
        if pd.isna(val):
            continue  # ignore nan values
        val_list = [ignore_space_and_case(val).split('=')[0]]  # grab just the 1st element of the split
        assert(validate_data(val_list, GOLF_COURSE_QLTY_ALLOWED_VALS)), \
            f"sheet '{SHEET_NAME_WANTS}', column '{communities.GOLF_COURSE_QLTY_KEY}' does not contain allowed values: {GOLF_COURSE_QLTY_ALLOWED_VALS}"
    logger.info(f"sheet '{SHEET_NAME_WANTS}', column '{communities.GOLF_COURSE_QLTY_KEY}' data contains only allowed values: {GOLF_COURSE_QLTY_ALLOWED_VALS}")

    for val in df_wants[communities.TRAILS_QLTY_KEY].values.tolist():
        if pd.isna(val):
            continue  # ignore nan values
        val_list = [ignore_space_and_case(val)]
        assert(validate_data(val_list, TRAILS_QLTY_ALLOWED_VALS)), \
            f"sheet '{SHEET_NAME_WANTS}', column '{communities.TRAILS_QLTY_KEY}' does not contain allowed values: {TRAILS_QLTY_ALLOWED_VALS}"
    logger.info(f"sheet '{SHEET_NAME_WANTS}', column '{communities.TRAILS_QLTY_KEY}' data contains only allowed values: {TRAILS_QLTY_ALLOWED_VALS}")

    for val in df_wants[communities.PICKLEBALL_KEY].values.tolist():
        assert(val >= MIN_RATING and val <= MAX_RATING), \
            f"sheet '{SHEET_NAME_WANTS}', column '{communities.PICKLEBALL_KEY}' data is not within allowed range: [{MIN_RATING},{MAX_RATING}]"
    logger.info(f"sheet '{SHEET_NAME_WANTS}', column '{communities.PICKLEBALL_KEY}' data is within allowed range: [{MIN_RATING},{MAX_RATING}]")

    def validate_has_feat_values(col: str):
        """Validate values for columns indicating if the community has a desired feature."""
        for feat in df_wants[col].values.tolist():
            feat_list = ignore_space_and_case(feat).split("&")
            assert(validate_data(feat_list, HAS_FEATURE_ALLOWED_VALS)), \
                f"sheet '{SHEET_NAME_WANTS}', column '{col}' does not contain allowed values: {HAS_FEATURE_ALLOWED_VALS}"
        logger.info(f"sheet '{SHEET_NAME_WANTS}', column '{col}' data contains only allowed values: {HAS_FEATURE_ALLOWED_VALS}")

    has_feat_cols = [
        communities.FISH_KEY,
        communities.DOG_PARK_KEY,
        communities.GATE_KEY,
        # communities.POOL_KEY,  # this column allows additional values
        communities.WOODWORK_KEY,
        communities.MTN_VIEW_KEY,
        communities.SOFTBALL_KEY,
        communities.ISOLATED_KEY
    ]
    for col in has_feat_cols:
        validate_has_feat_values(col)
    
    return event


def validate_data(data: list, allowed_values: list) -> bool:
    """Validates the data contains a subset of the allowed values."""
    return set(data) <= set(allowed_values)


def validate_data_types(data: list, type_: type, nan_allowed: bool = False) -> bool:
    """Validates the data is of a certain type."""
    for d in data:
        if nan_allowed and pd.isna(d):
            continue
        if not isinstance(d, type_):
            return False
    return True
