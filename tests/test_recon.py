import sys,os; sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
import run
def test_recon_catches_all():
    o=run.main(); assert o['caught_pct']==100.0 and o['false_alarms']==0
