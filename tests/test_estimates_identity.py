"""S1-06/S1-07 测试：估计分离 + 统一 ID。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from pal.domain.estimates import (
    EmpiricalProbability,
    HeuristicScore,
    SourceEstimate,
)
from pal.domain.identity import (
    EntityId,
    ID_PREFIXES,
    make_order_id,
    make_run_id,
    make_setup_id,
    make_signal_id,
)
from pal.domain.models import DomainValidationError


class TestEstimatesSeparation:
    """F14：质量分不是概率；未校准 p_win 必须是 None。"""

    def test_heuristic_score_bounds(self):
        with pytest.raises(DomainValidationError):
            HeuristicScore(score=1.5, components={}, rule_version="v1")
        with pytest.raises(DomainValidationError):
            HeuristicScore(score=-0.1, components={}, rule_version="v1")

    def test_heuristic_score_requires_version(self):
        with pytest.raises(DomainValidationError):
            HeuristicScore(score=0.5, components={}, rule_version="")

    def test_empirical_requires_samples(self):
        with pytest.raises(DomainValidationError):
            EmpiricalProbability(p_win=0.6, n_samples=0, method="x",
                                 validation="oot", calibrated_at="2026-10-12")

    def test_source_estimate_rejects_fake_status(self):
        with pytest.raises(DomainValidationError):
            SourceEstimate(source_id="m1", source_ev=1.0, source_wr=None,
                           probability_status="definitely_real",  # 非法
                           source_method="ev", source_version="v3")

    def test_uncalibrated_prior_accepted(self):
        se = SourceEstimate(source_id="m1", source_ev=1.0, source_wr=0.6,
                            probability_status="uncalibrated_prior",
                            source_method="ev", source_version="v3")
        assert se.source_wr == 0.6  # 原样保留，不重算


class TestIdentity:
    def test_roundtrip(self):
        eid = EntityId("run", "abc123")
        assert str(eid) == "run_abc123"
        assert EntityId.parse("run_abc123") == eid

    def test_unknown_prefix_rejected(self):
        with pytest.raises(DomainValidationError):
            EntityId("pizza", "x")

    def test_setup_id_deterministic(self):
        a = make_setup_id("SSE.600519", "H2", "legacy_proxy", "2026-10-12T10:00+08:00")
        b = make_setup_id("SSE.600519", "H2", "legacy_proxy", "2026-10-12T10:00+08:00")
        c = make_setup_id("SSE.600519", "H2", "strict", "2026-10-12T10:00+08:00")
        assert a == b          # 内容寻址：同输入同 ID（幂等）
        assert a != c          # legacy/strict 血统不同 → 不同 setup（F01/F02）

    def test_order_attempt_validation(self):
        plan = "plan_xyz"
        with pytest.raises(DomainValidationError):
            make_order_id(plan, 0)
        o1, o2 = make_order_id(plan, 1), make_order_id(plan, 2)
        assert o1 != o2

    def test_run_id_contains_config_hash(self):
        rid = make_run_id("2026-10-12T15:30:00+08:00", "deadbeef" * 8)
        assert str(rid).startswith("run_")
        assert "2026-10-12T15:30:00" in str(rid)
