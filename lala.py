import yfinance as yf

df = yf.download("BN", start="2021-04-01", actions=True)
df.rename(columns={'Dividends': 'divCash'}, inplace=True)
print(df)
df.to_csv("BAM.csv")
