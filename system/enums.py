from enum import StrEnum


class SerialNumberAbbreviation(StrEnum):
    """
    Abbreviations are two characters long
    Containing the first two-consonant-character of the model name
    """

    SCHOOL = "SC"
    SEMESTER = "SM"
    COURSE = "CR"
    SESSION = "SS"
    REPORT = "RP"


class CountryCallingCodes(StrEnum):
    """it shall be 3-digit long"""

    IRAN = "098"


class MobileNumberPrefixes(StrEnum):
    IRANCELL = "936"
    HAMRAHE_AVVAL = "919"


class LandlineNumberPrefixes(StrEnum):
    TEHRAN = "21"
