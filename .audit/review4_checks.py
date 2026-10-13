import json, subprocess, sys
from pathlib import Path
from dataclasses import replace, asdict
from datetime import date, datetime, time, timedelta
from pal.data.bars import Bar, resample_30m_to_daily
from pal.data.calendar import TZ, TradingCalendar
from pal.pipeline.orchestrator import SessionOrchestrator, OrchestratorConfig, ArmedSetup
from pal.pipeline.event_store import EventStore, replay_events
from pal.signals.engine import DecisionEngine, EngineConfig
from pal.context.regime import RegimeKind, assess_trend_regime
from pal.ledger.positions import AccountLedger
from pal.execution.market_rules import MAIN_BOARD
from pal.portfolio.allocator import PortfolioAllocator, AllocationRequest
from pal.portfolio.risk import PaperDefaults
from pal.selection.providers import Candidate
from pal.research.backtest_runner import BacktestDay, BacktestRunner

OUT=Path('review4_evidence'); OUT.mkdir(exist_ok=True)
IID='SSE.600519'; B='SZSE.000001'
CAL=TradingCalendar(tuple(date(2026,10,d) for d in (13,14,15,16)), 'review4-fixture')
starts=[s for d in CAL.trading_days for s,e in CAL.bars_for_day(d)]
T=starts[0]
def bar(t=T,o=10,h=10.5,l=9.8,c=10.2,v=100000,iid=IID):
    return Bar(iid,'30m',t,t+timedelta(minutes=30),t+timedelta(minutes=30),o,h,l,c,v)
def orch(cal=CAL):
    return SessionOrchestrator(OrchestratorConfig(EngineConfig('review4',enabled_families=('breakout',)),calendar=cal),AccountLedger(1_000_000))
def arm(q, sid='s',iid=IID,entry=10,stop=9,target=12,at=T-timedelta(minutes=30)):
    q.armed[sid]=ArmedSetup(sid,iid,'breakout',entry,stop,target,at)
def attempt(f):
    try: return f()
    except Exception as e: return {'error':type(e).__name__,'message':str(e)}
out={}
hist=[bar(t=starts[i],o=9.5,h=10,l=9,c=9.6) for i in range(21)]
sig=bar(t=starts[21],o=9.9,h=11,l=9.7,c=10.9)
daily=[]
d=date(2026,10,12)
while len(daily)<60:
    if d.weekday()<5:
        s=datetime.combine(d,time(9,30),tzinfo=TZ); e=datetime.combine(d,time(15),tzinfo=TZ)
        daily.append(Bar(IID,'1d',s,e,e,10,10.1,9.9,10,100000))
    d-=timedelta(days=1)
daily.reverse()
cand=Candidate('c',IID,('static_pool',),starts[16],starts[16],None)
out['context_kind']=assess_trend_regime(daily).kind.value
qe=orch(); qa=orch()
out['explicit_regime']=qe.on_bar(IID,sig,hist,daily,cand,RegimeKind.RANGE)
out['automatic_regime']=qa.on_bar(IID,sig,hist,daily,cand)
out['automatic_internal_setups']=[{'id':s.setup_id,'state':s.state.value} for s in qa.engine.book.active_setups()]
out['automatic_external_armed']=list(qa.armed)
follow=bar(t=starts[22],o=10.2,h=10.4,l=9.6,c=9.8)
out['failed_follow_still_fills']=qe.on_bar(IID,follow,hist+[sig],daily,None,RegimeKind.DOWNTREND)
class RecordingEngine(DecisionEngine):
    def __init__(self,cfg): super().__init__(cfg); self.lengths=[]
    def evaluate(self,asof,bars_30m,daily_bars,**kw):
        self.lengths.append(len(bars_30m))
        return super().evaluate(asof,bars_30m,daily_bars,**kw)
cfg=OrchestratorConfig(EngineConfig('review4',enabled_families=('breakout',)),calendar=CAL)
runner=BacktestRunner(cfg, 1_000_000); rec=RecordingEngine(cfg.engine); runner.orch.engine=rec
allbars=hist+[sig]
days=[]
for d in sorted({b.bar_start.date() for b in allbars}):
    at=datetime.combine(d,time(9,30),tzinfo=TZ)
    cd=Candidate(str(d),IID,('static_pool',),at,at,None)
    days.append(BacktestDay(d,tuple(b for b in allbars if b.bar_start.date()==d),tuple(daily),(cd,)))
res=runner.run(days)
out['runner_history']={'total_bars':len(allbars),'max_history_supplied':max(rec.lengths),'events':res.events,'final_nav':res.final_nav}
snap=OUT/'snapshot'; snap.mkdir(exist_ok=True)
(snap/'manifest.json').write_text(json.dumps({'asof_date':'2026-10-15','snapshot_id':'review4-synthetic','calendar_version':'review4-fixture'}))
(snap/'bars_main.jsonl').write_text('\n'.join(json.dumps(asdict(b),default=str) for b in allbars))
cli={}
for cmd in ('scan','backtest'):
    dest=OUT/cmd
    p=subprocess.run([sys.executable,'src/pal_cli.py',cmd,'--snapshot',str(snap),'--out',str(dest)],capture_output=True,text=True)
    cli[cmd]={'exit':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}
cli['scan_summary']=json.loads((OUT/'scan/daily_plan.json').read_text())['summary']
bt=json.loads((OUT/'backtest/backtest.json').read_text())
cli['backtest_values']={k:bt[k] for k in ('n_events','final_nav','final_cash')}
cli['backtest_files']=sorted(p.name for p in (OUT/'backtest').iterdir())
for name,args in [('paper',['paper','--events',str(snap/'bars_main.jsonl'),'--state',str(OUT/'paper')]),('reconcile',['reconcile','--run',str(OUT/'backtest')])]:
    p=subprocess.run([sys.executable,'src/pal_cli.py',*args],capture_output=True,text=True)
    cli[name]={'exit':p.returncode,'stdout':p.stdout.strip()}
out['cli']=cli
q=orch(); q.ledger.buy(IID,100,10,date(2026,10,12),MAIN_BOARD,t1_next_trading_day=date(2026,10,13))
b=bar(iid=B)
out['two_stock_mark_failure']=attempt(lambda:q.on_bar(B,b,[],[],None))
out['retry_failed_bar']=attempt(lambda:q.on_bar(B,b,[],[],None))
out['failed_bar_consumed']=q._bar_key(b) in q._consumed_bars
q=orch(); arm(q)
out['foreign_bar_trigger']=attempt(lambda:q.on_bar(B,b,[],[],None))
out['foreign_bar_bought_A']=q.ledger.positions.total_qty(IID)
q=orch(); arm(q,stop=9.9)
ev=q.on_bar(IID,bar(o=11,h=11.1,l=10.8,c=11),[],[],None)
qty=q.ledger.positions.total_qty(IID)
out['gap_risk']={'events':ev,'qty':qty,'gross':qty*11,'nominal_stop_risk':round(qty*(11-9.9),2),'configured_risk_budget':2500,'configured_position_cap':100000}
q=orch(); arm(q)
ev=q.on_bar(IID,bar(v=2500),[],[],None)
plan=q.position_plans.get(IID)
out['odd_lot_partial']={'events':ev,'qty':q.ledger.positions.total_qty(IID),'lot_size':MAIN_BOARD.lot_size,'order_qty':plan.order.qty,'state':plan.order.state.value,'remaining_setups':list(q.armed)}
q=orch(); arm(q); q.on_bar(IID,bar(),[],[],None)
out['zero_volume_stop_exit']=q.on_bar(IID,bar(t=starts[8],o=8.5,h=8.8,l=8,c=8.2,v=0),[],[],None)
bs=[bar(t=s) for s,e in CAL.bars_for_day(CAL.trading_days[0])]
bs[-1]=replace(bs[-1],available_at=bs[-1].bar_end+timedelta(minutes=7))
agg=resample_30m_to_daily(bs,IID,calendar=CAL)[0]
out['daily_delay']={'last_input_available':str(bs[-1].available_at),'output_available':str(agg.available_at),'final':agg.is_final}
led=AccountLedger(1_000_000)
led.buy('SSE.600001',24000,10,date(2026,10,12),MAIN_BOARD,t1_next_trading_day=date(2026,10,13))
alloc=PortfolioAllocator(); req=AllocationRequest(B,'new',10,9.9,12,industry='same-sector')
r=alloc.allocate([req],led,{'SSE.600001':10,B:10})[0]
out['sector_existing_exposure']={'approved_qty':r.qty,'post_sector_value':240000+r.qty*10,'nav':led.nav({'SSE.600001':10,B:10}),'cap_pct':.25}
small=PortfolioAllocator(replace(PaperDefaults(),max_positions=1))
out['max_position_count']=asdict(small.allocate([req],led,{'SSE.600001':10,B:10})[0])
es=EventStore(); es.append('session_init',{'initial_cash':10000})
payload={'fill_id':'f1','order_id':'o1','side':'buy','qty':100,'price':10,'instrument_id':IID,'commission':5,'sellable_from':'2026-10-14'}
es.append('fill',payload)
out['second_partial_fill']=attempt(lambda:es.append('fill',dict(payload,fill_id='f2')).to_json())
out['recovered_sellable']=replay_events(es.events()).sellable
q=orch(TradingCalendar((date(2026,10,13),),'last-day')); arm(q)
out['end_calendar_failure']=attempt(lambda:q.on_bar(IID,bar(),[],[],None))
q.cfg.calendar=CAL
out['retry_after_calendar_fix']=q.on_bar(IID,bar(),[],[],None)
out['retry_after_calendar_qty']=q.ledger.positions.total_qty(IID)
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
(OUT/'results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str))
