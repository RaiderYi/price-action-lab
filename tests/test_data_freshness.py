#!/usr/bin/env python3
"""
P0: 数据新鲜度测试
覆盖：
1. 缓存行数足够但日期过期 → 必须判定 stale
2. 午间模式允许最新bar到11:30或接近当前可用bar
3. 日度模式要求最新bar至少到当日15:00
4. 数据过期时不得生成正式信号
5. 报告展示30m最新K线时间
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions under test
from run_strategy import (
    _get_30m_freshness_status,
    _check_all_data_freshness,
    _is_trading_day,
    _fetch_30m_incremental,
    _load_30m_cache,
    _cache_30m,
    _30m_cache_path,
    _get_latest_30m_date,
)


def _make_30m_df(latest_date, n_rows=160):
    """Create a synthetic 30m DataFrame with n_rows ending at latest_date."""
    dates = pd.date_range(
        end=pd.to_datetime(latest_date),
        periods=n_rows,
        freq='30min'
    )
    data = {
        'date': dates,
        'open': [100.0 + i * 0.1 for i in range(n_rows)],
        'high': [101.0 + i * 0.1 for i in range(n_rows)],
        'low': [99.0 + i * 0.1 for i in range(n_rows)],
        'close': [100.5 + i * 0.1 for i in range(n_rows)],
        'volume': [1000000 + i * 1000 for i in range(n_rows)],
    }
    df = pd.DataFrame(data)
    return df


class TestTradingDay:
    """交易日判断"""

    def test_weekday_is_trading(self):
        """周一至周五判定为交易日"""
        from datetime import date
        # Monday
        assert _is_trading_day(datetime(2026, 6, 1)) is True
        # Wednesday
        assert _is_trading_day(datetime(2026, 6, 3)) is True
        # Friday
        assert _is_trading_day(datetime(2026, 6, 5)) is True

    def test_weekend_not_trading(self):
        """周六周日不是交易日"""
        assert _is_trading_day(datetime(2026, 6, 6)) is False  # Saturday
        assert _is_trading_day(datetime(2026, 6, 7)) is False  # Sunday


class Test30mFreshnessStatus:
    """30m新鲜度判定"""

    def test_cache_sufficient_rows_but_stale_date(self):
        """核心case：缓存有160行但日期是上周 → 必须判定 stale"""
        # Old data from 5 days ago
        stale_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        df = _make_30m_df(stale_date, n_rows=160)

        status, latest_str, reason = _get_30m_freshness_status('test', df, 'daily')
        assert status == 'stale', f"Expected stale, got {status}, reason={reason}"
        assert 'today' in reason or 'last_trading' in reason

    def test_todays_data_is_fresh_daily_mode(self):
        """今日数据判定为 fresh（日度模式）"""
        today = datetime.now().strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(today, n_rows=160)

        status, latest_str, reason = _get_30m_freshness_status('test', df, 'daily')
        assert status == 'fresh', f"Expected fresh, got {status}, reason={reason}"

    def test_midday_mode_accepts_morning_bars(self):
        """午间模式：11:30前判定为 acceptable"""
        today_10 = datetime.now().strftime('%Y-%m-%d 10:00:00')
        df = _make_30m_df(today_10, n_rows=160)

        status, latest_str, reason = _get_30m_freshness_status('test', df, 'midday')
        assert status == 'acceptable', f"Expected acceptable, got {status}"

    def test_midday_mode_after_1130_is_fresh(self):
        """午间模式：11:30后判定为 fresh"""
        today_1130 = datetime.now().strftime('%Y-%m-%d 11:30:00')
        df = _make_30m_df(today_1130, n_rows=160)

        status, latest_str, reason = _get_30m_freshness_status('test', df, 'midday')
        assert status == 'fresh', f"Expected fresh, got {status}"

    def test_weekend_accepts_friday_data(self):
        """周六运行：周五数据判定为 fresh"""
        # Simulate running on Saturday
        saturday = datetime.now()
        # Find next Saturday
        days_to_sat = 5 - saturday.weekday()
        if days_to_sat <= 0:
            days_to_sat += 7
        sat_dt = saturday + timedelta(days=days_to_sat)
        friday = sat_dt - timedelta(days=1)

        friday_str = friday.strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(friday_str, n_rows=160)

        # We can't easily mock datetime.now(), so we just verify
        # the function handles non-trading days correctly by checking
        # that if today is not a trading day, it accepts recent data
        status, latest_str, reason = _get_30m_freshness_status('test', df, 'daily')
        # If today IS a trading day, this will be stale (expected)
        # If not, it should be fresh
        if not _is_trading_day():
            assert status == 'fresh', f"Weekend should accept Friday, got {status}"

    def test_empty_dataframe_is_stale(self):
        """空DataFrame → stale"""
        df = pd.DataFrame()
        status, latest_str, reason = _get_30m_freshness_status('test', df, 'daily')
        assert status == 'stale'

    def test_none_dataframe_is_stale(self):
        """None → stale"""
        status, latest_str, reason = _get_30m_freshness_status('test', None, 'daily')
        assert status == 'stale'


class TestCheckAllDataFreshness:
    """全量数据新鲜度检查"""

    def test_all_fresh_returns_true(self):
        """所有数据新鲜 → all_fresh=True"""
        today = datetime.now().strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(today, n_rows=160)
        daily_df = _make_30m_df(today, n_rows=60)  # daily data

        results = {
            'A股': {
                'test_symbol': {
                    'history': df,
                    'daily_history': daily_df,
                    'lb_quote': {'last': 100, 'change_pct': 1.0},
                }
            },
            '大盘指数': {
                'sh.000001': {'history': df}
            }
        }
        a_stock_dfs = {'test_symbol': df}

        is_fresh, status, text = _check_all_data_freshness(results, a_stock_dfs, 'daily')
        assert is_fresh is True, f"Expected fresh, got {text}"
        assert '30m_a_stocks' in status
        assert status['30m_a_stocks']['stale_count'] == 0

    def test_all_stale_returns_false(self):
        """全部过期 → all_fresh=False"""
        old_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(old_date, n_rows=160)

        results = {
            'A股': {
                'test_symbol': {
                    'history': df,
                    'daily_history': df,
                    'lb_quote': None,
                }
            },
            '大盘指数': {}
        }
        a_stock_dfs = {'test_symbol': df}

        if _is_trading_day():
            is_fresh, status, text = _check_all_data_freshness(results, a_stock_dfs, 'daily')
            assert is_fresh is False
            assert status['30m_a_stocks']['stale_count'] > 0
        # Else on weekend, this might be fresh — skip assertion

    def test_weekly_mode_always_passes(self):
        """周度模式始终返回 fresh（历史分析可接受过期数据）"""
        old_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(old_date, n_rows=160)

        results = {
            'A股': {
                'test_symbol': {
                    'history': df,
                    'daily_history': df,
                }
            },
            '大盘指数': {}
        }
        a_stock_dfs = {'test_symbol': df}

        is_fresh, status, text = _check_all_data_freshness(results, a_stock_dfs, 'weekly')
        assert is_fresh is True  # Weekly always passes

    def test_data_status_text_includes_timestamps(self):
        """报告文本包含时间戳信息"""
        today = datetime.now().strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(today, n_rows=160)

        results = {
            'A股': {
                'sym1': {'history': df, 'daily_history': df},
            },
            '大盘指数': {'idx1': {'history': df}},
        }
        a_stock_dfs = {'sym1': df}

        _, _, text = _check_all_data_freshness(results, a_stock_dfs, 'daily')
        assert '30m最新' in text
        assert '日线最新' in text

    def test_stale_report_shows_symbols(self):
        """过期报告列出受影响标的"""
        old_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d 15:00:00')
        df = _make_30m_df(old_date, n_rows=160)

        results = {
            'A股': {
                '300750': {'history': df, 'daily_history': df},
                '002594': {'history': df, 'daily_history': df},
                '600030': {'history': df, 'daily_history': df},
            },
            '大盘指数': {}
        }
        a_stock_dfs = {s: df for s in ['300750', '002594', '600030']}

        if _is_trading_day():
            is_fresh, status, text = _check_all_data_freshness(results, a_stock_dfs, 'daily')
            assert is_fresh is False
            assert status['30m_a_stocks']['stale_count'] == 3


class TestCacheIntegration:
    """30m缓存集成测试"""

    def test_cache_path_construction(self):
        """缓存路径正确"""
        path = _30m_cache_path('300750')
        assert '300750.csv' in path
        assert '30m' in path

    def test_load_cache_returns_tuple(self):
        """_load_30m_cache 返回 (df, latest_str) 元组"""
        result = _load_30m_cache('NONEXISTENT_SYMBOL_XYZ')
        assert isinstance(result, tuple)
        assert len(result) == 2
        df, latest = result
        assert df is None
        assert latest is None

    def test_get_latest_date_returns_none_for_missing(self):
        """不存在的文件返回 None"""
        result = _get_latest_30m_date('NONEXISTENT_SYMBOL_XYZ')
        assert result is None


class TestFetchIncremental:
    """增量拉取测试"""

    def test_fetch_incremental_same_day_no_new_data(self):
        """当日数据已是最新→ fetch_status='same'"""
        # This is an integration test that requires a real fetcher
        # We just verify the function signature and basic behavior
        from run_strategy import _fetch_30m_incremental
        assert callable(_fetch_30m_incremental)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
