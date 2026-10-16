"""Thai reports for new research questions; numerical text comes from results.json."""
import json
from pathlib import Path
import mpmath as mp
from thai_report_io import ThaiReport
import bibliography

ROOT=Path(__file__).resolve().parents[1]
def pval(value):
    p=mp.mpf(value)
    return mp.nstr(p,3,min_fixed=0,max_fixed=0) if p<.0001 else f'{float(p):.4f}'.rstrip('0').rstrip('.')

def ci(values,digits=2):return f'{values[0]:.{digits}f} to {values[1]:.{digits}f}'

LABELS={'sedentary_minutes_day':'Sedentary time (min/day)','mean_pulse_bpm':'Pulse rate (bpm)',
 'age_years':'Recorded age (years)','sex':'Recorded sex','bmi_kg_m2':'BMI (kg/m²)',
 'smoking_status':'Smoking status','haemoglobin_g_dl':'Haemoglobin (g/dL)',
 'arm_circumference_cm':'Arm circumference (cm)','weight_kg':'Body weight (kg)','height_cm':'Height (cm)'}
ROLES={
 'data':('ตรวจและเตรียมข้อมูล ตรวจ missing data, outliers และ sample size ของแต่ละ analysis',
         'ร่วมกำหนด research questions และตรวจข้อมูลที่ใช้สร้าง tables และ figures'),
 'descriptive':('จัดทำ descriptive statistics, tables และ figures พร้อมเรียบเรียง results',
         'ร่วมตรวจค่าตัวเลขและความสอดคล้องระหว่าง figures กับเนื้อหารายงาน'),
 'inference':('ทำ hypothesis testing และ regression analysis ตรวจ assumptions และ program output',
         'ร่วมเลือก statistical methods และตรวจการแปลผล coefficients, confidence intervals และ p-values'),
 'literature':('ค้นคว้า research articles เรียบเรียง introduction และ discussion พร้อมจัดรูปแบบรายงาน',
         'ร่วมเปรียบเทียบผลกับงานวิจัยเดิม ตรวจ references และความครบถ้วนของรายงาน'),
}

class GroupReport(ThaiReport):
    def __init__(self,folder,r,group):
        super().__init__(folder,' '.join(r['config']['title']),r['config']['name'],r['variant'])
        self.edition=4;self.technical_terms_language='en';self.title_lines=r['config']['title']
        self.authors=[m['name'] for m in group['members']];self.contribution_status=group['contribution_status']
        self.group_number=group['group_number'];self.document_status='final'
        self.student_ids_pending=False;self.student_ids_displayed=False
        self.result=r;self.group=group;self.table_count=0
        self.p('ผู้จัดทำ: '+'; '.join(self.authors),main=False,style='caption')

    def section(self,title):self.h(title,main=True)
    def tab(self,title,headers,rows):
        self.table_count+=1
        self.table(title,headers,rows,f'table_{self.table_count:02}.csv')
    def finish(self):
        bibliography.finalize(self)
        (self.folder/'report_blocks.json').write_text(json.dumps(self.blocks,ensure_ascii=False,indent=2),encoding='utf-8')
        self.save()

def mean_sd(d):return f'{d["mean"]:.2f} ± {d["sd"]:.2f}'
def median(d):return f'{d["median"]:.2f} [{d["q1"]:.2f}, {d["q3"]:.2f}]'
def test_text(w):
    return f'Welch t={w["t"]:.3f}, df={w["df"]:.2f}, p={pval(w["p"])}'
def coef_text(c,digits=3):
    return f'β={c["beta"]:.{digits}f} (95% CI {ci(c["ci"],digits)}; t={c["t"]:.3f}, df={c["df"]:,}, p={pval(c["p"])})'
def wald_text(w):return f'F({w["df1"]}, {w["df2"]:,})={w["F"]:.3f}, p={pval(w["p"])}'

def common_methods(doc):
    doc.section('วิธีดำเนินการศึกษา')
    doc.p('การศึกษานี้เป็น cross-sectional analysis ของ NHANES 2021–2023 teaching dataset ที่ได้รับ มีผู้เข้าร่วม age ≥18 years จำนวน 8,153 คน และ 26 variables ใช้ participant ID ตรวจ duplicate records พบว่าไม่มี ID ซ้ำ ชุดข้อมูลไม่มี sample weights, strata หรือ primary sampling units (PSUs) จึงรายงาน unweighted sample estimates และไม่อ้างว่าเป็น estimates ของผู้ใหญ่ทั่วสหรัฐอเมริกา [1]')
    doc.p('กำหนด analysis-specific complete cases โดยใช้เฉพาะ variables ที่จำเป็นต่อแต่ละวิธี ให้ blank cells เป็น missing data และไม่แทนด้วยศูนย์ ตรวจ range, skewness และค่าที่อยู่นอก 1.5 × IQR fences เพื่อค้นหา outliers แต่เก็บค่าที่พบไว้ทั้งหมด เพราะไม่มีหลักฐานเพียงพอว่าเป็น measurement errors เปรียบเทียบ age และสัดส่วน Female ระหว่างผู้ที่เข้าและไม่เข้า primary regression เพื่อประเมิน selection ที่เกิดขึ้น โดยไม่ถือว่าการเปรียบเทียบนี้พิสูจน์ว่า missing data เป็น MCAR')
    doc.p('รายงาน mean ± standard deviation (SD), median [Q1, Q3] และ frequency (%) พร้อม denominator เพื่อตรวจทั้งระดับและ distribution ของข้อมูล ใช้ Jarque–Bera test ตรวจ H0: normal distribution แยกแต่ละกลุ่มและ primary-model residuals โดยอาศัย asymptotic chi-square distribution, df=2 เพราะทุกชุดที่ตรวจมี n>2,000 [9] ใช้ Brown–Forsythe test ซึ่งเป็น median-centred Levene test ตรวจ H0: equal group variances และอ่านผลร่วมกับ box plots, residual–fitted plots, Q–Q plots, skewness และ Cook’s distance')
    doc.p('คำถามเรื่อง group comparison มุ่งประมาณ mean difference จึงเลือก Welch’s t-test ซึ่งรองรับ unequal variances [3] แม้ normality test จะปฏิเสธ H0 ยังใช้ large-sample inference ได้เมื่อแต่ละกลุ่มมีมากกว่า 2,000 คน โดยพิจารณา skewness และ outliers ร่วมด้วย หลักการนี้ใช้กับ ordinary least squares (OLS) ที่สรุป linear mean association เช่นกัน [10] ใช้ HC3 standard errors รองรับ heteroscedasticity [4] และตรวจด้วย Koenker diagnostic การเลือกวิธีจึงพิจารณาทั้ง estimand, sample size และ assumptions ไม่ได้เปลี่ยนเป็น rank test ตาม normality p-value เพียงค่าเดียว')
    doc.p('ตรวจ independence ระหว่าง observations ด้วยจำนวน records, unique participant IDs และ IDs ที่ซ้ำข้ามกลุ่ม แต่ละคนมีหนึ่ง record และอยู่ได้เพียงกลุ่มเดียว จึงไม่มี repeated หรือ paired observations ใน group comparison อย่างไรก็ตาม ID audit ไม่ได้พิสูจน์ independence ระหว่างคนใน household หรือ PSU เดียวกัน เพราะไม่มี cluster IDs; p-values และ CIs จึงขึ้นกับ working assumption นี้ HC3 และ participant bootstrap ไม่ได้แก้ survey clustering ทั้งนี้ independence ที่วิธีเหล่านี้ต้องการเป็น independence ระหว่าง observations ไม่ได้กำหนดให้ predictor กับ outcome ไม่มี association')
    doc.p('กำหนด significance level 0.05 ใช้ two-sided tests สำหรับ coefficients และ mean differences ส่วน omnibus tests ใช้ upper tail ปรับ p-values ของ primary tests ทั้ง 3 research questions ด้วย Holm correction และรายงาน nominal 95% confidence intervals (CIs) ซึ่งไม่ได้ให้ simultaneous coverage การตรวจ assumptions และ sensitivity แสดงแยกและไม่รวมใน Holm family ส่วน age ≥80 years ถูก top-coded เป็น 80 จึง refit primary model เฉพาะ recorded age <80 เป็น sensitivity analysis [2]')

def common_results(doc):
    r=doc.result;a=r['adjusted'];inc=r['selection']['included'];exc=r['selection']['excluded']
    doc.section('ผลการศึกษา')
    doc.p(f'Primary regression ใช้ complete cases {a["n"]:,} คน และไม่รวม {exc["n"]:,} คนจาก missing data ใน variables ที่จำเป็น ผู้ที่เข้า analysis มี mean age {inc["age"]["mean"]:.2f} years และ Female {inc["female_percent"]:.1f}% เทียบกับ {exc["age"]["mean"]:.2f} years และ {exc["female_percent"]:.1f}% ในผู้ที่ไม่เข้า analysis จึงยังต้องคำนึงถึง selection bias ตารางที่ 1 แสดงจำนวนข้อมูลที่มีในแต่ละ variable; จำนวนเหล่านี้ไม่ใช่ sample size เดียวกันสำหรับทุก analysis')
    doc.tab('Table 1. Data availability and descriptive statistics; denominator for missingness = 8,153.',
      ['Variable','Observed n / missing %','Mean ± SD','Median [Q1, Q3]'],
      [[LABELS[k],f'{r["missingness"][k]["observed_n"]:,} / {r["missingness"][k]["missing_percent"]:.1f}%',mean_sd(v),median(v)] for k,v in r['descriptive'].items()])
    total=sum(v['n'] for v in r['groups'].values())
    doc.tab(f'Table 2. {r["group_outcome"]} by {r["group_label"].lower()}; group-comparison n={total:,}.',
      ['Group','n (%)','Mean ± SD','Median [Q1, Q3]'],
      [[k,f'{v["n"]:,} ({100*v["n"]/total:.1f}%)',mean_sd(v),median(v)] for k,v in r['groups'].items()])

def coefficient_table(doc):
    a=doc.result['adjusted']
    doc.tab(f'Table 3. Primary OLS model with HC3 standard errors; n={a["n"]:,}, residual df={a["df_resid"]:,}, R²={a["r_squared"]:.3f}.',
     ['Term','β [95% CI]','HC3 SE','t','p'],
     [[c['term'],f'{c["beta"]:.3f} [{ci(c["ci"],3)}]',f'{c["se"]:.3f}',f'{c["t"]:.3f}',pval(c['p'])] for c in a['coefficients']])

def diagnostics_text(doc):
    r=doc.result;d=r['adjusted']['diagnostics'];bf=r['brown_forsythe'];q=r['quadratic_joint']
    normal=list(r['assumptions']['normality'].values())
    group_tests='; '.join(f'{name}: JB={test["statistic"]:.2f}, p={pval(test["p"])}' for name,test in zip(r['groups'],normal[:2]))
    doc.p(f'Jarque–Bera test ให้ {group_tests} ส่วน residuals ให้ JB={normal[2]["statistic"]:.2f}, p={pval(normal[2]["p"])} ทุก test มี df=2 และปฏิเสธ normality จึงไม่อ้างว่าข้อมูลเป็น normal แต่คง Welch สำหรับ mean difference และ OLS-HC3 สำหรับ linear summary ตามเหตุผลด้าน large-sample inference ที่ระบุไว้ โดยแสดง n, skewness และ excess kurtosis ใน Appendix C')
    variance='พบหลักฐานว่า group variances ต่างกัน' if mp.mpf(bf['p'])<.05 else 'ยังไม่พบหลักฐานว่า group variances ต่างกัน แต่ไม่ได้พิสูจน์ว่าเท่ากัน'
    doc.p(f'Brown–Forsythe test ให้ {wald_text(bf)} จึง{variance} ส่วน Koenker LM={d["koenker_LM"]:.3f} (df={d["koenker_df"]}, p={pval(d["koenker_p"])}) สนับสนุนการใช้ HC3 สำหรับ heteroscedasticity ทั้งนี้ HC3 ไม่ได้แก้ nonlinearity มี {d["cooks_above_4_over_n"]:,} observations ที่ Cook’s distance >4/n และค่าสูงสุด {d["max_cooks"]:.4f}; เก็บไว้ทั้งหมดและใช้เป็น diagnostic flags ผลของ primary tests ทั้งสามยังมี Holm-adjusted p<0.05 ตาม Appendix C')

def common_appendix(doc):
    r=doc.result;variant=r['variant']
    bibliography.append_references(doc)
    doc.page();doc.h('Appendix A. Contribution statement')
    doc.p(f'การแบ่งหน้าที่ของสมาชิกกลุ่มที่ {doc.group_number} ประกอบด้วยหน้าที่หลักและงานร่วมในการจัดทำรายงาน ดังแสดงในตาราง',main=False)
    doc.tab('Member responsibilities', ['ชื่อสมาชิก','หน้าที่หลัก','งานร่วมและการตรวจทาน'],
     [[m['name'],*ROLES[m['work_package']]] for m in doc.group['members']])
    doc.h('Appendix B. Missing data and selection')
    doc.tab('Availability of every variable required by the primary model', ['Variable','Observed n','Missing n (%)'],
       [[LABELS[k],f'{v["observed_n"]:,}',f'{v["missing_n"]:,} ({v["missing_percent"]:.1f}%)'] for k,v in r['missingness'].items()])
    doc.tab('Primary regression inclusion', ['Subset','n','Age: mean ± SD','Female n (%)'],
       [[k.capitalize(),f'{v["n"]:,}',mean_sd(v['age']),f'{v["female_n"]:,} ({v["female_percent"]:.1f}%)'] for k,v in r['selection'].items()])
    doc.page();doc.h('Appendix C. Assumptions and program output')
    doc.tab('Primary tests; nominal CIs accompany estimates in Results', ['Question','Test','Raw p','Holm p'],
       [[str(v['question']),v['test'],pval(v['p']),pval(v['holm_p'])] for v in r['primary_tests']])
    doc.tab('Ranges, skewness and IQR flags; no observations deleted', ['Variable','Min / max','Skewness','Outside 1.5 × IQR'],
       [[LABELS[k],f'{v["min"]:.2f} / {v["max"]:.2f}',f'{v["skewness"]:.3f}',str(v['outlier_fence_count'])] for k,v in r['descriptive'].items()])
    doc.tab('Normality diagnostics: Jarque–Bera, df=2; H0: normal distribution',
       ['Sample / variable','n','Skewness / excess kurtosis','JB','p'],
       [[name,f'{v["n"]:,}',f'{v["skewness"]:.3f} / {v["excess_kurtosis"]:.3f}',f'{v["statistic"]:.3f}',pval(v['p'])]
        for name,v in r['assumptions']['normality'].items()])
    independence=r['assumptions']['independence']
    doc.tab('Participant ID audit for observation independence', ['Analysis sample','Records','Unique IDs'],
       [[name,f'{v["records"]:,}',f'{v["unique_ids"]:,}'] for name,v in independence['samples'].items()])
    doc.p(f'Group overlap = {independence["overlapping_group_ids"]} participant IDs; ทุกกลุ่มแยกจากกันและไม่มี repeated records การตรวจนี้รองรับ unpaired analysis แต่ยังตรวจ household/PSU independence ไม่ได้ เพราะไม่มี cluster IDs จึงไม่มี p-value ที่ใช้ยืนยัน independence จากข้อมูลนี้',main=False)
    d=r['adjusted']['diagnostics'];a=r['adjusted'];bf=r['brown_forsythe']
    doc.tab('Primary-model diagnostic output', ['Diagnostic','Value / p'],[
       ['Brown–Forsythe',wald_text(bf)],['Residual skewness / excess kurtosis',f'{d["residual_skewness"]:.3f} / {d["residual_excess_kurtosis"]:.3f}'],
       ['Jarque–Bera',f'{d["jarque_bera"]:.3f}; df=2; p={pval(d["jarque_bera_p"])}'],
       ['Koenker LM',f'{d["koenker_LM"]:.3f}; df={d["koenker_df"]}; p={pval(d["koenker_p"])}'],
       ['Cook’s distance >4/n / maximum',f'{d["cooks_above_4_over_n"]} / {d["max_cooks"]:.5f}'],
       ['Maximum leverage',f'{d["max_leverage"]:.5f}'],['In-sample residual RMSE',f'{a["residual_rmse"]:.3f}'],
       ['Robust overall model F',f'F({a["parameters"]-1}, {a["df_resid"]})={a["robust_model_F"]:.3f}; p={pval(a["robust_model_p"])}']])
    doc.page();doc.h('Appendix D. Regression diagnostic figures')
    doc.fig('figures/diagnostic_residuals.png','Figure D1. Residual–fitted plot ของ primary model; จุดสีเทาคือ observations ทั้งหมด เส้นสีส้มเชื่อม mean residuals ใน 12 equal-count bins และเส้นแนวนอนคือ residual=0 ใช้พิจารณา nonlinearity และ heteroscedasticity')
    doc.fig('figures/diagnostic_qq.png','Figure D2. Q–Q plot ของ standardized residuals เทียบกับ theoretical normal quantiles; การเบี่ยงจากเส้นอ้างอิงสะท้อนความต่างจาก normal distribution โดยไม่ใช้เป็นกฎสำหรับลบ observations')
    doc.page();doc.h('Appendix E. Sensitivity analyses and reproducibility')
    q=r['quadratic']
    doc.p(f'Expanded model ใช้ complete cases เดิม n={q["n"]:,}, R²={q["r_squared"]:.3f}; joint test ของ added terms: {wald_text(r["quadratic_joint"])} ผลทั้งหมดใน Appendix นี้เป็น exploratory analysis และ p-values ไม่ได้ผ่าน Holm correction ของ primary family',main=False)
    doc.tab('Expanded-model coefficients; HC3 CIs', ['Term','β [95% CI]','t','p'],
       [[c['term'],f'{c["beta"]:.3f} [{ci(c["ci"],3)}]',f'{c["t"]:.3f}',pval(c['p'])] for c in q['coefficients']])
    s=r['age_under_80']
    doc.p(f'Refit primary model เฉพาะ recorded age <80: n={s["n"]:,}, residual df={s["df_resid"]:,}, R²={s["r_squared"]:.3f} การจำกัด age นี้เปลี่ยน analysis population และไม่ใช่การลบ outliers',main=False)
    if variant==2:
        sensitivity_rows=[[sex+' age slope (per 10 years)',f'{c["estimate"]:.3f} [{ci(c["ci"],3)}]',f'{c["t"]:.3f}',pval(c['p'])] for sex,c in r['age_under_80_slopes'].items()]
        c=s['coefficients'][3]
        sensitivity_rows.append([c['term'],f'{c["beta"]:.3f} [{ci(c["ci"],3)}]',f'{c["t"]:.3f}',pval(c['p'])])
    else:
        c=s['coefficients'][1]
        sensitivity_rows=[[c['term'],f'{c["beta"]:.3f} [{ci(c["ci"],3)}]',f'{c["t"]:.3f}',pval(c['p'])]]
    doc.tab('Age <80: target coefficients; all covariates retained', ['Term','β [95% CI]','t','p'],sensitivity_rows)
    doc.p('วิเคราะห์ด้วย Python '+r['software']['python']+', NumPy '+r['software']['numpy']+' และ mpmath '+r['software']['mpmath']+' คำนวณ HC3 covariance ตาม formula [4] และตรวจ regression coefficients กับ standard errors ซ้ำด้วย QR decomposition และ leave-one-out refits',main=False)
    if 'spearman' in r:
        s=r['spearman'];doc.p(f'Spearman 95% CI ใช้ paired percentile bootstrap {s["resamples"]:,} resamples ด้วย NumPy default_rng seed={s["seed"]} โดย resample ผู้เข้าร่วมเป็นคู่และคำนวณ average ranks ใหม่ทุกครั้งเพื่อรองรับ ties',main=False)

def pulse(doc):
    r=doc.result;w=r['welch'];s=r['spearman'];a=r['adjusted'];c=a['coefficients'][1]
    doc.section('บทนำ')
    doc.p('Sedentary time และ pulse rate เป็นข้อมูลคนละด้านของ health behaviour และ physiological response งานของ Beijer และคณะพบว่า TV time ที่นานขึ้นมี association กับ pulse rate ที่สูงขึ้นเล็กน้อย [6] ส่วนงานของ McGregor และคณะพิจารณาเวลาตลอดวันร่วมกับ physical activity [7] การศึกษาจาก teaching dataset นี้จึงมุ่งตรวจว่ารูปแบบดังกล่าวปรากฏใน self-reported sedentary time หรือไม่ และ association มีขนาดเท่าใดเมื่อปรับ covariates ที่มีอยู่')
    for q in r['config']['questions']:doc.p(q)
    common_methods(doc)
    doc.p('Sedentary time มาจาก sedentary_minutes_day แปลงเป็น h/day โดยหารด้วย 60 และไม่รวม sleep ตามคำถามต้นทาง [5] Pulse rate ใช้ mean_pulse_bpm ซึ่ง codebook ระบุว่าเป็น mean ของ pulse readings ที่มีอยู่; NHANES วัดด้วย oscillometric device หลังนั่งพัก 5 minutes [8] กำหนดกลุ่ม <8 และ ≥8 h/day เพื่อให้ group contrast อธิบายได้ง่าย Cut-off นี้เป็น descriptive choice ไม่ใช่ clinical threshold และยังวิเคราะห์ sedentary time แบบ continuous ควบคู่กัน')
    doc.p('สำหรับ correlation เลือก Spearman เพียงวิธีเดียว เพื่อวัด monotonic association ในข้อมูลที่มี ties และไม่ผ่าน normality diagnostics โดยไม่บังคับ linearity ใช้ paired percentile bootstrap 2,000 resamples สำหรับ CI และ t approximation สำหรับ p-value Primary OLS มี outcome เป็น pulse rate; predictors ได้แก่ sedentary time, age, sex, BMI และ smoking status เพื่อคำนึงถึงความต่างด้าน demographic, body size และ smoking ใช้ Female และ Never เป็น reference groups และใช้ quadratic sedentary time กับ quadratic age เป็น sensitivity analysis')
    common_results(doc)
    doc.p(f'Group comparison และ Spearman ใช้ข้อมูล {s["n"]:,} คน กลุ่ม ≥8 h/day มี mean pulse rate สูงกว่ากลุ่ม <8 h/day {w["difference"]:.2f} bpm (95% CI {ci(w["ci"])}; {test_text(w)}) อย่างไรก็ตาม box plots มี overlap มาก จึงไม่ควรใช้ group membership เพื่อคาด pulse rate ของบุคคลโดยตรง')
    doc.p(f'Spearman ρ={s["rho"]:.3f} (95% bootstrap CI {ci(s["ci"],3)}; approximate t={s["t_approx"]:.3f}, df={s["df"]:,}, p={pval(s["p"])}) สะท้อน positive association ขนาดเล็ก หลังปรับ covariates พบ pulse rate ต่างกัน {c["beta"]:.3f} bpm ต่อ sedentary time 1 h/day โดย {coef_text(c)}; model R²={a["r_squared"]:.3f}')
    coefficient_table(doc);diagnostics_text(doc)
    q=r['quadratic_joint'];under=r['age_under_80']['coefficients'][1]
    doc.p(f'การเพิ่ม quadratic terms ให้ {wald_text(q)} และ R²={r["quadratic"]["r_squared"]:.3f} จึงยังไม่มีหลักฐานจาก test นี้ว่าจำเป็นต้องเพิ่ม curvature ตามรูปแบบที่เลือก เมื่อจำกัด recorded age <80 เหลือ n={r["age_under_80"]["n"]:,} และ sedentary coefficient เท่ากับ {under["beta"]:.3f} bpm/h (95% CI {ci(under["ci"],3)}) ซึ่งใกล้กับ primary estimate')
    doc.page();doc.h('Figures ประกอบผลการศึกษา')
    doc.fig('figures/figure_1_groups.png','Figure 1. Box plots ของ pulse rate ในกลุ่ม sedentary time <8 และ ≥8 h/day; boxes แสดง Q1–Q3 เส้นกลางคือ median และ whiskers สิ้นสุดที่ข้อมูลจริงภายใน 1.5 × IQR fences จุดนอก whiskers ยังคงอยู่ใน analysis')
    doc.fig('figures/figure_2_scatter.png','Figure 2. Sedentary time กับ pulse rate ของ complete pairs ทั้งหมด จุดสีเทาแสดง observations และเส้นสีเข้มเชื่อม medians ใน 10 equal-count bins เพื่ออธิบายแนวโน้ม ไม่ใช่ adjusted regression line หรือ causal effect')
    doc.page();doc.section('อภิปรายผล')
    doc.p(f'ผลทั้ง group comparison, correlation และ regression สนับสนุน positive association แต่ขนาดค่อนข้างเล็ก ภายใต้ linear model ความต่างของ sedentary time 4 h/day สัมพันธ์กับ pulse rate ต่างกันประมาณ {4*c["beta"]:.2f} bpm (95% CI {ci([4*t for t in c["ci"]])}) ขณะที่ SD ภายในกลุ่มอยู่ราว 12 bpm และ model อธิบาย variation ได้เพียง {100*a["r_squared"]:.1f}% การมี p-value ต่ำจึงยังไม่แสดงว่า sedentary time ทำนาย pulse rate รายบุคคลได้ดี')
    doc.p(f'Beijer และคณะใช้สอง cohorts ในสวีเดน รวม 47,457 คน พบว่า TV time 3 เทียบกับ 1 h/day สัมพันธ์กับ pulse rate สูงขึ้น 0.6 bpm ใน middle-aged females และ 0.9 bpm ใน middle-aged males [6] ทิศทางตรงกับ adjusted estimate {c["beta"]:.3f} bpm/h ใน NHANES subset นี้ จุดแข็งของงานสวีเดนคือ sample ขนาดใหญ่และการปรับ physical activity แต่ TV time เป็น self-report และครอบคลุม sedentary time เพียงบางส่วน ความต่างของ exposure และการไม่มี physical activity ใน model ของเราอาจอธิบายขนาด association ที่ต่างกัน จึงยังเปรียบเทียบ coefficients โดยตรงไม่ได้ ทั้งสองงานเป็น cross-sectional และแยก reverse causation ไม่ได้')
    doc.p('McGregor และคณะวิเคราะห์ Canadian Health Measures Survey ในผู้ใหญ่ 6,322 คนและ older adults 1,454 คน ด้วย compositional analysis ของเวลาในหนึ่งวัน ในกลุ่ม age 18–64 association ระหว่าง sedentary behaviour กับ resting heart rate มี p=0.301 [7] จุดแข็งคือวัด waking behaviours ด้วย accelerometer พิจารณา physical activity ร่วมกับเวลาส่วนอื่น และใช้ survey weights กับ design-aware bootstrap แต่ accelerometer แยก posture ได้จำกัด ส่วน sleep ยังเป็น self-report และการเลือกเฉพาะผู้มี valid wear time อาจเกิด selection bias เมื่อเทียบกับ self-reported sedentary hours และ unweighted analysis ของเรา ความต่างด้าน measurement, adjustment และ survey design อาจทำให้ estimates กับ standard errors ต่างกัน การที่งานหนึ่งมี p<0.05 แต่อีกงานไม่มีจึงยังไม่พิสูจน์ว่า association ขัดแย้งกัน')
    doc.p('ข้อจำกัดที่มีผลต่อการแปลผลคือ recall error ของ self-reported sedentary time และการไม่มี physical activity, cardiorespiratory fitness, sleep, caffeine หรือ rate-lowering medications สำหรับ adjustment BMI อาจอยู่บน causal pathway บางส่วน จึงควรอ่าน adjusted coefficient เป็น conditional association ตาม model ที่ระบุ การวัด exposure และ outcome ในช่วงเดียวกันยังแยก reverse causation ไม่ได้ และ complete-case selection อาจทำให้ผลต่างจากผู้ที่ไม่มี measurement')
    doc.p('ในบริบท biomedical engineering ผลสนับสนุนการศึกษาข้อมูล behaviour ร่วมกับ physiological measurements แต่ยังไม่เพียงพอสำหรับสร้าง decision threshold ของ wearable device หรือสรุปว่าลด sedentary time แล้ว pulse rate จะลดตาม coefficient การศึกษาต่อควรมี repeated measurements, objective activity data และ survey design information เพื่อประเมิน association และ uncertainty ได้ตรงกับจุดประสงค์มากขึ้น')
    doc.section('สรุปผล')
    doc.p(f'ใน teaching sample นี้ sedentary time มี positive association ขนาดเล็กกับ pulse rate โดย adjusted difference เท่ากับ {c["beta"]:.3f} bpm ต่อ 1 h/day และกลุ่ม ≥8 h/day มี mean pulse rate สูงกว่ากลุ่ม <8 h/day {w["difference"]:.2f} bpm ข้อจำกัดด้าน missing data, unmeasured confounding และ survey design ทำให้ผลนี้ใช้ยืนยัน causality หรือประเมินผลของ intervention ไม่ได้')
    common_appendix(doc)

def haemoglobin(doc):
    r=doc.result;w=r['welch'];a=r['adjusted'];interaction=a['coefficients'][3];f=r['age_slopes']['Female'];m=r['age_slopes']['Male']
    doc.section('บทนำ')
    doc.p('Haemoglobin เป็น laboratory measurement ที่ต้องพิจารณาร่วมกับ age และ sex การศึกษาจากเกาหลีพบว่า distribution ของ haemoglobin ต่างกันระหว่าง sex [6] ขณะที่งานจากจีนพบว่าแนวโน้มตาม age ไม่เป็นเส้นตรงและมีรูปแบบต่างกันระหว่างกลุ่ม [7] รายงานนี้จึงตรวจทั้ง mean difference และ age-by-sex interaction เพื่อหลีกเลี่ยงการสรุปแนวโน้มจาก pooled mean เพียงค่าเดียว โดยไม่ใช้ผลวิเคราะห์เพื่อกำหนด diagnostic threshold ของ anaemia')
    for q in r['config']['questions']:doc.p(q)
    common_methods(doc)
    doc.p('ใช้ haemoglobin_g_dl ซึ่งมาจาก CBC measurement (LBXHGB) และมี unit เป็น g/dL [5] ใช้ age_years เป็น recorded age และใช้ sex ตาม codebook ที่มี Female กับ Male เท่านั้น Primary model คือ haemoglobin = β0 + β1A + β2M + β3(A×M) โดย A=(age−50)/10 และ M=1 สำหรับ Male, 0 สำหรับ Female ดังนั้น β1 คือ Female age slope ต่อ 10 years, β1+β3 คือ Male slope และ β2 คือ sex difference ที่ age 50')
    doc.p('Question 1 ใช้ Welch’s t-test ของ unadjusted means ส่วน Question 2 ใช้ robust Wald F-test ของ null hypothesis β1=β3=0 พร้อมกัน เพื่อทดสอบ age association ใน model ที่ยอมให้ slopes ต่างกัน Question 3 ทดสอบ β3=0 โดยตรง CI ของ Male slope คำนวณจาก linear contrast ที่รวม covariance ระหว่าง β1 กับ β3 ใช้ quadratic age และ quadratic age-by-sex interaction ตรวจ sensitivity ของ linearity assumption และสรุป haemoglobin ตาม age groups 18–39, 40–59 และ 60+ เป็น descriptive analysis เพิ่มเติม')
    common_results(doc)
    doc.p(f'ข้อมูล haemoglobin มี n={a["n"]:,}; Female {r["groups"]["Female"]["n"]:,} คน และ Male {r["groups"]["Male"]["n"]:,} คน กลุ่ม Male มี mean haemoglobin สูงกว่า Female {w["difference"]:.3f} g/dL (95% CI {ci(w["ci"],3)}; {test_text(w)}) ค่า mean difference นี้ยังไม่ได้ปรับ age จึงต้องพิจารณาร่วมกับ model ที่มี interaction')
    doc.p(f'Joint test ของ age terms ให้ {wald_text(r["age_joint"])}; Female linear slope เท่ากับ {f["estimate"]:.3f} g/dL ต่อ 10 years (95% CI {ci(f["ci"],3)}) ส่วน Male slope เท่ากับ {m["estimate"]:.3f} (95% CI {ci(m["ci"],3)}) ความต่างระหว่าง slopes คือ {coef_text(interaction)}; R²={a["r_squared"]:.3f} จึงไม่ควรใช้ slope เดียวสรุปข้อมูลทั้งสองกลุ่ม')
    coefficient_table(doc);diagnostics_text(doc)
    doc.p(f'Quadratic sensitivity ให้ joint test {wald_text(r["quadratic_joint"])} และ R² เพิ่มเป็น {r["quadratic"]["r_squared"]:.3f} เป็นหลักฐานว่า age pattern มี curvature จึงแปล linear slopes เป็น summaries ตลอดช่วง recorded age ไม่ใช่อัตราการเปลี่ยนแปลงคงที่ทุกช่วง เมื่อจำกัด recorded age <80 (n={r["age_under_80"]["n"]:,}) slopes ของ Female และ Male เท่ากับ {r["age_under_80_slopes"]["Female"]["estimate"]:.3f} และ {r["age_under_80_slopes"]["Male"]["estimate"]:.3f} g/dL ต่อ 10 years ตามลำดับ โดยทิศทางยังต่างกัน')
    doc.tab('Table 4. Haemoglobin (g/dL) by recorded sex and age group; descriptive comparison.',
      ['Sex / age (years)','n','Mean ± SD','Median [Q1, Q3]'],
      [[k,str(v['n']),mean_sd(v),median(v)] for k,v in r['age_sex_descriptive'].items()])
    doc.page();doc.h('Figures ประกอบผลการศึกษา')
    doc.fig('figures/figure_1_groups.png','Figure 1. Box plots ของ haemoglobin จำแนกตาม recorded sex; boxes แสดง Q1–Q3 เส้นกลางคือ median และ whiskers สิ้นสุดที่ข้อมูลจริงภายใน 1.5 × IQR fences ทุก observation รวมอยู่ใน analysis')
    doc.fig('figures/figure_2_age.png','Figure 2. จุดแสดง mean haemoglobin ใน recorded age bands 18–29, 30–39, 40–49, 50–59, 60–69, 70–79 และ 80+ แยกตาม sex; เส้นแสดง fitted means จาก quadratic sensitivity model ในช่วง 18–79 years และไม่ใช่ individual trajectories จุด 80+ เป็น top-coded category จึงไม่ใช่ exact age 80 ของทุกคน')
    doc.page();doc.section('อภิปรายผล')
    doc.p(f'กลุ่ม Male มี mean haemoglobin สูงกว่า Female แต่ช่องว่างขึ้นกับ age เพราะ Male linear slope เป็นลบ ขณะที่ Female slope เป็นบวกเล็กน้อย ผลของ quadratic sensitivity ยืนยันว่าไม่ควรอ่าน linear summary ว่า haemoglobin เพิ่มหรือลดในอัตราเดียวตลอดช่วง age แม้ interaction มี p-value ต่ำ แต่ model R²={a["r_squared"]:.3f} และยังมี within-group variation ที่ age กับ sex อธิบายไม่ได้')
    doc.p(f'Nah และคณะศึกษาผู้เข้ารับ health checkups 1,159,298 คน จาก 16 centres ใน 13 เมืองของเกาหลี พบ mean haemoglobin 15.29±1.22 g/dL ใน Male และ 13.25±1.13 g/dL ใน Female [6] งานนี้มีข้อดีด้าน sample size และหลาย centres แต่ health-checkup sample อาจต่างจากผู้ไม่ได้เข้ารับการตรวจ ค่า Male-minus-Female difference เท่ากับ 2.04 g/dL เทียบกับ {w["difference"]:.3f} g/dL ของเรา ซึ่งมี Male mean ต่ำกว่า ขณะที่ Female mean ใกล้กัน NHANES subset นี้มี mean age {r["selection"]["included"]["age"]["mean"]:.2f} years และ missing haemoglobin {r["missingness"]["haemoglobin_g_dl"]["missing_percent"]:.1f}% ความต่างของ age distribution, health status และ complete-case selection อาจอธิบายช่องว่างบางส่วน แต่ยังไม่มี age-standardized comparison ที่ยืนยันสาเหตุ จึงไม่อาจสรุปว่าเกิดจากประเทศที่ต่างกัน')
    doc.p(f'Su และคณะใช้ health-checkup data 303,084 คนจาก centre เดียวในจีน โดยมี mean age 47.6 years และใช้ smoothing splines ร่วมกับ covariate adjustment [7] วิธีนี้แสดง nonlinearity ได้ละเอียดกว่า linear summary ของเรา งานจีนพบ Male haemoglobin ลดลงหลังช่วงวัยหนุ่ม ส่วนการเพิ่มช่วง age 50–59 ใน Female พบชัดใน non-hyperglycaemic subgroup ข้อจำกัดคือ health-checkup selection และการคัดผู้มีบาง severe diseases หรือ pregnancy ออก ผลของเราพบ Male slope {m["estimate"]:.3f} g/dL ต่อ 10 years และ quadratic age pattern จึงสอดคล้องด้านทิศทางและ nonlinearity โดยไม่จำเป็นต้องเหมือนกันทุกช่วง age เพราะ sample ของเรามี mean age สูงกว่า ใช้ age top-coding และไม่ได้ใช้ exclusion หรือ covariates ชุดเดียวกัน')
    doc.p('การเปลี่ยนแปลงของ menstruation, menopausal status, iron status และ renal function เป็นคำอธิบายที่ควรศึกษาเพิ่มเติม แต่ teaching dataset ไม่มีข้อมูลเหล่านี้ จึงทดสอบ mechanisms ดังกล่าวไม่ได้ เช่นเดียวกับ pregnancy, chronic disease และ medications ที่อาจมีผลต่อ haemoglobin การใช้ recorded sex สอง categories ยังไม่สามารถแทนข้อมูล hormonal status ของแต่ละบุคคล')
    doc.p('ข้อมูลเป็น cross-sectional จึงเปรียบเทียบคนต่าง age และอาจมี cohort effects หรือ survival selection; ไม่ใช่การติดตาม haemoglobin ของคนเดิมเมื่อ age เพิ่มขึ้น การมี low haemoglobin ใน sample ไม่ได้บอกสาเหตุของ anaemia และรายงานนี้ไม่ได้จำแนก anaemia status การตัดผู้ที่ไม่มี CBC measurement ออกและการไม่มี survey design variables ยังจำกัด generalizability ของผล')
    doc.p('ในงาน biomedical engineering ที่เกี่ยวกับ laboratory information systems ผลนี้สนับสนุนการแสดง distribution ตาม age และ sex ก่อนประเมิน pooled reference values อย่างไรก็ตามการสร้าง reference interval หรือ clinical alert ต้องมี protocol และ validation เฉพาะของตน ไม่ควรนำ regression line จาก teaching sample ไปใช้แทนเกณฑ์ของห้องปฏิบัติการ')
    doc.section('สรุปผล')
    doc.p(f'Mean haemoglobin ของ Male สูงกว่า Female {w["difference"]:.3f} g/dL และพบ age-by-sex interaction โดย linear age slopes มีทิศทางต่างกัน Quadratic sensitivity แสดง nonlinearity จึงควรแปลผลเป็น cross-sectional patterns ตาม age และ sex และยังใช้สรุป within-person ageing หรือวินิจฉัย anaemia ไม่ได้')
    common_appendix(doc)

def arm(doc):
    r=doc.result;w=r['welch'];s=r['spearman'];a=r['adjusted'];c=a['coefficients'][1]
    doc.section('บทนำ')
    doc.p('Arm circumference เป็น anthropometric measurement ที่นำไปศึกษาร่วมกับ body weight ได้โดยไม่ต้องสร้าง variable จาก body weight เอง งานของ Cattermole และคณะใช้ mid-arm circumference สร้างและตรวจ weight-estimation formula [6] แต่การเปรียบเทียบหลายวิธีในภายหลังแสดงว่า accuracy ยังขึ้นกับวิธีและกลุ่มที่ศึกษา [7] รายงานนี้จึงตรวจ association ของ arm circumference กับ body weight และบทบาทของ height, age และ sex ก่อนพิจารณาประโยชน์ด้าน weight estimation')
    for q in r['config']['questions']:doc.p(q)
    common_methods(doc)
    doc.p('ใช้ arm_circumference_cm, weight_kg และ height_cm จาก Body Measures; codebook จับคู่กับ BMXARMC, BMXWT และ BMXHT ตามลำดับ Arm circumference หมายถึง mid-upper arm circumference ตาม documentation [5] Question 1 เปรียบเทียบ arm circumference ระหว่าง sex ด้วย Welch’s t-test; Question 2 เลือก Spearman เป็น correlation เพียงวิธีเดียว เพื่อวัด monotonic association โดยรองรับ skewed distributions และไม่บังคับ linearity ใช้ paired percentile bootstrap 2,000 resamples สำหรับ CI และ t approximation สำหรับ p-value')
    doc.p('Primary OLS ใช้ body weight (kg) เป็น outcome และใช้ arm circumference ต่อ 5 cm, height ต่อ 10 cm, age ต่อ 10 years และ sex เป็น predictors โดยปรับจุดอ้างอิงเป็น 30 cm, 165 cm และ 50 years ตามลำดับ การเพิ่ม quadratic arm circumference และ arm-by-sex interaction เป็น sensitivity analysis สำหรับ nonlinearity และ slope variation; ไม่ใส่ BMI เพราะเป็น derived variable ที่มี body weight ซึ่งเป็น outcome อยู่ในสูตร รายงาน in-sample residual RMSE เพื่ออธิบาย spread รอบ fitted values แต่ไม่ได้ทำ external prediction validation')
    common_results(doc)
    doc.p(f'Welch comparison ใช้ arm circumference {w["n1"]+w["n2"]:,} คน พบ Male-minus-Female mean difference {w["difference"]:.2f} cm (95% CI {ci(w["ci"])}; {test_text(w)}) ส่วน complete pairs สำหรับ arm circumference กับ body weight มี n={s["n"]:,} และ Spearman ρ={s["rho"]:.3f} (95% bootstrap CI {ci(s["ci"],3)}; approximate t={s["t_approx"]:.3f}, df={s["df"]:,}, p={pval(s["p"])})')
    doc.p(f'หลังปรับ height, age และ sex แล้ว arm circumference ที่ต่างกัน 5 cm สัมพันธ์กับ body weight ต่างกัน {c["beta"]:.2f} kg โดย {coef_text(c)}; model R²={a["r_squared"]:.3f} และ in-sample residual RMSE={a["residual_rmse"]:.2f} kg แม้ association สูง ยังมีความต่างของ body weight ระหว่างคนที่มี arm circumference ใกล้กัน')
    coefficient_table(doc);diagnostics_text(doc)
    doc.p(f'Joint test ของ quadratic arm circumference กับ arm-by-sex interaction ให้ {wald_text(r["quadratic_joint"])} และ expanded-model R²={r["quadratic"]["r_squared"]:.3f} จึงมีหลักฐานว่า single linear slope สรุปข้อมูลได้ไม่ครบ และ coefficient {c["beta"]:.2f} kg ต่อ 5 cm ไม่ใช่ค่าคงที่ที่ใช้ได้กับทุก arm size เมื่อจำกัด recorded age <80 (n={r["age_under_80"]["n"]:,}) primary arm coefficient เท่ากับ {r["age_under_80"]["coefficients"][1]["beta"]:.2f} kg ต่อ 5 cm (95% CI {ci(r["age_under_80"]["coefficients"][1]["ci"])})')
    doc.page();doc.h('Figures ประกอบผลการศึกษา')
    doc.fig('figures/figure_1_groups.png','Figure 1. Box plots ของ arm circumference จำแนกตาม recorded sex; boxes แสดง Q1–Q3 เส้นกลางคือ median และ whiskers สิ้นสุดที่ข้อมูลจริงภายใน 1.5 × IQR fences จุดนอก whiskers ยังคงอยู่ในการคำนวณ')
    doc.fig('figures/figure_2_scatter.png','Figure 2. Arm circumference กับ body weight ของ complete pairs ทั้งหมด เส้นสีเข้มเชื่อม medians ใน 10 equal-count bins เพื่อแสดง unadjusted pattern; ไม่ใช่ weight-estimation formula ที่ผ่าน external validation')
    doc.page();doc.section('อภิปรายผล')
    doc.p(f'Arm circumference มี positive association สูงกับ body weight แม้ปรับ height, age และ sex แล้ว ความต่างของ arm circumference ระหว่าง sex ใน Question 1 ช่วยอธิบายว่าควรคำนึงถึง body-size distribution เมื่ออ่าน unadjusted association อย่างไรก็ตาม expanded model ตรวจพบ nonlinearity และ interaction ดังนั้น primary coefficient เป็น linear summary ภายใต้ model ที่กำหนด ไม่ควรตีความว่า arm circumference เพิ่ม 5 cm แล้ว body weight จะเพิ่ม {c["beta"]:.2f} kg ในคนเดิม')
    doc.p(f'Cattermole, Graham และ Rainer ใช้ NHANES 2011–2012 สำหรับ derivation และ 2009–2010 สำหรับ validation โดย adult samples มี 5,595 และ 6,049 คนตามลำดับ [6] Simplified formula คือ weight (kg)=4×arm circumference (cm)−50 และ estimates มากกว่า 60% อยู่ภายใน 10% ของ measured weight ใน adults และ adolescents จุดแข็งคือ validation ในคนละ survey cycle ซึ่งรายงานนี้ยังไม่ได้ทำ ส่วนข้อจำกัดคือ community measurements ยังไม่ยืนยัน accuracy ระหว่าง emergency care ค่า adjusted slope ของเราเท่ากับ {c["beta"]/5:.2f} kg/cm เทียบกับ 4 kg/cm ใน simple formula ความต่างอาจเกิดจากการปรับ height, age และ sex รวมถึง age range ที่ต่างกัน ขณะที่ standardized NHANES body measurements ที่ใช้ร่วมกันช่วยให้การพบ positive association ในทั้งสองงานมีพื้นฐานการวัดใกล้เคียงกัน')
    doc.p('Cattermole และ Wells เปรียบเทียบ 7 methods ใน NHANES 2017–2018 จำนวน 5,158 adults [7] Simplified MAC formula ให้ P10=62.3% และ P20=90.9% ส่วน Lorenz method ให้ 86.8% และ 99.4% ตามลำดับ โดย P10/P20 คือสัดส่วน estimates ที่มี error ไม่เกิน 10%/20% ของ measured weight จุดแข็งคือเปรียบเทียบ methods ใน sample เดียวกันและตรวจผลแยกตาม sex กับ BMI แต่ยังเป็น retrospective community data และวิธีที่ต้องใช้หลาย measurements อาจทำได้ยากระหว่าง emergency care ผลนี้อธิบายว่าทำไม Spearman ρ สูงในรายงานของเราจึงยังไม่พอสำหรับใช้งานรายบุคคล: คนที่มี arm circumference ใกล้กันอาจมี height และ body composition ต่างกัน ส่วน R² กับ in-sample RMSE ของเราไม่ได้วัด out-of-sample accuracy แบบ P10/P20')
    doc.p(f'แม้ primary R² เท่ากับ {a["r_squared"]:.3f} แต่ residual RMSE {a["residual_rmse"]:.2f} kg คำนวณจากข้อมูลที่ใช้ fit model จึงอาจดูดีกว่า error ในข้อมูลใหม่ และไม่ใช่ prediction interval ของบุคคล Residual plot กับ Koenker diagnostic ยังแสดง heteroscedasticity ทำให้ใช้ RMSE ค่าเดียวแทน uncertainty ทุก body size ไม่ได้ ก่อนพัฒนาเครื่องมือใช้งานจริงต้องตรวจ calibration, subgroup errors, prediction intervals และ external validation เพิ่มเติม')
    doc.p('Teaching dataset ไม่มี muscle mass, fat distribution, oedema หรือ measurement comment codes ที่ครบถ้วน จึงแยกสาเหตุของ residual variation ไม่ได้ อีกทั้ง missing measurements อาจเกี่ยวข้องกับ health status และข้อจำกัดระหว่าง examination การคง observations ที่มี extreme values ช่วยหลีกเลี่ยงการเลือก sample ตามผลลัพธ์ แต่ก็ทำให้ต้องอ่าน sensitivity และ influence diagnostics ร่วมด้วย ผลทั้งหมดเป็น unweighted associations ของ sample นี้')
    doc.p('ในบริบท biomedical engineering การใช้ arm circumference ร่วมกับ height อาจเป็นจุดตั้งต้นสำหรับศึกษา measurement-based weight estimation เมื่อชั่งโดยตรงได้ยาก แต่รายงานนี้ยังไม่ได้ประเมินอุปกรณ์หรือ clinical workflow และไม่ควรนำ fitted formula ไปใช้คำนวณ medication dose จากผลการเรียนครั้งนี้')
    doc.section('สรุปผล')
    doc.p(f'Arm circumference มี positive association สูงกับ body weight และหลังปรับ height, age และ sex ได้ linear estimate {c["beta"]:.2f} kg ต่อ 5 cm ขณะเดียวกันพบ nonlinearity, slope variation และ residual error จึงยังต้องมี prediction validation ก่อนพัฒนาเป็น weight-estimation tool')
    common_appendix(doc)

def main():
    group=json.loads((ROOT/'group_members.json').read_text(encoding='utf-8'))
    assert len(group['members'])==4 and {m['work_package'] for m in group['members']}==set(ROLES)
    folders=sorted((ROOT/'reports'/'group16').glob('variant_*'))
    assert len(folders)==3
    for folder in folders:
        r=json.loads((folder/'results.json').read_text(encoding='utf-8'))
        doc=GroupReport(folder,r,group)
        {1:pulse,2:haemoglobin,3:arm}[r['variant']](doc)
        doc.finish()

if __name__=='__main__':main()
