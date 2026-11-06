"""Classify a definite WeChat whitelist refusal, without retrying any API call."""
import ipaddress
import re


def whitelist_refusal(diagnostic: str, *, draft_payload_exists: bool):
    if not re.search(r'WeChat API error 40164\s*:', diagnostic):
        return None
    match = re.search(r'invalid ip\s+([0-9a-fA-F:.]+)', diagnostic, re.I)
    address = None
    if match:
        try:
            address = str(ipaddress.ip_address(match.group(1).rstrip('.,')))
        except ValueError:
            pass
    return {'outcome': 'waiting-whitelist', 'errcode': 40164, 'reported_egress_ip': address,
            'requires_reconcile': bool(draft_payload_exists), 'resume_requires_user_confirmation': True,
            'scope': 'wechat-draft-upload-only'}
