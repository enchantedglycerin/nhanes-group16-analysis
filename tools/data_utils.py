"""Read-only access and complete-case summaries for the supplied teaching data."""
import csv
import hashlib
import platform
from pathlib import Path
import stats_core as S
import numpy as np
import mpmath

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data'/'NHANES_BME_student - NHANES_BME_student.csv'
with SOURCE.open(encoding='utf-8-sig',newline='') as f:ROWS=list(csv.DictReader(f))
assert len(ROWS)==len({r['participant_id'] for r in ROWS})==8153

def subset(*columns,rows=ROWS):return [r for r in rows if all(r[c]!='' for c in columns)]
def arr(rows,column):return np.array([float(r[column]) for r in rows])
def male(rows):return np.array([r['sex']=='Male' for r in rows],float)
def age(rows):return (arr(rows,'age_years')-50)/10

def selection(rows):
    ids={r['participant_id'] for r in rows};excluded=[r for r in ROWS if r['participant_id'] not in ids]
    return {label:dict(n=len(g),age=S.describe(arr(g,'age_years')),
       female_n=sum(r['sex']=='Female' for r in g),female_percent=100*sum(r['sex']=='Female' for r in g)/len(g))
       for label,g in [('included',rows),('excluded',excluded)]}

def common(variables):
    return dict(source=SOURCE.name,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       total_n=len(ROWS),software=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mpmath.__version__),
       bootstrap_resamples=S.BOOTSTRAPS,missingness={c:dict(observed_n=len(subset(c)),missing_n=len(ROWS)-len(subset(c)),
       missing_percent=100*(len(ROWS)-len(subset(c)))/len(ROWS)) for c in variables})
