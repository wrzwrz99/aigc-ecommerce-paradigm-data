# -*- coding: utf-8 -*-
"""RDD 子样本重跑（校准后范式标签）+ Mann-Kendall 趋势（校准后）"""
import pandas as pd
import numpy as np
import statsmodels.api as sm

D = r'D:\论文\电商综述\AIGC文创电商\查新文本'
OUT = []

# ============ 1. 数据：新范式标签 ============
rd = pd.read_csv(D + r'\_rdd_main_data.csv', encoding='utf-8-sig')
cal = pd.read_csv(D + r'\_calibrated_codes.csv', encoding='utf-8-sig')
df = rd.merge(cal[['题名', '范式_校准']], on='题名', how='left')
df['paradigm_new'] = df['范式_校准']
df['c2'] = df['c'] ** 2
df['post_c'] = df['post'] * df['c']
df['post_c2'] = df['post'] * df['c2']
print('N =', len(df), '范式分布:', df['paradigm_new'].value_counts().to_dict())
OUT.append('N = %d 校准后范式分布: %s' % (len(df), df['paradigm_new'].value_counts().to_dict()))
df.to_csv(D + r'\_rdd_data_calibrated.csv', index=False, encoding='utf-8-sig')

CUT = 12  # 2018Q1

def rdd(sub, degree=1, controls=None, kernel='tri', h=8, cluster_journal=True):
    s = sub[(sub['quarter'] >= CUT - h) & (sub['quarter'] <= CUT + h)].copy()
    if kernel == 'tri':
        s['w'] = 1 - np.abs(s['c']) / h
    else:
        s['w'] = 1.0
    terms = ['post', 'c', 'post_c']
    if degree == 2:
        terms += ['c2', 'post_c2']
    if controls:
        terms += controls
    X = sm.add_constant(s[terms])
    y = s['ts_cite']
    if cluster_journal:
        m = sm.WLS(y, X, weights=s['w']).fit(cov_type='cluster', cov_kwds={'groups': s['journal']})
    else:
        m = sm.WLS(y, X, weights=s['w']).fit(cov_type='HC1')
    return m, s

def fmt(m, s, label, h, degree=1, controls=None, kernel='tri'):
    p = m.params['post']; se = m.bse['post']; pv = m.pvalues['post']
    out = f'{label}: post={p:.3f} (SE {se:.3f}, p={pv:.3f}), N={len(s)}'
    print(out)
    OUT.append(out)
    return {'label': label, 'h': h, 'degree': degree, 'kernel': kernel,
            'controls': ','.join(controls or []), 'N': len(s),
            'post': round(p, 3), 'SE': round(se, 3), 'p': round(pv, 3)}

ALL = []
# ============ 2. 主断点（应不变） ============
print('===== 主断点 2018Q1（ts_cite，三角核，期刊聚类） =====')
OUT.append('\n===== 主断点 2018Q1 =====')
for h in [4, 8, 12, 16]:
    m, s = rdd(df, h=h)
    ALL.append(fmt(m, s, f'主断点 h={h} 无控制', h))
CTRL = ['author_n', 'funded', 'kw_count', 'ifac']
s_tmp = df.dropna(subset=['ifac'])
m, s = rdd(s_tmp, h=8, controls=CTRL)
ALL.append(fmt(m, s, '主断点 h=8 有控制', 8, controls=CTRL))

# ============ 3. 范式子样本（h=8，小样本用 HC1） ============
print('\n===== 范式子样本 h=8 =====')
OUT.append('\n===== 范式子样本 h=8 =====')
for c in ['逻辑思辨', '实证主义', '技术驱动', '人文解释']:
    sub = df[df['paradigm_new'] == c]
    s = sub[(sub['quarter'] >= CUT - 8) & (sub['quarter'] <= CUT + 8)].copy()
    s['w'] = 1 - np.abs(s['c']) / 8
    X = sm.add_constant(s[['post', 'c', 'post_c']])
    try:
        m = sm.WLS(s['ts_cite'], X, weights=s['w']).fit(cov_type='HC1')
        ALL.append(fmt(m, s, f'{c} 子样本 h=8（子样本N={len(sub)}）', 8))
    except Exception as e:
        print(f'{c}: 估计失败 {str(e)[:120]}')
        OUT.append(f'{c}: 估计失败 {str(e)[:120]}')

# ============ 4. placebo（与旧口径一致：一阶无交互） ============
print('\n===== Placebo 2016Q1 / 2017Q1 =====')
OUT.append('\n===== Placebo =====')
for fc, name in [(4, '2016Q1'), (8, '2017Q1')]:
    sub = df.copy()
    sub['cc'] = sub['quarter'] - fc
    sub['postp'] = (sub['cc'] >= 0).astype(int)
    hh = 8
    s = sub[(sub['quarter'] >= fc - hh) & (sub['quarter'] <= fc + hh)].copy()
    s['w'] = 1 - np.abs(s['cc']) / hh
    X = sm.add_constant(s[['postp', 'cc']])
    m = sm.WLS(s['ts_cite'], X, weights=s['w']).fit(cov_type='cluster', cov_kwds={'groups': s['journal']})
    pp, sse, pv = m.params['postp'], m.bse['postp'], m.pvalues['postp']
    out = f'Placebo {name}: post={pp:.3f} (SE {sse:.3f}, p={pv:.3f}), N={len(s)}'
    print(out); OUT.append(out)
    ALL.append({'label': 'Placebo ' + name, 'h': hh, 'degree': 1, 'kernel': 'tri',
                'controls': '', 'N': len(s), 'post': round(pp, 3), 'SE': round(sse, 3), 'p': round(pv, 3)})

res = pd.DataFrame(ALL)
res.to_csv(D + r'\_rdd_calibrated_results.csv', index=False, encoding='utf-8-sig')

# ============ 5. Mann-Kendall 趋势（校准后） ============
print('\n===== Mann-Kendall 趋势（校准后，年度份额） =====')
OUT.append('\n===== Mann-Kendall（校准后） =====')
def mk(x):
    n = len(x)
    sgn = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = x[j] - x[i]
            sgn += (1 if d > 0 else -1 if d < 0 else 0)
    var = n * (n - 1) * (2 * n + 5) / 18
    z = (sgn - 1) / np.sqrt(var) if sgn > 0 else ((sgn + 1) / np.sqrt(var) if sgn < 0 else 0)
    p = 2 * (1 - __import__('scipy').stats.norm.cdf(abs(z)))
    return z, p

yr = df.groupby(['年份', 'paradigm_new']).size().unstack(fill_value=0)
yr['total'] = yr.sum(axis=1)
print(yr)
OUT.append(yr.to_string())
for c in ['逻辑思辨', '实证主义', '技术驱动', '人文解释']:
    if c in yr.columns:
        share = yr[c] / yr['total']
        z, p = mk(share.values)
        out = f'{c} 年度份额 MK z={z:.3f} p={p:.3f}'
        print(out); OUT.append(out)

# 季度份额（2015Q1起）
qdf = df.groupby(['quarter', 'paradigm_new']).size().unstack(fill_value=0)
qdf['total'] = qdf.sum(axis=1)
for c in ['逻辑思辨', '实证主义', '技术驱动', '人文解释']:
    if c in qdf.columns:
        share = qdf[c] / qdf['total']
        z, p = mk(share.values)
        out = f'{c} 季度份额 MK z={z:.3f} p={p:.3f}'
        print(out); OUT.append(out)

with open(D + r'\_rdd_calibrated_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('\n已保存: _rdd_data_calibrated.csv / _rdd_calibrated_results.csv / _rdd_calibrated_summary.txt')
