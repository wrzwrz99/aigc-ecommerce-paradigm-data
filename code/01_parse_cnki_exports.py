# -*- coding: utf-8 -*-
"""Parse all CNKI exports in the 查新文本 folder and summarize coverage."""
import os, glob, re
import pandas as pd

BASE = r"D:\论文\电商综述\AIGC文创电商\查新文本"

xls_files = sorted(glob.glob(os.path.join(BASE, "*.xls")))
print("xls 文件数:", len(xls_files))

frames = []
for f in xls_files:
    try:
        tables = pd.read_html(f, encoding="gbk")
        if not tables:
            tables = pd.read_html(f, encoding="utf-8")
        df = tables[0]
        frames.append((os.path.basename(f), df))
    except Exception as e:
        # 尝试 utf-8
        try:
            tables = pd.read_html(f, encoding="utf-8")
            df = tables[0]
            frames.append((os.path.basename(f), df))
        except Exception as e2:
            print("FAIL", os.path.basename(f), e, e2)

# 打印第一个文件的列与示例
name0, df0 = frames[0]
print("\n示例文件:", name0)
print("列:", list(df0.columns))
print(df0.head(3).to_string()[:2000])

# 统计各文件行数
print("\n各文件行数:")
total = 0
for n, df in frames:
    print(" ", n, len(df))
    total += len(df)
print("合计行数:", total)

# 统一列名后合并（列名可能因版本不同略有差异）
def normalize(df):
    cols = list(df.columns)
    rename = {}
    for c in cols:
        cs = str(c)
        if "题名" in cs: rename[c] = "题名"
        elif "作者" in cs: rename[c] = "作者"
        elif "期刊" in cs and "来源" in cs: rename[c] = "期刊"
        elif "来源" in cs: rename[c] = "期刊"
        elif "关键词" in cs: rename[c] = "关键词"
        elif "摘要" in cs: rename[c] = "摘要"
        elif "日期" in cs: rename[c] = "日期"
        elif "年份" in cs or "年" == cs: rename[c] = "年份"
        elif "被引" in cs: rename[c] = "被引"
        elif "下载" in cs: rename[c] = "下载"
        elif "文献" in cs: rename[c] = "文献类型"
    df = df.rename(columns=rename)
    return df

merged = []
for n, df in frames:
    df = normalize(df.copy())
    merged.append(df)
all_df = pd.concat(merged, ignore_index=True)
print("\n合并后列:", list(all_df.columns))
print("合并后行数:", len(all_df))

# 保存合并结果（CSV，供后续分析）
all_df.to_csv(os.path.join(BASE, "_merged_raw.csv"), index=False, encoding="utf-8-sig")
print("已保存 _merged_raw.csv")
