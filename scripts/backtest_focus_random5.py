# -*- coding: utf-8 -*-
"""
Focus v1 回测：随机5只A股 · 30m · walk-forward
- 信号: Focus v1 新信号面 (H2/L2/breakout/wedge/final_flag/tr_fade 的buy方向)
- A股约束: 只做多(卖信号记为risk-off不交易) + T+1(入场当日不退出)
- 入场: 信号bar收盘检测 → 下一bar开盘价入场
- 止损: 信号bar low - 1 tick (buy)
- 止盈: entry + 2.0×risk (TBTL/registry min_rr对齐)
- 超时: 40 bar (~5交易日, 与信号生命周期一致)
- 同bar同时命中TP/SL: 保守记止损
- 基准: 同期买入持有(策略可评估区间起点买入, 期末收盘)
"""
import sys, os, glob, json, random
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np
from market_analyzer import analyze_market_structure
from signal_predictor import predict_signals

D30 = 'data/market_data/30m'
TICK = 0.01
RR = 2.0
TIMEOUT_BARS = 40
LOOKBACK = 80          # analyze所需最小窗口
SEED = 20261011

# ── 1. 随机抽5只(固定种子可复现) ──
files = sorted(glob.glob(os.path.join(D30, '*.csv')))
random.seed(SEED)
picks = random.sample([os.path.basename(f)[:-4] for f in files], 5)
print(f"随机抽取(seed={SEED}): {picks}\n")

def load(sym):
    df = pd.read_csv(os.path.join(D30, sym + '.csv'))
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)

results = []
fatal_error = False
ERROR_RATE_LIMIT = 0.05   # 单票信号计算错误率超过5% → run=invalid
for sym in picks:
    df = load(sym)
    n = len(df)
    trades = []          # dict(entry_i, entry_px, stop, tp, exit_i, exit_px, exit_reason, sig, bars_held)
    open_trade = None
    sell_signal_days = set()
    signals_seen = {}
    errors_by_type = {}  # [S0-06/F13] 记录信号计算错误，不再静默

    for i in range(LOOKBACK, n - 1):
        window = df.iloc[:i+1]
        # ── 持仓管理(在信号检测前先处理出场) ──
        if open_trade is not None:
            bar = df.iloc[i]
            entry_date = df.iloc[open_trade['entry_i']]['date']
            can_exit = bar['date'].date() > entry_date.date()   # T+1
            if can_exit:
                if bar['low'] <= open_trade['stop']:            # 保守: 先查止损
                    open_trade.update(exit_i=i, exit_px=open_trade['stop'], exit_reason='stop')
                    trades.append(open_trade); open_trade = None
                elif bar['high'] >= open_trade['tp']:
                    open_trade.update(exit_i=i, exit_px=open_trade['tp'], exit_reason='tp')
                    trades.append(open_trade); open_trade = None
                elif i - open_trade['entry_i'] >= TIMEOUT_BARS:
                    open_trade.update(exit_i=i, exit_px=bar['close'], exit_reason='timeout')
                    trades.append(open_trade); open_trade = None
            continue  # 持仓中不检测新信号

        # ── 信号检测 ──
        # [S0-06/F13] 旧代码 except Exception: continue 会静默吞掉真实错误，
        # 改变样本且不可见。现在：错误计数并记录类型，结束后汇总输出；
        # 单票错误率超阈值时脚本以非零退出码失败（run=invalid 而非静默）。
        try:
            analysis = analyze_market_structure(window)
            preds = predict_signals(window.tail(160).reset_index(drop=True) if len(window) > 160 else window, analysis)
        except Exception as exc:  # noqa: BLE001
            key = f"{type(exc).__name__}: {str(exc)[:80]}"
            errors_by_type[key] = errors_by_type.get(key, 0) + 1
            continue
        buys = [p for p in preds if p.direction == 'buy']
        sells = [p for p in preds if p.direction == 'sell']
        if sells and not buys:
            sell_signal_days.add(str(df.iloc[i]['date'].date()))
        for p in buys + sells:
            signals_seen[p.signal_type] = signals_seen.get(p.signal_type, 0) + 1
        if not buys:
            continue
        best = max(buys, key=lambda p: p.confidence)
        sig_low = float(window.iloc[-1]['low'])
        entry_px = float(df.iloc[i+1]['open'])                 # 下一bar开盘入场
        if entry_px <= sig_low:                                 # 开盘已跌破信号bar低点, 放弃
            continue
        risk = entry_px - (sig_low - TICK)
        if risk <= 0 or risk / entry_px > 0.10:                 # 风险>10%不合理, 弃
            continue
        open_trade = dict(sig=best.signal_type, entry_i=i+1, entry_px=entry_px,
                          stop=sig_low - TICK, tp=entry_px + RR * risk)

    # 收尾: 强平于最后bar收盘
    if open_trade is not None:
        open_trade.update(exit_i=n-1, exit_px=float(df.iloc[-1]['close']), exit_reason='eod')
        trades.append(open_trade)

    # ── 绩效 ──
    pnls = [(t['exit_px'] - t['entry_px']) / (t['entry_px'] - t['stop'] + TICK) if t['exit_reason']=='stop'
            else (t['exit_px'] - t['entry_px']) / ((t['entry_px'] - t['stop']) + TICK) for t in trades]
    # R值统一: 盈亏/初始风险
    rs = []
    for t in trades:
        risk0 = t['entry_px'] - t['stop']
        rs.append((t['exit_px'] - t['entry_px']) / risk0)
    n_win = sum(1 for r in rs if r > 0)
    strat_ret = sum((t['exit_px'] - t['entry_px']) for t in trades) / df.iloc[LOOKBACK]['close']  # 按本金(区间起点价)计的总收益
    bh_ret = (df.iloc[-1]['close'] - df.iloc[LOOKBACK]['close']) / df.iloc[LOOKBACK]['close']

    # [S0-06/F13] 单票错误率检查：超阈值 → run=invalid
    n_evals = max(1, n - 1 - LOOKBACK)
    if errors_by_type:
        err_total = sum(errors_by_type.values())
        err_rate = err_total / n_evals
        print(f"  [{sym}] 信号计算错误 {err_total}/{n_evals} ({err_rate:.1%}): {errors_by_type}")
        if err_rate > ERROR_RATE_LIMIT:
            fatal_error = True
    results.append(dict(sym=sym, trades=len(trades), win=n_win, winrate=n_win/len(trades) if trades else 0,
                        avgR=np.mean(rs) if rs else 0, sumR=sum(rs), strat_ret=strat_ret, bh_ret=bh_ret,
                        signals=signals_seen, sell_days=len(sell_signal_days),
                        detail=[(t['sig'], round(t['entry_px'],2), round(t['exit_px'],2), t['exit_reason']) for t in trades]))

# ── 汇总 ──
print(f"{'股票':8s} {'交易数':>4s} {'胜率':>6s} {'avgR':>6s} {'sumR':>6s} {'策略收益':>8s} {'买入持有':>8s} {'超额':>8s}")
tot_ex = 0
for r in results:
    ex = r['strat_ret'] - r['bh_ret']
    tot_ex += ex
    print(f"{r['sym']:8s} {r['trades']:4d} {r['winrate']:6.0%} {r['avgR']:6.2f} {r['sumR']:6.2f} "
          f"{r['strat_ret']:8.2%} {r['bh_ret']:8.2%} {ex:+8.2%}")
print(f"\n平均超额收益: {tot_ex/len(results):+.2%}")
print("\n每股信号分布与交易明细:")
for r in results:
    print(f"  {r['sym']}: 信号={r['signals']} risk-off天数={r['sell_days']} 交易={r['detail']}")

# ── [S0-06/F13] 错误汇总：信号计算错误不再是静默的 ──
if fatal_error:
    print("\n[INVALID RUN] 存在单票信号计算错误率超 %.0f%% 的股票，本轮结果不可用于结论。" % (ERROR_RATE_LIMIT * 100))
    sys.exit(2)

json.dump(results, open('data/reviews/FOCUS_V1_BACKTEST_RANDOM5_20261011.json','w',encoding='utf-8'),
          ensure_ascii=False, indent=1, default=str)
print("\nsaved -> data/reviews/FOCUS_V1_BACKTEST_RANDOM5_20261011.json")
