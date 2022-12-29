import pandas as pd
import numpy as np


df = pd.read_csv("data/Q1_2021.csv", header=[0, 1], index_col=0)
for index, row in df.iterrows():
    print(row['Adj Close']['ABB'])
    break

"""
file = "data/Q3_2022.csv"

data = pd.read_csv(file, header=[0, 1], index_col=0)
dates = data.index

to_fill = [x[1] for x in data.columns[data.isna().any()].tolist()]
print(to_fill)

for n in to_fill:
    print(f"Processing {n}")
    to_add = pd.read_csv(f"data/{n}.csv", index_col=0)[['adjClose', 'divCash']]

    if n in ["PTR", "SNP", "BAM"]:
        start = "2022-07-01"
        end = "2022-09-30"
    else:
        start = dates[0] + "+00:00"
        try:
            end = to_add.index[to_add.index.tolist().index(dates[-1] + "+00:00")]
        except ValueError:
            end = None

    dividends = to_add['divCash'][start:end].values.tolist()
    if len(dividends) < len(data):
        dividends = dividends + np.zeros(len(data) - len(dividends)).tolist()
    if len(dividends) > len(data):
        dividends = dividends[:len(data)]

    adjClose = to_add['adjClose'][start:end].values.tolist()
    if len(adjClose) < len(data):
        last_price = adjClose[-1]
        adjClose = adjClose + np.repeat(last_price, len(data) - len(adjClose)).tolist()
    if len(adjClose) > len(data):
        adjClose = adjClose[:len(data)]

    data['Dividends', n] = dividends
    data['Adj Close', n] = adjClose

to_fill = [x[1] for x in data.columns[data.isna().any()].tolist()]
print(to_fill)
#print(data['Dividends', 'CTXS'])
#print(data['Adj Close', 'MXIM'])

data.to_csv(file)
"""
