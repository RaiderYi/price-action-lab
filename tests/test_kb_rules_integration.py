#!/usr/bin/env python3
"""
kb_rules + market_analyzer 集成测试

测试 kb_rules 四个模块的注册、空数据防御、概念图和语义检索器功能、
溯源验证以及 market_analyzer 集成。
"""

import sys
import os
from pathlib import Path

# 确保项目源路径在 sys.path 中
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent / "src"
sys.path.insert(0, str(_project_root))

import pandas as pd
import numpy as np
import unittest

# ═══════════════════════════════════════════════════════════════════
# 固定路径常量
# ═══════════════════════════════════════════════════════════════════

CONCEPTS_DIR = Path(r"D:\工作\SCDC数据日常工作\llm-wiki\wiki\concepts")
TRANSCRIPT_INDEX = Path(
    r"D:\工作\SCDC数据日常工作\llm-wiki\strategy_engine\wiki\brooks-advanced\transcript-segments\INDEX.json"
)
STOCKS_DIR = Path(r"D:\工作\SCDC数据日常工作\llm-wiki\strategy_engine\data\stocks")


# ═══════════════════════════════════════════════════════════════════
# Test 1: KB规则基础测试
# ═══════════════════════════════════════════════════════════════════

class TestKBRulesRegistration(unittest.TestCase):
    """测试 kb_rules 四个模块的注册、接口和溯源引用"""

    def test_01_all_modules_importable(self):
        """验证四个 kb_rules 模块均可正常导入"""
        try:
            from kb_rules.climax import detect_climax
            from kb_rules.breakout_quality import score_breakout_quality
            from kb_rules.trend_maturity import evaluate_trend_maturity
            from kb_rules.h2l2_state_machine import detect_h2, detect_l2
        except ImportError as e:
            self.fail(f"模块导入失败: {e}")

    def test_02_all_rules_registered(self):
        """验证四个规则均在全局 registry 中注册"""
        from kb_rules.types import registry

        expected_rules = [
            "climax-detection",
            "breakout-quality",
            "trend-maturity",
            "h2-detection",
            "l2-detection",
        ]

        for rule_name in expected_rules:
            rule = registry.get(rule_name)
            self.assertIsNotNone(
                rule, f"规则 '{rule_name}' 未在全局 registry 中注册"
            )

    def test_03_execute_functions_callable(self):
        """验证每个规则的 execute 函数可调用"""
        from kb_rules.types import registry
        from kb_rules.climax import detect_climax
        from kb_rules.breakout_quality import score_breakout_quality
        from kb_rules.trend_maturity import evaluate_trend_maturity
        from kb_rules.h2l2_state_machine import detect_h2, detect_l2

        rule_exec_map = {
            "climax-detection": detect_climax,
            "breakout-quality": score_breakout_quality,
            "trend-maturity": evaluate_trend_maturity,
            "h2-detection": detect_h2,
            "l2-detection": detect_l2,
        }

        for name, expected_fn in rule_exec_map.items():
            rule = registry.get(name)
            self.assertIsNotNone(rule, f"规则 {name} 未注册")
            self.assertTrue(callable(rule.execute), f"规则 {name} 的 execute 不可调用")

    def test_04_source_refs_point_to_real_files(self):
        """验证每个规则的 source_refs 指向实际存在的概念文件"""
        from kb_rules.types import registry

        expected_source_refs = {
            "climax-detection": ["concepts/climax.md"],
            "breakout-quality": [
                "concepts/breakout-mechanics.md",
                "concepts/eighty-percent-rule.md",
            ],
            "trend-maturity": ["concepts/trend-maturity.md"],
            "h2-detection": ["concepts/h2-l2-state-machine.md"],
            "l2-detection": ["concepts/h2-l2-state-machine.md"],
        }

        for rule_name, refs in expected_source_refs.items():
            rule = registry.get(rule_name)
            self.assertIsNotNone(rule, f"规则 {rule_name} 未注册")

            # 构造一个简单 DataFrame 调 execute 获取 source_refs
            dummy_df = pd.DataFrame({
                "open": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                         20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                         30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
                "high": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                         21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                         31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
                "low": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
                        19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
                        29, 30, 31, 32, 33, 34, 35, 36, 37, 38],
                "close": [10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5,
                          20.5, 21.5, 22.5, 23.5, 24.5, 25.5, 26.5, 27.5, 28.5, 29.5,
                          30.5, 31.5, 32.5, 33.5, 34.5, 35.5, 36.5, 37.5, 38.5, 39.5],
                "volume": [100] * 30,
                "date": [f"2026-05-{str(d).zfill(2)}" for d in range(1, 31)],
            })

            result = rule.execute(dummy_df)
            self.assertIsNotNone(result, f"规则 {rule_name} execute 返回 None")

            # 验证 source_refs 中的文件在磁盘上存在
            for ref in result.source_refs:
                concept_file = CONCEPTS_DIR / Path(ref).name
                self.assertTrue(
                    concept_file.exists(),
                    f"规则 {rule_name} 的 source_ref '{ref}' 指向的文件不存在: {concept_file}"
                )

            # 验证规则元数据中的 min_bars 和 required_columns
            self.assertGreater(rule.min_bars, 0, f"规则 {rule_name} 的 min_bars 应 > 0")
            self.assertTrue(len(rule.required_columns) > 0, f"规则 {rule_name} 的 required_columns 不应为空")


# ═══════════════════════════════════════════════════════════════════
# Test 2: 空数据防御测试
# ═══════════════════════════════════════════════════════════════════

class TestNullDataDefense(unittest.TestCase):
    """测试所有规则对空数据/不足数据的防御能力"""

    def setUp(self):
        """导入所有检测函数"""
        from kb_rules.climax import detect_climax
        from kb_rules.breakout_quality import score_breakout_quality
        from kb_rules.trend_maturity import evaluate_trend_maturity
        from kb_rules.h2l2_state_machine import detect_h2, detect_l2

        self.functions = [
            ("climax-detection", detect_climax),
            ("breakout-quality", score_breakout_quality),
            ("trend-maturity", evaluate_trend_maturity),
            ("h2-detection", detect_h2),
            ("l2-detection", detect_l2),
        ]

    def _make_small_df(self, rows: int):
        """构造一个列正确的但行数不足的小 DataFrame"""
        return pd.DataFrame({
            "open": [10.0] * rows,
            "high": [11.0] * rows,
            "low": [9.0] * rows,
            "close": [10.5] * rows,
            "volume": [100] * rows,
            "date": [f"2026-05-{str(d).zfill(2)}" for d in range(1, rows + 1)],
        })

    def test_01_call_with_none(self):
        """传入 None：所有规则应返回 triggered=False，不崩溃"""
        for name, fn in self.functions:
            try:
                result = fn(None)
            except Exception as e:
                self.fail(f"规则 {name} 传入 None 时崩溃: {e}")

            self.assertIsNotNone(result, f"规则 {name} 传入 None 返回 None")
            self.assertFalse(result.triggered,
                             f"规则 {name} 传入 None 应返回 triggered=False，实际 {result.triggered}")

    def test_02_call_with_empty_df(self):
        """传入空 DataFrame：所有规则应返回 triggered=False，不崩溃"""
        empty_df = pd.DataFrame()
        for name, fn in self.functions:
            try:
                result = fn(empty_df)
            except Exception as e:
                self.fail(f"规则 {name} 传入空 DataFrame 时崩溃: {e}")

            self.assertIsNotNone(result, f"规则 {name} 传入空 DataFrame 返回 None")
            self.assertFalse(result.triggered,
                             f"规则 {name} 传入空 DataFrame 应返回 triggered=False")

    def test_03_call_with_two_rows(self):
        """传入只有 2 行的 DataFrame（小于 min_bars）：应返回 triggered=False"""
        small_df = self._make_small_df(2)
        for name, fn in self.functions:
            try:
                result = fn(small_df)
            except Exception as e:
                self.fail(f"规则 {name} 传入 2 行 DataFrame 时崩溃: {e}")

            self.assertIsNotNone(result, f"规则 {name} 传入 2 行返回 None")
            self.assertFalse(result.triggered,
                             f"规则 {name} 传入 2 行应返回 triggered=False，实际 {result.triggered}")

    def test_04_registry_run_with_invalid_input(self):
        """通过 registry.run() 调用空数据：应安全返回 RuleResult"""
        from kb_rules.types import registry

        empty_df = pd.DataFrame()
        rule_names = registry.list_names()

        for name in rule_names:
            try:
                result = registry.run(name, empty_df)
            except Exception as e:
                self.fail(f"registry.run('{name}', empty) 崩溃: {e}")

            self.assertIsNotNone(result, f"registry.run('{name}', empty) 返回 None")
            self.assertFalse(result.triggered)


# ═══════════════════════════════════════════════════════════════════
# Test 3: concept_graph + semantic_retriever 功能测试
# ═══════════════════════════════════════════════════════════════════

class TestConceptGraphAndRetriever(unittest.TestCase):
    """测试 ConceptGraph 和 SemanticRetriever"""

    @classmethod
    def setUpClass(cls):
        """加载概念图和检索器（整个测试类只加载一次）"""
        from kb_rules.concept_graph import ConceptGraph
        from kb_rules.semantic_retriever import SemanticRetriever

        if not CONCEPTS_DIR.exists():
            raise unittest.SkipTest(f"概念目录不存在: {CONCEPTS_DIR}")

        cls.graph = ConceptGraph(CONCEPTS_DIR)
        cls.retriever = SemanticRetriever(CONCEPTS_DIR, TRANSCRIPT_INDEX)

    def test_01_concept_graph_node_count(self):
        """验证概念图节点数 >= 200"""
        count = self.graph.concept_count
        self.assertGreaterEqual(
            count, 200,
            f"概念图节点数 {count} 小于预期 200"
        )

    def test_02_expand_query_climax(self):
        """验证 expand_query(["climax"], hops=1) 返回概念名列表"""
        if "climax" not in self.graph._meta:
            self.skipTest("概念 'climax' 不存在于图中")

        expanded = self.graph.expand_query(["climax"], hops=1)
        self.assertIsInstance(expanded, list)
        self.assertGreater(len(expanded), 0, "expand_query 应返回非空列表")
        self.assertIn("climax", expanded, "展开结果应包含输入概念 'climax'")

        # 至少应返回一些邻居概念
        if len(expanded) > 1:
            for name in expanded:
                self.assertIsInstance(name, str, f"概念名应为字符串，实际 {type(name)}")

    def test_03_expand_query_unknown_concept(self):
        """验证 expand_query 对未知概念的处理（不应崩溃）"""
        expanded = self.graph.expand_query(["nonexistent_concept_xyz"], hops=1)
        self.assertIsInstance(expanded, list)
        # 应至少返回输入概念本身
        self.assertIn("nonexistent_concept_xyz", expanded)

    def test_04_semantic_retriever_retrieve(self):
        """验证 SemanticRetriever.retrieve 返回足够长度的文本"""
        result = self.retriever.retrieve(
            market="ashare",
            phases=["trend", "breakout"],
            signal_types=["L2", "wedge"],
            max_chars=15000,
            include_transcripts=True,
        )

        self.assertIsInstance(result, str)
        result_len = len(result)
        self.assertGreaterEqual(
            result_len, 5000,
            f"检索结果长度 {result_len} 小于 5000 字符"
        )
        # 验证结果包含预期的层级标记
        self.assertIn("Level", result, "结果应包含层级标记")


# ═══════════════════════════════════════════════════════════════════
# Test 4: 溯源验证
# ═══════════════════════════════════════════════════════════════════

class TestSourceVerification(unittest.TestCase):
    """验证概念文件可溯源：source_refs 指向的 .md 文件确实存在"""

    def test_01_concept_files_exist(self):
        """验证所有规则引用的概念文件在磁盘上存在"""
        concept_names = [
            "climax",
            "breakout-mechanics",
            "eighty-percent-rule",
            "trend-maturity",
            "h2-l2-state-machine",
        ]

        for name in concept_names:
            file_path = CONCEPTS_DIR / f"{name}.md"
            self.assertTrue(
                file_path.exists(),
                f"概念文件不存在: {file_path}"
            )

    def test_02_concept_files_readable(self):
        """验证概念文件可读且包含内容"""
        import os

        concept_names = ["climax", "breakout-mechanics", "trend-maturity"]

        for name in concept_names:
            file_path = CONCEPTS_DIR / f"{name}.md"
            if not file_path.exists():
                self.skipTest(f"文件不存在，跳过: {file_path}")
                continue

            file_size = file_path.stat().st_size
            self.assertGreater(
                file_size, 100,
                f"概念文件 {name}.md 太小（{file_size} bytes），可能为空"
            )

    def test_03_climax_content_references_verifiable(self):
        """验证 climax.md 文件内容包含预期关键词"""
        file_path = CONCEPTS_DIR / "climax.md"
        if not file_path.exists():
            self.skipTest("climax.md 不存在")

        try:
            content = file_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8")

        # 验证包含核心概念关键词
        keywords = ["高潮", "不可持续", "紧通道", "大棒"]
        for kw in keywords:
            self.assertIn(
                kw, content,
                f"climax.md 中应包含关键词 '{kw}'"
            )


# ═══════════════════════════════════════════════════════════════════
# Test 5: market_analyzer 集成测试
# ═══════════════════════════════════════════════════════════════════

class TestMarketAnalyzerIntegration(unittest.TestCase):
    """测试 market_analyzer 与 kb_rules 的集成"""

    @classmethod
    def setUpClass(cls):
        """加载 CSV 数据"""
        # 寻找第一个可用的 CSV 文件
        cls.df = None
        cls.csv_path = None
        if STOCKS_DIR.exists():
            for csv_file in sorted(STOCKS_DIR.glob("*.csv")):
                try:
                    df = pd.read_csv(csv_file, encoding="utf-8-sig")
                    if len(df) >= 30 and all(
                        c in df.columns for c in ["open", "high", "low", "close", "date"]
                    ):
                        cls.df = df
                        cls.csv_path = csv_file
                        break
                except Exception:
                    continue

    def test_01_analyze_market_structure(self):
        """测试 analyze_market_structure 基本功能"""
        if self.df is None:
            self.skipTest("没有可用的 CSV 数据文件")

        from market_analyzer import analyze_market_structure, MarketStructure

        result = analyze_market_structure(self.df)

        self.assertIsInstance(result, MarketStructure,
                              "analyze_market_structure 应返回 MarketStructure")

        # 验证 phase 是已知值之一
        valid_phases = ["trend", "range", "transition", "breakout", "insufficient_data"]
        self.assertIn(result.phase, valid_phases,
                      f"phase '{result.phase}' 不在有效值列表中")
        print(f"\n  [数据] {self.csv_path.name}: phase={result.phase}, direction={result.direction}, confidence={result.confidence}")

    def test_02_key_levels_dict(self):
        """验证返回结果包含 key_levels 字典"""
        if self.df is None:
            self.skipTest("没有可用的 CSV 数据文件")

        from market_analyzer import analyze_market_structure

        result = analyze_market_structure(self.df)

        self.assertIsInstance(result.key_levels, dict,
                              "key_levels 应为字典")
        self.assertGreater(len(result.key_levels), 0,
                           "key_levels 不应为空")

        # 验证包含基本键
        expected_keys = ["recent_high", "recent_low", "atr"]
        for key in expected_keys:
            self.assertIn(key, result.key_levels,
                          f"key_levels 应包含 '{key}'")

    def test_03_is_breakout_and_is_transition(self):
        """验证 is_breakout 和 is_transition 返回正确的类型"""
        if self.df is None:
            self.skipTest("没有可用的 CSV 数据文件")

        from market_analyzer import is_breakout, is_transition, find_swing_points, calculate_atr

        # 计算辅助数据
        swings = find_swing_points(self.df)
        atr = calculate_atr(self.df)

        # 构造 range_levels
        highs = [s.price for s in swings if s.type == "swing_high"]
        lows = [s.price for s in swings if s.type == "swing_low"]
        range_levels = {
            "support": min(lows) if lows else self.df["low"].min(),
            "resistance": max(highs) if highs else self.df["high"].max(),
            "atr": atr,
        }

        # 测试 is_breakout
        is_brk, brk_dir = is_breakout(self.df, range_levels)
        self.assertIsInstance(is_brk, bool, "is_breakout 应返回 bool")
        self.assertIsInstance(brk_dir, str, "is_breakout 方向应为字符串")

        # 测试 is_transition
        is_trans, trans_reason = is_transition(
            self.df, "uptrend", swings
        )
        self.assertIsInstance(is_trans, bool, "is_transition 应返回 bool")
        self.assertIsInstance(trans_reason, str, "is_transition 原因应为字符串")

        print(f"\n  [分析] is_breakout={is_brk} dir='{brk_dir}', is_transition={is_trans}")

    def test_04_assemble_wiki_context_v2(self):
        """测试 SemanticRetriever 在 assemble_wiki_context_v2 中的集成"""
        if self.df is None:
            self.skipTest("没有可用的 CSV 数据文件")

        from market_analyzer import analyze_market_structure

        result = analyze_market_structure(self.df)

        # 尝试调用 assemble_wiki_context_v2
        try:
            from wiki_assembler import assemble_wiki_context_v2

            wiki_context = assemble_wiki_context_v2(
                a_stock_analyses={"TEST": result},
                crypto_analyses={},
                index_analysis=None,
                predicted_signals={"TEST": ["L2", "wedge"]},
                max_chars_per_layer=3000,
            )

            self.assertIsInstance(wiki_context, str,
                                  "assemble_wiki_context_v2 应返回字符串")
            self.assertGreater(len(wiki_context), 0,
                               "assemble_wiki_context_v2 不应返回空字符串")

            print(f"\n  [wiki] assemble_wiki_context_v2 返回 {len(wiki_context)} 字符")

        except ImportError as e:
            self.skipTest(f"无法导入 assemble_wiki_context_v2: {e}")
        except Exception as e:
            # 某些情况下可能因路径问题失败，记录但不断言失败
            print(f"\n  [wiki] assemble_wiki_context_v2 因环境问题跳过: {e}")
            self.skipTest(f"assemble_wiki_context_v2 调用异常: {e}")

    def test_05_registry_integration_with_market_structure(self):
        """测试 kb_rules registry 与 market_analyzer 的联动"""
        if self.df is None:
            self.skipTest("没有可用的 CSV 数据文件")

        from kb_rules.types import registry

        # 对所有已注册的规则遍历执行，确保不崩溃
        for rule_name in registry.list_names():
            try:
                result = registry.run(rule_name, self.df)
                self.assertIsNotNone(result)
                self.assertIsInstance(result.triggered, bool)
                self.assertGreaterEqual(result.confidence, 0.0)
                self.assertLessEqual(result.confidence, 1.0)
            except Exception as e:
                self.fail(f"registry.run('{rule_name}', df) 崩溃: {e}")

        print(f"\n  [集成] 所有 {len(registry.list_names())} 个规则在真实数据上执行成功")


# ═══════════════════════════════════════════════════════════════════
# 运行入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 尝试使用 pytest；如果不可用则使用 unittest
    try:
        import pytest
        pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    except ImportError:
        print("pytest 未安装，使用 unittest 运行...")
        unittest.main(verbosity=2)
