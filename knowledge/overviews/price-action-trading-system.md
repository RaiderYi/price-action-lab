# Price Action Trading System Overview

## One-sentence Definition
A complete trading decision system based on Al Brooks Price Action -- from market structure analysis, signal recognition, background scoring to execution and exit.

## System Architecture

```
Layer 1: Market Structure
  - [[brooks-four-step-context]]
  - [[fsm-market-cycle]]
  - [[h2-l2-state-machine]]

Layer 2: Signal Recognition
  - [[brooks-signal-catalog]] (16 signals)
  - [[h1-l1-signal]], [[h2-l2-signal]]
  - [[btc-stc]], [[wedge-signal]], [[tr-fade]]

Layer 3: Scoring & Filtering
  - [[background-scoring-engine]]
  - [[rs-scoring]], [[atr-scaling]]
  - [[background-veto]]

Layer 4: Execution & Risk Control
  - [[trade-management-system]]
  - [[position-sizing]], [[emergency-exit]]
  - [[live-trading-monitor]]
```

## Core Data Sources

| Type | Key Pages |
|------|-----------|
| Core Textbooks | [[book-brooks-trends-revised]], [[book-brooks-trading-ranges]], [[book-brooks-reversals-cn]] |
| System Docs | [[README-summary]], [[article-wg-v15-analysis]], [[article-huangzongprice-live-system-guide]] |
| Course Notes | [[course-1-7-intro]], [[course-notes-8-11-chart-analysis]], [[course-notes-12-18-market-cycle]] |
| Trading Logs | [[journal-mes-daily-reviews]], [[corpus-mes-daily-reviews]] |

## Related Entities

- [[al-brooks]] -- Founder of Price Action methodology
- [[huangzongprice]] -- Author of MES 5-min strategy
- [[lance-beggs]] -- Another price action trader
- [[sam-seiden]] -- Supply/Demand trading

---
*Auto-generated 2026-05-20 | 138 sources + 230 concepts*
