"""P7.2-7.3: 系统价格计算层 — LLM 不再是价格源。"""
from typing import Dict, Tuple, Optional


def build_system_prices(symbol, signal_type, direction, current_price,
                        structure_evidence=None, recent_kline=None) -> dict:
    st = (signal_type or "").lower()
    dr = (direction or "").lower()
    se = structure_evidence if isinstance(structure_evidence, dict) else {}
    cp = current_price
    if (not cp or cp <= 0) and st != "wedge":
        return _insufficient("current_price 缺失")
    if cp and cp > 0:
        se = _sanitize_structure_evidence(se, cp)
    else:
        se = dict(se)
    builders = {"h1": _h2, "h2": _h2, "l1": _l2, "l2": _l2,
                "wedge": _wedge, "tr_fade": _tr_fade,
                "measured_move": _measured_move,
                "double_bottom": _double_bottom,
                "double_top": _double_top,
                "eighty_twenty": _generic}
    return builders.get(st, _generic)(cp, dr, se)


def _sanitize_structure_evidence(se: dict, cp: float) -> dict:
    """P7.3: 清洗 LLM 伪造的结构点。偏离当前价 >30% 的结构点置零。"""
    clean = dict(se)
    struct_points = ["HL1", "HL2", "LH1", "LH2",
                     "push_1", "push_2", "push_3",
                     "push_1_price", "push_2_price", "push_3_price",
                     "range_high", "range_low",
                     "trading_range_high", "trading_range_low",
                     "measure_start", "measure_end", "breakout_point",
                     "projected_target",
                     "bottom_1", "bottom_2", "bottom_1_price", "bottom_2_price",
                     "top_1", "top_2", "top_1_price", "top_2_price",
                     "neckline", "breakdown_point"]
    for key in struct_points:
        val = clean.get(key, 0)
        if val and isinstance(val, (int, float)) and val > 0:
            if abs(val - cp) / cp > 0.30:
                clean[key] = 0  # 清零伪造的结构点
    return clean


def _insufficient(reason):
    return dict(entry_min=0, entry_max=0, stop_loss=0, tp1=0, tp2=0,
                execution_rr=0, structure_rr=0,
                price_source=f"insufficient:{reason}",
                price_builder_status="insufficient_evidence",
                price_builder_reason=reason, source_points={})


def _wrap(result, source_label, pts=None):
    result["price_builder_status"] = "success"
    result["price_builder_reason"] = ""
    result["source_points"] = pts or {}
    return result


def _h2(cp, dr, se):
    hl1 = se.get("HL1", se.get("hl1", 0))
    hl2 = se.get("HL2", se.get("hl2", 0))
    if dr == "long":
        emin, emax = cp * 0.99, cp * 1.01
        sl = hl2 * 0.99 if hl2 else cp * 0.93
        # tp1 = prior_high (H2 long 目标位: 上方 swing high)
        # HL1 现在是 prior swing low，不可作为做多目标
        prior_high = se.get("prior_high", se.get("recent_high", se.get("swing_high", 0)))
        if prior_high and prior_high > cp:
            t1 = prior_high
        else:
            t1 = cp * 1.06
        t2 = cp * 1.10
    else:
        emin, emax = cp * 0.99, cp * 1.01
        sl = hl2 * 1.01 if hl2 else cp * 1.07
        t1 = hl1 if hl1 else cp * 0.94
        t2 = cp * 0.90
    risk = abs((emin + emax) / 2 - sl)
    reward = abs(t1 - (emin + emax) / 2)
    denom = abs(cp - hl2)
    srr = abs(hl1 - cp) / denom if hl1 and hl2 and cp and denom > 0.01 else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=round(reward / risk, 2) if risk else 0,
                      structure_rr=round(srr, 2),
                      price_source="system:current_price_based+HL_points" if hl1 and hl2 else "system:current_price_based"),
                 "HL_points", dict(HL1=hl1, HL2=hl2))


def _l2(cp, dr, se):
    lh1 = se.get("LH1", se.get("lh1", 0))
    lh2 = se.get("LH2", se.get("lh2", 0))
    if dr == "short":
        emin, emax = cp * 0.99, cp * 1.01
        sl = lh2 * 1.01 if lh2 else cp * 1.07
        # P0-fix: short TP1 使用下方 prior_low，不再使用 LH1（swing high）
        prior_low = se.get("prior_low", se.get("recent_low", se.get("swing_low", 0)))
        if prior_low and prior_low < cp:
            t1 = prior_low
        else:
            t1 = cp * 0.94
        t2 = cp * 0.90
    else:
        emin, emax = cp * 0.99, cp * 1.01
        sl = lh2 * 0.99 if lh2 else cp * 0.93
        # P2-fix: long TP1 使用上方 prior_high，不再使用 lh1（swing low）
        prior_high = se.get("prior_high", se.get("recent_high", se.get("swing_high", 0)))
        if prior_high and prior_high > cp:
            t1 = prior_high
        else:
            t1 = cp * 1.06
        t2 = cp * 1.10
    risk = abs((emin + emax) / 2 - sl)
    reward = abs(t1 - (emin + emax) / 2)
    srr = abs(cp - lh1) / abs(lh2 - cp) if lh1 and lh2 and cp else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=round(reward / risk, 2) if risk else 0,
                      structure_rr=round(srr, 2),
                      price_source="system:current_price_based+LH_points" if lh1 and lh2 else "system:current_price_based"),
                 "LH_points", dict(LH1=lh1, LH2=lh2))


def _tr_fade(cp, dr, se):
    rh = se.get("range_high", se.get("trading_range_high", 0))
    rl = se.get("range_low", se.get("trading_range_low", 0))
    if rh and rl:
        if dr == "long":
            emin, emax = rl * 1.01, cp * 1.01
            sl = rl * 0.98
            t1, t2 = (rh + rl) / 2, rh
        else:
            emin, emax = cp * 0.99, rh * 0.99
            sl = rh * 1.02
            t1, t2 = (rh + rl) / 2, rl
        src = "system:range_high_low_based"
    else:
        emin, emax = cp * 0.99, cp * 1.01
        sl = cp * 0.93 if dr == "long" else cp * 1.07
        t1 = cp * 1.06 if dr == "long" else cp * 0.94
        t2 = cp * 1.10 if dr == "long" else cp * 0.90
        src = "system:current_price_based(norange)"
    risk = abs(sl - (emin + emax) / 2)
    reward = abs(t1 - (emin + emax) / 2) if t1 else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=round(reward / risk, 2) if risk else 0,
                      structure_rr=abs(rh - cp) / abs(cp - rl) if rh and rl and cp else 0,
                      price_source=src),
                 "range_bounds", dict(range_high=rh, range_low=rl))


def _wedge(cp, dr, se):
    p1 = se.get("push_1", se.get("push_1_price", 0))
    p2 = se.get("push_2", se.get("push_2_price", 0))
    p3 = se.get("push_3", se.get("push_3_price", 0))
    if not p1 or not p2 or not p3:
        return _insufficient("wedge push_1/2/3 missing")
    if se.get("push_3_confirmed") is False:
        return _insufficient("wedge push_3 unconfirmed")

    p1, p2, p3 = float(p1), float(p2), float(p3)
    wedge_extreme = se.get("wedge_extreme", 0)
    wedge_start = se.get("wedge_start", 0)

    if dr == "short":
        extreme = float(wedge_extreme) if wedge_extreme else max(p1, p2, p3)
        target = float(wedge_start) if wedge_start else min(p1, p2, p3)
        buffer = max(abs(extreme - target) * 0.05, extreme * 0.01)
        sl = max(extreme + buffer, extreme * 1.02)
        entry_mid = p3
        emin = max(target, entry_mid - buffer * 0.5)
        emax = min(sl - buffer * 0.1, entry_mid + buffer * 0.25)
        if emax < emin:
            emin = emax = entry_mid
        t1 = target
        t2 = max(0, target - abs(extreme - target) * 0.5)
    else:
        extreme = float(wedge_extreme) if wedge_extreme else min(p1, p2, p3)
        target = float(wedge_start) if wedge_start else max(p1, p2, p3)
        buffer = max(abs(target - extreme) * 0.05, extreme * 0.01)
        sl = min(extreme - buffer, extreme * 0.98)
        entry_mid = p3
        emin = max(sl + buffer * 0.1, entry_mid - buffer * 0.25)
        emax = min(target, entry_mid + buffer * 0.5)
        if emax < emin:
            emin = emax = entry_mid
        t1 = target
        t2 = target + abs(target - extreme) * 0.5

    entry_mid = (emin + emax) / 2
    risk = abs(sl - entry_mid)
    reward = abs(t1 - entry_mid) if t1 else 0
    rr = round(reward / risk, 2) if risk else 0
    rr = min(rr, 10.0)
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=rr, structure_rr=rr,
                      price_source="system:wedge_push_based"),
                 "wedge_pushes",
                 dict(push_1=p1, push_2=p2, push_3=p3,
                      wedge_extreme=extreme, wedge_start=target))


def _measured_move(cp, dr, se):
    ms = se.get("measure_start", 0)
    me = se.get("measure_end", 0)
    bp = se.get("breakout_point", 0)
    if not ms or not me:
        return _generic(cp, dr, se)
    move = se.get("measured_distance", 0) or abs(me - ms)
    projected = se.get("projected_target", 0)
    emin, emax = cp * 0.99, cp * 1.01
    if dr == "long":
        sl = bp * 0.98 if bp else cp * 0.95
        t2 = projected if projected else ((bp or cp) + move)
        t1 = cp + abs(t2 - cp) * 0.5
    else:
        sl = bp * 1.02 if bp else cp * 1.05
        t2 = projected if projected else ((bp or cp) - move)
        t1 = cp - abs(cp - t2) * 0.5
    risk = abs(sl - (emin + emax) / 2)
    reward = abs(t1 - (emin + emax) / 2) if t1 else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=round(reward / risk, 2) if risk else 0,
                      structure_rr=round(move / risk, 2) if risk else 0,
                      price_source="system:measured_move_target_engine"),
                 "measured_move_points",
                 dict(measure_start=ms, measure_end=me, breakout_point=bp,
                      measured_distance=move, projected_target=t2))


def _double_bottom(cp, dr, se):
    b1 = se.get("bottom_1", se.get("bottom_1_price", 0))
    b2 = se.get("bottom_2", se.get("bottom_2_price", 0))
    neckline = se.get("neckline", se.get("breakout_point", 0))
    height = se.get("pattern_height", 0)
    if not b1 or not b2 or not neckline:
        return _insufficient("double_bottom bottom_1/bottom_2/neckline missing")
    floor = min(float(b1), float(b2))
    neckline = float(neckline)
    height = float(height) if height else neckline - floor
    if height <= 0:
        return _insufficient("double_bottom pattern_height invalid")
    target = se.get("projected_target", 0) or neckline + height
    buffer = max(height * 0.1, floor * 0.01)
    emin, emax = cp * 0.99, cp * 1.01
    sl = floor - buffer
    t1 = float(target)
    t2 = float(target) + height * 0.5
    risk = abs(sl - (emin + emax) / 2)
    reward = abs(t1 - (emin + emax) / 2)
    rr = round(reward / risk, 2) if risk else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=rr, structure_rr=rr,
                      price_source="system:double_bottom_neckline_target"),
                 "double_bottom_points",
                 dict(bottom_1=b1, bottom_2=b2, neckline=neckline,
                      pattern_height=height, projected_target=target))


def _double_top(cp, dr, se):
    t1p = se.get("top_1", se.get("top_1_price", 0))
    t2p = se.get("top_2", se.get("top_2_price", 0))
    neckline = se.get("neckline", se.get("breakdown_point", 0))
    height = se.get("pattern_height", 0)
    if not t1p or not t2p or not neckline:
        return _insufficient("double_top top_1/top_2/neckline missing")
    ceiling = max(float(t1p), float(t2p))
    neckline = float(neckline)
    height = float(height) if height else ceiling - neckline
    if height <= 0:
        return _insufficient("double_top pattern_height invalid")
    target = se.get("projected_target", 0) or neckline - height
    buffer = max(height * 0.1, ceiling * 0.01)
    emin, emax = cp * 0.99, cp * 1.01
    sl = ceiling + buffer
    t1 = float(target)
    t2 = max(0, float(target) - height * 0.5)
    risk = abs(sl - (emin + emax) / 2)
    reward = abs(t1 - (emin + emax) / 2)
    rr = round(reward / risk, 2) if risk else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=rr, structure_rr=rr,
                      price_source="system:double_top_neckline_target"),
                 "double_top_points",
                 dict(top_1=t1p, top_2=t2p, neckline=neckline,
                      pattern_height=height, projected_target=target))


def _generic(cp, dr, se):
    emin, emax = cp * 0.99, cp * 1.01
    sl = cp * 0.93 if dr == "long" else cp * 1.07
    t1 = cp * 1.06 if dr == "long" else cp * 0.94
    t2 = cp * 1.10 if dr == "long" else cp * 0.90
    risk = abs(sl - (emin + emax) / 2)
    reward = abs(t1 - (emin + emax) / 2) if t1 else 0
    return _wrap(dict(entry_min=round(emin, 2), entry_max=round(emax, 2),
                      stop_loss=round(sl, 2), tp1=round(t1, 2), tp2=round(t2, 2),
                      execution_rr=round(reward / risk, 2) if risk else 0,
                      structure_rr=0,
                      price_source="system:current_price_based(fallback)"),
                 "current_price_fallback", {})
