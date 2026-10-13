import json, subprocess, sys, shutil, os
from pathlib import Path
from datetime import datetime, date, time, timedelta
from dataclasses import replace
from pal.data.bars import Bar
from pal.data.calendar import TZ, TradingCalendar
from pal.pipeline.orchestrator import SessionOrchestrator, OrchestratorConfig, ArmedSetup, PositionPlan
from pal.pipeline.event_store import EventStore, replay_events
from pal.signals.engine import EngineConfig
from pal.ledger.positions import AccountLedger
from pal.execution.market_rules import MAIN_BOARD
from pal.selection.providers import Candidate
from pal.research.acceptance_pack import breakout_bars, build_pack, write_bar_jsonl
from pal.research.backtest_runner import BacktestDay, BacktestRunner

OUT=Path('review5_evidence'); OUT.mkdir(exist_ok=True)
IID='SSE.600519'; T=datetime(2026,10,13,10,0,tzinfo=TZ)
def bar(t=T,o=10,h=10.5,l=9.8,c=10.2,v=100000):
    return Bar(IID,'30m',t,t+timedelta(minutes=30),t+timedelta(minutes=30),o,h,l,c,v)
def qnew(store=None):
    return SessionOrchestrator(OrchestratorConfig(EngineConfig('r5',enabled_families=('breakout',))),AccountLedger(1_000_000),store=store)
def arm(q,sid='s',entry=10,stop=9,target=12):
    q.armed[sid]=ArmedSetup(sid,IID,'breakout',entry,stop,target,T-timedelta(minutes=30))
def cli(*args):
    p=subprocess.run([sys.executable,'src/pal_cli.py',*map(str,args)],capture_output=True,text=True,env=dict(os.environ,PYTHONPATH='src'))
    return {'exit':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()[-300:]}
out={}
# V02: future daily must not change past regime gate
bs=breakout_bars(); sig=bs[21]; hist=bs[:21]
at=sig.bar_start.replace(hour=0,minute=0)
cand=Candidate('c',IID,('static_pool',),at,at,None)
future=[]
for i in range(60):
    s=datetime(2026,11,1,9,30,tzinfo=TZ)+timedelta(days=i); e=s.replace(hour=15,minute=0)
    future.append(Bar(IID,'1d',s,e,e,10,10.1,9.9,10,100000))
a=qnew(); b=qnew()
out['V02_past_without_future']=a.on_bar(IID,sig,hist,[],cand)
out['V02_past_with_future_daily']=b.on_bar(IID,sig,hist,future,cand)
# V03: chunked == whole
GEN=OUT/'generated_pack'
build_pack(str(GEN))
import pal_cli
si=pal_cli._load_snapshot(str(GEN))
days=[]
for d in sorted({b.bar_start.date() for b in si['bars']}):
    bars=tuple(b for b in si['bars'] if b.bar_start.date()==d)
    atd=datetime.combine(d,time(0),tzinfo=TZ)
    cands=tuple(Candidate(f'{i}-{d}',i,('static_pool',),atd,atd,None) for i in si['manifest']['instruments'])
    days.append(BacktestDay(d,bars,tuple(si['daily']),cands))
cal=TradingCalendar(tuple(date.fromisoformat(x) for x in si['manifest']['trading_days']),'r5')
cfg=OrchestratorConfig(EngineConfig('r5'),calendar=cal)
whole=BacktestRunner(cfg, 1_000_000).run(days)
runner=BacktestRunner(cfg, 1_000_000); ev=[]
for d in days: ev+=runner.run([d]).events
out['V03_whole_vs_incremental']={'whole_events':[e for e in whole.events if 'setup_' in e or 'FILL' in e or 'EXIT' in e],'whole_cash':whole.final_cash,'incremental_same':[e for e in ev if 'setup_' in e or 'FILL' in e or 'EXIT' in e],'incremental_cash':runner.ledger.cash}
# V06: fill write failure -> zero half-state
class FailingStore(EventStore):
    def append(self,kind,payload,ts=''):
        if kind=='fill': raise OSError('injected fill write failure')
        return super().append(kind,payload,ts)
es=FailingStore(); q=qnew(es); arm(q)
try: q.on_bar(IID,bar(),[],[],None)
except Exception as e: out['V06_write_failure']=str(e)
out['V06_after_failure']={'cash':q.ledger.cash,'qty':q.ledger.positions.total_qty(IID),'stored_fills':len(es.by_kind('fill')),'consumed':len(q._consumed_bars)}
# V05/V04: paper restart with open position
state=OUT/'paper_open_recovery'
if state.exists(): shutil.rmtree(state)
state.mkdir()
es=EventStore(str(state/'events.jsonl')); q=qnew(es); arm(q)
q.on_bar(IID,bar(),[],[],None)
out['V05_before_restart']={'cash':q.ledger.cash,'qty':q.ledger.positions.total_qty(IID)}
bnext=bar(t=T+timedelta(days=1),o=8.5,h=8.8,l=8,c=8.2,v=1000000)
fp=OUT/'next_day.jsonl'; write_bar_jsonl(str(fp),[bnext])
out['V05_paper_restart']=cli('paper','--events',fp,'--state',state)
out['V05_recovered_ledger']=json.loads((state/'ledger_snapshot.json').read_text())
es2=EventStore(str(state/'events.jsonl')); st=replay_events(es2.events())
out['V05_event_replay']={'cash':st.cash,'positions':st.positions,'session_init_count':len(es2.by_kind('session_init'))}
out['V05_reconcile']=cli('reconcile','--run',state)
# V07: multi-lot no cross-batch sell
q=qnew()
q.ledger.buy(IID,100,10,date(2026,10,12),MAIN_BOARD,date(2026,10,13))
q.ledger.buy(IID,100,10,date(2026,10,13),MAIN_BOARD,date(2026,10,14))
q.position_plans[IID]=[
    PositionPlan(IID,'old',10,8,20,date(2026,10,12),100),
    PositionPlan(IID,'new',10,9.5,20,date(2026,10,13),100)]
out['V07_lot_exit_events']=q.on_bar(IID,bar(o=9.6,h=10,l=9,c=9.7),[],[],None)
out['V07_remaining']={'lots':[(l.qty,str(l.acquired_date)) for l in q.ledger.positions._lots[IID]],
                      'plans':[p.setup_id for p in (q.position_plans[IID] if isinstance(q.position_plans[IID],list) else [q.position_plans[IID]])]}
# V09: missing declared file rejected
cop=OUT/'missing_input_pack'
if cop.exists(): shutil.rmtree(cop)
shutil.copytree(GEN,cop)
(cop/'daily_SSE_600519.jsonl').unlink()
try:
    pal_cli._load_snapshot(str(cop)); out['V09_missing_file']='ACCEPTED'
except BaseException as e: out['V09_missing_file']=repr(e)[:80]
# V08: scan three states
scan_out=OUT/'scan'
out['V08_scan']=cli('scan','--snapshot',GEN,'--out',scan_out)
out['V08_scan_summary']=json.loads((scan_out/'daily_plan.json').read_text())['summary']
# V01: pack hash passes on clean checkout (this script regenerates: LF bytes)
out['V01_pack_manifest_ok']=all(
    __import__('hashlib').sha256(open(GEN/f,'rb').read()).hexdigest()==h
    for f,h in json.loads((GEN/'manifest.json').read_text())['file_sha256'].items())
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
(OUT/'review5_results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str))
