"""
Lists/Groups the available rules for INFOR. 

"""

def rule_e_01_completeness(record):
    return record


def rule_e_02_referential_integrity(record):
    return record


def rule_e_03_validity_windows(record):
    return record


def rule_e_04_stalled_transactions(record):
    return record


def rule_e_05_probable_duplicate_masters(record):
    return record


def rule_e_06_consequence_ranking(record):
    return record


def rule_e_07_trend_over_time(record):
    return record


RULES = [
    rule_e_01_completeness,
    rule_e_02_referential_integrity,
    rule_e_03_validity_windows,
    rule_e_04_stalled_transactions,
    rule_e_05_probable_duplicate_masters,
    rule_e_06_consequence_ranking,
    rule_e_07_trend_over_time,
]