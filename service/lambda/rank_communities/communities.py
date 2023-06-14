from enum import Enum
import logging
from statistics import fmean
from typing import Any

import numpy as np
import pandas as pd

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import add_console_handler, get_logger

from enum_needs import Filter, Price, Location, Size
from enum_wants import HasFeature, GolfCourseQuality, TrailsQuality
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __init__ import MODULE_NAME
MAX_PREFERENCE = 5
PRIMARY_KEY = "Community Name"
CITY_KEY = "City"
LOC_KEY = "Location"
PRICE_KEY = "Average Single Family Home Price (90 Days)"
HOA_KEY = "HOA/Rec Fee - 2 People Annual Total"
SIZE_KEY = "Size of Community"
HOME_TOT_KEY = "Total Homes in community"
HOME_AGE_KEY = "Average Age of Home"
PRES_KEY = "Preservation Fee"
N_GOLF_COURSE_KEY = "# of Golf Courses"
N_CLUBS_KEY = "# of Clubs Offered"
N_REC_CENTER_KEY = "# of Rec Centers"
GOLF_COURSE_QLTY_KEY = "Golf Course Quality"
TRAILS_QLTY_KEY = "Walking/Biking Trails"
FISH_KEY = "Fishing in Community"
DOG_PARK_KEY = "Dog Park?"
GATE_KEY = "Gated?"
POOL_KEY = "Indoor + Outdoor Pool"
WOODWORK_KEY = "Woodwork Shop?"
MTN_VIEW_KEY = "Nearby Mountain Views?"
SOFTBALL_KEY = "Softball Field?"
SCORE_KEY = "Homebuyer Score"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}", level=logging.INFO)
add_console_handler(logger)

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def read_excel_sheet(xlsx_fn: str, sheet_num: int) -> pd.DataFrame:
    """Read an excel sheet into a pandas DataFrame. Drops all rows where the
    column acting as the primary key is only whitespace or NaN."""
    logger.info(f"Reading sheet number {sheet_num} from '{xlsx_fn}' into DataFrame")
    df = pd.read_excel(xlsx_fn, sheet_name=sheet_num)
    
    logger.info(f"Cleansing the DataFrame")
    # remove leading/trailing whitespace
    df.rename(columns=lambda x: x.strip(), inplace=True)  # headers
    df[PRIMARY_KEY] = df[PRIMARY_KEY].str.strip()         # PK column
    
    df[PRIMARY_KEY].replace(to_replace='', value=np.nan, inplace=True)
    df = df[df[PRIMARY_KEY].notnull()]  # drop row if PK cell is NaN
    df.set_index(PRIMARY_KEY, inplace=True)
    logger.debug(df.to_string())
    return df


def filter_communities(df: pd.DataFrame, hb_needs: dict) -> pd.DataFrame:
    """Filter communities by homebuyer needs."""
    logger.info(f"Filtering communities by homebuyer needs:\n" \
                f"{fmt_json(hb_needs)}")
    
    # parse the inputs
    price_range_lower: str = hb_needs["price_range_lower"]
    price_range_upper: str = hb_needs["price_range_upper"]
    age_of_home: str = hb_needs["age_of_home"]
    location: list = hb_needs["location"]
    size_of_community: list = hb_needs["size_of_community"]

    price_range_lower = 1000*int(''.join(filter(str.isdigit, price_range_lower)))
    if price_range_upper.capitalize() == Price.MAX.value:
        price_range_upper = df[PRICE_KEY].max()
    else:
        price_range_upper = 1000*int(''.join(filter(str.isdigit, price_range_upper)))        
    
    if age_of_home.capitalize() == Filter.DOES_NOT_MATTER.value:
        year_built = 0
    else:
        year_built = int(''.join(filter(str.isdigit, age_of_home)))

    # cluster community sizes
    logger.info(f"Clustering size of communities: {Size.SML}, {Size.MED}, {Size.LRG}")
    df.sort_values(by=HOME_TOT_KEY, inplace=True)
    df = df[df[HOME_TOT_KEY].notnull()]  # remove rows where cells are NaN
    sizes = _cluster_community_sizes(df[HOME_TOT_KEY].values)
    df[SIZE_KEY] = sizes

    # filter by each community attribute
    logger.info("Filtering by each community attribute: Size, Location, Price, & Age")
    df = df[df[SIZE_KEY].isin(size_of_community)]
    df = df[df[LOC_KEY].isin(location)]
    df = df[df[PRICE_KEY].isin(range(price_range_lower, price_range_upper+1))]
    df = df[df[HOME_AGE_KEY] > year_built]
    logger.debug(df.to_string())

    return df


def score_communities(df: pd.DataFrame, hb_wants: dict) -> pd.DataFrame:
    """Score communities by homebuyer wants."""
    logger.info(f"Scoring communities using homebuyer wants:\n" \
                f"{fmt_json(hb_wants)}")
    
    def calc_score(multiplier: float, preference: int):
        """Calculate a score given a multiplier and a homebuyer preference."""
        return multiplier*(preference-1)/(MAX_PREFERENCE-1)

    def score_feature_yes_no(community: str, score: float, feature_present: str, **kwargs) -> float:
        """Score a feature that is either present or not in a community."""
        preference = int(kwargs["preference"])
        if pd.isnull(feature_present):
            new_score = score
        else:
            mult = 1 if HasFeature.YES.value in feature_present else 0
            new_score = score + calc_score(mult, preference)
        logger.debug(f"community: {community:25} | " \
                     f"new_score: {new_score:.2f} | " \
                     f"feature_present: {feature_present:8} | " \
                     f"preference: {preference}")
        return new_score

    def score_quality(community: str, score: float, quality: str, **kwargs) -> float:
        """Score a feature based on its quality rating."""
        preference = int(kwargs["preference"])
        quality_enum: Enum = kwargs["quality_enum"]
        if pd.isnull(quality):
            new_score = score
        else:
            for i,q in enumerate(quality_enum):
                # q is a string option of an Enum so use q.value to get the string repr
                if q.value.replace(" ", "") in quality.replace(" ", "").upper():
                    mult = i/(len(quality_enum)-1)
                    break
            new_score = score + calc_score(mult, preference)
        logger.debug(f"community: {community:25} | " \
                     f"new_score: {new_score:.2f} | " \
                     f"quality: {quality:10} | " \
                     f"preference: {preference}")
        return new_score
    
    def score_number_offerings(community: str, score: float, n_offerings: int, **kwargs) -> float:
        """Score a feature based on its number of offerings."""
        preference = int(kwargs["preference"])
        max_offerings = int(kwargs["max_offerings"])
        if pd.isnull(n_offerings):
            new_score = score
        else:
            mult = n_offerings/max_offerings
            new_score = score + calc_score(mult, preference)
        logger.debug(f"community: {community:25} | " \
                     f"new_score: {new_score:.2f} | " \
                     f"n_offerings: {n_offerings} | " \
                     f"preference: {preference}")
        return new_score

    def apply_score_func(df: pd.DataFrame, scoring_func: Any, feature: str, **kwargs) -> pd.Series:
        """Generic function to apply a supplied scoring function to an entire DataFrame column."""
        logger.info(feature)
        score_series = df.apply(lambda x: scoring_func(x.name, x[SCORE_KEY], x[feature], **kwargs), axis=1)
        return score_series

    # further clean the column data
    df[N_GOLF_COURSE_KEY] = pd.to_numeric(df[N_GOLF_COURSE_KEY], errors="coerce", downcast="integer")
    df[N_CLUBS_KEY] = pd.to_numeric(df[N_CLUBS_KEY].astype(str).str.extract('(\d+)', expand=False),
                                             errors="coerce",
                                             downcast="integer")  # if any cells are NaN, then column gets upcast to float

    community_features = {
        GATE_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["gated"] }
        },
        MTN_VIEW_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["mountain_views"] }
        },
        SOFTBALL_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["softball_field"] }
        },
        FISH_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["fishing"] }
        },
        WOODWORK_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["woodwork_shop"] }
        },
        POOL_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["indoor_pool"] }
        },
        DOG_PARK_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["dog_park"] }
        },
        GOLF_COURSE_QLTY_KEY: {
            "func": score_quality, "kwargs": { "preference": hb_wants["quality_golf_courses"], "quality_enum": GolfCourseQuality } 
        },
        TRAILS_QLTY_KEY: {
            "func": score_quality, "kwargs": { "preference": hb_wants["quality_trails"], "quality_enum": TrailsQuality } 
        },
        N_GOLF_COURSE_KEY: {
            "func": score_number_offerings, "kwargs": { "preference": hb_wants["mult_golf_courses"], "max_offerings": df[N_GOLF_COURSE_KEY].max() } 
        },
        N_CLUBS_KEY: {
            "func": score_number_offerings, "kwargs": { "preference": hb_wants["many_social_clubs"], "max_offerings": df[N_CLUBS_KEY].max() } 
        }
    }
    df[SCORE_KEY] = np.zeros(len(df.index))  # initialize the community scores
    for feature,scoring in community_features.items():
        df[SCORE_KEY] = apply_score_func(df, scoring["func"], feature, **scoring["kwargs"])

    # TODO: add `competitive_pickleball`
    return df


def rank_communities(df: pd.DataFrame) -> pd.DataFrame:
    """Rank communities by highest to lowest score."""
    df.sort_values(by=SCORE_KEY, ascending=False, inplace=True)
    logger.info(df[SCORE_KEY].to_string())
    return df


def compile_top_communities(df: pd.DataFrame, n: int) -> dict:
    """Compile key information for the `n` highest ranked communities."""
    top_communities = {}
    top_df = df.head(n)
    for idx,row in top_df.iterrows():
        top_communities[idx] = {
            "homebuyer_score": row[SCORE_KEY],
            "city": row[CITY_KEY],
            "location": row[LOC_KEY],
            "avg_price": row[PRICE_KEY],
            "avg_age": row[HOME_AGE_KEY],
            # "hoa_fee": row[HOA_KEY],  # there is an HOA column in each sheet that is causing a KeyError after merging sheets
            "preservation_fee": row[PRES_KEY],
            "size": row[SIZE_KEY],
            "n_golf_courses": row[N_GOLF_COURSE_KEY],
            "n_clubs": row[N_CLUBS_KEY],
            "n_rec_center": row[N_REC_CENTER_KEY],
            "golf_course_qlty": row[GOLF_COURSE_QLTY_KEY],
            "trails_qlty": row[TRAILS_QLTY_KEY],
            "fish": row[FISH_KEY],
            "dog_park": row[DOG_PARK_KEY],
            "gated": row[GATE_KEY],
            "indoor_pool": row[POOL_KEY],
            "woodwork": row[WOODWORK_KEY],
            "mtn_view": row[MTN_VIEW_KEY],
            "softball": row[SOFTBALL_KEY],
        }
    return top_communities


def _cluster_community_sizes(data: np.ndarray) -> list:
    """Cluster community sizes into 3 distinct groupings:
    small, medium, and large."""
    sorted_data: np.ndarray = np.sort(data)
    
    # initialize the centroids
    init_centroids = [
        np.min(sorted_data),                    # small
        sorted_data[np.size(sorted_data)//2],   # medium
        np.max(sorted_data)                     # large
    ]
    
    small, medium, large = _cluster_kmeans(sorted_data, init_centroids)
    logger.debug(f"Clustered {Size.SML.value}:{fmt_json(small)}")
    logger.debug(f"Clustered {Size.MED.value}:{fmt_json(medium)}")
    logger.debug(f"Clustered {Size.LRG.value}:{fmt_json(large)}")
    
    sizes = []
    for _ in small:
        sizes.append(Size.SML.value)
    for _ in medium:
        sizes.append(Size.MED.value)
    for _ in large:
        sizes.append(Size.LRG.value)
    return sizes


def _cluster_kmeans(data: np.ndarray, centroids: list) \
                    -> list[list]:
    """Naive k-means clustering algorithm (1-dimension).
    Return the clusters as a list of lists."""
    cluster_assignments_changed = True
    while cluster_assignments_changed:
        cluster_assignments_changed = False
        prev_centroids = centroids.copy()
        clusters = [[], [], []]
        for d in data:
            dist_arr = np.zeros(len(centroids))
            for i,c in enumerate(centroids):
                dist_arr[i] = abs(d - c)
            clusters[np.argmin(dist_arr)].append(d)
        for i,cluster in enumerate(clusters):
            centroids[i] = fmean(cluster)
        for p,c in zip(prev_centroids, centroids):
            if p != c:
                cluster_assignments_changed = True
                break
    return clusters
