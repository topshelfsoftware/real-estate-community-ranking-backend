from io import BytesIO
from typing import Union

import numpy as np
import pandas as pd

from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from . import MODULE_NAME

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def read_excel_sheet(xlsx: Union[str, BytesIO],
                     sheet_name: str,
                     pk: str) -> pd.DataFrame:
    """Read an excel sheet into a pandas DataFrame. Drops all rows where the
    column acting as the primary key is only whitespace or NaN."""
    if isinstance(xlsx, str):
        logger.info(f"Reading sheet {sheet_name} from file {xlsx} into DataFrame")
    elif isinstance(xlsx, BytesIO):
        logger.info(f"Reading sheet {sheet_name} from bytes into DataFrame")
    df = pd.read_excel(xlsx, sheet_name=sheet_name)
    
    logger.info(f"Cleansing the DataFrame")
    # remove leading/trailing whitespace
    df.rename(columns=lambda x: x.strip(), inplace=True)  # headers
    df[pk] = df[pk].str.strip()         # PK column
    
    df[pk].replace(to_replace='', value=np.nan, inplace=True)
    df = df[df[pk].notnull()]  # drop row if PK cell is NaN
    df.set_index(pk, inplace=True)
    logger.debug(df.to_string())
    return df
