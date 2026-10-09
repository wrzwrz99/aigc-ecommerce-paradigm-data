# -*- coding: utf-8 -*-
"""
负二项回归（校准后范式标签版）
范式标签来自 _calibrated_codes.csv 的 范式_校准（词级词典 v3，kappa=0.587）
模型与 _nb_analysis.py 一致：M1 IF控制 / M2 期刊FE / RDD子样本±1/±2年
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import negativebinomial
from statsmodels.discrete.count_model import ZeroInflatedNegativeBinomialP

D = r'D:\论文\电商综述\AIGC文创电商\查新文本'
OUT = []

cite = pd.read_csv(D + r'\数据2_被引频次模板.csv')
cal = pd.read_csv(D + r'\_calibrated_codes.csv')
clean = pd.read_csv(D + r'\_clean_records.csv')
ifac = pd.read_csv(D + r'\数据3_期刊影响因子.csv')

df = cite.merge(cal[['题名', '范式_校准']], on='题名', how='left')
df = df.merge(clean[['题名', '基金', '关键词']], on='题名', how='left')
df = df.merge(ifac[['期刊', '复合影响因子_2024版']], on='期刊', how='left')

df['age_months'] = (2026 - df['年份']) * 12 + 8
df['log_age'] = np.log(df['age_months'])
df['author_n'] = df['作者'].fillna('').apply(lambda s: len([x for x in str(s).split(';') if x.strip()]))
df['funded'] = (df['基金'].notna() & (df['基金'].astype(str).str.strip() != '')).astype(int)
df['kw_count'] = df['关键词'].fillna('').apply(lambda s: len([x for x in str(s).split(';;') if x.strip()]))
df['post2018'] = (df['年份'] >= 2018).astype(int)
df['ifac'] = df['复合影响因子_2024版']
df['journal'] = df['期刊']

PARA_MAP = {'逻辑思辨': 'logic', '实证主义': 'positivism',
            '技术驱动': 'tech', '人文解释': 'humanistic'}
df['paradigm'] = df['范式_校准'].map(PARA_MAP)
df['cite'] = df['被引频次_CNKI']
df = df.dropna(subset=['paradigm', 'cite'])
print('建模样本 N =', len(df))
OUT.append(f'建模样本 N = {len(df)}')

desc = df.groupby('paradigm').agg(
    N=('cite', 'size'),
    cite_mean=('cite', 'mean'),
    cite_med=('cite', 'median'),
    ifac_mean=('ifac', 'mean'),
    zero_share=('cite', lambda x: (x == 0).mean()),
).round(3)
desc.to_csv(D + r'\_nb_desc_calibrated.csv', encoding='utf-8-sig')
print(desc)
OUT.append('\n按范式描述统计:\n' + desc.to_string())

print('\n===== M1 负二项 + 期刊IF控制 =====')
m1 = negativebinomial(
    'cite ~ C(paradigm, Treatment(reference="logic")) + post2018 + log_age + author_n + funded + kw_count + ifac',
    data=df).fit(disp=0, maxiter=200)
print(m1.summary2())
OUT.append('\n===== M1 =====\n' + str(m1.summary2()))

print('\n===== M2 负二项 + 期刊FE =====')
try:
    m2 = negativebinomial(
        'cite ~ C(paradigm, Treatment(reference="logic")) + post2018 + log_age + author_n + funded + kw_count + C(journal)',
        data=df).fit(disp=0, maxiter=500)
    print(m2.summary2())
    OUT.append('\n===== M2 =====\n' + str(m2.summary2()))
except Exception as e:
    print('M2 未收敛:', str(e)[:300])
    OUT.append('\nM2 未收敛: ' + str(e)[:300])
    m2 = None

print('\n===== M3 ZINB =====')
infl = pd.get_dummies(df['paradigm'], prefix='p').astype(float)
infl['const'] = 1.0
try:
    m3 = ZeroInflatedNegativeBinomialP.from_formula(
        'cite ~ C(paradigm, Treatment(reference="logic")) + post2018 + log_age + author_n + funded + kw_count + C(journal)',
        data=df, exog_infl=infl).fit(disp=0, maxiter=500)
    print(m3.summary2())
    OUT.append('\n===== M3 ZINB =====\n' + str(m3.summary2()))
    if m2 is not None:
        OUT.append('\nAIC: NB=%.1f, ZINB=%.1f' % (m2.aic, m3.aic))
except Exception as e:
    print('M3 未收敛:', str(e)[:300])
    OUT.append('\nM3 未收敛: ' + str(e)[:300])
    m3 = None

print('\n===== M4/M5 RDD子样本 =====')
rdd_res = {}
for bw, name in [(1, 'bw1'), (2, 'bw2')]:
    sub = df[(df['年份'] >= 2018 - bw) & (df['年份'] <= 2018 + bw)].copy()
    mr = negativebinomial(
        'cite ~ C(paradigm, Treatment(reference="logic")) + post2018 + log_age + author_n + funded + kw_count + ifac',
        data=sub).fit(disp=0, maxiter=200)
    rdd_res[name] = mr
    print(f'--- 带宽±{bw}年, N={len(sub)}')
    print(mr.summary2())
    OUT.append(f'\n===== M{bw+3} RDD子样本带宽±{bw}年 N={len(sub)} =====\n' + str(mr.summary2()))

def irr_table(model, label):
    if model is None:
        return None
    cf = model.params
    se = model.bse
    pv = model.pvalues
    ci = model.conf_int()
    rows = []
    for k in cf.index:
        if k == 'Intercept' or k.startswith('C(journal)'):
            continue
        rows.append({
            'term': k, 'beta': round(cf[k], 4), 'IRR': round(np.exp(cf[k]), 3),
            'SE': round(se[k], 4), 'p': round(pv[k], 4),
            'CI_low': round(np.exp(ci.loc[k, 0]), 3), 'CI_high': round(np.exp(ci.loc[k, 1]), 3),
        })
    t = pd.DataFrame(rows)
    t.to_csv(D + rf'\_nb_results_cal_{label}.csv', index=False, encoding='utf-8-sig')
    return t

for m, label in [(m1, 'm1_if'), (m2, 'm2_journalFE'), (m3, 'm3_zinb')]:
    t = irr_table(m, label)
    if t is not None:
        print('\nIRR表', label)
        print(t.to_string(index=False))

for k, mr in rdd_res.items():
    t = irr_table(mr, 'm_rdd_' + k)
    print('\nIRR表 m_rdd_' + k)
    print(t.to_string(index=False))

keep = ['题名', '期刊', '年份', 'cite', 'paradigm', 'post2018', 'age_months',
        'log_age', 'author_n', 'funded', 'kw_count', 'ifac']
df[keep].to_csv(D + r'\_nb_data_calibrated.csv', index=False, encoding='utf-8-sig')
with open(D + r'\_nb_summary_calibrated.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('\n已保存: _nb_data_calibrated.csv / _nb_results_cal_*.csv / _nb_summary_calibrated.txt')
