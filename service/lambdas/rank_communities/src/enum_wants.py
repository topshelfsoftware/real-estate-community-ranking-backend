from enum import Enum


class HasFeature(str, Enum):
    """Community has feature or it does not."""
    NO = "N"
    YES = "Y"


class GolfCourseQuality(str, Enum):
    """Describe the quality of the community golf courses."""
    OK = "OK"
    OK_GOOD = "OK-GOOD"
    GOOD = "GOOD"
    VERY_GOOD = "VERY GOOD"
    GREAT = "GREAT"


class TrailsQuality(str, Enum):
    """Describe the quality of the walking trails in the community."""
    OK = "OK"
    GOOD = "GOOD"
    GREAT = "GREAT"
