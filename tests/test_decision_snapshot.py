"""S1-08 测试：决策快照。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from pal.domain.decision import DecisionSnapshot
from pal.domain.models import DomainValidationError


GOOD = dict(
    outcome="accept",
    rule_id="focus.live_gate.v1",
    reason_code="OK_STRUCTURE_CONFIRMED",
    evidence_ids=("evd_abc", "evd_def"),
    decided_at="2026-10-13T10:05:00+08:00",
)


class TestDecisionSnapshot:
    def test_valid_accept(self):
        ds = DecisionSnapshot(**GOOD)
        assert ds.outcome == "accept"

    def test_accept_without_evidence_rejected(self):
        bad = dict(GOOD, evidence_ids=())
        with pytest.raises(DomainValidationError, match="evidence"):
            DecisionSnapshot(**bad)

    def test_reject_without_evidence_ok(self):
        ds = DecisionSnapshot(**dict(GOOD, outcome="reject",
                                     reason_code="REJ_INSUFFICIENT_EVIDENCE",
                                     evidence_ids=()))
        assert ds.outcome == "reject"

    def test_unknown_reason_code_rejected(self):
        bad = dict(GOOD, reason_code="BECAUSE_I_SAY_SO")
        with pytest.raises(DomainValidationError, match="reason_code"):
            DecisionSnapshot(**bad)

    def test_unknown_outcome_rejected(self):
        with pytest.raises(DomainValidationError):
            DecisionSnapshot(**dict(GOOD, outcome="maybe"))

    def test_json_roundtrip(self):
        ds = DecisionSnapshot(**GOOD)
        rt = DecisionSnapshot.from_json(ds.to_json())
        assert rt == ds

    def test_json_is_sorted_deterministic(self):
        a = DecisionSnapshot(**GOOD).to_json()
        b = DecisionSnapshot(**GOOD).to_json()
        assert a == b  # 同输入同序列化（可重放）
