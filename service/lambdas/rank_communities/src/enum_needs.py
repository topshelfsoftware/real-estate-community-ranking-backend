from enum import Enum


class Filter(str, Enum):
    """Describe a filter that does not matter to homebuyer."""
    DOES_NOT_MATTER = "Does not matter"


class Price(str, Enum):
    """Describe a maximum price."""
    MAX = "Max"


class Location(str, Enum):
    """Describe a location in the valley."""
    WEST_VALLEY = "West Valley"
    EAST_VALLEY = "East Valley"
    CENTRAL = "Central"


class Size(str, Enum):
    """Describe the size of a community."""
    SML = "Small"
    MED = "Medium"
    LRG = "Large"
