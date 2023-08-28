from enum import Enum
from statistics import fmean
from typing import Callable

import numpy as np
import pandas as pd

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import get_logger

from .enum_needs import Filter, Price, Location, Size
from .enum_wants import HasFeature, GolfCourseQuality, TrailsQuality
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import MODULE_NAME
PRIMARY_KEY = "Community Name"

# homebuyer needs
SHEET_NAME_NEEDS = "Sheet1"
CITY_KEY = "City"
LOC_KEY = "Location"
PRICE_AVG_KEY = "Average Single Family Home Price (90 Days)"
PRICE_LOW_KEY = "Price Range Low"
PRICE_HIGH_KEY = "Price Range High"
HOA_KEY = "HOA/Rec Fee - 2 People Annual Total"
HOME_TOT_KEY = "Total Homes in community"
HOME_AGE_KEY = "Average Age of Home"
PRES_KEY = "Preservation Fee"
LINK_KEY = "Links"
HEADERS_NEEDS = [
    CITY_KEY, LOC_KEY, PRICE_AVG_KEY, PRICE_LOW_KEY, PRICE_HIGH_KEY,
    HOA_KEY, HOME_TOT_KEY, HOME_AGE_KEY, PRES_KEY, LINK_KEY
]
SIZE_KEY = "Size of Community"

# homebuyer wants
SHEET_NAME_WANTS = "Sheet2"
MAX_PREFERENCE = MAX_RATING = 5
MIN_PREFERENCE = MIN_RATING = 1
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
ISOLATED_KEY = "Isolated From Rest of City"
PICKLEBALL_KEY = "Competitive Pickleball?"
HEADERS_WANTS = [
    N_GOLF_COURSE_KEY, N_CLUBS_KEY, N_REC_CENTER_KEY, GOLF_COURSE_QLTY_KEY,
    TRAILS_QLTY_KEY, FISH_KEY, DOG_PARK_KEY, GATE_KEY, POOL_KEY, WOODWORK_KEY,
    MTN_VIEW_KEY, SOFTBALL_KEY, ISOLATED_KEY, PICKLEBALL_KEY
]
SCORE_KEY = "Homebuyer Score"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
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
        price_range_upper = df[PRICE_HIGH_KEY].max()
    else:
        price_range_upper = 1000*int(''.join(filter(str.isdigit, price_range_upper)))        
    
    if age_of_home.capitalize() == Filter.DOES_NOT_MATTER.value:
        year_built = 0
    else:
        year_built = int(''.join(filter(str.isdigit, age_of_home)))

    locations = "|".join(location)

    # cluster community sizes
    logger.info(f"Clustering size of communities: {Size.SML}, {Size.MED}, {Size.LRG}")
    df.sort_values(by=HOME_TOT_KEY, inplace=True)
    df = df[df[HOME_TOT_KEY].notnull()]  # remove rows where cells are NaN
    sizes = _cluster_community_sizes(df[HOME_TOT_KEY].values)
    df[SIZE_KEY] = sizes

    # filter by each community attribute
    logger.info("Filtering by each community attribute: Size, Location, Price, & Age")
    df = df[df[SIZE_KEY].isin(size_of_community)]
    df = df[df[LOC_KEY].str.contains(locations)]
    df = df[(df[PRICE_LOW_KEY].le(price_range_lower) & df[PRICE_HIGH_KEY].ge(price_range_lower)) | \
            (df[PRICE_LOW_KEY].le(price_range_upper) & df[PRICE_HIGH_KEY].ge(price_range_upper)) | \
            (df[PRICE_LOW_KEY].isin(range(price_range_lower, price_range_upper+1))) | \
            (df[PRICE_HIGH_KEY].isin(range(price_range_lower, price_range_upper+1)))]
    df = df[df[HOME_AGE_KEY] > year_built]
    logger.debug(df.to_string())

    return df


def score_communities(df: pd.DataFrame, hb_wants: dict) -> pd.DataFrame:
    """Score communities by homebuyer wants."""
    logger.info(f"Scoring communities using homebuyer wants:\n" \
                f"{fmt_json(hb_wants)}")
    
    def calc_score(multiplier: float, preference: int):
        """Calculate a score given a multiplier and a homebuyer preference."""
        return multiplier*(preference-MIN_PREFERENCE)/(MAX_PREFERENCE-MIN_PREFERENCE)

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

    def score_competition(community: str, score: float, competition: int, **kwargs) -> float:
        """Score a feature based on its competition rating."""
        preference = int(kwargs["preference"])
        if pd.isnull(competition):
            new_score = score
        else:
            mult = (competition-MIN_RATING)/(MAX_RATING-MIN_RATING)
            new_score = score + calc_score(mult, preference)
        logger.debug(f"community: {community:25} | " \
                     f"new_score: {new_score:.2f} | " \
                     f"competition: {competition} | " \
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

    def apply_score_func(df: pd.DataFrame, scoring_func: Callable, feature: str, **kwargs) -> pd.Series:
        """Generic function to apply a supplied scoring function to an entire DataFrame column."""
        logger.debug(feature)
        score_series = df.apply(lambda x: scoring_func(x.name, x[SCORE_KEY], x[feature], **kwargs), axis=1)
        return score_series

    # further clean the column data
    df[N_GOLF_COURSE_KEY] = pd.to_numeric(df[N_GOLF_COURSE_KEY], errors="coerce", downcast="integer")
    df[N_CLUBS_KEY] = pd.to_numeric(df[N_CLUBS_KEY].astype(str).str.extract(r'(\d+)', expand=False),
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
        ISOLATED_KEY: {
            "func": score_feature_yes_no, "kwargs": { "preference": hb_wants["isolated_from_city"] }
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
        PICKLEBALL_KEY: {
            "func": score_competition, "kwargs": { "preference": hb_wants["competitive_pickleball"] } 
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

    return df


def rank_communities(df: pd.DataFrame) -> pd.DataFrame:
    """Rank communities by highest to lowest score."""
    df.sort_values(by=SCORE_KEY, ascending=False, inplace=True)
    logger.info(df[SCORE_KEY].to_string())
    return df


def compile_top_communities(df: pd.DataFrame, n: int) -> dict:
    """Compile key information for the `n` highest ranked communities."""
    top_communities = {}
    top_df = df.copy().head(n)
    top_df.fillna("N/A", inplace=True)
    for idx,row in top_df.iterrows():
        top_communities[idx] = {
            "homebuyer_score": row[SCORE_KEY],
            "city": row[CITY_KEY],
            "location": row[LOC_KEY],
            "age_avg": row[HOME_AGE_KEY],
            "price_avg": row[PRICE_AVG_KEY],
            "price_lower": row[PRICE_LOW_KEY],
            "price_upper": row[PRICE_HIGH_KEY],
            "hoa_fee": row[HOA_KEY],
            "preservation_fee": row[PRES_KEY],
            "size": row[SIZE_KEY],
            "link": row[LINK_KEY],
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
            "isolated_from_city": row[ISOLATED_KEY],
            "competitive_pickleball": row[PICKLEBALL_KEY],
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
