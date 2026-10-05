from .case_e_rules import RULES



"""
Infor business rule set configuration.

Imports the available Case E business rules and defines the rule sets
that can be selected and executed for Infor M3 data.
"""


DEFAULT_RULE_SET = "E"

ALL_RULES_ORDER = ["E"]

RULE_SETS = {
    "E": RULES,
}

