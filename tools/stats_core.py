"""Transparent statistical calculations using NumPy and mpmath.

OLS uses least squares, HC3 uses the sandwich formula, ranks average ties,
and reference distribution tails use regularized beta/gamma functions.
Independent numerical checks are in tools/verify_analysis.py.
"""
import math
from functools import lru_cache
from statistics import NormalDist
import mpmath as mp
import numpy as np

mp.mp.dps = 35
BOOTSTRAPS = 2000


def probability(p):
    """Preserve very small tails as decimal strings instead of reporting zero."""
    return float(p) if p >= mp.mpf('1e-300') else str(mp.nstr(p, 12))


def t_p(t, df):
    x = mp.mpf(df) / (mp.mpf(df) + mp.mpf(float(t)) ** 2)
    return probability(mp.betainc(mp.mpf(df)/2, mp.mpf('.5'), 0, x, regularized=True))


def f_p(f, df1, df2):
    x = mp.mpf(df2)/(mp.mpf(df2)+mp.mpf(df1)*float(f))
    return probability(mp.betainc(mp.mpf(df2)/2, mp.mpf(df1)/2, 0, x, regularized=True))


def chi_p(value, df):
    return probability(mp.gammainc(mp.mpf(df)/2, mp.mpf(float(value))/2, mp.inf, regularized=True))


@lru_cache(maxsize=128)
def t_critical(df):
    lo, hi = 0., 20.
    for _ in range(46):
        mid = (lo+hi)/2
        if mp.mpf(t_p(mid, df)) > .05:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


def holm(pvalues):
    p = [mp.mpf(x) for x in pvalues]
    order = sorted(range(len(p)), key=lambda i:p[i])
    out = [None]*len(p)
    running = mp.mpf(0)
    for j,i in enumerate(order):
        running = min(mp.mpf(1), max(running, (len(p)-j)*p[i]))
        out[i] = probability(running)
    return out


def describe(values):
    x = np.asarray(values, dtype=float)
    q1, median, q3 = np.quantile(x,[.25,.5,.75])
    mean = x.mean()
    m2 = np.mean((x-mean)**2)
    skew = np.mean((x-mean)**3)/m2**1.5 if m2 else 0.
    excess = np.mean((x-mean)**4)/m2**2-3 if m2 else 0.
    return dict(n=len(x), mean=float(mean), sd=float(x.std(ddof=1)),
                median=float(median), q1=float(q1), q3=float(q3),
                min=float(x.min()), max=float(x.max()), skewness=float(skew),
                excess_kurtosis=float(excess),
                outlier_fence_count=int(np.sum((x<q1-1.5*(q3-q1))|(x>q3+1.5*(q3-q1)))))


def jarque_bera(values):
    """Large-sample normality diagnostic; all report samples exceed 2,000."""
    d = describe(values)
    statistic = d['n']/6*(d['skewness']**2+d['excess_kurtosis']**2/4)
    return dict(n=d['n'],statistic=float(statistic),df=2,p=chi_p(statistic,2),
                skewness=d['skewness'],excess_kurtosis=d['excess_kurtosis'])


def ranks(x):
    x = np.asarray(x)
    order = np.argsort(x,kind='stable')
    sorted_x = x[order]
    starts = np.r_[0, np.flatnonzero(sorted_x[1:] != sorted_x[:-1])+1]
    ends = np.r_[starts[1:],len(x)]
    result = np.empty(len(x),float)
    result[order] = np.repeat((starts+ends+1)/2,ends-starts)
    return result


def spearman(x,y,seed):
    x,y = np.asarray(x),np.asarray(y)
    n = len(x)
    rho = float(np.corrcoef(ranks(x),ranks(y))[0,1])
    t = rho*math.sqrt((n-2)/(1-rho*rho))
    rng = np.random.default_rng(seed)
    estimates = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        idx = rng.integers(0,n,n)
        # Re-rank within every resample, including its new multiplicities/ties.
        estimates[i] = np.corrcoef(ranks(x[idx]),ranks(y[idx]))[0,1]
    return dict(n=n,rho=rho,t_approx=t,df=n-2,p=t_p(t,n-2),
                ci=np.quantile(estimates,[.025,.975]).tolist(),resamples=BOOTSTRAPS,seed=seed)


def welch(x,y):
    x,y = np.asarray(x),np.asarray(y)
    n1,n2 = len(x),len(y)
    v1,v2 = x.var(ddof=1)/n1,y.var(ddof=1)/n2
    se = math.sqrt(v1+v2)
    df = (v1+v2)**2/(v1*v1/(n1-1)+v2*v2/(n2-1))
    diff = float(x.mean()-y.mean())
    t = diff/se
    margin = t_critical(float(df))*se
    return dict(n1=n1,n2=n2,difference=diff,se=se,t=t,df=float(df),p=t_p(t,df),ci=[diff-margin,diff+margin])




def brown_forsythe(groups):
    groups = [np.abs(np.asarray(x)-np.median(x)) for x in groups]
    k = len(groups)
    n = sum(map(len,groups))
    means = [x.mean() for x in groups]
    overall = np.concatenate(groups).mean()
    between = sum(len(x)*(m-overall)**2 for x,m in zip(groups,means))
    within = sum(np.sum((x-m)**2) for x,m in zip(groups,means))
    f = (between/(k-1))/(within/(n-k))
    return dict(F=float(f),df1=k-1,df2=n-k,p=f_p(f,k-1,n-k))






def ols(X,y,names):
    X,y = np.asarray(X,float),np.asarray(y,float)
    n,k = X.shape
    beta,_,rank,_ = np.linalg.lstsq(X,y,rcond=None)
    assert rank==k, 'Model matrix must have full column rank.'
    fitted = X@beta
    residual = y-fitted
    bread = np.linalg.inv(X.T@X)
    h = np.einsum('ij,jk,ik->i',X,bread,X)
    weighted = X*(residual/(1-h))[:,None]
    covariance = bread@(weighted.T@weighted)@bread
    se = np.sqrt(np.diag(covariance))
    t = beta/se
    crit = t_critical(n-k)
    sse = residual@residual
    r2 = 1-sse/np.sum((y-y.mean())**2)
    cooks = residual**2/(k*sse/(n-k))*h/(1-h)**2
    aux_beta = np.linalg.lstsq(X,residual**2,rcond=None)[0]
    aux_r2 = 1-np.sum((residual**2-X@aux_beta)**2)/np.sum((residual**2-np.mean(residual**2))**2)
    resid_desc = describe(residual)
    jb = n/6*(resid_desc['skewness']**2+resid_desc['excess_kurtosis']**2/4)
    coefficients = [dict(term=name,beta=float(b),se=float(s),t=float(test),df=n-k,p=t_p(test,n-k),
                         ci=[float(b-crit*s),float(b+crit*s)]) for name,b,s,test in zip(names,beta,se,t)]
    # A robust joint Wald F for all non-intercept coefficients.
    joint = float(beta[1:]@np.linalg.solve(covariance[1:,1:],beta[1:])/(k-1))
    output = dict(n=n,df_resid=n-k,parameters=k,r_squared=float(r2),adjusted_r_squared=float(1-(1-r2)*(n-1)/(n-k)),
                  coefficients=coefficients,robust_model_F=joint,robust_model_p=f_p(joint,k-1,n-k),
                  diagnostics=dict(residual_skewness=resid_desc['skewness'],residual_excess_kurtosis=resid_desc['excess_kurtosis'],
                                   jarque_bera=float(jb),jarque_bera_p=chi_p(jb,2),
                                   koenker_LM=float(n*aux_r2),koenker_df=k-1,koenker_p=chi_p(n*aux_r2,k-1),
                                   cooks_above_4_over_n=int(np.sum(cooks>4/n)),max_cooks=float(cooks.max()),
                                   max_leverage=float(h.max())))
    internal = dict(beta=beta,covariance=covariance,fitted=fitted,residual=residual,cooks=cooks,X=X,y=y)
    return output,internal


def contrast(model,internal,weights):
    weights = np.asarray(weights,float)
    estimate = float(weights@internal['beta'])
    se = float(np.sqrt(weights@internal['covariance']@weights))
    t = estimate/se
    margin = t_critical(model['df_resid'])*se
    return dict(estimate=estimate,se=se,t=t,df=model['df_resid'],p=t_p(t,model['df_resid']),ci=[estimate-margin,estimate+margin])


def joint_test(model,internal,indices):
    beta = internal['beta'][indices]
    cov = internal['covariance'][np.ix_(indices,indices)]
    f = float(beta@np.linalg.solve(cov,beta)/len(indices))
    return dict(F=f,df1=len(indices),df2=model['df_resid'],p=f_p(f,len(indices),model['df_resid']))
