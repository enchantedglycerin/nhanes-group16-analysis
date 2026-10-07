"""Compute the three Group 16 analyses from the supplied teaching data."""
import hashlib
import json
from pathlib import Path
import numpy as np
import stats_core as S
from data_utils import ROWS, SOURCE, subset, arr, male, age, selection, common

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'/'group16'
CONFIG={
 1:{'name':'variant_1_sedentary_pulse','title':['Sedentary time กับ pulse rate','ในผู้ใหญ่'],
 'questions':[
 '1. ผู้ที่มี sedentary time <8 และ ≥8 h/day มี mean pulse rate แตกต่างกันหรือไม่',
 '2. Sedentary time แบบ continuous มี association กับ pulse rate หรือไม่',
 '3. เมื่อปรับ age, sex, BMI และ smoking status แล้ว pulse rate ต่างกันเท่าใดต่อ sedentary time ที่เพิ่มขึ้น 1 h/day'],
 'primary_pairs':[['sedentary_minutes_day','mean_pulse_bpm']]},
 2:{'name':'variant_2_age_sex_haemoglobin','title':['Age และ sex กับ','Haemoglobin ในผู้ใหญ่'],
 'questions':[
 '1. กลุ่ม Male และ Female มี mean haemoglobin แตกต่างกันหรือไม่',
 '2. Age มี association กับ haemoglobin หรือไม่ เมื่อ model รวม sex และ age-by-sex interaction',
 '3. Linear age slope ของ haemoglobin แตกต่างกันระหว่างกลุ่ม Male และ Female หรือไม่'],
 'primary_pairs':[['sex','haemoglobin_g_dl'],['age_years','haemoglobin_g_dl']]},
 3:{'name':'variant_3_arm_body_weight','title':['Arm circumference กับ','Body weight ในผู้ใหญ่'],
 'questions':[
 '1. กลุ่ม Male และ Female มี mean arm circumference แตกต่างกันหรือไม่',
 '2. Arm circumference มี association กับ body weight หรือไม่',
 '3. เมื่อปรับ height, age และ sex แล้ว body weight ต่างกันเท่าใดต่อ arm circumference ที่เพิ่มขึ้น 5 cm'],
 'primary_pairs':[['sex','arm_circumference_cm'],['arm_circumference_cm','weight_kg']]},
}

def initialize(variant,variables,continuous):
    r=common(variables)
    r.update(variant=variant,config=CONFIG[variant],plan_sha256=hashlib.sha256((ROOT/'ANALYSIS_PLAN.md').read_bytes()).hexdigest())
    r['descriptive']={c:S.describe(arr(subset(c),c)) for c in continuous}
    r['data_quality']={'duplicate_ids':len(ROWS)-len({x['participant_id'] for x in ROWS}),
       'outliers_removed':0,'imputation':False,'weights_available':False,'n_age_topcoded_80':sum(x['age_years']=='80' for x in ROWS)}
    return r

def save(r,arrays,primary):
    r['primary_tests']=[{'question':i+1,'test':label,'p':p,'holm_p':hp}
          for i,((label,p),hp) in enumerate(zip(primary,S.holm([p for _,p in primary])))]
    r['adjusted']['residual_rmse']=float(np.sqrt(np.mean(arrays['residual']**2)))
    folder=OUT/r['config']['name'];folder.mkdir(parents=True,exist_ok=True)
    (folder/'results.json').write_text(json.dumps(r,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    np.savez_compressed(folder/'plot_data.npz',**arrays)
    print(r['config']['name'],json.dumps({'n':r['adjusted']['n'],'R2':r['adjusted']['r_squared'],'primary':r['primary_tests']},ensure_ascii=True),flush=True)

def diag_arrays(internal,rows):
    return {'X':internal['X'],'model_y':internal['y'],'fit':internal['fitted'],
        'residual':internal['residual'],'participant_ids':np.array([int(x['participant_id']) for x in rows])}

def topcode_sensitivity(X,y,names,rows):
    keep=arr(rows,'age_years')<80
    model,inside=S.ols(X[keep],y[keep],names)
    return model,inside

def pulse():
    vars=['sedentary_minutes_day','mean_pulse_bpm','age_years','sex','bmi_kg_m2','smoking_status']
    r=initialize(1,vars,[vars[0],vars[1],vars[2],vars[4]])
    pair=subset(*vars[:2]);x=arr(pair,vars[0])/60;y=arr(pair,vars[1])
    low=y[x<8];high=y[x>=8]
    r['groups']={'<8 h/day':S.describe(low),'≥8 h/day':S.describe(high)}
    r['group_label']='Sedentary time';r['group_outcome']='Pulse rate (bpm)'
    r['welch']=S.welch(high,low);r['welch']['contrast']='≥8 minus <8 h/day'
    r['brown_forsythe']=S.brown_forsythe([low,high])
    r['spearman']=S.spearman(x,y,6101)
    rows=subset(*vars);sed=arr(rows,vars[0])/60-6;a=age(rows)
    b=(arr(rows,'bmi_kg_m2')-25)/5;m=male(rows)
    former=np.array([z['smoking_status']=='Former' for z in rows],float)
    current=np.array([z['smoking_status']=='Current' for z in rows],float)
    X=np.column_stack([np.ones(len(rows)),sed,a,m,b,former,current]);outcome=arr(rows,vars[1])
    names=['Intercept','Sedentary time (per 1 h/day; centred at 6)','Age (per 10 years; centred at 50)',
       'Male vs Female','BMI (per 5 kg/m²; centred at 25)','Former vs Never smoking','Current vs Never smoking']
    r['adjusted'],inside=S.ols(X,outcome,names)
    r['selection']=selection(rows)
    r['quadratic'],quad=S.ols(np.column_stack([X,sed**2,a**2]),outcome,names+['Sedentary time squared','Age squared'])
    r['quadratic_joint']=S.joint_test(r['quadratic'],quad,[7,8])
    r['age_under_80'],_=topcode_sensitivity(X,outcome,names,rows)
    arrays=diag_arrays(inside,rows);arrays.update(x=x,y=y,group_0=low,group_1=high)
    save(r,arrays,[('Welch t-test',r['welch']['p']),('Spearman correlation',r['spearman']['p']),('Adjusted sedentary coefficient',r['adjusted']['coefficients'][1]['p'])])

def haemoglobin():
    vars=['haemoglobin_g_dl','age_years','sex']
    r=initialize(2,vars,vars[:2]);rows=subset(*vars)
    y=arr(rows,vars[0]);a=age(rows);m=male(rows)
    female=y[m==0];men=y[m==1]
    r['groups']={'Female':S.describe(female),'Male':S.describe(men)}
    r['group_label']='Recorded sex';r['group_outcome']='Haemoglobin (g/dL)'
    r['welch']=S.welch(men,female);r['welch']['contrast']='Male minus Female'
    r['brown_forsythe']=S.brown_forsythe([female,men])
    X=np.column_stack([np.ones(len(y)),a,m,a*m]);names=['Intercept (Female, age 50)','Age (Female; per 10 years)',
         'Male vs Female (at age 50)','Age × Male (slope difference per 10 years)']
    r['adjusted'],inside=S.ols(X,y,names);r['selection']=selection(rows)
    r['age_joint']=S.joint_test(r['adjusted'],inside,[1,3])
    r['age_slopes']={'Female':S.contrast(r['adjusted'],inside,[0,1,0,0]),'Male':S.contrast(r['adjusted'],inside,[0,1,0,1])}
    r['quadratic'],quad=S.ols(np.column_stack([X,a*a,a*a*m]),y,names+['Age squared (Female)','Age squared × Male'])
    r['quadratic_joint']=S.joint_test(r['quadratic'],quad,[4,5])
    r['age_under_80'],young=topcode_sensitivity(X,y,names,rows)
    r['age_under_80_slopes']={'Female':S.contrast(r['age_under_80'],young,[0,1,0,0]),'Male':S.contrast(r['age_under_80'],young,[0,1,0,1])}
    r['age_sex_descriptive']={}
    for sex in ['Female','Male']:
        for band in ['18-39','40-59','60+']:
            g=[z for z in rows if z['sex']==sex and z['age_group']==band]
            r['age_sex_descriptive'][sex+' / '+band]=S.describe(arr(g,vars[0]))
    arrays=diag_arrays(inside,rows);arrays.update(x=arr(rows,'age_years'),y=y,sex=m,group_0=female,group_1=men,
          quadratic_beta=quad['beta'],quadratic_covariance=quad['covariance'])
    save(r,arrays,[('Welch t-test',r['welch']['p']),('Joint age terms, robust Wald F',r['age_joint']['p']),('Age-by-sex interaction',r['adjusted']['coefficients'][3]['p'])])

def arm():
    vars=['arm_circumference_cm','weight_kg','height_cm','age_years','sex']
    r=initialize(3,vars,vars[:4])
    group_rows=subset(vars[0],'sex');circ=arr(group_rows,vars[0]);gsex=male(group_rows)
    female=circ[gsex==0];men=circ[gsex==1]
    r['groups']={'Female':S.describe(female),'Male':S.describe(men)}
    r['group_label']='Recorded sex';r['group_outcome']='Arm circumference (cm)'
    r['welch']=S.welch(men,female);r['welch']['contrast']='Male minus Female'
    r['brown_forsythe']=S.brown_forsythe([female,men])
    pair=subset(*vars[:2]);x=arr(pair,vars[0]);y=arr(pair,vars[1]);r['spearman']=S.spearman(x,y,6301)
    rows=subset(*vars);a=age(rows);arm=(arr(rows,vars[0])-30)/5;h=(arr(rows,'height_cm')-165)/10;m=male(rows)
    X=np.column_stack([np.ones(len(rows)),arm,h,a,m]);outcome=arr(rows,'weight_kg')
    names=['Intercept','Arm circumference (per 5 cm; centred at 30)','Height (per 10 cm; centred at 165)',
           'Age (per 10 years; centred at 50)','Male vs Female']
    r['adjusted'],inside=S.ols(X,outcome,names);r['selection']=selection(rows)
    r['quadratic'],quad=S.ols(np.column_stack([X,arm*arm,arm*m]),outcome,names+['Arm circumference squared','Arm circumference × Male'])
    r['quadratic_joint']=S.joint_test(r['quadratic'],quad,[5,6])
    r['age_under_80'],_=topcode_sensitivity(X,outcome,names,rows)
    arrays=diag_arrays(inside,rows);arrays.update(x=x,y=y,group_0=female,group_1=men)
    save(r,arrays,[('Welch t-test',r['welch']['p']),('Spearman correlation',r['spearman']['p']),('Adjusted arm coefficient',r['adjusted']['coefficients'][1]['p'])])

if __name__=='__main__':
    pulse();haemoglobin();arm()
