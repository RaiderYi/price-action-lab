"""
T2: AUDIT JSON 持久化测试

验证 save_strategy_report() 能正确序列化 result["json"] 中的
_compliance, _guardrail_summary, _evidence_summary, _temporal_summary,
_reject_log, _parser_warnings 到 AUDIT JSON。
"""

import sys, os, json, unittest, tempfile, shutil
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# 注意：save_strategy_report 使用模块级常量 REPORTS_DIR/PROJECT_ROOT
# 需要 monkeypatch 到临时目录

def _make_result(audit_overrides=None):
    """构造最小 result dict（模拟 _generate_via_dual_channel 输出）。"""
    result = {
        "markdown": "# 测试日报\n\n无内容",
        "json": {
            "signal_schema_version": "v4.2",
            "strategy_id": "DAILY_20260101_daily",
            "watchlist": [],
            "output_complete": True,
            "_phase1_retries": 0,
        },
        "usage": {"total_tokens": 100, "prompt_tokens": 80, "completion_tokens": 20},
        "prompt_hash": "abc12345",
        "metadata_missing": 0,
    }
    if audit_overrides:
        result["json"].update(audit_overrides)
    return result


class TestSaveAuditJson(unittest.TestCase):
    """测试 save_strategy_report 的 audit 持久化。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="test_audit_")
        cls.reports_dir = os.path.join(cls.tmpdir, "data", "reports")
        cls.audit_dir = os.path.join(cls.tmpdir, "data", "audit")
        os.makedirs(cls.reports_dir, exist_ok=True)
        os.makedirs(cls.audit_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _call_save(self, result, metadata_missing=0, prompt_hash=""):
        """在临时目录调用 save_strategy_report（mock 日期为 2026-01-01）。"""
        import strategy_generator
        from unittest.mock import patch as _patch
        fake_dt = datetime(2026, 1, 1, 15, 30, 0)

        class _FakeNow:
            @staticmethod
            def now(tz=None):
                return fake_dt
            @staticmethod
            def strftime(fmt):
                return fake_dt.strftime(fmt)
            @staticmethod
            def isoformat():
                return fake_dt.isoformat()

        with _patch.object(strategy_generator, 'REPORTS_DIR',
                          type(strategy_generator.REPORTS_DIR)(self.reports_dir)):
            with _patch.object(strategy_generator, 'PROJECT_ROOT',
                              type(strategy_generator.PROJECT_ROOT)(self.tmpdir)):
                with _patch('strategy_generator.datetime') as mock_dt:
                    mock_dt.now.return_value = fake_dt
                    strategy_generator.save_strategy_report(
                        result,
                        metadata_missing=metadata_missing,
                        prompt_hash=prompt_hash or result.get("prompt_hash", ""))

    def _read_audit(self, date_str="20260101"):
        path = os.path.join(self.audit_dir, f"AUDIT_{date_str}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── 正向测试 ──

    def test_guardrail_summary_persisted(self):
        """_guardrail_summary 非空 → AUDIT JSON 中 guardrail_summary 非空。"""
        result = _make_result({
            "_guardrail_summary": {
                "total_signals": 8, "recorded": 5, "rejected": 3,
                "duplicates": 0, "pass_rate": 0.625,
            },
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit, "AUDIT JSON 未生成")
        gs = audit.get("guardrail_summary", {})
        self.assertEqual(gs.get("total_signals"), 8)
        self.assertEqual(gs.get("recorded"), 5)
        self.assertEqual(gs.get("rejected"), 3)

    def test_reject_log_persisted(self):
        """_reject_log 非空 → AUDIT JSON 中 reject_log 非空。"""
        result = _make_result({
            "_reject_log": [
                {"symbol": "600030", "rr": 1.5, "reason": "RR<1.0"},
                {"symbol": "002594", "rr": 0.8, "reason": "RR<1.0"},
            ],
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        rl = audit.get("reject_log", [])
        self.assertEqual(len(rl), 2)
        self.assertEqual(rl[0]["symbol"], "600030")

    def test_evidence_summary_persisted(self):
        """_evidence_summary 非空 → AUDIT JSON 中 evidence_summary 非空。"""
        result = _make_result({
            "_evidence_summary": {
                "total": 8, "verified": 8, "passed": 6,
                "temporal": {
                    "verified_count": 8, "passed_count": 5,
                    "confirmed_swing_count": 14,
                },
            },
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        es = audit.get("evidence_summary", {})
        self.assertEqual(es.get("total"), 8)
        self.assertEqual(es.get("passed"), 6)
        self.assertEqual(es["temporal"]["confirmed_swing_count"], 14)

    def test_temporal_summary_persisted(self):
        """_temporal_summary 非空 → AUDIT JSON 中 temporal_summary 非空。"""
        result = _make_result({
            "_temporal_summary": {
                "kline_window_start": "2026-01-01 09:30",
                "kline_window_end": "2026-01-01 15:00",
                "signal_time": "2026-01-01T15:30:00",
            },
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        ts = audit.get("temporal_summary", {})
        self.assertIn("kline_window_start", ts)
        self.assertIn("2026-01-01", ts["kline_window_start"])

    def test_compliance_persisted(self):
        """_compliance 非空 → AUDIT JSON 中 contract_compliance 非空。"""
        result = _make_result({
            "_compliance": {
                "total_signals": 8, "complete_signals": 8,
                "missing_structure_evidence": 0,
            },
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        cc = audit.get("contract_compliance", {})
        self.assertEqual(cc.get("total_signals"), 8)

    def test_parser_warnings_persisted(self):
        """_parser_warnings 非空 → AUDIT JSON 中 parser_warnings 非空。"""
        result = _make_result({
            "_parser_warnings": ["counter_evidence_missing_in_json", "structure_evidence_missing"],
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        pw = audit.get("parser_warnings", [])
        self.assertGreater(len(pw), 0)

    def test_all_fields_together(self):
        """所有 audit key 同时存在 → AUDIT 完整写入。"""
        result = _make_result({
            "_compliance": {"total_signals": 10, "complete_signals": 9},
            "_guardrail_summary": {"total_signals": 10, "recorded": 7, "rejected": 3,
                                   "duplicates": 1, "pass_rate": 0.7},
            "_evidence_summary": {"total": 10, "verified": 10, "passed": 7,
                                  "temporal": {"verified_count": 10, "passed_count": 7}},
            "_temporal_summary": {"kline_window_start": "09:30", "kline_window_end": "15:00"},
            "_reject_log": [{"symbol": "X", "rr": 0.5}],
            "_parser_warnings": ["w1"],
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        # 全部非空
        self.assertIsInstance(audit.get("contract_compliance"), dict)
        self.assertIsInstance(audit.get("guardrail_summary"), dict)
        self.assertIsInstance(audit.get("evidence_summary"), dict)
        self.assertIsInstance(audit.get("temporal_summary"), dict)
        self.assertIsInstance(audit.get("reject_log"), list)
        self.assertIsInstance(audit.get("parser_warnings"), list)
        # 验证值
        self.assertTrue(audit["contract_compliance"])
        self.assertTrue(audit["guardrail_summary"])
        self.assertTrue(audit["evidence_summary"])
        self.assertTrue(audit["temporal_summary"])
        self.assertTrue(audit["reject_log"])
        self.assertTrue(audit["parser_warnings"])

    # ── 边界测试 ──

    def test_empty_signals_day_does_not_crash(self):
        """空信号日（所有 audit key 为空）→ AUDIT 结构存在但值为空。"""
        result = _make_result()  # 无任何 audit key
        self._call_save(result)
        audit = self._read_audit()
        self.assertIsNotNone(audit)
        # 结构应存在
        self.assertIn("guardrail_summary", audit)
        self.assertIn("evidence_summary", audit)
        self.assertIn("temporal_summary", audit)
        self.assertIn("reject_log", audit)
        self.assertIn("parser_warnings", audit)
        # 值为空
        self.assertEqual(audit["guardrail_summary"], {})
        self.assertEqual(audit["evidence_summary"], {})
        self.assertEqual(audit["temporal_summary"], {})
        self.assertEqual(audit["reject_log"], [])
        self.assertEqual(audit["parser_warnings"], [])

    def test_report_id_consistency(self):
        """AUDIT.report_id 应与 result["json"]["strategy_id"] 一致。"""
        result = _make_result()
        result["json"]["strategy_id"] = "DAILY_20260101_daily_custom"
        self._call_save(result)
        audit = self._read_audit()
        self.assertEqual(audit["report_id"], "DAILY_20260101_daily_custom")

    def test_partial_audit_keys(self):
        """部分 audit key 存在、部分缺失 → 各字段独立序列化不互扰。"""
        result = _make_result({
            "_guardrail_summary": {"total_signals": 3},
            "_reject_log": [{"s": "A"}],
            # _evidence_summary, _temporal_summary, _compliance 缺失
        })
        self._call_save(result)
        audit = self._read_audit()
        self.assertEqual(audit["guardrail_summary"]["total_signals"], 3)
        self.assertEqual(len(audit["reject_log"]), 1)
        self.assertEqual(audit["evidence_summary"], {})
        self.assertEqual(audit["temporal_summary"], {})
        self.assertEqual(audit["contract_compliance"], {})


if __name__ == "__main__":
    unittest.main()
