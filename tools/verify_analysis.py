"""Independent algebraic checks and raw-data reconciliation for the new topics."""
import csv
import hashlib
import json
from pathlib import Path
import math
import numpy as np
import mpmath as mp
import stats_core as S

ROOT=Path(__file__).resolve().parents[1];checks=[]
def check(label,value):
    assert value,label
    checks.append(label)

def assumption_checks(tag,r,z,rows,residual,q):
    normality=r['assumptions']['normality']
    samples=[z['group_0'],z['group_1'],residual]
    if 'spearman' in r:samples.extend([z['x'],z['y']])
    check(tag+'normality covers both groups, residuals and correlation inputs',
          len(normality)==len(samples) and all(v['n']>2000 for v in normality.values()))
    for (label,record),values in zip(normality.items(),samples):
        # Independent summation and the closed-form chi-square(2) survival.
        values=list(map(float,values));n=len(values);mean=math.fsum(values)/n
        moments={k:math.fsum((v-mean)**k for v in values)/n for k in [2,3,4]}
        skew=moments[3]/moments[2]**1.5;excess=moments[4]/moments[2]**2-3
        jb=n*(skew*skew/6+excess*excess/24)
        check(tag+label+' independently summed normality statistic',
              record['n']==n and record['df']==2 and math.isclose(jb,record['statistic'],rel_tol=1e-9)
              and math.isclose(skew,record['skewness'],abs_tol=1e-9)
              and math.isclose(excess,record['excess_kurtosis'],abs_tol=1e-9))
        expected_p=mp.exp(-mp.mpf(jb)/2)
        check(tag+label+' normality p from exponential survival',
              abs(mp.mpf(record['p'])/expected_p-1)<mp.mpf('1e-7'))
    deviations=[np.abs(values-np.median(values)) for values in samples[:2]]
    grand=math.fsum(float(v) for group in deviations for v in group)/sum(map(len,deviations))
    between=sum(len(group)*(group.mean()-grand)**2 for group in deviations)
    within=sum(math.fsum(float(v-group.mean())**2 for v in group) for group in deviations)
    df=sum(map(len,deviations))-2;statistic=between/(within/df);bf=r['brown_forsythe']
    check(tag+'Brown-Forsythe via absolute-deviation ANOVA',
          bf['df1']==1 and bf['df2']==df and math.isclose(statistic,bf['F'],rel_tol=1e-10)
          and math.isclose(float(S.t_p(math.sqrt(statistic),df)),float(bf['p']),rel_tol=1e-9))
    squared=residual**2;fitted=q@(q.T@squared)
    lm=len(squared)*(1-float(np.sum((squared-fitted)**2)/np.sum((squared-squared.mean())**2)))
    check(tag+'Koenker diagnostic from independent QR auxiliary regression',
          math.isclose(lm,r['adjusted']['diagnostics']['koenker_LM'],abs_tol=1e-7))
    if r['variant']==1:
        group_rows=[row for row in rows if row['mean_pulse_bpm'] and row['sedentary_minutes_day']]
        groups=[[row for row in group_rows if (float(row['sedentary_minutes_day'])<480)==low] for low in [True,False]]
        pair_rows=group_rows
    else:
        column='haemoglobin_g_dl' if r['variant']==2 else 'arm_circumference_cm'
        group_rows=[row for row in rows if row[column] and row['sex'] and (r['variant']==3 or row['age_years'])]
        groups=[[row for row in group_rows if row['sex']==sex] for sex in ['Female','Male']]
        pair_rows=[row for row in rows if row['arm_circumference_cm'] and row['weight_kg']]
    audit=r['assumptions']['independence'];ids=[{row['participant_id'] for row in group} for group in groups]
    expected_samples={'Source dataset':rows,'Group comparison':group_rows,
                      'Primary regression':[row for row in rows if all(row[c] for c in r['missingness'])]}
    if 'spearman' in r:expected_samples['Spearman complete pairs']=pair_rows
    check(tag+'independence audit reconciles all raw-data sample IDs',
          audit['samples']=={name:{'records':len(sample),'unique_ids':len({row['participant_id'] for row in sample})}
                             for name,sample in expected_samples.items()})
    check(tag+'unpaired group IDs are disjoint and counted once',
          audit['overlapping_group_ids']==len(ids[0]&ids[1])==0
          and list(audit['group_unique_ids'].values())==list(map(len,ids))
          and all(len(group)==len(unique) for group,unique in zip(groups,ids)))
    design=[c for c in rows[0] if any(term in c.lower() for term in ['psu','strat','cluster','household'])]
    check(tag+'survey independence is explicitly unverified',
          audit['available_cluster_or_stratum_columns']==design==[]
          and audit['survey_independence_verified'] is False)
    selection=r['assumptions']['method_selection']
    check(tag+'one correlation method and unchanged mean-difference estimand',
          selection['bivariate_correlation']==('Spearman only' if 'spearman' in r else 'Not part of the research questions')
          and selection['group_comparison'].startswith('Welch t-test:')
          and selection['normality_pretest_switching'] is False and 'pearson' not in r)

def main():
    source=ROOT/'data'/'NHANES_BME_student - NHANES_BME_student.csv'
    check('Original participant CSV unchanged',hashlib.sha256(source.read_bytes()).hexdigest()=='ee2bd4d6bccb4860967fbb1cf7d4af510a5ebfddd4911fe6d0cd155738cd8c09')
    codebook=ROOT/'data'/'NHANES_BME_codebook - NHANES_BME_codebook.csv'
    check('Original codebook unchanged',hashlib.sha256(codebook.read_bytes()).hexdigest()=='1653074b1b5c721ce74511da21fe658c0ff62caa000ed980f1ee051af911920b')
    with source.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    check('Unique 8153 participant IDs',len(rows)==len({x['participant_id'] for x in rows})==8153)
    check('Student t tail equals Cauchy tail at df 1',abs(S.t_p(1,1)-.5)<1e-12)
    check('Independent F(2,10) closed-form tail',abs(S.f_p(3,2,10)-(10/16)**5)<1e-12)
    forbidden=[{'bmi_kg_m2','mean_systolic_bp_mmHg'},{'diagnosed_hypertension','mean_systolic_bp_mmHg'},
       {'diabetes_status','hba1c_percent'},{'waist_cm','hba1c_percent'},{'smoking_status','hdl_mg_dl'},
       {'smoking_status','diagnosed_hypertension'}]
    summaries=[]
    for folder in sorted((ROOT/'reports'/'group16').glob('variant_*')):
        r=json.loads((folder/'results.json').read_text(encoding='utf-8'));z=np.load(folder/'plot_data.npz')
        tag=folder.name+': '
        check(tag+'three non-example research questions',len(r['config']['questions'])==3 and all(set(p) not in forbidden for p in r['config']['primary_pairs']))
        X,y=z['X'],z['model_y'];q,upper=np.linalg.qr(X,mode='reduced')
        beta=np.linalg.solve(upper,q.T@y);expected=np.array([c['beta'] for c in r['adjusted']['coefficients']])
        check(tag+'independent QR regression coefficients',np.allclose(beta,expected,rtol=1e-10,atol=1e-10))
        residual=y-X@beta;h=np.sum(q*q,axis=1);pinv=np.linalg.pinv(X)
        changes=pinv*(residual/(1-h))[None,:];se=np.sqrt(np.sum(changes*changes,axis=1))
        check(tag+'HC3 from delete-one changes',np.allclose(se,[c['se'] for c in r['adjusted']['coefficients']],rtol=1e-9))
        check(tag+'residuals and plot reconstruction',np.allclose(residual,z['residual'],atol=1e-9))
        for i in np.linspace(0,len(y)-1,8,dtype=int):
            keep=np.arange(len(y))!=i
            refit=np.linalg.lstsq(X[keep],y[keep],rcond=None)[0]
            assert np.allclose(beta-refit,changes[:,i],atol=1e-9)
        check(tag+'actual leave-one-out refits',True)
        used={int(x) for x in z['participant_ids']}
        needed=list(r['missingness'])
        expected_ids={int(x['participant_id']) for x in rows if all(x[c] for c in needed)}
        check(tag+'regression complete cases from raw CSV',used==expected_ids and len(y)==len(expected_ids))
        check(tag+'missingness reconciled',all(v['observed_n']==sum(bool(x[c]) for x in rows) for c,v in r['missingness'].items()))
        check(tag+'selection denominators',r['selection']['included']['n']+r['selection']['excluded']['n']==8153)
        lo,hi=z['group_0'],z['group_1'];v=hi.var(ddof=1)/len(hi)+lo.var(ddof=1)/len(lo)
        statistic=(hi.mean()-lo.mean())/math.sqrt(v)
        check(tag+'Welch mean difference and statistic',abs(r['welch']['difference']-(hi.mean()-lo.mean()))<1e-12 and abs(r['welch']['t']-statistic)<1e-12)
        check(tag+'Welch CI from independent SE',abs((r['welch']['ci'][1]-r['welch']['difference'])/math.sqrt(v)-S.t_critical(r['welch']['df']))<1e-10)
        if 'spearman' in r:
            def rank(v):
                unique,counts=np.unique(v,return_counts=True);mapping=dict(zip(unique,np.cumsum(counts)-(counts-1)/2))
                return np.array([mapping[x] for x in v])
            rho=np.corrcoef(rank(z['x']),rank(z['y']))[0,1]
            check(tag+'independent tied ranks',abs(rho-r['spearman']['rho'])<1e-12)
            check(tag+'bootstrap CI and resampling count',r['spearman']['ci'][0]<rho<r['spearman']['ci'][1] and r['spearman']['resamples']==2000)
        else:
            # Each sex-specific slope also equals a separate group's regression.
            for val,sex in [(0,'Female'),(1,'Male')]:
                keep=z['sex']==val
                standalone=np.linalg.lstsq(X[keep,:2],y[keep],rcond=None)[0]
                check(tag+sex+' slope from independent stratified fit',abs(standalone[1]-r['age_slopes'][sex]['estimate'])<1e-12)
            cov=changes@changes.T;ix=[1,3];test=beta[ix]@np.linalg.solve(cov[np.ix_(ix,ix)],beta[ix])/2
            check(tag+'independent joint age Wald test',abs(test-r['age_joint']['F'])<1e-8)
        for c in r['adjusted']['coefficients']:
            assert 0<mp.mpf(c['p'])<=1 and c['ci'][0]<c['beta']<c['ci'][1]
        check(tag+'nonzero p-values and valid coefficient CIs',True)
        p=[mp.mpf(t['p']) for t in r['primary_tests']];order=sorted(range(3),key=lambda k:p[k])
        expected_holm={};running=mp.mpf(0)
        for j,k in enumerate(order):
            running=min(mp.mpf(1),max(running,(3-j)*p[k]));expected_holm[k]=running
        check(tag+'Holm adjustment including tiny tails',all(abs(mp.mpf(t['holm_p'])/expected_holm[i]-1)<mp.mpf('1e-10') for i,t in enumerate(r['primary_tests'])))
        check(tag+'analysis plan matches result provenance',r['plan_sha256']==hashlib.sha256((ROOT/'ANALYSIS_PLAN.md').read_bytes()).hexdigest())
        assumption_checks(tag,r,z,rows,residual,q)
        summaries.append({'variant':folder.name,'questions':r['config']['questions'],'n':len(y),'result_sha256':hashlib.sha256((folder/'results.json').read_bytes()).hexdigest()})
    output={'passed':len(checks),'checks':checks,'reports':summaries,'independent_checks':'QR, actual leave-one-out refits, HC3 deletion identity, raw CSV reconciliation, independently summed normality moments, exponential chi-square(2) survival, absolute-deviation ANOVA and ID overlap audits.'}
    assert len(summaries)==3 and len(checks)==98
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'numerical_validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(checks)} numerical, data and topic checks.')

if __name__=='__main__':main()
