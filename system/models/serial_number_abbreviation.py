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
