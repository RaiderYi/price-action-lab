"""Legacy 信号别名迁移层（S1-03，F01/F02）。

目的：legacy proxy 信号（signal_predictor 路径）与 strict 信号在统计中
永不混淆。提供：
- canonical_signal_id：给 legacy 检测结果打上血统标注的规范 ID；
- alias_map：旧键名 → (family, implementation) 的显式映射；
- 兼容说明：旧回测 JSON 中的信号计数（如 "H2": 9）从本模块视角应读作
  legacy_proxy 血统的 H2。

不修改 legacy 代码本身（保持可复现）；新引擎（S4）必须通过本模块
读取 legacy 检测输出，禁止直接把 predictor 结果当 strict 用。
"""
from __future__ import annotations

from pal.domain.identity import make_setup_id
from pal.domain.models import Implementation

# 旧 predictor 的 signal_type 键 → 规范 (family, implementation)
ALIAS_MAP = {
    "H2": ("H2", Implementation.LEGACY_PROXY),
    "L2": ("L2", Implementation.LEGACY_PROXY),
    "H1": ("H1", Implementation.LEGACY_PROXY),
    "L1": ("L1", Implementation.LEGACY_PROXY),
    "breakout": ("breakout", Implementation.LEGACY_PROXY),
    "wedge": ("wedge", Implementation.LEGACY_PROXY),
    "final_flag": ("final_flag", Implementation.LEGACY_PROXY),
    "tr_fade": ("tr_fade", Implementation.LEGACY_PROXY),
    "climax_reversal": ("climax_reversal", Implementation.LEGACY_PROXY),
    "measured_move": ("measured_move", Implementation.RESEARCH),
    "double_bottom": ("double_bottom", Implementation.RESEARCH),
    "double_top": ("double_top", Implementation.RESEARCH),
    "eighty_twenty": ("eighty_twenty", Implementation.RESEARCH),
    # strict 检测器的旧键（registry 层另有登记，不在此重复开放）
}


def canonical_signal_id(legacy_signal_type: str, instrument_id: str,
                        formed_at: str) -> str:
    """把 legacy 检测输出包装为带血统的规范 setup_id。

    旧 JSON 里的 "H2" 与新引擎 strict H2 调用本函数后 ID 不同
    （implementation 参与内容 hash），统计天然分离（F01/F02 验收）。
    """
    try:
        family, impl = ALIAS_MAP[legacy_signal_type]
    except KeyError:
        raise KeyError(
            f"未知 legacy 信号类型: {legacy_signal_type!r}；"
            f"合法键: {sorted(ALIAS_MAP)}（新增须显式登记，防拼写错误静默通过）") from None
    sid = make_setup_id(instrument_id, family, impl.value, formed_at)
    return f"{sid}|{family}/{impl.value}"
