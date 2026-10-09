"""Small, explicit Case E demo: check completeness without inventing other results."""
import json
from pathlib import Path


def load_demo_policy():
    """Read editable example settings from the adjacent JSON file."""
    path = Path(__file__).with_name('demo_policy.json')
    return json.loads(path.read_text(encoding='utf-8'))


def apply_demo_completeness(record, policy):
    """Check mandatory fields, retaining incomplete records and original content."""
    missing = []
    for field in policy['required_fields'][record['order_type']]:
        value = record.get(field)
        # Zero is a valid quantity. Only absent or blank values are missing.
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    record['client_id'] = policy['client_id']
    record['is_demo'] = True
    record['policy_version'] = policy['policy_version']
    record['rule_results'] = {
        'E-01': {
            'status': 'fail' if missing else 'pass',
            'message': 'Missing required fields.' if missing else 'Required fields are present.',
            'missing_fields': missing,
        }
    }
    # Explicitly show that the demo has not evaluated the other six rules.
    for number in range(2, 8):
        record['rule_results'][f'E-0{number}'] = {
            'status': 'not_evaluated',
            'message': 'Outside this completeness demo; supporting data/policy not supplied.',
        }
    return record
