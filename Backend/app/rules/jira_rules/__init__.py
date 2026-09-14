from rules.jira_rules import rule_a
from rules.jira_rules import rule_b
from rules.jira_rules import rule_c
from rules.jira_rules import rule_d
from rules.jira_rules import rule_f
from rules.jira_rules import rule_g

DEFAULT_RULE_SET = "ALL"

ALL_RULE_ORDER = ["A", "B", "C", "D", "F", "G"]

RULE_SETS = {
    "A": rule_a.RULES,
    "B": rule_b.RULES,
    "C": rule_c.RULES,
    "D": rule_d.RULES,
    "F": rule_f.RULES,
    "G": rule_g.RULES,
    "L3": rule_a.RULES,
}

