"""Jodo Fee-Collection Lab (simulated data). Reconciliation engine, collection funnel, unit economics, AOP tracker."""
import numpy as np, pandas as pd, duckdb, json
rng=np.random.default_rng(7)
def make(n_students=20000):
    schools=pd.DataFrame({'school_id':range(120),'city':rng.choice(['Bengaluru','Hyderabad','Pune','Chennai','Kolkata'],120),
        'tier':rng.choice(['A','B','C'],120,p=[.3,.45,.25])})
    st=pd.DataFrame({'student_id':range(n_students),'school_id':rng.integers(0,120,n_students)}).merge(schools)
    fee=np.where(st.tier=='A',180000,np.where(st.tier=='B',90000,45000))*rng.uniform(.8,1.2,n_students)
    st['annual_fee']=fee.round(-2); st['plan']=rng.choice([1,3,6,12],n_students,p=[.35,.25,.25,.15])
    rows=[]
    for r in st.itertuples():
        amt=round(r.annual_fee/r.plan)
        for k in range(r.plan):
            p_miss=.03+.04*(r.plan==12)+.03*(r.tier=='C')
            rows.append((r.student_id,r.school_id,k,amt,rng.random()<p_miss))
    inst=pd.DataFrame(rows,columns=['student_id','school_id','inst_no','amount','missed'])
    inst['txn_id']=['T%07d'%i for i in range(len(inst))]
    return st,inst
def bank_feed(inst):
    paid=inst[~inst.missed].copy()
    b=pd.DataFrame({'bank_ref':paid.txn_id.values,'amount':paid.amount.values.astype(float)})
    idx=rng.choice(len(b),400,replace=False); kinds=np.array(['amount','dup','missing','reftypo'])[np.arange(400)%4]
    inj=[]
    for i,k in zip(idx,kinds):
        if k=='amount': b.loc[i,'amount']+=rng.choice([-500,-100,100,250])
        elif k=='reftypo': b.loc[i,'bank_ref']=b.loc[i,'bank_ref'].replace('T','T ',1)
        inj.append((b.loc[i,'bank_ref'].replace(' ',''),k))
    dup=b.iloc[idx[kinds=='dup']]; b=pd.concat([b,dup]); miss=set(b.iloc[idx[kinds=='missing']].bank_ref)
    b=b[~b.bank_ref.isin(miss)]
    return b.reset_index(drop=True),pd.DataFrame(inj,columns=['txn_id','kind'])
def reconcile(ledger,bank):
    bank=bank.assign(ref=bank.bank_ref.str.replace(' ','',regex=False))
    q="""with b as (select ref, count(*) n, sum(amount) amt, max(amount) one from bank group by ref)
    select l.txn_id, case when b.ref is null then 'missing' when b.n>1 then 'dup' when abs(b.one-l.amount)>0.5 then 'amount' else 'ok' end status
    from ledger l left join b on l.txn_id=b.ref"""
    return duckdb.sql(q).df()
def main():
    st,inst=make(); led=inst[~inst.missed][['txn_id','amount']]
    bank,inj=bank_feed(inst); rec=reconcile(led,bank); br=rec[rec.status!='ok']
    real=inj[inj.kind!='reftypo']; caught=real.txn_id.isin(br.txn_id).mean(); false=(~br.txn_id.isin(real.txn_id)).sum()
    automatched=int((~inj[inj.kind=='reftypo'].txn_id.isin(br.txn_id)).sum())
    miss=inst.groupby('student_id').missed.any().rename('any_miss').reset_index().merge(st)
    by_plan=miss.groupby('plan').any_miss.mean().round(3)
    # unit economics per student-year: MDR 1.5% income from school, 8% annual cost of funds on avg float, 1.2% credit loss on missed
    st['revenue']=st.annual_fee*.015+st.annual_fee*.06*(st.plan>1)
    st['cof']=st.annual_fee*.08*(st.plan-1)/(2*st.plan)
    lost=inst[inst.missed].groupby('student_id').amount.sum()
    st['credit_loss']=st.student_id.map(lost).fillna(0)*.35
    st['contribution']=st.revenue-st.cof-st.credit_loss
    ue=st.groupby('plan')[['revenue','cof','credit_loss','contribution']].mean().round(0)
    aop=pd.DataFrame({'month':range(1,13)}); aop['plan_cr']=np.linspace(12,20,12).round(1)
    aop['actual_cr']=(aop.plan_cr*rng.normal(.97,.06,12)).round(1); aop['var_pct']=((aop.actual_cr/aop.plan_cr-1)*100).round(1)
    out={'students':len(st),'installments':len(inst),'breaks_injected':len(real),'ref_typos_automatched':automatched,'caught_pct':round(caught*100,1),'false_alarms':int(false),
         'miss_rate_by_plan':by_plan.to_dict(),'unit_econ_by_plan':ue.to_dict('index'),'aop_months_below_95pct':int((aop.var_pct<-5).sum())}
    print(json.dumps(out,indent=1,default=str)); return out
if __name__=='__main__': main()
