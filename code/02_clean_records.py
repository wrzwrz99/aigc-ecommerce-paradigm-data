# -*- coding: utf-8 -*-
"""Clean merged CNKI records: drop header rows, filter anomalies, summarize journals."""
import os, re
import pandas as pd

BASE = r"D:\论文\电商综述\AIGC文创电商\查新文本"
df = pd.read_csv(os.path.join(BASE, "_merged_raw.csv"), encoding="utf-8-sig", dtype=str)

# 列0是表头标记行；每文件首行为表头
# 真正的表头行：列1 == 'Title-题名'
print("原始行数:", len(df))
header_rows = df[df["1"] == "Title-题名"].index
print("表头行数:", len(header_rows))
df = df.drop(header_rows).copy()
print("剔除表头后:", len(df))

# 统一列名
df.columns = ["文献类型", "题名", "作者", "单位", "期刊", "关键词", "摘要", "发表时间",
              "第一责任人", "基金", "年份", "卷", "期", "页码"]

# 清洗：年份为数字且在合理范围
df["年份"] = df["年份"].astype(str).str.strip()
df["年份_ok"] = df["年份"].str.match(r"^20(1[5-9]|2[0-6])$")
bad_year = df[~df["年份_ok"]]
print("\n年份异常记录:", len(bad_year))
print(bad_year[["题名", "期刊", "年份"]].head(15).to_string()[:1500])

# 剔除无题名或年份异常
clean = df[df["年份_ok"] & df["题名"].notna() & (df["题名"].str.strip() != "")].copy()
print("\n清洗后记录数:", len(clean))

# 年度分布
clean["年份"] = clean["年份"].astype(int)
print("\n年度分布:")
print(clean["年份"].value_counts().sort_index().to_string())

# 期刊分布
journals = clean["期刊"].str.strip()
print("\n期刊去重数量:", journals.nunique())
print("\n期刊频次 TOP 60:")
print(journals.value_counts().head(60).to_string())

# 重复题名检查
dup = clean[clean.duplicated(subset=["题名"], keep=False)]
print("\n重复题名组数:", len(dup))
clean.to_csv(os.path.join(BASE, "_clean_records.csv"), index=False, encoding="utf-8-sig")
print("\n已保存 _clean_records.csv")
