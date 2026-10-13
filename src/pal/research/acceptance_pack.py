"""N01：冻结离线输入与输出契约 + 固定验收包（第四轮 §7 包1）。

契约（snapshot v1）：
    acceptance_pack/
    ├── manifest.json        # asof_date/snapshot_id/calendar_version/
    │                        # instruments 行业映射/expected（精确期望）
    ├── bars_<iid>.jsonl     # 每票一文件（30m bar，schema 同 CLI _load_bars_file）
    └── daily_<iid>.jsonl    # 每票日线背景（引擎 regime 输入）

验收包设计（3 票 × 4 交易日，22 根历史 + 触发棒）：
    - SSE.600519（贵州茅台占位）：强突破场景 → 必须产生 ARMED
    - SZSE.000001：横盘无信号 → NO_SIGNAL（真实评估过）
    - SZSE.300750：下跌 regime → REGIME_BLOCK

expected 契约（N01 要求：输出必须包含决策、订单、成交、持仓 lot、
现金、NAV、风险事件与对账）——见 manifest.expected。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from pal.data.bars import Bar
from pal.data.calendar import TZ, TradingCalendar


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write_bar_jsonl(path: str, bars: Sequence[Bar]) -> str:
    with open(path, "w", encoding="utf-8") as f:
        for b in bars:
            f.write(json.dumps({
                "instrument_id": b.instrument_id, "timeframe": b.timeframe,
                "bar_start": b.bar_start.isoformat(),
                "bar_end": b.bar_end.isoformat(),
                "available_at": b.available_at.isoformat(),
                "open": b.open, "high": b.high, "low": b.low,
                "close": b.close, "volume": b.volume,
                "amount": b.amount, "is_final": b.is_final,
            }, ensure_ascii=False) + "\n")
    return file_sha256(path)


def bar(t, o, h, l, c, v=100_000, iid="SSE.600519", tf="30m",
        avail=None):
    e = t + timedelta(minutes=30) if tf == "30m" else t.replace(hour=15)
    return Bar(iid, tf, t, e, avail or e, o, h, l, c, v)


# ── 构建固定验收包（确定性生成，无随机）──

TRADING_DAYS = (date(2026, 10, 9), date(2026, 10, 12),
                date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15))
CAL = TradingCalendar(TRADING_DAYS, "acceptance-v1")


def _slots():
    return [s for d in TRADING_DAYS for s, _ in CAL.bars_for_day(d)]


def _daily_bg(iid: str, n: int = 60, base: float = 10.0,
              drift: float = 0.0) -> List[Bar]:
    """n 根历史日线（工作日回溯，regime 输入）。"""
    out = []
    d = TRADING_DAYS[0] - timedelta(days=1)
    while len(out) < n:
        if d.weekday() < 5:
            s = datetime.combine(d, time(9, 30), tzinfo=TZ)
            e = datetime.combine(d, time(15, 0), tzinfo=TZ)
            px = base + drift * len(out)
            out.append(Bar(iid, "1d", s, e, e, px, px * 1.01, px * 0.99,
                           px, 1e6, 5e7))
        d -= timedelta(days=1)
    out.reverse()
    return out


def breakout_bars(iid="SSE.600519"):
    """强突破全链：21 根窄幅 → 信号棒(10-13) → 触发棒(10-14) → 退出棒(10-15)。

    N01 验收矩阵第 3 行：候选→ARMED→FILL@10.0→T+1 隔日跳空止损退出@8.5。
    """
    slots = _slots()
    bars = []
    for i in range(21):
        bars.append(bar(slots[i], o=9.5, h=10.0, l=9.0, c=9.6, iid=iid))
    bars.append(bar(slots[21], o=9.9, h=11.0, l=9.7, c=10.9, iid=iid))  # 信号
    bars.append(bar(slots[23], o=9.9, h=10.5, l=9.6, c=10.3, v=1_000_000,
                    iid=iid))                                            # 触发
    bars.append(bar(slots[31], o=8.5, h=8.6, l=8.0, c=8.2, v=1_000_000,
                    iid=iid))                                            # 退出
    return bars


def flat_bars(iid="SZSE.000001"):
    """横盘无信号（对齐至 10-15）。"""
    slots = _slots()
    out = [bar(slots[i], o=10.0, h=10.3, l=9.8, c=10.05, iid=iid)
           for i in range(22)]
    out.append(bar(slots[23], o=10.0, h=10.2, l=9.9, c=10.0, iid=iid))
    out.append(bar(slots[31], o=10.0, h=10.2, l=9.9, c=10.0, iid=iid))
    return out


def downtrend_bars(iid="SZSE.300750"):
    """阴跌 → 下跌 regime（对齐至 10-15）。"""
    slots = _slots()
    out = []
    px = 11.0
    for i in range(22):
        out.append(bar(slots[i], o=px, h=px + 0.1, l=px - 0.35,
                       c=px - 0.25, iid=iid))
        px -= 0.25
    out.append(bar(slots[23], o=px, h=px + 0.1, l=px - 0.35,
                   c=px - 0.25, iid=iid))
    out.append(bar(slots[31], o=px - 0.25, h=px - 0.1, l=px - 0.6,
                   c=px - 0.5, iid=iid))
    return out


INSTRUMENT_META = {
    "SSE.600519": {"industry": "consumer", "display": "600519"},
    "SZSE.000001": {"industry": "bank", "display": "000001"},
    "SZSE.300750": {"industry": "battery", "display": "300750"},
}


def build_pack(out_dir: str) -> Dict[str, str]:
    """生成冻结验收包 + manifest（含每文件 SHA256 与精确期望）。"""
    os.makedirs(out_dir, exist_ok=True)
    hashes = {}
    for iid, bars in (("SSE.600519", breakout_bars()),
                      ("SZSE.000001", flat_bars()),
                      ("SZSE.300750", downtrend_bars())):
        fn = iid.replace(".", "_")
        hashes[f"bars_{fn}.jsonl"] = write_bar_jsonl(
            os.path.join(out_dir, f"bars_{fn}.jsonl"), bars)
        hashes[f"daily_{fn}.jsonl"] = write_bar_jsonl(
            os.path.join(out_dir, f"daily_{fn}.jsonl"),
            _daily_bg(iid, drift=0.002 if "300750" not in iid else -0.001))
    manifest = {
        "schema": "acceptance_pack/v1",
        "snapshot_id": "acceptance-frozen-v1",
        "asof_date": max(
            b.bar_start.date() for b in
            breakout_bars() + flat_bars() + downtrend_bars()
        ).isoformat(),   # 盘后语义：候选自行情末日起有效（覆盖全窗口）
        "calendar_version": CAL.calendar_version,
        "trading_days": [d.isoformat() for d in TRADING_DAYS],
        "instruments": INSTRUMENT_META,
        "file_sha256": hashes,
        # N01 精确期望（修复后必须逐项达成；当前全部未达成=红）
        "expected": {
            "SSE.600519": {
                "signal": "ARMED",      # 默认 regime 路径（A01 修复后）
                "note": "强突破+RANGE日线 → 自动环境 ARMED（非显式传入）",
            },
            "SZSE.000001": {
                "signal": "NO_SIGNAL",  # 真实评估后无信号 ≠ 未评估(A02)
            },
            "SZSE.300750": {
                "signal": "REGIME_BLOCK",
            },
            "cross_day_history": "引擎窗口 ≥22 根跨 3 个交易日（A03 修复后）",
            "multi_instrument": "异票行情互不干扰、无错票成交（A04）",
        },
        "disclaimer": "合成数据仅用于工程验收，不构成收益证据（N01 契约）",
    }
    with open(os.path.join(out_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return hashes
